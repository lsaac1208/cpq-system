import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

// 生产环境Vite配置
// 使用方法: npm run build -- --config deployment/vite.config.prod.ts
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
      '@': resolve(__dirname, '../apps/web/src'),
      '@/types': resolve(__dirname, '../packages/shared/src/types')
    }
  },

  // 生产环境构建优化
  build: {
    outDir: '../apps/web/dist',
    sourcemap: false,  // 生产环境关闭source map
    minify: 'terser',
    
    terserOptions: {
      compress: {
        drop_console: true,    // 移除console
        drop_debugger: true,   // 移除debugger
        pure_funcs: ['console.log', 'console.info']  // 移除特定函数
      },
      mangle: {
        safari10: true
      }
    },
    
    rollupOptions: {
      output: {
        // 分包策略
        manualChunks: {
          'vue-vendor': ['vue', 'vue-router'],
          'element-plus': ['element-plus'],
          'pinia': ['pinia'],
          'utils': ['axios'],
          'pdf-libs': ['jspdf', 'pdf-lib', '@pdf-lib/fontkit'],
          'chart-libs': ['echarts']
        },
        
        // 文件命名
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const extType = assetInfo.name.split('.').pop();
          if (/\.(png|jpe?g|gif|svg|ico)$/i.test(assetInfo.name)) {
            return 'images/[name]-[hash].[ext]';
          }
          if (/\.(ttf|woff2?|eot)$/i.test(assetInfo.name)) {
            return 'fonts/[name]-[hash].[ext]';
          }
          if (extType === 'css') {
            return 'css/[name]-[hash].[ext]';
          }
          return 'assets/[name]-[hash].[ext]';
        }
      }
    },
    
    // 包大小警告阈值
    chunkSizeWarningLimit: 1500,
    
    // 压缩配置
    reportCompressedSize: false,  // 关闭压缩大小报告以提高构建速度
    
    // 目标浏览器
    target: ['es2015', 'chrome58', 'firefox57', 'safari11', 'edge16']
  },

  // 优化依赖预构建
  optimizeDeps: {
    include: [
      'vue', 
      'vue-router', 
      'pinia', 
      'element-plus',
      'axios',
      '@element-plus/icons-vue'
    ]
  },

  // 定义全局变量
  define: {
    __VUE_OPTIONS_API__: true,
    __VUE_PROD_DEVTOOLS__: false,
    // 生产环境API地址
    'process.env.VITE_API_BASE_URL': JSON.stringify('http://cpqh.d1bbk.com'),
    'process.env.NODE_ENV': JSON.stringify('production')
  },

  // 生产环境服务器配置（用于预览）
  preview: {
    host: '0.0.0.0',
    port: 4173,
    strictPort: true
  }
})