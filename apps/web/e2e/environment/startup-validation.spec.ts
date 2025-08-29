/**
 * Development Environment Startup Validation Tests
 * 
 * These tests validate that the development environment starts up correctly
 * and all services are properly configured and accessible.
 */

import { test, expect } from '@playwright/test'

test.describe('Development Environment Startup Validation', () => {
  test.beforeAll(async () => {
    // Set longer timeout for startup tests
    test.setTimeout(60000)
  })

  test('should validate complete development environment startup', async ({ page }) => {
    console.log('🔍 Validating development environment startup...')
    
    const validationResults = {
      frontendServer: { status: 'unknown', details: '' },
      backendServer: { status: 'unknown', details: '' },
      proxyConfiguration: { status: 'unknown', details: '' },
      databaseConnection: { status: 'unknown', details: '' },
      corsConfiguration: { status: 'unknown', details: '' },
      staticAssets: { status: 'unknown', details: '' }
    }
    
    // 1. Test Frontend Server
    try {
      await page.goto('http://localhost:5173', { timeout: 10000 })
      await page.waitForLoadState('domcontentloaded', { timeout: 5000 })
      validationResults.frontendServer = { 
        status: 'healthy', 
        details: 'Frontend server accessible on port 5173' 
      }
    } catch (error) {
      validationResults.frontendServer = { 
        status: 'error', 
        details: `Frontend server not accessible: ${error.message}` 
      }
    }
    
    // 2. Test Backend Server (Direct)
    try {
      const backendResponse = await page.request.get('http://localhost:5000/api/health')
      if (backendResponse.status() === 200) {
        const data = await backendResponse.json()
        validationResults.backendServer = { 
          status: 'healthy', 
          details: `Backend server healthy: ${JSON.stringify(data)}` 
        }
      } else {
        validationResults.backendServer = { 
          status: 'error', 
          details: `Backend server returned status ${backendResponse.status()}` 
        }
      }
    } catch (error) {
      validationResults.backendServer = { 
        status: 'error', 
        details: `Backend server not accessible: ${error.message}` 
      }
    }
    
    // 3. Test Proxy Configuration
    if (validationResults.frontendServer.status === 'healthy') {
      try {
        await page.goto('http://localhost:5173')
        const proxyResponse = await page.request.get('/api/health')
        if (proxyResponse.status() === 200) {
          validationResults.proxyConfiguration = { 
            status: 'healthy', 
            details: 'Proxy correctly routes /api requests to backend' 
          }
        } else {
          validationResults.proxyConfiguration = { 
            status: 'error', 
            details: `Proxy returned status ${proxyResponse.status()}` 
          }
        }
      } catch (error) {
        validationResults.proxyConfiguration = { 
          status: 'error', 
          details: `Proxy configuration error: ${error.message}` 
        }
      }
    }
    
    // 4. Test Database Connection
    if (validationResults.backendServer.status === 'healthy') {
      try {
        // Test an endpoint that requires database access
        const dbResponse = await page.request.get('http://localhost:5000/api/products', {
          headers: { 'Authorization': 'Bearer invalid-token' }
        })
        // Should get 401 (unauthorized) not 500 (database error)
        if (dbResponse.status() === 401) {
          validationResults.databaseConnection = { 
            status: 'healthy', 
            details: 'Database connection working (authentication required)' 
          }
        } else if (dbResponse.status() >= 500) {
          validationResults.databaseConnection = { 
            status: 'error', 
            details: `Database connection error (status ${dbResponse.status()})` 
          }
        } else {
          validationResults.databaseConnection = { 
            status: 'warning', 
            details: `Unexpected response status ${dbResponse.status()}` 
          }
        }
      } catch (error) {
        validationResults.databaseConnection = { 
          status: 'error', 
          details: `Database test failed: ${error.message}` 
        }
      }
    }
    
    // 5. Test CORS Configuration
    if (validationResults.proxyConfiguration.status === 'healthy') {
      try {
        await page.goto('http://localhost:5173')
        const corsTest = await page.evaluate(async () => {
          try {
            const response = await fetch('/api/health', {
              method: 'GET',
              headers: {
                'Content-Type': 'application/json',
                'Origin': 'http://localhost:5173'
              }
            })
            return { success: true, status: response.status }
          } catch (error) {
            return { success: false, error: error.message }
          }
        })
        
        if (corsTest.success) {
          validationResults.corsConfiguration = { 
            status: 'healthy', 
            details: 'CORS correctly configured for frontend origin' 
          }
        } else {
          validationResults.corsConfiguration = { 
            status: 'error', 
            details: `CORS error: ${corsTest.error}` 
          }
        }
      } catch (error) {
        validationResults.corsConfiguration = { 
          status: 'error', 
          details: `CORS test failed: ${error.message}` 
        }
      }
    }
    
    // 6. Test Static Assets
    if (validationResults.frontendServer.status === 'healthy') {
      try {
        await page.goto('http://localhost:5173')
        
        const failedAssets: string[] = []
        page.on('requestfailed', request => {
          if (request.url().includes('.js') || request.url().includes('.css')) {
            failedAssets.push(request.url())
          }
        })
        
        await page.waitForLoadState('networkidle', { timeout: 10000 })
        
        if (failedAssets.length === 0) {
          validationResults.staticAssets = { 
            status: 'healthy', 
            details: 'All critical static assets loaded successfully' 
          }
        } else {
          validationResults.staticAssets = { 
            status: 'warning', 
            details: `Some assets failed to load: ${failedAssets.join(', ')}` 
          }
        }
      } catch (error) {
        validationResults.staticAssets = { 
          status: 'error', 
          details: `Static asset test failed: ${error.message}` 
        }
      }
    }
    
    // Log results
    console.log('\n📊 Development Environment Validation Results:')
    console.log('=' .repeat(60))
    
    Object.entries(validationResults).forEach(([component, result]) => {
      const icon = result.status === 'healthy' ? '✅' : 
                   result.status === 'warning' ? '⚠️' : '❌'
      console.log(`${icon} ${component}: ${result.status.toUpperCase()}`)
      console.log(`   ${result.details}`)
    })
    
    // Count healthy components
    const healthyCount = Object.values(validationResults)
      .filter(result => result.status === 'healthy').length
    const totalCount = Object.keys(validationResults).length
    
    console.log('\n📈 Health Score:', `${healthyCount}/${totalCount} components healthy`)
    
    // Test assertions
    expect(validationResults.frontendServer.status).toBe('healthy')
    expect(validationResults.backendServer.status).toBe('healthy')
    expect(validationResults.proxyConfiguration.status).toBe('healthy')
    expect(validationResults.databaseConnection.status).toBe('healthy')
    expect(validationResults.corsConfiguration.status).toBe('healthy')
    
    // Static assets can have warnings but should not be in error state
    expect(validationResults.staticAssets.status).not.toBe('error')
    
    // Overall health check
    const errorCount = Object.values(validationResults)
      .filter(result => result.status === 'error').length
    
    expect(errorCount).toBe(0)
  })

  test('should validate specific configuration values', async ({ page }) => {
    console.log('🔧 Validating configuration values...')
    
    // Test Vite proxy configuration
    await page.goto('http://localhost:5173')
    
    const configValidation = await page.evaluate(async () => {
      const results = {
        frontendPort: window.location.port,
        frontendHost: window.location.hostname,
        apiProxy: { working: false, error: '' },
        environment: 'unknown'
      }
      
      // Test API proxy
      try {
        const response = await fetch('/api/health')
        if (response.ok) {
          const data = await response.json()
          results.apiProxy.working = true
          results.environment = data.environment || 'unknown'
        }
      } catch (error) {
        results.apiProxy.error = error.message
      }
      
      return results
    })
    
    // Validate configuration
    expect(configValidation.frontendPort).toBe('5173')
    expect(configValidation.frontendHost).toBe('localhost')
    expect(configValidation.apiProxy.working).toBe(true)
    expect(['development', 'testing']).toContain(configValidation.environment)
    
    console.log('✅ Configuration validation passed')
    console.log(`   Frontend: ${configValidation.frontendHost}:${configValidation.frontendPort}`)
    console.log(`   API Proxy: ${configValidation.apiProxy.working ? '✅ Working' : '❌ Failed'}`)
    console.log(`   Environment: ${configValidation.environment}`)
  })

  test('should identify common startup issues', async ({ page }) => {
    console.log('🕵️ Checking for common startup issues...')
    
    const issues: string[] = []
    const warnings: string[] = []
    
    // Monitor console errors during startup
    page.on('console', msg => {
      if (msg.type() === 'error') {
        const text = msg.text()
        if (text.includes('CORS')) {
          issues.push('CORS Error: Frontend cannot communicate with backend')
        } else if (text.includes('Network Error') || text.includes('Failed to fetch')) {
          issues.push('Network Error: API requests failing')
        } else if (text.includes('404')) {
          warnings.push('404 Error: Some resources not found')
        }
      }
    })
    
    // Monitor failed requests
    page.on('requestfailed', request => {
      const url = request.url()
      const failure = request.failure()
      
      if (failure) {
        if (failure.errorText.includes('ERR_CONNECTION_REFUSED')) {
          issues.push(`Connection Refused: ${url}`)
        } else if (failure.errorText.includes('ERR_NAME_NOT_RESOLVED')) {
          issues.push(`DNS Resolution Failed: ${url}`)
        }
      }
    })
    
    // Load the application and wait
    await page.goto('http://localhost:5173')
    await page.waitForTimeout(5000)
    
    // Try to make API calls
    await page.evaluate(async () => {
      try {
        await fetch('/api/health')
      } catch (error) {
        console.error('Health check failed:', error.message)
      }
      
      try {
        await fetch('/api/products', {
          headers: { 'Authorization': 'Bearer test' }
        })
      } catch (error) {
        console.error('Products API failed:', error.message)
      }
    })
    
    // Wait for any async errors
    await page.waitForTimeout(2000)
    
    // Report findings
    if (issues.length > 0) {
      console.log('❌ Critical Issues Found:')
      issues.forEach(issue => console.log(`   - ${issue}`))
    }
    
    if (warnings.length > 0) {
      console.log('⚠️ Warnings:')
      warnings.forEach(warning => console.log(`   - ${warning}`))
    }
    
    if (issues.length === 0 && warnings.length === 0) {
      console.log('✅ No startup issues detected')
    }
    
    // Critical issues should fail the test
    expect(issues.length).toBe(0)
  })

  test('should validate development server performance', async ({ page }) => {
    console.log('⚡ Validating development server performance...')
    
    const performanceMetrics = {
      frontendStartTime: 0,
      apiResponseTime: 0,
      pageLoadTime: 0,
      firstContentfulPaint: 0
    }
    
    // Measure frontend load time
    const frontendStart = Date.now()
    await page.goto('http://localhost:5173')
    await page.waitForLoadState('domcontentloaded')
    performanceMetrics.frontendStartTime = Date.now() - frontendStart
    
    // Measure page load time
    const pageStart = Date.now()
    await page.waitForLoadState('networkidle')
    performanceMetrics.pageLoadTime = Date.now() - pageStart
    
    // Measure API response time
    const apiStart = Date.now()
    const apiResponse = await page.request.get('/api/health')
    performanceMetrics.apiResponseTime = Date.now() - apiStart
    expect(apiResponse.status()).toBe(200)
    
    // Get web vitals if available
    const webVitals = await page.evaluate(() => {
      return new Promise((resolve) => {
        if ('web-vital' in window) {
          // Web vitals library is loaded
          resolve({ fcp: 'available' })
        } else {
          // Use performance API
          const perfEntries = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
          resolve({
            domContentLoaded: perfEntries?.domContentLoadedEventEnd - perfEntries?.domContentLoadedEventStart,
            loadComplete: perfEntries?.loadEventEnd - perfEntries?.loadEventStart
          })
        }
      })
    })
    
    console.log('📊 Performance Metrics:')
    console.log(`   Frontend Start: ${performanceMetrics.frontendStartTime}ms`)
    console.log(`   Page Load: ${performanceMetrics.pageLoadTime}ms`)
    console.log(`   API Response: ${performanceMetrics.apiResponseTime}ms`)
    console.log(`   Web Vitals: ${JSON.stringify(webVitals)}`)
    
    // Performance thresholds for development environment
    expect(performanceMetrics.frontendStartTime).toBeLessThan(5000) // 5 seconds
    expect(performanceMetrics.pageLoadTime).toBeLessThan(10000) // 10 seconds
    expect(performanceMetrics.apiResponseTime).toBeLessThan(2000) // 2 seconds
    
    console.log('✅ All performance metrics within acceptable ranges')
  })
})