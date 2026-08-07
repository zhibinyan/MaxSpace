<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import { linuxDockerExecWsUrl } from '@/api/linux'
import '@xterm/xterm/css/xterm.css'

const props = defineProps<{
  hostId: number
  container: string
}>()

const elRef = ref<HTMLElement | null>(null)
let term: Terminal | null = null
let fit: FitAddon | null = null
let socket: WebSocket | null = null
let ro: ResizeObserver | null = null

onMounted(() => {
  if (!elRef.value) return
  term = new Terminal({
    cursorBlink: true,
    fontSize: 13,
    fontFamily: 'Menlo, Monaco, "Courier New", monospace',
    theme: { background: '#0d1117', foreground: '#e6edf3' },
  })
  fit = new FitAddon()
  term.loadAddon(fit)
  term.open(elRef.value)
  fit.fit()

  const ws = new WebSocket(linuxDockerExecWsUrl(props.hostId, props.container))
  socket = ws
  ws.binaryType = 'arraybuffer'
  ws.onopen = () => {
    ws.send(JSON.stringify({ type: 'resize', cols: term!.cols, rows: term!.rows }))
  }
  ws.onmessage = (ev) => {
    if (typeof ev.data === 'string') {
      try {
        const msg = JSON.parse(ev.data)
        if (msg?.type === 'error') {
          term?.writeln(`\r\n\x1b[31m${msg.message}\x1b[0m`)
          return
        }
      } catch {
        /* plain text */
      }
      term?.write(ev.data)
      return
    }
    term?.write(new Uint8Array(ev.data as ArrayBuffer))
  }
  ws.onclose = () => term?.writeln('\r\n\x1b[33m[连接已关闭]\x1b[0m')
  term.onData((data) => {
    if (ws.readyState === WebSocket.OPEN) ws.send(data)
  })

  ro = new ResizeObserver(() => {
    try {
      fit?.fit()
      if (ws.readyState === WebSocket.OPEN && term) {
        ws.send(JSON.stringify({ type: 'resize', cols: term.cols, rows: term.rows }))
      }
    } catch {
      /* ignore */
    }
  })
  ro.observe(elRef.value)
})

onUnmounted(() => {
  ro?.disconnect()
  try {
    socket?.close()
  } catch {
    /* ignore */
  }
  term?.dispose()
  term = null
  fit = null
  socket = null
})
</script>

<template>
  <div class="docker-exec">
    <p class="docker-exec__hint">docker exec · {{ container }}</p>
    <div ref="elRef" class="docker-exec__term" />
  </div>
</template>

<style scoped>
.docker-exec {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 360px;
}
.docker-exec__hint {
  margin: 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.45);
}
.docker-exec__term {
  flex: 1;
  min-height: 340px;
  border-radius: 8px;
  overflow: hidden;
  background: #0d1117;
}
</style>
