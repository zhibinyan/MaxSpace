import { reactive } from 'vue'
import type { MessageItem, MessageOptions, MessagePosition, MessageType } from './types'

let seed = 0

export const messageState = reactive({
  items: [] as MessageItem[],
})

const timers = new Map<number, ReturnType<typeof setTimeout>>()

function normalizeOptions(options: MessageOptions | string, type: MessageType): MessageOptions {
  if (typeof options === 'string') {
    return { message: options, type }
  }
  return { ...options, type: options.type ?? type }
}

export function pushMessage(raw: MessageOptions | string, defaultType: MessageType): number {
  const options = normalizeOptions(raw, defaultType)
  const id = ++seed

  const item: MessageItem = {
    id,
    title: options.title ?? defaultTitle(defaultType),
    message: options.message,
    type: options.type ?? defaultType,
    position: options.position ?? 'top-right',
    duration: options.duration ?? 4000,
    leaving: false,
  }

  messageState.items.push(item)

  if (item.duration > 0) {
    const timer = setTimeout(() => dismissMessage(id), item.duration)
    timers.set(id, timer)
  }

  return id
}

function defaultTitle(type: MessageType): string {
  switch (type) {
    case 'success':
      return '成功'
    case 'error':
      return '错误'
    case 'warning':
      return '警告'
    case 'info':
      return '提示'
  }
}

export function dismissMessage(id: number): void {
  const timer = timers.get(id)
  if (timer) {
    clearTimeout(timer)
    timers.delete(id)
  }

  const item = messageState.items.find((entry) => entry.id === id)
  if (!item || item.leaving) return

  item.leaving = true
}

export function removeMessage(id: number): void {
  const index = messageState.items.findIndex((entry) => entry.id === id)
  if (index !== -1) {
    messageState.items.splice(index, 1)
  }
}

export function clearMessages(position?: MessagePosition): void {
  messageState.items
    .filter((item) => !position || item.position === position)
    .forEach((item) => dismissMessage(item.id))
}
