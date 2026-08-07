import { handleApiNotify } from './notify'
import { ApiError, isApiSuccess, type ApiResponse } from './types'

const TOKEN_KEY = 'maxadmin_token'
const API_BASE = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')

function resolveApiUrl(url: string): string {
  if (/^https?:\/\//i.test(url)) return url
  if (!API_BASE) return url
  return `${API_BASE}${url.startsWith('/') ? url : `/${url}`}`
}

export interface ApiRequestOptions extends RequestInit {
  /** 为 true 时不弹出任何通知（含错误） */
  silent?: boolean
}

export async function apiRequest<T>(url: string, options: ApiRequestOptions = {}): Promise<T> {
  const { silent, ...fetchOptions } = options
  const token = localStorage.getItem(TOKEN_KEY)
  const headers = new Headers(fetchOptions.headers)
  const isFormData =
    typeof FormData !== 'undefined' && fetchOptions.body instanceof FormData

  // FormData 必须由浏览器自动带 boundary；手动 Content-Type 会导致后端收不到 file
  if (isFormData) {
    headers.delete('Content-Type')
  } else if (!headers.has('Content-Type') && fetchOptions.body) {
    headers.set('Content-Type', 'application/json')
  }
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  let res: Response
  try {
    res = await fetch(resolveApiUrl(url), { ...fetchOptions, headers })
  } catch {
    if (!silent) {
      handleApiNotify({
        code: 500,
        message: '网络异常，请检查连接',
        notify: { type: 'error', position: 'top-center', title: '网络' },
      })
    }
    throw new ApiError(500, '网络异常，请检查连接', !silent)
  }

  let payload: ApiResponse<T>
  try {
    payload = await res.json()
  } catch {
    if (!silent) {
      handleApiNotify({
        code: 500,
        message: '服务无响应',
        notify: { type: 'error', position: 'top-center', title: '系统' },
      })
    }
    throw new ApiError(500, '服务无响应', !silent)
  }

  if (!silent) {
    handleApiNotify(payload)
  }

  if (!isApiSuccess(payload.code)) {
    throw new ApiError(payload.code, payload.message || '请求失败', !silent)
  }

  return payload.data as T
}
