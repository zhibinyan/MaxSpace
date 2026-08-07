import type { MaxSelectOption } from '@/components/maxSelect'

/** 主机系统类型枚举（存入 os_name） */
export const LINUX_OS_OPTIONS: MaxSelectOption[] = [
  { label: '请选择系统', value: '' },
  { label: 'Windows Server', value: 'Windows Server' },
  { label: 'Linux', value: 'Linux' },
  { label: 'Ubuntu', value: 'Ubuntu' },
  { label: 'CentOS', value: 'CentOS' },
  { label: 'Debian', value: 'Debian' },
  { label: 'Rocky', value: 'Rocky' },
  { label: 'AlmaLinux', value: 'AlmaLinux' },
  { label: '麒麟', value: '麒麟' },
  { label: 'UOS', value: 'UOS' },
  { label: 'openEuler', value: 'openEuler' },
]

export function isWindowsOs(osName?: string | null): boolean {
  const name = (osName || '').trim().toLowerCase()
  return name.includes('windows')
}

export function defaultUsernameForOs(osName?: string | null): string {
  return isWindowsOs(osName) ? 'Administrator' : 'root'
}

export function defaultSftpPathForOs(osName?: string | null): string {
  return isWindowsOs(osName) ? 'C:/' : '/'
}
