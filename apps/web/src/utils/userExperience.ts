// 用户体验增强工具函数

import { ElMessage, ElNotification } from 'element-plus'

// 设备信息接口
export interface DeviceInfo {
  isMobile: boolean
  isTablet: boolean
  isDesktop: boolean
  isTouchDevice: boolean
  isIOS: boolean
  isAndroid: boolean
  screenWidth: number
  screenHeight: number
  pixelRatio: number
  orientation: 'portrait' | 'landscape'
  hasNotchSupport: boolean
}

// 性能指标接口
export interface PerformanceMetrics {
  loadTime: number
  renderTime: number
  interactionTime: number
  memoryUsage: number
  connectionType: string
  isSlowConnection: boolean
}

// 用户偏好接口
export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto'
  language: string
  fontSize: 'small' | 'medium' | 'large'
  reduceMotion: boolean
  highContrast: boolean
  notifications: boolean
  autoSave: boolean
}

class UserExperienceManager {
  private deviceInfo: DeviceInfo
  private performanceMetrics: PerformanceMetrics
  private userPreferences: UserPreferences
  private observers: Map<string, ResizeObserver | IntersectionObserver> = new Map()

  constructor() {
    this.deviceInfo = this.detectDevice()
    this.performanceMetrics = this.measurePerformance()
    this.userPreferences = this.loadUserPreferences()
    
    this.setupEventListeners()
    this.setupPerformanceMonitoring()
  }

  // 设备检测
  private detectDevice(): DeviceInfo {
    const userAgent = navigator.userAgent
    const screenWidth = window.innerWidth
    const screenHeight = window.innerHeight
    
    return {
      isMobile: screenWidth <= 768,
      isTablet: screenWidth > 768 && screenWidth <= 1024,
      isDesktop: screenWidth > 1024,
      isTouchDevice: 'ontouchstart' in window || navigator.maxTouchPoints > 0,
      isIOS: /iPad|iPhone|iPod/.test(userAgent),
      isAndroid: /Android/.test(userAgent),
      screenWidth,
      screenHeight,
      pixelRatio: window.devicePixelRatio || 1,
      orientation: screenWidth > screenHeight ? 'landscape' : 'portrait',
      hasNotchSupport: CSS.supports('padding: max(0px)')
    }
  }

  // 性能监测
  private measurePerformance(): PerformanceMetrics {
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
    const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection
    
    return {
      loadTime: navigation ? navigation.loadEventEnd - navigation.loadEventStart : 0,
      renderTime: navigation ? navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart : 0,
      interactionTime: 0,
      memoryUsage: (performance as any).memory ? (performance as any).memory.usedJSHeapSize : 0,
      connectionType: connection ? connection.effectiveType : 'unknown',
      isSlowConnection: connection ? connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g' : false
    }
  }

  // 加载用户偏好
  private loadUserPreferences(): UserPreferences {
    const stored = localStorage.getItem('userPreferences')
    const defaults: UserPreferences = {
      theme: 'auto',
      language: 'zh',
      fontSize: 'medium',
      reduceMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
      highContrast: window.matchMedia('(prefers-contrast: high)').matches,
      notifications: true,
      autoSave: true
    }
    
    return stored ? { ...defaults, ...JSON.parse(stored) } : defaults
  }

  // 保存用户偏好
  private saveUserPreferences(): void {
    localStorage.setItem('userPreferences', JSON.stringify(this.userPreferences))
  }

  // 设置事件监听器
  private setupEventListeners(): void {
    // 屏幕方向变化
    window.addEventListener('orientationchange', () => {
      setTimeout(() => {
        this.deviceInfo = this.detectDevice()
        this.adaptToDevice()
      }, 100)
    })

    // 窗口大小变化
    window.addEventListener('resize', this.debounce(() => {
      this.deviceInfo = this.detectDevice()
      this.adaptToDevice()
    }, 250))

    // 网络状态变化
    window.addEventListener('online', () => {
      ElMessage.success('网络连接已恢复')
    })

    window.addEventListener('offline', () => {
      ElMessage.warning('网络连接已断开，部分功能可能不可用')
    })

    // 可见性变化
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        // 页面隐藏时的优化
        this.pauseNonEssentialTasks()
      } else {
        // 页面显示时的恢复
        this.resumeNonEssentialTasks()
      }
    })
  }

  // 性能监控设置
  private setupPerformanceMonitoring(): void {
    // 长任务监控
    if ('PerformanceObserver' in window) {
      try {
        const longTaskObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.duration > 50) {
              console.warn('Long task detected:', entry.duration, 'ms')
            }
          }
        })
        longTaskObserver.observe({ entryTypes: ['longtask'] })
      } catch (e) {
        // Ignore if longtask is not supported
      }

      // 首次内容绘制监控
      try {
        const paintObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.name === 'first-contentful-paint') {
              console.log('First Contentful Paint:', entry.startTime, 'ms')
            }
          }
        })
        paintObserver.observe({ entryTypes: ['paint'] })
      } catch (e) {
        // Ignore if paint timing is not supported
      }
    }
  }

  // 防抖函数
  private debounce<T extends (...args: any[]) => any>(func: T, wait: number): T {
    let timeout: NodeJS.Timeout
    return ((...args: any[]) => {
      clearTimeout(timeout)
      timeout = setTimeout(() => func.apply(this, args), wait)
    }) as T
  }

  // 适配设备
  private adaptToDevice(): void {
    const body = document.body
    
    // 添加设备类名
    body.classList.remove('mobile', 'tablet', 'desktop', 'touch', 'no-touch')
    
    if (this.deviceInfo.isMobile) body.classList.add('mobile')
    if (this.deviceInfo.isTablet) body.classList.add('tablet')
    if (this.deviceInfo.isDesktop) body.classList.add('desktop')
    if (this.deviceInfo.isTouchDevice) body.classList.add('touch')
    else body.classList.add('no-touch')

    // 设置CSS变量
    document.documentElement.style.setProperty('--screen-width', `${this.deviceInfo.screenWidth}px`)
    document.documentElement.style.setProperty('--screen-height', `${this.deviceInfo.screenHeight}px`)
    document.documentElement.style.setProperty('--pixel-ratio', this.deviceInfo.pixelRatio.toString())
  }

  // 暂停非必要任务
  private pauseNonEssentialTasks(): void {
    // 暂停动画
    document.querySelectorAll('.pause-when-hidden').forEach(el => {
      (el as HTMLElement).style.animationPlayState = 'paused'
    })
  }

  // 恢复非必要任务
  private resumeNonEssentialTasks(): void {
    // 恢复动画
    document.querySelectorAll('.pause-when-hidden').forEach(el => {
      (el as HTMLElement).style.animationPlayState = 'running'
    })
  }

  // 获取设备信息
  getDeviceInfo(): DeviceInfo {
    return { ...this.deviceInfo }
  }

  // 获取性能指标
  getPerformanceMetrics(): PerformanceMetrics {
    return { ...this.performanceMetrics }
  }

  // 获取用户偏好
  getUserPreferences(): UserPreferences {
    return { ...this.userPreferences }
  }

  // 更新用户偏好
  updateUserPreferences(updates: Partial<UserPreferences>): void {
    this.userPreferences = { ...this.userPreferences, ...updates }
    this.saveUserPreferences()
    this.applyUserPreferences()
  }

  // 应用用户偏好
  private applyUserPreferences(): void {
    const { theme, fontSize, reduceMotion, highContrast } = this.userPreferences
    const root = document.documentElement

    // 主题
    root.setAttribute('data-theme', theme)

    // 字体大小
    root.setAttribute('data-font-size', fontSize)

    // 减少动画
    if (reduceMotion) {
      root.classList.add('reduce-motion')
    } else {
      root.classList.remove('reduce-motion')
    }

    // 高对比度
    if (highContrast) {
      root.classList.add('high-contrast')
    } else {
      root.classList.remove('high-contrast')
    }
  }

  // 智能提示
  showSmartNotification(
    message: string,
    type: 'success' | 'warning' | 'error' | 'info' = 'info',
    options: {
      duration?: number
      showOnMobile?: boolean
      actionText?: string
      actionHandler?: () => void
    } = {}
  ): void {
    const { duration = 3000, showOnMobile = true, actionText, actionHandler } = options

    // 移动端使用不同的通知方式
    if (this.deviceInfo.isMobile && showOnMobile) {
      if (actionText && actionHandler) {
        ElNotification({
          title: message,
          type,
          duration,
          showClose: true,
          onClick: actionHandler
        })
      } else {
        ElMessage({
          message,
          type,
          duration,
          showClose: true
        })
      }
    } else {
      ElMessage({
        message,
        type,
        duration
      })
    }
  }

  // 智能加载
  setupIntelligentLoading(
    element: HTMLElement,
    loadHandler: () => void,
    options: {
      rootMargin?: string
      threshold?: number
    } = {}
  ): void {
    const { rootMargin = '50px', threshold = 0.1 } = options

    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              loadHandler()
              observer.unobserve(element)
            }
          })
        },
        { rootMargin, threshold }
      )

      observer.observe(element)
      this.observers.set(`intersection-${Date.now()}`, observer)
    } else {
      // 降级处理
      loadHandler()
    }
  }

  // 响应式字体大小
  setupResponsiveFontSize(): void {
    const updateFontSize = () => {
      const baseSize = this.deviceInfo.isMobile ? 14 : 16
      const scaleFactor = Math.min(this.deviceInfo.screenWidth / 1200, 1.2)
      const fontSize = Math.max(baseSize * scaleFactor, 12)
      
      document.documentElement.style.setProperty('--base-font-size', `${fontSize}px`)
    }

    updateFontSize()
    window.addEventListener('resize', this.debounce(updateFontSize, 250))
  }

  // 键盘导航优化
  enhanceKeyboardNavigation(): void {
    // 跳过链接
    const skipLink = document.createElement('a')
    skipLink.href = '#main-content'
    skipLink.textContent = '跳到主内容'
    skipLink.className = 'skip-link'
    skipLink.style.cssText = `
      position: absolute;
      top: -40px;
      left: 6px;
      background: #000;
      color: #fff;
      padding: 8px;
      text-decoration: none;
      z-index: 9999;
      transition: top 0.3s;
    `
    
    skipLink.addEventListener('focus', () => {
      skipLink.style.top = '6px'
    })
    
    skipLink.addEventListener('blur', () => {
      skipLink.style.top = '-40px'
    })
    
    document.body.insertBefore(skipLink, document.body.firstChild)

    // 焦点管理
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        document.body.classList.add('keyboard-navigation')
      }
    })

    document.addEventListener('mousedown', () => {
      document.body.classList.remove('keyboard-navigation')
    })
  }

  // 触觉反馈 (支持的设备)
  provideTactileFeedback(type: 'light' | 'medium' | 'heavy' = 'light'): void {
    if ('vibrate' in navigator && this.deviceInfo.isTouchDevice) {
      const patterns = {
        light: [10],
        medium: [20],
        heavy: [30]
      }
      navigator.vibrate(patterns[type])
    }
  }

  // 清理资源
  cleanup(): void {
    this.observers.forEach(observer => {
      observer.disconnect()
    })
    this.observers.clear()
  }

  // 获取建议的操作
  getRecommendations(): string[] {
    const recommendations: string[] = []

    if (this.performanceMetrics.isSlowConnection) {
      recommendations.push('建议在较好的网络环境下使用以获得最佳体验')
    }

    if (this.deviceInfo.isMobile) {
      recommendations.push('移动端体验已优化，支持触摸操作')
    }

    if (this.userPreferences.reduceMotion) {
      recommendations.push('已为您减少动画效果')
    }

    if (!this.userPreferences.notifications) {
      recommendations.push('您可以在设置中开启通知以获得及时提醒')
    }

    return recommendations
  }
}

// 创建全局实例
export const uxManager = new UserExperienceManager()

// 便捷函数
export const getDeviceInfo = () => uxManager.getDeviceInfo()
export const getPerformanceMetrics = () => uxManager.getPerformanceMetrics()
export const getUserPreferences = () => uxManager.getUserPreferences()
export const updateUserPreferences = (updates: Partial<UserPreferences>) => 
  uxManager.updateUserPreferences(updates)
export const showSmartNotification = (
  message: string, 
  type?: 'success' | 'warning' | 'error' | 'info', 
  options?: any
) => uxManager.showSmartNotification(message, type, options)

export default uxManager