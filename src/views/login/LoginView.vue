<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Message from '../../components/massage'
import { useUserStore } from '../../stores/user'
import { useMenuStore } from '../../stores/menu'
import { useWallpaperStore } from '../../stores/wallpaper'
import { registerRoutesFromTree } from '@/router/setupDynamicRoutes'
import { md5Hash } from '../../utils/md5'
import {
  animateLoginStepSwitch,
  applyLoginStepInitial,
} from '../../utils/loginStepTransition'
import logo from '@/assets/logo.svg'
const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const menuStore = useMenuStore()
const wallpaperStore = useWallpaperStore()

const loading = ref(false)
const showPassword = ref(false)
const loginStep = ref<'username' | 'password'>('username')
const stepSwitching = ref(false)
const passwordInputRef = ref<HTMLInputElement | null>(null)
const usernameInputRef = ref<HTMLInputElement | null>(null)
const usernameStepRef = ref<HTMLElement | null>(null)
const passwordStepRef = ref<HTMLElement | null>(null)
const loginPageRef = ref<HTMLElement | null>(null)
const now = ref(new Date())

const form = reactive({
  username: '',
  password: '',
})

const displayName = computed(() => form.username.trim() || '用户')

const timeText = computed(() =>
  now.value.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false }),
)

const dateText = computed(() =>
  now.value.toLocaleDateString('zh-CN', { weekday: 'long', month: 'long', day: 'numeric' }),
)

let timer: ReturnType<typeof setInterval> | undefined

onMounted(() => {
  timer = setInterval(() => {
    now.value = new Date()
  }, 1000)
  nextTick(() => {
    if (usernameStepRef.value && passwordStepRef.value) {
      applyLoginStepInitial(usernameStepRef.value, true)
      applyLoginStepInitial(passwordStepRef.value, false)
    }
    usernameInputRef.value?.focus()
  })
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

function focusInput(input: HTMLInputElement | null | undefined) {
  requestAnimationFrame(() => {
    input?.focus({ preventScroll: true })
  })
}

async function switchLoginStep(next: 'username' | 'password') {
  if (stepSwitching.value || loginStep.value === next) return

  const fromEl = loginStep.value === 'username' ? usernameStepRef.value : passwordStepRef.value
  const toEl = next === 'username' ? usernameStepRef.value : passwordStepRef.value
  if (!fromEl || !toEl) return

  stepSwitching.value = true
  const direction = next === 'password' ? 'forward' : 'back'

  if (next === 'password') {
    form.password = ''
  } else {
    form.password = ''
    showPassword.value = false
  }

  try {
    await animateLoginStepSwitch(fromEl, toEl, direction)
    loginStep.value = next
    focusInput(next === 'password' ? passwordInputRef.value : usernameInputRef.value)
  } finally {
    stepSwitching.value = false
  }
}

function goToPasswordStep() {
  if (!form.username.trim()) return
  void switchLoginStep('password')
}

function backToUsername() {
  void switchLoginStep('username')
}

async function handleLogin() {
  if (!form.password) {
    Message.warning({
      title: displayName.value,
      message: '请输入密码',
      position: 'top-center',
    })
    return
  }

  loading.value = true
  try {
    const ok = await userStore.login(form.username.trim(), md5Hash(form.password))
    if (ok) {
      const redirect = (route.query.redirect as string) || '/dashboard'
      await menuStore.refreshTree()
      registerRoutesFromTree(router, menuStore.tree, true)
      if (loginPageRef.value) {
        await animateLoginPageSlideUp(loginPageRef.value)
      }
      router.push(redirect)
    } else {
      form.password = ''
      nextTick(() => focusInput(passwordInputRef.value))
    }
  } finally {
    loading.value = false
  }
}

function onUsernameKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    e.preventDefault()
    goToPasswordStep()
  }
}

function onPasswordKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    e.preventDefault()
    if (!loading.value) handleLogin()
  } else if (e.key === 'Escape') {
    backToUsername()
  }
}

function togglePassword() {
  showPassword.value = !showPassword.value
}

function prefersReducedMotion(): boolean {
  return typeof window !== 'undefined'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

function easeOutSoft(t: number): number {
  return 1 - (1 - t) ** 3.2
}

/** 登录成功：整页向上滑出；底层固定壁纸填补露出的区域 */
function animateLoginPageSlideUp(el: HTMLElement): Promise<void> {
  if (prefersReducedMotion()) return Promise.resolve()

  const duration = 760
  const distance = -(window.innerHeight + 32)

  return new Promise((resolve) => {
    el.style.willChange = 'transform'
    el.style.pointerEvents = 'none'

    const start = performance.now()

    const tick = (now: number) => {
      const linear = Math.min(1, (now - start) / duration)
      const eased = easeOutSoft(linear)
      el.style.transform = `translate3d(0, ${distance * eased}px, 0)`

      if (linear < 1) {
        requestAnimationFrame(tick)
      } else {
        resolve()
      }
    }

    requestAnimationFrame(tick)
  })
}
</script>

<template>
  <div class="login-shell">
    <div
      class="wallpaper-backdrop"
      :style="wallpaperStore.wallpaperStyle"
      aria-hidden="true"
    />

    <div ref="loginPageRef" class="login-page">
      <div class="wallpaper" :style="wallpaperStore.wallpaperStyle" />

      <div class="menu-bar">
        <div class="menu-left">
         <img :src="logo" class="apple-mark" alt="" />
          <span class="menu-app">Max Space</span>
        </div>
        <div class="menu-right">
          <span class="menu-clock">{{ timeText }}</span>
        </div>
      </div>

      <div class="lock-screen">
        <div class="lock-time">{{ timeText }}</div>
        <div class="lock-date">{{ dateText }}</div>
        <div class="user-avatar">{{ displayName[0]?.toUpperCase() }}</div>
        <div class="user-panel">
          <div class="login-step-stack">
            <div
              ref="usernameStepRef"
              class="login-step"
              :aria-hidden="loginStep !== 'username'"
            >
              <div class="field-shell">
                <input
                  ref="usernameInputRef"
                  v-model="form.username"
                  class="login-input"
                  type="text"
                  placeholder="输入账号"
                  autocomplete="username"
                  spellcheck="false"
                  :disabled="stepSwitching"
                  @keydown="onUsernameKeydown"
                />
              </div>
              <p class="field-hint">按回车继续</p>
            </div>

            <div
              ref="passwordStepRef"
              class="login-step"
              :aria-hidden="loginStep !== 'password'"
            >
              <div class="field-shell password-field">
                <input
                  ref="passwordInputRef"
                  v-model="form.password"
                  class="login-input"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="输入密码"
                  autocomplete="current-password"
                  :disabled="loading || stepSwitching"
                  @keydown="onPasswordKeydown"
                />
                <button type="button" class="toggle-btn" @click="togglePassword">
                  {{ showPassword ? '隐藏' : '显示' }}
                </button>
              </div>
              <p class="field-hint">
                {{ loading ? '登录中…' : '按回车登录 · Esc 返回' }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-shell {
  position: relative;
  min-height: 100vh;
}

.wallpaper-backdrop {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  transition: background 0.45s ease;
}

.login-page {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  overflow: hidden;
  color: #fff;
}

.wallpaper {
  position: fixed;
  inset: 0;
  z-index: 0;
  transition: background 0.45s ease;
}

.menu-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background: rgba(0, 0, 0, 0.25);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  font-size: 14px;
  font-weight: 500;
  z-index: 10;
}

.menu-left,
.menu-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.apple-mark {
  width: 22px;
  height: 22px;
  display: block;
  object-fit: contain;
  flex-shrink: 0;
}

.menu-app {
  font-weight: 600;
}

.menu-status {
  opacity: 0.85;
  font-size: 12px;
}

.lock-screen {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 24px 40px;
  text-align: center;
}

.lock-time {
  font-size: 96px;
  font-weight: 200;
  letter-spacing: -2px;
  line-height: 1;
  text-shadow: 0 2px 20px rgba(0, 0, 0, 0.3);
}

.lock-date {
  margin-top: 8px;
  font-size: 22px;
  font-weight: 400;
  opacity: 0.9;
  text-shadow: 0 1px 8px rgba(0, 0, 0, 0.25);
}

.user-panel {
  margin-top: 48px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.login-step-stack {
  position: relative;
  width: 260px;
  min-height: 88px;
}

.login-step {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  will-change: transform, opacity;
}

.user-avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 2px solid rgba(255, 255, 255, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: 500;
  text-transform: uppercase;
  margin-top: 38px;
}

.user-name {
  font-size: 18px;
  font-weight: 500;
}

.field-shell {
  width: 260px;
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.login-input {
  flex: 1;
  width: 100%;
  padding: 11px 14px;
  background: transparent;
  border: none;
  outline: none;
  color: #fff;
  font-size: 15px;
  text-align: center;
}

.login-input::placeholder {
  color: rgba(255, 255, 255, 0.55);
}

.login-input:disabled {
  opacity: 0.7;
}

.password-field .login-input {
  text-align: left;
}

.toggle-btn {
  padding: 0 12px;
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
  cursor: pointer;
  flex-shrink: 0;
}

.toggle-btn:hover {
  color: #fff;
}

.field-hint {
  margin: 0;
  font-size: 12px;
  opacity: 0.55;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}
</style>
