import { clearMessages, dismissMessage, pushMessage } from './store'
import type { MessageOptions, MessagePosition } from './types'

export type { MessageOptions, MessagePosition, MessageType } from './types'
export { default as MacNotificationHost } from './MacNotificationHost.vue'

function open(options: MessageOptions) {
  return pushMessage(options, options.type ?? 'info')
}

export const Message = {
  open,
  success(options: MessageOptions | string) {
    return pushMessage(options, 'success')
  },
  error(options: MessageOptions | string) {
    return pushMessage(options, 'error')
  },
  warning(options: MessageOptions | string) {
    return pushMessage(options, 'warning')
  },
  info(options: MessageOptions | string) {
    return pushMessage(options, 'info')
  },
  close(id: number) {
    dismissMessage(id)
  },
  clear(position?: MessagePosition) {
    clearMessages(position)
  },
}

export default Message
