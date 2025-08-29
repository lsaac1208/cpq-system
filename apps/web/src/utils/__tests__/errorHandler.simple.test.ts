/**
 * ErrorHandler工具函数简化测试
 * 测试实际存在的错误处理函数
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { 
  handleApiError,
  formatValidationErrors,
  validateField,
  validateFields,
  enhancedErrorHandler
} from '../errorHandler'

// Mock Element Plus components with proper structure
vi.mock('element-plus', () => {
  const mockElMessage = vi.fn()
  mockElMessage.error = vi.fn()
  mockElMessage.success = vi.fn()
  mockElMessage.warning = vi.fn()
  mockElMessage.info = vi.fn()

  return {
    ElMessage: mockElMessage,
    ElNotification: vi.fn(),
    ElMessageBox: {
      alert: vi.fn()
    }
  }
})

describe('ErrorHandler Utils - Simple Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('formatValidationErrors', () => {
    it('应该格式化数组格式的验证错误', () => {
      const errors = {
        username: ['用户名不能为空', '用户名长度至少3位'],
        email: ['邮箱格式不正确']
      }

      const result = formatValidationErrors(errors)

      expect(result.username).toBeDefined()
      expect(result.email).toBeDefined()
      // 数组会被转换为带索引的对象
      expect(result.email.error_0).toBe('邮箱格式不正确')
      expect(result.username.error_0).toBe('用户名不能为空')
      expect(result.username.error_1).toBe('用户名长度至少3位')
    })

    it('应该处理对象格式的验证错误', () => {
      const errors = {
        user: {
          name: '用户名无效',
          age: '年龄必须是数字'
        }
      }

      const result = formatValidationErrors(errors)

      expect(result.user).toBeDefined()
      expect(result.user.name).toBe('用户名无效')
      expect(result.user.age).toBe('年龄必须是数字')
    })

    it('应该处理空错误对象', () => {
      const result1 = formatValidationErrors(null)
      const result2 = formatValidationErrors({})

      expect(Object.keys(result1)).toHaveLength(0)
      expect(Object.keys(result2)).toHaveLength(0)
    })
  })

  describe('validateField', () => {
    it('应该验证必填字段', () => {
      const result = validateField('', { required: true }, '用户名')
      expect(result).toBe('用户名不能为空')

      const result2 = validateField('test', { required: true }, '用户名')
      expect(result2).toBeNull()
    })

    it('应该验证最小长度', () => {
      const result = validateField('ab', { minLength: 3 }, '用户名')
      expect(result).toBe('用户名不能少于3个字符')

      const result2 = validateField('abcd', { minLength: 3 }, '用户名')
      expect(result2).toBeNull()
    })

    it('应该验证邮箱格式', () => {
      const result = validateField('invalid-email', { email: true }, '邮箱')
      expect(result).toBe('请输入有效的邮箱地址')

      const result2 = validateField('test@example.com', { email: true }, '邮箱')
      expect(result2).toBeNull()
    })

    it('应该验证数字格式', () => {
      const result = validateField('abc', { numeric: true }, '年龄')
      expect(result).toBe('年龄必须是数字')

      const result2 = validateField('25', { numeric: true }, '年龄')
      expect(result2).toBeNull()
    })

    it('应该验证数字范围', () => {
      const result = validateField('5', { numeric: true, min: 10 }, '年龄')
      expect(result).toBe('年龄不能小于10')

      const result2 = validateField('150', { numeric: true, max: 100 }, '年龄')
      expect(result2).toBe('年龄不能大于100')

      const result3 = validateField('25', { numeric: true, min: 10, max: 100 }, '年龄')
      expect(result3).toBeNull()
    })
  })

  describe('validateFields', () => {
    it('应该验证多个字段', () => {
      const data = {
        username: 'ab',
        email: 'invalid-email',
        age: 'not-a-number'
      }

      const validations = {
        username: { required: true, minLength: 3 },
        email: { required: true, email: true },
        age: { numeric: true }
      }

      const result = validateFields(data, validations)

      expect(result.username).toBe('username不能少于3个字符')
      expect(result.email).toBe('请输入有效的邮箱地址')
      expect(result.age).toBe('age必须是数字')
    })

    it('应该只返回有错误的字段', () => {
      const data = {
        username: 'validuser',
        email: 'test@example.com',
        age: 'not-a-number'
      }

      const validations = {
        username: { required: true, minLength: 3 },
        email: { required: true, email: true },
        age: { numeric: true }
      }

      const result = validateFields(data, validations)

      expect(result.username).toBeUndefined()
      expect(result.email).toBeUndefined()
      expect(result.age).toBe('age必须是数字')
    })
  })

  describe('enhancedErrorHandler', () => {
    it('应该处理HTTP响应错误', () => {
      const error = {
        response: {
          status: 400,
          data: { error: '请求参数错误' }
        }
      }

      const result = enhancedErrorHandler.handle(error)

      expect(result.type).toBe('business')
      expect(result.message).toBe('请求参数错误')
      expect(result.code).toBe(400)
    })

    it('应该处理网络错误', () => {
      const error = {
        request: {},
        message: 'Network Error'
      }

      const result = enhancedErrorHandler.handle(error)

      expect(result.type).toBe('network')
      expect(result.message).toBe('网络连接失败，请检查网络设置')
      expect(result.severity).toBe('high')
    })

    it('应该处理一般JavaScript错误', () => {
      const error = new Error('Something went wrong')

      const result = enhancedErrorHandler.handle(error)

      expect(result.message).toBe('Something went wrong')
      expect(result.type).toBe('business')
    })

    it('应该处理权限相关错误', () => {
      const error = {
        response: {
          status: 401,
          data: { error: '未授权访问' }
        }
      }

      const result = enhancedErrorHandler.handle(error)

      expect(result.type).toBe('permission')
      expect(result.code).toBe(401)
      expect(result.message).toBe('未授权访问')
    })

    it('应该处理验证错误', () => {
      const error = {
        response: {
          status: 422,
          data: { error: '数据验证失败' }
        }
      }

      const result = enhancedErrorHandler.handle(error)

      expect(result.type).toBe('validation')
      expect(result.code).toBe(422)
      expect(result.severity).toBe('medium')
    })

    it('应该处理服务器错误', () => {
      const error = {
        response: {
          status: 500,
          data: { error: '服务器内部错误' }
        }
      }

      const result = enhancedErrorHandler.handle(error)

      expect(result.type).toBe('system')
      expect(result.code).toBe(500)
      expect(result.severity).toBe('high')
      expect(result.recoverable).toBe(true)
    })
  })

  describe('错误统计和日志', () => {
    it('应该记录错误统计信息', () => {
      // 清除之前的错误日志
      enhancedErrorHandler.clearErrorLog()

      // 添加一些错误
      enhancedErrorHandler.handle(new Error('Test error 1'))
      enhancedErrorHandler.handle({ response: { status: 404 } })
      enhancedErrorHandler.handle({ response: { status: 500 } })

      const stats = enhancedErrorHandler.getErrorStats()

      expect(stats.totalErrors).toBeGreaterThanOrEqual(3)
      expect(stats.errorsByType).toBeDefined()
      expect(stats.errorsBySeverity).toBeDefined()
    })

    it('应该获取错误日志', () => {
      enhancedErrorHandler.clearErrorLog()

      enhancedErrorHandler.handle(new Error('Test error'))
      const errorLog = enhancedErrorHandler.getErrorLog()

      expect(errorLog).toHaveLength(1)
      expect(errorLog[0].message).toBe('Test error')
    })

    it('应该清除错误日志', () => {
      enhancedErrorHandler.handle(new Error('Test error'))
      enhancedErrorHandler.clearErrorLog()

      const stats = enhancedErrorHandler.getErrorStats()
      const errorLog = enhancedErrorHandler.getErrorLog()

      expect(stats.totalErrors).toBe(0)
      expect(errorLog).toHaveLength(0)
    })
  })

  describe('边界情况', () => {
    it('应该处理null和undefined错误', () => {
      const result1 = enhancedErrorHandler.handle(null)
      const result2 = enhancedErrorHandler.handle(undefined)

      expect(result1.type).toBe('unknown')
      expect(result2.type).toBe('unknown')
    })

    it('应该处理字符串错误', () => {
      const result = enhancedErrorHandler.handle('Simple string error')

      expect(result.message).toBe('Simple string error')
      expect(result.type).toBe('business')
    })

    it('应该处理没有response.data的错误', () => {
      const error = {
        response: {
          status: 400
        }
      }

      const result = enhancedErrorHandler.handle(error)

      expect(result.type).toBe('business')
      expect(result.code).toBe(400)
      expect(result.message).toBe('请求参数错误')
    })
  })
})