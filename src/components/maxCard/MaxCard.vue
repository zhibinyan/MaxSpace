<script setup lang="ts">
import type { MaxCardShadow } from './types'

defineOptions({ inheritAttrs: false })

withDefaults(
  defineProps<{
    span?: number
    shadow?: MaxCardShadow
  }>(),
  {
    span: 6,
    shadow: 'hover',
  },
)
</script>

<template>
  <div
    class="max-card"
    :class="[
      `max-card--shadow-${shadow}`,
      { 'max-card--hoverable': shadow === 'hover' },
    ]"
    :style="{ gridColumn: `span ${span}` }"
    v-bind="$attrs"
  >
    <div v-if="$slots.header" class="max-card__header">
      <slot name="header" />
    </div>
    <div class="max-card__body">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.max-card {
  position: relative;
  min-width: 0;
  display: flex;
  flex-direction: column;
  --max-text: #ffffff;
  --max-head-text: rgba(255, 255, 255, 0.96);
  --max-muted-text: rgba(255, 255, 255, 0.62);
  --max-font-size: 16px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(24px) saturate(160%);
  -webkit-backdrop-filter: blur(24px) saturate(160%);
  border: 1px solid rgba(255, 255, 255, 0.22);
  overflow: hidden;
  color: var(--max-text);
  font-size: var(--max-font-size);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  transition:
    border-color 0.22s ease,
    box-shadow 0.22s ease;
}

.max-card--shadow-always {
  box-shadow:
    0 0 0 0.5px rgba(255, 255, 255, 0.08),
    0 12px 40px rgba(0, 0, 0, 0.12);
}

.max-card--shadow-hover {
  box-shadow:
    0 0 0 0.5px rgba(255, 255, 255, 0.06),
    0 4px 16px rgba(0, 0, 0, 0.08);
}

.max-card--hoverable:hover {
  border-color: rgba(255, 255, 255, 0.36);
  box-shadow:
    0 0 0 0.5px rgba(255, 255, 255, 0.1),
    0 16px 48px rgba(0, 0, 0, 0.16);
}

.max-card--shadow-never {
  box-shadow: none;
}

.max-card__header {
  flex-shrink: 0;
  padding: 14px 16px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.18);
  color: var(--max-head-text);
  font-size: var(--max-font-size);
  font-weight: 500;
  letter-spacing: 0.03em;
  text-shadow:
    0 0 1px rgba(0, 0, 0, 0.45),
    0 1px 3px rgba(0, 0, 0, 0.28);
}

.max-card__body {
  flex: 1;
  min-height: 0;
  padding: 16px;
  color: var(--max-text);
  font-weight: 700;
  text-shadow:
    0 0 1px rgba(0, 0, 0, 0.5),
    0 1px 4px rgba(0, 0, 0, 0.32);
}

.max-card__header :deep(*),
.max-card__body :deep(*) {
  color: inherit;
  font-weight: inherit;
}

.max-card__body :deep(.el-empty__description),
.max-card__body :deep(.el-timeline-item__timestamp) {
  color: var(--max-muted-text);
  font-weight: 500;
  text-shadow:
    0 0 1px rgba(0, 0, 0, 0.45),
    0 1px 3px rgba(0, 0, 0, 0.28);
}

.max-card__body :deep(.el-timeline-item__node) {
  background: rgba(255, 255, 255, 0.42);
}

.max-card__body :deep(.el-timeline-item__tail) {
  border-left-color: rgba(255, 255, 255, 0.22);
}
</style>
