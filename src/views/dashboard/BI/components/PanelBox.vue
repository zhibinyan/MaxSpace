<template>
  <section class="panel-box">
    <div class="panel-box__title">
      <img src="/bi/panel-title.svg" alt="" />
      <span>{{ title }}</span>
    </div>
    <div class="panel-box__body">
      <slot />
    </div>
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
})
</script>

<style scoped>
.panel-box {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 8px 10px 6px;
  pointer-events: auto;
  background: linear-gradient(180deg, rgba(8, 36, 68, 0.78), rgba(4, 20, 42, 0.58));
  border: 1px solid rgba(56, 160, 230, 0.4);
  box-shadow:
    0 0 20px rgba(20, 100, 180, 0.14),
    inset 0 0 24px rgba(40, 140, 220, 0.08);
  backdrop-filter: blur(6px);
  clip-path: polygon(
    0 10px, 10px 0, calc(100% - 10px) 0, 100% 10px,
    100% calc(100% - 10px), calc(100% - 10px) 100%, 10px 100%, 0 calc(100% - 10px)
  );
}

.panel-box__title {
  position: relative;
  display: flex;
  align-items: center;
  height: 28px;
  margin-bottom: 4px;
  flex-shrink: 0;
}

.panel-box__title img {
  position: absolute;
  left: 0;
  top: 50%;
  width: 100%;
  height: 28px;
  transform: translateY(-50%);
  opacity: 0.85;
  object-fit: fill;
}

.panel-box__title span {
  position: relative;
  z-index: 1;
  padding-left: 28px;
  font-size: 13px;
  letter-spacing: 0.12em;
  color: #d7f2ff;
  text-shadow: 0 0 8px rgba(80, 200, 255, 0.35);
  white-space: nowrap;
}

.panel-box__body {
  flex: 1;
  min-height: 0;
  width: 100%;
  position: relative;
}
</style>
