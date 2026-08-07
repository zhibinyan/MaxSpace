/** SFTP 传输任务队列：并发上传、进度、暂停、重试 */

import { computed, reactive } from 'vue'
import {
  sftpUpload,
  sftpUploadChunk,
  sftpUploadComplete,
  sftpUploadInit,
} from '@/api/linux'

export type TransferKind = 'upload' | 'download'
export type TransferStatus = 'queued' | 'running' | 'paused' | 'done' | 'error' | 'cancelled'

export interface TransferTask {
  id: string
  kind: TransferKind
  hostId: number
  remoteDir: string
  fileName: string
  size: number
  loaded: number
  status: TransferStatus
  error?: string
  file?: File
  token?: string
}

const CHUNK = 1024 * 1024
const BIG = 2 * 1024 * 1024
const CONCURRENCY = 2

const state = reactive({
  tasks: [] as TransferTask[],
  open: false,
})

let running = 0
const pauseFlags = new Set<string>()

export const transferTasks = computed(() => state.tasks)
export const transferPanelOpen = computed({
  get: () => state.open,
  set: (v: boolean) => {
    state.open = v
  },
})

export function toggleTransferPanel(force?: boolean) {
  state.open = force ?? !state.open
}

function uid() {
  return `t${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

async function runUpload(task: TransferTask) {
  const file = task.file
  if (!file) throw new Error('缺少文件')

  if (file.size < BIG) {
    await sftpUpload(task.hostId, task.remoteDir, file, (pct) => {
      task.loaded = Math.round((pct / 100) * file.size)
    })
    task.loaded = file.size
    return
  }

  const init = await sftpUploadInit(task.hostId, task.remoteDir, file.name, file.size)
  task.token = init.token
  let offset = init.offset
  task.loaded = offset

  while (offset < file.size) {
    if (pauseFlags.has(task.id) || task.status === 'cancelled') {
      task.status = task.status === 'cancelled' ? 'cancelled' : 'paused'
      return
    }
    const end = Math.min(offset + CHUNK, file.size)
    const blob = file.slice(offset, end)
    const res = await sftpUploadChunk(init.token, offset, blob)
    offset = res.offset
    task.loaded = offset
  }
  await sftpUploadComplete(init.token)
}

async function pump() {
  while (running < CONCURRENCY) {
    const next = state.tasks.find((t) => t.status === 'queued')
    if (!next) return
    next.status = 'running'
    running += 1
    void (async () => {
      try {
        if (next.kind === 'upload') await runUpload(next)
        if (next.status === 'paused' || next.status === 'cancelled') return
        next.status = 'done'
        next.loaded = next.size
      } catch (err) {
        next.status = 'error'
        next.error = err instanceof Error ? err.message : '传输失败'
      } finally {
        running -= 1
        void pump()
      }
    })()
  }
}

export function enqueueUploads(hostId: number, remoteDir: string, files: File[]) {
  for (const file of files) {
    state.tasks.unshift({
      id: uid(),
      kind: 'upload',
      hostId,
      remoteDir,
      fileName: file.name,
      size: file.size,
      loaded: 0,
      status: 'queued',
      file,
    })
  }
  state.open = true
  void pump()
}

export function pauseTask(id: string) {
  pauseFlags.add(id)
  const t = state.tasks.find((x) => x.id === id)
  if (t && t.status === 'queued') t.status = 'paused'
}

export function resumeTask(id: string) {
  pauseFlags.delete(id)
  const t = state.tasks.find((x) => x.id === id)
  if (!t) return
  if (t.status === 'paused' || t.status === 'error') {
    t.status = 'queued'
    t.error = undefined
    void pump()
  }
}

export function cancelTask(id: string) {
  pauseFlags.add(id)
  const t = state.tasks.find((x) => x.id === id)
  if (!t) return
  if (t.status === 'queued' || t.status === 'paused' || t.status === 'error') {
    t.status = 'cancelled'
  } else if (t.status === 'running') {
    t.status = 'cancelled'
  }
}

export function clearFinished() {
  state.tasks = state.tasks.filter((t) => !['done', 'cancelled'].includes(t.status))
}

export function progressOf(t: TransferTask) {
  if (!t.size) return t.status === 'done' ? 100 : 0
  return Math.min(100, Math.round((t.loaded / t.size) * 100))
}
