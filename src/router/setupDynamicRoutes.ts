import type { Router, RouteRecordRaw } from 'vue-router'
import type { MenuItem } from '@/api/menu'
import { buildAdminRoutes } from './dynamicRoutes'

const LAYOUT_ROUTE_NAME = 'AdminLayout'

let registered = false
const addedRouteNames: string[] = []

export function isDynamicRoutesRegistered() {
  return registered
}

function collectRouteNames(routes: RouteRecordRaw[]): string[] {
  const names: string[] = []
  for (const route of routes) {
    if (route.name) names.push(String(route.name))
    if (route.children?.length) names.push(...collectRouteNames(route.children))
  }
  return names
}

function clearDynamicRoutes(router: Router) {
  for (const name of addedRouteNames) {
    if (router.hasRoute(name)) {
      router.removeRoute(name)
    }
  }
  addedRouteNames.length = 0
  registered = false
}

/** 根据 menu tree 注册动态路由，不请求接口 */
export function registerRoutesFromTree(
  router: Router,
  menus: MenuItem[],
  force = false,
): boolean {
  if (registered && !force) return false

  if (force) {
    clearDynamicRoutes(router)
  }

  if (!menus.length) {
    console.warn('[router] menu tree is empty')
    return false
  }

  try {
    const routes = buildAdminRoutes(menus)

    for (const route of routes) {
      if (route.name && router.hasRoute(route.name)) {
        const existing = router.getRoutes().find((item) => item.name === route.name)
        if (existing?.meta?.fallback) {
          continue
        }
        router.removeRoute(route.name)
      }
      router.addRoute(LAYOUT_ROUTE_NAME, route)
    }

    addedRouteNames.push(...collectRouteNames(routes))
    registered = true
    return true
  } catch (error) {
    console.error('[router] failed to register dynamic routes', error)
    registered = false
    return false
  }
}

export function resetDynamicRoutes(router: Router) {
  clearDynamicRoutes(router)
}
