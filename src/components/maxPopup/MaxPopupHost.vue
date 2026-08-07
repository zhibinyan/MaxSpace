<script setup lang="ts">
import { computed, onMounted, onUnmounted, watch } from 'vue'
import { MaxButton } from '@/components/maxButton'
import {
  MAX_POPUP_ANIMATION_MS,
  cancelMaxPopupAction,
  confirmMaxPopupAction,
  maxPopupState,
} from './store'

const item = computed(() => maxPopupState.current)
const show = computed(() => !!item.value)

function onKeydown(e: KeyboardEvent) {
  if (!show.value || item.value?.leaving || item.value?.confirming) return
  if (e.key === 'Escape') {
    e.preventDefault()
    cancelMaxPopupAction()
  }
}

function onOverlayClick() {
  if (item.value?.showCancel) {
    cancelMaxPopupAction()
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
})

watch(show, (visible) => {
  document.body.style.overflow = visible ? 'hidden' : ''
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="item"
      class="max-popup-root"
      :class="{
        'max-popup-root--visible': item.visible,
        'max-popup-root--leaving': item.leaving,
      }"
    >
      <div class="max-popup-overlay" @click.self="onOverlayClick" />

      <div
        class="max-popup-panel"
        :class="[
          `max-popup-panel--${item.size}`,
          `max-popup-panel--from-${item.direction}`,
          {
            'max-popup-panel--visible': item.visible,
            'max-popup-panel--leaving': item.leaving,
          },
        ]"
        role="dialog"
        aria-modal="true"
        :aria-label="item.title"
        :style="{ '--max-popup-duration': `${MAX_POPUP_ANIMATION_MS}ms` }"
        @click.stop
      >
        <header class="max-popup-header">
          <div class="max-popup-header__left">
            <div class="max-popup-lights" aria-hidden="true">
              <button
                type="button"
                class="max-popup-light max-popup-light--red"
                title="关闭"
                @click="cancelMaxPopupAction"
              >
                <svg viewBox="0 0 8 8" aria-hidden="true">
                  <path d="M2 2l4 4M6 2L2 6" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" />
                </svg>
              </button>
              <span class="max-popup-light max-popup-light--yellow" />
              <span class="max-popup-light max-popup-light--green" />
            </div>
          </div>

          <div class="max-popup-header__title">{{ item.title }}</div>

          <div class="max-popup-header__actions">
            <MaxButton
              v-if="item.showCancel"
              variant="ghost"
              :disabled="item.confirming"
              @click="cancelMaxPopupAction"
            >
              {{ item.cancelText }}
            </MaxButton>
            <MaxButton
              variant="primary"
              :loading="item.confirming"
              @click="confirmMaxPopupAction"
            >
              {{ item.confirmText }}
            </MaxButton>
          </div>
        </header>

        <div v-if="item.content" class="max-popup-body">
          <component :is="item.content" v-bind="item.contentProps ?? {}" />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.max-popup-root {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.max-popup-root--visible {
  pointer-events: auto;
}

.max-popup-overlay {
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity var(--max-popup-duration, 420ms) ease;
}

.max-popup-root--visible .max-popup-overlay {
  opacity: 1;
}

.max-popup-root--leaving .max-popup-overlay {
  opacity: 0;
}

.max-popup-panel {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  max-height: min(88vh, 720px);
  border-radius: 16px;
  overflow: hidden;
  background: rgba(28, 32, 40, 0.1);
  backdrop-filter: blur(28px) saturate(160%);
  -webkit-backdrop-filter: blur(28px) saturate(160%);
  border: 1px solid rgba(255, 255, 255, 0.14);
  box-shadow:
    0 0 0 0.5px rgba(255, 255, 255, 0.08),
    0 24px 64px rgba(0, 0, 0, 0.38);
  opacity: 0;
  transition:
    transform var(--max-popup-duration, 420ms) cubic-bezier(0.22, 1, 0.36, 1),
    opacity calc(var(--max-popup-duration, 420ms) * 0.85) ease;
}

.max-popup-panel--sm {
  width: min(92vw, 400px);
}

.max-popup-panel--md {
  width: min(92vw, 560px);
}

.max-popup-panel--lg {
  width: min(92vw, 760px);
}

.max-popup-panel--from-top {
  transform: translate3d(0, -72px, 0) scale(0.96);
}

.max-popup-panel--from-bottom {
  transform: translate3d(0, 72px, 0) scale(0.96);
}

.max-popup-panel--from-left {
  transform: translate3d(-72px, 0, 0) scale(0.96);
}

.max-popup-panel--from-right {
  transform: translate3d(72px, 0, 0) scale(0.96);
}

.max-popup-panel--visible:not(.max-popup-panel--leaving) {
  opacity: 1;
  transform: translate3d(0, 0, 0) scale(1);
}

.max-popup-panel--leaving.max-popup-panel--from-top {
  opacity: 0;
  transform: translate3d(0, -72px, 0) scale(0.96);
}

.max-popup-panel--leaving.max-popup-panel--from-bottom {
  opacity: 0;
  transform: translate3d(0, 72px, 0) scale(0.96);
}

.max-popup-panel--leaving.max-popup-panel--from-left {
  opacity: 0;
  transform: translate3d(-72px, 0, 0) scale(0.96);
}

.max-popup-panel--leaving.max-popup-panel--from-right {
  opacity: 0;
  transform: translate3d(72px, 0, 0) scale(0.96);
}

.max-popup-header {
  position: sticky;
  top: 0;
  z-index: 2;
  flex-shrink: 0;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 12px;
  min-height: 56px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.04);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.max-popup-header__left {
  display: flex;
  align-items: center;
}

.max-popup-header__title {
  justify-self: center;
  max-width: 240px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: rgba(255, 255, 255, 0.92);
  font-size: 16px;
  font-weight: 500;
  letter-spacing: 0.01em;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.max-popup-header__actions {
  justify-self: end;
  display: flex;
  align-items: center;
  gap: 10px;
}

.max-popup-lights {
  display: flex;
  align-items: center;
  gap: 8px;
}

.max-popup-light {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 0.5px solid transparent;
  flex-shrink: 0;
}

.max-popup-light svg {
  width: 8px;
  height: 8px;
  opacity: 0;
  transition: opacity 0.12s ease;
}

.max-popup-lights:hover .max-popup-light svg {
  opacity: 1;
}

.max-popup-light--red {
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #ff5f57;
  border-color: #e0443e;
  color: #4d0000;
  cursor: pointer;
}

.max-popup-light--yellow {
  background: #febc2e;
  border-color: #dea123;
}

.max-popup-light--green {
  background: #28c840;
  border-color: #1aab29;
}

.max-popup-body {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 20px 24px 24px;
}
</style>
