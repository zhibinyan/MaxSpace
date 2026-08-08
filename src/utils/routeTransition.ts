import { ref } from 'vue'
import type { Router, RouteLocationNormalizedLoaded } from 'vue-router'

/** 内容区动画：book 淡入淡出 | none 无动画 */
export type RouteTransitionMode = 'book' | 'none'

export type RouteTransitionDirection = 'forward' | 'back'

/** 打开 / 进入：淡入 */
const ENTER_MS = 500
/** 关闭 / 离开：淡出 */
const LEAVE_MS = 100

export const routeTransitionDirection = ref<RouteTransitionDirection>('forward')

let pendingBackNavigation = false

/** 全局代数：新一次切换会使旧动画立即失效，避免频繁切换闪烁 */
let transitionEpoch = 0

if (typeof window !== 'undefined') {
  window.addEventListener('popstate', () => {
    pendingBackNavigation = true
  })
}

/** 在 router 安装后调用，用于判断翻页方向 */
export function initRouteTransition(router: Router): void {
  router.beforeEach(() => {
    transitionEpoch += 1
    routeTransitionDirection.value = pendingBackNavigation ? 'back' : 'forward'
    pendingBackNavigation = false
  })
}

function prefersReducedMotion(): boolean {
  return typeof window !== 'undefined'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

export function getKeepAliveKey(route: RouteLocationNormalizedLoaded): string {
  return String(route.name ?? route.fullPath)
}

export function getLiveRouteKey(route: RouteLocationNormalizedLoaded): string {
  return route.fullPath
}

export function shouldKeepAlive(route: RouteLocationNormalizedLoaded): boolean {
  return !!route.meta.keepAlive
}

type FadeCleanup = () => void

const fadeCleanups = new WeakMap<HTMLElement, FadeCleanup>()

function resetInlineStyles(el: HTMLElement): void {
  el.style.transition = ''
  el.style.opacity = ''
  el.style.zIndex = ''
  el.style.pointerEvents = ''
  el.style.willChange = ''
}

function cancelFade(el: HTMLElement): void {
  const cleanup = fadeCleanups.get(el)
  if (cleanup) {
    cleanup()
    fadeCleanups.delete(el)
  }
}

function runFade(
  el: HTMLElement,
  fromOpacity: number,
  toOpacity: number,
  durationMs: number,
  done: () => void,
): void {
  cancelFade(el)

  if (prefersReducedMotion()) {
    resetInlineStyles(el)
    done()
    return
  }

  const epoch = transitionEpoch
  let finished = false

  const finish = (callDone: boolean) => {
    if (finished) return
    finished = true
    el.removeEventListener('transitionend', onEnd)
    window.clearTimeout(fallbackTimer)
    fadeCleanups.delete(el)
    resetInlineStyles(el)
    if (callDone) done()
  }

  const onEnd = (event: TransitionEvent) => {
    if (event.target !== el || event.propertyName !== 'opacity') return
    // 已被更新的路由切换作废
    if (epoch !== transitionEpoch) {
      finish(false)
      done()
      return
    }
    finish(true)
  }

  el.style.pointerEvents = 'none'
  el.style.willChange = 'opacity'
  el.style.transition = 'none'
  el.style.opacity = String(fromOpacity)
  void el.offsetWidth

  el.addEventListener('transitionend', onEnd)
  el.style.transition = `opacity ${durationMs}ms ease-out`
  el.style.opacity = String(toOpacity)

  const fallbackTimer = window.setTimeout(() => {
    if (epoch !== transitionEpoch) {
      finish(false)
      done()
      return
    }
    finish(true)
  }, durationMs + 48)

  fadeCleanups.set(el, () => {
    finish(false)
  })
}

function bookEnter(el: HTMLElement, done: () => void): void {
  el.style.zIndex = '1'
  runFade(el, 0, 1, ENTER_MS, done)
}

function bookLeave(el: HTMLElement, done: () => void): void {
  el.style.zIndex = '2'
  runFade(el, 1, 0, LEAVE_MS, done)
}

function onCancelled(el: Element): void {
  cancelFade(el as HTMLElement)
  resetInlineStyles(el as HTMLElement)
}

/** 统一内容区过渡 hooks（MacRouteView 使用） */
export function createRouteTransitionHooks(mode: RouteTransitionMode = 'book') {
  const useBook = mode === 'book'

  return {
    onBeforeEnter(_el: Element) {},
    onEnter(el: Element, done: () => void) {
      if (useBook) {
        bookEnter(el as HTMLElement, done)
        return
      }
      done()
    },
    onAfterEnter(el: Element) {
      cancelFade(el as HTMLElement)
      resetInlineStyles(el as HTMLElement)
    },
    onEnterCancelled(el: Element) {
      onCancelled(el)
    },
    onBeforeLeave(_el: Element) {},
    onLeave(el: Element, done: () => void) {
      if (useBook) {
        bookLeave(el as HTMLElement, done)
        return
      }
      done()
    },
    onAfterLeave(el: Element) {
      cancelFade(el as HTMLElement)
      resetInlineStyles(el as HTMLElement)
    },
    onLeaveCancelled(el: Element) {
      onCancelled(el)
    },
  }
}
