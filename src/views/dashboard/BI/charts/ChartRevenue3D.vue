<template>
  <div ref="el" class="chart3d"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  months: {
    type: Array,
    default: () => ['1月', '3月', '5月', '7月', '9月', '11月'],
  },
  series: {
    type: Array,
    default: () => [
      { name: '东部', data: [28, 52, 36, 68, 44, 72], color: '#38bdf8' },
      { name: '中部', data: [18, 34, 26, 48, 32, 55], color: '#22d3ee' },
      { name: '西部', data: [12, 22, 16, 30, 20, 38], color: '#67e8f9' },
    ],
  },
})

const el = ref(null)
let chart

const option = () => ({
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(6, 28, 52, 0.92)',
    borderColor: 'rgba(70, 190, 255, 0.45)',
    textStyle: { color: '#e8f7ff', fontSize: 11 },
  },
  legend: {
    top: 0,
    right: 4,
    itemWidth: 10,
    itemHeight: 6,
    textStyle: { color: 'rgba(180,220,255,0.8)', fontSize: 10 },
  },
  grid: {
    left: 36,
    right: 12,
    top: 28,
    bottom: 24,
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: props.months,
    axisTick: { show: false },
    axisLine: { lineStyle: { color: 'rgba(80,160,220,0.4)' } },
    axisLabel: { color: 'rgba(180,220,255,0.8)', fontSize: 10 },
  },
  yAxis: {
    type: 'value',
    splitNumber: 4,
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: 'rgba(180,220,255,0.65)', fontSize: 10 },
    splitLine: { lineStyle: { color: 'rgba(40,100,160,0.22)' } },
  },
  series: props.series.map((s, i) => ({
    name: s.name,
    type: 'line',
    // 尖峰折线，区别于季度图的平滑曲线
    smooth: false,
    symbol: 'none',
    data: s.data,
    lineStyle: {
      width: 2,
      color: s.color,
      shadowColor: s.color,
      shadowBlur: 6,
    },
    areaStyle: {
      color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: echarts.color.modifyAlpha(s.color, 0.45 - i * 0.08) },
        { offset: 1, color: echarts.color.modifyAlpha(s.color, 0.02) },
      ]),
    },
    emphasis: { focus: 'series' },
    z: props.series.length - i,
  })),
})

onMounted(() => {
  chart = echarts.init(el.value)
  chart.setOption(option())
  requestAnimationFrame(() => chart?.resize())
})

watch(
  () => [props.months, props.series],
  () => chart?.setOption(option(), true),
  { deep: true },
)

onBeforeUnmount(() => chart?.dispose())
defineExpose({ resize: () => chart?.resize() })
</script>

<style scoped>
.chart3d {
  width: 100%;
  height: 100%;
  min-height: 120px;
}
</style>
