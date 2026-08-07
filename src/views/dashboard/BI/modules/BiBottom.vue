<template>
  <nav class="bi-bottom">
    <button
      v-for="(item, i) in menus"
      :key="item"
      type="button"
      class="menu-btn"
      :class="{ active: model === i }"
      @click="model = i"
    >
      {{ item }}
    </button>
  </nav>
</template>

<script setup>
const model = defineModel({ type: Number, default: 0 })

defineProps({
  menus: {
    type: Array,
    default: () => ['综合概览', '菜单二', '菜单三', '菜单四'],
  },
})
</script>

<style scoped>
.bi-bottom {
  position: absolute;
  left: 50%;
  bottom: 14px;
  z-index: 40;
  display: flex;
  gap: 12px;
  transform: translateX(-50%);
  padding: 8px 12px;
  background: rgba(4, 22, 44, 0.55);
  border: 1px solid rgba(60, 160, 230, 0.35);
  backdrop-filter: blur(8px);
}

.menu-btn {
  min-width: 108px;
  height: 34px;
  padding: 0 16px;
  color: rgba(180, 220, 255, 0.65);
  font-size: 13px;
  letter-spacing: 0.1em;
  cursor: pointer;
  background: linear-gradient(180deg, rgba(20, 60, 100, 0.45), rgba(8, 30, 58, 0.55));
  border: 1px solid rgba(70, 170, 240, 0.35);
  clip-path: polygon(10px 0, calc(100% - 10px) 0, 100% 50%, calc(100% - 10px) 100%, 10px 100%, 0 50%);
  transition: all 0.2s;
}
.menu-btn:hover,
.menu-btn.active {
  color: #fff;
  border-color: #7ef0ff;
  box-shadow: 0 0 16px rgba(60, 200, 255, 0.35);
  background: linear-gradient(180deg, rgba(30, 110, 170, 0.7), rgba(10, 50, 90, 0.75));
}

@media (max-width: 1200px) {
  .menu-btn { min-width: 88px; font-size: 12px; }
}
</style>
