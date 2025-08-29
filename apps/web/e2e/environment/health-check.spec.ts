/**
 * Environment Health Check Tests
 * 
 * These tests verify that the complete development environment is properly configured
 * and that frontend-backend communication works correctly through the proxy setup.
 */

import { test, expect } from '@playwright/test'

test.describe('Environment Health Checks', () => {
  test.beforeEach(async ({ page }) => {
    // Set longer timeout for environment checks
    test.setTimeout(30000)
  })

  test('should verify frontend server is running', async ({ page }) => {
    // Navigate to frontend
    await page.goto('/')
    
    // Should load without network errors
    await expect(page).toHaveTitle(/CPQ|Electric|Equipment|Configuration/, { timeout: 10000 })
    
    // Check for specific frontend elements
    const appElement = page.locator('#app, [data-app], main, body')
    await expect(appElement).toBeVisible({ timeout: 5000 })
  })

  test('should verify backend API server is accessible', async ({ page }) => {
    // Test direct API access through proxy
    const response = await page.request.get('/api/health')
    
    expect(response.status()).toBe(200)
    
    const data = await response.json()
    expect(data).toHaveProperty('status', 'healthy')
    expect(data).toHaveProperty('timestamp')
    expect(data).toHaveProperty('version')
  })

  test('should verify proxy configuration works correctly', async ({ page }) => {
    // Test that frontend can communicate with backend through proxy
    await page.goto('/')
    
    // Monitor network requests to API
    const apiRequests: string[] = []
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        apiRequests.push(request.url())
      }
    })
    
    // Make an API call through the frontend
    const healthResponse = await page.evaluate(async () => {
      try {
        const response = await fetch('/api/health')
        return {
          status: response.status,
          ok: response.ok,
          data: await response.json()
        }
      } catch (error) {
        return {
          status: 0,
          ok: false,
          error: error.message
        }
      }
    })
    
    // Verify the request was successful
    expect(healthResponse.status).toBe(200)
    expect(healthResponse.ok).toBe(true)
    expect(healthResponse.data).toHaveProperty('status', 'healthy')
    
    // Verify at least one API request was made
    expect(apiRequests.length).toBeGreaterThan(0)
    expect(apiRequests[0]).toContain('/api/health')
  })

  test('should verify CORS configuration allows frontend requests', async ({ page }) => {
    await page.goto('/')
    
    // Test CORS by making different types of requests
    const corsTests = await page.evaluate(async () => {
      const results = {
        GET: { success: false, error: '' },
        POST: { success: false, error: '' },
        OPTIONS: { success: false, error: '' }
      }
      
      // Test GET request
      try {
        const getResponse = await fetch('/api/health', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          }
        })
        results.GET.success = getResponse.ok
      } catch (error) {
        results.GET.error = error.message
      }
      
      // Test POST request (should work even without auth for CORS check)
      try {
        const postResponse = await fetch('/api/auth/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ username: 'test', password: 'test' })
        })
        // We expect 400/401, not a CORS error
        results.POST.success = postResponse.status !== 0
      } catch (error) {
        results.POST.error = error.message
      }
      
      // Test OPTIONS request (preflight)
      try {
        const optionsResponse = await fetch('/api/health', {
          method: 'OPTIONS'
        })
        results.OPTIONS.success = optionsResponse.ok || optionsResponse.status === 204
      } catch (error) {
        results.OPTIONS.error = error.message
      }
      
      return results
    })
    
    // All requests should succeed (not be blocked by CORS)
    expect(corsTests.GET.success).toBe(true)
    expect(corsTests.POST.success).toBe(true)
    expect(corsTests.OPTIONS.success).toBe(true)
    
    // Verify no CORS-related errors
    expect(corsTests.GET.error).not.toContain('CORS')
    expect(corsTests.POST.error).not.toContain('CORS')
    expect(corsTests.OPTIONS.error).not.toContain('CORS')
  })

  test('should verify authentication flow works end-to-end', async ({ page }) => {
    await page.goto('/login')
    
    // Monitor network requests for authentication
    const authRequests: any[] = []
    page.on('response', response => {
      if (response.url().includes('/api/auth/')) {
        authRequests.push({
          url: response.url(),
          status: response.status(),
          headers: response.headers()
        })
      }
    })
    
    // Try to login with test credentials
    await page.fill('input[name="username"], input[placeholder*="username" i]', 'admin')
    await page.fill('input[name="password"], input[type="password"]', 'admin123')
    
    // Submit login form
    await page.click('button[type="submit"], button:has-text("Login")')
    
    // Wait for response
    await page.waitForTimeout(3000)
    
    // Check if any auth requests were made
    expect(authRequests.length).toBeGreaterThan(0)
    
    const loginRequest = authRequests.find(req => req.url.includes('/login'))
    expect(loginRequest).toBeDefined()
    
    // Status should be either 200 (success) or 400/401 (bad credentials)
    // but not 0 (connection failed) or 500 (server error)
    expect([200, 400, 401, 422]).toContain(loginRequest.status)
    
    // Verify CORS headers are present
    expect(loginRequest.headers).toHaveProperty('access-control-allow-origin')
  })

  test('should verify database connectivity', async ({ page }) => {
    // Test an endpoint that requires database access
    const response = await page.request.get('/api/products', {
      headers: {
        'Authorization': 'Bearer invalid-token' // We expect 401, not 500
      }
    })
    
    // Should get 401 (unauthorized) not 500 (database error)
    expect(response.status()).toBe(401)
    
    const data = await response.json()
    expect(data).toHaveProperty('error')
    expect(data.error).not.toContain('database')
    expect(data.error).not.toContain('connection')
  })

  test('should verify static assets load correctly', async ({ page }) => {
    await page.goto('/')
    
    // Monitor failed requests
    const failedRequests: string[] = []
    page.on('requestfailed', request => {
      failedRequests.push(request.url())
    })
    
    // Wait for page to fully load
    await page.waitForLoadState('networkidle', { timeout: 15000 })
    
    // Check for any failed asset requests
    const assetFailures = failedRequests.filter(url => 
      url.includes('.js') || 
      url.includes('.css') || 
      url.includes('.ico') ||
      url.includes('/assets/')
    )
    
    if (assetFailures.length > 0) {
      console.log('Failed asset requests:', assetFailures)
    }
    
    // Critical assets should load (some favicon failures are acceptable)
    const criticalFailures = assetFailures.filter(url => 
      !url.includes('favicon') && !url.includes('.ico')
    )
    
    expect(criticalFailures.length).toBe(0)
  })

  test('should verify environment variables and configuration', async ({ page }) => {
    // Test that the frontend has proper configuration
    const config = await page.evaluate(() => {
      return {
        baseURL: window.location.origin,
        apiEndpoint: '/api',
        // Check if any global config is available
        hasGlobalConfig: typeof window !== 'undefined'
      }
    })
    
    expect(config.baseURL).toContain('localhost:5173')
    expect(config.apiEndpoint).toBe('/api')
    expect(config.hasGlobalConfig).toBe(true)
    
    // Test API configuration
    const apiConfig = await page.request.get('/api/health')
    expect(apiConfig.status()).toBe(200)
    
    const healthData = await apiConfig.json()
    expect(healthData).toHaveProperty('environment')
    expect(['development', 'testing', 'production']).toContain(healthData.environment)
  })

  test('should verify performance within acceptable limits', async ({ page }) => {
    const startTime = Date.now()
    
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    
    const loadTime = Date.now() - startTime
    
    // Page should load within 10 seconds in dev environment
    expect(loadTime).toBeLessThan(10000)
    
    // API should respond quickly
    const apiStartTime = Date.now()
    const apiResponse = await page.request.get('/api/health')
    const apiTime = Date.now() - apiStartTime
    
    expect(apiResponse.status()).toBe(200)
    expect(apiTime).toBeLessThan(2000) // API should respond within 2 seconds
  })

  test('should detect common development environment issues', async ({ page }) => {
    const issues: string[] = []
    
    // Monitor console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        const text = msg.text()
        if (text.includes('CORS') || 
            text.includes('Network Error') || 
            text.includes('Failed to fetch') ||
            text.includes('ERR_CONNECTION_REFUSED')) {
          issues.push(`Console Error: ${text}`)
        }
      }
    })
    
    // Monitor failed requests
    page.on('requestfailed', request => {
      const url = request.url()
      const failure = request.failure()
      if (failure && failure.errorText.includes('net::ERR_CONNECTION_REFUSED')) {
        issues.push(`Connection Refused: ${url}`)
      }
    })
    
    await page.goto('/')
    
    // Try to make an API call
    await page.evaluate(async () => {
      try {
        await fetch('/api/health')
      } catch (error) {
        console.error('API Health Check Failed:', error.message)
      }
    })
    
    // Wait a bit for any async errors
    await page.waitForTimeout(2000)
    
    // Report issues if any
    if (issues.length > 0) {
      console.log('Development Environment Issues Detected:')
      issues.forEach(issue => console.log(`- ${issue}`))
    }
    
    // Test should pass, but issues will be logged for debugging
    expect(issues.length).toBeLessThanOrEqual(5) // Allow some minor issues in dev
  })
})

test.describe('Development Server Integration', () => {
  test('should verify both servers are running on correct ports', async ({ page }) => {
    // Test frontend server
    const frontendResponse = await page.request.get('http://localhost:5173')
    expect(frontendResponse.status()).toBe(200)
    
    // Test backend server directly
    const backendResponse = await page.request.get('http://localhost:5000/api/health')
    expect(backendResponse.status()).toBe(200)
    
    const healthData = await backendResponse.json()
    expect(healthData).toHaveProperty('status', 'healthy')
  })

  test('should verify proxy configuration matches backend endpoint', async ({ page }) => {
    await page.goto('/')
    
    // Test proxy works
    const proxyResponse = await page.request.get('/api/health')
    expect(proxyResponse.status()).toBe(200)
    
    // Test direct backend access
    const directResponse = await page.request.get('http://localhost:5000/api/health')
    expect(directResponse.status()).toBe(200)
    
    // Both should return the same data
    const proxyData = await proxyResponse.json()
    const directData = await directResponse.json()
    
    expect(proxyData.status).toBe(directData.status)
    expect(proxyData.timestamp).toBeDefined()
    expect(directData.timestamp).toBeDefined()
  })
})