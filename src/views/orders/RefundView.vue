<script setup lang="ts">
import { ref } from 'vue'

const refunds = ref([
  { id: 'R001', orderId: 'O1003', reason: '商品不符', amount: '¥299.00', status: '处理中' },
  { id: 'R002', orderId: 'O0998', reason: '重复下单', amount: '¥88.00', status: '已退款' },
])
</script>

<template>
  <el-card>
    <template #header><span>退款管理</span></template>
    <el-table :data="refunds" stripe>
      <el-table-column prop="id" label="退款单号" width="100" />
      <el-table-column prop="orderId" label="关联订单" width="120" />
      <el-table-column prop="reason" label="原因" />
      <el-table-column prop="amount" label="金额" width="120" />
      <el-table-column prop="status" label="状态" width="100" />
    </el-table>
  </el-card>
</template>
