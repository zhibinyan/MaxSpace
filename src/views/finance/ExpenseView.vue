<script setup lang="ts">
import { ref } from 'vue'

const expenses = ref([
  { id: 1, item: '云服务器', amount: '¥1,200', date: '2026-06-01' },
  { id: 2, item: '短信服务', amount: '¥380', date: '2026-06-15' },
])
</script>

<template>
  <el-card>
    <template #header><span>支出明细</span></template>
    <el-table :data="expenses" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="item" label="项目" />
      <el-table-column prop="amount" label="金额" width="140" />
      <el-table-column prop="date" label="日期" width="140" />
    </el-table>
  </el-card>
</template>
