export type WallpaperCategory = 'featured' | 'landscape' | 'city' | 'gradient'

export type WallpaperType = 'image' | 'gradient'

export interface WallpaperItem {
  id: string
  title: string
  type: WallpaperType
  category: WallpaperCategory
  /** Image URL for image wallpapers */
  src?: string
  /** CSS background value for gradient wallpapers */
  background?: string
}

export interface WallpaperSettings {
  wallpaperId: string
  /** Apply the same wallpaper on login and desktop */
  fillAllSpaces: boolean
  updatedAt?: string
}
