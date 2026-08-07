<script setup lang="ts">
import { FitAddon } from '@xterm/addon-fit'
import { Terminal } from '@xterm/xterm'
import '@xterm/xterm/css/xterm.css'
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { linuxSshWsUrl } from '@/api/linux'
import { TERM_THEMES, type SshTermPrefs } from './sshSessionStore'

export type PaneStatus = 'idle' | 'connecting' | 'ready' | 'closed' | 'error'

const props = defineProps<{
  paneId: string
  hostId: number | null
  title: string
  active: boolean
  syncInput: boolean
  fontSize: number
  theme: SshTermPrefs['theme']
  recording: boolean
}>()

const emit = defineEmits<{
  status: [paneId: string, status: PaneStatus]
  focus: [paneId: string]
  command: [paneId: string, cmd: string]
  input: [paneId: string, data: string]
  ready: [paneId: string, sessionId: number]
  session: [paneId: string, sessionId: number]
}>()

const elRef = ref<HTMLDivElement | null>(null)
const status = ref<PaneStatus>('idle')
const sessionId = ref(0)

let term: Terminal | null = null
let fitAddon: FitAddon | null = null
let socket: WebSocket | null = null
let resizeObserver: ResizeObserver | null = null
let keepAliveTimer: ReturnType<typeof setInterval> | null = null
let lineBuf = ''
/** 正在吞掉 ESC 序列（方向键 / 鼠标 / CSI），避免污染命令历史 */
let escActive = false
let escBuf = ''
let selectCleanup: (() => void) | null = null

type CellPos = { col: number; row: number }

function setStatus(next: PaneStatus) {
  status.value = next
  emit('status', props.paneId, next)
}

function disposeSocket() {
  if (keepAliveTimer) {
    clearInterval(keepAliveTimer)
    keepAliveTimer = null
  }
  if (socket) {
    try {
      socket.close()
    } catch {
      /* ignore */
    }
    socket = null
  }
}

function disposeTerm() {
  selectCleanup?.()
  selectCleanup = null
  resizeObserver?.disconnect()
  resizeObserver = null
  fitAddon = null
  if (term) {
    term.dispose()
    term = null
  }
}

/** 鼠标坐标 → buffer 格子（含 viewport 偏移） */
function coordsFromEvent(ev: MouseEvent): CellPos | null {
  if (!term || !elRef.value) return null
  const screen = elRef.value.querySelector('.xterm-screen') as HTMLElement | null
  const target = screen || elRef.value
  const rect = target.getBoundingClientRect()
  if (rect.width <= 0 || rect.height <= 0) return null
  const cellW = rect.width / term.cols
  const cellH = rect.height / term.rows
  const col = Math.max(0, Math.min(term.cols - 1, Math.floor((ev.clientX - rect.left) / cellW)))
  const rowInView = Math.max(
    0,
    Math.min(term.rows - 1, Math.floor((ev.clientY - rect.top) / cellH)),
  )
  return { col, row: term.buffer.active.viewportY + rowInView }
}

function applyLocalSelection(a: CellPos, b: CellPos) {
  if (!term) return
  let start = a
  let end = b
  if (a.row > b.row || (a.row === b.row && a.col > b.col)) {
    start = b
    end = a
  }
  const cols = term.cols
  const length =
    start.row === end.row
      ? Math.max(1, end.col - start.col + 1)
      : cols - start.col + (end.row - start.row - 1) * cols + (end.col + 1)
  term.select(start.col, start.row, length)
}

async function copySelection() {
  if (!term?.hasSelection()) return false
  const text = term.getSelection()
  if (!text) return false
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    try {
      const ta = document.createElement('textarea')
      ta.value = text
      ta.style.position = 'fixed'
      ta.style.left = '-9999px'
      document.body.appendChild(ta)
      ta.select()
      const ok = document.execCommand('copy')
      ta.remove()
      return ok
    } catch {
      return false
    }
  }
}

/**
 * 方案 2：左键拖选走本地（拦截，不发 mouse 协议给 tmux）；
 * 滚轮不拦截 → 仍由 tmux mouse 翻历史。
 */
function bindLocalSelectAndCopy(root: HTMLElement) {
  let dragging = false
  let moved = false
  let start: CellPos | null = null
  let onMove: ((e: MouseEvent) => void) | null = null
  let onUp: ((e: MouseEvent) => void) | null = null

  const endDragListeners = () => {
    if (onMove) document.removeEventListener('mousemove', onMove, true)
    if (onUp) document.removeEventListener('mouseup', onUp, true)
    onMove = null
    onUp = null
  }

  const onDown = (ev: MouseEvent) => {
    if (!term || ev.button !== 0) return
    if (ev.ctrlKey || ev.metaKey || ev.altKey) return
    const pos = coordsFromEvent(ev)
    if (!pos) return

    dragging = true
    moved = false
    start = pos
    term.clearSelection()
    term.focus()
    emit('focus', props.paneId)
    ev.preventDefault()
    ev.stopImmediatePropagation()

    onMove = (e: MouseEvent) => {
      if (!dragging || !start || !term) return
      const p = coordsFromEvent(e)
      if (!p) return
      if (p.col !== start.col || p.row !== start.row) moved = true
      if (moved) applyLocalSelection(start, p)
      e.preventDefault()
      e.stopImmediatePropagation()
    }
    onUp = (e: MouseEvent) => {
      if (dragging && start && term) {
        const p = coordsFromEvent(e) || start
        if (!moved || (p.col === start.col && p.row === start.row)) {
          term.clearSelection()
        } else {
          applyLocalSelection(start, p)
        }
      }
      dragging = false
      moved = false
      start = null
      endDragListeners()
      e.preventDefault()
      e.stopImmediatePropagation()
    }
    document.addEventListener('mousemove', onMove, true)
    document.addEventListener('mouseup', onUp, true)
  }

  const onContextMenu = (ev: MouseEvent) => {
    if (!term?.hasSelection()) return
    ev.preventDefault()
    ev.stopPropagation()
    void copySelection()
  }

  root.addEventListener('mousedown', onDown, true)
  root.addEventListener('contextmenu', onContextMenu)

  selectCleanup = () => {
    endDragListeners()
    root.removeEventListener('mousedown', onDown, true)
    root.removeEventListener('contextmenu', onContextMenu)
  }
}

function applyTheme() {
  if (!term) return
  const t = TERM_THEMES[props.theme] || TERM_THEMES.dark
  term.options.theme = t
}

function fitAndResize() {
  if (!term || !fitAddon) return
  try {
    fitAddon.fit()
  } catch {
    /* ignore */
  }
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ type: 'resize', cols: term.cols, rows: term.rows }))
  }
}

function resetLineCapture() {
  lineBuf = ''
  escActive = false
  escBuf = ''
}

function feedEsc(ch: string): boolean {
  if (!escActive) return false
  escBuf += ch
  // CSI: ESC [ ... 最终字节 @-~（'[' 是引导符，不能当最终字节）
  if (escBuf.startsWith('\x1b[')) {
    if (escBuf.length >= 3) {
      const code = ch.charCodeAt(0)
      if (code >= 0x40 && code <= 0x7e) {
        escActive = false
        escBuf = ''
      }
    }
    return true
  }
  // SS3: ESC O A/B/C/D
  if (escBuf.startsWith('\x1bO')) {
    if (escBuf.length >= 3) {
      escActive = false
      escBuf = ''
    }
    return true
  }
  // 其它两字符 ESC 序列
  if (escBuf.length >= 2) {
    escActive = false
    escBuf = ''
  }
  return true
}

function sendRaw(data: string, fromSync = false) {
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(data)
  }
  if (fromSync) return

  for (const ch of data) {
    if (feedEsc(ch)) continue

    if (ch === '\x1b') {
      escActive = true
      escBuf = '\x1b'
      continue
    }

    // Ctrl+C / Ctrl+U：清空本地行缓冲
    if (ch === '\u0003' || ch === '\u0015') {
      resetLineCapture()
      continue
    }

    if (ch === '\r' || ch === '\n') {
      const cmd = lineBuf.replace(/\t/g, '').trim()
      if (cmd) {
        emit('command', props.paneId, cmd)
        if (socket?.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ type: 'command', text: cmd }))
        }
      }
      resetLineCapture()
      continue
    }

    if (ch === '\u007f' || ch === '\b') {
      lineBuf = lineBuf.slice(0, -1)
      continue
    }

    // Tab 由远端补全，不写入本地 buffer
    if (ch === '\t') continue

    if (ch >= ' ') {
      lineBuf += ch
    }
  }
}

function setRecording(on: boolean) {
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ type: 'record', on }))
  }
}

function connect() {
  disposeSocket()
  sessionId.value = 0
  if (!props.hostId || !term) {
    setStatus('idle')
    return
  }

  setStatus('connecting')
  term.reset()
  resetLineCapture()
  term.writeln(`\r\n\x1b[36m正在连接 ${props.title} ...\x1b[0m\r\n`)

  const ws = new WebSocket(linuxSshWsUrl(props.hostId))
  socket = ws
  ws.binaryType = 'arraybuffer'

  ws.onopen = () => {
    fitAndResize()
    keepAliveTimer = setInterval(() => {
      if (socket?.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'ping' }))
      }
    }, 25000)
  }

  ws.onmessage = (ev) => {
    if (typeof ev.data === 'string') {
      try {
        const msg = JSON.parse(ev.data)
        if (msg.type === 'ready') {
          setStatus('ready')
          const sid = Number(msg.sessionId || 0)
          sessionId.value = sid
          emit('ready', props.paneId, sid)
          emit('session', props.paneId, sid)
          if (msg.tmux) {
            term?.writeln(
              '\x1b[32m[tmux] 已附着（拖选可复制；滚轮翻历史；↑↓ 切换命令）\x1b[0m\r\n',
            )
          }
          if (props.recording) setRecording(true)
          return
        }
        if (msg.type === 'pong') return
        if (msg.type === 'record') return
        if (msg.type === 'error') {
          setStatus('error')
          term?.writeln(`\r\n\x1b[31m${msg.message || '连接失败'}\x1b[0m\r\n`)
          return
        }
      } catch {
        term?.write(ev.data)
      }
      return
    }
    term?.write(new Uint8Array(ev.data as ArrayBuffer))
  }

  ws.onerror = () => {
    setStatus('error')
    term?.writeln('\r\n\x1b[31mWebSocket 错误\x1b[0m\r\n')
  }

  ws.onclose = () => {
    if (status.value !== 'error') setStatus('closed')
    term?.writeln('\r\n\x1b[33m连接已关闭\x1b[0m\r\n')
  }
}

async function ensureTerm() {
  await nextTick()
  if (!elRef.value) return
  if (!term) {
    const t = TERM_THEMES[props.theme] || TERM_THEMES.dark
    term = new Terminal({
      cursorBlink: true,
      fontSize: props.fontSize,
      fontFamily: 'Menlo, Monaco, "Courier New", monospace',
      theme: t,
      scrollback: 10000,
      scrollOnUserInput: true,
      scrollSensitivity: 1,
      fastScrollSensitivity: 5,
    })
    fitAddon = new FitAddon()
    term.loadAddon(fitAddon)
    term.open(elRef.value)
    /**
     * 滚轮策略：
     * - 本地 buffer 有历史 → 滚 xterm 视口，不发给 shell（避免 ↑↓ 切命令）
     * - 本地无历史（常见于 tmux 备用屏）→ 交给 xterm/tmux（mouse on）滚内容
     */
    term.attachCustomWheelEventHandler((ev) => {
      if (!term || !elRef.value) return true
      const buf = term.buffer.active
      const canScrollLocal = buf.baseY > 0 || buf.viewportY > 0
      if (!canScrollLocal) return true
      ev.preventDefault()
      const cellH = Math.max(8, elRef.value.clientHeight / Math.max(term.rows, 1))
      let delta = ev.deltaY
      if (ev.deltaMode === WheelEvent.DOM_DELTA_LINE) delta *= cellH
      else if (ev.deltaMode === WheelEvent.DOM_DELTA_PAGE) delta *= elRef.value.clientHeight
      const dir = delta < 0 ? -1 : 1
      const lines = dir * Math.max(1, Math.round(Math.abs(delta) / cellH))
      term.scrollLines(lines)
      return false
    })
    // 有选区时 Cmd/Ctrl+C 复制，避免当成中断发给远端
    term.attachCustomKeyEventHandler((ev) => {
      if (ev.type !== 'keydown') return true
      const copyKey = (ev.metaKey || ev.ctrlKey) && ev.key.toLowerCase() === 'c'
      if (copyKey && term?.hasSelection()) {
        void copySelection()
        return false
      }
      return true
    })
    term.onData((data) => {
      emit('focus', props.paneId)
      sendRaw(data, false)
      if (props.syncInput) {
        emit('input', props.paneId, data)
      }
    })
    term.onSelectionChange(() => emit('focus', props.paneId))
    bindLocalSelectAndCopy(elRef.value)
    resizeObserver = new ResizeObserver(() => fitAndResize())
    resizeObserver.observe(elRef.value)
  }
  term.options.fontSize = props.fontSize
  applyTheme()
  fitAndResize()
}

function focus() {
  term?.focus()
}

function clear() {
  term?.clear()
}

function write(data: string) {
  sendRaw(data, true)
}

function reconnect() {
  connect()
}

function writeReplay(data: string | Uint8Array) {
  term?.write(data)
}

watch(
  () => props.hostId,
  async (id) => {
    await ensureTerm()
    if (id) connect()
    else {
      disposeSocket()
      setStatus('idle')
    }
  },
)

watch(
  () => props.fontSize,
  (size) => {
    if (term) {
      term.options.fontSize = size
      fitAndResize()
    }
  },
)

watch(
  () => props.theme,
  () => applyTheme(),
)

watch(
  () => props.recording,
  (on) => {
    if (status.value === 'ready') setRecording(on)
  },
)

watch(
  () => props.active,
  (active) => {
    if (active) {
      fitAndResize()
      focus()
    }
  },
)

onMounted(async () => {
  await ensureTerm()
  if (props.hostId) connect()
})

onUnmounted(() => {
  disposeSocket()
  disposeTerm()
})

defineExpose({
  focus,
  clear,
  write,
  reconnect,
  fitAndResize,
  setRecording,
  writeReplay,
  status,
  sessionId,
})
</script>

<template>
  <div
    class="ssh-pane"
    :class="{ 'ssh-pane--active': active }"
    @mousedown="emit('focus', paneId)"
  >
    <header class="ssh-pane__head">
      <span class="ssh-pane__title">{{ title || '空闲' }}</span>
      <em class="ssh-pane__status">
        {{ status }}
        <span v-if="recording && status === 'ready'" class="ssh-pane__rec">REC</span>
      </em>
    </header>
    <div ref="elRef" class="ssh-pane__term" title="拖选文字后右键或 Cmd/Ctrl+C 复制；滚轮翻历史" />
  </div>
</template>

<style scoped>
.ssh-pane {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  height: 100%;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  overflow: hidden;
  background: #0d1117;
}

.ssh-pane--active {
  border-color: rgba(10, 132, 255, 0.55);
  box-shadow: inset 0 0 0 1px rgba(10, 132, 255, 0.25);
}

.ssh-pane__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 4px 10px;
  background: rgba(255, 255, 255, 0.04);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.ssh-pane__title {
  color: rgba(255, 255, 255, 0.88);
  font-size: 12px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ssh-pane__status {
  font-style: normal;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.ssh-pane__rec {
  color: #ff6b6b;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.ssh-pane__term {
  flex: 1;
  min-height: 0;
  padding: 6px;
  overflow: hidden;
}

.ssh-pane__term :deep(.xterm) {
  width: 100%;
  height: 100%;
}
</style>
