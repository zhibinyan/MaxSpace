<script setup lang="ts">
import { ref } from 'vue'

const categories = ref([
  { id: 1, name: '技术', count: 24, sort: 1 },
  { id: 2, name: '产品', count: 12, sort: 2 },
  { id: 3, name: '设计', count: 8, sort: 3 },
])
</script>

<template>
  <el-card>
    <template #header><span>分类管理</span></template>
    <el-table :data="categories" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="分类名称" />
      <el-table-column prop="count" label="文章数" width="100" />
      <el-table-column prop="sort" label="排序" width="80" />
    </el-table>
  </el-card>
</template>
