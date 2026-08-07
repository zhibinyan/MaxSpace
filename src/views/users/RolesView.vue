<script setup lang="ts">
import { ref } from 'vue'

const roles = ref([
  { id: 1, name: '管理员', code: 'admin', userCount: 1, description: '拥有全部权限' },
  { id: 2, name: '编辑', code: 'editor', userCount: 2, description: '可编辑内容与用户' },
  { id: 3, name: '访客', code: 'viewer', userCount: 2, description: '只读访问' },
])
</script>

<template>
  <el-card>
    <template #header>
      <span>角色管理</span>
    </template>
    <el-table :data="roles" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="角色名称" />
      <el-table-column prop="code" label="标识" />
      <el-table-column prop="userCount" label="用户数" width="100" />
      <el-table-column prop="description" label="说明" />
    </el-table>
  </el-card>
</template>
