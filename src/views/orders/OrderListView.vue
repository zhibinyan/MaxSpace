<script setup lang="ts">
import { ref } from 'vue'

const orders = ref([
  { id: 'O1001', user: '张三', amount: '¥128.00', status: '已完成', time: '2026-06-26 09:12' },
  { id: 'O1002', user: '李四', amount: '¥56.50', status: '待发货', time: '2026-06-26 10:05' },
  { id: 'O1003', user: '王五', amount: '¥299.00', status: '退款中', time: '2026-06-26 11:20' },
])
</script>

<template>
  <el-card>
    <template #header><span>订单列表</span></template>
    <el-table :data="orders" stripe>
      <el-table-column prop="id" label="订单号" width="120" />
      <el-table-column prop="user" label="用户" />
      <el-table-column prop="amount" label="金额" width="120" />
      <el-table-column prop="status" label="状态" width="100" />
      <el-table-column prop="time" label="下单时间" />
    </el-table>
  </el-card>
</template>
