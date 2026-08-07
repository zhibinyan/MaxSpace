import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchMenuTree, type MenuItem } from '@/api/menu'
import { flattenMenus } from '@/router/dynamicRoutes'
import { getMenuTreeCache, setMenuTreeCache } from '@/utils/menuCache'

export type DockMenuItem = {
  path: string
  title: string
  icon: string
}

export const useMenuStore = defineStore('menu', () => {
  const tree = ref<MenuItem[]>(getMenuTreeCache())

  let inflightRefresh: Promise<MenuItem[]> | null = null

  function hydrateFromCache() {
    tree.value = getMenuTreeCache()
    return tree.value
  }

  function applyTree(menus: MenuItem[]) {
    tree.value = menus
    setMenuTreeCache(menus)
    return menus
  }

  function reset() {
    tree.value = []
    inflightRefresh = null
  }

  /** 唯一 tree 接口入口，in-flight 去重避免重复请求 */
  async function refreshTree(force = false): Promise<MenuItem[]> {
    if (inflightRefresh) {
      if (!force) return inflightRefresh
      try {
        await inflightRefresh
      } catch {
        /* 强制刷新时忽略上一次失败 */
      }
    }

    const task = fetchMenuTree()
      .then((menus) => applyTree(menus))
      .finally(() => {
        inflightRefresh = null
      })

    inflightRefresh = task
    return task
  }

  function getDockMenus(): DockMenuItem[] {
    return flattenMenus(tree.value)
      .filter((menu) => menu.dock)
      .map((menu) => ({
        path: menu.fullPath,
        title: menu.title,
        icon: menu.icon,
      }))
  }

  return {
    tree,
    hydrateFromCache,
    refreshTree,
    reset,
    getDockMenus,
  }
})
