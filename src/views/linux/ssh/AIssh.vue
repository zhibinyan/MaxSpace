<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { fetchLinuxAiHistory, type LinuxAiChatItem } from '@/api/linux'
import Message from '@/components/massage'
import { MaxButton } from '@/components/maxButton'
import MaxPopup from '@/components/maxPopup'
import AiStreamBody from './AiStreamBody.vue'

const emit = defineEmits<{
  /** 将命令发送到当前 SSH 窗格 */
  run: [cmd: string]
}>()

const prompt = ref('')
/** 流式原文（边收边显） */
const streamText = ref('')
/** 归一化后的最终命令 */
const answer = ref('')
const loading = ref(false)
const history = ref<LinuxAiChatItem[]>([])
const historyLoading = ref(false)
let abort: AbortController | null = null

/** 弹窗内实时镜像侧栏流式内容 */
const streamView = reactive({
  streamText: '',
  loading: false,
  answer: '',
})

watch(
  [streamText, loading, answer],
  () => {
    streamView.streamText = streamText.value
    streamView.loading = loading.value
    streamView.answer = answer.value
  },
  { immediate: true },
)

function openStreamPopup() {
  void MaxPopup.open({
    title: loading.value ? '流式输出' : '模型原文',
    size: 'md',
    content: AiStreamBody,
    contentProps: {
      view: streamView,
      onRun: () => {
        runToSsh()
        MaxPopup.close(true)
      },
    },
    confirmText: '关闭',
    showCancel: false,
  })
}

function normalizeCmd(raw: string) {
  let text = raw.trim()
  text = text.replace(/^```(?:bash|sh|shell)?\s*/i, '').replace(/\s*```$/i, '')
  text = text.replace(/^命令[：:]\s*/i, '')
  const first = text.split('\n').map((l) => l.trim()).find(Boolean) || ''
  return first
}

async function loadHistory() {
  historyLoading.value = true
  try {
    history.value = await fetchLinuxAiHistory(30)
  } catch {
    /* 列表失败不打断主流程 */
  } finally {
    historyLoading.value = false
  }
}

/** 回车：只查询，不运行 */
async function ask() {
  const q = prompt.value.trim()
  if (!q) {
    Message.warning('请输入你想做的事，例如：查看磁盘占用')
    return
  }
  abort?.abort()
  abort = new AbortController()
  loading.value = true
  streamText.value = ''
  answer.value = ''
  openStreamPopup()

  const token = localStorage.getItem('maxadmin_token') || ''
  try {
    const res = await fetch('/api/linux/ai/command', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ prompt: q }),
      signal: abort.signal,
    })

    if (!res.ok) {
      let msg = `请求失败（${res.status}）`
      try {
        const payload = await res.json()
        if (payload?.message) msg = payload.message
      } catch {
        /* ignore */
      }
      throw new Error(msg)
    }

    if (!res.body) throw new Error('无流式响应')

    const reader = res.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buf = ''
    /** 最终命令只取 delta.content；reasoning_content 仅流式展示 */
    let contentAcc = ''

    const consumeLine = (line: string) => {
      const trimmed = line.replace(/\r$/, '').trim()
      if (!trimmed.startsWith('data:')) return
      const data = trimmed.slice(5).trim()
      if (!data || data === '[DONE]') return
      try {
        const json = JSON.parse(data) as {
          choices?: Array<{
            delta?: { content?: string; reasoning_content?: string }
            message?: { content?: string }
          }>
        }
        const delta = json.choices?.[0]?.delta
        // DeepSeek：先 reasoning_content（思考），后 content（命令）
        const reason = delta?.reasoning_content ?? ''
        const content = delta?.content ?? json.choices?.[0]?.message?.content ?? ''
        if (reason) streamText.value += reason
        if (content) {
          contentAcc += content
          streamText.value += content
        }
      } catch {
        /* 非 JSON 行忽略 */
      }
    }

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })
      const parts = buf.split('\n')
      buf = parts.pop() || ''
      for (const line of parts) consumeLine(line)
    }
    if (buf.trim()) consumeLine(buf)

    answer.value = normalizeCmd(contentAcc || streamText.value)
    if (!answer.value) {
      Message.warning('未解析到有效命令，请换个说法再试')
      return
    }
    await loadHistory()
  } catch (err) {
    if ((err as Error).name === 'AbortError') return
    Message.error(err instanceof Error ? err.message : 'AI 查询失败')
  } finally {
    loading.value = false
  }
}

/** 按钮：把当前结果发到 SSH */
function runToSsh() {
  const cmd = normalizeCmd(answer.value)
  if (!cmd) {
    Message.warning('请先回车查询生成命令')
    return
  }
  emit('run', cmd)
}

function onKeydown(e: KeyboardEvent) {
  if (e.key !== 'Enter') return
  if (e.shiftKey) return // Shift+Enter 换行
  e.preventDefault()
  if (!loading.value) void ask()
}

function openHistory(item: LinuxAiChatItem) {
  prompt.value = item.prompt
  streamText.value = item.answer
  answer.value = item.answer
}

onMounted(() => {
  void loadHistory()
})
</script>

<template>
  <div class="ai-ssh">
    <p class="ai-ssh__hint">回车查询命令；点按钮发到当前 SSH 窗口（Shift+Enter 换行）</p>
    <textarea
      v-model="prompt"
      class="ai-ssh__textarea"
      rows="6"
      placeholder="例如：查看内存占用最高的进程"
      :disabled="loading"
      @keydown="onKeydown"
    />
   
    <!-- 上流：边收边显；下流：归一化后的可执行命令 -->
    <div v-if="loading || streamText" class="ai-ssh__stream" :class="{ 'ai-ssh__stream--live': loading }">
      <div class="ai-ssh__stream-label">{{ loading ? '流式输出' : '模型原文' }}</div>
      <pre class="ai-ssh__stream-body">{{ streamText || 'AI 正在思考...' }}<span
        v-if="loading"
        class="ai-ssh__caret"
      /></pre>
    </div>

    <button
      v-if="loading || streamText"
      type="button"
      class="ai-ssh__expand"
      @click="openStreamPopup"
    >
      弹窗查看
    </button>

    <div v-if="answer && !loading" class="ai-ssh__final">
      <div class="ai-ssh__stream-label">最终命令</div>
      <pre class="ai-ssh__result">{{ answer }}</pre>
      <MaxButton variant="primary" @click="runToSsh">运行到当前窗口</MaxButton>
    </div>
    <div class="ai-ssh__hist-head">
      <h4>历史记录</h4>
      <button type="button" class="ai-ssh__refresh" :disabled="historyLoading" @click="loadHistory">
        {{ historyLoading ? '加载中…' : '刷新' }}
      </button>
    </div>
    <p v-if="!history.length && !historyLoading" class="ai-ssh__empty">暂无记录</p>
    <button
      v-for="item in history"
      :key="item.id"
      type="button"
      class="ai-ssh__hist-item"
      @click="openHistory(item)"
    >
      <strong>{{ item.prompt }}</strong>
      <code>{{ item.answer }}</code>
      <em>{{ item.createdAt }}</em>
    </button>
  </div>
</template>

<style scoped>
.ai-ssh {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 8px;
  min-height: 0;
  height: 100%;
  overflow: auto;
}

.ai-ssh__hint {
  margin: 0;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
  line-height: 1.4;
}

.ai-ssh__textarea {
  width: 100%;
  min-height: 140px;
  resize: vertical;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  font-size: 14px;
  line-height: 1.5;
  outline: none;
  font-family: inherit;
  box-sizing: border-box;
}

.ai-ssh__textarea::placeholder {
  color: rgba(255, 255, 255, 0.38);
}

.ai-ssh__textarea:focus {
  border-color: rgba(10, 132, 255, 0.55);
  box-shadow: 0 0 0 3px rgba(10, 132, 255, 0.18);
}

.ai-ssh__textarea:disabled {
  opacity: 0.7;
}

.ai-ssh__stream-label {
  margin-bottom: 4px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
}

.ai-ssh__stream {
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(0, 0, 0, 0.28);
  padding: 8px 10px;
}

.ai-ssh__stream--live {
  border-color: rgba(10, 132, 255, 0.45);
}

.ai-ssh__expand {
  align-self: flex-start;
  margin: 0;
  padding: 0;
  border: none;
  background: transparent;
  color: rgba(10, 132, 255, 0.95);
  font-size: 11px;
  cursor: pointer;
}

.ai-ssh__stream-body {
  margin: 0;
  max-height: 180px;
  overflow-y: auto;
  min-height: 1.5em;
  color: rgba(255, 255, 255, 0.78);
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: Menlo, Monaco, 'Courier New', monospace;
}

.ai-ssh__caret {
  display: inline-block;
  width: 7px;
  height: 1em;
  margin-left: 2px;
  vertical-align: text-bottom;
  background: rgba(10, 132, 255, 0.9);
  animation: ai-blink 0.9s step-end infinite;
}

@keyframes ai-blink {
  50% {
    opacity: 0;
  }
}

.ai-ssh__final {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ai-ssh__result {
  margin: 0;
  padding: 10px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.35);
  border: 1px solid rgba(10, 132, 255, 0.28);
  color: #9ecbff;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: Menlo, Monaco, 'Courier New', monospace;
}

.ai-ssh__hist-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: 4px;
}

.ai-ssh__hist-head h4 {
  margin: 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
}

.ai-ssh__refresh {
  margin: 0;
  padding: 0;
  border: none;
  background: transparent;
  color: rgba(10, 132, 255, 0.95);
  font-size: 11px;
  cursor: pointer;
}

.ai-ssh__refresh:disabled {
  opacity: 0.5;
  cursor: default;
}

.ai-ssh__empty {
  margin: 0;
  padding: 12px 4px;
  text-align: center;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.35);
}

.ai-ssh__hist-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
  margin: 0;
  padding: 8px 10px;
  border: 1px solid transparent;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.04);
  color: #fff;
  text-align: left;
  cursor: pointer;
}

.ai-ssh__hist-item:hover {
  border-color: rgba(10, 132, 255, 0.35);
  background: rgba(10, 132, 255, 0.14);
}

.ai-ssh__hist-item strong {
  font-size: 12px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ai-ssh__hist-item code {
  font-size: 11px;
  color: #9ecbff;
  word-break: break-all;
  font-family: Menlo, Monaco, 'Courier New', monospace;
}

.ai-ssh__hist-item em {
  font-style: normal;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.4);
}
</style>
