/** 登录页账号/密码步骤切换（独立，与 routeTransition 无关） */

const DURATION_MS = 240

function easeOutCubic(t: number): number {
  return 1 - (1 - t) ** 3
}

function setStepVisual(
  el: HTMLElement,
  opacity: number,
  translateY: number,
  interactive: boolean,
): void {
  el.style.opacity = String(opacity)
  el.style.transform = `translate3d(0, ${translateY}px, 0)`
  el.style.pointerEvents = interactive ? 'auto' : 'none'
}

/** 交叉淡入淡出，避免 out-in 空档卡顿 */
export function animateLoginStepSwitch(
  fromEl: HTMLElement,
  toEl: HTMLElement,
  direction: 'forward' | 'back',
): Promise<void> {
  const leaveY = direction === 'forward' ? -10 : 10
  const enterFromY = direction === 'forward' ? 10 : -10

  setStepVisual(fromEl, 1, 0, false)
  setStepVisual(toEl, 0, enterFromY, false)

  return new Promise((resolve) => {
    const start = performance.now()

    const tick = (now: number) => {
      const progress = Math.min(1, (now - start) / DURATION_MS)
      const eased = easeOutCubic(progress)

      setStepVisual(fromEl, 1 - eased, leaveY * eased, false)
      setStepVisual(toEl, eased, enterFromY * (1 - eased), false)

      if (progress < 1) {
        requestAnimationFrame(tick)
        return
      }

      setStepVisual(fromEl, 0, leaveY, false)
      setStepVisual(toEl, 1, 0, true)
      resolve()
    }

    requestAnimationFrame(tick)
  })
}

/** 初始化当前步骤显示 */
export function applyLoginStepInitial(el: HTMLElement, active: boolean): void {
  setStepVisual(el, active ? 1 : 0, active ? 0 : 10, active)
}
