/**
 * Unit tests for Auth Store
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '../auth'
import { mockAuthApi, mockUser, mockLoginResponse, mockLocalStorage } from '@/test/mocks/api'
import type { LoginRequest, RegisterRequest } from '@/types/auth'

// Mock the auth API
vi.mock('@/api/auth', () => ({
  authApi: mockAuthApi
}))

// Mock localStorage
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage
})

describe('Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const authStore = useAuthStore()

      expect(authStore.user).toBeNull()
      expect(authStore.token).toBeNull()
      expect(authStore.refreshToken).toBeNull()
      expect(authStore.loading).toBe(false)
      expect(authStore.isAuthenticated).toBe(false)
    })
  })

  describe('Getters', () => {
    it('should return correct authentication status', () => {
      const authStore = useAuthStore()

      // Initially not authenticated
      expect(authStore.isAuthenticated).toBe(false)

      // Set token to simulate authentication
      authStore.$patch({ token: 'mock-token' })
      expect(authStore.isAuthenticated).toBe(true)
    })

    it('should return correct user role', () => {
      const authStore = useAuthStore()

      // Default role when no user
      expect(authStore.userRole).toBe('sales')

      // Set user with specific role
      authStore.$patch({ user: mockUser })
      expect(authStore.userRole).toBe(mockUser.role)
    })

    it('should return correct admin status', () => {
      const authStore = useAuthStore()

      // Not admin by default
      expect(authStore.isAdmin).toBe(false)

      // Set admin user
      authStore.$patch({ 
        user: { ...mockUser, role: 'admin' }
      })
      expect(authStore.isAdmin).toBe(true)
    })

    it('should return correct engineer status', () => {
      const authStore = useAuthStore()

      // Not engineer by default
      expect(authStore.isEngineer).toBe(false)

      // Set engineer user
      authStore.$patch({ 
        user: { ...mockUser, role: 'engineer' }
      })
      expect(authStore.isEngineer).toBe(true)
    })

    it('should return correct manager status', () => {
      const authStore = useAuthStore()

      // Not manager by default
      expect(authStore.isManager).toBe(false)

      // Set manager user
      authStore.$patch({ 
        user: { ...mockUser, role: 'manager' }
      })
      expect(authStore.isManager).toBe(true)
    })

    it('should return correct product edit permissions', () => {
      const authStore = useAuthStore()

      // Regular user cannot edit products
      authStore.$patch({ user: { ...mockUser, role: 'user' } })
      expect(authStore.canEditProducts).toBe(false)

      // Engineer can edit products
      authStore.$patch({ user: { ...mockUser, role: 'engineer' } })
      expect(authStore.canEditProducts).toBe(true)

      // Admin can edit products
      authStore.$patch({ user: { ...mockUser, role: 'admin' } })
      expect(authStore.canEditProducts).toBe(true)

      // Manager can edit products
      authStore.$patch({ user: { ...mockUser, role: 'manager' } })
      expect(authStore.canEditProducts).toBe(true)
    })

    it('should return correct product delete permissions', () => {
      const authStore = useAuthStore()

      // Regular user cannot delete products
      authStore.$patch({ user: { ...mockUser, role: 'user' } })
      expect(authStore.canDeleteProducts).toBe(false)

      // Engineer can delete products
      authStore.$patch({ user: { ...mockUser, role: 'engineer' } })
      expect(authStore.canDeleteProducts).toBe(true)

      // Admin can delete products
      authStore.$patch({ user: { ...mockUser, role: 'admin' } })
      expect(authStore.canDeleteProducts).toBe(true)

      // Manager can delete products
      authStore.$patch({ user: { ...mockUser, role: 'manager' } })
      expect(authStore.canDeleteProducts).toBe(true)
    })
  })

  describe('Actions', () => {
    describe('initializeAuth', () => {
      it('should initialize auth from localStorage', async () => {
        const authStore = useAuthStore()
        
        // Mock localStorage to return tokens
        mockLocalStorage.getItem.mockImplementation((key: string) => {
          if (key === 'cpq_access_token') return 'stored-token'
          if (key === 'cpq_refresh_token') return 'stored-refresh-token'
          return null
        })

        await authStore.initializeAuth()

        expect(mockAuthApi.getCurrentUser).toHaveBeenCalled()
        expect(authStore.token).toBe('stored-token')
        expect(authStore.refreshToken).toBe('stored-refresh-token')
        expect(authStore.user).toEqual(mockUser)
      })

      it('should clear auth if getCurrentUser fails', async () => {
        const authStore = useAuthStore()
        
        // Mock localStorage to return tokens
        mockLocalStorage.getItem.mockImplementation((key: string) => {
          if (key === 'cpq_access_token') return 'invalid-token'
          if (key === 'cpq_refresh_token') return 'invalid-refresh-token'
          return null
        })

        // Mock API to reject
        mockAuthApi.getCurrentUser.mockRejectedValueOnce(new Error('Token invalid'))

        await authStore.initializeAuth()

        expect(authStore.user).toBeNull()
        expect(authStore.token).toBeNull()
        expect(authStore.refreshToken).toBeNull()
        expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('cpq_access_token')
        expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('cpq_refresh_token')
      })

      it('should do nothing if no stored tokens', async () => {
        const authStore = useAuthStore()
        
        mockLocalStorage.getItem.mockReturnValue(null)

        await authStore.initializeAuth()

        expect(mockAuthApi.getCurrentUser).not.toHaveBeenCalled()
        expect(authStore.token).toBeNull()
        expect(authStore.user).toBeNull()
      })
    })

    describe('login', () => {
      it('should login successfully', async () => {
        const authStore = useAuthStore()
        const credentials: LoginRequest = {
          username: 'testuser',
          password: 'password123'
        }

        const result = await authStore.login(credentials)

        expect(mockAuthApi.login).toHaveBeenCalledWith(credentials)
        expect(authStore.loading).toBe(false)
        expect(authStore.user).toEqual(mockUser)
        expect(authStore.token).toBe(mockLoginResponse.tokens.access_token)
        expect(authStore.refreshToken).toBe(mockLoginResponse.tokens.refresh_token)
        expect(mockLocalStorage.setItem).toHaveBeenCalledWith('cpq_access_token', mockLoginResponse.tokens.access_token)
        expect(mockLocalStorage.setItem).toHaveBeenCalledWith('cpq_refresh_token', mockLoginResponse.tokens.refresh_token)
        expect(result).toEqual(mockLoginResponse)
      })

      it('should handle login error', async () => {
        const authStore = useAuthStore()
        const credentials: LoginRequest = {
          username: 'testuser',
          password: 'wrongpassword'
        }

        const error = new Error('Invalid credentials')
        mockAuthApi.login.mockRejectedValueOnce(error)

        await expect(authStore.login(credentials)).rejects.toThrow('Invalid credentials')
        expect(authStore.loading).toBe(false)
        expect(authStore.user).toBeNull()
        expect(authStore.token).toBeNull()
      })

      it('should set loading state during login', async () => {
        const authStore = useAuthStore()
        const credentials: LoginRequest = {
          username: 'testuser',
          password: 'password123'
        }

        // Make API call hang to test loading state
        let resolveLogin: (value: any) => void
        const loginPromise = new Promise(resolve => {
          resolveLogin = resolve
        })
        mockAuthApi.login.mockReturnValueOnce(loginPromise)

        const resultPromise = authStore.login(credentials)
        
        // Should be loading
        expect(authStore.loading).toBe(true)

        // Resolve the promise
        resolveLogin!(mockLoginResponse)
        await resultPromise

        // Should not be loading anymore
        expect(authStore.loading).toBe(false)
      })
    })

    describe('register', () => {
      it('should register successfully', async () => {
        const authStore = useAuthStore()
        const userData: RegisterRequest = {
          username: 'newuser',
          email: 'newuser@example.com',
          password: 'password123',
          first_name: 'New',
          last_name: 'User'
        }

        const result = await authStore.register(userData)

        expect(mockAuthApi.register).toHaveBeenCalledWith(userData)
        expect(authStore.loading).toBe(false)
        expect(authStore.user).toEqual(mockUser)
        expect(authStore.token).toBe(mockLoginResponse.tokens.access_token)
        expect(authStore.refreshToken).toBe(mockLoginResponse.tokens.refresh_token)
        expect(result).toEqual(mockLoginResponse)
      })

      it('should handle registration error', async () => {
        const authStore = useAuthStore()
        const userData: RegisterRequest = {
          username: 'existinguser',
          email: 'existing@example.com',
          password: 'password123',
          first_name: 'Existing',
          last_name: 'User'
        }

        const error = new Error('Username already exists')
        mockAuthApi.register.mockRejectedValueOnce(error)

        await expect(authStore.register(userData)).rejects.toThrow('Username already exists')
        expect(authStore.loading).toBe(false)
        expect(authStore.user).toBeNull()
        expect(authStore.token).toBeNull()
      })
    })

    describe('refreshAccessToken', () => {
      it('should refresh token successfully', async () => {
        const authStore = useAuthStore()
        const newToken = 'new-access-token'
        mockAuthApi.refresh.mockResolvedValueOnce({ access_token: newToken })

        const result = await authStore.refreshAccessToken()

        expect(mockAuthApi.refresh).toHaveBeenCalled()
        expect(authStore.token).toBe(newToken)
        expect(mockLocalStorage.setItem).toHaveBeenCalledWith('cpq_access_token', newToken)
        expect(result).toEqual({ access_token: newToken })
      })

      it('should clear auth on refresh failure', async () => {
        const authStore = useAuthStore()
        
        // Set initial auth state
        authStore.$patch({
          user: mockUser,
          token: 'old-token',
          refreshToken: 'old-refresh-token'
        })

        const error = new Error('Refresh token expired')
        mockAuthApi.refresh.mockRejectedValueOnce(error)

        await expect(authStore.refreshAccessToken()).rejects.toThrow('Refresh token expired')
        
        // Should clear auth state
        expect(authStore.user).toBeNull()
        expect(authStore.token).toBeNull()
        expect(authStore.refreshToken).toBeNull()
        expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('cpq_access_token')
        expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('cpq_refresh_token')
      })
    })

    describe('logout', () => {
      it('should logout and clear auth state', () => {
        const authStore = useAuthStore()
        
        // Set initial auth state
        authStore.$patch({
          user: mockUser,
          token: 'access-token',
          refreshToken: 'refresh-token'
        })

        authStore.logout()

        expect(authStore.user).toBeNull()
        expect(authStore.token).toBeNull()
        expect(authStore.refreshToken).toBeNull()
        expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('cpq_access_token')
        expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('cpq_refresh_token')
      })
    })

    describe('updateUser', () => {
      it('should update user data', () => {
        const authStore = useAuthStore()
        const updatedUser = { ...mockUser, first_name: 'Updated' }

        authStore.updateUser(updatedUser)

        expect(authStore.user).toEqual(updatedUser)
      })
    })
  })
})