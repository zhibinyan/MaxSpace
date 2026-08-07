import { apiRequest } from './http'

export type FileCategory =
  | 'folder'
  | 'image'
  | 'video'
  | 'audio'
  | 'document'
  | 'office'
  | 'pdf'
  | 'markdown'
  | 'code'
  | 'archive'
  | 'install'
  | 'other'

export type FilePreviewKind =
  | 'folder'
  | 'image'
  | 'video'
  | 'audio'
  | 'pdf'
  | 'text'
  | 'office'
  | 'install'
  | 'download'

export interface FileEntry {
  id: number
  parentId: number | null
  name: string
  isFolder: boolean
  ext: string | null
  mimeType: string | null
  sizeBytes: number
  category: FileCategory
  createdBy: string | null
  updatedBy: string | null
  createdAt?: string
  updatedAt?: string
  previewKind: FilePreviewKind
  canPreview: boolean
}

export interface FileBreadcrumb {
  id: number | null
  name: string
}

export interface FileListResult {
  list: FileEntry[]
  breadcrumbs: FileBreadcrumb[]
  parentId: number | null
}

export interface FileTextPreview {
  name: string
  content: string
  truncated: boolean
}

export interface FileListQuery {
  parentId?: number | null
  keyword?: string
  category?: string
  ext?: string
  createdBy?: string
}

function authHeaders(): HeadersInit {
  const token = localStorage.getItem('maxadmin_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function buildQuery(query: FileListQuery = {}) {
  const params = new URLSearchParams()
  if (query.parentId != null) params.set('parentId', String(query.parentId))
  if (query.keyword) params.set('keyword', query.keyword)
  if (query.category) params.set('category', query.category)
  if (query.ext) params.set('ext', query.ext)
  if (query.createdBy) params.set('createdBy', query.createdBy)
  const qs = params.toString()
  return qs ? `?${qs}` : ''
}

export function fetchFiles(query: FileListQuery = {}) {
  return apiRequest<FileListResult>(`/api/files${buildQuery(query)}`)
}

export function fetchFile(id: number) {
  return apiRequest<FileEntry>(`/api/files/${id}`)
}

export function createFolder(parentId: number | null, name: string) {
  return apiRequest<FileEntry>('/api/files/folder', {
    method: 'POST',
    body: JSON.stringify({ parentId, name }),
  })
}

export function uploadFile(
  parentId: number | null,
  file: File,
  onProgress?: (percent: number) => void,
  relativePath?: string,
) {
  return new Promise<FileEntry>((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    const form = new FormData()
    if (parentId != null) form.append('parentId', String(parentId))
    form.append('file', file)
    const rel = (relativePath || (file as File & { webkitRelativePath?: string }).webkitRelativePath || '').trim()
    if (rel) form.append('relativePath', rel)

    xhr.open('POST', '/api/files/upload')
    const token = localStorage.getItem('maxadmin_token')
    if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`)

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    }

    xhr.onload = () => {
      try {
        const payload = JSON.parse(xhr.responseText)
        if (payload.code === 0 || (payload.code >= 1000 && payload.code < 2000)) {
          resolve(payload.data as FileEntry)
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

export function renameFile(id: number, name: string) {
  return apiRequest<FileEntry>(`/api/files/${id}/rename`, {
    method: 'PUT',
    body: JSON.stringify({ name }),
  })
}

export function moveFile(id: number, parentId: number | null) {
  return apiRequest<FileEntry>(`/api/files/${id}/move`, {
    method: 'PUT',
    body: JSON.stringify({ parentId }),
  })
}

export function deleteFiles(ids: number[]) {
  return apiRequest<{ count: number }>('/api/files/delete', {
    method: 'POST',
    body: JSON.stringify({ ids }),
  })
}

export function fetchTextPreview(id: number) {
  return apiRequest<FileTextPreview>(`/api/files/${id}/text`)
}

export function fileRawUrl(id: number) {
  const token = localStorage.getItem('maxadmin_token')
  const q = token ? `?token=${encodeURIComponent(token)}` : ''
  // 浏览器 <img>/<video> 无法自定义 Authorization，提供带 token 查询的备用路径不方便改后端
  // 这里用 blob 下载方式；预览组件会用 fetch + blob URL
  return `/api/files/${id}/raw${q}`
}

export async function fetchFileBlob(id: number, asAttachment = false) {
  const path = asAttachment ? `/api/files/${id}/download` : `/api/files/${id}/raw`
  const res = await fetch(path, { headers: authHeaders() })
  if (!res.ok) throw new Error('文件加载失败')
  return res.blob()
}

export async function downloadFileById(id: number, filename: string) {
  const blob = await fetchFileBlob(id, true)
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
