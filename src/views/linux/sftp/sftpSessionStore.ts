/** SFTP 工作区持久化：刷新后恢复主机与当前路径（不分屏） */

export interface SftpWorkspace {
  hostId: number | null
  path: string
  /** 各主机上次浏览路径，切换主机时可恢复 */
  pathByHost?: Record<string, string>
}

const WORKSPACE_KEY = 'maxadmin_sftp_workspace'

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

export function loadSftpWorkspace(): SftpWorkspace | null {
  return readJson<SftpWorkspace | null>(WORKSPACE_KEY, null)
}

export function saveSftpWorkspace(ws: SftpWorkspace) {
  writeJson(WORKSPACE_KEY, ws)
}

export function clearSftpWorkspace() {
  localStorage.removeItem(WORKSPACE_KEY)
}
