<template>
  <aside class="bi-left">
    <PanelBox title="年度经济增长点">
      <ChartPie3D />
    </PanelBox>
    <PanelBox title="专项资金用途">
      <ChartBar3D ref="barRef" />
    </PanelBox>
    <PanelBox title="各季度增长情况">
      <ChartQuarter3D ref="quarterRef" />
    </PanelBox>
  </aside>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import PanelBox from '../components/PanelBox.vue'
import ChartPie3D from '../charts/ChartPie3D.vue'
import ChartBar3D from '../charts/ChartBar3D.vue'
import ChartQuarter3D from '../charts/ChartQuarter3D.vue'

const barRef = ref(null)
const quarterRef = ref(null)

const onResize = () => {
  barRef.value?.resize?.()
  quarterRef.value?.resize?.()
}

onMounted(() => window.addEventListener('resize', onResize))
onBeforeUnmount(() => window.removeEventListener('resize', onResize))
</script>

<style scoped>
.bi-left {
  position: absolute;
  top: 100px;
  bottom: 72px;
  left: 14px;
  z-index: 35;
  width: min(22vw, 340px);
  display: flex;
  flex-direction: column;
  gap: 10px;
  pointer-events: none;
}

@media (max-width: 1200px) {
  .bi-left { width: 240px; }
}
@media (max-width: 900px) {
  .bi-left { display: none; }
}
</style>
