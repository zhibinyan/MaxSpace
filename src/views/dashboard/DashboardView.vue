<template>
  <div class="bi-screen">
    <div v-if="!sceneReady" class="bi-boot" aria-busy="true">
      <span class="bi-boot__spinner" />
      <span class="bi-boot__text">驾驶舱加载中…</span>
    </div>

    <template v-else>
      <div class="bi-center">
        <Main />
      </div>
      <BiTop />
      <BiLeft />
      <BiRight />
      <BiBottom v-model="activeMenu" />
    </template>
  </div>
</template>

<script setup lang="ts">
import { defineAsyncComponent, onActivated, onMounted, onUnmounted, ref } from 'vue'

const Main = defineAsyncComponent(() => import('./BI/main.vue'))
const BiTop = defineAsyncComponent(() => import('./BI/modules/BiTop.vue'))
const BiLeft = defineAsyncComponent(() => import('./BI/modules/BiLeft.vue'))
const BiRight = defineAsyncComponent(() => import('./BI/modules/BiRight.vue'))
const BiBottom = defineAsyncComponent(() => import('./BI/modules/BiBottom.vue'))

/** 与书页进入时长大致对齐，避免动画中初始化 WebGL */
const DEFER_HEAVY_MS = 100

const activeMenu = ref(0)
const sceneReady = ref(false)

let cancelled = false
let deferTimer = 0

function mountHeavyScene() {
  if (sceneReady.value || cancelled) return
  const reduced =
    typeof window !== 'undefined'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const delay = reduced ? 0 : DEFER_HEAVY_MS

  window.clearTimeout(deferTimer)
  deferTimer = window.setTimeout(() => {
    if (cancelled) return
    requestAnimationFrame(() => {
      if (cancelled) return
      sceneReady.value = true
    })
  }, delay)
}

onMounted(() => {
  cancelled = false
  mountHeavyScene()
})

onActivated(() => {
  cancelled = false
  mountHeavyScene()
})

onUnmounted(() => {
  cancelled = true
  window.clearTimeout(deferTimer)
})
</script>

<style scoped>
.bi-screen {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: #061428;
  color: #e8f7ff;
  font-family: 'DIN Alternate', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.bi-boot {
  position: absolute;
  inset: 0;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  background:
    radial-gradient(ellipse 80% 60% at 50% 45%, #0a2a4a 0%, transparent 55%),
    linear-gradient(180deg, #04101f 0%, #061428 40%, #030b18 100%);
}

.bi-boot__spinner {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid rgba(90, 210, 255, 0.22);
  border-top-color: rgba(90, 210, 255, 0.92);
  animation: bi-spin 0.75s linear infinite;
}

.bi-boot__text {
  font-size: 13px;
  letter-spacing: 0.06em;
  color: rgba(180, 230, 255, 0.72);
}

.bi-center {
  position: absolute;
  inset: 0;
  z-index: 1;
}

@keyframes bi-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>

<!-- 父级 .window-content 不在本组件内，scoped / :deep 都改不到；用 :has 限定仅本页 -->
<style>
.window-content:has(> .bi-screen) {
  padding: 0 !important;
}
</style>
