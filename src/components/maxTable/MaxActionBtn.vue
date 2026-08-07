<script setup lang="ts">
export type MaxActionIcon = 'edit' | 'delete'

withDefaults(
  defineProps<{
    title?: string
    disabled?: boolean
    icon?: MaxActionIcon
  }>(),
  {
    title: '',
    disabled: false,
  },
)

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()
</script>

<template>
  <button
    type="button"
    class="max-action-btn"
    :title="title"
    :disabled="disabled"
    @click="emit('click', $event)"
  >
    <slot>
      <svg v-if="icon === 'edit'" viewBox="0 0 16 16" aria-hidden="true">
        <path
          d="M11.5 2.5l2 2L6 12H4v-2l7.5-7.5z"
          fill="none"
          stroke="currentColor"
          stroke-width="1.3"
          stroke-linejoin="round"
        />
      </svg>
      <svg v-else-if="icon === 'delete'" viewBox="0 0 16 16" aria-hidden="true">
        <path
          d="M3.5 5.5h9M6 5.5V4h4v1.5M5.5 5.5l.5 7h4.5l.5-7"
          fill="none"
          stroke="currentColor"
          stroke-width="1.3"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </slot>
  </button>
</template>

<style scoped>
.max-action-btn {
  width: 28px;
  height: 28px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.22);
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.82);
  cursor: pointer;
  transition:
    background 0.18s ease,
    border-color 0.18s ease,
    color 0.18s ease,
    transform 0.18s ease;
}

.max-action-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.18);
  border-color: rgba(255, 255, 255, 0.34);
  color: #fff;
}

.max-action-btn:active:not(:disabled) {
  transform: scale(0.96);
}

.max-action-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.max-action-btn :deep(svg) {
  width: 14px;
  height: 14px;
  display: block;
}
</style>
