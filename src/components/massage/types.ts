export type MessageType = 'success' | 'error' | 'warning' | 'info'

export type MessagePosition = 'top-right' | 'top-center'

export interface MessageOptions {
  /** 通知标题 */
  title?: string
  /** 通知正文 */
  message: string
  /** 类型，影响图标与强调色 */
  type?: MessageType
  /** 弹出位置 */
  position?: MessagePosition
  /** 自动关闭毫秒，0 表示不自动关闭 */
  duration?: number
}

export interface MessageItem extends Required<Pick<MessageOptions, 'message' | 'type' | 'position' | 'duration'>> {
  id: number
  title: string
  leaving: boolean
}
