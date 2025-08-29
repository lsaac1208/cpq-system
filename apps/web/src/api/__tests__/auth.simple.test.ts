/**
 * Auth API简化测试
 * 测试实际存在的authApi对象
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { authApi } from '../auth'

// Mock http module
vi.mock('../http', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

// Import the mocked http for assertions
import http from '../http'
const mockedHttp = vi.mocked(http)

describe('Auth API - Simple Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('authApi.login', () => {
    it('应该调用正确的API端点进行登录', async () => {
      const mockResponse = {
        user: { id: 1, username: 'testuser' },
        access_token: 'test-token'
      }

      mockedHttp.post.mockResolvedValueOnce(mockResponse)

      const loginData = {
        username: 'testuser',
        password: 'password123'
      }

      const result = await authApi.login(loginData)

      expect(mockedHttp.post).toHaveBeenCalledWith('/auth/login', loginData)
      expect(result).toEqual(mockResponse)
    })

    it('应该处理登录失败', async () => {
      const mockError = new Error('Login failed')
      mockedHttp.post.mockRejectedValueOnce(mockError)

      const loginData = {
        username: 'wronguser',
        password: 'wrongpass'
      }

      await expect(authApi.login(loginData)).rejects.toThrow('Login failed')
    })
  })

  describe('authApi.register', () => {
    it('应该调用正确的API端点进行注册', async () => {
      const mockResponse = {
        user: { id: 2, username: 'newuser' },
        message: '注册成功'
      }

      mockedHttp.post.mockResolvedValueOnce(mockResponse)

      const registerData = {
        username: 'newuser',
        email: 'new@example.com',
        password: 'password123'
      }

      const result = await authApi.register(registerData)

      expect(mockedHttp.post).toHaveBeenCalledWith('/auth/register', registerData)
      expect(result).toEqual(mockResponse)
    })

    it('应该处理注册失败', async () => {
      const mockError = new Error('Registration failed')
      mockedHttp.post.mockRejectedValueOnce(mockError)

      const registerData = {
        username: 'existinguser',
        email: 'existing@example.com',
        password: 'password123'
      }

      await expect(authApi.register(registerData)).rejects.toThrow('Registration failed')
    })
  })

  describe('authApi.refresh', () => {
    it('应该调用刷新token的API端点', async () => {
      const mockResponse = {
        access_token: 'new-access-token'
      }

      mockedHttp.post.mockResolvedValueOnce(mockResponse)

      const result = await authApi.refresh()

      expect(mockedHttp.post).toHaveBeenCalledWith('/auth/refresh')
      expect(result).toEqual(mockResponse)
    })

    it('应该处理刷新失败', async () => {
      const mockError = new Error('Refresh failed')
      mockedHttp.post.mockRejectedValueOnce(mockError)

      await expect(authApi.refresh()).rejects.toThrow('Refresh failed')
    })
  })

  describe('authApi.getCurrentUser', () => {
    it('应该获取当前用户信息', async () => {
      const mockResponse = {
        user: {
          id: 1,
          username: 'testuser',
          email: 'test@example.com'
        }
      }

      mockedHttp.get.mockResolvedValueOnce(mockResponse)

      const result = await authApi.getCurrentUser()

      expect(mockedHttp.get).toHaveBeenCalledWith('/auth/me')
      expect(result).toEqual(mockResponse)
    })

    it('应该处理获取用户信息失败', async () => {
      const mockError = new Error('Failed to get user')
      mockedHttp.get.mockRejectedValueOnce(mockError)

      await expect(authApi.getCurrentUser()).rejects.toThrow('Failed to get user')
    })
  })

  describe('API方法存在性验证', () => {
    it('应该具有所有必需的API方法', () => {
      expect(typeof authApi.login).toBe('function')
      expect(typeof authApi.register).toBe('function')
      expect(typeof authApi.refresh).toBe('function')
      expect(typeof authApi.getCurrentUser).toBe('function')
    })

    it('API方法应该返回Promise', () => {
      // Mock每个调用分别设置
      mockedHttp.post.mockResolvedValue({})
      mockedHttp.get.mockResolvedValue({})

      const loginPromise = authApi.login({ username: 'test', password: 'test' })
      const registerPromise = authApi.register({ username: 'test', email: 'test@test.com', password: 'test' })
      const refreshPromise = authApi.refresh()
      const getCurrentUserPromise = authApi.getCurrentUser()

      expect(loginPromise).toBeInstanceOf(Promise)
      expect(registerPromise).toBeInstanceOf(Promise)
      expect(refreshPromise).toBeInstanceOf(Promise)
      expect(getCurrentUserPromise).toBeInstanceOf(Promise)

      // 确保Promise能正常resolve
      return Promise.all([loginPromise, registerPromise, refreshPromise, getCurrentUserPromise])
    })
  })

  describe('错误处理', () => {
    it('应该传递网络错误', async () => {
      const networkError = {
        code: 'NETWORK_ERROR',
        message: 'Network Error'
      }

      mockedHttp.post.mockRejectedValueOnce(networkError)

      await expect(authApi.login({ username: 'test', password: 'test' }))
        .rejects.toEqual(networkError)
    })

    it('应该传递HTTP错误', async () => {
      const httpError = {
        response: {
          status: 401,
          data: { error: 'Unauthorized' }
        }
      }

      mockedHttp.post.mockRejectedValueOnce(httpError)

      await expect(authApi.login({ username: 'test', password: 'test' }))
        .rejects.toEqual(httpError)
    })
  })
})