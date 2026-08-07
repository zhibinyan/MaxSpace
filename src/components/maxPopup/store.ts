import { reactive } from 'vue'
import type { MaxPopupItem, MaxPopupOptions } from './types'

let seed = 0
const ANIMATION_MS = 420

export const maxPopupState = reactive({
  current: null as MaxPopupItem | null,
})

const resolvers = new Map<number, (value: boolean) => void>()

function createItem(options: MaxPopupOptions): MaxPopupItem {
  return {
    id: ++seed,
    title: options.title ?? '编辑',
    size: options.size ?? 'md',
    direction: options.direction ?? 'top',
    confirmText: options.confirmText ?? '确定',
    cancelText: options.cancelText ?? '取消',
    showCancel: options.showCancel ?? true,
    content: options.content,
    contentProps: options.contentProps,
    onConfirm: options.onConfirm,
    onCancel: options.onCancel,
    visible: false,
    leaving: false,
    confirming: false,
  }
}

export function openMaxPopup(options: MaxPopupOptions = {}): Promise<boolean> {
  if (maxPopupState.current && !maxPopupState.current.leaving) {
    finishMaxPopup(false)
  }

  const item = createItem(options)
  maxPopupState.current = item

  return new Promise((resolve) => {
    resolvers.set(item.id, resolve)
    requestAnimationFrame(() => {
      if (maxPopupState.current?.id === item.id) {
        maxPopupState.current.visible = true
      }
    })
  })
}

function finishMaxPopup(confirmed: boolean) {
  const item = maxPopupState.current
  if (!item) return

  const resolve = resolvers.get(item.id)
  resolvers.delete(item.id)
  maxPopupState.current = null
  resolve?.(confirmed)
}

export async function confirmMaxPopupAction() {
  const item = maxPopupState.current
  if (!item || item.leaving || item.confirming) return

  if (item.onConfirm) {
    item.confirming = true
    try {
      const result = await item.onConfirm()
      if (result === false) return
    } finally {
      if (maxPopupState.current?.id === item.id) {
        maxPopupState.current.confirming = false
      }
    }
  }

  closeMaxPopup(true)
}

export function cancelMaxPopupAction() {
  const item = maxPopupState.current
  if (!item || item.leaving) return
  item.onCancel?.()
  closeMaxPopup(false)
}

export function closeMaxPopup(confirmed: boolean) {
  const item = maxPopupState.current
  if (!item || item.leaving) return

  item.leaving = true
  item.visible = false

  window.setTimeout(() => {
    if (maxPopupState.current?.id === item.id) {
      finishMaxPopup(confirmed)
    }
  }, ANIMATION_MS)
}

export const MAX_POPUP_ANIMATION_MS = ANIMATION_MS
