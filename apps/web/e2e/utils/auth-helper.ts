/**
 * Authentication helper functions for E2E tests
 */

import { Page, expect } from '@playwright/test'

export interface TestUser {
  username: string
  email: string
  password: string
  first_name: string
  last_name: string
  role: string
}

export const testUsers: Record<string, TestUser> = {
  user: {
    username: 'testuser',
    email: 'test@example.com',
    password: 'testpass123',
    first_name: 'Test',
    last_name: 'User',
    role: 'user'
  },
  admin: {
    username: 'admin',
    email: 'admin@example.com',
    password: 'admin123', // Updated to match demo credentials
    first_name: 'Admin',
    last_name: 'User',
    role: 'admin'
  },
  engineer: {
    username: 'engineer',
    email: 'engineer@example.com',
    password: 'engineer123', // Updated to match demo credentials
    first_name: 'Engineer',
    last_name: 'User',
    role: 'engineer'
  },
  manager: {
    username: 'manager',
    email: 'manager@example.com',
    password: 'manager123', // Updated to match demo credentials
    first_name: 'Manager',
    last_name: 'User',
    role: 'manager'
  }
}

/**
 * Navigate to login page and perform login
 */
export async function login(page: Page, userType: keyof typeof testUsers = 'user') {
  const user = testUsers[userType]
  
  // Navigate to login page
  await page.goto('/login')
  
  // Wait for login form to be visible
  await page.waitForSelector('form', { state: 'visible' })
  
  // Fill login form
  await page.fill('input[placeholder*="username" i], input[name="username"]', user.username)
  await page.fill('input[placeholder*="password" i], input[name="password"], input[type="password"]', user.password)
  
  // Submit login form
  await page.click('button[type="submit"], button:has-text("Login"), button:has-text("登录")')
  
  // Wait for successful login (redirect to dashboard or home)
  await page.waitForURL(/\/(dashboard|home|products|\/)$/, { timeout: 10000 })
  
  // Verify we're logged in by checking for user menu or logout button
  await expect(page.locator('[data-testid="user-menu"], .user-menu, button:has-text("Logout"), button:has-text("退出")')).toBeVisible({ timeout: 5000 })
}

/**
 * Register a new user account
 */
export async function register(page: Page, user: TestUser) {
  // Navigate to register page
  await page.goto('/register')
  
  // Wait for register form to be visible
  await page.waitForSelector('form', { state: 'visible' })
  
  // Fill registration form
  await page.fill('input[name="username"], input[placeholder*="username" i]', user.username)
  await page.fill('input[name="email"], input[placeholder*="email" i], input[type="email"]', user.email)
  await page.fill('input[name="password"], input[placeholder*="password" i], input[type="password"]', user.password)
  await page.fill('input[name="first_name"], input[placeholder*="first" i]', user.first_name)
  await page.fill('input[name="last_name"], input[placeholder*="last" i]', user.last_name)
  
  // Select role if dropdown is available
  const roleSelect = page.locator('select[name="role"], .el-select:has-text("Role")')
  if (await roleSelect.isVisible()) {
    await roleSelect.click()
    await page.click(`option[value="${user.role}"], .el-option:has-text("${user.role}")`)
  }
  
  // Submit registration form
  await page.click('button[type="submit"], button:has-text("Register"), button:has-text("注册")')
  
  // Wait for successful registration (redirect to dashboard or login)
  await page.waitForURL(/\/(dashboard|login|home|\/)$/, { timeout: 10000 })
}

/**
 * Logout current user
 */
export async function logout(page: Page) {
  // Look for logout button in various possible locations
  const logoutSelectors = [
    'button:has-text("Logout")',
    'button:has-text("退出")',
    '[data-testid="logout-button"]',
    '.logout-button',
    '.user-menu button:has-text("Logout")',
    '.user-menu button:has-text("退出")'
  ]
  
  let logoutButton
  for (const selector of logoutSelectors) {
    logoutButton = page.locator(selector)
    if (await logoutButton.isVisible()) {
      break
    }
  }
  
  if (!logoutButton || !(await logoutButton.isVisible())) {
    // Try clicking user menu first
    const userMenu = page.locator('[data-testid="user-menu"], .user-menu, .user-avatar')
    if (await userMenu.isVisible()) {
      await userMenu.click()
      
      // Wait for dropdown and try logout again
      await page.waitForTimeout(500)
      for (const selector of logoutSelectors) {
        logoutButton = page.locator(selector)
        if (await logoutButton.isVisible()) {
          break
        }
      }
    }
  }
  
  if (logoutButton && (await logoutButton.isVisible())) {
    await logoutButton.click()
  }
  
  // Wait for redirect to login page
  await page.waitForURL(/\/login$/, { timeout: 10000 })
  
  // Verify we're logged out
  await expect(page.locator('button:has-text("Login"), button:has-text("登录")')).toBeVisible()
}

/**
 * Check if user is currently logged in
 */
export async function isLoggedIn(page: Page): Promise<boolean> {
  try {
    const userIndicators = [
      '[data-testid="user-menu"]',
      '.user-menu',
      'button:has-text("Logout")',
      'button:has-text("退出")',
      '.user-avatar'
    ]
    
    for (const selector of userIndicators) {
      if (await page.locator(selector).isVisible()) {
        return true
      }
    }
    
    return false
  } catch {
    return false
  }
}

/**
 * Get current user info from the page
 */
export async function getCurrentUser(page: Page): Promise<{ username?: string; role?: string } | null> {
  try {
    // Try to get user info from user menu or profile section
    const userMenu = page.locator('[data-testid="user-menu"], .user-menu')
    if (await userMenu.isVisible()) {
      await userMenu.click()
      await page.waitForTimeout(500)
      
      const username = await page.locator('[data-testid="username"], .username').textContent()
      const role = await page.locator('[data-testid="user-role"], .user-role').textContent()
      
      return {
        username: username || undefined,
        role: role || undefined
      }
    }
    
    return null
  } catch {
    return null
  }
}

/**
 * Ensure user is logged in with specific role
 */
export async function ensureLoggedIn(page: Page, userType: keyof typeof testUsers = 'user') {
  if (!(await isLoggedIn(page))) {
    await login(page, userType)
  } else {
    // Check if current user has the right role
    const currentUser = await getCurrentUser(page)
    if (currentUser?.role !== testUsers[userType].role) {
      await logout(page)
      await login(page, userType)
    }
  }
}

/**
 * Clear all authentication data
 */
export async function clearAuth(page: Page) {
  // Clear localStorage and sessionStorage
  await page.evaluate(() => {
    localStorage.clear()
    sessionStorage.clear()
  })
  
  // Clear cookies
  await page.context().clearCookies()
}

/**
 * Setup test user for API access (create if doesn't exist)
 */
export async function setupTestUser(page: Page, userType: keyof typeof testUsers = 'user'): Promise<TestUser> {
  const user = testUsers[userType]
  
  try {
    // Try to login with existing user
    await login(page, userType)
    return user
  } catch {
    // User doesn't exist, create it
    await register(page, user)
    return user
  }
}

/**
 * Validate API connectivity before authentication tests
 */
export async function validateApiConnectivity(page: Page): Promise<void> {
  try {
    const response = await page.request.get('/api/health')
    if (response.status() !== 200) {
      throw new Error(`API health check failed with status ${response.status()}`)
    }
    
    const data = await response.json()
    if (data.status !== 'healthy') {
      throw new Error(`API is not healthy: ${JSON.stringify(data)}`)
    }
  } catch (error) {
    throw new Error(`API connectivity validation failed: ${error.message}`)
  }
}

/**
 * Validate CORS configuration works correctly
 */
export async function validateCorsConfiguration(page: Page): Promise<void> {
  await page.goto('/')
  
  const corsTest = await page.evaluate(async () => {
    try {
      const response = await fetch('/api/health', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      return {
        success: response.ok,
        status: response.status,
        error: null
      }
    } catch (error) {
      return {
        success: false,
        status: 0,
        error: error.message
      }
    }
  })
  
  if (!corsTest.success) {
    throw new Error(
      `CORS configuration validation failed: ${corsTest.error || `Status ${corsTest.status}`}`
    )
  }
}

/**
 * Enhanced login with environment validation
 */
export async function loginWithValidation(page: Page, userType: keyof typeof testUsers = 'user') {
  // First validate API connectivity
  await validateApiConnectivity(page)
  
  // Validate CORS configuration
  await validateCorsConfiguration(page)
  
  // Proceed with normal login
  await login(page, userType)
}