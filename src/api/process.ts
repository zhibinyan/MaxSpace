import { apiRequest } from './http'

export interface ProcessFlowData {
  nodes?: Array<Record<string, unknown>>
  edges?: Array<Record<string, unknown>>
}

export interface ProcessItem {
  id: number
  title: string
  description: string
  processData?: ProcessFlowData | null
  createdAt?: string
  updatedAt?: string
}

export function fetchProcesses() {
  return apiRequest<ProcessItem[]>('/api/processes')
}

export function fetchProcess(id: number) {
  return apiRequest<ProcessItem>(`/api/processes/${id}`)
}

export function createProcess(payload: Partial<ProcessItem>) {
  return apiRequest<ProcessItem>('/api/processes', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateProcess(id: number, payload: Partial<ProcessItem>) {
  return apiRequest<ProcessItem>(`/api/processes/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function deleteProcess(id: number) {
  return apiRequest<void>(`/api/processes/${id}`, {
    method: 'DELETE',
  })
}
