<template>
  <aside class="bi-right">
    <PanelBox title="各经济产业">
      <ChartIndustry3D />
    </PanelBox>
    <PanelBox title="各省经济收益">
      <ChartRevenue3D ref="revenueRef" />
    </PanelBox>
    <PanelBox title="用电情况">
      <ChartPower3D ref="powerRef" />
    </PanelBox>
  </aside>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import PanelBox from '../components/PanelBox.vue'
import ChartIndustry3D from '../charts/ChartIndustry3D.vue'
import ChartRevenue3D from '../charts/ChartRevenue3D.vue'
import ChartPower3D from '../charts/ChartPower3D.vue'

const revenueRef = ref(null)
const powerRef = ref(null)

const onResize = () => {
  revenueRef.value?.resize?.()
  powerRef.value?.resize?.()
}

onMounted(() => window.addEventListener('resize', onResize))
onBeforeUnmount(() => window.removeEventListener('resize', onResize))
</script>

<style scoped>
.bi-right {
  position: absolute;
  top: 100px;
  bottom: 72px;
  right: 14px;
  z-index: 35;
  width: min(22vw, 340px);
  display: flex;
  flex-direction: column;
  gap: 10px;
  pointer-events: none;
}

@media (max-width: 1200px) {
  .bi-right { width: 240px; }
}
@media (max-width: 900px) {
  .bi-right { display: none; }
}
</style>
