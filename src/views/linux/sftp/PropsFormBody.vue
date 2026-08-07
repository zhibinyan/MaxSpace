<script setup lang="ts">
import { MaxForm, MaxInput } from '@/components/maxInput'

defineProps<{
  form: { mode: string; uid: string; gid: string }
  windows?: boolean
}>()
</script>

<template>
  <MaxForm>
    <MaxInput v-model="form.mode" label="权限 (chmod)" placeholder="如 755 或 644" />
    <template v-if="!windows">
      <MaxInput v-model="form.uid" label="UID" placeholder="数字用户 ID" />
      <MaxInput v-model="form.gid" label="GID" placeholder="数字组 ID" />
    </template>
    <p v-else class="hint">Windows 主机仅支持 chmod，不支持 chown。</p>
  </MaxForm>
</template>

<style scoped>
.hint {
  margin: 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}
</style>
