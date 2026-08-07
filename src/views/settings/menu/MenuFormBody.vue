<script setup lang="ts">
import { computed } from 'vue'
import { MaxForm, MaxInput } from '@/components/maxInput'
import { MaxSelect, type MaxSelectOption } from '@/components/maxSelect'
import { MaxSwitch } from '@/components/maxSwitch'
import { MaxSvgPicker } from '@/components/maxSvgPicker'
import { flattenMenus } from '@/router/dynamicRoutes'
import { useMenuStore } from '@/stores/menu'

const props = defineProps<{
  form: {
    id: number
    parentId: number | null
    path: string
    name: string
    title: string
    icon: string
    component: string
    redirect: string
    keepAlive: boolean
    dock: boolean
    sortOrder: number
  }
}>()

const menuStore = useMenuStore()

const parentOptions = computed<MaxSelectOption[]>(() => {
  const options: MaxSelectOption[] = [{ label: '顶级菜单', value: null }]
  const flat = flattenMenus(menuStore.tree)
  for (const item of flat) {
    if (props.form.id && item.id === props.form.id) continue
    options.push({
      label: `${item.fullPath} (${item.title})`,
      value: item.id,
    })
  }
  return options
})
</script>

<template>
  <MaxForm @submit.prevent>
    <MaxSelect
      id="menu-parent"
      v-model="form.parentId"
      label="父级菜单"
      :options="parentOptions"
    />
    <MaxInput
      id="menu-path"
      v-model="form.path"
      label="路径"
      placeholder="如 list 或 browser"
    />
    <MaxInput
      id="menu-name"
      v-model="form.name"
      label="路由名"
      placeholder="如 UserList"
    />
    <MaxInput id="menu-title" v-model="form.title" label="标题" />
    <MaxSvgPicker id="menu-icon" v-model="form.icon" label="图标" />
    <MaxInput
      id="menu-component"
      v-model="form.component"
      label="组件"
      placeholder="@/views/settings/menu/MenuManagementView.vue"
    />
    <MaxInput
      id="menu-redirect"
      v-model="form.redirect"
      label="重定向"
      placeholder="/users/list"
    />
    <MaxInput
      id="menu-sort"
      v-model.number="form.sortOrder"
      label="排序"
      type="number"
      min="0"
    />
    <MaxSwitch id="menu-dock" v-model="form.dock" label="Dock" />
    <MaxSwitch id="menu-keep" v-model="form.keepAlive" label="KeepAlive" />
  </MaxForm>
</template>
