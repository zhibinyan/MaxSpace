<template>
  <div ref="el" class="chart3d"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  categories: {
    type: Array,
    default: () => ['一季度', '二季度', '三季度', '四季度'],
  },
  bars: {
    type: Array,
    default: () => [42, 58, 51, 67],
  },
  line: {
    type: Array,
    default: () => [28, 45, 38, 55],
  },
  line2: {
    type: Array,
    default: () => [18, 32, 26, 40],
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
    data: ['增长额', '类型2', '类型3'],
  },
  grid: {
    left: 36,
    right: 12,
    top: 28,
    bottom: 24,
  },
  xAxis: {
    type: 'category',
    data: props.categories,
    axisTick: { show: false },
    axisLine: { lineStyle: { color: 'rgba(80,160,220,0.4)' } },
    axisLabel: { color: 'rgba(180,220,255,0.8)', fontSize: 10 },
  },
  yAxis: {
    type: 'value',
    max: 80,
    splitNumber: 4,
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: 'rgba(180,220,255,0.65)', fontSize: 10 },
    splitLine: { lineStyle: { color: 'rgba(40,100,160,0.22)' } },
  },
  series: [
    {
      name: '增长额',
      type: 'bar',
      data: props.bars,
      barWidth: 14,
      itemStyle: {
        borderRadius: [3, 3, 0, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(125, 211, 252, 0.95)' },
          { offset: 0.45, color: 'rgba(14, 165, 233, 0.85)' },
          { offset: 1, color: 'rgba(12, 74, 110, 0.55)' },
        ]),
        shadowColor: 'rgba(56, 189, 248, 0.45)',
        shadowBlur: 8,
      },
    },
    {
      name: '类型2',
      type: 'line',
      data: props.line,
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: { width: 2, color: '#38bdf8' },
      itemStyle: { color: '#7dd3fc', borderColor: '#0ea5e9', borderWidth: 1 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(56, 189, 248, 0.25)' },
          { offset: 1, color: 'rgba(56, 189, 248, 0)' },
        ]),
      },
    },
    {
      name: '类型3',
      type: 'line',
      data: props.line2,
      smooth: true,
      symbol: 'circle',
      symbolSize: 5,
      lineStyle: { width: 2, color: '#67e8f9' },
      itemStyle: { color: '#a5f3fc' },
    },
  ],
})

onMounted(() => {
  chart = echarts.init(el.value)
  chart.setOption(option())
  requestAnimationFrame(() => chart?.resize())
})

watch(
  () => [props.categories, props.bars, props.line, props.line2],
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
