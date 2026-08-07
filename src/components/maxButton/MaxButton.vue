<script setup lang="ts">
import type { MaxButtonNativeType, MaxButtonSize, MaxButtonVariant } from './types'

defineOptions({ inheritAttrs: false })

withDefaults(
  defineProps<{
    variant?: MaxButtonVariant
    size?: MaxButtonSize
    nativeType?: MaxButtonNativeType
    disabled?: boolean
    loading?: boolean
    loadingText?: string
    block?: boolean
  }>(),
  {
    variant: 'ghost',
    size: 'md',
    nativeType: 'button',
    disabled: false,
    loading: false,
    loadingText: '提交中…',
    block: false,
  },
)

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()
</script>

<template>
  <button
    class="max-button"
    :class="[
      `max-button--${variant}`,
      `max-button--${size}`,
      { 'max-button--block': block, 'max-button--loading': loading },
    ]"
    :type="nativeType"
    :disabled="disabled || loading"
    v-bind="$attrs"
    @click="emit('click', $event)"
  >
    <slot v-if="!loading" />
    <template v-else>{{ loadingText }}</template>
  </button>
</template>

<style scoped>
.max-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  border: 1px solid transparent;
  font-weight: 500;
  white-space: nowrap;
  cursor: pointer;
  transition:
    background 0.18s ease,
    border-color 0.18s ease,
    color 0.18s ease,
    transform 0.18s ease,
    opacity 0.18s ease,
    box-shadow 0.18s ease;
}

.max-button--sm {
  min-width: 56px;
  height: 28px;
  padding: 0 12px;
  font-size: 13px;
}

.max-button--md {
  min-width: 72px;
  height: 34px;
  padding: 0 16px;
  font-size: 14px;
}

.max-button--lg {
  min-width: 88px;
  height: 40px;
  padding: 0 20px;
  font-size: 15px;
}

.max-button--block {
  display: flex;
  width: 100%;
}

.max-button:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.max-button:active:not(:disabled) {
  transform: scale(0.98);
}

.max-button--ghost {
  color: rgba(255, 255, 255, 0.88);
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.16);
}

.max-button--ghost:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.24);
}

.max-button--primary {
  color: #fff;
  background: #0a84ff;
  border-color: rgba(10, 132, 255, 0.85);
  box-shadow: 0 4px 14px rgba(10, 132, 255, 0.28);
}

.max-button--primary:hover:not(:disabled) {
  background: #409cff;
}

.max-button--danger {
  color: #fff;
  background: #ff453a;
  border-color: rgba(255, 69, 58, 0.85);
  box-shadow: 0 4px 14px rgba(255, 69, 58, 0.24);
}

.max-button--danger:hover:not(:disabled) {
  background: #ff6961;
}

.max-button--text {
  min-width: auto;
  height: auto;
  padding: 6px 10px;
  color: rgba(255, 255, 255, 0.82);
  background: transparent;
  border-color: transparent;
}

.max-button--text:hover:not(:disabled) {
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
}

.max-button--link,
.max-button--link-danger {
  min-width: auto;
  height: auto;
  padding: 4px 8px;
  background: transparent;
  border-color: transparent;
  box-shadow: none;
}

.max-button--link {
  color: #409cff;
}

.max-button--link:hover:not(:disabled) {
  color: #66b0ff;
  background: rgba(10, 132, 255, 0.12);
}

.max-button--link-danger {
  color: #ff6961;
}

.max-button--link-danger:hover:not(:disabled) {
  color: #ff8a82;
  background: rgba(255, 69, 58, 0.12);
}

.max-button--loading {
  cursor: wait;
}
</style>
