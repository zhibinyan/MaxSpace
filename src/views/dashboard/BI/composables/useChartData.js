
import { reactive } from 'vue';
import * as echarts from 'echarts';

export function useChartData() {
  // 饼图配置：运力分布
  const pieChartOption = reactive({
    tooltip: { trigger: 'item' },
    legend: { top: '5%', left: 'center', textStyle: { color: '#fff' } },
    series: [
      {
        name: '运力类型',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#0b1120',
          borderWidth: 2
        },
        label: { show: false, position: 'center' },
        emphasis: {
          label: { show: true, fontSize: 20, fontWeight: 'bold', color: '#fff' }
        },
        data: [
          { value: 1048, name: '集装箱船', itemStyle: { color: '#38bdf8' } },
          { value: 735, name: '散货船', itemStyle: { color: '#818cf8' } },
          { value: 580, name: '油轮', itemStyle: { color: '#c084fc' } },
          { value: 484, name: '液化气船', itemStyle: { color: '#f472b6' } }
        ]
      }
    ]
  });

  // 折线图配置：货运趋势
  const lineChartOption = reactive({
    tooltip: { trigger: 'axis' },
    grid: { top: 10, bottom: 20, left: 30, right: 10, containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
      axisLine: { lineStyle: { color: '#475569' } },
      axisLabel: { color: '#94a3b8' }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#1e293b' } },
      axisLabel: { color: '#94a3b8' }
    },
    series: [
      {
        name: '货运量',
        type: 'line',
        smooth: true,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(56, 189, 248, 0.5)' },
            { offset: 1, color: 'rgba(56, 189, 248, 0.0)' }
          ])
        },
        itemStyle: { color: '#38bdf8' },
        data: [120, 132, 101, 134, 90, 230, 210]
      }
    ]
  });

  // 柱状图配置：港口效率
  const barChartOption = reactive({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { top: 10, bottom: 20, left: 30, right: 10, containLabel: true },
    xAxis: {
      type: 'category',
      data: ['上海', '新加坡', '鹿特丹', '洛杉矶', '迪拜'],
      axisLine: { lineStyle: { color: '#475569' } },
      axisLabel: { color: '#94a3b8', interval: 0, fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#1e293b' } },
      axisLabel: { color: '#94a3b8' }
    },
    series: [
      {
        name: '作业效率',
        type: 'bar',
        barWidth: '40%',
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#4ade80' },
            { offset: 1, color: '#22c55e' }
          ])
        },
        data: [320, 302, 301, 334, 390]
      }
    ]
  });

  return {
    pieChartOption,
    lineChartOption,
    barChartOption
  };
}
