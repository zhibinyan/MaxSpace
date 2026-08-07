<script setup lang="ts">
import { ref } from 'vue'

const incomes = ref([
  { id: 1, source: '订单收入', amount: '¥12,840', date: '2026-06-26' },
  { id: 2, source: '会员订阅', amount: '¥3,200', date: '2026-06-25' },
])
</script>

<template>
  <el-card>
    <template #header><span>收入明细</span></template>
    <el-table :data="incomes" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="source" label="来源" />
      <el-table-column prop="amount" label="金额" width="140" />
      <el-table-column prop="date" label="日期" width="140" />
    </el-table>
  </el-card>
</template>
