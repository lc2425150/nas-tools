import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
export default defineConfig({
  plugins: [vue()],
  server: { host: '0.0.0.0', port: 5173, proxy: { '/api': 'http://localhost:8932', '/ws': { target: 'ws://localhost:8932', ws: true } } },
  build: { outDir: 'dist', emptyOutDir: true },
})
