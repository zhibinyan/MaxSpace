<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  fetchLinuxHosts,
  sftpChmod,
  sftpChown,
  sftpDelete,
  sftpDownloadUrl,
  sftpDownloadZip,
  sftpList,
  sftpMkdir,
  sftpRead,
  sftpRename,
  sftpSearch,
  sftpWrite,
  type LinuxHost,
  type SftpEntry,
} from '@/api/linux'
import Message from '@/components/massage'
import MaxConfirm from '@/components/maxConfirm'
import MaxPopup from '@/components/maxPopup'
import { MaxButton } from '@/components/maxButton'
import { MaxForm, MaxInput } from '@/components/maxInput'
import { MaxSelect, type MaxSelectOption } from '@/components/maxSelect'
import { MaxSvg } from '@/components/maxSvg'
import { LayoutToolbar } from '@/layout'
import FileNameFormBody from '@/views/files/FileNameFormBody.vue'
import { defaultSftpPathForOs, isWindowsOs } from '../osOptions'
import PropsFormBody from './PropsFormBody.vue'
import {
  loadSftpWorkspace,
  saveSftpWorkspace,
} from './sftpSessionStore'
import {
  cancelTask,
  clearFinished,
  enqueueUploads,
  pauseTask,
  progressOf,
  resumeTask,
  toggleTransferPanel,
  transferPanelOpen,
  transferTasks,
} from './transferQueue'

defineOptions({ name: 'SftpFileView' })

const route = useRoute()
const router = useRouter()

const hosts = ref<LinuxHost[]>([])
const hostId = ref('')
const path = ref('/')
const isWindowsHost = ref(false)
const loading = ref(false)
const entries = ref<SftpEntry[]>([])
const breadcrumbs = ref<Array<{ name: string; path: string }>>([{ name: '/', path: '/' }])
const keyword = ref('')
const selected = ref<SftpEntry | null>(null)
const selectedPaths = ref<Set<string>>(new Set())
const lastClickedPath = ref('')
const fileInputRef = ref<HTMLInputElement | null>(null)
const searchMode = ref(false)
const searchResults = ref<Array<SftpEntry & { parent?: string }>>([])
const searching = ref(false)
/** 与 SSH workspaceReady 同理：初始化完成前不落盘、不因 watch 重置路径 */
const workspaceReady = ref(false)
const pathByHost = reactive<Record<string, string>>({})

const ctxMenu = reactive<{
  open: boolean
  x: number
  y: number
  row: SftpEntry | null
}>({
  open: false,
  x: 0,
  y: 0,
  row: null,
})

const editor = reactive({
  open: false,
  path: '',
  name: '',
  content: '',
  saving: false,
})

const nameForm = reactive({ name: '' })
const propsForm = reactive({ mode: '755', uid: '0', gid: '0' })

const hostOptions = computed<MaxSelectOption[]>(() => [
  { label: '选择主机…', value: '' },
  ...hosts.value.map((h) => ({ label: `${h.name} (${h.host})`, value: String(h.id) })),
])

const currentHost = computed(() => hosts.value.find((h) => String(h.id) === hostId.value) ?? null)

const displayList = computed(() => {
  if (searchMode.value) return searchResults.value
  const q = keyword.value.trim().toLowerCase()
  if (!q) return entries.value
  return entries.value.filter((e) => e.name.toLowerCase().includes(q))
})

const activeUploads = computed(() =>
  transferTasks.value.filter((t) => ['queued', 'running', 'paused', 'error'].includes(t.status)).length,
)

function joinPath(parent: string, name: string) {
  if (isWindowsHost.value) {
    const base = parent.replace(/\\/g, '/').replace(/\/+$/, '')
    return `${base}/${name}`
  }
  return parent === '/' ? `/${name}` : `${parent.replace(/\/+$/, '')}/${name}`
}

function parentPathOf(full: string) {
  const normalized = full.replace(/\\/g, '/')
  if (isWindowsHost.value) {
    const idx = normalized.lastIndexOf('/')
    if (idx <= 2) return 'C:/'
    return normalized.slice(0, idx) || 'C:/'
  }
  const idx = normalized.lastIndexOf('/')
  if (idx <= 0) return '/'
  return normalized.slice(0, idx) || '/'
}

async function loadHosts() {
  hosts.value = await fetchLinuxHosts()
}

async function loadDir() {
  if (!hostId.value) {
    entries.value = []
    return
  }
  loading.value = true
  searchMode.value = false
  try {
    const data = await sftpList(Number(hostId.value), path.value)
    path.value = data.path
    breadcrumbs.value = data.breadcrumbs
    entries.value = data.list
    isWindowsHost.value = !!data.windows || isWindowsOs(currentHost.value?.osName)
    selected.value = null
    selectedPaths.value = new Set()
  } catch (err) {
    Message.error(err instanceof Error ? err.message : '列出目录失败')
  } finally {
    loading.value = false
  }
}

function goPath(p: string) {
  path.value = p
  void loadDir()
}

function toggleSelect(row: SftpEntry, e: MouseEvent) {
  selected.value = row
  const set = new Set(selectedPaths.value)
  if (e.metaKey || e.ctrlKey) {
    if (set.has(row.path)) set.delete(row.path)
    else set.add(row.path)
    lastClickedPath.value = row.path
  } else if (e.shiftKey && lastClickedPath.value) {
    const list = displayList.value
    const a = list.findIndex((x) => x.path === lastClickedPath.value)
    const b = list.findIndex((x) => x.path === row.path)
    if (a >= 0 && b >= 0) {
      const [lo, hi] = a < b ? [a, b] : [b, a]
      for (let i = lo; i <= hi; i++) set.add(list[i].path)
    } else {
      set.clear()
      set.add(row.path)
    }
  } else {
    set.clear()
    set.add(row.path)
    lastClickedPath.value = row.path
  }
  selectedPaths.value = set
}

type SftpRow = SftpEntry & { parent?: string }

function openEntry(row: SftpRow) {
  selected.value = row
  if (searchMode.value) {
    if (row.isDir) {
      goPath(row.path)
      return
    }
    goPath(row.parent || parentPathOf(row.path))
    if (row.editable) void openEditor(row)
    return
  }
  if (row.isDir) {
    goPath(row.path)
    return
  }
  if (row.editable) void openEditor(row)
}

function closeCtxMenu() {
  ctxMenu.open = false
  ctxMenu.row = null
}

function openCtxMenu(row: SftpEntry, e: MouseEvent) {
  selected.value = row
  if (!selectedPaths.value.has(row.path)) {
    selectedPaths.value = new Set([row.path])
  }
  ctxMenu.row = row
  ctxMenu.x = e.clientX
  ctxMenu.y = e.clientY
  ctxMenu.open = true
}

function runCtxAction(
  action: 'open' | 'edit' | 'download' | 'rename' | 'delete' | 'props' | 'zip',
) {
  const row = ctxMenu.row
  closeCtxMenu()
  if (!row) return
  if (action === 'open') openEntry(row)
  else if (action === 'edit') void openEditor(row)
  else if (action === 'download') handleDownload(row)
  else if (action === 'rename') handleRename(row)
  else if (action === 'delete') void handleDelete(row)
  else if (action === 'props') handleProps(row)
  else if (action === 'zip') void handleZipDownload()
}

function iconName(row: SftpEntry) {
  if (row.isDir) return 'files/folder'
  const map: Record<string, string> = {
    png: 'files/image',
    jpg: 'files/image',
    jpeg: 'files/image',
    gif: 'files/image',
    webp: 'files/image',
    mp4: 'files/video',
    mov: 'files/video',
    mp3: 'files/audio',
    wav: 'files/audio',
    pdf: 'files/pdf',
    zip: 'files/archive',
    tar: 'files/archive',
    gz: 'files/archive',
    md: 'files/markdown',
    py: 'files/code',
    js: 'files/code',
    ts: 'files/code',
    vue: 'files/code',
    json: 'files/code',
    sh: 'files/code',
  }
  return map[row.ext] || 'files/file'
}

function handleCreateDir() {
  nameForm.name = ''
  void MaxPopup.open({
    title: '新建目录',
    size: 'sm',
    content: FileNameFormBody,
    contentProps: { form: nameForm, label: '目录名', placeholder: '请输入目录名' },
    onConfirm: async () => {
      const name = nameForm.name.trim()
      if (!name) {
        Message.warning('请输入目录名')
        return false
      }
      const target = joinPath(path.value, name)
      try {
        await sftpMkdir(Number(hostId.value), target)
        await loadDir()
        return true
      } catch {
        return false
      }
    },
  })
}

function handleRename(row: SftpEntry) {
  nameForm.name = row.name
  void MaxPopup.open({
    title: '重命名',
    size: 'sm',
    content: FileNameFormBody,
    contentProps: { form: nameForm, label: '新名称', placeholder: '请输入新名称' },
    onConfirm: async () => {
      const name = nameForm.name.trim()
      if (!name || name === row.name) return true
      const parent = parentPathOf(row.path)
      const newPath = joinPath(parent, name)
      try {
        await sftpRename(Number(hostId.value), row.path, newPath)
        await loadDir()
        return true
      } catch {
        return false
      }
    },
  })
}

function handleProps(row: SftpEntry) {
  propsForm.mode = (row.mode || '0o755').replace(/^0o/, '')
  propsForm.uid = '0'
  propsForm.gid = '0'
  void MaxPopup.open({
    title: `属性 · ${row.name}`,
    size: 'sm',
    content: PropsFormBody,
    contentProps: { form: propsForm, windows: isWindowsHost.value },
    onConfirm: async () => {
      try {
        await sftpChmod(Number(hostId.value), row.path, propsForm.mode.trim())
        if (!isWindowsHost.value) {
          const uid = Number(propsForm.uid)
          const gid = Number(propsForm.gid)
          if (!Number.isNaN(uid) && !Number.isNaN(gid)) {
            await sftpChown(Number(hostId.value), row.path, uid, gid)
          }
        }
        await loadDir()
        return true
      } catch {
        return false
      }
    },
  })
}

async function handleDelete(row: SftpEntry) {
  const ok = await MaxConfirm.delete({
    title: '删除确认',
    message: `确定删除「${row.name}」吗？此操作不可恢复。`,
  })
  if (!ok) return
  await sftpDelete(Number(hostId.value), row.path)
  await loadDir()
}

function handleDownload(row: SftpEntry) {
  if (row.isDir) {
    void sftpDownloadZip(Number(hostId.value), [row.path]).catch((err) => {
      Message.error(err instanceof Error ? err.message : '打包下载失败')
    })
    return
  }
  const a = document.createElement('a')
  a.href = sftpDownloadUrl(Number(hostId.value), row.path)
  a.download = row.name
  a.click()
}

async function handleZipDownload() {
  if (!hostId.value) return
  const paths = [...selectedPaths.value]
  if (!paths.length && selected.value) paths.push(selected.value.path)
  if (!paths.length) {
    Message.warning('请先选择文件或目录')
    return
  }
  try {
    await sftpDownloadZip(Number(hostId.value), paths)
    Message.success('打包下载已开始')
  } catch (err) {
    Message.error(err instanceof Error ? err.message : '打包下载失败')
  }
}

function triggerUpload() {
  fileInputRef.value?.click()
}

function enqueueFiles(files: FileList | File[]) {
  if (!hostId.value) return
  enqueueUploads(Number(hostId.value), path.value, Array.from(files))
  Message.success('已加入传输队列')
  const timer = window.setInterval(() => {
    const busy = transferTasks.value.some((t) => ['queued', 'running'].includes(t.status))
    if (!busy) {
      window.clearInterval(timer)
      void loadDir()
    }
  }, 1200)
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files?.length || !hostId.value) return
  enqueueFiles(input.files)
  input.value = ''
}

function onDrop(e: DragEvent) {
  e.preventDefault()
  if (!hostId.value || !e.dataTransfer?.files?.length) return
  enqueueFiles(e.dataTransfer.files)
}

async function runSearch() {
  if (!hostId.value) {
    Message.warning('请先选择主机')
    return
  }
  const q = keyword.value.trim()
  if (!q) {
    Message.warning('请输入搜索关键词')
    return
  }
  searching.value = true
  try {
    const data = await sftpSearch(Number(hostId.value), path.value, q, {
      recursive: true,
      maxDepth: 5,
    })
    searchMode.value = true
    searchResults.value = data.list
    if (!data.list.length) {
      Message.warning('未找到匹配项')
    } else if (data.truncated) {
      Message.warning('结果过多已截断，请缩小范围')
    }
  } catch (err) {
    Message.error(err instanceof Error ? err.message : '搜索失败')
  } finally {
    searching.value = false
  }
}

function exitSearch() {
  searchMode.value = false
  searchResults.value = []
}

async function openEditor(row: SftpEntry) {
  try {
    const data = await sftpRead(Number(hostId.value), row.path)
    editor.open = true
    editor.path = data.path
    editor.name = data.name
    editor.content = data.content
  } catch (err) {
    Message.error(err instanceof Error ? err.message : '读取失败')
  }
}

async function saveEditor() {
  editor.saving = true
  try {
    await sftpWrite(Number(hostId.value), editor.path, editor.content)
    editor.open = false
  } finally {
    editor.saving = false
  }
}

watch(hostId, (id, prev) => {
  if (!workspaceReady.value) return

  if (prev) {
    pathByHost[prev] = path.value
  }

  if (!id) {
    entries.value = []
    breadcrumbs.value = [{ name: '/', path: '/' }]
    persistWorkspace()
    return
  }

  const host = currentHost.value
  isWindowsHost.value = isWindowsOs(host?.osName)
  if (id !== prev) {
    path.value = pathByHost[id] || defaultSftpPathForOs(host?.osName)
  }
  closeCtxMenu()
  exitSearch()
  void loadDir()
})

function persistWorkspace() {
  if (!workspaceReady.value) return
  if (hostId.value) {
    pathByHost[hostId.value] = path.value
  }
  saveSftpWorkspace({
    hostId: hostId.value ? Number(hostId.value) : null,
    path: path.value,
    pathByHost: { ...pathByHost },
  })
}

function restoreWorkspace() {
  const ws = loadSftpWorkspace()
  if (!ws) return false

  if (ws.pathByHost) {
    Object.assign(pathByHost, ws.pathByHost)
  }

  const hid = ws.hostId
  if (!hid || !hosts.value.some((h) => h.id === hid)) return false

  const id = String(hid)
  const host = hosts.value.find((h) => h.id === hid)
  isWindowsHost.value = isWindowsOs(host?.osName)
  path.value = ws.path || pathByHost[id] || defaultSftpPathForOs(host?.osName)
  pathByHost[id] = path.value
  hostId.value = id
  return true
}

function applyHostFromQuery(raw: unknown) {
  const q = Array.isArray(raw) ? raw[0] : raw
  if (q == null || q === '') return false
  const id = String(q)
  if (!hosts.value.some((h) => String(h.id) === id)) return false

  const host = hosts.value.find((h) => String(h.id) === id)
  if (hostId.value !== id) {
    isWindowsHost.value = isWindowsOs(host?.osName)
    path.value = pathByHost[id] || defaultSftpPathForOs(host?.osName)
    pathByHost[id] = path.value
    hostId.value = id
  }
  return true
}

function stripHostIdQuery() {
  if (!('hostId' in route.query)) return
  const nextQuery = { ...route.query }
  delete nextQuery.hostId
  void router.replace({ query: nextQuery })
}

function flushWorkspaceOnLeave() {
  workspaceReady.value = true
  persistWorkspace()
}

watch([hostId, path], () => persistWorkspace())

watch(
  () => route.query.hostId,
  (val) => {
    if (!workspaceReady.value || !val) return
    applyHostFromQuery(val)
    stripHostIdQuery()
  },
)

onMounted(async () => {
  document.addEventListener('click', closeCtxMenu)
  document.addEventListener('scroll', closeCtxMenu, true)
  await loadHosts()

  restoreWorkspace()

  const q = route.query.hostId
  if (q) {
    applyHostFromQuery(q)
    // 清掉 hostId，避免再次 F5 只按 query 打开而丢掉已保存路径
    stripHostIdQuery()
  }

  workspaceReady.value = true
  if (hostId.value) {
    void loadDir()
  }
  persistWorkspace()

  window.addEventListener('pagehide', flushWorkspaceOnLeave)
})

onUnmounted(() => {
  document.removeEventListener('click', closeCtxMenu)
  document.removeEventListener('scroll', closeCtxMenu, true)
  window.removeEventListener('pagehide', flushWorkspaceOnLeave)
  flushWorkspaceOnLeave()
})
</script>

<template>
  <div class="sftp-page" @dragover.prevent @drop="onDrop">
    <LayoutToolbar>
      <template #left>
        <MaxSelect v-model="hostId" :width="240" :options="hostOptions" />
        <MaxInput v-model="keyword" :placeholder="searchMode ? '搜索关键词' : '过滤 / 搜索'" />
        <MaxButton :disabled="!hostId || searching" @click="runSearch">
          {{ searching ? '搜索中…' : '搜索' }}
        </MaxButton>
        <MaxButton v-if="searchMode" @click="exitSearch">退出搜索</MaxButton>
      </template>
      <template #right>
        <MaxButton :disabled="!hostId" @click="loadDir">刷新</MaxButton>
        <MaxButton :disabled="!hostId" @click="handleCreateDir">新建目录</MaxButton>
        <MaxButton :disabled="!hostId || !selectedPaths.size" @click="handleZipDownload">
          打包下载
        </MaxButton>
        <MaxButton variant="primary" :disabled="!hostId" @click="triggerUpload">上传</MaxButton>
        <MaxButton @click="toggleTransferPanel()">
          传输队列{{ activeUploads ? ` (${activeUploads})` : '' }}
        </MaxButton>
        <MaxButton @click="router.push({ name: 'linuxHosts' })">主机管理</MaxButton>
      </template>
    </LayoutToolbar>

    <input
      ref="fileInputRef"
      class="sftp-hidden"
      type="file"
      multiple
      @change="onFileChange"
    />

    <nav class="sftp-crumbs" aria-label="路径">
      <template v-for="(c, idx) in breadcrumbs" :key="c.path">
        <span v-if="idx > 0" class="sftp-sep" aria-hidden="true">/</span>
        <button
          v-if="idx < breadcrumbs.length - 1"
          type="button"
          class="sftp-crumb"
          @click="goPath(c.path)"
        >
          {{ c.name }}
        </button>
        <span v-else class="sftp-crumb sftp-crumb--on">{{ c.name }}</span>
      </template>
    </nav>

    <p v-if="searchMode" class="sftp-hint">搜索结果 {{ searchResults.length }} 项 · Cmd/Ctrl 多选 · Shift 连选</p>

    <p v-if="!hostId" class="sftp-empty">请先选择主机</p>
    <p v-else-if="loading" class="sftp-empty">加载中…</p>
    <p v-else-if="!displayList.length" class="sftp-empty">
      {{ searchMode ? '无匹配结果' : '目录为空，可拖拽文件到此处上传' }}
    </p>
    <div v-else class="sftp-grid">
      <button
        v-for="row in displayList"
        :key="row.path"
        type="button"
        class="sftp-item"
        :class="{ 'sftp-item--on': selectedPaths.has(row.path) || selected?.path === row.path }"
        @click="toggleSelect(row, $event)"
        @dblclick="openEntry(row)"
        @contextmenu.prevent="openCtxMenu(row, $event)"
      >
        <MaxSvg :name="iconName(row)" :size="64" :alt="row.name" />
        <span class="sftp-item__name">{{ row.name }}</span>
        <span v-if="searchMode" class="sftp-item__path">{{ row.path }}</span>
        <span class="sftp-item__mode">{{ row.mode }}</span>
      </button>
    </div>

    <aside v-if="transferPanelOpen" class="sftp-queue">
      <header>
        <h3>传输队列</h3>
        <div>
          <MaxButton size="sm" @click="clearFinished">清理已完成</MaxButton>
          <MaxButton size="sm" @click="toggleTransferPanel(false)">关闭</MaxButton>
        </div>
      </header>
      <p v-if="!transferTasks.length" class="sftp-empty">暂无任务</p>
      <div v-for="t in transferTasks" :key="t.id" class="sftp-queue__item">
        <strong>{{ t.fileName }}</strong>
        <span>{{ t.status }} · {{ progressOf(t) }}% · {{ t.remoteDir }}</span>
        <div class="sftp-queue__bar"><i :style="{ width: `${progressOf(t)}%` }" /></div>
        <p v-if="t.error" class="sftp-queue__err">{{ t.error }}</p>
        <div class="sftp-queue__actions">
          <MaxButton
            v-if="t.status === 'running' || t.status === 'queued'"
            size="sm"
            @click="pauseTask(t.id)"
          >
            暂停
          </MaxButton>
          <MaxButton
            v-if="t.status === 'paused' || t.status === 'error'"
            size="sm"
            @click="resumeTask(t.id)"
          >
            重试
          </MaxButton>
          <MaxButton
            v-if="!['done', 'cancelled'].includes(t.status)"
            size="sm"
            @click="cancelTask(t.id)"
          >
            取消
          </MaxButton>
        </div>
      </div>
    </aside>

    <Teleport to="body">
      <div
        v-if="ctxMenu.open && ctxMenu.row"
        class="sftp-ctx"
        :style="{ left: `${ctxMenu.x}px`, top: `${ctxMenu.y}px` }"
        @click.stop
        @contextmenu.prevent
      >
        <button
          v-if="ctxMenu.row.isDir"
          type="button"
          class="sftp-ctx__item"
          @click="runCtxAction('open')"
        >
          打开
        </button>
        <button
          v-else-if="ctxMenu.row.editable"
          type="button"
          class="sftp-ctx__item"
          @click="runCtxAction('edit')"
        >
          编辑
        </button>
        <button type="button" class="sftp-ctx__item" @click="runCtxAction('download')">
          下载
        </button>
        <button type="button" class="sftp-ctx__item" @click="runCtxAction('zip')">
          打包下载所选
        </button>
        <button type="button" class="sftp-ctx__item" @click="runCtxAction('props')">
          属性 / 权限
        </button>
        <button type="button" class="sftp-ctx__item" @click="runCtxAction('rename')">
          重命名
        </button>
        <button
          type="button"
          class="sftp-ctx__item sftp-ctx__item--danger"
          @click="runCtxAction('delete')"
        >
          删除
        </button>
      </div>
    </Teleport>

    <div v-if="editor.open" class="sftp-editor" @click.self="editor.open = false">
      <div class="sftp-editor__panel">
        <header>
          <h3>{{ editor.name }}</h3>
          <div>
            <MaxButton :loading="editor.saving" variant="primary" @click="saveEditor">保存</MaxButton>
            <MaxButton @click="editor.open = false">关闭</MaxButton>
          </div>
        </header>
        <MaxForm>
          <textarea v-model="editor.content" class="sftp-editor__textarea" spellcheck="false" />
        </MaxForm>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sftp-page {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  gap: 10px;
}

.sftp-hidden {
  display: none;
}

.sftp-crumbs {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 32px;
}

.sftp-crumb {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 28px;
  margin: 0;
  padding: 0 12px;
  white-space: nowrap;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.72);
  font-size: 12px;
  cursor: pointer;
}

button.sftp-crumb:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.14);
}

.sftp-crumb--on {
  color: #fff;
  font-weight: 600;
  cursor: default;
  background: rgba(10, 132, 255, 0.28);
  border-color: rgba(10, 132, 255, 0.45);
}

.sftp-sep {
  color: rgba(255, 255, 255, 0.28);
  font-size: 12px;
}

.sftp-hint {
  margin: 0;
  text-align: center;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.45);
}

.sftp-empty {
  margin: 48px 0;
  text-align: center;
  color: rgba(255, 255, 255, 0.45);
}

.sftp-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 10px;
  overflow: auto;
  flex: 1;
  min-height: 0;
  align-content: start;
}

.sftp-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 8px;
  border-radius: 12px;
  border: 1px solid transparent;
  background: transparent;
  color: #fff;
  cursor: default;
}

.sftp-item:hover,
.sftp-item--on {
  background: rgba(10, 132, 255, 0.14);
  border-color: rgba(10, 132, 255, 0.35);
}

.sftp-item__name {
  width: 100%;
  text-align: center;
  font-size: 13px;
  word-break: break-word;
}

.sftp-item__path,
.sftp-item__mode {
  width: 100%;
  text-align: center;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.4);
  word-break: break-all;
}

.sftp-queue {
  position: absolute;
  right: 12px;
  bottom: 12px;
  width: min(380px, calc(100% - 24px));
  max-height: 42%;
  overflow: auto;
  z-index: 20;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(22, 22, 24, 0.96);
  padding: 12px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
}

.sftp-queue header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.sftp-queue header h3 {
  margin: 0;
  font-size: 14px;
}

.sftp-queue header div {
  display: flex;
  gap: 6px;
}

.sftp-queue__item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px;
  margin-bottom: 8px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
}

.sftp-queue__item strong {
  font-size: 13px;
}

.sftp-queue__item span {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
}

.sftp-queue__bar {
  height: 4px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.1);
  overflow: hidden;
}

.sftp-queue__bar i {
  display: block;
  height: 100%;
  background: #0a84ff;
}

.sftp-queue__err {
  margin: 0;
  font-size: 11px;
  color: #ffb4ae;
}

.sftp-queue__actions {
  display: flex;
  gap: 6px;
}

.sftp-ctx {
  position: fixed;
  z-index: 3000;
  min-width: 150px;
  padding: 6px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(28, 28, 30, 0.96);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35);
}

.sftp-ctx__item {
  display: block;
  width: 100%;
  margin: 0;
  padding: 8px 12px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: rgba(255, 255, 255, 0.9);
  text-align: left;
  font-size: 13px;
  cursor: pointer;
}

.sftp-ctx__item:hover {
  background: rgba(10, 132, 255, 0.28);
}

.sftp-ctx__item--danger {
  color: #ffb4ae;
}

.sftp-editor {
  position: fixed;
  inset: 0;
  z-index: 2100;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.55);
  padding: 24px;
}

.sftp-editor__panel {
  width: min(960px, 100%);
  height: min(80vh, 720px);
  display: flex;
  flex-direction: column;
  border-radius: 14px;
  background: #1c1c1e;
  border: 1px solid rgba(255, 255, 255, 0.14);
  overflow: hidden;
}

.sftp-editor__panel header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sftp-editor__panel h3 {
  margin: 0;
  color: #fff;
  font-size: 15px;
}

.sftp-editor__panel header div {
  display: flex;
  gap: 8px;
}

.sftp-editor__textarea {
  width: 100%;
  height: calc(80vh - 80px);
  max-height: 640px;
  border: none;
  resize: none;
  padding: 16px;
  background: #0d1117;
  color: #e6edf3;
  font: 13px/1.5 Menlo, Monaco, Consolas, monospace;
  outline: none;
}
</style>
