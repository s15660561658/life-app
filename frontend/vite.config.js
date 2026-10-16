import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 开发期代理：/api 转发到本地 FastAPI（8321）
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8321',
        changeOrigin: true
      }
    }
  }
})
