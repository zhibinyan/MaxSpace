<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  fetchLinuxHosts,
  getLinuxPref,
  setLinuxPref,
  type LinuxHost,
} from '@/api/linux'
import Message from '@/components/massage'
import { MaxButton } from '@/components/maxButton'
import { MaxSelect, type MaxSelectOption } from '@/components/maxSelect'
import { LayoutToolbar } from '@/layout'
import dockerCmdDocs from '../docker.json'
import AIssh from './AIssh.vue'
import SshTermPane, { type PaneStatus } from './SshTermPane.vue'
import {
  DEFAULT_LAYOUT_RATIOS,
  DEFAULT_TERM_PREFS,
  loadRecentSessionsAsync,
  loadWorkspace,
  pushCmdHistory,
  saveWorkspace,
  syncOpenSession,
  type SshLayoutMode,
  type SshLayoutRatios,
  type SshRecentSession,
  type SshTermPrefs,
} from './sshSessionStore'

defineOptions({ name: 'SshTerminalView' })

type DockerCmdItem = { command: string; description?: string }
type DockerExample = { purpose: string; command: string; notes?: string }
type DockerTechnology = {
  name: string
  description?: string
  examples?: DockerExample[]
}
type DockerCategory = {
  name: string
  commands?: DockerCmdItem[]
  technologies?: DockerTechnology[]
}
type DockerDoc = {
  title: string
  categories: DockerCategory[]
}

const dockerDocs = dockerCmdDocs as DockerDoc[]
const expandedCats = ref<Record<string, boolean>>({})

interface PaneState {
  id: string
  hostId: number | null
  title: string
  status: PaneStatus
  sessionId: number
}

const route = useRoute()
const router = useRouter()

const hosts = ref<LinuxHost[]>([])
const pickHostId = ref('')
const layout = ref<SshLayoutMode>('single')
const syncInput = ref(false)
const recording = ref(false)
const fontSize = ref(DEFAULT_TERM_PREFS.fontSize)
const theme = ref<SshTermPrefs['theme']>(DEFAULT_TERM_PREFS.theme)
const encoding = ref(DEFAULT_TERM_PREFS.encoding)
const ratios = ref<SshLayoutRatios>({ ...DEFAULT_LAYOUT_RATIOS })
const activePaneId = ref('p0')
const sideTab = ref<'recent' | 'cmds' | 'ai'>('recent')

const recent = ref<SshRecentSession[]>([])

const paneRefs = ref<Record<string, InstanceType<typeof SshTermPane> | null>>({})
const stageRef = ref<HTMLElement | null>(null)
const workspaceReady = ref(false)

const panes = ref<PaneState[]>([
  { id: 'p0', hostId: null, title: 'Pane 1', status: 'idle', sessionId: 0 },
])

const hostOptions = computed<MaxSelectOption[]>(() => [
  { label: '选择主机…', value: '' },
  ...hosts.value.map((h) => ({
    label: `${h.name} (${h.host})`,
    value: String(h.id),
  })),
])

const layoutOptions: MaxSelectOption[] = [
  { label: '单屏', value: 'single' },
  { label: '左右分屏', value: 'horizontal' },
  { label: '上下分屏', value: 'vertical' },
  { label: '四宫格', value: 'quad' },
]

const themeOptions: MaxSelectOption[] = [
  { label: '暗色', value: 'dark' },
  { label: '亮色', value: 'light' },
  { label: 'Solarized', value: 'solarized' },
  { label: 'Monokai', value: 'monokai' },
]

const encodingOptions: MaxSelectOption[] = [
  { label: 'UTF-8', value: 'utf-8' },
  { label: 'GBK（显示用）', value: 'gbk' },
]

const paneCount = computed(() => {
  if (layout.value === 'single') return 1
  if (layout.value === 'quad') return 4
  return 2
})

const visiblePanes = computed(() => panes.value.slice(0, paneCount.value))

function recentHostStatus(hostId: number): PaneStatus | 'offline' {
  const pane = visiblePanes.value.find((p) => p.hostId === hostId)
  return pane?.status ?? 'offline'
}

function paneStatusLabel(status: PaneStatus | 'offline'): string {
  if (status === 'ready') return 'ready'
  if (status === 'connecting') return 'connecting'
  if (status === 'closed') return 'closed'
  if (status === 'error') return 'error'
  if (status === 'offline') return 'offline'
  return 'idle'
}

function paneStatusTone(status: PaneStatus | 'offline'): string {
  if (status === 'ready') return 'ready'
  if (status === 'connecting') return 'connecting'
  if (status === 'error') return 'error'
  if (status === 'closed' || status === 'offline') return 'offline'
  return 'idle'
}

const stageStyle = computed(() => {
  const r = ratios.value
  if (layout.value === 'horizontal') {
    return {
      gridTemplateColumns: `${r.horizontal[0]}fr ${r.horizontal[1]}fr`,
      gridTemplateRows: '1fr',
      '--split-x': `${(r.horizontal[0] / (r.horizontal[0] + r.horizontal[1])) * 100}%`,
    } as Record<string, string>
  }
  if (layout.value === 'vertical') {
    return {
      gridTemplateColumns: '1fr',
      gridTemplateRows: `${r.vertical[0]}fr ${r.vertical[1]}fr`,
      '--split-y': `${(r.vertical[0] / (r.vertical[0] + r.vertical[1])) * 100}%`,
    } as Record<string, string>
  }
  if (layout.value === 'quad') {
    return {
      gridTemplateColumns: `${r.quadCols[0]}fr ${r.quadCols[1]}fr`,
      gridTemplateRows: `${r.quadRows[0]}fr ${r.quadRows[1]}fr`,
      '--split-x': `${(r.quadCols[0] / (r.quadCols[0] + r.quadCols[1])) * 100}%`,
      '--split-y': `${(r.quadRows[0] / (r.quadRows[0] + r.quadRows[1])) * 100}%`,
    } as Record<string, string>
  }
  return { gridTemplateColumns: '1fr', gridTemplateRows: '1fr' }
})

function setPaneRef(id: string, el: unknown) {
  paneRefs.value[id] = (el as InstanceType<typeof SshTermPane>) || null
}

function ensurePaneCount() {
  const need = paneCount.value
  while (panes.value.length < need) {
    const idx = panes.value.length
    panes.value.push({
      id: `p${idx}`,
      hostId: null,
      title: `Pane ${idx + 1}`,
      status: 'idle',
      sessionId: 0,
    })
  }
  if (!visiblePanes.value.find((p) => p.id === activePaneId.value)) {
    activePaneId.value = visiblePanes.value[0]?.id || 'p0'
  }
}

async function refreshLists() {
  recent.value = await loadRecentSessionsAsync()
}

function catKey(docIndex: number, catIndex: number) {
  return `${docIndex}-${catIndex}`
}

function isCatOpen(docIndex: number, catIndex: number) {
  const key = catKey(docIndex, catIndex)
  if (key in expandedCats.value) return expandedCats.value[key]
  return docIndex === 0 && catIndex === 0
}

function toggleCat(docIndex: number, catIndex: number) {
  const key = catKey(docIndex, catIndex)
  expandedCats.value[key] = !isCatOpen(docIndex, catIndex)
}

function runDockerCmd(raw: string) {
  let cmd = raw.trim()
  if (!cmd) return
  if (!cmd.includes('\n') && cmd.includes(' 或 ')) {
    cmd = cmd.split(' 或 ')[0]!.trim()
  }
  // 只填入终端，不回车；用户确认后再按 Enter 发送
  sendToActive(cmd.endsWith('\n') ? cmd.replace(/\n+$/, '') : cmd, false)
}

async function loadHosts() {
  hosts.value = await fetchLinuxHosts()
}

async function loadPrefs() {
  try {
    const term = await getLinuxPref<SshTermPrefs>('ssh.term')
    if (term) {
      fontSize.value = term.fontSize || DEFAULT_TERM_PREFS.fontSize
      theme.value = term.theme || DEFAULT_TERM_PREFS.theme
      encoding.value = term.encoding || DEFAULT_TERM_PREFS.encoding
    }
    const layoutRatios = await getLinuxPref<SshLayoutRatios>('ssh.layoutRatios')
    if (layoutRatios) {
      ratios.value = { ...DEFAULT_LAYOUT_RATIOS, ...layoutRatios }
    }
  } catch {
    /* ignore */
  }
}

function persistTermPrefs() {
  void setLinuxPref('ssh.term', {
    fontSize: fontSize.value,
    theme: theme.value,
    encoding: encoding.value,
  })
}

function persistRatios() {
  void setLinuxPref('ssh.layoutRatios', ratios.value)
}

function focusPane(id: string) {
  activePaneId.value = id
}

function onPaneStatus(paneId: string, status: PaneStatus) {
  const pane = panes.value.find((p) => p.id === paneId)
  if (pane) pane.status = status
}

function onPaneSession(paneId: string, sid: number) {
  const pane = panes.value.find((p) => p.id === paneId)
  if (pane) pane.sessionId = sid
}

function onPaneCommand(_paneId: string, cmd: string) {
  pushCmdHistory(cmd)
}

function onPaneInput(fromId: string, data: string) {
  if (!syncInput.value) return
  for (const pane of visiblePanes.value) {
    if (pane.id === fromId || !pane.hostId) continue
    paneRefs.value[pane.id]?.write(data)
  }
}

async function bindHostToPane(paneId: string, hostId: number) {
  const host = hosts.value.find((h) => h.id === hostId)
  if (!host) {
    Message.warning('主机不存在')
    return
  }
  const pane = panes.value.find((p) => p.id === paneId)
  if (!pane) return
  pane.hostId = host.id
  pane.title = host.name
  pane.status = 'connecting'
  pane.sessionId = 0
  activePaneId.value = paneId

  const meta = {
    hostId: host.id,
    title: host.name,
    host: host.host,
    username: host.username,
    port: host.port,
  }
  await syncOpenSession(meta)
  await refreshLists()
}

function openOnActivePane(hostId: number) {
  void bindHostToPane(activePaneId.value, hostId)
}

function addFromPicker() {
  if (!pickHostId.value) {
    Message.warning('请选择主机')
    return
  }
  openOnActivePane(Number(pickHostId.value))
}

function openSessionSmart(hostId: number) {
  const idle = visiblePanes.value.find((p) => !p.hostId)
  void bindHostToPane(idle?.id || activePaneId.value, hostId)
}

function reconnectActive() {
  paneRefs.value[activePaneId.value]?.reconnect()
}

function clearActive() {
  // 只对当前 SSH 窗格执行 clear，不联动其它窗格
  paneRefs.value[activePaneId.value]?.write('clear\n')
}

function reconnectAll() {
  for (const p of visiblePanes.value) {
    if (p.hostId) paneRefs.value[p.id]?.reconnect()
  }
}

function zoom(delta: number) {
  fontSize.value = Math.min(24, Math.max(10, fontSize.value + delta))
  persistTermPrefs()
}

function toggleRecording() {
  recording.value = !recording.value
  Message.info(recording.value ? '已开启录制（写入当前在线会话）' : '已停止录制')
}

function sendToActive(cmd: string, asEnter = true) {
  const text = asEnter && !cmd.endsWith('\n') ? `${cmd}\n` : cmd
  paneRefs.value[activePaneId.value]?.write(text)
  if (syncInput.value) {
    for (const pane of visiblePanes.value) {
      if (pane.id === activePaneId.value || !pane.hostId) continue
      paneRefs.value[pane.id]?.write(text)
    }
  }
  pushCmdHistory(cmd.replace(/\r?\n$/, ''))
}

function runHistoryCmd(cmd: string) {
  sendToActive(cmd, true)
}

/** 拖拽分割条 */
function startDrag(kind: 'h' | 'v' | 'qc' | 'qr', e: MouseEvent) {
  e.preventDefault()
  const stage = stageRef.value
  if (!stage) return
  const rect = stage.getBoundingClientRect()
  const onMove = (ev: MouseEvent) => {
    if (kind === 'h') {
      const ratio = Math.min(0.85, Math.max(0.15, (ev.clientX - rect.left) / rect.width))
      const a = Math.round(ratio * 100)
      ratios.value.horizontal = [a, 100 - a]
    } else if (kind === 'v') {
      const ratio = Math.min(0.85, Math.max(0.15, (ev.clientY - rect.top) / rect.height))
      const a = Math.round(ratio * 100)
      ratios.value.vertical = [a, 100 - a]
    } else if (kind === 'qc') {
      const ratio = Math.min(0.85, Math.max(0.15, (ev.clientX - rect.left) / rect.width))
      const a = Math.round(ratio * 100)
      ratios.value.quadCols = [a, 100 - a]
    } else {
      const ratio = Math.min(0.85, Math.max(0.15, (ev.clientY - rect.top) / rect.height))
      const a = Math.round(ratio * 100)
      ratios.value.quadRows = [a, 100 - a]
    }
    void nextTick(() => {
      for (const p of visiblePanes.value) paneRefs.value[p.id]?.fitAndResize?.()
    })
  }
  const onUp = () => {
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('mouseup', onUp)
    persistRatios()
    void nextTick(() => {
      for (const p of visiblePanes.value) paneRefs.value[p.id]?.fitAndResize?.()
    })
  }
  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onUp)
}

function persistWorkspace() {
  if (!workspaceReady.value) return
  saveWorkspace({
    layout: layout.value,
    activePaneId: activePaneId.value,
    syncInput: syncInput.value,
    panes: panes.value.map((p) => ({
      id: p.id,
      hostId: p.hostId,
      title: p.title,
    })),
  })
}

function restoreWorkspace() {
  const ws = loadWorkspace()
  if (!ws?.panes?.length) return false

  layout.value = ws.layout || 'single'
  if (typeof ws.syncInput === 'boolean') syncInput.value = ws.syncInput

  // 先按布局补齐窗格，再按保存的 panes 补齐（四宫格切左右后再回来也不丢）
  ensurePaneCount()
  const need = Math.max(paneCount.value, ws.panes.length)
  while (panes.value.length < need) {
    const idx = panes.value.length
    panes.value.push({
      id: `p${idx}`,
      hostId: null,
      title: `Pane ${idx + 1}`,
      status: 'idle',
      sessionId: 0,
    })
  }

  for (const saved of ws.panes) {
    let pane = panes.value.find((p) => p.id === saved.id)
    if (!pane) {
      pane = {
        id: saved.id,
        hostId: null,
        title: saved.title || saved.id,
        status: 'idle',
        sessionId: 0,
      }
      panes.value.push(pane)
    }
    if (saved.hostId && hosts.value.some((h) => h.id === saved.hostId)) {
      pane.hostId = saved.hostId
      pane.title =
        saved.title || hosts.value.find((h) => h.id === saved.hostId)?.name || pane.title
      pane.status = 'connecting'
    } else if (!saved.hostId) {
      pane.hostId = null
      pane.title = saved.title || pane.title
      pane.status = 'idle'
    }
  }

  if (ws.activePaneId && panes.value.some((p) => p.id === ws.activePaneId)) {
    activePaneId.value = ws.activePaneId
  } else if (!visiblePanes.value.find((p) => p.id === activePaneId.value)) {
    activePaneId.value = visiblePanes.value[0]?.id || 'p0'
  }

  return panes.value.some((p) => p.hostId != null)
}

function flushWorkspaceOnLeave() {
  workspaceReady.value = true
  persistWorkspace()
}

watch(
  [layout, activePaneId, panes, syncInput],
  () => persistWorkspace(),
  { deep: true },
)

watch(layout, () => {
  ensurePaneCount()
  void nextTick(() => {
    for (const p of visiblePanes.value) paneRefs.value[p.id]?.fitAndResize?.()
  })
})

watch([theme, encoding], () => persistTermPrefs())

watch(
  () => route.query.hostId,
  (val) => {
    if (!workspaceReady.value || !val) return
    const hid = Number(val)
    if (!Number.isFinite(hid)) return
    // 已在某分屏中则只激活，避免刷新/带参跳转打乱布局
    const existing = panes.value.find((p) => p.hostId === hid)
    if (existing) {
      activePaneId.value = existing.id
      return
    }
    openSessionSmart(hid)
  },
)

onMounted(async () => {
  ensurePaneCount()
  await loadPrefs()
  await refreshLists()
  await loadHosts()

  const q = route.query.hostId
  restoreWorkspace()

  if (q) {
    const hid = Number(q)
    if (Number.isFinite(hid)) {
      const already = panes.value.some((p) => p.hostId === hid)
      if (!already) openSessionSmart(hid)
    }
    // 清掉 hostId，避免再次 F5 只按单主机打开而丢掉分屏
    const nextQuery = { ...route.query }
    delete nextQuery.hostId
    void router.replace({ query: nextQuery })
  }

  workspaceReady.value = true
  persistWorkspace()

  window.addEventListener('pagehide', flushWorkspaceOnLeave)
})

onUnmounted(() => {
  window.removeEventListener('pagehide', flushWorkspaceOnLeave)
  flushWorkspaceOnLeave()
})
</script>

<template>
  <div class="ssh-page">
    <LayoutToolbar>
      <template #left>
        <MaxSelect v-model="pickHostId" :width="200" :options="hostOptions" />
        <MaxButton variant="primary" @click="addFromPicker">连接到当前窗格</MaxButton>
        <MaxSelect v-model="layout" :width="120" :options="layoutOptions" />
        <MaxButton :variant="syncInput ? 'primary' : 'ghost'" @click="syncInput = !syncInput">
          {{ syncInput ? '同步输入·开' : '同步输入·关' }}
        </MaxButton>
         <MaxButton @click="reconnectActive">重连</MaxButton>
        <MaxButton @click="reconnectAll">全部重连</MaxButton>
        <MaxButton @click="clearActive">清屏</MaxButton>
        <MaxButton @click="zoom(1)">字体+</MaxButton>
        <MaxButton @click="zoom(-1)">字体-</MaxButton>
        <MaxSelect v-model="theme" :width="120" :options="themeOptions" />
        <MaxSelect v-model="encoding" :width="120" :options="encodingOptions" />
         <MaxButton :variant="recording ? 'primary' : 'ghost'" @click="toggleRecording">
          {{ recording ? '录制中' : '录制' }}
        </MaxButton>
       
        <MaxButton @click="router.push({ name: 'linuxAudit' })">审计</MaxButton>
      </template>
      <template #right>
       
        <MaxButton @click="router.push({ name: 'linuxHosts' })">主机管理</MaxButton>
      </template>
    </LayoutToolbar>

    <div class="ssh-body">
      <aside class="ssh-side">
        <div class="ssh-side__tabs">
          <button type="button" :class="{ on: sideTab === 'recent' }" @click="sideTab = 'recent'">
            最近
          </button>
          <button type="button" :class="{ on: sideTab === 'cmds' }" @click="sideTab = 'cmds'">
            命令
          </button>
          <button type="button" :class="{ on: sideTab === 'ai' }" @click="sideTab = 'ai'">
            AI
          </button>
        </div>

        <div v-if="sideTab === 'recent'" class="ssh-side__list">
          <p v-if="!recent.length" class="ssh-side__empty">暂无最近会话</p>
          <button
            v-for="item in recent"
            :key="`${item.hostId}-${item.lastAt}`"
            type="button"
            class="ssh-side__item"
            @click="openSessionSmart(item.hostId)"
          >
            <div class="ssh-side__item-top">
              <strong>{{ item.title }}</strong>
              <em
                class="ssh-status"
                :class="`ssh-status--${paneStatusTone(recentHostStatus(item.hostId))}`"
              >
                {{ paneStatusLabel(recentHostStatus(item.hostId)) }}
              </em>
            </div>
            <span>{{ item.username }}@{{ item.host }}:{{ item.port }}</span>
          </button>
        </div>

        <div v-else-if="sideTab === 'cmds'" class="ssh-side__list ssh-side__cmds">
          <div v-for="(doc, di) in dockerDocs" :key="doc.title" class="ssh-side__doc">
            <h4 class="ssh-side__doc-title">{{ doc.title }}</h4>
            <div v-for="(cat, ci) in doc.categories" :key="cat.name" class="ssh-side__cat">
              <button type="button" class="ssh-side__cat-toggle" @click="toggleCat(di, ci)">
                <em>{{ isCatOpen(di, ci) ? '▾' : '▸' }}</em>
                <span>{{ cat.name }}</span>
              </button>
              <div v-if="isCatOpen(di, ci)" class="ssh-side__cat-body">
                <button
                  v-for="(item, idx) in cat.commands || []"
                  :key="`${cat.name}-c-${idx}`"
                  type="button"
                  class="ssh-side__item"
                  :title="item.description || item.command"
                  @click="runDockerCmd(item.command)"
                >
                  <strong>{{ item.command }}</strong>
                  <span v-if="item.description">{{ item.description }}</span>
                </button>
                <template v-for="(tech, ti) in cat.technologies || []" :key="`${cat.name}-t-${ti}`">
                  <p class="ssh-side__tech">{{ tech.name }}</p>
                  <button
                    v-for="(ex, ei) in tech.examples || []"
                    :key="`${cat.name}-t-${ti}-e-${ei}`"
                    type="button"
                    class="ssh-side__item"
                    :title="ex.notes || ex.purpose"
                    @click="runDockerCmd(ex.command)"
                  >
                    <strong>{{ ex.purpose }}</strong>
                    <span>{{ ex.command }}</span>
                  </button>
                </template>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="ssh-side__ai">
          <AIssh @run="runHistoryCmd" />
        </div>
      </aside>

      <div ref="stageRef" class="ssh-stage" :class="`ssh-stage--${layout}`" :style="stageStyle">
        <SshTermPane
          v-for="pane in visiblePanes"
          :key="pane.id"
          :ref="(el) => setPaneRef(pane.id, el)"
          :pane-id="pane.id"
          :host-id="pane.hostId"
          :title="pane.title"
          :active="activePaneId === pane.id"
          :sync-input="syncInput"
          :font-size="fontSize"
          :theme="theme"
          :recording="recording"
          @focus="focusPane"
          @status="onPaneStatus"
          @session="onPaneSession"
          @command="onPaneCommand"
          @input="onPaneInput"
        />

        <div
          v-if="layout === 'horizontal'"
          class="ssh-split ssh-split--v"
          @mousedown="startDrag('h', $event)"
        />
        <div
          v-if="layout === 'vertical'"
          class="ssh-split ssh-split--h"
          @mousedown="startDrag('v', $event)"
        />
        <template v-if="layout === 'quad'">
          <div class="ssh-split ssh-split--v ssh-split--quad-c" @mousedown="startDrag('qc', $event)" />
          <div class="ssh-split ssh-split--h ssh-split--quad-r" @mousedown="startDrag('qr', $event)" />
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ssh-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  gap: 8px;
}

.ssh-body {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 10px;
}

.ssh-side {
  display: flex;
  flex-direction: column;
  min-height: 0;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.04);
  overflow: hidden;
}

.ssh-side__tabs {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.ssh-side__tabs button {
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.55);
  padding: 10px 4px;
  font-size: 12px;
  cursor: pointer;
}

.ssh-side__tabs button.on {
  color: #fff;
  background: rgba(10, 132, 255, 0.22);
}

.ssh-side__list,
.ssh-side__ai {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ssh-side__ai {
  padding: 0;
}

.ssh-side__empty {
  margin: 24px 8px;
  text-align: center;
  color: rgba(255, 255, 255, 0.4);
  font-size: 12px;
}

.ssh-side__item {
  display: flex;
  flex-direction: column;
  gap: 2px;
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

.ssh-side__item:hover {
  border-color: rgba(10, 132, 255, 0.35);
  background: rgba(10, 132, 255, 0.14);
}

.ssh-side__item strong {
  font-size: 13px;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ssh-side__item-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.ssh-side__item span {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.55);
  word-break: break-all;
}

.ssh-side__cmds {
  gap: 10px;
}

.ssh-side__doc-title {
  margin: 4px 2px 6px;
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.78);
  line-height: 1.4;
}

.ssh-side__cat {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 6px;
}

.ssh-side__cat-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  margin: 0;
  padding: 6px 8px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.88);
  font-size: 12px;
  text-align: left;
  cursor: pointer;
}

.ssh-side__cat-toggle em {
  flex-shrink: 0;
  width: 12px;
  font-style: normal;
  color: rgba(255, 255, 255, 0.45);
}

.ssh-side__cat-toggle:hover {
  border-color: rgba(10, 132, 255, 0.35);
  background: rgba(10, 132, 255, 0.12);
}

.ssh-side__cat-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-left: 2px;
}

.ssh-side__tech {
  margin: 4px 2px 0;
  font-size: 11px;
  color: rgba(158, 203, 255, 0.9);
}

.ssh-status {
  flex-shrink: 0;
  margin: 0;
  padding: 1px 7px;
  border-radius: 999px;
  font-size: 10px;
  font-style: normal;
  font-weight: 600;
  letter-spacing: 0.02em;
  line-height: 1.5;
}

.ssh-status--ready {
  background: rgba(40, 200, 64, 0.25);
  color: #8dff9d;
}

.ssh-status--connecting {
  background: rgba(10, 132, 255, 0.28);
  color: #9ecbff;
}

.ssh-status--offline,
.ssh-status--idle {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.55);
}

.ssh-status--error {
  background: rgba(255, 80, 80, 0.22);
  color: #ffb4ae;
}

.ssh-side__hist-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 2px 2px 4px;
}

.ssh-side__hist-head h4 {
  margin: 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
}

.ssh-side__refresh {
  margin: 0;
  padding: 0;
  border: none;
  background: transparent;
  color: rgba(10, 132, 255, 0.95);
  font-size: 11px;
  cursor: pointer;
}

.ssh-side__refresh:disabled {
  opacity: 0.5;
  cursor: default;
}

.ssh-side__time {
  font-style: normal;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.4);
}

.ssh-stage {
  position: relative;
  min-height: 0;
  display: grid;
  gap: 8px;
}

.ssh-split {
  position: absolute;
  z-index: 5;
  background: rgba(10, 132, 255, 0.35);
  transition: background 0.15s ease;
}

.ssh-split:hover {
  background: rgba(10, 132, 255, 0.7);
}

.ssh-split--v {
  top: 0;
  bottom: 0;
  width: 6px;
  left: var(--split-x, 50%);
  transform: translateX(-50%);
  cursor: col-resize;
}

.ssh-split--h {
  left: 0;
  right: 0;
  height: 6px;
  top: var(--split-y, 50%);
  transform: translateY(-50%);
  cursor: row-resize;
}

.ssh-stage--horizontal > .ssh-split--v,
.ssh-stage--quad > .ssh-split--quad-c {
  left: var(--split-x, 50%);
}

.ssh-stage--vertical > .ssh-split--h,
.ssh-stage--quad > .ssh-split--quad-r {
  top: var(--split-y, 50%);
}
</style>
