<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { Check } from '@element-plus/icons-vue'
import {
  getWallpaperBackground,
  wallpaperCatalog,
  wallpaperCategoryLabels,
} from '../../config/wallpapers'
import { useWallpaperStore } from '../../stores/wallpaper'
import type { WallpaperCategory, WallpaperItem } from '../../types/wallpaper'

const wallpaperStore = useWallpaperStore()

const categoryOrder: WallpaperCategory[] = ['featured', 'landscape', 'city', 'gradient']

const groupedWallpapers = computed(() =>
  categoryOrder
    .map((category) => ({
      category,
      label: wallpaperCategoryLabels[category],
      items: wallpaperCatalog.filter((item) => item.category === category),
    }))
    .filter((group) => group.items.length > 0),
)

function thumbStyle(item: WallpaperItem) {
  return { background: getWallpaperBackground(item) }
}

function selectWallpaper(id: string) {
  wallpaperStore.selectWallpaper(id)
  wallpaperStore.persistToServer()
}

onMounted(() => {
  wallpaperStore.loadFromServer()
})
</script>

<template>
  <div class="wallpaper-page">
    <header class="page-header">
      <h1 class="page-title">墙纸</h1>
      <p class="page-desc">选择桌面与登录页背景，设置会自动保存到本地</p>
    </header>

    <section class="current-section">
      <div class="current-preview" :style="wallpaperStore.wallpaperStyle" />
      <div class="current-meta">
        <h2 class="current-title">{{ wallpaperStore.activeWallpaper.title }}</h2>
        <div class="current-options">
          <div class="option-row">
            <span>应用到登录页与桌面</span>
            <el-switch
              disabled
              :model-value="wallpaperStore.settings.fillAllSpaces"
              @change="(v: boolean) => { wallpaperStore.setFillAllSpaces(v); wallpaperStore.persistToServer() }"
            />
          </div>
        </div>
      </div>
    </section>

    <section
      v-for="group in groupedWallpapers"
      :key="group.category"
      class="wallpaper-group"
    >
      <div class="group-header">
        <h3>{{ group.label }}</h3>
      </div>
      <div class="wallpaper-grid">
        <button
          v-for="item in group.items"
          :key="item.id"
          type="button"
          class="wallpaper-card"
          :class="{ active: wallpaperStore.settings.wallpaperId === item.id }"
          @click="selectWallpaper(item.id)"
        >
          <div class="wallpaper-thumb" :style="thumbStyle(item)">
            <span v-if="wallpaperStore.settings.wallpaperId === item.id" class="thumb-check">
              <el-icon><Check /></el-icon>
            </span>
          </div>
          <span class="wallpaper-name">{{ item.title }}</span>
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.wallpaper-page {
  max-width: 920px;
  width: 100%;
  margin: 0 auto;
  flex: 1;
  min-height: 0;
  height: 100%;
  overflow-x: hidden;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  box-sizing: border-box;
  padding-bottom: 24px;
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  color: #1d1d1f;
  letter-spacing: -0.02em;
}

.page-desc {
  margin: 6px 0 0;
  font-size: 13px;
  color: rgba(60, 60, 67, 0.7);
}

.current-section {
  display: flex;
  gap: 24px;
  align-items: stretch;
  margin-bottom: 32px;
  padding: 20px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.42);
  border: 1px solid rgba(255, 255, 255, 0.55);
  backdrop-filter: blur(20px) saturate(160%);
  -webkit-backdrop-filter: blur(20px) saturate(160%);
}

.current-preview {
  width: 280px;
  height: 168px;
  flex-shrink: 0;
  border-radius: 12px;
  box-shadow:
    0 0 0 0.5px rgba(0, 0, 0, 0.12),
    0 8px 24px rgba(0, 0, 0, 0.12);
}

.current-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
}

.current-title {
  margin: 0 0 16px;
  font-size: 20px;
  font-weight: 600;
  color: #1d1d1f;
}

.current-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.option-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  font-size: 14px;
  color: #3c3c43;
}

.current-hint {
  margin: 16px 0 0;
  font-size: 12px;
  color: rgba(60, 60, 67, 0.55);
}

.wallpaper-group + .wallpaper-group {
  margin-top: 28px;
}

.group-header {
  margin-bottom: 12px;
}

.group-header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #1d1d1f;
}

.wallpaper-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(148px, 1fr));
  gap: 14px;
}

.wallpaper-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  text-align: left;
}

.wallpaper-thumb {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 10;
  border-radius: 10px;
  box-shadow:
    0 0 0 0.5px rgba(0, 0, 0, 0.1),
    0 4px 12px rgba(0, 0, 0, 0.08);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.wallpaper-card:hover .wallpaper-thumb {
  transform: translateY(-2px);
  box-shadow:
    0 0 0 0.5px rgba(0, 0, 0, 0.12),
    0 8px 20px rgba(0, 0, 0, 0.14);
}

.wallpaper-card.active .wallpaper-thumb {
  box-shadow:
    0 0 0 2px #007aff,
    0 4px 16px rgba(0, 122, 255, 0.28);
}

.thumb-check {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #007aff;
  color: #fff;
  font-size: 12px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}

.wallpaper-name {
  font-size: 12px;
  color: #3c3c43;
  padding: 0 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 720px) {
  .current-section {
    flex-direction: column;
  }

  .current-preview {
    width: 100%;
    height: 180px;
  }
}
</style>
