<script setup lang="ts">
import { nextTick, onUnmounted, ref, watch } from 'vue'
import { LAYOUT_TOOLBAR_TELEPORT_TARGET } from './layoutToolbar'
import { useLayoutToolbarTeleport } from './useLayoutToolbarTeleport'
import { MaxButton } from '@/components/maxButton'

const { toolbarTeleportReady } = useLayoutToolbarTeleport()
const leftRef = ref<HTMLElement | null>(null)

/** 鼠标滚轮横向滚动工具栏左侧 */
function onLeftWheel(e: WheelEvent) {
  const el = leftRef.value
  if (!el) return
  const delta = Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX : e.deltaY
  if (!delta) return
  if (el.scrollWidth <= el.clientWidth) return
  e.preventDefault()
  el.scrollLeft += delta
}

watch(
  [toolbarTeleportReady, leftRef],
  async ([ready], _, onCleanup) => {
    if (!ready) return
    await nextTick()
    const el = leftRef.value
    if (!el) return
    el.addEventListener('wheel', onLeftWheel, { passive: false })
    onCleanup(() => {
      el.removeEventListener('wheel', onLeftWheel)
    })
  },
  { flush: 'post' },
)

onUnmounted(() => {
  leftRef.value?.removeEventListener('wheel', onLeftWheel)
})
</script>

<template>
  <div>
    <Teleport v-if="toolbarTeleportReady" defer :to="LAYOUT_TOOLBAR_TELEPORT_TARGET">
      <div class="layout-toolbar">
        <div ref="leftRef" class="layout-toolbar-left">
          <slot name="left" />
        </div>
        <div class="layout-toolbar-right">
          <slot name="right" />
          <MaxButton title="展开">展开</MaxButton>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.layout-toolbar {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  width: 100%;
  height: 44px;
  min-width: 0;
  overflow: hidden;
}

.layout-toolbar-left {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 10px;
  flex-wrap: nowrap;
  overflow-x: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.layout-toolbar-left::-webkit-scrollbar {
  display: none;
}

.layout-toolbar-left :deep(> *) {
  flex: 0 0 auto;
  width: 160px;
}

.layout-toolbar-left :deep(.max-input) {
  width: 160px;
  align-self: center;
}

.layout-toolbar-left :deep(.max-input__control) {
  height: 30px;
}

.layout-toolbar-left :deep(.max-select) {
  width: 160px;
  align-self: center;
}

.layout-toolbar-left :deep(.max-select__control) {
  height: 30px;
}

.layout-toolbar-right {
  display: flex;
  flex-shrink: 0;
  gap: 10px;
  flex-wrap: nowrap;
  align-items: center;
}
</style>
