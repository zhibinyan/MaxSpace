<script setup lang="ts">
import { watch } from 'vue'
import { MaxForm, MaxInput } from '@/components/maxInput'
import { MaxSelect, type MaxSelectOption } from '@/components/maxSelect'
import { defaultUsernameForOs, isWindowsOs, LINUX_OS_OPTIONS } from '../osOptions'

const props = defineProps<{
  form: {
    name: string
    host: string
    port: string
    username: string
    authType: string
    password: string
    privateKey: string
    groupId: string
    envType: string
    osName: string
    owner: string
    remark: string
    tagIds: number[]
  }
  isEdit: boolean
  groupOptions: MaxSelectOption[]
  tagOptions: MaxSelectOption[]
}>()

const authOptions: MaxSelectOption[] = [
  { label: '密码', value: 'password' },
  { label: '私钥', value: 'key' },
]

const envOptions: MaxSelectOption[] = [
  { label: '未设置', value: '' },
  { label: '生产', value: 'prod' },
  { label: '预发', value: 'stage' },
  { label: '测试', value: 'test' },
  { label: '开发', value: 'dev' },
]

const osOptions = LINUX_OS_OPTIONS

watch(
  () => props.form.osName,
  (osName, prev) => {
    if (props.isEdit) return
    // 仅在系统切换时，若用户名仍是另一侧默认值，则自动切换
    const nextDefault = defaultUsernameForOs(osName)
    const prevDefault = defaultUsernameForOs(prev)
    if (!props.form.username || props.form.username === prevDefault) {
      props.form.username = nextDefault
    }
  },
)

function toggleTag(form: { tagIds: number[] }, id: number) {
  const idx = form.tagIds.indexOf(id)
  if (idx >= 0) form.tagIds.splice(idx, 1)
  else form.tagIds.push(id)
}
</script>

<template>
  <MaxForm @submit.prevent>
    <MaxInput id="lh-name" v-model="form.name" label="名称" placeholder="如 web-01" />
    <MaxInput id="lh-host" v-model="form.host" label="地址" placeholder="IP 或域名" />
    <MaxInput id="lh-port" v-model="form.port" label="端口" type="number" />
    <MaxSelect id="lh-os" v-model="form.osName" label="系统" :options="osOptions" />
    <p v-if="isWindowsOs(form.osName)" class="lh-hint">
      Windows Server 需已安装并启动 OpenSSH Server，否则 SSH / 远程文件不可用。
    </p>
    <MaxInput
      id="lh-user"
      v-model="form.username"
      label="用户名"
      :placeholder="isWindowsOs(form.osName) ? 'Administrator' : 'root'"
    />
    <MaxSelect id="lh-auth" v-model="form.authType" label="认证" :options="authOptions" />
    <MaxInput
      v-if="form.authType !== 'key'"
      id="lh-pass"
      v-model="form.password"
      label="密码"
      type="password"
      :placeholder="isEdit ? '留空则不修改' : '登录密码'"
    />
    <MaxInput
      v-else
      id="lh-key"
      v-model="form.privateKey"
      label="私钥"
      :placeholder="isEdit ? '留空则不修改' : '粘贴私钥内容'"
    />
    <MaxSelect id="lh-group" v-model="form.groupId" label="分组" :options="groupOptions" />
    <MaxSelect id="lh-env" v-model="form.envType" label="环境" :options="envOptions" />
    <MaxInput id="lh-owner" v-model="form.owner" label="负责人" />
    <MaxInput id="lh-remark" v-model="form.remark" label="备注" />
    <div class="lh-tags">
      <span class="lh-tags__label">标签</span>
      <div class="lh-tags__list">
        <button
          v-for="tag in tagOptions"
          :key="String(tag.value)"
          type="button"
          class="lh-tag"
          :class="{ 'lh-tag--on': form.tagIds.includes(Number(tag.value)) }"
          @click="toggleTag(form, Number(tag.value))"
        >
          {{ tag.label }}
        </button>
      </div>
    </div>
  </MaxForm>
</template>

<style scoped>
.lh-hint {
  margin: -4px 0 4px;
  padding-left: 92px;
  font-size: 12px;
  line-height: 1.4;
  color: rgba(255, 196, 96, 0.92);
}

.lh-tags {
  display: grid;
  grid-template-columns: 80px 1fr;
  gap: 12px;
  align-items: start;
}

.lh-tags__label {
  color: rgba(255, 255, 255, 0.78);
  font-size: 14px;
  font-weight: 500;
  text-align: right;
  padding-top: 6px;
}

.lh-tags__list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.lh-tag {
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.78);
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  cursor: pointer;
}

.lh-tag--on {
  background: rgba(10, 132, 255, 0.28);
  border-color: rgba(10, 132, 255, 0.5);
  color: #fff;
}
</style>
