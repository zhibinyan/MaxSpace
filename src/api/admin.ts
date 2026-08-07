import { apiRequest } from './http'

export interface Admin {
  id: number
  username: string
  isSuper: boolean
  createdAt: string
  updatedAt: string
}

export function fetchAdmins() {
  return apiRequest<Admin[]>('/api/admins')
}

export function createAdmin(username: string, passwordMd5: string) {
  return apiRequest<Admin>('/api/admins', {
    method: 'POST',
    body: JSON.stringify({ username, password: passwordMd5 }),
  })
}

export function updateAdmin(id: number, payload: { username?: string; password?: string }) {
  return apiRequest<Admin>(`/api/admins/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function deleteAdmin(id: number) {
  return apiRequest<void>(`/api/admins/${id}`, {
    method: 'DELETE',
  })
}
