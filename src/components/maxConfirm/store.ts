import { reactive } from 'vue'
import type { MaxConfirmItem, MaxConfirmOptions, MaxDeleteConfirmOptions } from './types'

let seed = 0
const ANIMATION_MS = 380

export const maxConfirmState = reactive({
  current: null as MaxConfirmItem | null,
})

const resolvers = new Map<number, (value: boolean) => void>()

function createItem(options: MaxConfirmOptions, danger: boolean): MaxConfirmItem {
  return {
    id: ++seed,
    title: options.title ?? '提示',
    message: options.message,
    size: options.size ?? 'sm',
    direction: options.direction ?? 'top',
    confirmText: options.confirmText ?? '确定',
    cancelText: options.cancelText ?? '取消',
    danger,
    visible: false,
    leaving: false,
  }
}

export function openMaxConfirm(options: MaxConfirmOptions, danger = false): Promise<boolean> {
  if (maxConfirmState.current && !maxConfirmState.current.leaving) {
    finishMaxConfirm(false)
  }

  const item = createItem(options, danger)
  maxConfirmState.current = item

  return new Promise((resolve) => {
    resolvers.set(item.id, resolve)
    requestAnimationFrame(() => {
      if (maxConfirmState.current?.id === item.id) {
        maxConfirmState.current.visible = true
      }
    })
  })
}

export function openMaxDeleteConfirm(options: MaxDeleteConfirmOptions): Promise<boolean> {
  return openMaxConfirm(
    {
      title: options.title ?? '删除确认',
      message: options.message,
      confirmText: options.confirmText ?? '删除',
      cancelText: options.cancelText ?? '取消',
      direction: options.direction ?? 'top',
      size: 'sm',
    },
    true,
  )
}

function finishMaxConfirm(confirmed: boolean) {
  const item = maxConfirmState.current
  if (!item) return

  const resolve = resolvers.get(item.id)
  resolvers.delete(item.id)
  maxConfirmState.current = null
  resolve?.(confirmed)
}

export function closeMaxConfirm(confirmed: boolean) {
  const item = maxConfirmState.current
  if (!item || item.leaving) return

  item.leaving = true
  item.visible = false

  window.setTimeout(() => {
    if (maxConfirmState.current?.id === item.id) {
      finishMaxConfirm(confirmed)
    }
  }, ANIMATION_MS)
}

export const MAX_CONFIRM_ANIMATION_MS = ANIMATION_MS
