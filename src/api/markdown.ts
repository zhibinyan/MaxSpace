import { apiRequest } from './http'

export interface MarkdownItem {
  id: number
  title: string
  content: string
  createdAt?: string
  updatedAt?: string
}

export function fetchMarkdowns() {
  return apiRequest<MarkdownItem[]>('/api/markdowns')
}

export function fetchMarkdown(id: number) {
  return apiRequest<MarkdownItem>(`/api/markdowns/${id}`)
}

export function createMarkdown(payload: Partial<MarkdownItem>) {
  return apiRequest<MarkdownItem>('/api/markdowns', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateMarkdown(id: number, payload: Partial<MarkdownItem>) {
  return apiRequest<MarkdownItem>(`/api/markdowns/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function deleteMarkdown(id: number) {
  return apiRequest<void>(`/api/markdowns/${id}`, {
    method: 'DELETE',
  })
}
