import type { MessagePosition, MessageType } from '../components/massage/types'

/** 与后端 python/response.py ApiCode 保持一致 */
export const ApiCode = {
  /** 查询成功（列表/详情）· 不弹窗 */
  OK: 0,

  /** 登录成功 · 弹窗 success · 右上角 */
  LOGIN_SUCCESS: 1001,
  /** 创建成功 · 弹窗 success · 右上角 */
  CREATE_SUCCESS: 1002,
  /** 更新成功 · 弹窗 success · 右上角 */
  UPDATE_SUCCESS: 1003,
  /** 删除成功 · 弹窗 success · 右上角 */
  DELETE_SUCCESS: 1004,

  /** 参数/校验错误 · 弹窗 warning · 顶部 */
  BAD_REQUEST: 400,
  /** 未登录/认证失败 · 弹窗 error · 顶部 */
  UNAUTHORIZED: 401,
  /** 无权限 · 弹窗 warning · 顶部 */
  FORBIDDEN: 403,
  /** 资源不存在 · 弹窗 error · 顶部 */
  NOT_FOUND: 404,
  /** 服务/网络异常 · 弹窗 error · 顶部 */
  SERVER_ERROR: 500,
} as const

export type ApiCode = (typeof ApiCode)[keyof typeof ApiCode]

export interface ApiNotify {
  type?: MessageType
  position?: MessagePosition
  title?: string
}

export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data?: T
  title?: string
  notify?: ApiNotify
}

export class ApiError extends Error {
  code: number

  notified: boolean

  constructor(code: number, message: string, notified = true) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.notified = notified
  }
}

export function isApiSuccess(code: number): boolean {
  return code === ApiCode.OK || (code >= 1000 && code < 2000)
}
