<script setup lang="ts">
import { ref } from 'vue'

const permissions = ref([
  { id: 1, name: '查看仪表盘', code: 'dashboard:read', module: '仪表盘' },
  { id: 2, name: '用户管理', code: 'users:write', module: '用户管理' },
  { id: 3, name: '角色管理', code: 'roles:write', module: '用户管理' },
  { id: 4, name: '系统设置', code: 'settings:write', module: '系统设置' },
])
</script>

<template>
  <el-card>
    <template #header>
      <span>权限配置</span>
    </template>
    <el-table :data="permissions" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="权限名称" />
      <el-table-column prop="code" label="权限标识" />
      <el-table-column prop="module" label="所属模块" />
    </el-table>
  </el-card>
</template>
