<script setup lang="ts">
import { computed } from 'vue'
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
</script>

<template>
  <div class="mac-route-stage">
    <router-view v-slot="{ Component, route: viewRoute }">
      <div class="mac-route-stack">
        <!--
          KeepAlive 必须稳定挂载：不能包在 :key=fullPath 的节点里，
          否则书页切换会拆掉缓存，keepAlive meta 形同虚设。
          官方模式：Transition > KeepAlive > keyed component。
        -->
        <template v-if="isAnimated">
          <Transition mode="out-in" :css="false" v-bind="transitionHooks">
            <KeepAlive :max="12">
              <component
                :is="Component"
                v-if="Component && shouldKeepAlive(viewRoute)"
                :key="getKeepAliveKey(viewRoute)"
                class="mac-route-viewport window-content"
              />
            </KeepAlive>
          </Transition>
          <Transition mode="out-in" :css="false" v-bind="transitionHooks">
            <component
              :is="Component"
              v-if="Component && !shouldKeepAlive(viewRoute)"
              :key="getLiveRouteKey(viewRoute)"
              class="mac-route-viewport window-content"
            />
            <div
              v-else-if="!Component"
              key="mac-route-empty"
              class="mac-route-viewport window-content mac-route-empty"
            >
              {{ emptyText }}
            </div>
          </Transition>
        </template>
        <template v-else>
          <div
            v-if="Component"
            class="mac-route-viewport window-content"
          >
            <KeepAlive :max="12">
              <component
                :is="Component"
                v-if="shouldKeepAlive(viewRoute)"
                :key="getKeepAliveKey(viewRoute)"
              />
            </KeepAlive>
            <component
              :is="Component"
              v-if="!shouldKeepAlive(viewRoute)"
              :key="getLiveRouteKey(viewRoute)"
            />
          </div>
          <div v-else class="mac-route-viewport window-content mac-route-empty">
            {{ emptyText }}
          </div>
        </template>
      </div>
    </router-view>
  </div>
</template>

<style scoped>
.mac-route-stage {
  flex: 1;
  min-height: 0;
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
  width: 100%;
  overflow: hidden;
  transform-style: preserve-3d;
}

.mac-route-viewport {
  grid-area: 1 / 1;
  width: 100%;
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  backface-visibility: hidden;
  transform-style: preserve-3d;
}

.window-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
  overflow: hidden;
  padding: 10px;
  background: rgba(255, 255, 255, 0.06);
  border-top: 1px solid rgba(255, 255, 255, 0.22);
}

.mac-route-empty {
  padding: 48px 24px;
  text-align: center;
  color: rgba(255, 255, 255, 0.65);
  font-size: 14px;
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
