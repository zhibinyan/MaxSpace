<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  createAdmin,
  deleteAdmin,
  fetchAdmins,
  updateAdmin,
  type Admin,
} from '@/api/admin'
import MaxConfirm from '@/components/maxConfirm'
import MaxPopup from '@/components/maxPopup'
import {MaxInput} from '@/components/maxInput'
import {
  MaxActionBtn,
  MaxTable,
  type MaxColumn,
} from '@/components/maxTable'
import { MaxButton } from '@/components/maxButton'
import { md5Hash } from '@/utils/md5'
import AdminFormBody from './AdminFormBody.vue'
import { LayoutToolbar } from '@/layout'

const loading = ref(false)
const saving = ref(false)
const admins = ref<Admin[]>([])
const selectedIds = ref<Array<string | number>>([])
const search = reactive({
  username: '',
})

const columns: MaxColumn<Admin>[] = [
  { key: 'id', label: 'ID', width: 72, align: 'center' },
  { key: 'username', label: '用户名' },
  { key: 'isSuper', label: '类型' ,align: 'center' },
  { key: 'createdAt', label: '创建时间' },
  { key: 'updatedAt', label: '更新时间' },
]

const form = reactive({
  id: 0,
  username: '',
  password: '',
})

async function loadAdmins() {
  loading.value = true
  try {
    admins.value = await fetchAdmins()
  } finally {
    loading.value = false
  }
}

function openAdminPopup(title: string) {
  void MaxPopup.open({
    title,
    size: 'md',
    direction: 'top',
    content: AdminFormBody,
    contentProps: {
      form,
      isEdit: !!form.id,
    },
    onConfirm: saveAdmin,
  })
}

function resetForm() {
  form.id = 0
  form.username = ''
  form.password = ''
}

function openAdd() {
  resetForm()
  openAdminPopup('新增管理员')
}

function openEdit(row: Admin) {
  form.id = row.id
  form.username = row.username
  form.password = ''
  openAdminPopup('编辑管理员')
}

async function saveAdmin(): Promise<boolean> {
  if (!form.username.trim()) {
    ElMessage.warning('请输入用户名')
    return false
  }
  if (!form.id && !form.password) {
    ElMessage.warning('请输入密码')
    return false
  }

  saving.value = true
  try {
    if (form.id) {
      const payload: { username: string; password?: string } = {
        username: form.username.trim(),
      }
      if (form.password) {
        payload.password = md5Hash(form.password)
      }
      await updateAdmin(form.id, payload)
    } else {
      await createAdmin(form.username.trim(), md5Hash(form.password))
    }
    await loadAdmins()
    return true
  } catch {
    return false
  } finally {
    saving.value = false
  }
}

async function removeAdmin(row: Admin) {
  if (row.isSuper) {
    ElMessage.warning('超级管理员不可删除')
    return
  }

  const ok = await MaxConfirm.delete({
    title: '删除确认',
    message: `确定删除管理员「${row.username}」吗？此操作不可恢复。`,
  })
  if (!ok) return

  await deleteAdmin(row.id)
  await loadAdmins()
}

onMounted(loadAdmins)
</script>

<template>
  <LayoutToolbar>
    <template #left>
      <MaxInput  v-model="search.username" placeholder="搜索管理员" />
      <MaxInput v-model="search.username" placeholder="搜索管理员" />
      <MaxInput v-model="search.username" placeholder="搜索管理员" />
      <MaxInput v-model="search.username" placeholder="搜索管理员" />
      <MaxInput v-model="search.username" placeholder="搜索管理员" />
      <MaxInput v-model="search.username" placeholder="搜索管理员" />
      <MaxInput v-model="search.username" placeholder="搜索管理员" />
      <MaxInput v-model="search.username" placeholder="搜索管理员" />
      <MaxInput v-model="search.username" placeholder="搜索管理员" />
      <MaxInput v-model="search.username" placeholder="搜索管理员" />
      <MaxInput v-model="search.username" placeholder="搜索管理员" />
      <MaxInput v-model="search.username" placeholder="搜索管理员" />
      <MaxInput v-model="search.username" placeholder="搜索管理员" />

    </template>
    <template #right>
      <MaxButton title="搜索">搜索</MaxButton>
      <MaxButton title="新增管理员" @click="openAdd" > 新增管理员</MaxButton>
    </template>
  </LayoutToolbar>

  <MaxTable
    v-model="selectedIds"
    :columns="columns"
    :data="admins"
    :loading="loading"
    selectable
    row-key="id"
  >
    <template #isSuper="{ row }">
      <span :style="{ color: row.isSuper ? '#ffb4ae' : '' }">
        {{ row.isSuper ? '超级管理员' : '普通管理员' }}
      </span>
    </template>
    <template #actions="{ row }">
      <MaxActionBtn icon="edit" title="编辑" @click="openEdit(row)" />
      <MaxActionBtn
        icon="delete"
        title="删除"
        :disabled="row.isSuper"
        @click="removeAdmin(row)"
      />
    </template>
  </MaxTable>
</template>
