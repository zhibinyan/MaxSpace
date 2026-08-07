<template>
  <div ref="el" class="chart3d"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  categories: {
    type: Array,
    default: () => ['就学就业', '扶贫攻坚', '防灾减灾', '环境工程'],
  },
  values: {
    type: Array,
    default: () => [62, 78, 54, 86],
  },
})

const el = ref(null)
let chart

const colors = [
  ['#0ea5e9', '#7dd3fc'],
  ['#06b6d4', '#67e8f9'],
  ['#3b82f6', '#93c5fd'],
  ['#10b981', '#6ee7b7'],
]

const option = () => {
  const cats = [...props.categories].reverse()
  const vals = [...props.values].reverse()

  return {
    grid: { left: 72, right: 42, top: 8, bottom: 4 },
    xAxis: {
      type: 'value',
      max: 100,
      show: false,
    },
    yAxis: {
      type: 'category',
      data: cats,
      axisTick: { show: false },
      axisLine: { show: false },
      axisLabel: {
        color: 'rgba(180, 220, 255, 0.85)',
        fontSize: 11,
      },
    },
    series: [
      // 底层轨道（立体凹槽）
      {
        type: 'bar',
        data: cats.map(() => 100),
        barWidth: 12,
        barGap: '-100%',
        silent: true,
        itemStyle: {
          borderRadius: 6,
          color: 'rgba(20, 60, 100, 0.55)',
          borderColor: 'rgba(70, 160, 220, 0.25)',
          borderWidth: 1,
          shadowColor: 'rgba(0, 0, 0, 0.35)',
          shadowBlur: 6,
          shadowOffsetY: 2,
        },
        z: 1,
      },
      // 进度条（立体渐变）
      {
        type: 'bar',
        data: vals.map((v, i) => ({
          value: v,
          itemStyle: {
            borderRadius: 6,
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: colors[i % colors.length][0] },
              { offset: 1, color: colors[i % colors.length][1] },
            ]),
            shadowColor: colors[i % colors.length][1],
            shadowBlur: 10,
            shadowOffsetY: 0,
          },
        })),
        barWidth: 12,
        label: {
          show: true,
          position: 'right',
          color: '#7ef0ff',
          fontSize: 11,
          formatter: '{c}%',
        },
        z: 2,
      },
      // 顶部高光，增强立体感
      {
        type: 'pictorialBar',
        data: vals,
        symbol: 'rect',
        symbolSize: [3, 10],
        symbolOffset: [2, 0],
        symbolPosition: 'end',
        z: 3,
        itemStyle: {
          color: 'rgba(255, 255, 255, 0.55)',
        },
        tooltip: { show: false },
      },
    ],
  }
}

const render = () => {
  if (!el.value) return
  chart = echarts.init(el.value)
  chart.setOption(option())
}

onMounted(() => {
  render()
  // 面板刚挂载时尺寸可能为 0，下一帧再 resize
  requestAnimationFrame(() => chart?.resize())
})

watch(
  () => [props.categories, props.values],
  () => chart?.setOption(option(), true),
  { deep: true },
)

onBeforeUnmount(() => chart?.dispose())

defineExpose({
  resize: () => chart?.resize(),
})
</script>

<style scoped>
.chart3d {
  width: 100%;
  height: 100%;
  min-height: 120px;
}
</style>
