<script setup lang="ts">
defineOptions({ inheritAttrs: false })

const model = defineModel<boolean>({ default: false })

withDefaults(
  defineProps<{
    label: string
    id?: string
    disabled?: boolean
  }>(),
  {
    disabled: false,
  },
)
</script>

<template>
  <div class="max-switch">
    <span class="max-switch__label">{{ label }}</span>
    <label class="max-switch__control" :class="{ 'max-switch__control--disabled': disabled }">
      <input
        :id="id"
        v-model="model"
        class="max-switch__input"
        type="checkbox"
        :disabled="disabled"
        v-bind="$attrs"
      />
      <span class="max-switch__track" aria-hidden="true" />
    </label>
  </div>
</template>

<style scoped>
.max-switch {
  display: grid;
  grid-template-columns: 80px 1fr;
  gap: 12px;
  align-items: center;
}

.max-switch__label {
  color: rgba(255, 255, 255, 0.78);
  font-size: 14px;
  font-weight: 500;
  text-align: right;
}

.max-switch__control {
  position: relative;
  display: inline-flex;
  align-items: center;
  width: 44px;
  height: 26px;
  cursor: pointer;
}

.max-switch__control--disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.max-switch__input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.max-switch__control--disabled .max-switch__input {
  cursor: not-allowed;
}

.max-switch__track {
  position: relative;
  width: 44px;
  height: 26px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.14);
  transition: background 0.18s ease;
}

.max-switch__track::after {
  content: '';
  position: absolute;
  top: 3px;
  left: 3px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #fff;
  transition: transform 0.18s ease;
}

.max-switch__input:checked + .max-switch__track {
  background: #0a84ff;
  border-color: rgba(10, 132, 255, 0.85);
}

.max-switch__input:checked + .max-switch__track::after {
  transform: translateX(18px);
}

.max-switch__input:focus-visible + .max-switch__track {
  box-shadow: 0 0 0 3px rgba(10, 132, 255, 0.18);
}
</style>
