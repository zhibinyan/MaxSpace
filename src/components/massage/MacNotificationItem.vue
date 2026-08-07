<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { MessageItem } from './types'

const props = defineProps<{
  item: MessageItem
}>()

const emit = defineEmits<{
  close: [id: number]
  removed: [id: number]
}>()

const visible = ref(false)

const iconPaths: Record<MessageItem['type'], string> = {
  success: 'M6.5 10.5L3.5 7.5L4.5 6.5L6.5 8.5L11.5 3.5L12.5 4.5L6.5 10.5Z',
  error: 'M4.5 4.5L11.5 11.5M11.5 4.5L4.5 11.5',
  warning: 'M8 3.5L13.5 12.5H2.5L8 3.5ZM8 6V9M8 11V11.5',
  info: 'M8 7V11M8 5V5.5',
}

onMounted(() => {
  requestAnimationFrame(() => {
    visible.value = true
  })
})

function onTransitionEnd(e: TransitionEvent) {
  if (e.propertyName !== 'transform' && e.propertyName !== 'opacity') return
  if (props.item.leaving) {
    emit('removed', props.item.id)
  }
}

function handleClose() {
  emit('close', props.item.id)
}
</script>

<template>
  <article
    class="mac-notification"
    :class="[
      `mac-notification--${item.type}`,
      `mac-notification--${item.position}`,
      { 'mac-notification--visible': visible, 'mac-notification--leaving': item.leaving },
    ]"
    role="alert"
    @transitionend="onTransitionEnd"
    @click="handleClose"
  >
    <div class="mac-notification__icon" aria-hidden="true">
      <svg viewBox="0 0 16 16">
        <path
          :d="iconPaths[item.type]"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </div>
    <div class="mac-notification__body">
      <div class="mac-notification__title">{{ item.title }}</div>
      <div class="mac-notification__message">{{ item.message }}</div>
    </div>
  </article>
</template>

<style scoped>
.mac-notification {
  display: flex;
  align-items: center;
  gap: 12px;
  width: min(360px, calc(100vw - 32px));
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(28px) saturate(180%);
  -webkit-backdrop-filter: blur(28px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.55);
  box-shadow:
    0 0 0 0.5px rgba(0, 0, 0, 0.06),
    0 10px 32px rgba(0, 0, 0, 0.14),
    0 2px 8px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  opacity: 0;
  transform: translate3d(0, 0, 0);
  transition:
    transform 0.52s cubic-bezier(0.22, 1, 0.36, 1),
    opacity 0.42s ease;
  will-change: transform, opacity;
}

.mac-notification--top-right {
  transform: translate3d(calc(100% + 24px), 0, 0);
}

.mac-notification--top-center {
  transform: translate3d(0, calc(-100% - 20px), 0);
}

.mac-notification--top-right.mac-notification--visible:not(.mac-notification--leaving) {
  opacity: 1;
  transform: translate3d(0, 0, 0);
}

.mac-notification--top-center.mac-notification--visible:not(.mac-notification--leaving) {
  opacity: 1;
  transform: translate3d(0, 0, 0);
}

.mac-notification--top-right.mac-notification--leaving {
  opacity: 0;
  transform: translate3d(calc(100% + 24px), 0, 0);
}

.mac-notification--top-center.mac-notification--leaving {
  opacity: 0;
  transform: translate3d(0, calc(-100% - 20px), 0);
}

.mac-notification__icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.mac-notification__icon svg {
  width: 18px;
  height: 18px;
}

.mac-notification--success .mac-notification__icon {
  background: linear-gradient(180deg, #3ddc68 0%, #28c840 100%);
}

.mac-notification--error .mac-notification__icon {
  background: linear-gradient(180deg, #ff6961 0%, #ff453a 100%);
}

.mac-notification--warning .mac-notification__icon {
  background: linear-gradient(180deg, #ffb340 0%, #ff9f0a 100%);
}

.mac-notification--info .mac-notification__icon {
  background: linear-gradient(180deg, #409cff 0%, #0a84ff 100%);
}

.mac-notification__body {
  min-width: 0;
  flex: 1;
}

.mac-notification__title {
  font-size: 13px;
  font-weight: 600;
  line-height: 1.3;
  color: rgba(0, 0, 0, 0.88);
  letter-spacing: -0.01em;
}

.mac-notification__message {
  margin-top: 2px;
  font-size: 13px;
  line-height: 1.35;
  color: rgba(0, 0, 0, 0.62);
  word-break: break-word;
}
</style>
