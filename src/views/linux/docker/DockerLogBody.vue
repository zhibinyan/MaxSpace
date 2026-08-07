<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { fetchDockerContainerLogs } from '@/api/linux'
import Message from '@/components/massage'
import { MaxButton } from '@/components/maxButton'
import { MaxInput } from '@/components/maxInput'

const props = defineProps<{
  /** Live mode: fetch container logs */
  hostId?: number
  container?: string
  /** Static mode: show pre-fetched text (compose config/logs) */
  staticContent?: string
  title?: string
}>()

const isStatic = computed(() => props.staticContent != null)

const logs = ref('')
const loading = ref(false)
const keyword = ref('')
const since = ref('')
const tail = ref('300')
const timestamps = ref(true)
const autoRefresh = ref(false)
let timer: number | null = null

const filtered = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  if (!q) return logs.value
  return logs.value
    .split('\n')
    .filter((line) => line.toLowerCase().includes(q))
    .join('\n')
})

async function load() {
  if (isStatic.value) {
    logs.value = props.staticContent || ''
    return
  }
  if (!props.hostId || !props.container) {
    Message.warning('缺少主机或容器信息')
    return
  }
  loading.value = true
  try {
    const data = await fetchDockerContainerLogs(
      props.hostId,
      props.container,
      Math.min(Math.max(Number(tail.value) || 300, 1), 5000),
      since.value.trim(),
      timestamps.value,
    )
    logs.value = data.logs
  } catch (err) {
    Message.error(err instanceof Error ? err.message : '读取日志失败')
  } finally {
    loading.value = false
  }
}

function download() {
  const blob = new Blob([filtered.value || logs.value || ''], { type: 'text/plain;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `${props.container || props.title || 'logs'}.txt`
  a.click()
  URL.revokeObjectURL(a.href)
}

function clearView() {
  logs.value = ''
}

watch(autoRefresh, (on) => {
  if (timer) {
    window.clearInterval(timer)
    timer = null
  }
  if (on && !isStatic.value) {
    timer = window.setInterval(() => {
      void load()
    }, 5000)
  }
})

watch(
  () => props.staticContent,
  (v) => {
    if (v != null) logs.value = v
  },
)

onMounted(() => {
  void load()
})

onUnmounted(() => {
  if (timer) window.clearInterval(timer)
})
</script>

<template>
  <div class="docker-log">
    <p v-if="title" class="docker-log__title">{{ title }}</p>
    <div class="docker-log__tools">
      <MaxInput v-model="keyword" placeholder="搜索日志" />
      <template v-if="!isStatic">
        <MaxInput v-model="since" placeholder="since，如 1h / 2024-01-01" />
        <MaxInput v-model="tail" placeholder="行数" />
        <label class="chk">
          <input v-model="timestamps" type="checkbox" />
          时间戳
        </label>
        <label class="chk">
          <input v-model="autoRefresh" type="checkbox" />
          自动刷新(5s)
        </label>
        <MaxButton size="sm" :disabled="loading" @click="load">{{ loading ? '…' : '刷新' }}</MaxButton>
      </template>
      <MaxButton size="sm" @click="download">下载</MaxButton>
      <MaxButton size="sm" @click="clearView">清空视图</MaxButton>
    </div>
    <pre class="docker-log__body">{{ filtered || (loading ? '加载中…' : '（空）') }}</pre>
  </div>
</template>

<style scoped>
.docker-log {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.docker-log__title {
  margin: 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}
.docker-log__tools {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.chk {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.65);
}
.docker-log__body {
  margin: 0;
  max-height: min(52vh, 420px);
  overflow: auto;
  padding: 12px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.35);
  color: #c8e0ff;
  font-size: 12px;
  line-height: 1.45;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: Menlo, Monaco, 'Courier New', monospace;
}
</style>
