<script setup lang="ts">
import { computed } from 'vue'
import type { MaxSelectOption } from './types'

defineOptions({ inheritAttrs: false })

const model = defineModel<string | number | null>({ default: null })

const props = withDefaults(
  defineProps<{
    label?: string
    id?: string
    options: MaxSelectOption[]
    /** 组件总宽度，如 280 或 '280px'；不传则默认 100% */
    width?: number | string
  }>(),
  {
    label: '',
  },
)

const hasLabel = computed(() => !!props.label?.trim())

const rootStyle = computed(() => {
  if (props.width == null || props.width === '') return undefined
  const w = typeof props.width === 'number' ? `${props.width}px` : props.width
  return { width: w }
})

function serializeValue(value: string | number | null | undefined) {
  return value === null || value === undefined ? '' : String(value)
}

function onChange(event: Event) {
  const raw = (event.target as HTMLSelectElement).value
  const matched = props.options.find((option) => serializeValue(option.value) === raw)
  model.value = matched ? matched.value : raw
}
</script>

<template>
  <div class="max-select" :class="{ 'max-select--no-label': !hasLabel }" :style="rootStyle">
    <label class="max-select__label" :for="id">{{ label }}</label>
    <select
      :id="id"
      class="max-select__control"
      :value="serializeValue(model)"
      v-bind="$attrs"
      @change="onChange"
    >
      <option
        v-for="option in options"
        :key="serializeValue(option.value)"
        :value="serializeValue(option.value)"
      >
        {{ option.label }}
      </option>
    </select>
  </div>
</template>

<style scoped>
.max-select {
  display: grid;
  grid-template-columns: 80px 1fr;
  gap: 12px;
  align-items: center;
  width: 100%;
  min-width: 0;
}

.max-select--no-label {
  grid-template-columns: 0px 1fr;
  gap: 0;
}

.max-select--no-label .max-select__label {
  overflow: hidden;
  padding: 0;
}

.max-select__label {
  color: rgba(255, 255, 255, 0.78);
  font-size: 14px;
  font-weight: 500;
  text-align: right;
}

.max-select__control {
  width: 100%;
  height: 38px;
  padding: 0 12px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  font-size: 14px;
  outline: none;
  transition:
    border-color 0.18s ease,
    background 0.18s ease,
    box-shadow 0.18s ease;
}

.max-select__control:focus {
  border-color: rgba(10, 132, 255, 0.65);
  background: rgba(255, 255, 255, 0.12);
  box-shadow: 0 0 0 3px rgba(10, 132, 255, 0.18);
}
</style>
