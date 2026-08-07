import Message from '../components/massage'
import type { MessagePosition, MessageType } from '../components/massage/types'
import { ApiCode, type ApiNotify, type ApiResponse } from './types'

interface NotifyRule {
  type: MessageType
  position: MessagePosition
}

const DEFAULT_NOTIFY_RULES: Partial<Record<ApiCode, NotifyRule>> = {
  [ApiCode.LOGIN_SUCCESS]: { type: 'success', position: 'top-right' },
  [ApiCode.CREATE_SUCCESS]: { type: 'success', position: 'top-right' },
  [ApiCode.UPDATE_SUCCESS]: { type: 'success', position: 'top-right' },
  [ApiCode.DELETE_SUCCESS]: { type: 'success', position: 'top-right' },
  [ApiCode.BAD_REQUEST]: { type: 'warning', position: 'top-center' },
  [ApiCode.UNAUTHORIZED]: { type: 'error', position: 'top-center' },
  [ApiCode.FORBIDDEN]: { type: 'warning', position: 'top-center' },
  [ApiCode.NOT_FOUND]: { type: 'error', position: 'top-center' },
  [ApiCode.SERVER_ERROR]: { type: 'error', position: 'top-center' },
}

function defaultTitle(code: number): string {
  switch (code) {
    case ApiCode.LOGIN_SUCCESS:
      return '登录'
    case ApiCode.CREATE_SUCCESS:
      return '创建'
    case ApiCode.UPDATE_SUCCESS:
      return '更新'
    case ApiCode.DELETE_SUCCESS:
      return '删除'
    case ApiCode.BAD_REQUEST:
      return '提示'
    case ApiCode.UNAUTHORIZED:
      return '认证'
    case ApiCode.FORBIDDEN:
      return '权限'
    default:
      return '系统'
  }
}

function resolveNotifyRule(code: number, notify?: ApiNotify): NotifyRule | null {
  if (code === ApiCode.OK) return null

  const fallback = DEFAULT_NOTIFY_RULES[code as ApiCode]
  if (!fallback && code >= 1000 && code < 2000) {
    return { type: 'success', position: 'top-right' }
  }
  if (!fallback && code >= 400) {
    return { type: 'error', position: 'top-center' }
  }
  if (!fallback) return null

  return {
    type: notify?.type ?? fallback.type,
    position: notify?.position ?? fallback.position,
  }
}

/** 根据后端 code / message / notify 统一弹窗 */
export function handleApiNotify<T>(payload: ApiResponse<T>): void {
  const rule = resolveNotifyRule(payload.code, payload.notify)
  if (!rule || !payload.message) return

  const title = payload.notify?.title ?? payload.title ?? defaultTitle(payload.code)

  Message[rule.type]({
    title,
    message: payload.message,
    position: rule.position,
  })
}
