// 全局状态管理组合式函数

import { inject, ref, computed, type Ref } from 'vue'
import { ElMessage } from 'element-plus'
import { handleError, withRetry, type ErrorContext, type RetryConfig } from '@/utils/errorHandler'

// 全局加载管理器类型
interface GlobalLoadingManager {
  startGlobalLoading: (task?: any) => void
  updateGlobalLoading: (updates: any) => void
  stopGlobalLoading: () => void
  startPageLoading: (text?: string) => void
  stopPageLoading: () => void
  showSuccess: (title: string, message?: string, action?: any) => void
  showWarning: (title: string, message?: string, action?: any) => void
  showError: (title: string, message?: string, action?: any) => void
  showInfo: (title: string, message?: string, action?: any) => void
  addTask: (task: any) => string
  updateTask: (taskId: string, updates: any) => void
  removeTask: (taskId: string) => void
}

// 全局状态接口
interface GlobalState {
  isOnline: boolean
  systemStatus: 'healthy' | 'warning' | 'error'
  notifications: Array<{
    id: string
    type: 'success' | 'warning' | 'error' | 'info'
    title: string
    message: string
    timestamp: number
    read: boolean
  }>
  activeRequests: number
  lastActivity: number
}

// 创建全局状态
const globalState = ref<GlobalState>({
  isOnline: navigator.onLine,
  systemStatus: 'healthy',
  notifications: [],
  activeRequests: 0,
  lastActivity: Date.now()
})

// 网络状态监听
let networkListenersAdded = false

const addNetworkListeners = () => {
  if (networkListenersAdded) return
  
  window.addEventListener('online', () => {
    globalState.value.isOnline = true
    ElMessage.success('网络连接已恢复')
  })
  
  window.addEventListener('offline', () => {
    globalState.value.isOnline = false
    ElMessage.warning('网络连接已断开')
  })
  
  networkListenersAdded = true
}

export function useGlobalState() {
  // 注入加载管理器
  const loadingManager = inject<Ref<GlobalLoadingManager>>('loadingManager')

  // 添加网络监听器
  addNetworkListeners()

  // 计算属性
  const isOnline = computed(() => globalState.value.isOnline)
  const systemStatus = computed(() => globalState.value.systemStatus)
  const unreadNotifications = computed(() => 
    globalState.value.notifications.filter(n => !n.read)
  )
  const hasActiveRequests = computed(() => globalState.value.activeRequests > 0)

  // 方法
  const updateActivity = () => {
    globalState.value.lastActivity = Date.now()
  }

  const incrementActiveRequests = () => {
    globalState.value.activeRequests++
    updateActivity()
  }

  const decrementActiveRequests = () => {
    globalState.value.activeRequests = Math.max(0, globalState.value.activeRequests - 1)
    updateActivity()
  }

  const addNotification = (
    type: 'success' | 'warning' | 'error' | 'info',
    title: string,
    message: string
  ) => {
    const notification = {
      id: Date.now().toString(),
      type,
      title,
      message,
      timestamp: Date.now(),
      read: false
    }
    
    globalState.value.notifications.unshift(notification)
    
    // 限制通知数量
    if (globalState.value.notifications.length > 50) {
      globalState.value.notifications = globalState.value.notifications.slice(0, 50)
    }
    
    return notification.id
  }

  const markNotificationRead = (notificationId: string) => {
    const notification = globalState.value.notifications.find(n => n.id === notificationId)
    if (notification) {
      notification.read = true
    }
  }

  const markAllNotificationsRead = () => {
    globalState.value.notifications.forEach(n => n.read = true)
  }

  const removeNotification = (notificationId: string) => {
    const index = globalState.value.notifications.findIndex(n => n.id === notificationId)
    if (index !== -1) {
      globalState.value.notifications.splice(index, 1)
    }
  }

  const clearNotifications = () => {
    globalState.value.notifications = []
  }

  const setSystemStatus = (status: 'healthy' | 'warning' | 'error') => {
    globalState.value.systemStatus = status
  }

  // 加载状态管理方法
  const showLoading = (title = '处理中...', description = '正在执行操作，请稍候') => {
    if (loadingManager?.value) {
      loadingManager.value.startGlobalLoading({
        title,
        description,
        showProgress: false
      })
    }
  }

  const showLoadingWithProgress = (
    title = '处理中...',
    description = '正在执行操作，请稍候',
    allowCancel = false,
    onCancel?: () => void
  ) => {
    if (loadingManager?.value) {
      loadingManager.value.startGlobalLoading({
        title,
        description,
        showProgress: true,
        allowCancel,
        onCancel
      })
    }
  }

  const updateLoadingProgress = (
    progress: number,
    progressText = '',
    estimatedTime = 0
  ) => {
    if (loadingManager?.value) {
      loadingManager.value.updateGlobalLoading({
        progress,
        progressText,
        estimatedTime
      })
    }
  }

  const hideLoading = () => {
    if (loadingManager?.value) {
      loadingManager.value.stopGlobalLoading()
    }
  }

  const showPageLoading = (text = '加载中...') => {
    if (loadingManager?.value) {
      loadingManager.value.startPageLoading(text)
    }
  }

  const hidePageLoading = () => {
    if (loadingManager?.value) {
      loadingManager.value.stopPageLoading()
    }
  }

  // 反馈消息方法
  const showSuccess = (title: string, message = '') => {
    if (loadingManager?.value) {
      loadingManager.value.showSuccess(title, message)
    }
    addNotification('success', title, message)
  }

  const showWarning = (title: string, message = '') => {
    if (loadingManager?.value) {
      loadingManager.value.showWarning(title, message)
    }
    addNotification('warning', title, message)
  }

  const showError = (title: string, message = '') => {
    if (loadingManager?.value) {
      loadingManager.value.showError(title, message)
    }
    addNotification('error', title, message)
  }

  const showInfo = (title: string, message = '') => {
    if (loadingManager?.value) {
      loadingManager.value.showInfo(title, message)
    }
    addNotification('info', title, message)
  }

  // 任务管理方法
  const addTask = (
    title: string,
    description = '',
    showProgress = false,
    allowCancel = false
  ) => {
    if (loadingManager?.value) {
      return loadingManager.value.addTask({
        title,
        description,
        showProgress,
        allowCancel
      })
    }
    return ''
  }

  const updateTask = (taskId: string, updates: any) => {
    if (loadingManager?.value) {
      loadingManager.value.updateTask(taskId, updates)
    }
  }

  const removeTask = (taskId: string) => {
    if (loadingManager?.value) {
      loadingManager.value.removeTask(taskId)
    }
  }

  // 增强的异步操作处理
  const executeWithLoading = async <T>(
    operation: () => Promise<T>,
    options: {
      loadingTitle?: string
      loadingDescription?: string
      showProgress?: boolean
      successMessage?: string
      errorContext?: ErrorContext
      retryConfig?: Partial<RetryConfig>
    } = {}
  ): Promise<T> => {
    const {
      loadingTitle = '处理中...',
      loadingDescription = '正在执行操作，请稍候',
      showProgress = false,
      successMessage,
      errorContext,
      retryConfig
    } = options

    try {
      incrementActiveRequests()
      
      if (showProgress) {
        showLoadingWithProgress(loadingTitle, loadingDescription)
      } else {
        showLoading(loadingTitle, loadingDescription)
      }

      const result = retryConfig 
        ? await withRetry(operation, retryConfig, errorContext)
        : await operation()

      hideLoading()
      
      if (successMessage) {
        showSuccess('操作成功', successMessage)
      }

      return result
    } catch (error) {
      hideLoading()
      handleError(error, errorContext)
      throw error
    } finally {
      decrementActiveRequests()
    }
  }

  // 批量操作处理
  const executeBatchWithProgress = async <T>(
    operations: Array<() => Promise<T>>,
    options: {
      batchTitle?: string
      batchDescription?: string
      successMessage?: string
      onProgress?: (completed: number, total: number) => void
      errorContext?: ErrorContext
    } = {}
  ): Promise<T[]> => {
    const {
      batchTitle = '批量处理中...',
      batchDescription = '正在批量执行操作，请稍候',
      successMessage,
      onProgress,
      errorContext
    } = options

    const results: T[] = []
    const total = operations.length

    try {
      incrementActiveRequests()
      showLoadingWithProgress(batchTitle, batchDescription)

      for (let i = 0; i < operations.length; i++) {
        const progress = Math.round(((i + 1) / total) * 100)
        updateLoadingProgress(
          progress,
          `正在处理第 ${i + 1} 项，共 ${total} 项`,
          Math.round((total - i - 1) * 2) // 估算剩余时间
        )

        try {
          const result = await operations[i]()
          results.push(result)
          
          if (onProgress) {
            onProgress(i + 1, total)
          }
        } catch (error) {
          console.error(`Batch operation ${i + 1} failed:`, error)
          handleError(error, {
            ...errorContext,
            additionalData: { batchIndex: i + 1, total }
          })
        }
      }

      hideLoading()
      
      if (successMessage) {
        showSuccess('批量操作完成', successMessage)
      }

      return results
    } catch (error) {
      hideLoading()
      handleError(error, errorContext)
      throw error
    } finally {
      decrementActiveRequests()
    }
  }

  return {
    // 状态
    isOnline,
    systemStatus,
    notifications: computed(() => globalState.value.notifications),
    unreadNotifications,
    hasActiveRequests,
    
    // 基础方法
    updateActivity,
    addNotification,
    markNotificationRead,
    markAllNotificationsRead,
    removeNotification,
    clearNotifications,
    setSystemStatus,
    
    // 加载状态管理
    showLoading,
    showLoadingWithProgress,
    updateLoadingProgress,
    hideLoading,
    showPageLoading,
    hidePageLoading,
    
    // 反馈消息
    showSuccess,
    showWarning,
    showError,
    showInfo,
    
    // 任务管理
    addTask,
    updateTask,
    removeTask,
    
    // 增强操作
    executeWithLoading,
    executeBatchWithProgress
  }
}

export type { GlobalState }