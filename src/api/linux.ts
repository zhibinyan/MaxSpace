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

/* ─── Docker 管理 ─────────────────────────────────── */

export interface DockerOverview {
  version: string
  status: string
  containers: { total: number; running: number; stopped: number; paused: number }
  images: number
  volumes: number
  networks: number
  storage: string
  driver: string
  os: string
}

export interface DockerContainer {
  id: string
  name: string
  image: string
  status: string
  state: string
  created: string
  ports: string
  networks: string
  command: string
  cpu?: string
  mem?: string
  memPerc?: string
}

export interface DockerImage {
  id: string
  repository: string
  tag: string
  size: string
  created: string
  usedBy?: string[]
  usedCount?: number
}

export interface DockerNetwork {
  id: string
  name: string
  driver: string
  scope: string
  containers?: string[]
  containerCount?: number
}

export interface DockerVolume {
  name: string
  driver: string
  mountpoint: string
  created?: string
  usedBy?: string[]
  usedCount?: number
}

export interface DockerComposeApp {
  name: string
  status: string
  configFiles: string
  serviceCount?: number
  updatedAt?: string
}

export interface DockerAuditItem {
  id: number
  hostId: number
  username: string
  action: string
  target: string
  detail: string
  success: boolean
  createdAt: string
}

export interface DockerStatItem {
  id: string
  name: string
  cpu: string
  memUsage: string
  memPerc: string
  netIO: string
  blockIO: string
}

function dockerQs(hostId: number, extra: Record<string, string | number | undefined> = {}) {
  const qs = new URLSearchParams({ hostId: String(hostId) })
  for (const [k, v] of Object.entries(extra)) {
    if (v !== undefined && v !== '') qs.set(k, String(v))
  }
  return qs.toString()
}

export function fetchDockerOverview(hostId: number) {
  return apiRequest<DockerOverview>(`/api/linux/docker/overview?${dockerQs(hostId)}`, { silent: true })
}

export function fetchDockerContainers(hostId: number, all = true) {
  return apiRequest<DockerContainer[]>(
    `/api/linux/docker/containers?${dockerQs(hostId, { all: all ? 1 : 0 })}`,
    { silent: true },
  )
}

export function fetchDockerContainerInspect(hostId: number, id: string) {
  return apiRequest<Record<string, unknown>>(
    `/api/linux/docker/containers/inspect?${dockerQs(hostId, { id })}`,
  )
}

export function fetchDockerContainerDetail(hostId: number, id: string) {
  return apiRequest<Record<string, unknown>>(
    `/api/linux/docker/containers/detail?${dockerQs(hostId, { id })}`,
  )
}

export function fetchDockerContainerStats(hostId: number, id?: string) {
  return apiRequest<DockerStatItem[]>(
    `/api/linux/docker/containers/stats?${dockerQs(hostId, { id })}`,
    { silent: true },
  )
}

export function fetchDockerContainerLogs(
  hostId: number,
  id: string,
  tail = 200,
  since = '',
  timestamps = false,
) {
  return apiRequest<{ container: string; tail: number; logs: string }>(
    `/api/linux/docker/containers/logs?${dockerQs(hostId, {
      id,
      tail,
      since,
      timestamps: timestamps ? 1 : 0,
    })}`,
  )
}

export function dockerContainerAction(hostId: number, id: string, action: string) {
  return apiRequest<{ ok: boolean; output: string }>('/api/linux/docker/containers/action', {
    method: 'POST',
    body: JSON.stringify({ hostId, id, action }),
  })
}

export function fetchDockerImages(hostId: number) {
  return apiRequest<DockerImage[]>(`/api/linux/docker/images?${dockerQs(hostId)}`, { silent: true })
}

export function dockerImagePull(hostId: number, image: string) {
  return apiRequest<{ ok: boolean; output: string }>('/api/linux/docker/images/pull', {
    method: 'POST',
    body: JSON.stringify({ hostId, image }),
  })
}

export function dockerImageRemove(hostId: number, image: string, force = false) {
  return apiRequest<{ ok: boolean; output: string }>('/api/linux/docker/images/remove', {
    method: 'POST',
    body: JSON.stringify({ hostId, image, force }),
  })
}

export function fetchDockerImageInspect(hostId: number, image: string) {
  return apiRequest<Record<string, unknown>>(
    `/api/linux/docker/images/inspect?${dockerQs(hostId, { image })}`,
  )
}

export function dockerImageExportUrl(hostId: number, image: string) {
  return `/api/linux/docker/images/export?${dockerQs(hostId, { image })}`
}

export async function dockerImageImport(hostId: number, file: File) {
  const fd = new FormData()
  fd.append('hostId', String(hostId))
  fd.append('file', file)
  return apiRequest<{ ok: boolean; output: string }>('/api/linux/docker/images/import', {
    method: 'POST',
    body: fd,
  })
}

export function fetchDockerNetworks(hostId: number) {
  return apiRequest<DockerNetwork[]>(`/api/linux/docker/networks?${dockerQs(hostId)}`, {
    silent: true,
  })
}

export function fetchDockerNetworkInspect(hostId: number, name: string) {
  return apiRequest<Record<string, unknown>>(
    `/api/linux/docker/networks/inspect?${dockerQs(hostId, { name })}`,
  )
}

export function dockerNetworkCreate(hostId: number, name: string, driver = 'bridge') {
  return apiRequest<{ ok: boolean; id: string }>('/api/linux/docker/networks', {
    method: 'POST',
    body: JSON.stringify({ hostId, name, driver }),
  })
}

export function dockerNetworkRemove(hostId: number, name: string) {
  return apiRequest<{ ok: boolean; output: string }>('/api/linux/docker/networks/remove', {
    method: 'POST',
    body: JSON.stringify({ hostId, name }),
  })
}

export function fetchDockerVolumes(hostId: number) {
  return apiRequest<DockerVolume[]>(`/api/linux/docker/volumes?${dockerQs(hostId)}`, { silent: true })
}

export function fetchDockerVolumeInspect(hostId: number, name: string) {
  return apiRequest<Record<string, unknown>>(
    `/api/linux/docker/volumes/inspect?${dockerQs(hostId, { name })}`,
  )
}

export function dockerVolumeCreate(hostId: number, name: string) {
  return apiRequest<{ ok: boolean; name: string }>('/api/linux/docker/volumes', {
    method: 'POST',
    body: JSON.stringify({ hostId, name }),
  })
}

export function dockerVolumeRemove(hostId: number, name: string) {
  return apiRequest<{ ok: boolean; output: string }>('/api/linux/docker/volumes/remove', {
    method: 'POST',
    body: JSON.stringify({ hostId, name }),
  })
}

export function dockerVolumeBackupUrl(hostId: number, name: string) {
  return `/api/linux/docker/volumes/backup?${dockerQs(hostId, { name })}`
}

export async function dockerVolumeRestore(hostId: number, name: string, file: File) {
  const fd = new FormData()
  fd.append('hostId', String(hostId))
  fd.append('name', name)
  fd.append('file', file)
  return apiRequest<{ ok: boolean; output: string }>('/api/linux/docker/volumes/restore', {
    method: 'POST',
    body: fd,
  })
}

export function fetchDockerCompose(hostId: number) {
  return apiRequest<DockerComposeApp[]>(`/api/linux/docker/compose?${dockerQs(hostId)}`, {
    silent: true,
  })
}

export function fetchDockerComposeConfig(hostId: number, project: string, file = '') {
  return apiRequest<{ project: string; config: string }>(
    `/api/linux/docker/compose/config?${dockerQs(hostId, { project, file })}`,
  )
}

export function fetchDockerComposeLogs(hostId: number, project: string, tail = 200) {
  return apiRequest<{ project: string; logs: string }>(
    `/api/linux/docker/compose/logs?${dockerQs(hostId, { project, tail })}`,
  )
}

export function dockerComposeAction(hostId: number, project: string, action: string, file = '') {
  return apiRequest<{ ok: boolean; output: string }>('/api/linux/docker/compose/action', {
    method: 'POST',
    body: JSON.stringify({ hostId, project, action, file }),
  })
}

export function fetchDockerAudit(params: {
  hostId?: number | string
  username?: string
  limit?: number
} = {}) {
  const qs = new URLSearchParams()
  if (params.hostId) qs.set('hostId', String(params.hostId))
  if (params.username) qs.set('username', params.username)
  if (params.limit) qs.set('limit', String(params.limit))
  const q = qs.toString()
  return apiRequest<DockerAuditItem[]>(`/api/linux/docker/audit${q ? `?${q}` : ''}`)
}

export function linuxDockerExecWsUrl(hostId: number, container: string) {
  const token = localStorage.getItem('maxadmin_token') || ''
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const host = window.location.host
  return `${proto}://${host}/ws/linux/docker/${hostId}/exec?container=${encodeURIComponent(container)}&token=${encodeURIComponent(token)}`
}
