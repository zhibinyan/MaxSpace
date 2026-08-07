import { nextTick, onActivated, onDeactivated, onMounted, onUnmounted, ref } from 'vue'
import { LAYOUT_TOOLBAR_TELEPORT_ID } from './layoutToolbar'

/** Teleport 到 AdminLayout 地址栏；配合 KeepAlive / 书页切换，避免 emitsOptions 报错 */
export function useLayoutToolbarTeleport() {
  const toolbarTeleportReady = ref(false)

  function enable() {
    void nextTick(() => {
      toolbarTeleportReady.value = !!document.getElementById(LAYOUT_TOOLBAR_TELEPORT_ID)
    })
  }

  function disable() {
    toolbarTeleportReady.value = false
  }

  onMounted(enable)
  onActivated(enable)
  onDeactivated(disable)
  onUnmounted(disable)

  return { toolbarTeleportReady }
}
