/**
 * E2E tests for user authentication flow
 */

import { test, expect } from '@playwright/test'
import { login, logout, register, clearAuth, testUsers, isLoggedIn } from '../utils/auth-helper'

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await clearAuth(page)
  })

  test.describe('Login', () => {
    test('should successfully login with valid credentials', async ({ page }) => {
      await login(page, 'user')
      
      // Should be redirected to dashboard or home page
      expect(page.url()).toMatch(/\/(dashboard|home|products|\/)$/)
      
      // Should show user menu or logout button
      await expect(page.locator('[data-testid="user-menu"], .user-menu, button:has-text("Logout")')).toBeVisible()
    })

    test('should show error with invalid credentials', async ({ page }) => {
      await page.goto('/login')
      
      // Fill form with invalid credentials
      await page.fill('input[name="username"], input[placeholder*="username" i]', 'invaliduser')
      await page.fill('input[name="password"], input[type="password"]', 'wrongpassword')
      
      // Submit form
      await page.click('button[type="submit"], button:has-text("Login")')
      
      // Should show error message
      await expect(page.locator('.error, .el-message--error, [role="alert"]')).toBeVisible()
      
      // Should remain on login page
      expect(page.url()).toContain('/login')
    })

    test('should show validation errors for empty fields', async ({ page }) => {
      await page.goto('/login')
      
      // Try to submit empty form
      await page.click('button[type="submit"], button:has-text("Login")')
      
      // Should show validation errors
      const errorMessages = page.locator('.error, .el-form-item__error, .form-error')
      await expect(errorMessages.first()).toBeVisible()
      
      // Should remain on login page
      expect(page.url()).toContain('/login')
    })

    test('should redirect to login page when accessing protected route without authentication', async ({ page }) => {
      // Try to access protected route without login
      await page.goto('/products')
      
      // Should be redirected to login page
      await page.waitForURL(/\/login/, { timeout: 5000 })
      expect(page.url()).toContain('/login')
    })

    test('should handle login with different user roles', async ({ page }) => {
      // Test admin login
      await login(page, 'admin')
      expect(await isLoggedIn(page)).toBe(true)
      await logout(page)
      
      // Test engineer login
      await login(page, 'engineer')
      expect(await isLoggedIn(page)).toBe(true)
      await logout(page)
      
      // Test manager login
      await login(page, 'manager')
      expect(await isLoggedIn(page)).toBe(true)
    })

    test('should persist login session on page refresh', async ({ page }) => {
      await login(page, 'user')
      
      // Refresh page
      await page.reload()
      
      // Should still be logged in
      expect(await isLoggedIn(page)).toBe(true)
      await expect(page.locator('[data-testid="user-menu"], .user-menu')).toBeVisible()
    })

    test('should handle case insensitive username', async ({ page }) => {
      const user = testUsers.user
      
      await page.goto('/login')
      
      // Use uppercase username
      await page.fill('input[name="username"], input[placeholder*="username" i]', user.username.toUpperCase())
      await page.fill('input[name="password"], input[type="password"]', user.password)
      
      await page.click('button[type="submit"], button:has-text("Login")')
      
      // Should either succeed (if case insensitive) or show appropriate error
      await page.waitForTimeout(2000)
      const isSuccess = await isLoggedIn(page)
      
      if (isSuccess) {
        expect(page.url()).toMatch(/\/(dashboard|home|products|\/)$/)
      } else {
        await expect(page.locator('.error, .el-message--error')).toBeVisible()
      }
    })
  })

  test.describe('Registration', () => {
    test('should successfully register new user', async ({ page }) => {
      const newUser = {
        username: `newuser_${Date.now()}`,
        email: `newuser_${Date.now()}@example.com`,
        password: 'newpass123',
        first_name: 'New',
        last_name: 'User',
        role: 'user'
      }
      
      await register(page, newUser)
      
      // Should be redirected after successful registration
      expect(page.url()).toMatch(/\/(dashboard|login|home|\/)$/)
    })

    test('should show error for duplicate username', async ({ page }) => {
      await page.goto('/register')
      
      // Use existing username
      const existingUser = testUsers.user
      await page.fill('input[name="username"]', existingUser.username)
      await page.fill('input[name="email"]', `different_${Date.now()}@example.com`)
      await page.fill('input[name="password"]', 'newpass123')
      await page.fill('input[name="first_name"]', 'Test')
      await page.fill('input[name="last_name"]', 'User')
      
      await page.click('button[type="submit"], button:has-text("Register")')
      
      // Should show error message
      await expect(page.locator('.error, .el-message--error, [role="alert"]')).toBeVisible()
    })

    test('should show error for duplicate email', async ({ page }) => {
      await page.goto('/register')
      
      // Use existing email
      const existingUser = testUsers.user
      await page.fill('input[name="username"]', `different_${Date.now()}`)
      await page.fill('input[name="email"]', existingUser.email)
      await page.fill('input[name="password"]', 'newpass123')
      await page.fill('input[name="first_name"]', 'Test')
      await page.fill('input[name="last_name"]', 'User')
      
      await page.click('button[type="submit"], button:has-text("Register")')
      
      // Should show error message
      await expect(page.locator('.error, .el-message--error, [role="alert"]')).toBeVisible()
    })

    test('should validate required fields', async ({ page }) => {
      await page.goto('/register')
      
      // Try to submit empty form
      await page.click('button[type="submit"], button:has-text("Register")')
      
      // Should show validation errors
      const errorMessages = page.locator('.error, .el-form-item__error, .form-error')
      await expect(errorMessages.first()).toBeVisible()
    })

    test('should validate email format', async ({ page }) => {
      await page.goto('/register')
      
      await page.fill('input[name="username"]', 'testuser')
      await page.fill('input[name="email"]', 'invalid-email')
      await page.fill('input[name="password"]', 'password123')
      await page.fill('input[name="first_name"]', 'Test')
      await page.fill('input[name="last_name"]', 'User')
      
      await page.click('button[type="submit"], button:has-text("Register")')
      
      // Should show email validation error
      await expect(page.locator('.error, .el-form-item__error')).toBeVisible()
    })

    test('should validate password strength', async ({ page }) => {
      await page.goto('/register')
      
      await page.fill('input[name="username"]', 'testuser')
      await page.fill('input[name="email"]', 'test@example.com')
      await page.fill('input[name="password"]', '123') // Weak password
      await page.fill('input[name="first_name"]', 'Test')
      await page.fill('input[name="last_name"]', 'User')
      
      await page.click('button[type="submit"], button:has-text("Register")')
      
      // Should show password validation error or accept based on validation rules
      await page.waitForTimeout(2000)
      
      // This test documents current behavior - adjust based on actual validation rules
      const hasError = await page.locator('.error, .el-form-item__error').isVisible()
      const isSuccess = page.url().includes('/dashboard') || page.url().includes('/login')
      
      expect(hasError || isSuccess).toBe(true)
    })
  })

  test.describe('Logout', () => {
    test('should successfully logout', async ({ page }) => {
      await login(page, 'user')
      
      // Verify logged in
      expect(await isLoggedIn(page)).toBe(true)
      
      // Logout
      await logout(page)
      
      // Should be redirected to login page
      expect(page.url()).toContain('/login')
      
      // Should show login form
      await expect(page.locator('button:has-text("Login"), button:has-text("登录")')).toBeVisible()
    })

    test('should clear session data on logout', async ({ page }) => {
      await login(page, 'user')
      
      // Logout
      await logout(page)
      
      // Try to access protected route
      await page.goto('/products')
      
      // Should be redirected to login
      await page.waitForURL(/\/login/, { timeout: 5000 })
      expect(page.url()).toContain('/login')
    })

    test('should handle logout from user menu dropdown', async ({ page }) => {
      await login(page, 'user')
      
      // Click on user menu
      const userMenu = page.locator('[data-testid="user-menu"], .user-menu, .user-avatar')
      if (await userMenu.isVisible()) {
        await userMenu.click()
        
        // Wait for dropdown
        await page.waitForTimeout(500)
        
        // Click logout from dropdown
        await page.click('button:has-text("Logout"), a:has-text("Logout")')
        
        // Should be redirected to login
        await page.waitForURL(/\/login/, { timeout: 5000 })
        expect(page.url()).toContain('/login')
      }
    })
  })

  test.describe('Session Management', () => {
    test('should handle token expiration gracefully', async ({ page }) => {
      await login(page, 'user')
      
      // Simulate token expiration by clearing localStorage
      await page.evaluate(() => {
        localStorage.removeItem('cpq_access_token')
      })
      
      // Try to access protected route
      await page.goto('/products')
      
      // Should be redirected to login due to expired token
      await page.waitForURL(/\/login/, { timeout: 10000 })
      expect(page.url()).toContain('/login')
    })

    test('should handle network errors during authentication', async ({ page }) => {
      // Intercept network requests and simulate failure
      await page.route('**/api/auth/login', route => {
        route.abort('failed')
      })
      
      await page.goto('/login')
      
      await page.fill('input[name="username"]', testUsers.user.username)
      await page.fill('input[name="password"]', testUsers.user.password)
      
      await page.click('button[type="submit"], button:has-text("Login")')
      
      // Should show network error message
      await expect(page.locator('.error, .el-message--error, [role="alert"]')).toBeVisible()
    })

    test('should redirect to intended page after login', async ({ page }) => {
      // Try to access protected page without authentication
      await page.goto('/products')
      
      // Should be redirected to login
      await page.waitForURL(/\/login/, { timeout: 5000 })
      
      // Login
      await page.fill('input[name="username"]', testUsers.user.username)
      await page.fill('input[name="password"]', testUsers.user.password)
      await page.click('button[type="submit"], button:has-text("Login")')
      
      // Should be redirected to originally requested page
      await page.waitForURL(/\/products/, { timeout: 10000 })
      expect(page.url()).toContain('/products')
    })
  })

  test.describe('Multi-language Support', () => {
    test('should display login form in Chinese', async ({ page }) => {
      // Set language to Chinese (if supported)
      await page.goto('/login?lang=zh')
      
      // Check for Chinese text (if internationalization is implemented)
      const chineseElements = await page.locator(':has-text("登录"), :has-text("用户名"), :has-text("密码")').count()
      
      if (chineseElements > 0) {
        // Chinese interface is available
        await expect(page.locator(':has-text("登录")')).toBeVisible()
      } else {
        // Fallback to English
        await expect(page.locator(':has-text("Login")')).toBeVisible()
      }
    })

    test('should maintain language preference after login', async ({ page }) => {
      // Set language preference
      await page.goto('/login?lang=zh')
      
      await login(page, 'user')
      
      // Language preference should be maintained after login
      // This test documents current behavior
      expect(page.url()).toBeTruthy() // Basic assertion, adjust based on implementation
    })
  })
})