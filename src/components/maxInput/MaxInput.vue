<script setup lang="ts">
import { computed } from 'vue'

defineOptions({ inheritAttrs: false })

const model = defineModel<string | number>({ default: '' })

const props = withDefaults(
  defineProps<{
    label?: string
    id?: string
    type?: 'text' | 'password' | 'email' | 'number' | 'search' | 'tel' | 'url'
  }>(),
  {
    label: '',
    type: 'text',
  },
)

const hasLabel = computed(() => !!props.label?.trim())
</script>

<template>
  <div class="max-input" :class="{ 'max-input--no-label': !hasLabel }">
    <label class="max-input__label" :for="id">{{ label }}</label>
    <input
      :id="id"
      v-model="model"
      class="max-input__control"
      :type="type"
      v-bind="$attrs"
    />
  </div>
</template>

<style scoped>
.max-input {
  display: grid;
  grid-template-columns: 80px 1fr;
  gap: 12px;
  align-items: center;
  width: 100%;
  min-width: 0;
}

.max-input--no-label {
  grid-template-columns: 0px 1fr;
  gap: 0;
}

.max-input--no-label .max-input__label {
  overflow: hidden;
  padding: 0;
}

.max-input__label {
  color: rgba(255, 255, 255, 0.78);
  font-size: 14px;
  font-weight: 500;
  text-align: right;
}

.max-input__control {
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

.max-input__control::placeholder {
  color: rgba(255, 255, 255, 0.38);
}

.max-input__control:focus {
  border-color: rgba(10, 132, 255, 0.65);
  background: rgba(255, 255, 255, 0.12);
  box-shadow: 0 0 0 3px rgba(10, 132, 255, 0.18);
}
</style>
