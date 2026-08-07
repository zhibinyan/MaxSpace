<script setup lang="ts">
import { FitAddon } from '@xterm/addon-fit'
import { Terminal } from '@xterm/xterm'
import '@xterm/xterm/css/xterm.css'
import { nextTick, onMounted, onUnmounted, ref } from 'vue'
import { fetchSessionRecording } from '@/api/linux'
import Message from '@/components/massage'
import { TERM_THEMES } from '../ssh/sshSessionStore'

const props = defineProps<{
  sessionId: number
  title?: string
}>()

const elRef = ref<HTMLDivElement | null>(null)
const loading = ref(true)
let term: Terminal | null = null
let fitAddon: FitAddon | null = null

onMounted(async () => {
  await nextTick()
  if (!elRef.value) return
  const theme = TERM_THEMES.dark
  term = new Terminal({
    cursorBlink: false,
    disableStdin: true,
    fontSize: 13,
    fontFamily: 'Menlo, Monaco, "Courier New", monospace',
    theme,
  })
  fitAddon = new FitAddon()
  term.loadAddon(fitAddon)
  term.open(elRef.value)
  fitAddon.fit()

  try {
    const data = await fetchSessionRecording(props.sessionId)
    loading.value = false
    if (!data.chunks.length) {
      term.writeln('\x1b[33m该会话没有录制内容\x1b[0m')
      return
    }
    for (const chunk of data.chunks) {
      const binary = atob(chunk)
      const bytes = new Uint8Array(binary.length)
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
      term.write(bytes)
      await new Promise((r) => setTimeout(r, 8))
    }
  } catch (err) {
    loading.value = false
    Message.error(err instanceof Error ? err.message : '回放失败')
    term.writeln('\x1b[31m回放失败\x1b[0m')
  }
})

onUnmounted(() => {
  term?.dispose()
  term = null
  fitAddon = null
})
</script>

<template>
  <div class="replay">
    <p v-if="loading" class="replay__hint">加载录制…</p>
    <div ref="elRef" class="replay__term" />
  </div>
</template>

<style scoped>
.replay {
  min-height: 360px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.replay__hint {
  margin: 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
}
.replay__term {
  flex: 1;
  min-height: 340px;
  border-radius: 8px;
  overflow: hidden;
  background: #0d1117;
  padding: 8px;
}
</style>
