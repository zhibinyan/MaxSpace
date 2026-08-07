<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  batchLinuxHosts,
  createLinuxGroup,
  createLinuxHost,
  createLinuxTag,
  deleteLinuxGroup,
  deleteLinuxHost,
  deleteLinuxTag,
  fetchLinuxGroups,
  fetchLinuxHosts,
  fetchLinuxTags,
  testLinuxHost,
  updateLinuxGroup,
  updateLinuxHost,
  type LinuxGroup,
  type LinuxHost,
  type LinuxTag,
} from '@/api/linux'
import Message from '@/components/massage'
import MaxConfirm from '@/components/maxConfirm'
import MaxPopup from '@/components/maxPopup'
import { MaxButton } from '@/components/maxButton'
import { MaxInput } from '@/components/maxInput'
import { MaxSelect, type MaxSelectOption } from '@/components/maxSelect'
import { MaxSvg } from '@/components/maxSvg'
import { LayoutToolbar } from '@/layout'
import GroupFormBody from './GroupFormBody.vue'
import HostFormBody from './HostFormBody.vue'
import { defaultUsernameForOs, isWindowsOs } from '../osOptions'

defineOptions({ name: 'HostManageView' })

const router = useRouter()
const loading = ref(false)
const groups = ref<LinuxGroup[]>([])
const tags = ref<LinuxTag[]>([])
const hosts = ref<LinuxHost[]>([])
const selectedIds = ref<number[]>([])
const activeGroupId = ref<number | null>(null)
const activeTagId = ref<number | null>(null)

const filters = reactive({
  keyword: '',
  envType: '',
  status: '',
  favorite: '',
})

const hostForm = reactive({
  id: 0,
  name: '',
  host: '',
  port: '22',
  username: 'root',
  authType: 'password',
  password: '',
  privateKey: '',
  groupId: '',
  envType: '',
  osName: 'Linux',
  owner: '',
  remark: '',
  tagIds: [] as number[],
})

const groupForm = reactive({
  id: 0,
  name: '',
  parentId: '',
})

const envFilterOptions: MaxSelectOption[] = [
  { label: '全部环境', value: '' },
  { label: '生产', value: 'prod' },
  { label: '预发', value: 'stage' },
  { label: '测试', value: 'test' },
  { label: '开发', value: 'dev' },
]

const statusFilterOptions: MaxSelectOption[] = [
  { label: '全部状态', value: '' },
  { label: '在线', value: 'online' },
  { label: '离线', value: 'offline' },
  { label: '未知', value: 'unknown' },
]

const favoriteOptions: MaxSelectOption[] = [
  { label: '全部', value: '' },
  { label: '仅收藏', value: '1' },
]

function flattenGroups(list: LinuxGroup[], depth = 0): Array<LinuxGroup & { depth: number }> {
  const out: Array<LinuxGroup & { depth: number }> = []
  for (const g of list) {
    out.push({ ...g, depth })
    if (g.children?.length) out.push(...flattenGroups(g.children, depth + 1))
  }
  return out
}

const flatGroups = computed(() => flattenGroups(groups.value))

const groupOptions = computed<MaxSelectOption[]>(() => [
  { label: '未分组', value: '' },
  ...flatGroups.value.map((g) => ({
    label: `${'—'.repeat(g.depth)} ${g.name}`.trim(),
    value: String(g.id),
  })),
])

const parentGroupOptions = computed<MaxSelectOption[]>(() => [
  { label: '顶级分组', value: '' },
  ...flatGroups.value
    .filter((g) => g.id !== groupForm.id)
    .map((g) => ({
      label: `${'—'.repeat(g.depth)} ${g.name}`.trim(),
      value: String(g.id),
    })),
])

const tagOptions = computed<MaxSelectOption[]>(() =>
  tags.value.map((t) => ({ label: t.name, value: t.id })),
)

async function loadAll() {
  loading.value = true
  try {
    const [g, t, h] = await Promise.all([
      fetchLinuxGroups(),
      fetchLinuxTags(),
      fetchLinuxHosts({
        keyword: filters.keyword,
        groupId: activeGroupId.value,
        tagId: activeTagId.value,
        envType: filters.envType,
        status: filters.status,
        favorite: filters.favorite,
      }),
    ])
    groups.value = g
    tags.value = t
    hosts.value = h
  } finally {
    loading.value = false
  }
}

async function reloadHosts() {
  hosts.value = await fetchLinuxHosts({
    keyword: filters.keyword,
    groupId: activeGroupId.value,
    tagId: activeTagId.value,
    envType: filters.envType,
    status: filters.status,
    favorite: filters.favorite,
  })
}

function selectGroup(id: number | null) {
  activeGroupId.value = id
  void reloadHosts()
}

function selectTag(id: number | null) {
  activeTagId.value = id
  void reloadHosts()
}

function resetHostForm() {
  hostForm.id = 0
  hostForm.name = ''
  hostForm.host = ''
  hostForm.port = '22'
  hostForm.osName = 'Linux'
  hostForm.username = defaultUsernameForOs(hostForm.osName)
  hostForm.authType = 'password'
  hostForm.password = ''
  hostForm.privateKey = ''
  hostForm.groupId = activeGroupId.value != null ? String(activeGroupId.value) : ''
  hostForm.envType = ''
  hostForm.owner = ''
  hostForm.remark = ''
  hostForm.tagIds = []
}

function openCreateHost() {
  resetHostForm()
  void MaxPopup.open({
    title: '新增主机',
    size: 'md',
    content: HostFormBody,
    contentProps: {
      form: hostForm,
      isEdit: false,
      groupOptions: groupOptions.value,
      tagOptions: tagOptions.value,
    },
    onConfirm: async () => {
      if (!hostForm.name.trim() || !hostForm.host.trim() || !hostForm.username.trim()) {
        Message.warning('请填写名称、地址、用户名')
        return false
      }
      try {
        await createLinuxHost({
          name: hostForm.name.trim(),
          host: hostForm.host.trim(),
          port: Number(hostForm.port) || 22,
          username: hostForm.username.trim(),
          authType: hostForm.authType,
          password: hostForm.password || undefined,
          privateKey: hostForm.privateKey || undefined,
          groupId: hostForm.groupId ? Number(hostForm.groupId) : null,
          envType: hostForm.envType,
          osName: hostForm.osName,
          owner: hostForm.owner,
          remark: hostForm.remark,
          tagIds: hostForm.tagIds,
        })
        await reloadHosts()
        groups.value = await fetchLinuxGroups()
        return true
      } catch {
        return false
      }
    },
  })
}

function openEditHost(row: LinuxHost) {
  hostForm.id = row.id
  hostForm.name = row.name
  hostForm.host = row.host
  hostForm.port = String(row.port || 22)
  hostForm.username = row.username
  hostForm.authType = row.authType || 'password'
  hostForm.password = ''
  hostForm.privateKey = ''
  hostForm.groupId = row.groupId != null ? String(row.groupId) : ''
  hostForm.envType = row.envType || ''
  hostForm.osName = row.osName || ''
  hostForm.owner = row.owner || ''
  hostForm.remark = row.remark || ''
  hostForm.tagIds = row.tags.map((t) => t.id)
  void MaxPopup.open({
    title: '编辑主机',
    size: 'md',
    content: HostFormBody,
    contentProps: {
      form: hostForm,
      isEdit: true,
      groupOptions: groupOptions.value,
      tagOptions: tagOptions.value,
    },
    onConfirm: async () => {
      try {
        const payload: Record<string, unknown> = {
          name: hostForm.name.trim(),
          host: hostForm.host.trim(),
          port: Number(hostForm.port) || 22,
          username: hostForm.username.trim(),
          authType: hostForm.authType,
          groupId: hostForm.groupId ? Number(hostForm.groupId) : null,
          envType: hostForm.envType,
          osName: hostForm.osName,
          owner: hostForm.owner,
          remark: hostForm.remark,
          tagIds: hostForm.tagIds,
        }
        if (hostForm.password) payload.password = hostForm.password
        if (hostForm.privateKey) payload.privateKey = hostForm.privateKey
        await updateLinuxHost(hostForm.id, payload)
        await reloadHosts()
        return true
      } catch {
        return false
      }
    },
  })
}

function openCreateGroup() {
  groupForm.id = 0
  groupForm.name = ''
  groupForm.parentId = ''
  void MaxPopup.open({
    title: '新建分组',
    size: 'sm',
    content: GroupFormBody,
    contentProps: { form: groupForm, parentOptions: parentGroupOptions.value },
    onConfirm: async () => {
      if (!groupForm.name.trim()) {
        Message.warning('请输入分组名称')
        return false
      }
      try {
        await createLinuxGroup({
          name: groupForm.name.trim(),
          parentId: groupForm.parentId ? Number(groupForm.parentId) : null,
        })
        groups.value = await fetchLinuxGroups()
        return true
      } catch {
        return false
      }
    },
  })
}

function openEditGroup(g: LinuxGroup) {
  groupForm.id = g.id
  groupForm.name = g.name
  groupForm.parentId = g.parentId != null ? String(g.parentId) : ''
  void MaxPopup.open({
    title: '编辑分组',
    size: 'sm',
    content: GroupFormBody,
    contentProps: { form: groupForm, parentOptions: parentGroupOptions.value },
    onConfirm: async () => {
      try {
        await updateLinuxGroup(g.id, {
          name: groupForm.name.trim(),
          parentId: groupForm.parentId ? Number(groupForm.parentId) : null,
        })
        groups.value = await fetchLinuxGroups()
        return true
      } catch {
        return false
      }
    },
  })
}

async function removeGroup(g: LinuxGroup) {
  const ok = await MaxConfirm.delete({
    title: '删除分组',
    message: `确定删除分组「${g.name}」吗？`,
  })
  if (!ok) return
  await deleteLinuxGroup(g.id)
  if (activeGroupId.value === g.id) activeGroupId.value = null
  groups.value = await fetchLinuxGroups()
  await reloadHosts()
}

async function addTag() {
  const name = window.prompt('新标签名称')
  if (!name?.trim()) return
  await createLinuxTag({ name: name.trim() })
  tags.value = await fetchLinuxTags()
}

async function removeTag(tag: LinuxTag) {
  const ok = await MaxConfirm.delete({
    title: '删除标签',
    message: `确定删除标签「${tag.name}」吗？`,
  })
  if (!ok) return
  await deleteLinuxTag(tag.id)
  if (activeTagId.value === tag.id) activeTagId.value = null
  tags.value = await fetchLinuxTags()
  await reloadHosts()
}

function toggleSelect(id: number, event: MouseEvent) {
  if (event.metaKey || event.ctrlKey) {
    if (selectedIds.value.includes(id)) {
      selectedIds.value = selectedIds.value.filter((x) => x !== id)
    } else {
      selectedIds.value = [...selectedIds.value, id]
    }
    return
  }
  selectedIds.value = [id]
}

function isSelected(id: number) {
  return selectedIds.value.includes(id)
}

async function removeHost(row: LinuxHost) {
  const ok = await MaxConfirm.delete({
    title: '删除主机',
    message: `确定删除主机「${row.name}」吗？`,
  })
  if (!ok) return
  await deleteLinuxHost(row.id)
  await reloadHosts()
  groups.value = await fetchLinuxGroups()
}

async function handleTest(row: LinuxHost) {
  try {
    await testLinuxHost(row.id)
    await reloadHosts()
  } catch {
    /* ignore */
  }
}

async function toggleFavorite(row: LinuxHost) {
  await updateLinuxHost(row.id, { isFavorite: !row.isFavorite })
  await reloadHosts()
}

function copyConn(row: LinuxHost) {
  const text = `ssh ${row.username}@${row.host} -p ${row.port}`
  void navigator.clipboard.writeText(text)
  if (isWindowsOs(row.osName)) {
    Message.success('已复制 SSH 命令（需主机已开启 OpenSSH Server）')
  } else {
    Message.success('连接信息已复制')
  }
}

function openSsh(row: LinuxHost) {
  router.push({ name: 'linuxSsh', query: { hostId: String(row.id) } })
}

function openSftp(row: LinuxHost) {
  router.push({ name: 'linuxSftp', query: { hostId: String(row.id) } })
}

async function batchDelete() {
  if (!selectedIds.value.length) {
    Message.warning('请先选择主机')
    return
  }
  const ok = await MaxConfirm.delete({
    title: '批量删除',
    message: `确定删除选中的 ${selectedIds.value.length} 台主机吗？`,
  })
  if (!ok) return
  await batchLinuxHosts('delete', selectedIds.value)
  selectedIds.value = []
  await loadAll()
}

async function batchFavorite() {
  if (!selectedIds.value.length) {
    Message.warning('请先选择主机')
    return
  }
  await batchLinuxHosts('favorite', selectedIds.value)
  selectedIds.value = []
  await reloadHosts()
}

function statusLabel(status: string) {
  if (status === 'online') return '在线'
  if (status === 'offline') return '离线'
  return '未知'
}

watch(
  () => [filters.keyword, filters.envType, filters.status, filters.favorite],
  () => {
    void reloadHosts()
  },
)

onMounted(loadAll)
</script>

<template>
  <div class="linux-hosts">
    <LayoutToolbar>
      <template #left>
        <MaxInput v-model="filters.keyword" placeholder="搜索名称 / IP / 备注" />
        <MaxSelect v-model="filters.envType" :options="envFilterOptions" />
        <MaxSelect v-model="filters.status" :options="statusFilterOptions" />
        <MaxSelect v-model="filters.favorite" :options="favoriteOptions" />
      </template>
      <template #right>
        <MaxButton @click="reloadHosts">刷新</MaxButton>
        <MaxButton @click="batchFavorite">批量收藏</MaxButton>
        <MaxButton @click="batchDelete">批量删除</MaxButton>
        <MaxButton variant="primary" @click="openCreateHost">新增主机</MaxButton>
      </template>
    </LayoutToolbar>

    <div class="linux-hosts__layout">
      <aside class="linux-hosts__side">
        <div class="side-block">
          <div class="side-block__head">
            <span>分组</span>
            <MaxButton size="sm" @click="openCreateGroup">新建</MaxButton>
          </div>
          <button
            type="button"
            class="side-item"
            :class="{ 'side-item--on': activeGroupId == null }"
            @click="selectGroup(null)"
          >
            全部主机
          </button>
          <div
            v-for="g in flatGroups"
            :key="g.id"
            class="side-item-row"
            :style="{ paddingLeft: `${10 + g.depth * 14}px` }"
          >
            <button
              type="button"
              class="side-item"
              :class="{ 'side-item--on': activeGroupId === g.id }"
              @click="selectGroup(g.id)"
            >
              {{ g.name }}
              <em>{{ g.hostCount }}</em>
            </button>
            <button type="button" class="side-mini" title="编辑" @click="openEditGroup(g)">✎</button>
            <button type="button" class="side-mini" title="删除" @click="removeGroup(g)">✕</button>
          </div>
        </div>

        <div class="side-block">
          <div class="side-block__head">
            <span>标签</span>
            <MaxButton size="sm" @click="addTag">新建</MaxButton>
          </div>
          <button
            type="button"
            class="side-item"
            :class="{ 'side-item--on': activeTagId == null }"
            @click="selectTag(null)"
          >
            全部标签
          </button>
          <div v-for="tag in tags" :key="tag.id" class="side-item-row">
            <button
              type="button"
              class="side-item"
              :class="{ 'side-item--on': activeTagId === tag.id }"
              @click="selectTag(tag.id)"
            >
              {{ tag.name }}
            </button>
            <button type="button" class="side-mini" title="删除" @click="removeTag(tag)">✕</button>
          </div>
        </div>
      </aside>

      <section class="linux-hosts__main">
        <p v-if="loading" class="linux-empty">加载中…</p>
        <p v-else-if="!hosts.length" class="linux-empty">暂无主机，点击「新增主机」开始</p>
        <div v-else class="host-grid">
          <button
            v-for="row in hosts"
            :key="row.id"
            type="button"
            class="host-card"
            :class="{ 'host-card--selected': isSelected(row.id) }"
            @click="toggleSelect(row.id, $event)"
            @dblclick="openSsh(row)"
          >
            <div class="host-card__top">
              <MaxSvg name="ssh" :size="40" alt="" />
              <span
                class="host-status"
                :class="`host-status--${row.status || 'unknown'}`"
              >
                {{ statusLabel(row.status) }}
              </span>
            </div>
            <h3 class="host-card__name">
              <span v-if="row.isFavorite" class="host-fav">★</span>
              {{ row.name }}
            </h3>
            <p class="host-card__ip">{{ row.username }}@{{ row.host }}:{{ row.port }}</p>
            <p class="host-card__meta">
              {{ row.envType || '未设环境' }}
              <template v-if="row.osName"> · {{ row.osName }}</template>
            </p>
            <div v-if="row.tags.length" class="host-card__tags">
              <span v-for="t in row.tags" :key="t.id">{{ t.name }}</span>
            </div>
            <div class="host-card__actions" @click.stop>
              <MaxButton size="sm" variant="primary" @click="openSsh(row)">SSH</MaxButton>
              <MaxButton size="sm" @click="openSftp(row)">文件</MaxButton>
              <MaxButton size="sm" @click="handleTest(row)">测试</MaxButton>
              <MaxButton size="sm" @click="openEditHost(row)">编辑</MaxButton>
              <MaxButton size="sm" @click="toggleFavorite(row)">
                {{ row.isFavorite ? '取消收藏' : '收藏' }}
              </MaxButton>
              <MaxButton size="sm" @click="copyConn(row)">复制</MaxButton>
              <MaxButton size="sm" variant="link-danger" @click="removeHost(row)">删除</MaxButton>
            </div>
          </button>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.linux-hosts {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
  min-height: 0;
}

.linux-hosts__layout {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 12px;
  flex: 1;
  min-height: 0;
}

.linux-hosts__side {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
  overflow: auto;
  padding: 10px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.side-block + .side-block {
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  padding-top: 10px;
}

.side-block__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  color: rgba(255, 255, 255, 0.85);
  font-size: 13px;
  font-weight: 600;
}

.side-item-row {
  display: flex;
  align-items: center;
  gap: 2px;
}

.side-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.75);
  text-align: left;
  padding: 7px 8px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
}

.side-item em {
  font-style: normal;
  color: rgba(255, 255, 255, 0.4);
  font-size: 12px;
}

.side-item:hover,
.side-item--on {
  background: rgba(10, 132, 255, 0.18);
  color: #fff;
}

.side-mini {
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.4);
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
}

.side-mini:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.08);
}

.linux-hosts__main {
  min-height: 0;
  overflow: auto;
}

.linux-empty {
  margin: 48px 0;
  text-align: center;
  color: rgba(255, 255, 255, 0.45);
}

.host-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 12px;
}

.host-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin: 0;
  padding: 14px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.06);
  color: #fff;
  text-align: left;
  cursor: default;
}

.host-card--selected {
  border-color: rgba(10, 132, 255, 0.55);
  background: rgba(10, 132, 255, 0.14);
}

.host-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.host-status {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.1);
}

.host-status--online {
  background: rgba(40, 200, 64, 0.25);
  color: #8dff9d;
}

.host-status--offline {
  background: rgba(255, 80, 80, 0.22);
  color: #ffb4ae;
}

.host-card__name {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
}

.host-fav {
  color: #ffd666;
  margin-right: 4px;
}

.host-card__ip,
.host-card__meta {
  margin: 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.68);
  text-shadow: none;
}

.host-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.host-card__tags span {
  font-size: 11px;
  padding: 2px 7px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.75);
}

.host-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
}
</style>
