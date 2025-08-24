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
        target: process.env.VITE_APP_ENV === 'development' 
          ? 'http://localhost:3000' 
          : 'https://eduscreenapi.psyventures.cn',
        changeOrigin: true,
        secure: process.env.VITE_APP_ENV !== 'development',
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