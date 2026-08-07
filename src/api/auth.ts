import { apiRequest } from './http'

export interface LoginResult {
  token: string
  username: string
  isSuper: boolean
}

export function login(username: string, passwordMd5: string) {
  return apiRequest<LoginResult>('/api/login', {
    method: 'POST',
    body: JSON.stringify({ username, password: passwordMd5 }),
  })
}
