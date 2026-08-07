<script setup lang="ts">
import { computed, onMounted, onUnmounted, watch } from 'vue'
import { MaxButton } from '@/components/maxButton'
import { MAX_CONFIRM_ANIMATION_MS, closeMaxConfirm, maxConfirmState } from './store'

const item = computed(() => maxConfirmState.current)
const show = computed(() => !!item.value)

function onKeydown(e: KeyboardEvent) {
  if (!show.value || item.value?.leaving) return
  if (e.key === 'Escape') {
    e.preventDefault()
    closeMaxConfirm(false)
  } else if (e.key === 'Enter') {
    e.preventDefault()
    closeMaxConfirm(true)
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
      class="max-confirm-root"
      :class="{
        'max-confirm-root--visible': item.visible,
        'max-confirm-root--leaving': item.leaving,
      }"
    >
      <div class="max-confirm-overlay" @click.self="closeMaxConfirm(false)" />

      <div
        class="max-confirm-panel"
        :class="[
          `max-confirm-panel--${item.size}`,
          `max-confirm-panel--from-${item.direction}`,
          {
            'max-confirm-panel--visible': item.visible,
            'max-confirm-panel--leaving': item.leaving,
          },
        ]"
        role="alertdialog"
        aria-modal="true"
        :aria-label="item.title"
        :style="{ '--max-confirm-duration': `${MAX_CONFIRM_ANIMATION_MS}ms` }"
        @click.stop
      >
        <header class="max-confirm-header">
          <div class="max-confirm-header__left">
            <button
              type="button"
              class="max-confirm-light max-confirm-light--red"
              title="关闭"
              @click="closeMaxConfirm(false)"
            >
              <svg viewBox="0 0 8 8" aria-hidden="true">
                <path d="M2 2l4 4M6 2L2 6" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" />
              </svg>
            </button>
          </div>

          <div class="max-confirm-header__title">{{ item.title }}</div>
        </header>

        <div class="max-confirm-body">
          <p class="max-confirm-message">{{ item.message }}</p>
        </div>

        <footer class="max-confirm-footer">
          <div class="max-confirm-footer__actions">
            <MaxButton variant="ghost" @click="closeMaxConfirm(false)">
              {{ item.cancelText }}
            </MaxButton>
            <MaxButton
              :variant="item.danger ? 'danger' : 'primary'"
              @click="closeMaxConfirm(true)"
            >
              {{ item.confirmText }}
            </MaxButton>
          </div>
        </footer>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.max-confirm-root {
  position: fixed;
  inset: 0;
  z-index: 10001;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.max-confirm-root--visible {
  pointer-events: auto;
}

.max-confirm-overlay {
  position: absolute;
  inset: 0;
  background: rgba(8, 12, 20, 0.48);
  opacity: 0;
  transition: opacity var(--max-confirm-duration, 380ms) ease;
}

.max-confirm-root--visible .max-confirm-overlay {
  opacity: 1;
}

.max-confirm-root--leaving .max-confirm-overlay {
  opacity: 0;
}

.max-confirm-panel {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  max-height: min(88vh, 360px);
  width: min(92vw, 420px);
  border-radius: 16px;
  overflow: hidden;
  background: rgba(28, 32, 40, 0.78);
  backdrop-filter: blur(28px) saturate(160%);
  -webkit-backdrop-filter: blur(28px) saturate(160%);
  border: 1px solid rgba(255, 255, 255, 0.14);
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.38);
  opacity: 0;
  transition:
    transform var(--max-confirm-duration, 380ms) cubic-bezier(0.22, 1, 0.36, 1),
    opacity calc(var(--max-confirm-duration, 380ms) * 0.85) ease;
}

.max-confirm-panel--from-top {
  transform: translate3d(0, -56px, 0) scale(0.96);
}

.max-confirm-panel--from-bottom {
  transform: translate3d(0, 56px, 0) scale(0.96);
}

.max-confirm-panel--from-left {
  transform: translate3d(-56px, 0, 0) scale(0.96);
}

.max-confirm-panel--from-right {
  transform: translate3d(56px, 0, 0) scale(0.96);
}

.max-confirm-panel--visible:not(.max-confirm-panel--leaving) {
  opacity: 1;
  transform: translate3d(0, 0, 0) scale(1);
}

.max-confirm-panel--leaving.max-confirm-panel--from-top {
  opacity: 0;
  transform: translate3d(0, -56px, 0) scale(0.96);
}

.max-confirm-panel--leaving.max-confirm-panel--from-bottom {
  opacity: 0;
  transform: translate3d(0, 56px, 0) scale(0.96);
}

.max-confirm-panel--leaving.max-confirm-panel--from-left {
  opacity: 0;
  transform: translate3d(-56px, 0, 0) scale(0.96);
}

.max-confirm-panel--leaving.max-confirm-panel--from-right {
  opacity: 0;
  transform: translate3d(56px, 0, 0) scale(0.96);
}

.max-confirm-header {
  position: relative;
  z-index: 2;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  min-height: 56px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.04);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.max-confirm-header__left {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
}

.max-confirm-header__title {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  max-width: calc(100% - 48px);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: rgba(255, 255, 255, 0.92);
  font-size: 16px;
  font-weight: 500;
  letter-spacing: 0.01em;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  pointer-events: none;
}

.max-confirm-light {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 0.5px solid transparent;
  flex-shrink: 0;
}

.max-confirm-light svg {
  width: 8px;
  height: 8px;
  opacity: 0;
  transition: opacity 0.12s ease;
}

.max-confirm-header__left:hover .max-confirm-light svg {
  opacity: 1;
}

.max-confirm-light--red {
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #ff5f57;
  border-color: #e0443e;
  color: #4d0000;
  cursor: pointer;
}

.max-confirm-body {
  flex: 1;
  min-height: 0;
  overflow: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  text-align: center;
}

.max-confirm-message {
  margin: 0;
  color: rgba(255, 255, 255, 0.82);
  font-size: 15px;
  line-height: 1.55;
  font-weight: 500;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.18);
}

.max-confirm-footer {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 64px;
  padding: 16px 24px;
  background: rgba(255, 255, 255, 0.02);
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.max-confirm-footer__actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}
</style>
