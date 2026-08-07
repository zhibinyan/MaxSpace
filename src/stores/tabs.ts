import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { RouteLocationNormalized } from 'vue-router'

export type VisitedTab = {
  path: string
  title: string
}

function getRouteTitle(route: RouteLocationNormalized) {
  return String(route.meta?.title ?? route.name ?? route.path)
}

export const useTabsStore = defineStore('tabs', () => {
  const visitedTabs = ref<VisitedTab[]>([])

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
