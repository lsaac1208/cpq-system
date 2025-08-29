import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import { authApi } from '@/api/auth'
import type { User, LoginRequest, RegisterRequest } from '@/types/auth'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)
  const loading = ref(false)

  // Getters
  const isAuthenticated = computed(() => !!token.value)
  const userRole = computed(() => user.value?.role || 'sales')
  const isAdmin = computed(() => userRole.value === 'admin')
  const isEngineer = computed(() => userRole.value === 'engineer')
  const isManager = computed(() => userRole.value === 'manager')
  const canEditProducts = computed(() => 
    ['engineer', 'admin', 'manager'].includes(userRole.value)
  )
  const canDeleteProducts = computed(() => 
    ['engineer', 'admin', 'manager'].includes(userRole.value)
  )
  
  // AI Analysis permissions
  const canUseAIAnalysis = computed(() => 
    ['engineer', 'admin', 'manager'].includes(userRole.value)
  )
  const hasAIAnalysisRole = computed(() => 
    isAuthenticated.value && canUseAIAnalysis.value
  )

  // Actions
  const initializeAuth = () => {
    // 🔧 简化初始化：仅恢复token状态，不做API调用，避免循环依赖
    const storedToken = localStorage.getItem('cpq_access_token')
    const storedRefreshToken = localStorage.getItem('cpq_refresh_token')
    
    if (storedToken) {
      token.value = storedToken
      refreshToken.value = storedRefreshToken
      console.log('✅ Token状态已恢复，等待首次API调用验证')
    }
  }

  const loadUserProfile = async () => {
    // 🔧 单独的用户信息加载方法，让interceptor处理token验证
    if (!token.value) {
      console.warn('❌ 没有token，无法加载用户信息')
      return
    }
    
    try {
      const response = await authApi.getCurrentUser()
      user.value = response.data.user
      console.log('✅ 用户信息加载成功:', user.value.username)
    } catch (error) {
      console.warn('❌ 用户信息加载失败，让interceptor处理:', error)
      // 让interceptor处理token刷新和错误处理
    }
  }

  const login = async (credentials: LoginRequest) => {
    loading.value = true
    try {
      console.log('🔄 开始登录请求...', credentials.username)
      const response = await authApi.login(credentials)
      console.log('📨 收到登录响应:', response)
      
      // 验证响应结构 - 注意后端返回的是嵌套结构
      if (!response || !response.data || !response.data.data || !response.data.data.tokens) {
        console.error('❌ 登录响应格式错误:', response)
        throw new Error('登录响应格式错误')
      }
      
      console.log('✅ 响应结构验证通过')
      
      // Store tokens and user info - 访问嵌套的data.data结构
      token.value = response.data.data.tokens.access_token
      refreshToken.value = response.data.data.tokens.refresh_token
      user.value = response.data.data.user
      
      console.log('💾 Token已存储到状态:', {
        hasToken: !!token.value,
        hasUser: !!user.value,
        username: user.value?.username
      })
      
      // Persist to localStorage - 访问嵌套的data.data结构
      localStorage.setItem('cpq_access_token', response.data.data.tokens.access_token)
      localStorage.setItem('cpq_refresh_token', response.data.data.tokens.refresh_token)
      
      console.log('💾 Token已持久化到localStorage')
      
      return response
    } catch (error) {
      console.error('❌ 登录过程出错:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const register = async (userData: RegisterRequest) => {
    loading.value = true
    try {
      const response = await authApi.register(userData)
      
      // Store tokens and user info - 访问嵌套的data.data结构
      token.value = response.data.data.tokens.access_token
      refreshToken.value = response.data.data.tokens.refresh_token
      user.value = response.data.data.user
      
      // Persist to localStorage - 访问嵌套的data.data结构
      localStorage.setItem('cpq_access_token', response.data.data.tokens.access_token)
      localStorage.setItem('cpq_refresh_token', response.data.data.tokens.refresh_token)
      
      return response
    } finally {
      loading.value = false
    }
  }

  const refreshAccessToken = async () => {
    try {
      const response = await authApi.refresh()
      token.value = response.data.access_token
      localStorage.setItem('cpq_access_token', response.data.access_token)
      return response
    } catch (error) {
      // Refresh failed, clear auth
      clearAuth()
      throw error
    }
  }

  const logout = () => {
    clearAuth()
  }

  const clearAuth = () => {
    user.value = null
    token.value = null
    refreshToken.value = null
    localStorage.removeItem('cpq_access_token')
    localStorage.removeItem('cpq_refresh_token')
  }

  const updateUser = (updatedUser: User) => {
    user.value = updatedUser
  }

  return {
    // State
    user: readonly(user),
    token: readonly(token),
    refreshToken: readonly(refreshToken),
    loading: readonly(loading),
    
    // Getters
    isAuthenticated,
    userRole,
    isAdmin,
    isEngineer,
    isManager,
    canEditProducts,
    canDeleteProducts,
    canUseAIAnalysis,
    hasAIAnalysisRole,
    
    // Actions
    initializeAuth,
    loadUserProfile,
    login,
    register,
    refreshAccessToken,
    logout,
    updateUser
  }
})