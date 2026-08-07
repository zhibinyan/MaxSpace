import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi } from '../api/auth'
import { fetchCurrentAdmin } from '../api/menu'
import router from '../router'
import { resetDynamicRoutes } from '../router/setupDynamicRoutes'
import { clearMenuTreeCache } from '../utils/menuCache'
import { useMenuStore } from './menu'

const TOKEN_KEY = 'maxadmin_token'
const USERNAME_KEY = 'maxadmin_username'
const IS_SUPER_KEY = 'maxadmin_is_super'

export const useUserStore = defineStore('user', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const username = ref(localStorage.getItem(USERNAME_KEY) || '管理员')
  const isSuper = ref(localStorage.getItem(IS_SUPER_KEY) === 'true')

  const isLoggedIn = computed(() => !!token.value)

  function setSession(result: { token: string; username: string; isSuper?: boolean }) {
    token.value = result.token
    username.value = result.username
    isSuper.value = !!result.isSuper
    localStorage.setItem(TOKEN_KEY, result.token)
    localStorage.setItem(USERNAME_KEY, result.username)
    localStorage.setItem(IS_SUPER_KEY, String(!!result.isSuper))
  }

  async function login(user: string, passwordMd5: string): Promise<boolean> {
    try {
      const result = await loginApi(user, passwordMd5)
      setSession(result)
      return true
    } catch {
      return false
    }
  }

  async function refreshProfile() {
    if (!token.value) return
    try {
      const profile = await fetchCurrentAdmin()
      username.value = profile.username
      isSuper.value = profile.isSuper
      localStorage.setItem(USERNAME_KEY, profile.username)
      localStorage.setItem(IS_SUPER_KEY, String(profile.isSuper))
    } catch {
      /* ignore */
    }
  }

  function logout() {
    token.value = null
    username.value = '管理员'
    isSuper.value = false
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USERNAME_KEY)
    localStorage.removeItem(IS_SUPER_KEY)
    clearMenuTreeCache()
    useMenuStore().reset()
    resetDynamicRoutes(router)
  }

  return { token, username, isSuper, isLoggedIn, login, logout, refreshProfile, setSession }
})
