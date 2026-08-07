/** SSH 会话 / 命令持久化：优先服务端，失败回落 localStorage */

import {
  fetchSshHistory,
  fetchSshRecent,
  registerSshSession,
  type SshSessionItem,
} from '@/api/linux'

export type SshLayoutMode = 'single' | 'horizontal' | 'vertical' | 'quad'

export interface SshRecentSession {
  hostId: number
  title: string
  host: string
  username: string
  port: number
  lastAt: string
  sessionId?: number
  hasRecording?: boolean
}

export interface SshCmdTemplate {
  id: string
  name: string
  command: string
}

export interface SshTermPrefs {
  fontSize: number
  theme: 'dark' | 'light' | 'solarized' | 'monokai'
  encoding: string
}

export interface SshLayoutRatios {
  horizontal: [number, number]
  vertical: [number, number]
  quadCols: [number, number]
  quadRows: [number, number]
}

const RECENT_KEY = 'maxadmin_ssh_recent'
const HISTORY_KEY = 'maxadmin_ssh_history'
const CMD_HISTORY_KEY = 'maxadmin_ssh_cmd_history'
const TEMPLATES_KEY = 'maxadmin_ssh_cmd_templates'
const MAX_RECENT = 30
const MAX_HISTORY = 50
const MAX_CMD = 100

const DEFAULT_TEMPLATES: SshCmdTemplate[] = [
  { id: 't1', name: '磁盘', command: 'df -h\n' },
  { id: 't2', name: '内存', command: 'free -h\n' },
  { id: 't3', name: '进程', command: 'top -bn1 | head -n 20\n' },
  { id: 't4', name: '网络', command: 'ss -lntp\n' },
  { id: 't5', name: '系统', command: 'uname -a && uptime\n' },
  { id: 't6', name: 'Docker', command: 'docker ps -a\n' },
]

export const DEFAULT_TERM_PREFS: SshTermPrefs = {
  fontSize: 14,
  theme: 'dark',
  encoding: 'utf-8',
}

export const DEFAULT_LAYOUT_RATIOS: SshLayoutRatios = {
  horizontal: [1, 1],
  vertical: [1, 1],
  quadCols: [1, 1],
  quadRows: [1, 1],
}

export const TERM_THEMES: Record<
  SshTermPrefs['theme'],
  { background: string; foreground: string; cursor: string }
> = {
  dark: { background: '#0d1117', foreground: '#e6edf3', cursor: '#58a6ff' },
  light: { background: '#f6f8fa', foreground: '#1f2328', cursor: '#0969da' },
  solarized: { background: '#002b36', foreground: '#839496', cursor: '#268bd2' },
  monokai: { background: '#272822', foreground: '#f8f8f2', cursor: '#f92672' },
}

function readJson<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return fallback
    return JSON.parse(raw) as T
  } catch {
    return fallback
  }
}

function writeJson(key: string, value: unknown) {
  localStorage.setItem(key, JSON.stringify(value))
}

function mapServerItem(item: SshSessionItem): SshRecentSession {
  return {
    hostId: item.hostId,
    title: item.title,
    host: item.host,
    username: item.username,
    port: item.port,
    lastAt: item.lastAt,
    sessionId: item.sessionId,
    hasRecording: item.hasRecording,
  }
}

export function loadRecentSessions(): SshRecentSession[] {
  return readJson(RECENT_KEY, [])
}

export async function loadRecentSessionsAsync(): Promise<SshRecentSession[]> {
  try {
    const list = await fetchSshRecent()
    const mapped = list.map(mapServerItem)
    writeJson(RECENT_KEY, mapped.slice(0, MAX_RECENT))
    return mapped
  } catch {
    return loadRecentSessions()
  }
}

export function pushRecentSession(item: Omit<SshRecentSession, 'lastAt'>) {
  const list = loadRecentSessions().filter((x) => x.hostId !== item.hostId)
  list.unshift({ ...item, lastAt: new Date().toISOString() })
  writeJson(RECENT_KEY, list.slice(0, MAX_RECENT))
}

export function loadSessionHistory(): SshRecentSession[] {
  return readJson(HISTORY_KEY, [])
}

export async function loadSessionHistoryAsync(): Promise<SshRecentSession[]> {
  try {
    const list = await fetchSshHistory()
    const mapped = list.map(mapServerItem)
    writeJson(HISTORY_KEY, mapped.slice(0, MAX_HISTORY))
    return mapped
  } catch {
    return loadSessionHistory()
  }
}

export function pushSessionHistory(item: Omit<SshRecentSession, 'lastAt'>) {
  const list = loadSessionHistory()
  list.unshift({ ...item, lastAt: new Date().toISOString() })
  writeJson(HISTORY_KEY, list.slice(0, MAX_HISTORY))
}

export async function syncOpenSession(item: {
  hostId: number
  title: string
  host: string
  username: string
  port: number
}) {
  pushRecentSession(item)
  pushSessionHistory(item)
  try {
    await registerSshSession(item)
  } catch {
    /* local fallback already written */
  }
}

export function loadCmdHistory(): string[] {
  const list = readJson<string[]>(CMD_HISTORY_KEY, [])
  const cleaned = list.map((x) => String(x || '').trim()).filter(isUsableShellCmd)
  // 去掉历史里已污染的无效项
  if (cleaned.length !== list.length) {
    writeJson(CMD_HISTORY_KEY, cleaned.slice(0, MAX_CMD))
  }
  return cleaned
}

/** 可再次执行的 shell 命令；过滤 CSI/鼠标/DA/方向键残留等垃圾 */
export function isUsableShellCmd(cmd: string): boolean {
  const text = cmd.replace(/\r?\n$/, '').trim()
  if (!text) return false
  if (text.length > 2000) return false
  if (/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/.test(text)) return false
  // CSI / DA（带 [）
  if (/^\[[?>!=]?[\d;]*[A-Za-z~@`]/.test(text)) return false
  if (/^\[</.test(text) || /^\[M/.test(text)) return false
  // DA 丢 ESC/[：>0;276;0c
  if (/^>[0-9;]+[A-Za-z]/.test(text)) return false
  // 鼠标报告（有无 [）
  if (/\[?<\d+;\d+;\d+[Mm]/.test(text)) return false
  // bracketed paste
  if (text.includes('200~') || text.includes('201~')) return false
  // SS3 方向键残留 OA/OB/OC/OD
  if (/^(?:O[A-D])+/.test(text)) return false
  // docker ps 输出误贴
  if (/^[0-9a-f]{12}\s+\S+/.test(text)) return false
  if (!/[A-Za-z0-9_./~$*-]/.test(text)) return false
  if (text.length <= 3 && /^\[[A-Za-z~]$/.test(text)) return false
  return true
}

export function pushCmdHistory(cmd: string) {
  const text = cmd.replace(/\r?\n$/, '').replace(/\t/g, '').trim()
  if (!isUsableShellCmd(text)) return
  const list = loadCmdHistory().filter((x) => x !== text)
  list.unshift(text)
  writeJson(CMD_HISTORY_KEY, list.slice(0, MAX_CMD))
}

export function loadCmdTemplates(): SshCmdTemplate[] {
  const stored = readJson<SshCmdTemplate[] | null>(TEMPLATES_KEY, null)
  if (!stored || !stored.length) {
    writeJson(TEMPLATES_KEY, DEFAULT_TEMPLATES)
    return [...DEFAULT_TEMPLATES]
  }
  return stored
}

export function addCmdTemplate(name: string, command: string): SshCmdTemplate[] {
  const list = loadCmdTemplates()
  list.unshift({
    id: `c${Date.now()}`,
    name,
    command: command.endsWith('\n') ? command : `${command}\n`,
  })
  writeJson(TEMPLATES_KEY, list)
  return list
}

/** 刷新后恢复布局与各窗格主机（配合远端 tmux 续会话） */
export interface SshWorkspacePane {
  id: string
  hostId: number | null
  title: string
}

export interface SshWorkspace {
  layout: SshLayoutMode
  activePaneId: string
  panes: SshWorkspacePane[]
  syncInput?: boolean
}

const WORKSPACE_KEY = 'maxadmin_ssh_workspace'

export function loadWorkspace(): SshWorkspace | null {
  return readJson<SshWorkspace | null>(WORKSPACE_KEY, null)
}

export function saveWorkspace(ws: SshWorkspace) {
  writeJson(WORKSPACE_KEY, ws)
}

export function clearWorkspace() {
  localStorage.removeItem(WORKSPACE_KEY)
}
