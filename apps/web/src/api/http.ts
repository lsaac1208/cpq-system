import axios from 'axios'
import type { InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import { showMessage } from '@/utils/message'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

// Create axios instance
const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 120000, // 增加到2分钟，支持AI分析长时间处理
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
http.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const authStore = useAuthStore()
    
    // Add auth token if available
    if (authStore.token && config.headers) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    
    // For FormData requests (file uploads), remove Content-Type header
    // to let axios set multipart/form-data with proper boundary
    if (config.data instanceof FormData && config.headers) {
      delete config.headers['Content-Type']
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
http.interceptors.response.use(
  (response: AxiosResponse) => {
    // Return the full response object to maintain compatibility with auth APIs
    // The response structure should be { data: actualData, status, headers, etc }
    return response
  },
  async (error) => {
    const authStore = useAuthStore()
    const originalRequest = error.config
    
    if (error.response) {
      const { status, data } = error.response
      
      switch (status) {
        case 401:
          // Unauthorized - try to refresh token first
          if (!originalRequest._retry && authStore.refreshToken) {
            originalRequest._retry = true
            
            try {
              await authStore.refreshAccessToken()
              // Retry the original request with new token
              originalRequest.headers.Authorization = `Bearer ${authStore.token}`
              return http(originalRequest)
            } catch (refreshError) {
              // Refresh failed, clear auth and redirect to login
              authStore.logout()
              router.push('/login')
              showMessage.error('登录已过期，请重新登录')
              break
            }
          } else {
            // No refresh token or already retried, logout
            authStore.logout()
            router.push('/login')
            showMessage.error('登录已过期，请重新登录')
          }
          break
        case 403:
          showMessage.error('Access forbidden')
          break
        case 404:
          showMessage.error('Resource not found')
          break
        case 422:
          showMessage.error('Validation error')
          break
        case 500:
          showMessage.error('Server error. Please try again later.')
          break
        default:
          showMessage.error(data?.error || 'An error occurred')
      }
    } else if (error.request) {
      showMessage.error('Network error. Please check your connection.')
    } else {
      showMessage.error('Request failed')
    }
    
    return Promise.reject(error)
  }
)

export default http