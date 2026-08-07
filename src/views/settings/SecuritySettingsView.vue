<script setup lang="ts">
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'

const form = reactive({
  twoFactor: false,
  ipWhitelist: '',
  passwordExpire: 90,
  loginLock: true,
})

function handleSave() {
  ElMessage.success('安全设置已保存')
}
</script>

<template>
  <el-card>
    <template #header><span>安全设置</span></template>
    <el-form :model="form" label-width="120px" style="max-width: 560px">
      <el-form-item label="双因素认证">
        <el-switch v-model="form.twoFactor" />
      </el-form-item>
      <el-form-item label="IP 白名单">
        <el-input v-model="form.ipWhitelist" placeholder="多个 IP 用逗号分隔" />
      </el-form-item>
      <el-form-item label="密码过期天数">
        <el-input-number v-model="form.passwordExpire" :min="30" :max="365" />
      </el-form-item>
      <el-form-item label="登录失败锁定">
        <el-switch v-model="form.loginLock" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>
