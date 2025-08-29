import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
      imports: [
        'vue',
        'vue-router',
        'pinia',
        '@vueuse/core'
      ],
      dts: true
    }),
    Components({
      resolvers: [ElementPlusResolver()],
      dts: true
    }),
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@/types': resolve(__dirname, '../../packages/shared/src/types')
    }
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true, // Fail if port is already in use
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false,
        ws: true, // Enable WebSocket proxying
        timeout: 0, // 禁用代理超时，让客户端控制超时
        proxyTimeout: 300000, // 5分钟代理超时，支持长时间AI分析
        configure: (proxy, options) => {
          proxy.on('error', (err, req, res) => {
            console.log('Proxy error:', err.message);
          });
          proxy.on('proxyReq', (proxyReq, req, res) => {
            console.log(`Proxying ${req.method} ${req.url} → http://localhost:5000${req.url}`);
            // 为AI分析请求设置特殊的超时
            if (req.url && req.url.includes('/ai-analysis/analyze-document')) {
              console.log('🤖 AI Analysis request detected - extending timeout');
              proxyReq.setTimeout(300000); // 5分钟
            }
          });
          proxy.on('proxyRes', (proxyRes, req, res) => {
            console.log(`Response: ${proxyRes.statusCode} for ${req.method} ${req.url}`);
          });
        }
      },
      '/health': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false
      },
      '/ping': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      },
    },
    rollupOptions: {
      output: {
        manualChunks: {
          'element-plus': ['element-plus'],
          'vue': ['vue', 'vue-router'],
          'pinia': ['pinia'],
          'utils': ['axios', 'dayjs', 'lodash-es']
        },
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]'
      }
    },
    chunkSizeWarningLimit: 1000
  },
  optimizeDeps: {
    include: ['vue', 'vue-router', 'pinia', 'element-plus', 'axios']
  }
})