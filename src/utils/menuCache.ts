import type { MenuItem } from '@/api/menu'

const MENU_TREE_CACHE_KEY = 'maxadmin_menu_tree'

export function getMenuTreeCache(): MenuItem[] {
  try {
    const raw = localStorage.getItem(MENU_TREE_CACHE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as MenuItem[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export function setMenuTreeCache(menus: MenuItem[]) {
  localStorage.setItem(MENU_TREE_CACHE_KEY, JSON.stringify(menus))
}

export function clearMenuTreeCache() {
  localStorage.removeItem(MENU_TREE_CACHE_KEY)
}
