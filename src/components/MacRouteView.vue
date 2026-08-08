<script setup lang="ts">
import { computed } from 'vue'
import type { Component } from 'vue'
import type { RouteLocationNormalizedLoaded } from 'vue-router'
import {
  createRouteTransitionHooks,
  getKeepAliveKey,
  getLiveRouteKey,
  shouldKeepAlive,
  type RouteTransitionMode,
} from '../utils/routeTransition'

const props = withDefaults(
  defineProps<{
    /** book：macOS 书页翻转；none：无动画 */
    mode?: RouteTransitionMode
    emptyText?: string
  }>(),
  {
    mode: 'book',
    emptyText: '页面不存在或组件加载失败',
  },
)

const transitionHooks = computed(() => createRouteTransitionHooks(props.mode))
const isAnimated = computed(() => props.mode === 'book')

function resolveAlive(
  Component: Component | null | undefined,
  route: RouteLocationNormalizedLoaded,
) {
  return Component && shouldKeepAlive(route) ? Component : null
}

function resolveLive(
  Component: Component | null | undefined,
  route: RouteLocationNormalizedLoaded,
) {
  return Component && !shouldKeepAlive(route) ? Component : null
}
</script>

<template>
  <div class="mac-route-stage">
    <router-view v-slot="{ Component, route: viewRoute }">
      <div class="mac-route-stack">
        <!--
          稳定 viewport：多根页面也有高度。
          KeepAlive 始终存在，只接收 meta.keepAlive 页面（外包单根 div）。
          非 keepAlive 走独立分支并按 fullPath 重挂载，保证 onMounted 重新请求。
        -->
        <div class="mac-route-viewport window-content">
          <template
            v-for="alive in [resolveAlive(Component, viewRoute)]"
            :key="'mac-alive'"
          >
            <Transition
              v-if="isAnimated"
              mode="out-in"
              :css="false"
              v-bind="transitionHooks"
            >
              <KeepAlive :max="12">
                <div
                  v-if="alive"
                  :key="getKeepAliveKey(viewRoute)"
                  class="mac-route-page"
                >
                  <component :is="alive" />
                </div>
              </KeepAlive>
            </Transition>
            <KeepAlive v-else :max="12">
              <div
                v-if="alive"
                :key="getKeepAliveKey(viewRoute)"
                class="mac-route-page"
              >
                <component :is="alive" />
              </div>
            </KeepAlive>
          </template>

          <template
            v-for="live in [resolveLive(Component, viewRoute)]"
            :key="'mac-live'"
          >
            <Transition
              v-if="isAnimated"
              mode="out-in"
              :css="false"
              v-bind="transitionHooks"
            >
              <div
                v-if="live"
                :key="getLiveRouteKey(viewRoute)"
                class="mac-route-page"
              >
                <component :is="live" />
              </div>
              <div
                v-else-if="!Component"
                key="mac-route-empty"
                class="mac-route-page mac-route-empty"
              >
                {{ emptyText }}
              </div>
            </Transition>
            <template v-else>
              <div
                v-if="live"
                :key="getLiveRouteKey(viewRoute)"
                class="mac-route-page"
              >
                <component :is="live" />
              </div>
              <div
                v-else-if="!Component"
                class="mac-route-page mac-route-empty"
              >
                {{ emptyText }}
              </div>
            </template>
          </template>
        </div>
      </div>
    </router-view>
  </div>
</template>

<style scoped>
.mac-route-stage {
  flex: 1;
  min-height: 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  perspective: 1500px;
  perspective-origin: 50% 92%;
  transform-style: preserve-3d;
}

.mac-route-stack {
  position: relative;
  display: grid;
  grid-template-columns: 1fr;
  flex: 1;
  min-height: 0;
  min-width: 0;
  width: 100%;
  overflow: hidden;
  transform-style: preserve-3d;
}

.mac-route-viewport {
  grid-area: 1 / 1;
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 0;
  min-width: 0;
  backface-visibility: hidden;
  transform-style: preserve-3d;
}

.window-content {
  flex: 1;
  min-height: 0;
  min-width: 0;
  height: 100%;
  overflow: hidden;
  padding: 10px;
  background: rgba(255, 255, 255, 0.06);
  border-top: 1px solid rgba(255, 255, 255, 0.22);
}

/*
  Transition / KeepAlive 是抽象组件，页面根会直接挂到 viewport 下。
  绝对定位叠层，避免切换瞬间双页把 flex 高度撑裂。
*/
.mac-route-page {
  position: absolute;
  inset: 0;
  min-height: 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
  backface-visibility: hidden;
}

.mac-route-empty {
  padding: 48px 24px;
  text-align: center;
  color: rgba(255, 255, 255, 0.65);
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.window-content :deep(.el-card) {
  background: rgba(255, 255, 255, 0.32);
  backdrop-filter: blur(24px) saturate(160%);
  -webkit-backdrop-filter: blur(24px) saturate(160%);
  border: 1px solid rgba(255, 255, 255, 0.38);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.window-content :deep(.el-card__header) {
  background: rgba(255, 255, 255, 0.12);
  border-bottom: 1px solid rgba(255, 255, 255, 0.22);
}
</style>
