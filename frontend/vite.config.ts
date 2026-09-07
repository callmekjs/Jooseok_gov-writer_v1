import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../static',      // ★ 기본값(dist)이면 FastAPI 가 못 찾는다
    emptyOutDir: true,
  },
  server: {
    port: 5174,      // ★ 8010·5173 은 이 PC 의 다른 프로젝트 전용 포트 — 여기선 8011·5174
    proxy: {
      '/api': { target: 'http://localhost:8011', changeOrigin: true },   // ★ 8011 (run.ps1 과 일치해야 함)
    },
  },
})
