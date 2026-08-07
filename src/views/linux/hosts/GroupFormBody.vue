<script setup lang="ts">
import { MaxForm, MaxInput } from '@/components/maxInput'
import { MaxSelect, type MaxSelectOption } from '@/components/maxSelect'

defineProps<{
  form: {
    name: string
    parentId: string
  }
  parentOptions: MaxSelectOption[]
}>()
</script>

<template>
  <MaxForm @submit.prevent>
    <MaxInput id="lg-name" v-model="form.name" label="名称" placeholder="分组名称" />
    <MaxSelect id="lg-parent" v-model="form.parentId" label="父级" :options="parentOptions" />
  </MaxForm>
</template>
