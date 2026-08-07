import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import {
  DEFAULT_WALLPAPER_ID,
  getWallpaperBackground,
  getWallpaperById,
} from '../config/wallpapers'
import { fetchWallpaperSettings, saveWallpaperSettings } from '../api/wallpaper'
import type { WallpaperSettings } from '../types/wallpaper'

const STORAGE_KEY = 'maxadmin_wallpaper'

function readLocalSettings(): WallpaperSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return { wallpaperId: DEFAULT_WALLPAPER_ID, fillAllSpaces: true }
    }
    const parsed = JSON.parse(raw) as WallpaperSettings
    const wallpaperId = parsed.wallpaperId === 'dubai-png' ? 'dubai' : parsed.wallpaperId
    if (!getWallpaperById(wallpaperId)) {
      return { wallpaperId: DEFAULT_WALLPAPER_ID, fillAllSpaces: true }
    }
    return {
      wallpaperId,
      fillAllSpaces: parsed.fillAllSpaces ?? true,
      updatedAt: parsed.updatedAt,
    }
  } catch {
    return { wallpaperId: DEFAULT_WALLPAPER_ID, fillAllSpaces: true }
  }
}

function writeLocalSettings(settings: WallpaperSettings) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
}

export const useWallpaperStore = defineStore('wallpaper', () => {
  const settings = ref<WallpaperSettings>(readLocalSettings())
  const syncing = ref(false)

  const activeWallpaper = computed(
    () => getWallpaperById(settings.value.wallpaperId) ?? getWallpaperById(DEFAULT_WALLPAPER_ID)!,
  )

  const wallpaperStyle = computed(() => ({
    background: getWallpaperBackground(activeWallpaper.value),
  }))

  function applySettings(next: WallpaperSettings) {
    settings.value = {
      ...next,
      updatedAt: new Date().toISOString(),
    }
    writeLocalSettings(settings.value)
  }

  function selectWallpaper(wallpaperId: string) {
    if (!getWallpaperById(wallpaperId)) return
    applySettings({
      ...settings.value,
      wallpaperId,
    })
  }

  function setFillAllSpaces(fillAllSpaces: boolean) {
    applySettings({
      ...settings.value,
      fillAllSpaces,
    })
  }

  async function loadFromServer() {
    syncing.value = true
    try {
      const remote = await fetchWallpaperSettings()
      if (remote && getWallpaperById(remote.wallpaperId)) {
        applySettings(remote)
      }
    } finally {
      syncing.value = false
    }
  }

  async function persistToServer() {
    syncing.value = true
    try {
      await saveWallpaperSettings(settings.value)
    } finally {
      syncing.value = false
    }
  }

  return {
    settings,
    syncing,
    activeWallpaper,
    wallpaperStyle,
    selectWallpaper,
    setFillAllSpaces,
    loadFromServer,
    persistToServer,
  }
})
