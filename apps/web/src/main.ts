import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import { createI18n } from 'vue-i18n'
import en from './locales/en.json'
import zh from './locales/zh.json'

// Import responsive styles
import './styles/responsive.css'

// Create i18n instance
const i18n = createI18n({
  legacy: false,
  locale: 'en',
  fallbackLocale: 'en',
  messages: {
    en,
    zh
  }
})

// Create app
const app = createApp(App)

// Register Element Plus icons
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// Install plugins
const pinia = createPinia()
app.use(pinia)
app.use(router)
app.use(ElementPlus)
app.use(i18n)

// Initialize auth before mounting
async function initApp() {
  const { useAuthStore } = await import('./stores/auth')
  const authStore = useAuthStore()
  
  try {
    // 初始化认证状态（仅恢复token，不调用API）
    authStore.initializeAuth()
    
    // 如果有token，尝试加载用户信息
    if (authStore.isAuthenticated) {
      try {
        await authStore.loadUserProfile()
        console.log('✅ App初始化: 用户信息加载成功', authStore.user?.username, '角色:', authStore.userRole)
      } catch (error) {
        console.warn('⚠️ App初始化: 用户信息加载失败，将在首次API调用时重试', error)
      }
    }
  } catch (error) {
    console.warn('❌ App初始化: 认证初始化失败', error)
  }
  
  // Mount app after auth initialization
  app.mount('#app')
}

initApp()