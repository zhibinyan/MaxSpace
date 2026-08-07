<template>
  <header class="bi-top">
    <!-- 背景光效层 -->
    <div class="top-glow" aria-hidden="true" />
    <div class="top-scan" aria-hidden="true" />

    <!-- 装饰图 + 立体翼展 -->
    <div class="top-deco-wrap" aria-hidden="true">
      <div class="wing wing-l" />
      <div class="wing wing-r" />
      <img class="top-deco" src="/bi/header-deco.svg" alt="" />
      <div class="deco-dots">
        <i v-for="n in 12" :key="n" :style="dotStyle(n)" />
      </div>
    </div>

    <div class="top-inner">
      <div class="top-kpis left">
        <div class="kpi-card kpi-3d">
          <div class="kpi-face">
            <div class="kpi-label">2024年生产总值</div>
            <div class="kpi-value">
              <span class="num">31500</span>
              <small>亿元</small>
            </div>
          </div>
          <div class="kpi-edge" />
        </div>
      </div>

      <div class="title-block">
        <div class="title-3d" data-text="全国经济数据可视化驾驶舱大屏">
          <h1 class="top-title">全国经济数据可视化驾驶舱大屏</h1>
        </div>
        <div class="title-underline">
          <span /><span /><span />
        </div>
      </div>

      <div class="top-kpis right">
        <div class="kpi-card kpi-3d">
          <div class="kpi-face">
            <div class="kpi-label">2024年常驻人数</div>
            <div class="kpi-value">
              <span class="num">15000</span>
              <small>万人</small>
            </div>
          </div>
          <div class="kpi-edge" />
        </div>
        <div class="top-clock kpi-3d clock-3d">
          <div class="clock-time">{{ currentTime }}</div>
          <div class="clock-brand">数字像素</div>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { onMounted } from 'vue'
import { useTime } from '../composables/useTime'

const { currentTime, startTimer } = useTime()
onMounted(() => startTimer())

const dotStyle = (n) => {
  const t = (n - 1) / 11
  return {
    left: `${8 + t * 84}%`,
    animationDelay: `${n * 0.18}s`,
    animationDuration: `${2.4 + (n % 3) * 0.4}s`,
  }
}
</script>

<style scoped>
.bi-top {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 40;
  height: 108px;
  perspective: 900px;
  pointer-events: none;
  background: linear-gradient(
    180deg,
    rgba(4, 18, 40, 0.98) 0%,
    rgba(4, 22, 48, 0.72) 55%,
    transparent 100%
  );
  overflow: hidden;
}

.top-inner {
  position: relative;
  z-index: 2;
  height: 100%;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  align-items: center;
  padding: 14px clamp(28px, 3vw, 56px) 0;
  transform-style: preserve-3d;
}

.top-kpis {
  display: flex;
  align-items: center;
  gap: 16px;
  pointer-events: auto;
  transform-style: preserve-3d;
  min-width: 0;
}
.top-kpis.left {
  justify-content: flex-start;
  /* 略向内收，避免 rotateY 在宽屏把卡片挤出左边缘 */
  transform: rotateY(6deg) translateZ(6px) translateX(10px);
  padding-left: 4px;
}
.top-kpis.right {
  justify-content: flex-end;
  transform: rotateY(-6deg) translateZ(6px) translateX(-10px);
  padding-right: 4px;
}

@media (min-width: 1200px) {
  .top-inner {
    padding-left: clamp(40px, 4vw, 72px);
    padding-right: clamp(40px, 4vw, 72px);
  }
  .top-kpis.left {
    transform: rotateY(5deg) translateZ(4px) translateX(16px);
  }
  .top-kpis.right {
    transform: rotateY(-5deg) translateZ(4px) translateX(-16px);
  }
}

@media (max-width: 1200px) {
  .kpi-card { min-width: 120px; }
  .kpi-value .num { font-size: 20px; }
  .wing { display: none; }
  .top-kpis.left,
  .top-kpis.right {
    transform: none;
    padding: 0;
  }
}
@media (max-width: 900px) {
  .top-kpis.left { display: none; }
  .top-title,
  .title-3d::before { font-size: 16px; letter-spacing: 0.08em; }
  .top-kpis.right { transform: none; }
}

.top-glow {
  position: absolute;
  left: 50%;
  top: -40px;
  width: 70%;
  height: 120px;
  transform: translateX(-50%);
  background: radial-gradient(ellipse at center, rgba(40, 160, 255, 0.35), transparent 70%);
  filter: blur(8px);
  animation: glowPulse 4s ease-in-out infinite;
}

.top-scan {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    100deg,
    transparent 0%,
    rgba(125, 240, 255, 0.08) 45%,
    rgba(125, 240, 255, 0.18) 50%,
    rgba(125, 240, 255, 0.08) 55%,
    transparent 100%
  );
  background-size: 220% 100%;
  animation: scanMove 5.5s linear infinite;
  pointer-events: none;
}

.top-deco-wrap {
  position: absolute;
  left: 50%;
  top: 4px;
  width: min(94vw, 1180px);
  height: 86px;
  transform: translateX(-50%) rotateX(18deg);
  transform-style: preserve-3d;
}

.top-deco {
  position: relative;
  width: 100%;
  height: auto;
  display: block;
  filter:
    drop-shadow(0 0 8px rgba(61, 231, 255, 0.55))
    drop-shadow(0 10px 18px rgba(0, 80, 160, 0.45));
  animation: decoFloat 3.6s ease-in-out infinite;
}

.wing {
  position: absolute;
  top: 34px;
  width: 120px;
  height: 28px;
  background: linear-gradient(90deg, rgba(61, 231, 255, 0.55), transparent);
  clip-path: polygon(0 50%, 18% 0, 100% 35%, 100% 65%, 18% 100%);
  filter: drop-shadow(0 0 8px rgba(61, 231, 255, 0.4));
  opacity: 0.75;
  animation: wingPulse 2.8s ease-in-out infinite;
}
.wing-l {
  left: -8px;
  transform: scaleX(-1);
}
.wing-r {
  right: -8px;
  background: linear-gradient(90deg, transparent, rgba(61, 231, 255, 0.55));
  clip-path: polygon(0 35%, 82% 0, 100% 50%, 82% 100%, 0 65%);
  animation-delay: 0.4s;
}

.deco-dots {
  position: absolute;
  inset: 18px 10% 0;
  pointer-events: none;
}
.deco-dots i {
  position: absolute;
  top: 0;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #7ef0ff;
  box-shadow:
    0 0 8px #3de7ff,
    0 0 16px rgba(61, 231, 255, 0.8);
  animation: dotFloat ease-in-out infinite;
}

.title-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  transform: translateZ(28px) rotateX(8deg);
  transform-style: preserve-3d;
}

.title-3d {
  position: relative;
}

.title-3d::before {
  content: attr(data-text);
  position: absolute;
  left: 0;
  top: 0;
  color: transparent;
  -webkit-text-stroke: 1px rgba(61, 231, 255, 0.35);
  transform: translate3d(2px, 3px, -8px);
  filter: blur(0.3px);
  opacity: 0.7;
  white-space: nowrap;
  font-size: clamp(18px, 2vw, 30px);
  font-weight: 700;
  letter-spacing: 0.2em;
}

.top-title {
  position: relative;
  margin: 0;
  font-size: clamp(18px, 2vw, 30px);
  font-weight: 700;
  letter-spacing: 0.2em;
  white-space: nowrap;
  color: #f0fbff;
  background: linear-gradient(180deg, #ffffff 0%, #9ae8ff 45%, #3de7ff 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  filter: drop-shadow(0 0 14px rgba(61, 231, 255, 0.65))
    drop-shadow(0 4px 0 rgba(8, 60, 110, 0.55));
  animation: titleShine 3.2s ease-in-out infinite;
}

.title-underline {
  display: flex;
  gap: 6px;
  margin-top: 6px;
  align-items: center;
}
.title-underline span {
  display: block;
  height: 2px;
  border-radius: 2px;
  background: linear-gradient(90deg, transparent, #3de7ff, transparent);
  box-shadow: 0 0 8px #3de7ff;
}
.title-underline span:nth-child(1) { width: 28px; opacity: 0.45; }
.title-underline span:nth-child(2) { width: 90px; opacity: 0.95; animation: linePulse 2s ease-in-out infinite; }
.title-underline span:nth-child(3) { width: 28px; opacity: 0.45; }

.kpi-3d {
  position: relative;
  transform-style: preserve-3d;
  transform: rotateX(12deg);
  animation: cardFloat 3.4s ease-in-out infinite;
}

.kpi-card {
  min-width: 148px;
}

.kpi-face {
  position: relative;
  z-index: 2;
  padding: 8px 16px 10px;
  background:
    linear-gradient(145deg, rgba(30, 90, 140, 0.75), rgba(6, 28, 56, 0.85) 55%, rgba(4, 20, 42, 0.9));
  border: 1px solid rgba(125, 240, 255, 0.45);
  box-shadow:
    inset 0 1px 0 rgba(180, 240, 255, 0.35),
    inset 0 -8px 18px rgba(0, 40, 80, 0.35),
    0 8px 20px rgba(0, 40, 90, 0.45),
    0 0 18px rgba(61, 231, 255, 0.2);
  clip-path: polygon(10px 0, calc(100% - 10px) 0, 100% 10px, 100% calc(100% - 10px), calc(100% - 10px) 100%, 10px 100%, 0 calc(100% - 10px), 0 10px);
}

.kpi-edge {
  position: absolute;
  left: 4px;
  right: 4px;
  bottom: -5px;
  height: 8px;
  z-index: 1;
  background: linear-gradient(180deg, rgba(20, 90, 140, 0.9), rgba(4, 30, 60, 0.95));
  transform: translateZ(-6px) rotateX(-70deg);
  transform-origin: top;
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.35);
  opacity: 0.85;
}

.kpi-label {
  font-size: 11px;
  letter-spacing: 0.08em;
  color: rgba(160, 210, 240, 0.75);
}

.kpi-value {
  margin-top: 2px;
  display: flex;
  align-items: baseline;
  gap: 4px;
}
.kpi-value .num {
  font-size: 24px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #9aefff;
  text-shadow:
    0 0 12px rgba(80, 220, 255, 0.75),
    0 2px 0 rgba(0, 60, 100, 0.8);
  background: linear-gradient(180deg, #fff 10%, #7ef0ff 70%, #22d3ee 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
.kpi-value small {
  font-size: 12px;
  color: rgba(180, 220, 255, 0.75);
}

.clock-3d {
  padding: 8px 12px;
  text-align: right;
  background: linear-gradient(145deg, rgba(20, 70, 110, 0.55), rgba(6, 24, 48, 0.7));
  border: 1px solid rgba(90, 200, 255, 0.35);
  box-shadow:
    inset 0 1px 0 rgba(180, 240, 255, 0.2),
    0 6px 14px rgba(0, 40, 80, 0.4);
  clip-path: polygon(8px 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%, 0 8px);
}

.clock-time {
  font-size: 13px;
  color: #9ad8ff;
  letter-spacing: 0.04em;
  text-shadow: 0 0 8px rgba(80, 200, 255, 0.5);
}
.clock-brand {
  margin-top: 2px;
  font-size: 12px;
  color: rgba(160, 210, 240, 0.55);
  letter-spacing: 0.16em;
}

@keyframes glowPulse {
  0%, 100% { opacity: 0.55; transform: translateX(-50%) scale(1); }
  50% { opacity: 0.95; transform: translateX(-50%) scale(1.05); }
}
@keyframes scanMove {
  0% { background-position: 120% 0; }
  100% { background-position: -120% 0; }
}
@keyframes decoFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}
@keyframes wingPulse {
  0%, 100% { opacity: 0.45; filter: drop-shadow(0 0 4px rgba(61, 231, 255, 0.3)); }
  50% { opacity: 0.9; filter: drop-shadow(0 0 12px rgba(61, 231, 255, 0.7)); }
}
@keyframes dotFloat {
  0%, 100% { transform: translateY(0) scale(0.7); opacity: 0.35; }
  50% { transform: translateY(10px) scale(1.15); opacity: 1; }
}
@keyframes titleShine {
  0%, 100% { filter: drop-shadow(0 0 10px rgba(61, 231, 255, 0.45)) drop-shadow(0 4px 0 rgba(8, 60, 110, 0.55)); }
  50% { filter: drop-shadow(0 0 20px rgba(125, 240, 255, 0.85)) drop-shadow(0 4px 0 rgba(8, 60, 110, 0.55)); }
}
@keyframes linePulse {
  0%, 100% { opacity: 0.55; transform: scaleX(0.92); }
  50% { opacity: 1; transform: scaleX(1); }
}
@keyframes cardFloat {
  0%, 100% { transform: rotateX(12deg) translateY(0); }
  50% { transform: rotateX(12deg) translateY(-3px); }
}
</style>
