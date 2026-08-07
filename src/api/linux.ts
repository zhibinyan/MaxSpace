import { apiRequest } from './http'

export interface LinuxGroup {
  id: number
  parentId: number | null
  name: string
  sortOrder: number
  hostCount: number
  children?: LinuxGroup[]
}

export interface LinuxTag {
  id: number
  name: string
  color?: string | null
}

export interface LinuxHost {
  id: number
  name: string
  host: string
  port: number
  username: string
  authType: 'password' | 'key' | string
  hasPassword: boolean
  hasPrivateKey: boolean
  groupId: number | null
  osName: string
  envType: string
  owner: string
  remark: string
  isFavorite: boolean
  status: string
  lastConnectedAt?: string | null
  createdAt?: string | null
  updatedAt?: string | null
  tags: LinuxTag[]
}

export interface LinuxHostInput {
  name: string
  host: string
  port?: number
  username: string
  authType?: string
  password?: string
  privateKey?: string
  groupId?: number | null
  osName?: string
  envType?: string
  owner?: string
  remark?: string
  isFavorite?: boolean
  tagIds?: number[]
}

export interface SftpEntry {
  name: string
  path: string
  isDir: boolean
  size: number
  mtime: number
  mode: string
  ext: string
  editable: boolean
}

export interface SftpListResult {
  path: string
  breadcrumbs: Array<{ name: string; path: string }>
  list: SftpEntry[]
  windows?: boolean
}

export function fetchLinuxGroups() {
  return apiRequest<LinuxGroup[]>('/api/linux/groups')
}

export function createLinuxGroup(data: { name: string; parentId?: number | null; sortOrder?: number }) {
  return apiRequest<LinuxGroup>('/api/linux/groups', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updateLinuxGroup(id: number, data: Partial<{ name: string; parentId: number | null; sortOrder: number }>) {
  return apiRequest<LinuxGroup>(`/api/linux/groups/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export function deleteLinuxGroup(id: number) {
  return apiRequest<null>(`/api/linux/groups/${id}`, { method: 'DELETE' })
}

export function fetchLinuxTags() {
  return apiRequest<LinuxTag[]>('/api/linux/tags')
}

export function createLinuxTag(data: { name: string; color?: string }) {
  return apiRequest<LinuxTag>('/api/linux/tags', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function deleteLinuxTag(id: number) {
  return apiRequest<null>(`/api/linux/tags/${id}`, { method: 'DELETE' })
}

export function fetchLinuxHosts(params: Record<string, string | number | undefined | null> = {}) {
  const qs = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') qs.set(k, String(v))
  })
  const query = qs.toString()
  return apiRequest<LinuxHost[]>(`/api/linux/hosts${query ? `?${query}` : ''}`)
}

export function createLinuxHost(data: LinuxHostInput) {
  return apiRequest<LinuxHost>('/api/linux/hosts', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updateLinuxHost(id: number, data: Partial<LinuxHostInput>) {
  return apiRequest<LinuxHost>(`/api/linux/hosts/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export function deleteLinuxHost(id: number) {
  return apiRequest<null>(`/api/linux/hosts/${id}`, { method: 'DELETE' })
}

export function testLinuxHost(id: number) {
  return apiRequest<{ ok: boolean; message: string; uname?: string }>(`/api/linux/hosts/${id}/test`, {
    method: 'POST',
  })
}

export function batchLinuxHosts(action: string, ids: number[], extra: Record<string, unknown> = {}) {
  return apiRequest<{ count: number }>('/api/linux/hosts/batch', {
    method: 'POST',
    body: JSON.stringify({ action, ids, ...extra }),
  })
}

export function sftpList(hostId: number, path = '/') {
  const qs = new URLSearchParams({ hostId: String(hostId), path })
  return apiRequest<SftpListResult>(`/api/linux/sftp/list?${qs}`, { silent: true })
}

export function sftpMkdir(hostId: number, path: string) {
  return apiRequest<null>('/api/linux/sftp/mkdir', {
    method: 'POST',
    body: JSON.stringify({ hostId, path }),
  })
}

export function sftpRename(hostId: number, oldPath: string, newPath: string) {
  return apiRequest<null>('/api/linux/sftp/rename', {
    method: 'POST',
    body: JSON.stringify({ hostId, oldPath, newPath }),
  })
}

export function sftpDelete(hostId: number, path: string) {
  return apiRequest<null>('/api/linux/sftp/delete', {
    method: 'POST',
    body: JSON.stringify({ hostId, path }),
  })
}

export function sftpUpload(
  hostId: number,
  path: string,
  file: File,
  onProgress?: (percent: number) => void,
) {
  return new Promise<{ name: string; path: string }>((resolve, reject) => {
    const form = new FormData()
    form.append('hostId', String(hostId))
    form.append('path', path)
    form.append('file', file, file.name)

    const xhr = new XMLHttpRequest()
    xhr.open('POST', '/api/linux/sftp/upload')
    const token = localStorage.getItem('maxadmin_token')
    if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`)
    // 不要设置 Content-Type，交给浏览器生成 multipart boundary

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    }

    xhr.onload = () => {
      try {
        const payload = JSON.parse(xhr.responseText)
        if (payload.code === 0 || (payload.code >= 1000 && payload.code < 2000)) {
          resolve(payload.data as { name: string; path: string })
        } else {
          reject(new Error(payload.message || '上传失败'))
        }
      } catch {
        reject(new Error('上传响应解析失败'))
      }
    }
    xhr.onerror = () => reject(new Error('网络异常'))
    xhr.send(form)
  })
}

export function sftpDownloadUrl(hostId: number, path: string) {
  const token = localStorage.getItem('maxadmin_token') || ''
  const qs = new URLSearchParams({ hostId: String(hostId), path, token })
  return `/api/linux/sftp/download?${qs}`
}

export function sftpRead(hostId: number, path: string) {
  const qs = new URLSearchParams({ hostId: String(hostId), path })
  return apiRequest<{ name: string; path: string; content: string }>(`/api/linux/sftp/read?${qs}`)
}

export function sftpWrite(hostId: number, path: string, content: string) {
  return apiRequest<null>('/api/linux/sftp/write', {
    method: 'PUT',
    body: JSON.stringify({ hostId, path, content }),
  })
}

export function sftpChmod(hostId: number, path: string, mode: string) {
  return apiRequest<null>('/api/linux/sftp/chmod', {
    method: 'PUT',
    body: JSON.stringify({ hostId, path, mode }),
  })
}

export function sftpChown(hostId: number, path: string, uid: number, gid: number) {
  return apiRequest<null>('/api/linux/sftp/chown', {
    method: 'PUT',
    body: JSON.stringify({ hostId, path, uid, gid }),
  })
}

export function sftpUploadInit(hostId: number, path: string, fileName: string, size: number) {
  return apiRequest<{ token: string; path: string; offset: number; size: number }>(
    '/api/linux/sftp/upload/init',
    {
      method: 'POST',
      body: JSON.stringify({ hostId, path, fileName, size }),
    },
  )
}

export function sftpUploadChunk(token: string, offset: number, chunk: Blob) {
  return new Promise<{ token: string; offset: number; size: number }>((resolve, reject) => {
    const form = new FormData()
    form.append('token', token)
    form.append('offset', String(offset))
    form.append('chunk', chunk, 'chunk.bin')

    const xhr = new XMLHttpRequest()
    xhr.open('POST', '/api/linux/sftp/upload/chunk')
    const auth = localStorage.getItem('maxadmin_token')
    if (auth) xhr.setRequestHeader('Authorization', `Bearer ${auth}`)

    xhr.onload = () => {
      try {
        const payload = JSON.parse(xhr.responseText)
        if (payload.code === 0 || (payload.code >= 1000 && payload.code < 2000)) {
          resolve(payload.data as { token: string; offset: number; size: number })
        } else {
          reject(new Error(payload.message || '分片上传失败'))
        }
      } catch {
        reject(new Error('分片响应解析失败'))
      }
    }
    xhr.onerror = () => reject(new Error('网络异常'))
    xhr.send(form)
  })
}

export function sftpUploadComplete(token: string) {
  return apiRequest<{ name: string; path: string; size: number }>('/api/linux/sftp/upload/complete', {
    method: 'POST',
    body: JSON.stringify({ token }),
  })
}

export function sftpUploadStatus(token: string) {
  return apiRequest<{
    token: string
    path: string
    offset: number
    size: number
    status: string
    hostId: number
    fileName: string
  }>(`/api/linux/sftp/upload/${encodeURIComponent(token)}`)
}

export async function sftpDownloadZip(hostId: number, paths: string[]) {
  const token = localStorage.getItem('maxadmin_token') || ''
  const res = await fetch('/api/linux/sftp/download-zip', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ hostId, paths }),
  })
  if (!res.ok) {
    let msg = '打包下载失败'
    try {
      const j = await res.json()
      msg = j.message || msg
    } catch {
      /* ignore */
    }
    throw new Error(msg)
  }
  const blob = await res.blob()
  const cd = res.headers.get('Content-Disposition') || ''
  const m = /filename="?([^"]+)"?/.exec(cd)
  const name = m?.[1] || 'download.zip'
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = name
  a.click()
  URL.revokeObjectURL(url)
}

export function sftpSearch(
  hostId: number,
  path: string,
  keyword: string,
  opts: { recursive?: boolean; maxDepth?: number } = {},
) {
  const qs = new URLSearchParams({
    hostId: String(hostId),
    path,
    keyword,
    recursive: opts.recursive === false ? '0' : '1',
    maxDepth: String(opts.maxDepth ?? 5),
  })
  return apiRequest<{
    path: string
    keyword: string
    recursive: boolean
    maxDepth: number
    truncated: boolean
    list: Array<SftpEntry & { parent?: string }>
  }>(`/api/linux/sftp/search?${qs}`, { silent: true })
}

export function getLinuxPref<T = unknown>(key: string) {
  return apiRequest<T | null>(`/api/linux/prefs/${encodeURIComponent(key)}`, { silent: true })
}

export function setLinuxPref(key: string, value: unknown) {
  return apiRequest<unknown>(`/api/linux/prefs/${encodeURIComponent(key)}`, {
    method: 'PUT',
    body: JSON.stringify(value),
    silent: true,
  })
}

export interface SshSessionItem {
  hostId: number
  title: string
  host: string
  username: string
  port: number
  lastAt: string
  sessionId?: number
  status?: string
  hasRecording?: boolean
}

export interface SshAuditSession {
  id: number
  hostId: number
  username: string
  hostTitle: string
  host: string
  hostUser: string
  port: number
  status: string
  hasRecording: boolean
  recordingBytes: number
  startedAt?: string | null
  endedAt?: string | null
}

export interface SshAuditCommand {
  id: number
  sessionId: number
  hostId: number
  username: string
  command: string
  createdAt?: string | null
}

export function fetchSshRecent() {
  return apiRequest<SshSessionItem[]>('/api/linux/sessions/recent', { silent: true })
}

export function fetchSshHistory() {
  return apiRequest<SshSessionItem[]>('/api/linux/sessions/history', { silent: true })
}

export function registerSshSession(data: {
  hostId: number
  title: string
  host: string
  username: string
  port: number
}) {
  return apiRequest('/api/linux/sessions', {
    method: 'POST',
    body: JSON.stringify(data),
    silent: true,
  })
}

export function fetchAuditSessions(params: Record<string, string | number | undefined | null> = {}) {
  const qs = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') qs.set(k, String(v))
  })
  const query = qs.toString()
  return apiRequest<SshAuditSession[]>(`/api/linux/audit/sessions${query ? `?${query}` : ''}`)
}

export function fetchAuditCommands(params: Record<string, string | number | undefined | null> = {}) {
  const qs = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') qs.set(k, String(v))
  })
  const query = qs.toString()
  return apiRequest<SshAuditCommand[]>(`/api/linux/audit/commands${query ? `?${query}` : ''}`)
}

export function fetchSessionRecording(sessionId: number) {
  return apiRequest<{
    session: SshAuditSession
    chunks: string[]
    encoding: string
  }>(`/api/linux/sessions/${sessionId}/recording`)
}

export function linuxSshWsUrl(hostId: number) {
  const token = localStorage.getItem('maxadmin_token') || ''
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const host = window.location.host
  return `${proto}://${host}/ws/linux/ssh/${hostId}?token=${encodeURIComponent(token)}`
}

export interface LinuxAiChatItem {
  id: number
  prompt: string
  answer: string
  createdAt: string
}

export function fetchLinuxAiHistory(limit = 50) {
  return apiRequest<LinuxAiChatItem[]>(`/api/linux/ai/history?limit=${limit}`)
}
