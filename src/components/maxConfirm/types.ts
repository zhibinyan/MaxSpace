export type MaxConfirmSize = 'sm' | 'md'

export type MaxConfirmDirection = 'top' | 'bottom' | 'left' | 'right'

export interface MaxConfirmOptions {
  /** 标题 */
  title?: string
  /** 提示正文 */
  message: string
  /** 尺寸，默认 sm */
  size?: MaxConfirmSize
  /** 弹出方向，默认 top */
  direction?: MaxConfirmDirection
  confirmText?: string
  cancelText?: string
}

export interface MaxConfirmItem extends Required<Omit<MaxConfirmOptions, 'message'>> {
  id: number
  message: string
  visible: boolean
  leaving: boolean
  danger: boolean
}

export interface MaxDeleteConfirmOptions {
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  direction?: MaxConfirmDirection
}
