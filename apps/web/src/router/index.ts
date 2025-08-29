import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/views/Layout.vue'),
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/products',
        name: 'Products',
        component: () => import('@/views/Products.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/products/create',
        name: 'CreateProduct',
        component: () => import('@/views/CreateProduct.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/products/create-ai',
        name: 'CreateProductAI',
        component: () => import('@/views/CreateProductAI.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/products/:id',
        name: 'ProductDetail',
        component: () => import('@/views/ProductDetail.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/search',
        name: 'Search',
        component: () => import('@/views/SearchPage.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/quotes',
        name: 'Quotes',
        component: () => import('@/views/Quotes.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/quotes/create',
        name: 'CreateQuote',
        component: () => import('@/views/CreateQuote.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/quotes/:id',
        name: 'QuoteDetail',
        component: () => import('@/views/QuoteDetail.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
        meta: { requiresAuth: true, requiresAdmin: true }
      },
      {
        path: '/prompt-optimization',
        name: 'PromptOptimization',
        component: () => import('@/views/PromptOptimization.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/document-comparison',
        name: 'DocumentComparison',
        component: () => import('@/views/DocumentComparison.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/batch-analysis',
        name: 'BatchAnalysis',
        component: () => import('@/views/BatchAnalysis.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/batch-analysis/results/:jobId',
        name: 'BatchAnalysisResults',
        component: () => import('@/views/BatchAnalysisResultsSimple.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/ai-analysis-enhanced',
        name: 'AIAnalysisEnhanced',
        component: () => import('@/views/AIAnalysisEnhanced.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/pricing-decision',
        name: 'PricingDecision',
        component: () => import('@/views/PricingDecision.vue'),
        meta: { requiresAuth: true }
      },
    ]
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresGuest: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { requiresGuest: true }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guards
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // 🔧 检查认证状态并初始化用户信息
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    const storedToken = localStorage.getItem('cpq_access_token')
    
    if (storedToken) {
      // 恢复token状态
      authStore.initializeAuth()
      
      // 如果token存在但用户信息不存在，尝试加载用户信息
      if (!authStore.user) {
        try {
          await authStore.loadUserProfile()
        } catch (error) {
          console.warn('路由守卫中加载用户信息失败:', error)
          // 如果加载失败，继续执行，让应用程序处理
        }
      }
    }
  }
  
  // 基础认证检查
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
    return
  }
  
  // 访客页面检查
  if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next('/')
    return
  }
  
  // 管理员权限检查 - 修复逻辑
  if (to.meta.requiresAdmin) {
    // 如果已认证但用户信息还未加载，先尝试加载
    if (authStore.isAuthenticated && !authStore.user) {
      try {
        await authStore.loadUserProfile()
      } catch (error) {
        console.warn('管理员权限检查时加载用户信息失败:', error)
      }
    }
    
    // 检查管理员权限
    if (!authStore.isAdmin) {
      console.warn('用户无管理员权限，重定向到仪表盘')
      next('/')
      return
    }
  }
  
  next()
})

export default router