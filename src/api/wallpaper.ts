import type { WallpaperSettings } from '../types/wallpaper'

/**
 * Backend wallpaper API (reserved).
 * Replace implementations when server endpoints are ready.
 */
const WALLPAPER_API = '/api/settings/wallpaper'

export async function fetchWallpaperSettings(): Promise<WallpaperSettings | null> {
  // TODO: GET WALLPAPER_API
  void WALLPAPER_API
  return null
}

export async function saveWallpaperSettings(settings: WallpaperSettings): Promise<void> {
  // TODO: PUT WALLPAPER_API, body: settings
  void settings
}
