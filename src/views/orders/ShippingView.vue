<script setup lang="ts">
import { ref } from 'vue'

const shipments = ref([
  { id: 'S2001', orderId: 'O1002', carrier: '顺丰', tracking: 'SF1234567890', status: '运输中' },
  { id: 'S2002', orderId: 'O1001', carrier: '中通', tracking: 'ZT9876543210', status: '已签收' },
])
</script>

<template>
  <el-card>
    <template #header><span>发货管理</span></template>
    <el-table :data="shipments" stripe>
      <el-table-column prop="id" label="发货单号" width="100" />
      <el-table-column prop="orderId" label="订单号" width="120" />
      <el-table-column prop="carrier" label="快递公司" width="100" />
      <el-table-column prop="tracking" label="运单号" />
      <el-table-column prop="status" label="状态" width="100" />
    </el-table>
  </el-card>
</template>
