import type { Component } from 'vue'

export type MaxPopupSize = 'sm' | 'md' | 'lg'

/** 弹窗进入 / 离开方向 */
export type MaxPopupDirection = 'top' | 'bottom' | 'left' | 'right'

export interface MaxPopupOptions {
  /** 标题，显示在顶栏中间 */
  title?: string
  /** 尺寸：小 / 中（默认）/ 大 */
  size?: MaxPopupSize
  /** 弹出方向，默认 top */
  direction?: MaxPopupDirection
  /** 确定按钮文案 */
  confirmText?: string
  /** 取消按钮文案 */
  cancelText?: string
  /** 是否显示取消按钮，默认 true */
  showCancel?: boolean
  /** 表单内容组件 */
  content?: Component
  /** 传给 content 组件的 props */
  contentProps?: Record<string, unknown>
  /** 点击确定：返回 false 阻止关闭 */
  onConfirm?: () => boolean | void | Promise<boolean | void>
  /** 点击取消 */
  onCancel?: () => void
}

export interface MaxPopupItem extends Required<Omit<MaxPopupOptions, 'showCancel' | 'content' | 'contentProps' | 'onConfirm' | 'onCancel'>> {
  id: number
  showCancel: boolean
  content?: Component
  contentProps?: Record<string, unknown>
  onConfirm?: () => boolean | void | Promise<boolean | void>
  onCancel?: () => void
  visible: boolean
  leaving: boolean
  confirming: boolean
}
