import 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    icon?: string
    public?: boolean
    /** 切换路由后保留组件状态 */
    keepAlive?: boolean
  }
}
