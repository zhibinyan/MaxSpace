<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { User } from '../../types'

const users = ref<User[]>([
  { id: 1, username: 'admin', email: 'admin@example.com', role: 'admin', status: 'active', createdAt: '2026-01-15' },
  { id: 2, username: 'zhangsan', email: 'zhangsan@example.com', role: 'editor', status: 'active', createdAt: '2026-02-20' },
  { id: 3, username: 'lisi', email: 'lisi@example.com', role: 'editor', status: 'active', createdAt: '2026-03-10' },
  { id: 4, username: 'wangwu', email: 'wangwu@example.com', role: 'viewer', status: 'disabled', createdAt: '2026-04-05' },
  { id: 5, username: 'zhaoliu', email: 'zhaoliu@example.com', role: 'viewer', status: 'active', createdAt: '2026-05-18' },
])

const dialogVisible = ref(false)
const editingUser = ref<Partial<User>>({})

const roleMap: Record<User['role'], string> = {
  admin: '管理员',
  editor: '编辑',
  viewer: '访客',
}

function openCreate() {
  editingUser.value = { role: 'viewer', status: 'active' }
  dialogVisible.value = true
}

function openEdit(row: User) {
  editingUser.value = { ...row }
  dialogVisible.value = true
}

function saveUser() {
  if (!editingUser.value.username || !editingUser.value.email) {
    ElMessage.warning('请填写完整信息')
    return
  }

  if (editingUser.value.id) {
    const idx = users.value.findIndex((u) => u.id === editingUser.value.id)
    if (idx >= 0) users.value[idx] = editingUser.value as User
    ElMessage.success('用户已更新')
  } else {
    users.value.push({
      ...(editingUser.value as User),
      id: Date.now(),
      createdAt: new Date().toISOString().slice(0, 10),
    })
    ElMessage.success('用户已创建')
  }
  dialogVisible.value = false
}

async function deleteUser(row: User) {
  await ElMessageBox.confirm(`确定删除用户「${row.username}」吗？`, '提示', { type: 'warning' })
  users.value = users.value.filter((u) => u.id !== row.id)
  ElMessage.success('已删除')
}
</script>

<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>用户列表</span>
        <el-button type="primary" @click="openCreate">新增用户</el-button>
      </div>
    </template>

    <el-table :data="users" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column prop="role" label="角色">
        <template #default="{ row }">
          <el-tag :type="row.role === 'admin' ? 'danger' : row.role === 'editor' ? 'warning' : 'info'">
            {{ roleMap[row.role as User['role']] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'info'">
            {{ row.status === 'active' ? '正常' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="createdAt" label="创建时间" />
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="deleteUser(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>

  <el-dialog v-model="dialogVisible" :title="editingUser.id ? '编辑用户' : '新增用户'" width="480">
    <el-form label-width="80px">
      <el-form-item label="用户名">
        <el-input v-model="editingUser.username" />
      </el-form-item>
      <el-form-item label="邮箱">
        <el-input v-model="editingUser.email" />
      </el-form-item>
      <el-form-item label="角色">
        <el-select v-model="editingUser.role" style="width: 100%">
          <el-option label="管理员" value="admin" />
          <el-option label="编辑" value="editor" />
          <el-option label="访客" value="viewer" />
        </el-select>
      </el-form-item>
      <el-form-item label="状态">
        <el-radio-group v-model="editingUser.status">
          <el-radio value="active">正常</el-radio>
          <el-radio value="disabled">禁用</el-radio>
        </el-radio-group>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="saveUser">保存</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
