import type { WallpaperCategory, WallpaperItem } from '../types/wallpaper'
import dubai from '../assets/wallpapers/dubai.jpg'
import dubai2 from '../assets/wallpapers/dubai2.jpg'
import mountain from '../assets/wallpapers/mountain.jpg'
import fogValley from '../assets/wallpapers/fog-valley.jpg'
import cityNight from '../assets/wallpapers/city-night.jpg'
import beach from '../assets/wallpapers/beach.jpg'
import peaks from '../assets/wallpapers/peaks.jpg'

export const DEFAULT_WALLPAPER_ID = 'aurora'

const AURORA_GRADIENT = [
  'radial-gradient(ellipse 80% 60% at 20% 80%, rgba(255, 120, 80, 0.45), transparent)',
  'radial-gradient(ellipse 70% 50% at 80% 20%, rgba(80, 160, 255, 0.5), transparent)',
  'radial-gradient(ellipse 60% 40% at 50% 50%, rgba(180, 100, 220, 0.35), transparent)',
  'linear-gradient(160deg, #1a3a5c 0%, #2d1b4e 35%, #4a1942 65%, #1e2d5a 100%)',
].join(', ')

export const wallpaperCatalog: WallpaperItem[] = [
  {
    id: 'mountain',
    title: '雪山晨曦',
    type: 'image',
    category: 'landscape',
    src: mountain,
  },
  {
    id: 'fog-valley',
    title: '雾谷晨光',
    type: 'image',
    category: 'landscape',
    src: fogValley,
  },
  {
    id: 'peaks',
    title: '峻岭云海',
    type: 'image',
    category: 'landscape',
    src: peaks,
  },
  {
    id: 'beach',
    title: '热带海岸',
    type: 'image',
    category: 'featured',
    src: beach,
  },
  {
    id: 'city-night',
    title: '都市夜色',
    type: 'image',
    category: 'city',
    src: cityNight,
  },
  {
    id: 'dubai',
    title: '迪拜都市',
    type: 'image',
    category: 'city',
    src: dubai,
  },
  {
    id: 'dubai2',
    title: '迪拜天际线',
    type: 'image',
    category: 'city',
    src: dubai2,
  },
  {
    id: 'aurora',
    title: '极光渐变',
    type: 'gradient',
    category: 'gradient',
    background: AURORA_GRADIENT,
  },
  {
    id: 'sunset',
    title: '暮色渐变',
    type: 'gradient',
    category: 'gradient',
    background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 40%, #e94560 100%)',
  },
  {
    id: 'ocean',
    title: '深海渐变',
    type: 'gradient',
    category: 'gradient',
    background: 'linear-gradient(160deg, #0f2027 0%, #203a43 50%, #2c5364 100%)',
  },
]

export const wallpaperCategoryLabels: Record<WallpaperCategory, string> = {
  featured: '精选',
  landscape: '风景',
  city: '城市',
  gradient: '渐变',
}

export function getWallpaperById(id: string): WallpaperItem | undefined {
  return wallpaperCatalog.find((item) => item.id === id)
}

export function getWallpaperBackground(item: WallpaperItem): string {
  if (item.type === 'image' && item.src) {
    return `url("${item.src}") center / cover no-repeat`
  }
  return item.background ?? AURORA_GRADIENT
}
