import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  base: './',
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  optimizeDeps: {
    include: ['@vue-flow/core', '@vueuse/core'],
  },
  server: {
    host: true, // 允许局域网 IP 访问，如 http://192.168.x.x:8888
    port: 8888,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5050',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://127.0.0.1:5050',
        ws: true,
        changeOrigin: true,
      },
    },
  },
})
