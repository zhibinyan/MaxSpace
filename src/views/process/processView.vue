<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { deleteProcess, fetchProcesses, type ProcessItem } from '@/api/process'
import { MaxButton } from '@/components/maxButton'
import { MaxCard, MaxCardRow } from '@/components/maxCard'

defineOptions({ name: 'ProcessView' })

const router = useRouter()
const loading = ref(false)
const error = ref('')
const processes = ref<ProcessItem[]>([])

async function loadProcesses() {
  loading.value = true
  error.value = ''
  try {
    processes.value = await fetchProcesses()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
    processes.value = []
  } finally {
    loading.value = false
  }
}

function openCreate() {
  router.push({ name: 'processEditor' })
}

function openEdit(id: number) {
  router.push({ name: 'processEditor', params: { id: String(id) } })
}

async function handleDelete(event: MouseEvent, item: ProcessItem) {
  event.stopPropagation()
  if (!window.confirm(`确定删除「${item.title}」？`)) return
  await deleteProcess(item.id)
  await loadProcesses()
}

onMounted(loadProcesses)
</script>

<template>
  <div class="browser-page">
    <div class="browser-page__toolbar">
      <h1 class="browser-page__title">流程列表</h1>
      <MaxButton variant="primary" @click="openCreate">新建流程</MaxButton>
    </div>

    <p v-if="loading" class="browser-page__hint">加载中…</p>
    <p v-else-if="error" class="browser-page__hint browser-page__hint--error">{{ error }}</p>
    <p v-else-if="!processes.length" class="browser-page__hint">暂无流程，点击「新建流程」开始</p>

    <MaxCardRow v-else :gutter="16">
      <MaxCard
        v-for="item in processes"
        :key="item.id"
        :span="6"
        class="process-card"
        role="button"
        tabindex="0"
        @click="openEdit(item.id)"
        @keydown.enter="openEdit(item.id)"
      >
        <div class="process-card__body">
          <h2 class="process-card__title">{{ item.title }}</h2>
          <p v-if="item.description" class="process-card__desc">{{ item.description }}</p>
          <p class="process-card__meta">更新于 {{ item.updatedAt || item.createdAt || '—' }}</p>
          <MaxButton
            class="process-card__delete"
            variant="link-danger"
            size="sm"
            @click="handleDelete($event, item)"
          >
            删除
          </MaxButton>
        </div>
      </MaxCard>
    </MaxCardRow>
  </div>
</template>

<style scoped>
.browser-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.browser-page__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.browser-page__title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #ffffff;
  text-shadow:
    0 0 1px rgba(0, 0, 0, 0.5),
    0 1px 4px rgba(0, 0, 0, 0.32);
}

.browser-page__hint {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.62);
  text-shadow:
    0 0 1px rgba(0, 0, 0, 0.45),
    0 1px 3px rgba(0, 0, 0, 0.28);
}

.browser-page__hint--error {
  color: rgba(255, 160, 160, 0.92);
}

.process-card {
  min-height: 140px;
  cursor: pointer;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.process-card:hover {
  border-color: rgba(255, 255, 255, 0.36);
}

.process-card__body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 108px;
  text-shadow: none;
  -webkit-font-smoothing: auto;
  -moz-osx-font-smoothing: auto;
}

.process-card__title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #ffffff;
  text-shadow: none;
}

.process-card__desc {
  margin: 0;
  font-size: 13px;
  font-weight: 500;
  line-height: 1.5;
  color: rgba(255, 255, 255, 0.88);
  text-shadow: none;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.process-card__meta {
  margin: auto 0 0;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.4;
  color: rgba(255, 255, 255, 0.68);
  text-shadow: none;
}

.process-card__delete {
  align-self: flex-start;
  margin-top: 4px;
}
</style>
