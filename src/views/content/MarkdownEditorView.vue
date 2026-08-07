<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  createMarkdown,
  fetchMarkdown,
  updateMarkdown,
  type MarkdownItem,
} from '@/api/markdown'
import { MaxButton } from '@/components/maxButton'
import { renderMarkdown } from '@/utils/markdown'

defineOptions({ name: 'markdownEditorView' })

const route = useRoute()
const router = useRouter()

function parseMarkdownId(raw: unknown): number | null {
  if (raw === undefined || raw === null || raw === '') return null
  const id = Number(raw)
  return Number.isFinite(id) && id > 0 ? id : null
}

const markdownId = computed(() => parseMarkdownId(route.params.id))
const isCreate = computed(() => markdownId.value === null)
const isViewMode = computed(() => route.query.mode === 'view' && !isCreate.value)
const isReadonly = computed(() => isViewMode.value)

const title = ref('未命名备忘录')
const content = ref('')
const loading = ref(false)
const saving = ref(false)

const renderedHtml = computed(() => renderMarkdown(content.value))
const pageTitle = computed(() => {
  if (isCreate.value) return '新建备忘录'
  if (isViewMode.value) return '查看备忘录'
  return '编辑备忘录'
})

async function loadMarkdown() {
  if (isCreate.value) {
    title.value = '未命名备忘录'
    content.value = ''
    return
  }

  loading.value = true
  try {
    const item = await fetchMarkdown(markdownId.value!)
    title.value = item.title
    content.value = item.content
  } finally {
    loading.value = false
  }
}

function goBack() {
  if (window.history.length > 1) {
    router.back()
    return
  }
  router.push({ name: 'articleList' }).catch(() => {
    router.push({ path: '/dashboard' })
  })
}

function switchToEdit() {
  if (isCreate.value) return
  router.replace({
    name: 'markdownEditor',
    params: { id: String(markdownId.value) },
  })
}

async function saveMarkdown() {
  if (!title.value.trim()) {
    window.alert('请填写标题')
    return
  }

  saving.value = true
  try {
    const payload: Partial<MarkdownItem> = {
      title: title.value.trim(),
      content: content.value,
    }

    if (isCreate.value) {
      const created = await createMarkdown(payload)
      router.replace({ name: 'markdownEditor', params: { id: String(created.id) } })
    } else {
      await updateMarkdown(markdownId.value!, payload)
    }
  } finally {
    saving.value = false
  }
}

watch(
  () => [route.params.id, route.query.mode] as const,
  () => {
    void loadMarkdown()
  },
  { immediate: true },
)
</script>

<template>
  <div class="markdown-editor">
    <header class="markdown-editor__toolbar">
      <div class="markdown-editor__toolbar-left">
        <MaxButton variant="ghost" @click="goBack">返回</MaxButton>
        <span class="markdown-editor__mode">{{ pageTitle }}</span>
        <input
          v-if="!isReadonly"
          v-model="title"
          class="markdown-editor__title-input"
          type="text"
          placeholder="标题"
          spellcheck="false"
        />
        <span v-else class="markdown-editor__title-readonly">{{ title }}</span>
      </div>
      <div class="markdown-editor__toolbar-right">
        <MaxButton v-if="isViewMode" variant="primary" @click="switchToEdit">编辑</MaxButton>
        <MaxButton
          v-else
          variant="primary"
          :loading="saving"
          :disabled="loading"
          @click="saveMarkdown"
        >
          保存
        </MaxButton>
      </div>
    </header>

    <div v-if="loading" class="markdown-editor__loading">加载中…</div>
    <template v-else>
      <textarea
        v-if="!isReadonly"
        v-model="content"
        class="markdown-editor__textarea"
        placeholder="在此输入 Markdown 内容…"
        spellcheck="false"
      />
      <article
        v-else
        class="markdown-editor__preview markdown-body"
        v-html="renderedHtml"
      />
    </template>
  </div>
</template>

<style scoped>
.markdown-editor {
  display: flex;
  flex-direction: column;
  flex: 1;
  width: 100%;
  min-height: 0;
  height: 100%;
  box-sizing: border-box;
}

.markdown-editor__toolbar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.18);
}

.markdown-editor__toolbar-left,
.markdown-editor__toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.markdown-editor__mode {
  font-size: 13px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.55);
  white-space: nowrap;
}

.markdown-editor__title-input,
.markdown-editor__title-readonly {
  height: 34px;
  padding: 0 12px;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
}

.markdown-editor__title-input {
  width: min(280px, 36vw);
  border: 1px solid rgba(255, 255, 255, 0.22);
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
  font-weight: 600;
}

.markdown-editor__title-input:focus {
  border-color: rgba(255, 255, 255, 0.42);
}

.markdown-editor__title-readonly {
  display: inline-flex;
  align-items: center;
  font-weight: 700;
  color: #ffffff;
}

.markdown-editor__loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.62);
  font-size: 14px;
}

.markdown-editor__textarea {
  flex: 1;
  min-height: 0;
  width: 100%;
  padding: 16px 20px;
  border: none;
  outline: none;
  resize: none;
  background: rgba(255, 255, 255, 0.04);
  color: #ffffff;
  font-size: 14px;
  line-height: 1.7;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  box-sizing: border-box;
}

.markdown-editor__preview {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 20px 24px;
  color: rgba(255, 255, 255, 0.92);
  font-size: 15px;
  line-height: 1.75;
}

.markdown-editor__preview :deep(h1),
.markdown-editor__preview :deep(h2),
.markdown-editor__preview :deep(h3),
.markdown-editor__preview :deep(h4),
.markdown-editor__preview :deep(h5),
.markdown-editor__preview :deep(h6) {
  margin: 1.2em 0 0.6em;
  font-weight: 700;
  color: #ffffff;
}

.markdown-editor__preview :deep(h1) { font-size: 1.75em; }
.markdown-editor__preview :deep(h2) { font-size: 1.5em; }
.markdown-editor__preview :deep(h3) { font-size: 1.25em; }

.markdown-editor__preview :deep(p) {
  margin: 0.75em 0;
}

.markdown-editor__preview :deep(a) {
  color: rgba(120, 190, 255, 0.95);
}

.markdown-editor__preview :deep(ul) {
  margin: 0.75em 0;
  padding-left: 1.4em;
}

.markdown-editor__preview :deep(li) {
  margin: 0.35em 0;
}

.markdown-editor__preview :deep(.md-inline-code),
.markdown-editor__preview :deep(code) {
  padding: 0.15em 0.4em;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.1);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.92em;
}

.markdown-editor__preview :deep(.md-pre) {
  margin: 1em 0;
  padding: 14px 16px;
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.28);
  overflow: auto;
}

.markdown-editor__preview :deep(.md-pre code) {
  padding: 0;
  background: transparent;
}

.markdown-editor__preview :deep(.md-table) {
  width: 100%;
  margin: 1em 0;
  border-collapse: collapse;
  font-size: 14px;
}

.markdown-editor__preview :deep(.md-table th),
.markdown-editor__preview :deep(.md-table td) {
  padding: 8px 12px;
  border: 1px solid rgba(255, 255, 255, 0.22);
}

.markdown-editor__preview :deep(.md-table th) {
  background: rgba(255, 255, 255, 0.1);
  font-weight: 700;
  color: #ffffff;
}

.markdown-editor__preview :deep(.md-table td) {
  background: rgba(255, 255, 255, 0.04);
}
</style>
