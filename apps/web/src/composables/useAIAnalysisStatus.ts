/**
 * AI分析状态管理 Composable
 * 提供实时状态反馈、智能重试和等待时间估算
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { showMessage } from '@/utils/message'

// 服务状态类型
export interface ServiceStatus {
  status: 'healthy' | 'degraded' | 'unavailable' | 'unknown'
  queue_size: number
  processing_count: number
  max_concurrent: number
  estimated_wait_time?: number
  recommendations?: string[]
  last_check: string
}

// 分析状态类型
export interface AnalysisStatus {
  isAnalyzing: boolean
  estimatedTime: number
  actualStartTime: number | null
  remainingTime: number
  confidence: number // 时间估算的置信度
}

export function useAIAnalysisStatus() {
  // 响应式状态
  const serviceStatus = ref<ServiceStatus>({
    status: 'unknown',
    queue_size: 0,
    processing_count: 0,
    max_concurrent: 3,
    last_check: new Date().toISOString()
  })

  const analysisStatus = ref<AnalysisStatus>({
    isAnalyzing: false,
    estimatedTime: 0,
    actualStartTime: null,
    remainingTime: 0,
    confidence: 0
  })

  const networkStatus = ref({
    isOnline: navigator.onLine,
    latency: 0,
    lastCheck: Date.now()
  })

  // 计算属性
  const isServiceHealthy = computed(() => serviceStatus.value.status === 'healthy')
  const isServiceAvailable = computed(() => serviceStatus.value.status !== 'unavailable')
  const queueUtilization = computed(() => 
    Math.round((serviceStatus.value.queue_size / 50) * 100) // 假设队列最大50
  )
  const processingUtilization = computed(() => 
    Math.round((serviceStatus.value.processing_count / serviceStatus.value.max_concurrent) * 100)
  )

  const serviceStatusText = computed(() => {
    switch (serviceStatus.value.status) {
      case 'healthy': return '服务正常'
      case 'degraded': return '服务繁忙'
      case 'unavailable': return '服务不可用'
      default: return '检查中...'
    }
  })

  const serviceStatusColor = computed(() => {
    switch (serviceStatus.value.status) {
      case 'healthy': return 'success'
      case 'degraded': return 'warning'
      case 'unavailable': return 'danger'
      default: return 'info'
    }
  })

  // 状态检查器
  let statusCheckInterval: number | null = null
  let analysisTimer: number | null = null

  // 方法
  const checkServiceStatus = async (): Promise<ServiceStatus> => {
    try {
      const response = await fetch('/api/v1/system/health')
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      
      const data = await response.json()
      
      const status: ServiceStatus = {
        status: data.status === 'healthy' ? 'healthy' : 
                data.status === 'warning' ? 'degraded' : 'unavailable',
        queue_size: data.ai_analysis?.queue_size || 0,
        processing_count: data.ai_analysis?.processing_count || 0,
        max_concurrent: data.ai_analysis?.max_concurrent || 3,
        estimated_wait_time: calculateWaitTime(data.ai_analysis?.queue_size || 0),
        last_check: new Date().toISOString()
      }

      // 获取推荐信息
      if (status.status !== 'healthy') {
        status.recommendations = generateRecommendations(status)
      }

      serviceStatus.value = status
      return status
      
    } catch (error) {
      console.error('服务状态检查失败:', error)
      serviceStatus.value = {
        status: 'unknown',
        queue_size: 0,
        processing_count: 0,
        max_concurrent: 3,
        last_check: new Date().toISOString()
      }
      return serviceStatus.value
    }
  }

  const calculateWaitTime = (queueSize: number): number => {
    // 基于队列长度估算等待时间 (秒)
    const avgProcessingTime = 45 // 平均45秒处理一个文档
    const concurrentProcessing = serviceStatus.value.max_concurrent
    return Math.ceil((queueSize * avgProcessingTime) / concurrentProcessing)
  }

  const generateRecommendations = (status: ServiceStatus): string[] => {
    const recommendations: string[] = []
    
    if (status.queue_size > 20) {
      recommendations.push('当前队列较长，建议稍后重试')
    }
    
    if (status.processing_count >= status.max_concurrent) {
      recommendations.push('服务器处理能力已满，请等待当前任务完成')
    }
    
    if (status.status === 'degraded') {
      recommendations.push('服务正在降级模式运行，处理时间可能延长')
    }
    
    if (status.status === 'unavailable') {
      recommendations.push('服务暂时不可用，请检查网络连接或稍后重试')
    }
    
    return recommendations
  }

  const estimateAnalysisTime = (fileSize: number, fileType: string): number => {
    // 基于文件大小和类型估算处理时间
    let baseTime = 30 // 基础30秒
    
    // 文件大小影响 (MB)
    const sizeMB = fileSize / (1024 * 1024)
    baseTime += sizeMB * 5 // 每MB增加5秒
    
    // 文件类型影响
    switch (fileType.toLowerCase()) {
      case 'pdf':
        baseTime *= 1.5 // PDF需要更多处理时间
        break
      case 'docx':
      case 'doc':
        baseTime *= 1.3
        break
      case 'txt':
        baseTime *= 0.8 // 纯文本处理更快
        break
      case 'png':
      case 'jpg':
      case 'jpeg':
        baseTime *= 2.0 // 图片OCR需要更多时间
        break
    }
    
    // 服务状态影响
    if (serviceStatus.value.status === 'degraded') {
      baseTime *= 1.5
    }
    
    // 队列等待时间
    const waitTime = serviceStatus.value.estimated_wait_time || 0
    
    return Math.round(baseTime + waitTime)
  }

  const startAnalysisTimer = (fileSize: number, fileType: string) => {
    const estimatedTime = estimateAnalysisTime(fileSize, fileType)
    
    analysisStatus.value = {
      isAnalyzing: true,
      estimatedTime,
      actualStartTime: Date.now(),
      remainingTime: estimatedTime,
      confidence: calculateConfidence(estimatedTime)
    }
    
    // 启动倒计时
    analysisTimer = window.setInterval(() => {
      const elapsed = (Date.now() - (analysisStatus.value.actualStartTime || 0)) / 1000
      const remaining = Math.max(0, analysisStatus.value.estimatedTime - elapsed)
      
      analysisStatus.value.remainingTime = remaining
      
      // 调整置信度
      if (elapsed > analysisStatus.value.estimatedTime * 1.2) {
        analysisStatus.value.confidence = Math.max(20, analysisStatus.value.confidence - 10)
      }
      
    }, 1000)
  }

  const stopAnalysisTimer = () => {
    if (analysisTimer) {
      clearInterval(analysisTimer)
      analysisTimer = null
    }
    
    analysisStatus.value.isAnalyzing = false
    analysisStatus.value.remainingTime = 0
  }

  const calculateConfidence = (estimatedTime: number): number => {
    // 基于历史数据和当前状态计算置信度
    let confidence = 75 // 基础置信度75%
    
    if (serviceStatus.value.status === 'healthy') {
      confidence += 15
    } else if (serviceStatus.value.status === 'degraded') {
      confidence -= 20
    } else {
      confidence -= 40
    }
    
    // 网络状况影响
    if (networkStatus.value.isOnline && networkStatus.value.latency < 200) {
      confidence += 10
    } else {
      confidence -= 15
    }
    
    return Math.max(10, Math.min(95, confidence))
  }

  const checkNetworkLatency = async () => {
    const start = Date.now()
    try {
      await fetch('/api/v1/system/health', { method: 'HEAD' })
      networkStatus.value.latency = Date.now() - start
      networkStatus.value.lastCheck = Date.now()
    } catch (error) {
      networkStatus.value.latency = 9999 // 表示网络异常
    }
  }

  const getRetryRecommendation = (errorType?: string): {
    shouldRetry: boolean
    retryDelay: number
    reason: string
  } => {
    const queueSize = serviceStatus.value.queue_size
    const serviceHealth = serviceStatus.value.status
    
    // 基于错误类型和服务状态决定重试策略
    if (errorType === 'timeout') {
      if (serviceHealth === 'healthy' && queueSize < 10) {
        return {
          shouldRetry: true,
          retryDelay: 5000, // 5秒后重试
          reason: '服务状态良好，建议立即重试'
        }
      } else {
        return {
          shouldRetry: true,
          retryDelay: 30000, // 30秒后重试
          reason: '服务繁忙，建议稍后重试'
        }
      }
    }
    
    if (errorType === 'network') {
      return {
        shouldRetry: networkStatus.value.isOnline,
        retryDelay: networkStatus.value.isOnline ? 10000 : 60000,
        reason: networkStatus.value.isOnline ? '网络已恢复，可以重试' : '请检查网络连接'
      }
    }
    
    if (serviceHealth === 'unavailable') {
      return {
        shouldRetry: false,
        retryDelay: 0,
        reason: '服务暂时不可用，请稍后再试'
      }
    }
    
    return {
      shouldRetry: true,
      retryDelay: 15000,
      reason: '可以重试，建议等待15秒'
    }
  }

  const formatTime = (seconds: number): string => {
    if (seconds < 60) {
      return `${Math.round(seconds)}秒`
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60)
      const remainingSeconds = Math.round(seconds % 60)
      return `${minutes}分${remainingSeconds}秒`
    } else {
      const hours = Math.floor(seconds / 3600)
      const minutes = Math.floor((seconds % 3600) / 60)
      return `${hours}小时${minutes}分钟`
    }
  }

  // 生命周期管理
  const startStatusMonitoring = () => {
    // 立即检查一次
    checkServiceStatus()
    checkNetworkLatency()
    
    // 定期检查服务状态 (每30秒)
    statusCheckInterval = window.setInterval(() => {
      checkServiceStatus()
      checkNetworkLatency()
    }, 30000)
  }

  const stopStatusMonitoring = () => {
    if (statusCheckInterval) {
      clearInterval(statusCheckInterval)
      statusCheckInterval = null
    }
    stopAnalysisTimer()
  }

  // 网络状态监听
  const handleOnline = () => {
    networkStatus.value.isOnline = true
    checkServiceStatus() // 网络恢复时立即检查服务状态
    showMessage.success('网络连接已恢复')
  }

  const handleOffline = () => {
    networkStatus.value.isOnline = false
    showMessage.warning('网络连接已断开')
  }

  onMounted(() => {
    startStatusMonitoring()
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
  })

  onUnmounted(() => {
    stopStatusMonitoring()
    window.removeEventListener('online', handleOnline)
    window.removeEventListener('offline', handleOffline)
  })

  return {
    // 状态
    serviceStatus: computed(() => serviceStatus.value),
    analysisStatus: computed(() => analysisStatus.value),
    networkStatus: computed(() => networkStatus.value),
    
    // 计算属性
    isServiceHealthy,
    isServiceAvailable,
    queueUtilization,
    processingUtilization,
    serviceStatusText,
    serviceStatusColor,
    
    // 方法
    checkServiceStatus,
    estimateAnalysisTime,
    startAnalysisTimer,
    stopAnalysisTimer,
    getRetryRecommendation,
    formatTime,
    startStatusMonitoring,
    stopStatusMonitoring
  }
}