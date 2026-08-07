<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  createMenu,
  deleteMenu,
  fetchMenus,
  updateMenu,
  type MenuItem,
} from '@/api/menu'
import MaxConfirm from '@/components/maxConfirm'
import MaxPopup from '@/components/maxPopup'
import {
  MaxActionBtn,
  MaxTable,
  type MaxColumn,
} from '@/components/maxTable'
import { LayoutToolbar } from '@/layout'
import { registerRoutesFromTree } from '@/router/setupDynamicRoutes'
import { useMenuStore } from '@/stores/menu'
import { useUserStore } from '@/stores/user'
import MenuFormBody from './MenuFormBody.vue'
import { MaxSvg } from '@/components/maxSvg'

const router = useRouter()
const userStore = useUserStore()
const menuStore = useMenuStore()

const loading = ref(false)
const saving = ref(false)
const menus = ref<MenuItem[]>([])

const columns: MaxColumn<MenuItem>[] = [
  { key: 'id', label: 'ID', width: 72, align: 'center' },
  { key: 'parentId', label: '父级', minWidth: 120 },
  { key: 'path', label: '路径', minWidth: 100 },
  { key: 'name', label: '路由名', minWidth: 120 },
  { key: 'title', label: '标题', minWidth: 120 },
  { key: 'icon', label: '图标', width: 100 },
  { key: 'component', label: '组件', minWidth: 180 },
  { key: 'sortOrder', label: '排序', width: 72, align: 'center' },
  { key: 'keepAlive', label: '缓存', width: 72, align: 'center' },
  { key: 'dock', label: 'Dock', width: 72, align: 'center' },
]

const form = reactive({
  id: 0,
  parentId: null as number | null,
  path: '',
  name: '',
  title: '',
  icon: 'menu',
  component: '',
  redirect: '',
  keepAlive: false,
  dock: false,
  sortOrder: 0,
})

function resetForm() {
  form.id = 0
  form.parentId = null
  form.path = ''
  form.name = ''
  form.title = ''
  form.icon = 'menu'
  form.component = ''
  form.redirect = ''
  form.keepAlive = false
  form.dock = false
  form.sortOrder = 0
}

function getParentTitle(parentId: number | null) {
  if (parentId == null) return '顶级菜单'
  return menus.value.find((item) => item.id === parentId)?.title ?? `#${parentId}`
}

async function reloadAll() {
  await menuStore.refreshTree(true)
  registerRoutesFromTree(router, menuStore.tree, true)
  menus.value = await fetchMenus()
}

async function loadMenus() {
  loading.value = true
  try {
    menuStore.hydrateFromCache()
    menus.value = await fetchMenus()
  } finally {
    loading.value = false
  }
}

function openMenuPopup(title: string) {
  void MaxPopup.open({
    title,
    size: 'lg',
    direction: 'top',
    content: MenuFormBody,
    contentProps: {
      form,
    },
    onConfirm: saveMenu,
  })
}

function openCreate() {
  resetForm()
  openMenuPopup('新增菜单')
}

function openEdit(row: MenuItem) {
  form.id = row.id
  form.parentId = row.parentId
  form.path = row.path
  form.name = row.name ?? ''
  form.title = row.title
  form.icon = row.icon
  form.component = row.component ?? ''
  form.redirect = row.redirect ?? ''
  form.keepAlive = row.keepAlive
  form.dock = row.dock
  form.sortOrder = row.sortOrder
  openMenuPopup('编辑菜单')
}

async function saveMenu(): Promise<boolean> {
  if (!form.path.trim() || !form.title.trim()) {
    ElMessage.warning('请填写路径和标题')
    return false
  }

  const payload = {
    parentId: form.parentId,
    path: form.path.trim(),
    name: form.name.trim() || null,
    title: form.title.trim(),
    icon: form.icon,
    component: form.component.trim() || null,
    redirect: form.redirect.trim() || null,
    keepAlive: form.keepAlive,
    dock: form.dock,
    sortOrder: form.sortOrder,
  }

  saving.value = true
  try {
    if (form.id) {
      await updateMenu(form.id, payload)
    } else {
      await createMenu(payload)
    }
    await reloadAll()
    return true
  } catch {
    return false
  } finally {
    saving.value = false
  }
}

async function removeMenu(row: MenuItem) {
  if (!userStore.isSuper) {
    ElMessage.warning('仅超级管理员可删除菜单')
    return
  }

  const ok = await MaxConfirm.delete({
    title: '删除确认',
    message: `确定删除菜单「${row.title}」吗？此操作不可恢复。`,
  })
  if (!ok) return

  await deleteMenu(row.id)
  await reloadAll()
}

onMounted(async () => {
  await userStore.refreshProfile()
  await loadMenus()
})
</script>

<template>
  <LayoutToolbar>
    <MaxActionBtn title="新增菜单" @click="openCreate">新增菜单</MaxActionBtn>
  </LayoutToolbar>
    <MaxTable
      :columns="columns"
      :data="menus"
      :loading="loading"
      row-key="id"
    >
      <template #parentId="{ row }">
        <span :style="{ color: row.parentId ? '' : 'rgb(255, 180, 174)' }">
          {{ getParentTitle(row.parentId) }}
        </span>
      </template>

      <template #icon="{ row }">
        <MaxSvg :name="row.icon" :size="34" />
      </template>

      <template #keepAlive="{ row }">
        <span
          class="cache-badge"
          :class="row.keepAlive ? 'cache-badge--yes' : 'cache-badge--no'"
        >
          {{ row.keepAlive ? '是' : '否' }}
        </span>
      </template>

      <template #dock="{ row }">
        <span
          class="cache-badge"
          :class="row.dock ? 'cache-badge--yes' : 'cache-badge--no'"
        >
          {{ row.dock ? '是' : '否' }}
        </span>
      </template>

      <template #actions="{ row }">
        <MaxActionBtn icon="edit" title="编辑" @click="openEdit(row)" />
        <MaxActionBtn
          icon="delete"
          title="删除"
          :disabled="!userStore.isSuper"
          @click="removeMenu(row)"
        />
      </template>
    </MaxTable>
</template>

<style scoped>
.cache-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 36px;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 700;
  line-height: 1.4;
  border: 1px solid transparent;
}

.cache-badge--yes {
  color: #9ed8ff;
  background: rgba(10, 132, 255, 0.16);
  border-color: rgba(10, 132, 255, 0.28);
}

.cache-badge--no {
  color: rgba(255, 255, 255, 0.72);
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.18);
}
</style>
