import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import type { RouteLocationNormalized } from 'vue-router'

export type VisitedTab = {
  path: string
  title: string
}

const TABS_KEY = 'maxadmin_visited_tabs'

function getRouteTitle(route: RouteLocationNormalized) {
  return String(route.meta?.title ?? route.name ?? route.path)
}

function loadTabs(): VisitedTab[] {
  try {
    const raw = localStorage.getItem(TABS_KEY)
    if (!raw) return []
    const list = JSON.parse(raw) as VisitedTab[]
    if (!Array.isArray(list)) return []
    return list
      .filter((t) => t && typeof t.path === 'string' && t.path && typeof t.title === 'string')
      .map((t) => ({ path: t.path, title: t.title || t.path }))
  } catch {
    return []
  }
}

function saveTabs(tabs: VisitedTab[]) {
  try {
    localStorage.setItem(TABS_KEY, JSON.stringify(tabs))
  } catch {
    /* ignore */
  }
}

export const useTabsStore = defineStore('tabs', () => {
  const visitedTabs = ref<VisitedTab[]>(loadTabs())

  watch(
    visitedTabs,
    (tabs) => {
      saveTabs(tabs)
    },
    { deep: true },
  )

  function addTab(route: RouteLocationNormalized) {
    if (route.meta?.public) return

    const path = route.path
    const existing = visitedTabs.value.find((tab) => tab.path === path)
    const title = getRouteTitle(route)

    if (existing) {
      existing.title = title
      return
    }

    visitedTabs.value.push({ path, title })
  }

  function removeTab(path: string) {
    const index = visitedTabs.value.findIndex((tab) => tab.path === path)
    if (index === -1) return -1
    visitedTabs.value.splice(index, 1)
    return index
  }

  function clearTabs() {
    visitedTabs.value = []
  }

  return { visitedTabs, addTab, removeTab, clearTabs }
})
