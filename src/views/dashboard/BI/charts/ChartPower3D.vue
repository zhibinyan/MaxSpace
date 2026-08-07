<template>
  <div ref="el" class="chart3d"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  categories: {
    type: Array,
    default: () => ['23Q1', '23Q2', '23Q3', '23Q4', '24Q1', '24Q2'],
  },
  series: {
    type: Array,
    default: () => [
      { name: '工业用电', data: [120, 132, 145, 160, 170, 188], color: '#0ea5e9' },
      { name: '居民用电', data: [80, 86, 90, 95, 102, 110], color: '#22d3ee' },
      { name: '其他', data: [40, 42, 48, 50, 55, 60], color: '#818cf8' },
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
    data: props.categories,
    axisTick: { show: false },
    axisLine: { lineStyle: { color: 'rgba(80,160,220,0.4)' } },
    axisLabel: { color: 'rgba(180,220,255,0.8)', fontSize: 10 },
  },
  yAxis: {
    type: 'value',
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: 'rgba(180,220,255,0.65)', fontSize: 10 },
    splitLine: { lineStyle: { color: 'rgba(40,100,160,0.22)' } },
  },
  series: props.series.map((s) => ({
    name: s.name,
    type: 'line',
    stack: 'power',
    smooth: true,
    symbol: 'none',
    data: s.data,
    lineStyle: { width: 1, color: s.color },
    areaStyle: {
      opacity: 0.55,
      color: s.color,
    },
    emphasis: { focus: 'series' },
  })),
})

onMounted(() => {
  chart = echarts.init(el.value)
  chart.setOption(option())
  requestAnimationFrame(() => chart?.resize())
})

watch(
  () => [props.categories, props.series],
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
