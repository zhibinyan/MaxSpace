import { closeMaxConfirm, openMaxConfirm, openMaxDeleteConfirm } from './store'
import type { MaxConfirmOptions, MaxDeleteConfirmOptions } from './types'

export type {
  MaxConfirmDirection,
  MaxConfirmItem,
  MaxConfirmOptions,
  MaxConfirmSize,
  MaxDeleteConfirmOptions,
} from './types'
export { default as MaxConfirmHost } from './MaxConfirmHost.vue'
export { MAX_CONFIRM_ANIMATION_MS } from './store'

/** 删除 / 二次确认弹窗：正文提示 + 底部按钮 */
export const MaxConfirm = {
  open(options: MaxConfirmOptions) {
    return openMaxConfirm(options, false)
  },
  /** 删除确认：红色删除按钮 */
  delete(options: MaxDeleteConfirmOptions | string) {
    if (typeof options === 'string') {
      return openMaxDeleteConfirm({ message: options })
    }
    return openMaxDeleteConfirm(options)
  },
  close(confirmed = false) {
    closeMaxConfirm(confirmed)
  },
}

export default MaxConfirm
