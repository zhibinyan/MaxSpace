import { cancelMaxPopupAction, closeMaxPopup, confirmMaxPopupAction, openMaxPopup } from './store'
import type { MaxPopupOptions } from './types'

export type { MaxPopupDirection, MaxPopupItem, MaxPopupOptions, MaxPopupSize } from './types'
export { default as MaxPopupHost } from './MaxPopupHost.vue'
export { MAX_POPUP_ANIMATION_MS } from './store'

/** 表单弹窗：顶栏固定，body 放 content 组件 */
export const MaxPopup = {
  open(options: MaxPopupOptions) {
    return openMaxPopup(options)
  },
  close(confirmed = false) {
    closeMaxPopup(confirmed)
  },
  confirmAction() {
    return confirmMaxPopupAction()
  },
  cancelAction() {
    return cancelMaxPopupAction()
  },
}

export default MaxPopup
