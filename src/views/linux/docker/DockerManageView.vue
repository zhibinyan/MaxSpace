<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  dockerComposeAction,
  dockerContainerAction,
  dockerImageImport,
  dockerImagePull,
  dockerImageRemove,
  dockerImageExportUrl,
  dockerNetworkCreate,
  dockerNetworkRemove,
  dockerVolumeBackupUrl,
  dockerVolumeCreate,
  dockerVolumeRemove,
  dockerVolumeRestore,
  fetchDockerAudit,
  fetchDockerCompose,
  fetchDockerComposeConfig,
  fetchDockerComposeLogs,
  fetchDockerContainerDetail,
  fetchDockerContainerStats,
  fetchDockerContainers,
  fetchDockerImageInspect,
  fetchDockerImages,
  fetchDockerNetworkInspect,
  fetchDockerNetworks,
  fetchDockerOverview,
  fetchDockerVolumeInspect,
  fetchDockerVolumes,
  fetchLinuxHosts,
  type DockerAuditItem,
  type DockerComposeApp,
  type DockerContainer,
  type DockerImage,
  type DockerNetwork,
  type DockerOverview,
  type DockerStatItem,
  type DockerVolume,
  type LinuxHost,
} from '@/api/linux'
import Message from '@/components/massage'
import MaxConfirm from '@/components/maxConfirm'
import MaxPopup from '@/components/maxPopup'
import { MaxButton } from '@/components/maxButton'
import { MaxInput } from '@/components/maxInput'
import { MaxSelect, type MaxSelectOption } from '@/components/maxSelect'
import { LayoutToolbar } from '@/layout'
import DockerDetailBody from './DockerDetailBody.vue'
import DockerExecBody from './DockerExecBody.vue'
import DockerJsonBody from './DockerJsonBody.vue'
import DockerLogBody from './DockerLogBody.vue'

defineOptions({ name: 'DockerManageView' })

type TabKey =
  | 'overview'
  | 'containers'
  | 'images'
  | 'compose'
  | 'networks'
  | 'volumes'
  | 'monitor'
  | 'audit'

const router = useRouter()
const hosts = ref<LinuxHost[]>([])
const hostId = ref('')
const tab = ref<TabKey>('overview')
const loading = ref(false)
const keyword = ref('')
const monitorAuto = ref(false)
let monitorTimer: number | null = null

const overview = ref<DockerOverview | null>(null)
const containers = ref<DockerContainer[]>([])
const images = ref<DockerImage[]>([])
const networks = ref<DockerNetwork[]>([])
const volumes = ref<DockerVolume[]>([])
const composeApps = ref<DockerComposeApp[]>([])
const stats = ref<DockerStatItem[]>([])
const audits = ref<DockerAuditItem[]>([])

const pullImage = ref('')
const newNetwork = ref('')
const newNetworkDriver = ref('bridge')
const newVolume = ref('')

const importInput = ref<HTMLInputElement | null>(null)
const restoreInput = ref<HTMLInputElement | null>(null)
const restoreVolumeName = ref('')

const tabs: { key: TabKey; label: string }[] = [
  { key: 'overview', label: '概览' },
  { key: 'containers', label: '容器' },
  { key: 'images', label: '镜像' },
  { key: 'compose', label: 'Compose' },
  { key: 'networks', label: '网络' },
  { key: 'volumes', label: '数据卷' },
  { key: 'monitor', label: '监控' },
  { key: 'audit', label: '审计' },
]

const hostOptions = computed<MaxSelectOption[]>(() => [
  { label: '选择主机', value: '' },
  ...hosts.value.map((h) => ({ label: `${h.name} (${h.host})`, value: String(h.id) })),
])

const hid = computed(() => Number(hostId.value) || 0)

const filteredContainers = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  if (!q) return containers.value
  return containers.value.filter(
    (c) =>
      c.name.toLowerCase().includes(q) ||
      c.image.toLowerCase().includes(q) ||
      c.id.toLowerCase().includes(q),
  )
})

const filteredImages = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  if (!q) return images.value
  return images.value.filter(
    (i) =>
      i.repository.toLowerCase().includes(q) ||
      i.tag.toLowerCase().includes(q) ||
      i.id.toLowerCase().includes(q),
  )
})

function stateClass(state: string) {
  const s = (state || '').toLowerCase()
  if (s.includes('running')) return 'ok'
  if (s.includes('paused')) return 'warn'
  if (s.includes('restart')) return 'warn'
  if (s.includes('exited') || s.includes('dead')) return 'bad'
  return ''
}

function imageRef(img: DockerImage) {
  return img.repository === '<none>' ? img.id : `${img.repository}:${img.tag}`
}

async function downloadAuthed(url: string, fallbackName: string) {
  const token = localStorage.getItem('maxadmin_token') || ''
  const res = await fetch(url, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
  if (!res.ok) throw new Error('下载失败')
  const blob = await res.blob()
  const cd = res.headers.get('Content-Disposition') || ''
  const m = /filename="?([^"]+)"?/.exec(cd)
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = m?.[1] || fallbackName
  a.click()
  URL.revokeObjectURL(a.href)
}

async function ensureHost(): Promise<number> {
  if (!hid.value) {
    Message.warning('请先选择主机')
    throw new Error('no host')
  }
  return hid.value
}

function goTab(key: TabKey) {
  tab.value = key
}

async function loadTab() {
  if (!hid.value) {
    overview.value = null
    containers.value = []
    images.value = []
    networks.value = []
    volumes.value = []
    composeApps.value = []
    stats.value = []
    audits.value = []
    return
  }
  loading.value = true
  try {
    const id = hid.value
    if (tab.value === 'overview') {
      overview.value = await fetchDockerOverview(id)
    } else if (tab.value === 'containers') {
      containers.value = await fetchDockerContainers(id, true)
    } else if (tab.value === 'images') {
      images.value = await fetchDockerImages(id)
    } else if (tab.value === 'compose') {
      composeApps.value = await fetchDockerCompose(id)
    } else if (tab.value === 'networks') {
      networks.value = await fetchDockerNetworks(id)
    } else if (tab.value === 'volumes') {
      volumes.value = await fetchDockerVolumes(id)
    } else if (tab.value === 'monitor') {
      stats.value = await fetchDockerContainerStats(id)
    } else if (tab.value === 'audit') {
      audits.value = await fetchDockerAudit({ hostId: id, limit: 100 })
    }
  } catch (err) {
    Message.error(err instanceof Error ? err.message : '加载失败')
  } finally {
    loading.value = false
  }
}

function clearMonitorTimer() {
  if (monitorTimer) {
    window.clearInterval(monitorTimer)
    monitorTimer = null
  }
}

function syncMonitorTimer() {
  clearMonitorTimer()
  if (monitorAuto.value && tab.value === 'monitor' && hid.value) {
    monitorTimer = window.setInterval(() => {
      void loadTab()
    }, 5000)
  }
}

async function onContainerAction(c: DockerContainer, action: string) {
  const id = await ensureHost()
  if (action === 'remove' || action === 'forceRemove') {
    const ok = await MaxConfirm.delete({
      title: action === 'forceRemove' ? '强制删除容器' : '删除容器',
      message: `确定删除容器「${c.name || c.id}」吗？`,
    })
    if (!ok) return
  }
  try {
    await dockerContainerAction(id, c.id || c.name, action)
    Message.success(`已执行 ${action}`)
    await loadTab()
  } catch (err) {
    Message.error(err instanceof Error ? err.message : '操作失败')
  }
}

function showLogs(c: DockerContainer) {
  if (!hid.value) {
    Message.warning('请先选择主机')
    return
  }
  void MaxPopup.open({
    title: `日志 · ${c.name || c.id}`,
    size: 'lg',
    content: DockerLogBody,
    contentProps: { hostId: hid.value, container: c.id || c.name, title: c.name || c.id },
    confirmText: '关闭',
    showCancel: false,
  })
}

async function showDetail(c: DockerContainer) {
  const id = await ensureHost()
  try {
    const data = await fetchDockerContainerDetail(id, c.id || c.name)
    void MaxPopup.open({
      title: `详情 · ${c.name || c.id}`,
      size: 'lg',
      content: DockerDetailBody,
      contentProps: { data },
      confirmText: '关闭',
      showCancel: false,
    })
  } catch (err) {
    Message.error(err instanceof Error ? err.message : '读取详情失败')
  }
}

async function openExec(c: DockerContainer) {
  const id = await ensureHost()
  void MaxPopup.open({
    title: `终端 · ${c.name || c.id}`,
    size: 'lg',
    content: DockerExecBody,
    contentProps: { hostId: id, container: c.id || c.name },
    confirmText: '关闭',
    showCancel: false,
  })
}

async function doPull() {
  const id = await ensureHost()
  const image = pullImage.value.trim()
  if (!image) {
    Message.warning('请输入镜像，如 nginx:latest')
    return
  }
  loading.value = true
  try {
    await dockerImagePull(id, image)
    Message.success('拉取完成')
    pullImage.value = ''
    await loadTab()
  } catch (err) {
    Message.error(err instanceof Error ? err.message : '拉取失败')
  } finally {
    loading.value = false
  }
}

async function removeImage(img: DockerImage, force = false) {
  const id = await ensureHost()
  const ref = imageRef(img)
  const ok = await MaxConfirm.delete({
    title: force ? '强制删除镜像' : '删除镜像',
    message: `确定删除镜像「${ref}」吗？`,
  })
  if (!ok) return
  try {
    await dockerImageRemove(id, ref, force)
    Message.success('镜像已删除')
    await loadTab()
  } catch (err) {
    Message.error(err instanceof Error ? err.message : '删除失败')
  }
}

async function inspectImage(img: DockerImage) {
  const id = await ensureHost()
  const ref = imageRef(img)
  try {
    const data = await fetchDockerImageInspect(id, ref)
    void MaxPopup.open({
      title: `镜像 · ${ref}`,
      size: 'lg',
      content: DockerJsonBody,
      contentProps: { data },
      confirmText: '关闭',
      showCancel: false,
    })
  } catch (err) {
    Message.error(err instanceof Error ? err.message : '读取失败')
  }
}

async function exportImage(img: DockerImage) {
  const id = await ensureHost()
  const ref = imageRef(img)
  try {
    await downloadAuthed(dockerImageExportUrl(id, ref), `${ref.replace(/[/:]/g, '_')}.tar`)
    Message.success('导出已开始')
  } catch (err) {
    Message.error(err instanceof Error ? err.message : '导出失败')
  }
}

function triggerImport() {
  importInput.value?.click()
}

async function onImportFile(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  const id = await ensureHost()
  loading.value = true
  try {
    await dockerImageImport(id, file)
    Message.success('镜像导入完成')
    await loadTab()
  } catch (err) {
    Message.error(err instanceof Error ? err.message : '导入失败')
  } finally {
    loading.value = false
  }
}

async function onCompose(app: DockerComposeApp, action: string) {
  const id = await ensureHost()
  if (action === 'down') {
    const ok = await MaxConfirm.delete({
      title: '停止 Compose 应用',
      message: `确定停止并移除应用「${app.name}」吗？`,
    })
    if (!ok) return
  }
  try {
    await dockerComposeAction(id, app.name, action)
    Message.success(`Compose ${action} 完成`)
    await loadTab()
  } catch (err) {
    Message.error(err instanceof Error ? err.message : '操作失败')
  }
}

async function showComposeConfig(app: DockerComposeApp) {
  const id = await ensureHost()
  try {
    const data = await fetchDockerComposeConfig(id, app.name, app.configFiles || '')
    void MaxPopup.open({
      title: `配置 · ${app.name}`,
      size: 'lg',
      content: DockerLogBody,
      contentProps: { staticContent: data.config, title: app.name },
      confirmText: '关闭',
      showCancel: false,
    })
  } catch (err) {
    Message.error(err instanceof Error ? err.message : '读取配置失败')
  }
}

async function showComposeLogs(app: DockerComposeApp) {
  const id = await ensureHost()
  try {
    const data = await fetchDockerComposeLogs(id, app.name, 300)
    void MaxPopup.open({
      title: `日志 · ${app.name}`,
      size: 'lg',
      content: DockerLogBody,
      contentProps: { staticContent: data.logs, title: app.name },
      confirmText: '关闭',
      showCancel: false,
    })
  } catch (err) {
    Message.error(err instanceof Error ? err.message : '读取日志失败')
  }
}

async function createNetwork() {
  const id = await ensureHost()
  const name = newNetwork.value.trim()
  if (!name) {
    Message.warning('请填写网络名称')
    return
  }
  try {
    await dockerNetworkCreate(id, name, newNetworkDriver.value || 'bridge')
    Message.success('网络已创建')
    newNetwork.value = ''
    await loadTab()
  } catch (err) {
    Message.error(err instanceof Error ? err.message : '创建失败')
  }
}

async function removeNetwork(n: DockerNetwork) {
  const id = await ensureHost()
  const ok = await MaxConfirm.delete({
    title: '删除网络',
    message: `确定删除网络「${n.name}」吗？`,
  })
  if (!ok) return
  try {
    await dockerNetworkRemove(id, n.name)
    Message.success('网络已删除')
    await loadTab()
  } catch (err) {
    Message.error(err instanceof Error ? err.message : '删除失败')
  }
}

async function inspectNetwork(n: DockerNetwork) {
  const id = await ensureHost()
  try {
    const data = await fetchDockerNetworkInspect(id, n.name)
    void MaxPopup.open({
      title: `网络 · ${n.name}`,
      size: 'lg',
      content: DockerJsonBody,
      contentProps: { data },
      confirmText: '关闭',
      showCancel: false,
    })
  } catch (err) {
    Message.error(err instanceof Error ? err.message : '读取失败')
  }
}

async function createVolume() {
  const id = await ensureHost()
  const name = newVolume.value.trim()
  if (!name) {
    Message.warning('请填写数据卷名称')
    return
  }
  try {
    await dockerVolumeCreate(id, name)
    Message.success('数据卷已创建')
    newVolume.value = ''
    await loadTab()
  } catch (err) {
    Message.error(err instanceof Error ? err.message : '创建失败')
  }
}

async function removeVolume(v: DockerVolume) {
  const id = await ensureHost()
  const ok = await MaxConfirm.delete({
    title: '删除数据卷',
    message: `确定删除数据卷「${v.name}」吗？此操作不可恢复。`,
  })
  if (!ok) return
  try {
    await dockerVolumeRemove(id, v.name)
    Message.success('数据卷已删除')
    await loadTab()
  } catch (err) {
    Message.error(err instanceof Error ? err.message : '删除失败')
  }
}

async function inspectVolume(v: DockerVolume) {
  const id = await ensureHost()
  try {
    const data = await fetchDockerVolumeInspect(id, v.name)
    void MaxPopup.open({
      title: `数据卷 · ${v.name}`,
      size: 'md',
      content: DockerJsonBody,
      contentProps: { data },
      confirmText: '关闭',
      showCancel: false,
    })
  } catch (err) {
    Message.error(err instanceof Error ? err.message : '读取失败')
  }
}

async function backupVolume(v: DockerVolume) {
  const id = await ensureHost()
  try {
    await downloadAuthed(dockerVolumeBackupUrl(id, v.name), `${v.name}.tar.gz`)
    Message.success('备份下载已开始')
  } catch (err) {
    Message.error(err instanceof Error ? err.message : '备份失败')
  }
}

function triggerRestore(v: DockerVolume) {
  restoreVolumeName.value = v.name
  restoreInput.value?.click()
}

async function onRestoreFile(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  const name = restoreVolumeName.value
  restoreVolumeName.value = ''
  if (!file || !name) return
  const id = await ensureHost()
  loading.value = true
  try {
    await dockerVolumeRestore(id, name, file)
    Message.success('数据卷恢复完成')
    await loadTab()
  } catch (err) {
    Message.error(err instanceof Error ? err.message : '恢复失败')
  } finally {
    loading.value = false
  }
}

watch([hostId, tab], () => {
  void loadTab()
  syncMonitorTimer()
})

watch(monitorAuto, () => {
  syncMonitorTimer()
})

onMounted(async () => {
  try {
    hosts.value = await fetchLinuxHosts()
  } catch {
    Message.error('加载主机列表失败')
  }
})

onUnmounted(() => {
  clearMonitorTimer()
})
</script>

<template>
  <div class="dk-page">
    <LayoutToolbar>
      <template #left>
        <MaxSelect v-model="hostId" :width="240" :options="hostOptions" />
        <MaxButton variant="primary" :disabled="loading || !hostId" @click="loadTab">
          {{ loading ? '加载中…' : '刷新' }}
        </MaxButton>
      </template>
      <template #right>
        <MaxButton @click="router.push({ name: 'linuxHosts' })">主机管理</MaxButton>
        <MaxButton @click="router.push({ name: 'linuxSsh' })">SSH 终端</MaxButton>
      </template>
    </LayoutToolbar>

    <div class="dk-layout">
      <aside class="dk-side">
        <button
          v-for="t in tabs"
          :key="t.key"
          type="button"
          class="side-item"
          :class="{ 'side-item--on': tab === t.key }"
          @click="goTab(t.key)"
        >
          {{ t.label }}
        </button>
      </aside>

      <section class="dk-main">
        <p v-if="!hostId" class="dk-empty">请选择一台 Linux 主机开始管理 Docker</p>

        <!-- 概览 -->
        <div v-else-if="tab === 'overview'" class="dk-section">
          <p v-if="!overview && !loading" class="dk-empty">暂无数据</p>
          <div v-if="overview" class="dk-dash">
            <button type="button" class="dk-card dk-card--click" @click="goTab('overview')">
              <h4>Docker Status</h4>
              <strong :class="overview.status === 'Running' ? 'ok' : 'bad'"
                >● {{ overview.status }}</strong
              >
              <span>Engine {{ overview.version || '-' }}</span>
              <span>{{ overview.os || overview.driver || '-' }}</span>
            </button>
            <button type="button" class="dk-card dk-card--click" @click="goTab('containers')">
              <h4>Containers</h4>
              <strong>{{ overview.containers.total }}</strong>
              <span>Running {{ overview.containers.running }}</span>
              <span>Stopped {{ overview.containers.stopped }}</span>
              <span v-if="overview.containers.paused">Paused {{ overview.containers.paused }}</span>
            </button>
            <button type="button" class="dk-card dk-card--click" @click="goTab('images')">
              <h4>Images</h4>
              <strong>{{ overview.images }}</strong>
              <span>本地镜像</span>
            </button>
            <button type="button" class="dk-card dk-card--click" @click="goTab('volumes')">
              <h4>Volumes</h4>
              <strong>{{ overview.volumes }}</strong>
              <span>数据卷</span>
            </button>
            <button type="button" class="dk-card dk-card--click" @click="goTab('networks')">
              <h4>Networks</h4>
              <strong>{{ overview.networks }}</strong>
              <span>网络</span>
            </button>
            <article class="dk-card dk-card--wide">
              <h4>Storage</h4>
              <span class="dk-mono">{{ overview.storage || '-' }}</span>
            </article>
          </div>
        </div>

        <!-- 容器 -->
        <div v-else-if="tab === 'containers'" class="dk-section">
          <div class="dk-toolbar-row">
            <MaxInput v-model="keyword" placeholder="搜索容器…" />
          </div>
          <p v-if="!filteredContainers.length && !loading" class="dk-empty">暂无容器</p>
          <div class="dk-list">
            <article v-for="c in filteredContainers" :key="c.id" class="dk-item">
              <header>
                <strong>{{ c.name || c.id }}</strong>
                <em :class="stateClass(c.state)">{{ c.status || c.state }}</em>
              </header>
              <p>{{ c.image }}</p>
              <p class="dk-meta">{{ c.id }} · {{ c.created }}</p>
              <p class="dk-meta">
                CPU {{ c.cpu || '-' }} · Mem {{ c.mem || '-' }}
                <template v-if="c.memPerc">（{{ c.memPerc }}）</template>
              </p>
              <p class="dk-meta">{{ c.ports || '无端口映射' }} · {{ c.networks || '-' }}</p>
              <div class="dk-actions">
                <MaxButton size="sm" @click="onContainerAction(c, 'start')">启动</MaxButton>
                <MaxButton size="sm" @click="onContainerAction(c, 'stop')">停止</MaxButton>
                <MaxButton size="sm" @click="onContainerAction(c, 'restart')">重启</MaxButton>
                <MaxButton size="sm" @click="onContainerAction(c, 'pause')">暂停</MaxButton>
                <MaxButton size="sm" @click="onContainerAction(c, 'unpause')">恢复</MaxButton>
                <MaxButton size="sm" @click="showLogs(c)">日志</MaxButton>
                <MaxButton size="sm" @click="showDetail(c)">详情</MaxButton>
                <MaxButton size="sm" variant="primary" @click="openExec(c)">终端</MaxButton>
                <MaxButton size="sm" @click="onContainerAction(c, 'remove')">删除</MaxButton>
                <MaxButton size="sm" @click="onContainerAction(c, 'forceRemove')">强删</MaxButton>
              </div>
            </article>
          </div>
        </div>

        <!-- 镜像 -->
        <div v-else-if="tab === 'images'" class="dk-section">
          <div class="dk-form-row">
            <MaxInput v-model="pullImage" placeholder="拉取镜像，如 nginx:alpine" />
            <MaxButton variant="primary" :disabled="loading" @click="doPull">拉取</MaxButton>
            <MaxButton :disabled="loading" @click="triggerImport">导入</MaxButton>
            <input
              ref="importInput"
              type="file"
              accept=".tar,.tar.gz,.tgz"
              class="dk-hidden"
              @change="onImportFile"
            />
            <MaxInput v-model="keyword" placeholder="搜索镜像…" />
          </div>
          <p v-if="!filteredImages.length && !loading" class="dk-empty">暂无镜像</p>
          <div class="dk-list">
            <article v-for="img in filteredImages" :key="img.id + img.tag" class="dk-item">
              <header>
                <strong>{{ img.repository }}:{{ img.tag }}</strong>
                <em>{{ img.size }}</em>
              </header>
              <p class="dk-meta">{{ img.id }} · {{ img.created }}</p>
              <p class="dk-meta">
                使用
                {{ img.usedCount ?? (img.usedBy?.length || 0) }}
                <template v-if="img.usedBy?.length"> · {{ img.usedBy.join(', ') }}</template>
              </p>
              <div class="dk-actions">
                <MaxButton size="sm" @click="inspectImage(img)">详情</MaxButton>
                <MaxButton size="sm" @click="exportImage(img)">导出</MaxButton>
                <MaxButton size="sm" @click="removeImage(img, false)">删除</MaxButton>
                <MaxButton size="sm" @click="removeImage(img, true)">强删</MaxButton>
              </div>
            </article>
          </div>
        </div>

        <!-- Compose -->
        <div v-else-if="tab === 'compose'" class="dk-section">
          <p v-if="!composeApps.length && !loading" class="dk-empty">
            未发现 Compose 应用（需主机安装 docker compose）
          </p>
          <div class="dk-list">
            <article v-for="app in composeApps" :key="app.name" class="dk-item">
              <header>
                <strong>{{ app.name }}</strong>
                <em>{{ app.status }}</em>
              </header>
              <p class="dk-meta">
                {{ app.configFiles || '-' }}
                <template v-if="app.serviceCount != null"> · {{ app.serviceCount }} 服务</template>
              </p>
              <div class="dk-actions">
                <MaxButton size="sm" @click="onCompose(app, 'up')">启动</MaxButton>
                <MaxButton size="sm" @click="onCompose(app, 'stop')">停止</MaxButton>
                <MaxButton size="sm" @click="onCompose(app, 'restart')">重启</MaxButton>
                <MaxButton size="sm" @click="onCompose(app, 'pull')">Pull</MaxButton>
                <MaxButton size="sm" @click="onCompose(app, 'update')">Update</MaxButton>
                <MaxButton size="sm" @click="onCompose(app, 'down')">Down</MaxButton>
                <MaxButton size="sm" @click="onCompose(app, 'ps')">状态</MaxButton>
                <MaxButton size="sm" @click="showComposeConfig(app)">配置</MaxButton>
                <MaxButton size="sm" @click="showComposeLogs(app)">日志</MaxButton>
              </div>
            </article>
          </div>
        </div>

        <!-- 网络 -->
        <div v-else-if="tab === 'networks'" class="dk-section">
          <div class="dk-form-row">
            <MaxInput v-model="newNetwork" placeholder="新网络名称" />
            <MaxSelect
              v-model="newNetworkDriver"
              :width="120"
              :options="[
                { label: 'bridge', value: 'bridge' },
                { label: 'overlay', value: 'overlay' },
                { label: 'host', value: 'host' },
              ]"
            />
            <MaxButton variant="primary" @click="createNetwork">创建</MaxButton>
          </div>
          <div class="dk-list">
            <article v-for="n in networks" :key="n.id" class="dk-item">
              <header>
                <strong>{{ n.name }}</strong>
                <em>{{ n.driver }} / {{ n.scope }}</em>
              </header>
              <p class="dk-meta">{{ n.id }}</p>
              <p class="dk-meta">
                容器 {{ n.containerCount ?? n.containers?.length ?? 0 }}
                <template v-if="n.containers?.length"> · {{ n.containers.join(', ') }}</template>
              </p>
              <div class="dk-actions">
                <MaxButton size="sm" @click="inspectNetwork(n)">详情</MaxButton>
                <MaxButton size="sm" @click="removeNetwork(n)">删除</MaxButton>
              </div>
            </article>
          </div>
        </div>

        <!-- 数据卷 -->
        <div v-else-if="tab === 'volumes'" class="dk-section">
          <div class="dk-form-row">
            <MaxInput v-model="newVolume" placeholder="新数据卷名称" />
            <MaxButton variant="primary" @click="createVolume">创建</MaxButton>
            <input
              ref="restoreInput"
              type="file"
              accept=".tar,.tar.gz,.tgz"
              class="dk-hidden"
              @change="onRestoreFile"
            />
          </div>
          <div class="dk-list">
            <article v-for="v in volumes" :key="v.name" class="dk-item">
              <header>
                <strong>{{ v.name }}</strong>
                <em>{{ v.driver }}</em>
              </header>
              <p class="dk-meta">{{ v.mountpoint || '-' }}</p>
              <p class="dk-meta">
                创建 {{ v.created || '-' }} · 使用
                {{ v.usedCount ?? (v.usedBy?.length || 0) }}
                <template v-if="v.usedBy?.length"> · {{ v.usedBy.join(', ') }}</template>
              </p>
              <div class="dk-actions">
                <MaxButton size="sm" @click="inspectVolume(v)">详情</MaxButton>
                <MaxButton size="sm" @click="backupVolume(v)">备份</MaxButton>
                <MaxButton size="sm" @click="triggerRestore(v)">恢复</MaxButton>
                <MaxButton size="sm" @click="removeVolume(v)">删除</MaxButton>
              </div>
            </article>
          </div>
        </div>

        <!-- 监控 -->
        <div v-else-if="tab === 'monitor'" class="dk-section">
          <div class="dk-toolbar-row">
            <label class="dk-chk">
              <input v-model="monitorAuto" type="checkbox" />
              自动刷新（5s）
            </label>
          </div>
          <p v-if="!stats.length && !loading" class="dk-empty">暂无运行中容器统计</p>
          <div class="dk-list">
            <article v-for="s in stats" :key="s.id || s.name" class="dk-item">
              <header>
                <strong>{{ s.name || s.id }}</strong>
                <em>CPU {{ s.cpu }}</em>
              </header>
              <p>内存 {{ s.memUsage }}（{{ s.memPerc }}）</p>
              <p class="dk-meta">Net {{ s.netIO }} · IO {{ s.blockIO }}</p>
            </article>
          </div>
        </div>

        <!-- 审计 -->
        <div v-else-if="tab === 'audit'" class="dk-section">
          <p v-if="!audits.length && !loading" class="dk-empty">暂无操作记录</p>
          <div class="dk-list">
            <article v-for="a in audits" :key="a.id" class="dk-item">
              <header>
                <strong>{{ a.action }} · {{ a.target || '-' }}</strong>
                <em :class="a.success ? 'ok' : 'bad'">{{ a.success ? '成功' : '失败' }}</em>
              </header>
              <p class="dk-meta">{{ a.username }} · {{ a.createdAt }}</p>
              <p v-if="a.detail" class="dk-meta">{{ a.detail }}</p>
            </article>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.dk-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  gap: 12px;
}

.dk-layout {
  display: grid;
  grid-template-columns: 160px 1fr;
  gap: 12px;
  flex: 1;
  min-height: 0;
}

.dk-side {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-height: 0;
  overflow: auto;
  padding: 10px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.side-item {
  display: flex;
  align-items: center;
  width: 100%;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.75);
  text-align: left;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
}

.side-item:hover,
.side-item--on {
  background: rgba(10, 132, 255, 0.18);
  color: #fff;
}

.dk-main {
  min-height: 0;
  overflow: auto;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.03);
  padding: 14px;
}

.dk-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.dk-empty {
  margin: 48px 0;
  text-align: center;
  color: rgba(255, 255, 255, 0.4);
  font-size: 13px;
}

.dk-dash {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}

.dk-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
  text-align: left;
}

.dk-card--click {
  margin: 0;
  cursor: pointer;
  font: inherit;
}

.dk-card--click:hover {
  border-color: rgba(10, 132, 255, 0.45);
  background: rgba(10, 132, 255, 0.12);
}

.dk-card--wide {
  grid-column: 1 / -1;
}

.dk-card h4 {
  margin: 0;
  font-size: 12px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.5);
}

.dk-card strong {
  font-size: 22px;
  font-weight: 600;
}

.dk-card span {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
}

.dk-mono {
  font-family: Menlo, Monaco, 'Courier New', monospace;
  word-break: break-all;
}

.dk-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dk-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(0, 0, 0, 0.22);
}

.dk-item header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.dk-item strong {
  font-size: 14px;
}

.dk-item em {
  font-style: normal;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
}

.dk-item p {
  margin: 0;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.75);
}

.dk-meta {
  font-size: 11px !important;
  color: rgba(255, 255, 255, 0.42) !important;
  word-break: break-all;
}

.dk-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
}

.dk-form-row,
.dk-toolbar-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.dk-chk {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
}

.dk-hidden {
  display: none;
}

.ok {
  color: #3ddc84 !important;
}
.warn {
  color: #febc2e !important;
}
.bad {
  color: #ff6b6b !important;
}
</style>
