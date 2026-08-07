<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { MaxSvg } from '@/components/maxSvg'
import MaxSvgGrid from './MaxSvgGrid.vue'

defineOptions({ inheritAttrs: false })

const model = defineModel<string>({ default: '' })

withDefaults(
  defineProps<{
    label?: string
    id?: string
    placeholder?: string
    columns?: number
    iconSize?: number
  }>(),
  {
    placeholder: '选择图标',
    columns: 6,
    iconSize: 28,
  },
)

const emit = defineEmits<{
  change: [value: string]
}>()

const open = ref(false)
const rootRef = ref<HTMLElement | null>(null)

function togglePanel() {
  open.value = !open.value
}

function closePanel() {
  open.value = false
}

function onSelect(name: string) {
  model.value = name
  emit('change', name)
  closePanel()
}

function onPointerDownOutside(event: MouseEvent) {
  if (!open.value || !rootRef.value) return
  if (!rootRef.value.contains(event.target as Node)) {
    closePanel()
  }
}

onMounted(() => {
  document.addEventListener('mousedown', onPointerDownOutside, true)
})

onUnmounted(() => {
  document.removeEventListener('mousedown', onPointerDownOutside, true)
})
</script>

<template>
  <div
    ref="rootRef"
    class="max-svg-picker"
    :class="{
      'max-svg-picker--labeled': !!label,
      'max-svg-picker--open': open,
    }"
  >
    <label v-if="label" class="max-svg-picker__label" :for="id">{{ label }}</label>

    <div class="max-svg-picker__field">
      <button
        :id="id"
        type="button"
        class="max-svg-picker__trigger"
        :class="{ 'max-svg-picker__trigger--open': open }"
        v-bind="$attrs"
        @click.stop="togglePanel"
      >
        <MaxSvg v-if="model" :name="model" :size="28" />
        <span v-else class="max-svg-picker__placeholder">{{ placeholder }}</span>
      </button>

      <div v-if="open" class="max-svg-picker__panel">
        <span class="max-svg-picker__caret" aria-hidden="true" />
        <MaxSvgGrid
          v-model="model"
          :columns="columns"
          :icon-size="iconSize"
          @update:model-value="onSelect"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.max-svg-picker {
  position: relative;
}

.max-svg-picker--labeled {
  display: grid;
  grid-template-columns: 80px 1fr;
  gap: 12px;
  align-items: start;
}

.max-svg-picker__label {
  padding-top: 10px;
  color: rgba(255, 255, 255, 0.78);
  font-size: 14px;
  font-weight: 500;
  text-align: right;
}

.max-svg-picker--open {
  position: relative;
  z-index: 20;
}

.max-svg-picker__field {
  position: relative;
}

.max-svg-picker--open .max-svg-picker__field {
  z-index: 1;
}

.max-svg-picker__trigger {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  min-height: 38px;
  padding: 0 12px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  transition:
    border-color 0.18s ease,
    background 0.18s ease,
    box-shadow 0.18s ease;
}

.max-svg-picker__trigger:hover,
.max-svg-picker__trigger--open {
  border-color: rgba(10, 132, 255, 0.65);
  background: rgba(255, 255, 255, 0.12);
  box-shadow: 0 0 0 3px rgba(10, 132, 255, 0.18);
}

.max-svg-picker__placeholder {
  color: rgba(255, 255, 255, 0.42);
}

.max-svg-picker__value {
  color: rgba(255, 255, 255, 0.88);
  font-size: 13px;
}

.max-svg-picker__panel {
  position: absolute;
  top: calc(100% + 10px);
  left: 0;
  z-index: 50;
  width: min(100%, 320px);
}

.max-svg-picker__caret {
  position: absolute;
  top: -5px;
  left: 50%;
  z-index: 2;
  width: 10px;
  height: 10px;
  margin-left: -5px;
  background: rgba(28, 28, 30, 0.96);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-right-color: transparent;
  border-bottom-color: transparent;
  border-radius: 2px 0 0 0;
  transform: rotate(45deg);
  box-shadow:
    -1px -1px 0 rgba(255, 255, 255, 0.04),
    0 -2px 6px rgba(0, 0, 0, 0.18);
}

.max-svg-picker__panel :deep(.max-svg-grid) {
  position: relative;
  z-index: 1;
}
</style>
