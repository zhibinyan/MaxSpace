import { createRouter, createWebHashHistory } from 'vue-router'
import { useMenuStore } from '../stores/menu'
import { useUserStore } from '../stores/user'
import { isDynamicRoutesRegistered, registerRoutesFromTree } from './setupDynamicRoutes'

const router = createRouter({
  history: createWebHashHistory(), // createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/login/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      name: 'AdminLayout',
      component: () => import('../layout/AdminLayout.vue'),
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('../views/dashboard/DashboardView.vue'),
          meta: { title: '仪表盘', fallback: true, keepAlive: true },
        },
        {
          path: 'processEditorView/:id?',
          name: 'processEditor',
          component: () => import('../views/process/processEditorView.vue'),
          meta: { title: '流程编辑' },
        },
        {
          path: 'markdownEditorView/:id?',
          name: 'markdownEditor',
          component: () => import('../views/content/MarkdownEditorView.vue'),
          meta: { title: '备忘录编辑' },
        },
      ],
    }
  ],
})

router.beforeEach(async (to) => {
  const userStore = useUserStore()

  if (!to.meta.public && !userStore.isLoggedIn) {
    return { name: 'Login', query: { redirect: to.fullPath } }
  }

  if (to.name === 'Login' && userStore.isLoggedIn) {
    return { path: '/dashboard', replace: true }
  }

  if (!userStore.isLoggedIn) return

  if (!isDynamicRoutesRegistered()) {
    const menuStore = useMenuStore()
    menuStore.hydrateFromCache()
    registerRoutesFromTree(router, menuStore.tree)

    if (!menuStore.tree.length) {
      await menuStore.refreshTree()
      registerRoutesFromTree(router, menuStore.tree, true)
    }

    if (!isDynamicRoutesRegistered()) {
      if (to.path === '/dashboard' || to.path === '/') return
      return { path: '/dashboard', replace: true }
    }
    return { ...to, replace: true }
  }
})

export default router
