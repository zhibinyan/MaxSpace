<script setup lang="ts">
import { computed } from 'vue'
import MacNotificationItem from './MacNotificationItem.vue'
import { dismissMessage, messageState, removeMessage } from './store'
import type { MessagePosition } from './types'

const positions: MessagePosition[] = ['top-right', 'top-center']

const grouped = computed(() => ({
  'top-right': messageState.items.filter((item) => item.position === 'top-right'),
  'top-center': messageState.items.filter((item) => item.position === 'top-center'),
}))

function onClose(id: number) {
  dismissMessage(id)
}

function onRemoved(id: number) {
  removeMessage(id)
}
</script>

<template>
  <div class="mac-notification-layer" aria-live="polite" aria-relevant="additions">
    <section
      v-for="position in positions"
      :key="position"
      class="mac-notification-stack"
      :class="`mac-notification-stack--${position}`"
    >
      <MacNotificationItem
        v-for="item in grouped[position]"
        :key="item.id"
        :item="item"
        @close="onClose"
        @removed="onRemoved"
      />
    </section>
  </div>
</template>

<style scoped>
.mac-notification-layer {
  position: fixed;
  inset: 0;
  z-index: 9999;
  pointer-events: none;
}

.mac-notification-stack {
  position: fixed;
  display: flex;
  flex-direction: column;
  gap: 10px;
  pointer-events: none;
}

.mac-notification-stack--top-right {
  top: 40px;
  right: 16px;
  align-items: flex-end;
}

.mac-notification-stack--top-center {
  top: 40px;
  left: 50%;
  transform: translateX(-50%);
  align-items: center;
}

.mac-notification-stack :deep(.mac-notification) {
  pointer-events: auto;
}
</style>
