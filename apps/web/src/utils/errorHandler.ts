/**
 * Centralized error handling utilities - Enhanced version
 */

import { ElMessage, ElNotification, ElMessageBox } from 'element-plus'

export interface ApiError {
  success: false
  message: string
  errors?: Record<string, string[]> | Record<string, string>
  status?: number
}

export interface ValidationErrors {
  [section: string]: {
    [field: string]: string
  }
}

/**
 * Format validation errors for display
 */
export function formatValidationErrors(errors: any): ValidationErrors {
  const formatted: ValidationErrors = {}
  
  if (!errors || typeof errors !== 'object') {
    return formatted
  }
  
  // Handle nested validation errors from API
  Object.keys(errors).forEach(section => {
    const sectionErrors = errors[section]
    
    if (Array.isArray(sectionErrors)) {
      // Handle array format: { field: ["error1", "error2"] }
      formatted[section] = {}
      sectionErrors.forEach((error: string, index: number) => {
        formatted[section][`error_${index}`] = error
      })
    } else if (typeof sectionErrors === 'object') {
      // Handle object format: { field: "error" } or { field: ["error1", "error2"] }
      formatted[section] = {}
      Object.keys(sectionErrors).forEach(field => {
        const fieldError = sectionErrors[field]
        if (Array.isArray(fieldError)) {
          formatted[section][field] = fieldError.join(', ')
        } else {
          formatted[section][field] = String(fieldError)
        }
      })
    } else {
      // Handle simple string errors
      formatted[section] = { general: String(sectionErrors) }
    }
  })
  
  return formatted
}

/**
 * Handle API errors with appropriate user feedback
 */
export function handleApiError(error: any, context?: string): void {
  console.error('API Error:', error)
  
  let message = '操作失败'
  let duration = 3000
  
  if (error?.response?.data) {
    const apiError = error.response.data as ApiError
    
    if (apiError.message) {
      message = apiError.message
    }
    
    // Handle validation errors
    if (apiError.errors) {
      const formattedErrors = formatValidationErrors(apiError.errors)
      const errorMessages: string[] = []
      
      Object.keys(formattedErrors).forEach(section => {
        Object.keys(formattedErrors[section]).forEach(field => {
          errorMessages.push(formattedErrors[section][field])
        })
      })
      
      if (errorMessages.length > 0) {
        // Show detailed validation errors in notification
        ElNotification({
          title: context ? `${context}失败` : '验证错误',
          message: errorMessages.join('\n'),
          type: 'error',
          duration: 5000,
          dangerouslyUseHTMLString: false
        })
        return
      }
    }
  } else if (error?.message) {
    message = error.message
  }
  
  // Add context to message if provided
  if (context) {
    message = `${context}: ${message}`
  }
  
  // Handle different error types
  if (error?.response?.status === 401) {
    message = '请重新登录'
    duration = 5000
  } else if (error?.response?.status === 403) {
    message = '权限不足'
    duration = 4000
  } else if (error?.response?.status === 404) {
    message = '资源不存在'
  } else if (error?.response?.status >= 500) {
    message = '服务器错误，请稍后重试'
    duration = 5000
  }
  
  ElMessage({
    message,
    type: 'error',
    duration
  })
}

/**
 * Handle network errors
 */
export function handleNetworkError(error: any): void {
  console.error('Network Error:', error)
  
  let message = '网络连接失败'
  
  if (error.code === 'NETWORK_ERROR') {
    message = '网络连接失败，请检查网络设置'
  } else if (error.code === 'TIMEOUT_ERROR') {
    message = '请求超时，请稍后重试'
  } else if (error.message?.includes('timeout')) {
    message = '请求超时'
  } else if (error.message?.includes('Network')) {
    message = '网络错误'
  }
  
  ElMessage({
    message,
    type: 'error',
    duration: 5000
  })
}

/**
 * Show success message
 */
export function showSuccess(message: string, context?: string): void {
  const fullMessage = context ? `${context}: ${message}` : message
  
  ElMessage({
    message: fullMessage,
    type: 'success',
    duration: 3000
  })
}

/**
 * Show warning message
 */
export function showWarning(message: string, context?: string): void {
  const fullMessage = context ? `${context}: ${message}` : message
  
  ElMessage({
    message: fullMessage,
    type: 'warning',
    duration: 4000
  })
}

/**
 * Show info message
 */
export function showInfo(message: string, context?: string): void {
  const fullMessage = context ? `${context}: ${message}` : message
  
  ElMessage({
    message: fullMessage,
    type: 'info',
    duration: 3000
  })
}

/**
 * Validate form data on client side
 */
export interface FieldValidation {
  required?: boolean
  minLength?: number
  maxLength?: number
  email?: boolean
  url?: boolean
  numeric?: boolean
  min?: number
  max?: number
  pattern?: RegExp
  custom?: (value: any) => string | null
}

export function validateField(value: any, validation: FieldValidation, fieldName: string): string | null {
  // Required validation
  if (validation.required && (!value || String(value).trim().length === 0)) {
    return `${fieldName}不能为空`
  }
  
  // Skip other validations if value is empty and not required
  if (!value || String(value).trim().length === 0) {
    return null
  }
  
  const stringValue = String(value).trim()
  
  // Length validations
  if (validation.minLength && stringValue.length < validation.minLength) {
    return `${fieldName}不能少于${validation.minLength}个字符`
  }
  
  if (validation.maxLength && stringValue.length > validation.maxLength) {
    return `${fieldName}不能超过${validation.maxLength}个字符`
  }
  
  // Email validation
  if (validation.email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(stringValue)) {
      return `请输入有效的邮箱地址`
    }
  }
  
  // URL validation
  if (validation.url) {
    try {
      new URL(stringValue)
    } catch {
      return `请输入有效的URL地址`
    }
  }
  
  // Numeric validations
  if (validation.numeric) {
    const numValue = Number(value)
    if (isNaN(numValue)) {
      return `${fieldName}必须是数字`
    }
    
    if (validation.min !== undefined && numValue < validation.min) {
      return `${fieldName}不能小于${validation.min}`
    }
    
    if (validation.max !== undefined && numValue > validation.max) {
      return `${fieldName}不能大于${validation.max}`
    }
  }
  
  // Pattern validation
  if (validation.pattern && !validation.pattern.test(stringValue)) {
    return `${fieldName}格式不正确`
  }
  
  // Custom validation
  if (validation.custom) {
    return validation.custom(value)
  }
  
  return null
}

/**
 * Validate multiple fields
 */
export function validateFields(data: Record<string, any>, validations: Record<string, FieldValidation>): Record<string, string> {
  const errors: Record<string, string> = {}
  
  Object.keys(validations).forEach(field => {
    const value = data[field]
    const validation = validations[field]
    const error = validateField(value, validation, field)
    
    if (error) {
      errors[field] = error
    }
  })
  
  return errors
}

// Enhanced error handling features

export interface ErrorContext {
  component?: string
  action?: string
  userId?: number
  timestamp?: number
  additionalData?: Record<string, any>
}

export interface ErrorInfo {
  code?: string | number
  message: string
  type: 'network' | 'validation' | 'business' | 'system' | 'permission' | 'unknown'
  severity: 'low' | 'medium' | 'high' | 'critical'
  recoverable: boolean
  context?: ErrorContext
}

export interface RetryConfig {
  maxRetries: number
  delay: number
  backoff: 'linear' | 'exponential'
  retryCondition?: (error: any) => boolean
}

class EnhancedErrorHandler {
  private errorLog: ErrorInfo[] = []
  private maxLogSize = 100
  private globalErrorCount = 0
  private lastErrorTime = 0

  /**
   * 处理错误的主要方法
   */
  handle(error: any, context?: ErrorContext): ErrorInfo {
    const errorInfo = this.parseError(error, context)
    this.logError(errorInfo)
    this.showUserFeedback(errorInfo)
    this.reportError(errorInfo)
    
    return errorInfo
  }

  /**
   * 解析错误信息
   */
  private parseError(error: any, context?: ErrorContext): ErrorInfo {
    let errorInfo: ErrorInfo = {
      message: '未知错误',
      type: 'unknown',
      severity: 'medium',
      recoverable: true,
      context: {
        ...context,
        timestamp: Date.now()
      }
    }

    if (error?.response) {
      // HTTP 响应错误
      const status = error.response.status
      const data = error.response.data

      errorInfo = {
        code: status,
        message: data?.message || data?.error || this.getHttpErrorMessage(status),
        type: this.getErrorTypeFromStatus(status),
        severity: this.getSeverityFromStatus(status),
        recoverable: this.isRecoverableFromStatus(status),
        context: errorInfo.context
      }
    } else if (error?.request) {
      // 网络请求错误
      errorInfo = {
        message: '网络连接失败，请检查网络设置',
        type: 'network',
        severity: 'high',
        recoverable: true,
        context: errorInfo.context
      }
    } else if (error instanceof Error) {
      // 一般错误
      errorInfo = {
        message: error.message,
        type: this.inferErrorType(error.message),
        severity: this.inferSeverity(error.message),
        recoverable: true,
        context: errorInfo.context
      }
    } else if (typeof error === 'string') {
      // 字符串错误
      errorInfo = {
        message: error,
        type: this.inferErrorType(error),
        severity: this.inferSeverity(error),
        recoverable: true,
        context: errorInfo.context
      }
    }

    return errorInfo
  }

  /**
   * 根据HTTP状态码获取错误消息
   */
  private getHttpErrorMessage(status: number): string {
    const messages: Record<number, string> = {
      400: '请求参数错误',
      401: '未授权访问，请重新登录',
      403: '权限不足，无法执行此操作',
      404: '请求的资源不存在',
      408: '请求超时，请重试',
      409: '数据冲突，请刷新后重试',
      422: '数据验证失败',
      429: '请求过于频繁，请稍后重试',
      500: '服务器内部错误',
      502: '网关错误',
      503: '服务暂时不可用',
      504: '网关超时'
    }
    return messages[status] || `请求失败 (状态码: ${status})`
  }

  /**
   * 根据HTTP状态码判断错误类型
   */
  private getErrorTypeFromStatus(status: number): ErrorInfo['type'] {
    if (status >= 400 && status < 500) {
      if (status === 401 || status === 403) return 'permission'
      if (status === 422) return 'validation'
      return 'business'
    }
    if (status >= 500) return 'system'
    return 'network'
  }

  /**
   * 根据HTTP状态码判断错误严重程度
   */
  private getSeverityFromStatus(status: number): ErrorInfo['severity'] {
    if (status === 401 || status === 403) return 'medium'
    if (status >= 500) return 'high'
    if (status === 429) return 'low'
    return 'medium'
  }

  /**
   * 根据HTTP状态码判断是否可恢复
   */
  private isRecoverableFromStatus(status: number): boolean {
    // 服务器错误和超时错误通常可以重试
    return status >= 500 || status === 408 || status === 429
  }

  /**
   * 根据错误消息推断错误类型
   */
  private inferErrorType(message: string): ErrorInfo['type'] {
    const lowerMessage = message.toLowerCase()
    
    if (lowerMessage.includes('network') || lowerMessage.includes('连接') || lowerMessage.includes('超时')) {
      return 'network'
    }
    if (lowerMessage.includes('permission') || lowerMessage.includes('权限') || lowerMessage.includes('unauthorized')) {
      return 'permission'
    }
    if (lowerMessage.includes('validation') || lowerMessage.includes('验证') || lowerMessage.includes('格式')) {
      return 'validation'
    }
    if (lowerMessage.includes('server') || lowerMessage.includes('服务器') || lowerMessage.includes('系统')) {
      return 'system'
    }
    
    return 'business'
  }

  /**
   * 根据错误消息推断严重程度
   */
  private inferSeverity(message: string): ErrorInfo['severity'] {
    const lowerMessage = message.toLowerCase()
    
    if (lowerMessage.includes('critical') || lowerMessage.includes('fatal') || lowerMessage.includes('严重')) {
      return 'critical'
    }
    if (lowerMessage.includes('server') || lowerMessage.includes('system') || lowerMessage.includes('服务器')) {
      return 'high'
    }
    if (lowerMessage.includes('validation') || lowerMessage.includes('format') || lowerMessage.includes('格式')) {
      return 'low'
    }
    
    return 'medium'
  }

  /**
   * 记录错误日志
   */
  private logError(errorInfo: ErrorInfo): void {
    this.errorLog.unshift(errorInfo)
    
    // 限制日志大小
    if (this.errorLog.length > this.maxLogSize) {
      this.errorLog = this.errorLog.slice(0, this.maxLogSize)
    }
    
    this.globalErrorCount++
    this.lastErrorTime = Date.now()
    
    // 在开发环境中打印到控制台
    if (import.meta.env.DEV) {
      console.error('Error handled:', errorInfo)
    }
  }

  /**
   * 显示用户反馈
   */
  private showUserFeedback(errorInfo: ErrorInfo): void {
    const { type, severity, message, recoverable } = errorInfo

    switch (severity) {
      case 'critical':
        ElMessageBox.alert(
          message,
          '系统错误',
          {
            type: 'error',
            showClose: false,
            confirmButtonText: '刷新页面',
            callback: () => {
              window.location.reload()
            }
          }
        )
        break

      case 'high':
        ElNotification({
          title: '操作失败',
          message: message,
          type: 'error',
          duration: 8000,
          showClose: true
        })
        break

      case 'medium':
        if (type === 'permission') {
          ElMessage({
            message: message,
            type: 'warning',
            duration: 5000,
            showClose: true
          })
        } else {
          ElMessage.error({
            message: message,
            duration: 5000,
            showClose: true
          })
        }
        break

      case 'low':
        ElMessage({
          message: message,
          type: 'warning',
          duration: 3000
        })
        break
    }
  }

  /**
   * 上报错误（可以发送到监控系统）
   */
  private reportError(errorInfo: ErrorInfo): void {
    // 这里可以集成错误监控服务，如 Sentry
    if (errorInfo.severity === 'critical' || errorInfo.severity === 'high') {
      // 发送到错误监控服务
      this.sendToMonitoring(errorInfo)
    }
  }

  /**
   * 发送错误到监控系统
   */
  private sendToMonitoring(errorInfo: ErrorInfo): void {
    // 模拟发送到监控系统
    if (import.meta.env.PROD) {
      // 实际项目中这里会调用监控服务的API
      console.warn('Error would be sent to monitoring:', errorInfo)
    }
  }

  /**
   * 带重试的异步操作
   */
  async withRetry<T>(
    operation: () => Promise<T>,
    retryConfig: Partial<RetryConfig> = {},
    context?: ErrorContext
  ): Promise<T> {
    const config: RetryConfig = {
      maxRetries: 3,
      delay: 1000,
      backoff: 'exponential',
      retryCondition: (error) => {
        // 默认只重试网络错误和服务器错误
        const errorInfo = this.parseError(error)
        return errorInfo.recoverable && (errorInfo.type === 'network' || errorInfo.type === 'system')
      },
      ...retryConfig
    }

    let lastError: any
    let delay = config.delay

    for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
      try {
        return await operation()
      } catch (error) {
        lastError = error
        
        // 如果是最后一次尝试，或者错误不满足重试条件
        if (attempt === config.maxRetries || !config.retryCondition!(error)) {
          break
        }

        // 等待指定时间后重试
        await this.delay(delay)
        
        // 计算下次延迟时间
        if (config.backoff === 'exponential') {
          delay *= 2
        } else {
          delay += config.delay
        }

        // 记录重试信息
        if (import.meta.env.DEV) {
          console.warn(`Retrying operation (attempt ${attempt + 1}/${config.maxRetries})`)
        }
      }
    }

    // 所有重试都失败了，处理最后的错误
    throw this.handle(lastError, context)
  }

  /**
   * 延迟函数
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  /**
   * 获取错误统计信息
   */
  getErrorStats(): {
    totalErrors: number
    recentErrors: number
    errorsByType: Record<string, number>
    errorsBySeverity: Record<string, number>
    lastErrorTime: number
  } {
    const recentTime = Date.now() - 24 * 60 * 60 * 1000 // 24小时前
    const recentErrors = this.errorLog.filter(error => 
      (error.context?.timestamp || 0) > recentTime
    )

    const errorsByType: Record<string, number> = {}
    const errorsBySeverity: Record<string, number> = {}

    this.errorLog.forEach(error => {
      errorsByType[error.type] = (errorsByType[error.type] || 0) + 1
      errorsBySeverity[error.severity] = (errorsBySeverity[error.severity] || 0) + 1
    })

    return {
      totalErrors: this.globalErrorCount,
      recentErrors: recentErrors.length,
      errorsByType,
      errorsBySeverity,
      lastErrorTime: this.lastErrorTime
    }
  }

  /**
   * 获取错误日志
   */
  getErrorLog(): ErrorInfo[] {
    return [...this.errorLog]
  }

  /**
   * 清除错误日志
   */
  clearErrorLog(): void {
    this.errorLog = []
    this.globalErrorCount = 0
    this.lastErrorTime = 0
  }
}

// 创建全局错误处理器实例
export const enhancedErrorHandler = new EnhancedErrorHandler()

// 便捷方法
export const handleError = (error: any, context?: ErrorContext) => 
  enhancedErrorHandler.handle(error, context)

export const withRetry = <T>(
  operation: () => Promise<T>,
  retryConfig?: Partial<RetryConfig>,
  context?: ErrorContext
) => enhancedErrorHandler.withRetry(operation, retryConfig, context)

export default {
  // 原有方法
  handleApiError,
  handleNetworkError,
  showSuccess,
  showWarning,
  showInfo,
  formatValidationErrors,
  validateField,
  validateFields,
  
  // 新增增强方法
  enhancedErrorHandler,
  handleError,
  withRetry
}