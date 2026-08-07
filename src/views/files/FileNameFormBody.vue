<script setup lang="ts">
import { MaxForm, MaxInput } from '@/components/maxInput'

defineProps<{
  form: {
    name: string
  }
  label?: string
  placeholder?: string
}>()
</script>

<template>
  <MaxForm @submit.prevent>
    <MaxInput
      id="file-entry-name"
      v-model="form.name"
      :label="label || '名称'"
      type="text"
      autocomplete="off"
      :placeholder="placeholder || '请输入名称'"
    />
  </MaxForm>
</template>
