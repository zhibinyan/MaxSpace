<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { deleteMarkdown, fetchMarkdowns, type MarkdownItem } from '@/api/markdown'
import { MaxButton } from '@/components/maxButton'
import { MaxCard, MaxCardRow } from '@/components/maxCard'
import { markdownExcerpt } from '@/utils/markdown'

defineOptions({ name: 'ArticleListView' })

const router = useRouter()
const loading = ref(false)
const error = ref('')
const items = ref<MarkdownItem[]>([])

async function loadItems() {
  loading.value = true
  error.value = ''
  try {
    items.value = await fetchMarkdowns()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
    items.value = []
  } finally {
    loading.value = false
  }
}

function openCreate() {
  router.push({ name: 'markdownEditor' })
}

function openEdit(id: number) {
  router.push({ name: 'markdownEditor', params: { id: String(id) } })
}

function openView(event: MouseEvent, id: number) {
  event.stopPropagation()
  router.push({
    name: 'markdownEditor',
    params: { id: String(id) },
    query: { mode: 'view' },
  })
}

async function handleDelete(event: MouseEvent, item: MarkdownItem) {
  event.stopPropagation()
  if (!window.confirm(`确定删除「${item.title}」？`)) return
  await deleteMarkdown(item.id)
  await loadItems()
}

onMounted(loadItems)
</script>

<template>
  <div class="article-list">
    <div class="article-list__toolbar">
      <h1 class="article-list__title">Markdown 备忘录</h1>
      <MaxButton variant="primary" @click="openCreate">新建备忘录</MaxButton>
    </div>

    <p v-if="loading" class="article-list__hint">加载中…</p>
    <p v-else-if="error" class="article-list__hint article-list__hint--error">{{ error }}</p>
    <p v-else-if="!items.length" class="article-list__hint">暂无备忘录，点击「新建备忘录」开始</p>

    <MaxCardRow v-else :gutter="16">
      <MaxCard
        v-for="item in items"
        :key="item.id"
        :span="6"
        class="memo-card"
        role="button"
        tabindex="0"
        @click="openEdit(item.id)"
        @keydown.enter="openEdit(item.id)"
      >
        <template #header>
          <span class="memo-card__header-title">{{ item.title }}</span>
        </template>
        <div class="memo-card__body">
          <p class="memo-card__excerpt">
            {{ markdownExcerpt(item.content) || '（空内容）' }}
          </p>
          <p class="memo-card__meta">更新于 {{ item.updatedAt || item.createdAt || '—' }}</p>
          <div class="memo-card__actions">
            <MaxButton variant="ghost" size="sm" @click="openView($event, item.id)">
              查看
            </MaxButton>
            <MaxButton
              variant="link-danger"
              size="sm"
              @click="handleDelete($event, item)"
            >
              删除
            </MaxButton>
          </div>
        </div>
      </MaxCard>
    </MaxCardRow>
  </div>
</template>

<style scoped>
.article-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.article-list__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.article-list__title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #ffffff;
  text-shadow:
    0 0 1px rgba(0, 0, 0, 0.5),
    0 1px 4px rgba(0, 0, 0, 0.32);
}

.article-list__hint {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.62);
}

.article-list__hint--error {
  color: rgba(255, 160, 160, 0.92);
}

.memo-card {
  min-height: 160px;
  cursor: pointer;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.memo-card:hover {
  border-color: rgba(255, 255, 255, 0.36);
}

.memo-card__header-title {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.memo-card__body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 108px;
  /* 覆盖 MaxCard 默认 text-shadow，避免正文发糊 */
  text-shadow: none;
  -webkit-font-smoothing: auto;
  -moz-osx-font-smoothing: auto;
}

.memo-card__excerpt {
  margin: 0;
  font-size: 13px;
  font-weight: 500;
  line-height: 1.5;
  color: rgba(255, 255, 255, 0.88);
  text-shadow: none;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.memo-card__meta {
  margin: auto 0 0;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.4;
  color: rgba(255, 255, 255, 0.68);
  text-shadow: none;
}

.memo-card__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}
</style>
