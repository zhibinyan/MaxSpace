<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import Message from '@/components/massage'
import {
  createFolder,
  deleteFiles,
  downloadFileById,
  fetchFiles,
  fetchTextPreview,
  fileRawUrl,
  moveFile,
  renameFile,
  uploadFile,
  type FileBreadcrumb,
  type FileEntry,
} from '@/api/file'
import MaxConfirm from '@/components/maxConfirm'
import MaxPopup from '@/components/maxPopup'
import { MaxButton } from '@/components/maxButton'
import { MaxInput } from '@/components/maxInput'
import { MaxSelect, type MaxSelectOption } from '@/components/maxSelect'
import { MaxSvg } from '@/components/maxSvg'
import { LayoutToolbar } from '@/layout'
import FileNameFormBody from './FileNameFormBody.vue'

const loading = ref(false)
const uploading = ref(false)
const uploadPercent = ref(0)
const parentId = ref<number | null>(null)
const files = ref<FileEntry[]>([])
const breadcrumbs = ref<FileBreadcrumb[]>([{ id: null, name: '根目录' }])
const selectedIds = ref<Array<string | number>>([])
const clipboard = ref<{ mode: 'cut' | 'copy'; ids: number[] } | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const folderInputRef = ref<HTMLInputElement | null>(null)

const filters = reactive({
  keyword: '',
  category: '',
})

const preview = reactive<{
  open: boolean
  item: FileEntry | null
  text: string
  mediaUrl: string
}>({
  open: false,
  item: null,
  text: '',
  mediaUrl: '',
})

const categoryOptions: MaxSelectOption[] = [
  { value: '', label: '全部类型' },
  { value: 'image', label: '图片' },
  { value: 'video', label: '视频' },
  { value: 'audio', label: '音频' },
  { value: 'document', label: '文档' },
  { value: 'office', label: 'Office' },
  { value: 'pdf', label: 'PDF' },
  { value: 'markdown', label: 'Markdown' },
  { value: 'code', label: '代码' },
  { value: 'archive', label: '压缩包' },
  { value: 'install', label: '安装包' },
  { value: 'other', label: '其它' },
]

const isSearching = computed(
  () => !!(filters.keyword.trim() || filters.category),
)

function iconNameFor(row: FileEntry) {
  if (row.isFolder) return 'files/folder'
  switch (row.category) {
    case 'image':
      return 'files/image'
    case 'video':
      return 'files/video'
    case 'audio':
      return 'files/audio'
    case 'pdf':
      return 'files/pdf'
    case 'code':
      return 'files/code'
    case 'markdown':
      return 'files/markdown'
    case 'office':
      return 'files/office'
    case 'archive':
      return 'files/archive'
    case 'install':
      return 'files/install'
    case 'document':
      return 'files/document'
    default:
      return 'files/file'
  }
}

function isSelected(id: number) {
  return selectedIds.value.includes(id)
}

function toggleSelect(row: FileEntry, event: MouseEvent) {
  if (event.metaKey || event.ctrlKey) {
    if (isSelected(row.id)) {
      selectedIds.value = selectedIds.value.filter((id) => id !== row.id)
    } else {
      selectedIds.value = [...selectedIds.value, row.id]
    }
    return
  }
  selectedIds.value = [row.id]
}

async function openItem(row: FileEntry) {
  if (row.isFolder) {
    openFolder(row)
    return
  }
  await openPreview(row)
}

async function loadFiles() {
  loading.value = true
  try {
    const result = await fetchFiles({
      parentId: isSearching.value ? undefined : parentId.value,
      keyword: filters.keyword.trim() || undefined,
      category: filters.category || undefined,
    })
    files.value = result.list
    if (!isSearching.value) {
      breadcrumbs.value = result.breadcrumbs
    }
  } finally {
    loading.value = false
  }
}

function goCrumb(id: number | null) {
  filters.keyword = ''
  filters.category = ''
  parentId.value = id
  selectedIds.value = []
  void loadFiles()
}

function goUp() {
  if (breadcrumbs.value.length < 2) return
  const prev = breadcrumbs.value[breadcrumbs.value.length - 2]
  goCrumb(prev.id)
}

function openFolder(row: FileEntry) {
  if (!row.isFolder) return
  filters.keyword = ''
  filters.category = ''
  parentId.value = row.id
  selectedIds.value = []
  void loadFiles()
}

async function openPreview(row: FileEntry) {
  if (row.isFolder) {
    openFolder(row)
    return
  }

  if (row.previewKind === 'install' || row.previewKind === 'office' || row.previewKind === 'download') {
    Message.info('当前文件类型不支持在线预览，请下载后查看。')
    return
  }

  preview.item = row
  preview.text = ''
  preview.mediaUrl = ''
  preview.open = true

  if (row.previewKind === 'text') {
    const data = await fetchTextPreview(row.id)
    preview.text = data.content
  } else {
    preview.mediaUrl = fileRawUrl(row.id)
  }
}

function closePreview() {
  preview.open = false
  preview.item = null
  preview.text = ''
  preview.mediaUrl = ''
}

const nameForm = reactive({
  name: '',
  renameId: 0,
  originalName: '',
})

async function handleCreateFolder() {
  nameForm.name = ''
  nameForm.renameId = 0
  nameForm.originalName = ''
  void MaxPopup.open({
    title: '新建文件夹',
    size: 'sm',
    direction: 'top',
    content: FileNameFormBody,
    contentProps: {
      form: nameForm,
      label: '文件夹名称',
      placeholder: '请输入文件夹名称',
    },
    onConfirm: async () => {
      const name = nameForm.name.trim()
      if (!name) {
        Message.warning('请输入文件夹名称')
        return false
      }
      try {
        await createFolder(parentId.value, name)
        await loadFiles()
        return true
      } catch (err) {
        Message.error(err instanceof Error ? err.message : '创建失败')
        return false
      }
    },
  })
}

async function handleRename(row: FileEntry) {
  nameForm.name = row.name
  nameForm.renameId = row.id
  nameForm.originalName = row.name
  void MaxPopup.open({
    title: '重命名',
    size: 'sm',
    direction: 'top',
    content: FileNameFormBody,
    contentProps: {
      form: nameForm,
      label: '新名称',
      placeholder: '请输入新名称',
    },
    onConfirm: async () => {
      const name = nameForm.name.trim()
      if (!name) {
        Message.warning('请输入名称')
        return false
      }
      if (name === nameForm.originalName) {
        return true
      }
      try {
        await renameFile(nameForm.renameId, name)
        await loadFiles()
        return true
      } catch (err) {
        Message.error(err instanceof Error ? err.message : '重命名失败')
        return false
      }
    },
  })
}

function triggerUpload() {
  fileInputRef.value?.click()
}

function triggerFolderUpload() {
  folderInputRef.value?.click()
}

async function uploadSelectedFiles(list: FileList | File[]) {
  const filesToUpload = Array.from(list)
  if (!filesToUpload.length) return

  uploading.value = true
  uploadPercent.value = 0
  try {
    const total = filesToUpload.length
    for (let i = 0; i < total; i++) {
      const file = filesToUpload[i]
      const relativePath =
        (file as File & { webkitRelativePath?: string }).webkitRelativePath || file.name
      await uploadFile(
        parentId.value,
        file,
        (p) => {
          // 整体进度：已完成文件 + 当前文件进度
          uploadPercent.value = Math.round(((i + p / 100) / total) * 100)
        },
        relativePath,
      )
    }
    uploadPercent.value = 100
    Message.success(`已上传 ${total} 个文件`)
    await loadFiles()
  } catch (err) {
    Message.error(err instanceof Error ? err.message : '上传失败')
  } finally {
    uploading.value = false
    uploadPercent.value = 0
  }
}

async function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return
  await uploadSelectedFiles(input.files)
  input.value = ''
}

async function onFolderChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return
  await uploadSelectedFiles(input.files)
  input.value = ''
}

function selectedEntry(): FileEntry | null {
  if (selectedIds.value.length !== 1) return null
  const id = Number(selectedIds.value[0])
  return files.value.find((f) => f.id === id) ?? null
}

async function handleDownload(row: FileEntry) {
  if (row.isFolder) {
    Message.warning('文件夹压缩下载暂未开放，请进入目录逐个下载')
    return
  }
  await downloadFileById(row.id, row.name)
}

function handleRenameSelected() {
  const row = selectedEntry()
  if (!row) {
    Message.warning('请先选择一个文件或文件夹')
    return
  }
  void handleRename(row)
}

async function handleDownloadSelected() {
  const row = selectedEntry()
  if (!row) {
    Message.warning('请先选择一个文件')
    return
  }
  await handleDownload(row)
}

async function handleDelete(rows?: FileEntry[]) {
  const targets =
    rows ??
    files.value.filter((f) => selectedIds.value.includes(f.id))
  if (!targets.length) {
    Message.warning('请先选择文件')
    return
  }
  const ok = await MaxConfirm.delete({
    title: '删除确认',
    message: `确定删除选中的 ${targets.length} 项吗？此操作不可恢复。`,
  })
  if (!ok) return
  await deleteFiles(targets.map((t) => t.id))
  selectedIds.value = []
  await loadFiles()
}

function handleCut() {
  const ids = selectedIds.value.map(Number)
  if (!ids.length) {
    Message.warning('请先选择文件')
    return
  }
  clipboard.value = { mode: 'cut', ids }
  Message.success('已剪切，进入目标目录后点击粘贴')
}

async function handlePaste() {
  if (!clipboard.value?.ids.length) {
    Message.warning('剪贴板为空')
    return
  }
  if (clipboard.value.mode === 'cut') {
    for (const id of clipboard.value.ids) {
      await moveFile(id, parentId.value)
    }
    clipboard.value = null
    Message.success('已粘贴')
    await loadFiles()
  }
}

watch(
  () => [filters.keyword, filters.category],
  () => {
    void loadFiles()
  },
)

onMounted(loadFiles)
</script>

<template>
  <div class="fm-page">
    <LayoutToolbar>
      <template #left>
        <MaxInput v-model="filters.keyword" placeholder="搜索文件名" />
        <MaxSelect v-model="filters.category" :options="categoryOptions" />
      </template>
      <template #right>
        <MaxButton @click="goUp">上一级</MaxButton>
        <MaxButton @click="handleCreateFolder">新建文件夹</MaxButton>
        <MaxButton variant="primary" :disabled="uploading" @click="triggerUpload">
          {{ uploading ? `上传中 ${uploadPercent}%` : '上传文件' }}
        </MaxButton>
        <MaxButton :disabled="uploading" @click="triggerFolderUpload">上传文件夹</MaxButton>
        <MaxButton @click="handleCut">剪切</MaxButton>
        <MaxButton @click="handlePaste">粘贴</MaxButton>
        <MaxButton @click="handleRenameSelected">重命名</MaxButton>
        <MaxButton @click="handleDownloadSelected">下载</MaxButton>
        <MaxButton @click="handleDelete()">删除</MaxButton>
      </template>
    </LayoutToolbar>

    <input
      ref="fileInputRef"
      class="fm-file-input"
      type="file"
      multiple
      @change="onFileChange"
    />
    <input
      ref="folderInputRef"
      class="fm-file-input"
      type="file"
      multiple
      webkitdirectory
      directory
      @change="onFolderChange"
    />

    <nav class="fm-crumbs" aria-label="面包屑">
      <template v-if="isSearching">
        <span class="fm-crumb fm-crumb--current">搜索结果</span>
      </template>
      <template v-else>
        <template v-for="(crumb, idx) in breadcrumbs" :key="`${crumb.id}-${idx}`">
          <span v-if="idx > 0" class="fm-crumb-sep" aria-hidden="true">/</span>
          <button
            v-if="idx < breadcrumbs.length - 1"
            type="button"
            class="fm-crumb"
            @click="goCrumb(crumb.id)"
          >
            {{ crumb.name }}
          </button>
          <span v-else class="fm-crumb fm-crumb--current">{{ crumb.name }}</span>
        </template>
      </template>
    </nav>

    <div class="fm-grid-wrap">
      <div v-if="loading" class="fm-empty">加载中…</div>
      <div v-else-if="!files.length" class="fm-empty">暂无文件</div>
      <div v-else class="fm-grid">
        <button
          v-for="row in files"
          :key="row.id"
          type="button"
          class="fm-item"
          :class="{ 'fm-item--selected': isSelected(row.id) }"
          :title="row.name"
          @click="toggleSelect(row, $event)"
          @dblclick="openItem(row)"
          @contextmenu.prevent="handleRename(row)"
        >
          <MaxSvg class="fm-item__icon" :name="iconNameFor(row)" :size="72" :alt="row.name" />
          <span class="fm-item__name">{{ row.name }}</span>
        </button>
      </div>
    </div>

    <div v-if="preview.open" class="fm-preview" @click.self="closePreview">
      <div class="fm-preview__panel">
        <header class="fm-preview__head">
          <h3>{{ preview.item?.name }}</h3>
          <button type="button" class="fm-preview__close" @click="closePreview">关闭</button>
        </header>
        <div class="fm-preview__body">
          <img
            v-if="preview.item?.previewKind === 'image' && preview.mediaUrl"
            :src="preview.mediaUrl"
            class="fm-preview__media"
            alt=""
          />
          <video
            v-else-if="preview.item?.previewKind === 'video' && preview.mediaUrl"
            :src="preview.mediaUrl"
            class="fm-preview__media"
            controls
          />
          <audio
            v-else-if="preview.item?.previewKind === 'audio' && preview.mediaUrl"
            :src="preview.mediaUrl"
            controls
          />
          <iframe
            v-else-if="preview.item?.previewKind === 'pdf' && preview.mediaUrl"
            :src="preview.mediaUrl"
            class="fm-preview__frame"
            title="pdf"
          />
          <pre v-else-if="preview.item?.previewKind === 'text'" class="fm-preview__code">{{ preview.text }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fm-page {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  height: 100%;
  gap: 10px;
}

.fm-file-input {
  display: none;
}

.fm-crumbs {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 32px;
  padding: 0;
  background: transparent;
}

.fm-crumb {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 28px;
  white-space: nowrap;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.72);
  font-size: 12px;
  line-height: 1;
  cursor: pointer;
  padding: 0 12px;
  transition:
    color 0.15s ease,
    background 0.15s ease,
    border-color 0.15s ease;
}

button.fm-crumb:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.14);
  border-color: rgba(255, 255, 255, 0.22);
}

.fm-crumb--current {
  color: #fff;
  font-weight: 600;
  cursor: default;
  background: rgba(10, 132, 255, 0.28);
  border-color: rgba(10, 132, 255, 0.45);
}

.fm-crumb-sep {
  flex-shrink: 0;
  color: rgba(255, 255, 255, 0.28);
  font-size: 12px;
  user-select: none;
  pointer-events: none;
}

.fm-grid-wrap {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 8px 4px 16px;
}

.fm-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(108px, 1fr));
  gap: 12px 8px;
  align-content: start;
}

.fm-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  width: 100%;
  margin: 0;
  padding: 12px 8px 10px;
  border: 1px solid transparent;
  border-radius: 12px;
  background: transparent;
  color: rgba(255, 255, 255, 0.9);
  cursor: default;
  user-select: none;
  transition:
    background 0.15s ease,
    border-color 0.15s ease;
}

.fm-item:hover {
  background: rgba(255, 255, 255, 0.06);
}

.fm-item--selected {
  background: rgba(10, 132, 255, 0.18);
  border-color: rgba(10, 132, 255, 0.35);
}

.fm-item__icon {
  pointer-events: none;
}

.fm-item__name {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  width: 100%;
  text-align: center;
  font-size: 13px;
  line-height: 1.35;
  word-break: break-word;
}

.fm-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 160px;
  color: rgba(255, 255, 255, 0.45);
  font-size: 14px;
}

.fm-preview {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.55);
  padding: 24px;
}

.fm-preview__panel {
  width: min(960px, 100%);
  max-height: 88vh;
  display: flex;
  flex-direction: column;
  border-radius: 14px;
  background: rgba(28, 28, 32, 0.96);
  border: 1px solid rgba(255, 255, 255, 0.16);
  overflow: hidden;
}

.fm-preview__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.fm-preview__head h3 {
  margin: 0;
  font-size: 15px;
  color: #fff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.fm-preview__close {
  border: none;
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  border-radius: 8px;
  padding: 6px 12px;
  cursor: pointer;
}

.fm-preview__body {
  flex: 1;
  min-height: 240px;
  max-height: calc(88vh - 56px);
  overflow: auto;
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.fm-preview__media {
  max-width: 100%;
  max-height: calc(88vh - 100px);
}

.fm-preview__frame {
  width: 100%;
  height: calc(88vh - 100px);
  border: none;
  background: #fff;
}

.fm-preview__code {
  width: 100%;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  color: #e8f0ff;
  font-size: 13px;
  line-height: 1.55;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}
</style>
