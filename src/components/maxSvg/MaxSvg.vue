<script setup lang="ts">
import { computed } from 'vue'
import { resolveSvgByName } from './svgMap'
import type { MaxSvgSize } from './types'

defineOptions({ inheritAttrs: false })

const props = withDefaults(
  defineProps<{
    /** 文件名（不含扩展名），对应 `@/assets/svg/{name}.svg` */
    name?: string
    /** 直接传入 SVG URL，优先级高于 `name` */
    src?: string
    size?: MaxSvgSize | number
    alt?: string
    opacity?: number
  }>(),
  {
    size: 'md',
    alt: '',
    opacity: 1,
  },
)

const sizeMap: Record<MaxSvgSize, number> = {
  sm: 12,
  md: 14,
  lg: 18,
  xl: 24,
}

const iconSrc = computed(() => {
  if (props.src) return props.src
  if (props.name) return resolveSvgByName(props.name)
  return undefined
})

const sizePx = computed(() =>
  typeof props.size === 'number' ? props.size : sizeMap[props.size],
)

const iconStyle = computed(() => ({
  width: `${sizePx.value}px`,
  height: `${sizePx.value}px`,
  opacity: props.opacity,
}))
</script>

<template>
  <img
    v-if="iconSrc"
    :src="iconSrc"
    class="max-svg"
    :style="iconStyle"
    :alt="alt"
    v-bind="$attrs"
  />
</template>

<style scoped>
.max-svg {
  display: block;
  flex-shrink: 0;
  object-fit: contain;
}
</style>
