<script setup lang="ts">
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'

const form = reactive({
  emailNotify: true,
  smsNotify: false,
  orderAlert: true,
  systemAlert: true,
})

function handleSave() {
  ElMessage.success('通知设置已保存')
}
</script>

<template>
  <el-card>
    <template #header><span>通知设置</span></template>
    <el-form :model="form" label-width="120px" style="max-width: 560px">
      <el-form-item label="邮件通知">
        <el-switch v-model="form.emailNotify" />
      </el-form-item>
      <el-form-item label="短信通知">
        <el-switch v-model="form.smsNotify" />
      </el-form-item>
      <el-form-item label="订单提醒">
        <el-switch v-model="form.orderAlert" />
      </el-form-item>
      <el-form-item label="系统告警">
        <el-switch v-model="form.systemAlert" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>
