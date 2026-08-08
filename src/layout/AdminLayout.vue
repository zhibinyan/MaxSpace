<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useTabsStore } from '@/stores/tabs'
import { useWallpaperStore } from '@/stores/wallpaper'
import {
  Close,
} from '@element-plus/icons-vue'
import { useMenuStore } from '@/stores/menu'
import MacRouteView from '@/components/MacRouteView.vue'
import AppDock from '@/views/Dock/appDock.vue'
import { MaxSvg } from '@/components/maxSvg'
import logo from '@/assets/logo.svg'
import { LAYOUT_TOOLBAR_TELEPORT_ID } from '@/layout/layoutToolbar'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const tabsStore = useTabsStore()
const wallpaperStore = useWallpaperStore()
const menuStore = useMenuStore()

const FULLSCREEN_KEY = 'maxAdmin-fullscreen'

const now = ref(new Date())
const isFullscreen = ref(false)
const fullscreenEnabled = ref(localStorage.getItem(FULLSCREEN_KEY) !== 'false')
const macDesktopRef = ref<HTMLElement | null>(null)
const closingWindow = ref(false)
const routeTabsRef = ref<HTMLElement | null>(null)

/** 鼠标滚轮横向滚动标签栏 */
function onTabsWheel(e: WheelEvent) {
  const el = routeTabsRef.value
  if (!el) return
  const delta = Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX : e.deltaY
  if (!delta) return
  if (el.scrollWidth <= el.clientWidth) return
  e.preventDefault()
  el.scrollLeft += delta
}

function bindTabsWheel() {
  routeTabsRef.value?.addEventListener('wheel', onTabsWheel, { passive: false })
}

function unbindTabsWheel() {
  routeTabsRef.value?.removeEventListener('wheel', onTabsWheel)
}

const dockTrackRef = ref<HTMLElement | null>(null)

/** 鼠标滚轮横向滚动程序坞（需 passive:false 才能阻止页面纵向滚动） */
function onDockWheel(e: WheelEvent) {
  const el = dockTrackRef.value
  if (!el) return
  const delta = Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX : e.deltaY
  if (!delta) return
  if (el.scrollWidth <= el.clientWidth) return
  e.preventDefault()
  el.scrollLeft += delta
}

function bindDockWheel() {
  dockTrackRef.value?.addEventListener('wheel', onDockWheel, { passive: false })
}

function unbindDockWheel() {
  dockTrackRef.value?.removeEventListener('wheel', onDockWheel)
}

function onDockLauncherClick() {
  appDockOpen.value = !appDockOpen.value
}

function onDockLinkClick(e: MouseEvent, title: string, path: string) {
  showDockTooltip(e, title, path)
  appDockOpen.value = false
}

function isDockActive(path: string) {
  return route.path === path || route.path.startsWith(`${path}/`)
}

function handleBack() {
  router.back()
}

function handleForward() {
  router.forward()
}

function handleRefresh() {
  window.location.reload()
}

async function enterFullscreen() {
  try {
    if (!document.fullscreenElement) {
      await document.documentElement.requestFullscreen()
    }
    isFullscreen.value = true
  } catch {
    isFullscreen.value = !!document.fullscreenElement
  }
}

async function exitFullscreen() {
  try {
    if (document.fullscreenElement) {
      await document.exitFullscreen()
    }
  } catch {
    /* ignore */
  }
  isFullscreen.value = false
}

async function setFullscreen(enabled: boolean) {
  fullscreenEnabled.value = enabled
  localStorage.setItem(FULLSCREEN_KEY, String(enabled))
  if (enabled) {
    await enterFullscreen()
    if (!document.fullscreenElement) {
      document.addEventListener('click', restoreFullscreenOnInteraction, { once: true })
      document.addEventListener('keydown', restoreFullscreenOnInteraction, { once: true })
    }
  } else {
    await exitFullscreen()
  }
}

function handleFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement
}

function restoreFullscreenOnInteraction() {
  if (fullscreenEnabled.value && !document.fullscreenElement) {
    enterFullscreen()
  }
  document.removeEventListener('click', restoreFullscreenOnInteraction)
  document.removeEventListener('keydown', restoreFullscreenOnInteraction)
}

function toggleFullscreen() {
  setFullscreen(!isFullscreen.value)
}

const menus = computed(() => menuStore.getDockMenus())
const appDockOpen = ref(false)

type DockTooltipState = {
  title: string
  x: number
  y: number
}

const dockTooltip = ref<DockTooltipState | null>(null)
const hoveredDock = ref<{ path: string; title: string } | null>(null)

function updateDockTooltipPosition(target: HTMLElement, title: string) {
  const itemRect = target.getBoundingClientRect()
  const icon = target.querySelector('.dock-icon') as HTMLElement | null
  dockTooltip.value = {
    title,
    x: icon
      ? itemRect.left + icon.offsetLeft + icon.offsetWidth / 2
      : itemRect.left + itemRect.width / 2,
    y: icon ? itemRect.top + icon.offsetTop : itemRect.top,
  }
}

function showDockTooltip(event: Event, title: string, path: string) {
  const target = event.currentTarget as HTMLElement | null
  if (!target) return
  hoveredDock.value = { path, title }
  updateDockTooltipPosition(target, title)
}

function hideDockTooltip() {
  dockTooltip.value = null
  hoveredDock.value = null
}

function refreshDockTooltip() {
  if (!hoveredDock.value) return
  const { path, title } = hoveredDock.value
  const target = document.querySelector(
    `.dock-item[data-dock-path="${path}"]`,
  ) as HTMLElement | null
  if (!target) return
  updateDockTooltipPosition(target, title)
}

watch(() => route.path, () => {
  tabsStore.addTab(route)
  requestAnimationFrame(refreshDockTooltip)
}, { immediate: true })

const timeText = computed(() =>
  now.value.toLocaleTimeString('zh-CN', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }),
)

let timer: ReturnType<typeof setInterval> | undefined

onMounted(() => {
  timer = setInterval(() => {
    now.value = new Date()
  }, 30000)

  document.addEventListener('fullscreenchange', handleFullscreenChange)
  isFullscreen.value = !!document.fullscreenElement
  bindTabsWheel()
  bindDockWheel()

  if (fullscreenEnabled.value && !document.fullscreenElement) {
    enterFullscreen().then(() => {
      if (!document.fullscreenElement) {
        document.addEventListener('click', restoreFullscreenOnInteraction, { once: true })
        document.addEventListener('keydown', restoreFullscreenOnInteraction, { once: true })
      }
    })
  }
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
  document.removeEventListener('click', restoreFullscreenOnInteraction)
  document.removeEventListener('keydown', restoreFullscreenOnInteraction)
  unbindTabsWheel()
  unbindDockWheel()
})

function navigateTab(path: string) {
  if (route.path !== path) {
    router.push(path)
  }
}

function closeTab(path: string) {
  const index = tabsStore.removeTab(path)
  if (index === -1) return

  if (route.path === path) {
    const nextTab = tabsStore.visitedTabs[index] ?? tabsStore.visitedTabs[index - 1]
    router.push(nextTab?.path ?? '/dashboard')
  }
}

function commitLogout() {
  tabsStore.clearTabs()
  userStore.logout()
  router.push('/login')
}

function closeCurrentTab() {
  closeTab(route.path)
}

function prefersReducedMotion(): boolean {
  return typeof window !== 'undefined'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

function easeInSoft(t: number): number {
  return t ** 2.6
}

/** 退出登录：整页向下滑出；底层固定壁纸填补露出的区域 */
function animateMacDesktopSlideDown(el: HTMLElement): Promise<void> {
  if (prefersReducedMotion()) return Promise.resolve()

  const duration = 760
  const distance = window.innerHeight + 32

  return new Promise((resolve) => {
    el.style.willChange = 'transform'
    el.style.pointerEvents = 'none'

    const start = performance.now()

    const tick = (now: number) => {
      const linear = Math.min(1, (now - start) / duration)
      const eased = easeInSoft(linear)
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

async function handleLogout() {
  if (closingWindow.value) return
  closingWindow.value = true

  try {
    if (macDesktopRef.value) {
      await animateMacDesktopSlideDown(macDesktopRef.value)
    }
    commitLogout()
  } finally {
    closingWindow.value = false
  }
}
</script>

<template>
  <div class="mac-shell">
    <div
      class="wallpaper-backdrop"
      :style="wallpaperStore.wallpaperStyle"
      aria-hidden="true"
    />

    <div ref="macDesktopRef" class="mac-desktop">
    <div class="wallpaper" :style="wallpaperStore.wallpaperStyle" />

    <header class="menu-bar">
      <div class="menu-left">
        <img :src="logo" class="apple-mark" alt="" />
        <span class="menu-app">Max Space</span>
        <nav class="menu-items">
          <span>系统</span>
          <span>个人资料</span>
          <span>帮助</span>
          <span @click="toggleFullscreen">全屏</span>

        </nav>
      </div>
      <div class="menu-center">
        <div ref="routeTabsRef" class="route-tabs">
          <button
            v-for="tab in tabsStore.visitedTabs"
            :key="tab.path"
            type="button"
            class="user-chip route-tab"
            :class="{ active: route.path === tab.path }"
            @click="navigateTab(tab.path)"
          >
            <span class="user-avatar">{{ tab.title[0] }}</span>
            <span class="route-tab-title">{{ tab.title }}</span>
            <el-icon class="close-tab-icon" @click.stop="closeTab(tab.path)"><Close /></el-icon>
          </button>
        </div>
      </div>
      <div class="menu-right">
        <button class="user-chip" >
          <span class="user-avatar">{{ userStore.username[0]?.toUpperCase() }}</span>
          <span>{{ userStore.username }}</span>
         
        </button>
        <span class="menu-clock">{{ timeText }}</span>
        <button
          type="button"
          class="logout-btn"
          title="退出登录"
          aria-label="退出登录"
          :disabled="closingWindow"
          @click.stop="handleLogout"
        >
          <MaxSvg
            name="loginout"
            :opacity="0.92"
            size="md"
            class="logout-icon"
            alt=""
          />
        </button>
      </div>
    </header>

    <main class="desktop-area">
      <div class="mac-window">
      <!-- v-if="isFullscreen" -->
        <div  class="window-titlebar">
          <div class="traffic-lights">
            <button type="button" class="light red" title="关闭" @click="closeCurrentTab">
              <svg class="light-icon" viewBox="0 0 8 8" aria-hidden="true">
                <path d="M2 2l4 4M6 2L2 6" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" />
              </svg>
            </button>
            <button type="button" class="light yellow" title="最小化">
              <svg class="light-icon" viewBox="0 0 8 8" aria-hidden="true">
                <path d="M1.5 4h5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" />
              </svg>
            </button>
            <button type="button" class="light green" title="全屏" @click="toggleFullscreen">
              <svg class="light-icon" viewBox="0 0 8 8" aria-hidden="true">
                <path
                  d="M5.5 1.5H6.5V2.5M2.5 6.5H1.5V5.5"
                  stroke="currentColor"
                  stroke-width="1.1"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  fill="none"
                />
                <path d="M1.5 6.5L6.5 1.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" />
              </svg>
            </button>
          </div>
          <div class="browser-toolbar">
            <div class="nav-buttons">
              <button type="button" class="nav-btn" title="后退" @click="handleBack">
                <svg viewBox="0 0 16 16" aria-hidden="true">
                  <path d="M10 3L5 8l5 5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </button>
              <button type="button" class="nav-btn" title="前进" @click="handleForward">
                <svg viewBox="0 0 16 16" aria-hidden="true">
                  <path d="M6 3l5 5-5 5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </button>
              <button type="button" class="nav-btn" title="刷新" @click="handleRefresh">
                <svg viewBox="0 0 16 16" aria-hidden="true">
                  <path d="M13 3v4H9M3 13V9h4" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                  <path d="M3.5 6.5A5 5 0 0 1 12 4.5M12.5 9.5A5 5 0 0 1 4 11.5" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
                </svg>
              </button>
            </div>
            <div
              :id="LAYOUT_TOOLBAR_TELEPORT_ID"
              class="address-toolbar-slot"
            />
          </div>
        </div>
        <MacRouteView mode="book" />
      </div>
    </main>
    </div>

    <footer class="dock" :class="{ 'dock--above-launchpad': appDockOpen }">
      <div class="dock-panel">
        <nav class="dock-scroll" aria-label="程序坞">
          <div ref="dockTrackRef" class="dock-track">
            <button
              type="button"
              class="dock-item dock-item--launcher"
              data-dock-path="__launcher__"
              aria-label="程序坞"
              @click="onDockLauncherClick"
              @mouseenter="showDockTooltip($event, '程序坞', '__launcher__')"
              @mouseleave="hideDockTooltip"
            >
              <span class="dock-icon-large">
                <MaxSvg name="menu" :size="42" />
              </span>
              <span class="dock-dot" aria-hidden="true" />
            </button>
            <router-link
              v-for="item in menus"
              :key="item.path"
              :to="item.path"
              :data-dock-path="item.path"
              class="dock-item"
              :class="{ active: isDockActive(item.path) }"
              @mouseenter="showDockTooltip($event, item.title, item.path)"
              @mouseleave="hideDockTooltip"
              @click="onDockLinkClick($event, item.title, item.path)"
            >
              <span class="dock-icon-large" >
                <MaxSvg :name="item.icon" :size="42" />
              </span>
              <span class="dock-dot" :class="{ visible: isDockActive(item.path) }" />
            </router-link>
          </div>
        </nav>
      </div>
    </footer>

    <Teleport to="body">
      <div
        v-if="dockTooltip"
        class="dock-tooltip-floating"
        :class="{ 'dock-tooltip-floating--above-launchpad': appDockOpen }"
        :style="{
          left: `${dockTooltip.x}px`,
          top: `${dockTooltip.y}px`,
        }"
      >
        {{ dockTooltip.title }}
      </div>
    </Teleport>

    <AppDock v-model:open="appDockOpen" />
  </div>
</template>

<style scoped>
.mac-shell {
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

.mac-desktop {
  position: relative;
  z-index: 1;
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.wallpaper {
  position: fixed;
  inset: 0;
  z-index: 0;
  transition: background 0.45s ease;
}

.menu-bar {
  position: relative;
  z-index: 20;
  height: 32px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 14px 0 18px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.92);
}

.menu-left,
.menu-center,
.menu-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.menu-center {
  flex: 1;
  justify-content: center;
  min-width: 0;
  padding: 0 8px;
}

.route-tabs {
  display: flex;
  align-items: center;
  gap: 6px;
  max-width: 100%;
  overflow-x: auto;
  scrollbar-width: none;
}

.route-tabs::-webkit-scrollbar {
  display: none;
}

.route-tab.active {
  background: rgba(255, 255, 255, 0.24);
}

.route-tab-title {
  max-width: 96px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  margin-right: 4px;
}

.menu-items {
  display: flex;
  gap: 16px;
  margin-left: 8px;
}

.menu-items span {
  cursor: default;
  opacity: 0.9;
}

.menu-items span:hover {
  opacity: 1;
}

.menu-icon {
  font-size: 14px;
  opacity: 0.85;
}

.fullscreen-switch {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  cursor: pointer;
  user-select: none;
}

.fullscreen-switch :deep(.el-switch) {
  --el-switch-on-color: #28c840;
  --el-switch-off-color: rgba(255, 255, 255, 0.25);
}

.menu-clock {
  font-size: 14px;
  opacity: 0.9;
  width: 148px;
  min-width: 148px;
  text-align: right;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
  font-feature-settings: 'tnum';
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 3px 9px 3px 5px;
  background: rgba(255, 255, 255, 0.12);
  border: none;
  border-radius: 7px;
  color: inherit;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s;
}

.user-chip:hover {
  background: rgba(255, 255, 255, 0.22);
}

.user-avatar {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
}

.logout-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  border: none;
  border-radius: 7px;
  background: transparent;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s ease;
}

.logout-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.16);
}

.logout-btn:active:not(:disabled) {
  background: rgba(255, 255, 255, 0.22);
}

.logout-btn:disabled {
  cursor: wait;
  opacity: 0.55;
}

.logout-icon {
  pointer-events: none;
  filter: brightness(0) invert(1);
}
.close-tab-icon {
  font-size: 13px;
  opacity: 0.7;
}
.desktop-area {
  position: relative;
  z-index: 1;
  flex: 1;
  display: flex;
  align-items: stretch;
  justify-content: center;
  padding: 16px 16px 92px;
  min-height: 0;
}

.mac-window {
  width: 100%;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(48px) saturate(190%);
  -webkit-backdrop-filter: blur(48px) saturate(190%);
  border-radius: 12px;
  box-shadow:
    0 0 0 0.5px rgba(255, 255, 255, 0.35),
    0 8px 40px rgba(0, 0, 0, 0.2),
    0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.window-titlebar {
  min-height: 44px;
  max-height: 44px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 7px 12px 7px 14px;
}

.traffic-lights {
  display: flex;
  gap: 8px;
}

.light {
  width: 12px;
  height: 12px;
  padding: 0;
  border-radius: 50%;
  border: 0.5px solid transparent;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: default;
  flex-shrink: 0;
}

.light-icon {
  width: 8px;
  height: 8px;
  opacity: 0;
  transition: opacity 0.12s ease;
}

.window-titlebar:hover .light-icon {
  opacity: 1;
}

.light.red {
  background: #ff5f57;
  border-color: #e0443e;
  color: #4d0000;
  cursor: pointer;
}

.light.yellow {
  background: #febc2e;
  border-color: #dea123;
  color: #995700;
}

.light.green {
  background: #28c840;
  border-color: #1aab29;
  color: #006500;
}

.browser-toolbar {
  flex: 1;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  min-width: 0;
  row-gap: 8px;
}

.nav-buttons {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}

.nav-btn {
  width: 28px;
  height: 28px;
  padding: 0;
  border: none;
  background: transparent;
  color: #a84848;
  border-radius: 6px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s, color 0.15s;
}

.nav-btn svg {
  width: 16px;
  height: 16px;
}

.nav-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #c25555;
}

.address-bar {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  height: 30px;
  padding: 0 14px;
  background: #f2f2f2;
  border-radius: 999px;
  min-width: 0;
  box-shadow: inset 0 0 0 0.5px rgba(0, 0, 0, 0.06);
}

.info-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  color: #888;
}

.address-text {
  flex: 1;
  display: flex;
  align-items: center;
  min-width: 0;
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
}

.address-host {
  flex-shrink: 0;
  color: #555;
}

.address-path-input {
  flex: 1;
  min-width: 0;
  border: none;
  outline: none;
  background: transparent;
  padding: 0;
  font: inherit;
  color: #999;
}

.address-toolbar-slot {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
}

.address-path-input:focus {
  color: #333;
}

.dock {
  position: fixed;
  bottom: 8px;
  left: 0;
  right: 0;
  z-index: 100;
  display: flex;
  justify-content: center;
  pointer-events: none;
  overflow: visible;
}

.dock--above-launchpad {
  z-index: 12001;
}

.dock-panel {
  position: relative;
  width: fit-content;
  min-width: 360px;
  max-width: 80%;
  max-height: 68px;
  height: 68px;
  padding-inline: 8px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 18px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
  pointer-events: auto;
  overflow: visible;
  box-sizing: border-box;
}

.dock-scroll {
  max-width: 100%;
  overflow: visible;
}

.dock-track {
  display: flex;
  height: 60px;
  flex-wrap: nowrap;
  align-items: flex-end;
  gap: 4px;
  max-width: 100%;
  overflow-x: auto;
  overflow-y: visible;
  overscroll-behavior-x: contain;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  padding-inline: 0px;
}

.dock-track::-webkit-scrollbar {
  display: none;
}

.dock-item {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 0 6px 0px;
  text-decoration: none;
  color: inherit;
  flex-shrink: 0;
  outline: none;
}

.dock-item--launcher {
  border: none;
  background: transparent;
  cursor: pointer;
  font: inherit;
}

.dock-item:hover,
.dock-item:focus-visible {
  z-index: 200;
}

.dock-item:hover .dock-icon,
.dock-item:focus-visible .dock-icon {
  transform: translateY(-6px) scale(1.06);
}
.dock-icon-large{
  width: 42px;
  height: 42px;
  border-radius: 14px;
}
.dock-item:hover .dock-icon-large,
.dock-item:focus-visible .dock-icon-large {
  transform: translateY(-6px) scale(1.06);
}

.dock-tooltip-floating {
  position: fixed;
  z-index: 9999;
  transform: translate(-50%, calc(-100% - 22px));
  padding: 5px 12px;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.2;
  color: #fff;
  white-space: nowrap;
  background: rgba(58, 38, 42, 0.94);
  border: 1px solid rgba(0, 0, 0, 0.55);
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
  pointer-events: none;
}

.dock-tooltip-floating--above-launchpad {
  z-index: 12002;
}

.dock-tooltip-floating::before {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: rgba(0, 0, 0, 0.55);
}

.dock-tooltip-floating::after {
  content: '';
  position: absolute;
  top: calc(100% - 1px);
  left: 50%;
  transform: translateX(-50%);
  border: 5px solid transparent;
  border-top-color: rgba(58, 38, 42, 0.94);
}

.dock-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow:
    0 0 0 2px transparent,
    0 2px 6px rgba(0, 0, 0, 0.18),
    inset 0 0 0 0.5px rgba(255, 255, 255, 0.15);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  transform-origin: center bottom;
  flex-shrink: 0;
}

.dock-item.active .dock-icon {
  box-shadow:
    0 0 0 2px rgba(255, 255, 255, 0.6),
    0 2px 6px rgba(0, 0, 0, 0.18),
    inset 0 0 0 0.5px rgba(255, 255, 255, 0.2);
}

.dock-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.85);
  opacity: 0;
  pointer-events: none;
}

.dock-dot.visible {
  opacity: 1;
}
</style>
