import type { RouteRecordRaw } from 'vue-router'
import type { MenuItem } from '../api/menu'

const viewModules = import.meta.glob('../views/**/*.vue')

const viewLoaderMap = new Map<string, () => Promise<unknown>>()

for (const [key, loader] of Object.entries(viewModules)) {
  viewLoaderMap.set(key, loader)
  viewLoaderMap.set(key.replace(/^\.\.\//, ''), loader)
  const viewsIndex = key.indexOf('/views/')
  if (viewsIndex >= 0) {
    const suffix = key.slice(viewsIndex + 1)
    viewLoaderMap.set(suffix, loader)
    viewLoaderMap.set(`../${suffix}`, loader)
  }
}

function loadView(component?: string | null) {
  if (!component) return undefined

  const candidates = [
    component,
    component.replace(/^\.\.\//, ''),
    component.startsWith('../') ? component : `../${component}`,
  ]

  for (const key of candidates) {
    const loader = viewLoaderMap.get(key)
    if (loader) return loader
  }

  const fileName = component.split('/').pop()
  if (fileName) {
    for (const [key, loader] of viewLoaderMap.entries()) {
      if (key.endsWith(`/${fileName}`)) return loader
    }
  }

  console.warn(`Menu component not found: ${component}`, Object.keys(viewModules))
  return undefined
}

function buildRoute(menu: MenuItem): RouteRecordRaw {
  const component = loadView(menu.component)
  const route = {
    path: menu.path,
    name: menu.name ?? undefined,
    meta: {
      title: menu.title,
      icon: menu.icon,
      keepAlive: menu.keepAlive,
    },
    ...(menu.redirect ? { redirect: menu.redirect } : {}),
    ...(component ? { component } : {}),
    ...(menu.children?.length ? { children: menu.children.map(buildRoute) } : {}),
  } as RouteRecordRaw

  return route
}

export function buildAdminRoutes(menus: MenuItem[]): RouteRecordRaw[] {
  return menus.map(buildRoute)
}

export function getFullPath(menu: MenuItem, parentPath = ''): string {
  const current = `${parentPath}/${menu.path}`.replace(/\/+/g, '/')
  return current.startsWith('/') ? current : `/${current}`
}

export function flattenMenus(menus: MenuItem[], parentPath = ''): Array<MenuItem & { fullPath: string }> {
  const result: Array<MenuItem & { fullPath: string }> = []
  for (const menu of menus) {
    const fullPath = getFullPath(menu, parentPath)
    result.push({ ...menu, fullPath })
    if (menu.children?.length) {
      result.push(...flattenMenus(menu.children, fullPath))
    }
  }
  return result
}
