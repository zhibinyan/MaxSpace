<script setup lang="ts">
import { MaxForm, MaxInput } from '@/components/maxInput'

defineProps<{
  form: {
    username: string
    password: string
  }
  isEdit: boolean
}>()
</script>

<template>
  <MaxForm @submit.prevent>
    <MaxInput
      id="admin-username"
      v-model="form.username"
      label="用户名"
      type="text"
      autocomplete="off"
    />
    <MaxInput
      id="admin-password"
      v-model="form.password"
      :label="isEdit ? '新密码' : '密码'"
      type="password"
      autocomplete="new-password"
      :placeholder="isEdit ? '留空则不修改' : '请输入密码'"
    />
  </MaxForm>
</template>
