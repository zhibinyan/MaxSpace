<script setup lang="ts">
import { LAYOUT_TOOLBAR_TELEPORT_TARGET } from './layoutToolbar'
import { useLayoutToolbarTeleport } from './useLayoutToolbarTeleport'
import { MaxButton } from '@/components/maxButton'
const { toolbarTeleportReady } = useLayoutToolbarTeleport()
</script>

<template>
  <div>
  
  <Teleport v-if="toolbarTeleportReady" defer :to="LAYOUT_TOOLBAR_TELEPORT_TARGET">
    <div class="layout-toolbar">
      <div class="layout-toolbar-left">
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
