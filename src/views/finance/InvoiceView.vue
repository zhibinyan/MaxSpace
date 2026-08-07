<script setup lang="ts">
import { ref } from 'vue'

const invoices = ref([
  { id: 'INV-001', company: '示例科技', amount: '¥5,000', status: '已开票' },
  { id: 'INV-002', company: '测试企业', amount: '¥2,800', status: '待审核' },
])
</script>

<template>
  <el-card>
    <template #header><span>发票管理</span></template>
    <el-table :data="invoices" stripe>
      <el-table-column prop="id" label="发票号" width="120" />
      <el-table-column prop="company" label="企业名称" />
      <el-table-column prop="amount" label="金额" width="120" />
      <el-table-column prop="status" label="状态" width="100" />
    </el-table>
  </el-card>
</template>
