import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from '@/router'
import { initRouteTransition } from '@/utils/routeTransition'
import { registerRoutesFromTree } from '@/router/setupDynamicRoutes'
import { useMenuStore } from '@/stores/menu'
import { useUserStore } from '@/stores/user'
import '@/style.css'

async function bootstrap() {
  const app = createApp(App)
  const pinia = createPinia()

  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
  }

  app.use(pinia)

  const userStore = useUserStore()
  const menuStore = useMenuStore()

  if (userStore.isLoggedIn) {
    menuStore.hydrateFromCache()
    registerRoutesFromTree(router, menuStore.tree)
  }

  app.use(router)
  initRouteTransition(router)
  await router.isReady()
  app.use(ElementPlus)
  app.mount('#app')

  if (userStore.isLoggedIn) {
    void menuStore.refreshTree().then((menus) => {
      if (menus.length) {
        registerRoutesFromTree(router, menus, true)
      }
    })
  }
}

bootstrap()
