import { apiRequest } from './http'

export interface MenuItem {
  id: number
  parentId: number | null
  path: string
  name: string | null
  title: string
  icon: string
  component: string | null
  redirect: string | null
  keepAlive: boolean
  dock: boolean
  sortOrder: number
  createdAt?: string
  updatedAt?: string
  children?: MenuItem[]
}

export interface CurrentAdmin {
  username: string
  isSuper: boolean
}

export function fetchMenuTree() {
  return apiRequest<MenuItem[]>('/api/menus/tree')
}

export function fetchMenus() {
  return apiRequest<MenuItem[]>('/api/menus')
}

export function createMenu(payload: Partial<MenuItem>) {
  return apiRequest<MenuItem>('/api/menus', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateMenu(id: number, payload: Partial<MenuItem>) {
  return apiRequest<MenuItem>(`/api/menus/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function deleteMenu(id: number) {
  return apiRequest<void>(`/api/menus/${id}`, {
    method: 'DELETE',
  })
}

export function fetchCurrentAdmin() {
  return apiRequest<CurrentAdmin>('/api/menus/me')
}
