<script setup lang="ts">
import { MaxButton } from '@/components/maxButton'

defineProps<{
  view: { streamText: string; loading: boolean; answer: string }
  onRun?: () => void
}>()
</script>

<template>
  <div class="ai-stream-wrap">
    <div class="ai-stream-body" :class="{ 'ai-stream-body--live': view.loading }">
      <div class="ai-stream-body__label">{{ view.loading ? '流式输出' : '模型原文' }}</div>
      <pre class="ai-stream-body__pre">{{ view.streamText || 'AI 正在思考...' }}<span
        v-if="view.loading"
        class="ai-stream-body__caret"
      /></pre>
    </div>

    <div v-if="view.answer && !view.loading" class="ai-stream-final">
      <div class="ai-stream-body__label">最终命令</div>
      <pre class="ai-stream-final__result">{{ view.answer }}</pre>
      <MaxButton variant="primary" @click="onRun?.()">运行到当前窗口</MaxButton>
    </div>
  </div>
</template>

<style scoped>
.ai-stream-wrap {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ai-stream-body {
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(0, 0, 0, 0.28);
  padding: 8px 10px;
}

.ai-stream-body--live {
  border-color: rgba(10, 132, 255, 0.45);
}

.ai-stream-body__label {
  margin-bottom: 4px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
}

.ai-stream-body__pre {
  margin: 0;
  max-height: min(52vh, 420px);
  overflow-y: auto;
  min-height: 1.5em;
  color: rgba(255, 255, 255, 0.78);
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: Menlo, Monaco, 'Courier New', monospace;
}

.ai-stream-body__caret {
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

.ai-stream-final {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ai-stream-final__result {
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
</style>
