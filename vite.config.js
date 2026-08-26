import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 5173,
    host: true,
    allowedHosts: ['eduscreen.psyventures.cn', 'localhost'],
    proxy: {
      '/api': {
        // 默认使用本地开发环境，除非明确设置为生产环境
        // 本地后端端口可用 BACKEND_PORT 覆盖；8003 为本项目专用端口（8001 已被其他项目占用）
        target: process.env.NODE_ENV === 'production'
          ? 'https://eduscreenapi.psyventures.cn'
          : `http://localhost:${process.env.BACKEND_PORT || 8003}`,
        changeOrigin: true,
        secure: process.env.NODE_ENV === 'production',
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
  },
  // 明确指定入口文件
  root: path.resolve(__dirname),
  publicDir: path.resolve(__dirname, 'public'),
  optimizeDeps: {
    include: ['vue', 'vue-router', 'element-plus', 'jspsych']
  }
});