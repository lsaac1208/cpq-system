<template>
  <div id="app">
    <router-view />
    
    <!-- 全局加载和反馈管理器 -->
    <GlobalLoadingManager ref="loadingManager" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, provide } from 'vue'
import { useAuthStore } from '@/stores/auth'
import GlobalLoadingManager from '@/components/common/GlobalLoadingManager.vue'

const authStore = useAuthStore()
const loadingManager = ref()

// 提供全局加载管理器给子组件使用
provide('loadingManager', loadingManager)

// 页面可见性变化处理
const handleVisibilityChange = () => {
  if (document.visibilityState === 'visible' && !authStore.token) {
    // 页面从隐藏变为可见时，恢复认证状态
    const storedToken = localStorage.getItem('cpq_access_token')
    if (storedToken) {
      console.log('🔄 检测到页面重新激活，恢复认证状态...')
      authStore.initializeAuth()
    }
  }
}

onMounted(() => {
  // 🔧 应用启动时仅恢复认证状态，不做API调用
  authStore.initializeAuth()
  console.log('🚀 应用启动认证状态恢复完成')
  
  // 监听页面可见性变化
  document.addEventListener('visibilitychange', handleVisibilityChange)
})

onUnmounted(() => {
  document.removeEventListener('visibilitychange', handleVisibilityChange)
})
</script>

<style scoped>
#app {
  min-height: 100vh;
  font-family: 'Helvetica Neue', Arial, sans-serif;
}
</style>