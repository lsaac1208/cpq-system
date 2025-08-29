import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import { visualizer } from 'rollup-plugin-visualizer'
import { compression } from 'vite-plugin-compression2'

// 生产环境专用配置
// https://vitejs.dev/config/
export default defineConfig({
  mode: 'production',
  
  plugins: [
    vue({
      template: {
        compilerOptions: {
          // 移除生产环境中的注释
          comments: false
        }
      }
    }),
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
    // Gzip 压缩
    compression({
      algorithm: 'gzip',
      include: /\.(js|mjs|json|css|html)$/i,
      threshold: 1024
    }),
    // Brotli 压缩
    compression({
      algorithm: 'brotliCompress',
      include: /\.(js|mjs|json|css|html)$/i,
      threshold: 1024
    }),
    // 构建分析器（可选）
    process.env.ANALYZE === 'true' && visualizer({
      filename: 'dist/stats.html',
      open: true,
      gzipSize: true,
      brotliSize: true
    })
  ].filter(Boolean),

  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@/types': resolve(__dirname, '../../packages/shared/src/types')
    }
  },

  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    
    // 生产环境不生成 source map
    sourcemap: false,
    
    // 使用 esbuild 压缩 (更快，更可靠)
    minify: 'esbuild',
    
    // 备用 terser 配置 (注释掉以避免过度混淆)
    // terserOptions: {
    //   compress: {
    //     drop_console: true,
    //     drop_debugger: true,
    //     pure_funcs: ['console.log'],
    //     passes: 1  // 减少压缩轮次避免循环依赖
    //   },
    //   mangle: {
    //     keep_fnames: true,  // 保持函数名避免初始化问题
    //     reserved: ['ze', 'Ze', '$', 'Vue', 'App']  // 保留可能的关键变量名
    //   }
    // },

    // 代码分割配置
    rollupOptions: {
      output: {
        // 静态资源文件名格式
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js', 
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name!.split('.')
          const extType = info[info.length - 1]
          // 按文件类型分目录
          if (/\.(mp4|webm|ogg|mp3|wav|flac|aac)(\?.*)?$/i.test(assetInfo.name!)) {
            return `media/[name]-[hash].[ext]`
          }
          if (/\.(png|jpe?g|gif|svg|ico|webp)(\?.*)?$/i.test(assetInfo.name!)) {
            return `images/[name]-[hash].[ext]`
          }
          if (/\.(woff2?|eot|ttf|otf)(\?.*)?$/i.test(assetInfo.name!)) {
            return `fonts/[name]-[hash].[ext]`
          }
          return `assets/[name]-[hash].[ext]`
        },

        // 简化的代码分割配置 (避免复杂依赖导致初始化问题)
        manualChunks: {
          // 第三方库分离
          'vendor-vue': ['vue', 'vue-router', 'pinia'],
          'vendor-ui': ['element-plus', '@element-plus/icons-vue'],
          'vendor-utils': ['axios', 'dayjs', 'lodash-es', '@vueuse/core'],
          // PDF 相关库单独分离
          'vendor-pdf': ['pdf-lib', 'jspdf']
        }
      }
    },

    // 包大小警告限制 (KB)
    chunkSizeWarningLimit: 1000,
    
    // 资源内联限制 (bytes)
    assetsInlineLimit: 4096,

    // CSS 代码分割
    cssCodeSplit: true,

    // 构建时清空输出目录
    emptyOutDir: true,
    
    // 构建目标
    target: ['es2015', 'chrome63', 'firefox57', 'safari11.1']
  },

  // 预构建依赖优化 - 确保正确的模块加载顺序
  optimizeDeps: {
    include: [
      'vue',
      'vue-router', 
      'pinia',
      'element-plus',
      'axios',
      '@element-plus/icons-vue',
      '@vueuse/core'
    ],
    exclude: [
      // 排除可能导致循环依赖的大型库
      'pdf-lib',
      'jspdf'
    ],
    // 强制预构建，确保依赖关系正确
    force: true
  },

  // CSS 配置
  css: {
    preprocessorOptions: {
      scss: {
        charset: false
      }
    }
  },

  // 构建性能配置 - 简化避免初始化问题
  esbuild: {
    legalComments: 'none',
    // 只在非调试模式下移除console
    drop: process.env.DEBUG ? [] : ['console', 'debugger'],
    // 保持源码映射用于调试
    keepNames: true
  },

  // 基础路径
  base: '/',
  
  // 资源处理
  assetsInclude: ['**/*.pdf', '**/*.docx', '**/*.xlsx']
})