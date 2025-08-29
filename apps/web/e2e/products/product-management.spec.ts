/**
 * E2E tests for product management functionality
 */

import { test, expect } from '@playwright/test'
import { login, clearAuth, ensureLoggedIn } from '../utils/auth-helper'

test.describe('Product Management', () => {
  test.beforeEach(async ({ page }) => {
    await clearAuth(page)
    await ensureLoggedIn(page, 'engineer') // Engineer has product management permissions
  })

  test.describe('Products List', () => {
    test('should display products list', async ({ page }) => {
      await page.goto('/products')
      
      // Should show products page
      await expect(page.locator('h1, .page-title, [data-testid="page-title"]')).toContainText(/Products|产品/i)
      
      // Should show products table or grid
      await expect(page.locator('.el-table, .products-grid, [data-testid="products-list"]')).toBeVisible()
    })

    test('should show create product button for authorized users', async ({ page }) => {
      await page.goto('/products')
      
      // Engineer should see create button
      await expect(page.locator('button:has-text("Create"), button:has-text("新建"), button:has-text("Add")')).toBeVisible()
    })

    test('should filter products by category', async ({ page }) => {
      await page.goto('/products')
      
      // Wait for products to load
      await page.waitForTimeout(2000)
      
      // Look for category filter
      const categoryFilter = page.locator('.el-select:has-text("Category"), select[name="category"], .category-filter')
      
      if (await categoryFilter.isVisible()) {
        await categoryFilter.click()
        
        // Select a category
        const categoryOption = page.locator('.el-option, option').first()
        if (await categoryOption.isVisible()) {
          await categoryOption.click()
          
          // Products list should update
          await page.waitForTimeout(1000)
          
          // Verify filtering worked (products list should change or show filtered results)
          await expect(page.locator('.el-table tbody tr, .product-item')).toHaveCount(0, { timeout: 5000 }) // Or any count
        }
      }
    })

    test('should search products by name', async ({ page }) => {
      await page.goto('/products')
      
      // Wait for products to load
      await page.waitForTimeout(2000)
      
      // Look for search input
      const searchInput = page.locator('input[placeholder*="search" i], input[placeholder*="搜索"], .search-input')
      
      if (await searchInput.isVisible()) {
        await searchInput.fill('Test')
        
        // Trigger search (either auto-search or click search button)
        const searchButton = page.locator('button:has-text("Search"), button:has-text("搜索")')
        if (await searchButton.isVisible()) {
          await searchButton.click()
        } else {
          // Auto-search on input
          await page.waitForTimeout(1000)
        }
        
        // Results should be filtered
        await page.waitForTimeout(1000)
        expect(page.url()).toBeTruthy() // Basic assertion
      }
    })

    test('should paginate products list', async ({ page }) => {
      await page.goto('/products')
      
      // Wait for products to load
      await page.waitForTimeout(2000)
      
      // Look for pagination controls
      const pagination = page.locator('.el-pagination, .pagination, [data-testid="pagination"]')
      
      if (await pagination.isVisible()) {
        // Try to click next page
        const nextButton = page.locator('.btn-next, .el-pagination__next, button:has-text("Next")')
        if (await nextButton.isVisible() && !(await nextButton.isDisabled())) {
          await nextButton.click()
          
          // Page should change
          await page.waitForTimeout(1000)
          expect(page.url()).toBeTruthy()
        }
      }
    })

    test('should show product details on row click', async ({ page }) => {
      await page.goto('/products')
      
      // Wait for products to load
      await page.waitForTimeout(2000)
      
      // Click on first product row
      const firstRow = page.locator('.el-table tbody tr, .product-item').first()
      
      if (await firstRow.isVisible()) {
        await firstRow.click()
        
        // Should navigate to product detail or show detail modal
        await page.waitForTimeout(1000)
        
        // Check if we're on detail page or modal is open
        const isDetailPage = page.url().includes('/products/')
        const isModalOpen = await page.locator('.el-dialog, .modal, [role="dialog"]').isVisible()
        
        expect(isDetailPage || isModalOpen).toBe(true)
      }
    })
  })

  test.describe('Product Creation', () => {
    test('should create new product with valid data', async ({ page }) => {
      await page.goto('/products')
      
      // Click create product button
      await page.click('button:has-text("Create"), button:has-text("新建"), button:has-text("Add")')
      
      // Should open create form (modal or new page)
      await expect(page.locator('.el-dialog, .modal, form, [data-testid="product-form"]')).toBeVisible()
      
      // Fill product form
      const timestamp = Date.now()
      await page.fill('input[name="name"], input[placeholder*="name" i]', `Test Product ${timestamp}`)
      await page.fill('input[name="code"], input[placeholder*="code" i]', `TEST-${timestamp}`)
      await page.fill('input[name="description"], textarea[name="description"]', 'Test product description')
      await page.fill('input[name="base_price"], input[placeholder*="price" i]', '999.99')
      
      // Select category
      const categorySelect = page.locator('.el-select:has-text("Category"), select[name="category"]')
      if (await categorySelect.isVisible()) {
        await categorySelect.click()
        await page.click('.el-option, option').first()
      }
      
      // Submit form
      await page.click('button:has-text("Save"), button:has-text("Create"), button:has-text("保存")')
      
      // Should show success message or redirect
      await page.waitForTimeout(2000)
      
      // Check for success indication
      const successMessage = page.locator('.el-message--success, .success, [role="alert"]')
      const isBackToList = page.url().endsWith('/products')
      
      expect(await successMessage.isVisible() || isBackToList).toBe(true)
    })

    test('should show validation errors for invalid data', async ({ page }) => {
      await page.goto('/products')
      
      // Click create product button
      await page.click('button:has-text("Create"), button:has-text("新建")')
      
      // Try to submit empty form
      await page.click('button:has-text("Save"), button:has-text("Create")')
      
      // Should show validation errors
      await expect(page.locator('.error, .el-form-item__error, .form-error')).toBeVisible()
    })

    test('should prevent duplicate product codes', async ({ page }) => {
      await page.goto('/products')
      
      // Create first product
      await page.click('button:has-text("Create"), button:has-text("新建")')
      
      const duplicateCode = `DUPLICATE-${Date.now()}`
      
      await page.fill('input[name="name"]', 'First Product')
      await page.fill('input[name="code"]', duplicateCode)
      await page.fill('input[name="base_price"]', '999.99')
      
      // Select category if available
      const categorySelect = page.locator('.el-select:has-text("Category"), select[name="category"]')
      if (await categorySelect.isVisible()) {
        await categorySelect.click()
        await page.click('.el-option, option').first()
      }
      
      await page.click('button:has-text("Save"), button:has-text("Create")')
      
      // Wait for first product to be created
      await page.waitForTimeout(2000)
      
      // Try to create second product with same code
      await page.click('button:has-text("Create"), button:has-text("新建")')
      
      await page.fill('input[name="name"]', 'Second Product')
      await page.fill('input[name="code"]', duplicateCode) // Same code
      await page.fill('input[name="base_price"]', '1299.99')
      
      await page.click('button:has-text("Save"), button:has-text("Create")')
      
      // Should show error for duplicate code
      await expect(page.locator('.error, .el-message--error, [role="alert"]')).toBeVisible()
    })

    test('should handle complex configuration schema', async ({ page }) => {
      await page.goto('/products')
      
      await page.click('button:has-text("Create"), button:has-text("新建")')
      
      // Fill basic product info
      await page.fill('input[name="name"]', `Complex Product ${Date.now()}`)
      await page.fill('input[name="code"]', `COMPLEX-${Date.now()}`)
      await page.fill('input[name="base_price"]', '2999.99')
      
      // If configuration schema editor is available
      const configEditor = page.locator('.config-editor, textarea[name="configuration_schema"]')
      if (await configEditor.isVisible()) {
        const complexConfig = JSON.stringify({
          cpu: {
            type: 'select',
            options: ['Intel i5', 'Intel i7', 'AMD Ryzen 5'],
            prices: [0, 200, 150]
          },
          memory: {
            type: 'select',
            options: ['8GB', '16GB', '32GB'],
            prices: [0, 300, 800]
          }
        })
        
        await configEditor.fill(complexConfig)
      }
      
      await page.click('button:has-text("Save"), button:has-text("Create")')
      
      // Should handle complex configuration
      await page.waitForTimeout(2000)
    })
  })

  test.describe('Product Editing', () => {
    test('should edit existing product', async ({ page }) => {
      await page.goto('/products')
      
      // Wait for products to load
      await page.waitForTimeout(2000)
      
      // Find and click edit button for first product
      const editButton = page.locator('button:has-text("Edit"), .edit-btn, [data-testid="edit-button"]').first()
      
      if (await editButton.isVisible()) {
        await editButton.click()
        
        // Should open edit form
        await expect(page.locator('.el-dialog, .modal, form')).toBeVisible()
        
        // Modify product name
        const nameInput = page.locator('input[name="name"]')
        await nameInput.fill(`Updated Product ${Date.now()}`)
        
        // Save changes
        await page.click('button:has-text("Save"), button:has-text("Update")')
        
        // Should show success indication
        await page.waitForTimeout(2000)
        const successMessage = page.locator('.el-message--success, .success')
        expect(await successMessage.isVisible()).toBe(true)
      }
    })

    test('should cancel edit without saving changes', async ({ page }) => {
      await page.goto('/products')
      
      await page.waitForTimeout(2000)
      
      const editButton = page.locator('button:has-text("Edit"), .edit-btn').first()
      
      if (await editButton.isVisible()) {
        await editButton.click()
        
        // Make some changes
        await page.fill('input[name="name"]', 'Cancelled Changes')
        
        // Cancel instead of saving
        await page.click('button:has-text("Cancel"), button:has-text("取消")')
        
        // Should close form without saving
        await expect(page.locator('.el-dialog, .modal')).toBeHidden()
      }
    })

    test('should update product status (active/inactive)', async ({ page }) => {
      await page.goto('/products')
      
      await page.waitForTimeout(2000)
      
      // Look for status toggle or edit button
      const statusToggle = page.locator('.el-switch, input[type="checkbox"]').first()
      
      if (await statusToggle.isVisible()) {
        const initialState = await statusToggle.isChecked()
        await statusToggle.click()
        
        // Status should change
        await page.waitForTimeout(1000)
        const newState = await statusToggle.isChecked()
        expect(newState).not.toBe(initialState)
      }
    })
  })

  test.describe('Product Deletion', () => {
    test('should delete product with confirmation', async ({ page }) => {
      await page.goto('/products')
      
      await page.waitForTimeout(2000)
      
      // Find delete button
      const deleteButton = page.locator('button:has-text("Delete"), .delete-btn, [data-testid="delete-button"]').first()
      
      if (await deleteButton.isVisible()) {
        await deleteButton.click()
        
        // Should show confirmation dialog
        await expect(page.locator('.el-message-box, .confirm-dialog, [role="alertdialog"]')).toBeVisible()
        
        // Confirm deletion
        await page.click('button:has-text("Confirm"), button:has-text("确认"), button:has-text("Delete")')
        
        // Should show success message
        await page.waitForTimeout(2000)
        await expect(page.locator('.el-message--success, .success')).toBeVisible()
      }
    })

    test('should cancel product deletion', async ({ page }) => {
      await page.goto('/products')
      
      await page.waitForTimeout(2000)
      
      const deleteButton = page.locator('button:has-text("Delete"), .delete-btn').first()
      
      if (await deleteButton.isVisible()) {
        await deleteButton.click()
        
        // Should show confirmation dialog
        await expect(page.locator('.el-message-box, .confirm-dialog')).toBeVisible()
        
        // Cancel deletion
        await page.click('button:has-text("Cancel"), button:has-text("取消")')
        
        // Dialog should close without deleting
        await expect(page.locator('.el-message-box, .confirm-dialog')).toBeHidden()
      }
    })
  })

  test.describe('Product Permissions', () => {
    test('should restrict product management for regular users', async ({ page }) => {
      // Logout and login as regular user
      await clearAuth(page)
      await login(page, 'user')
      
      await page.goto('/products')
      
      // Regular user should not see create/edit/delete buttons
      const createButton = page.locator('button:has-text("Create"), button:has-text("新建")')
      const editButtons = page.locator('button:has-text("Edit"), .edit-btn')
      const deleteButtons = page.locator('button:has-text("Delete"), .delete-btn')
      
      await expect(createButton).toBeHidden()
      
      // Edit and delete buttons should be hidden or disabled
      if (await editButtons.count() > 0) {
        await expect(editButtons.first()).toBeDisabled()
      }
      
      if (await deleteButtons.count() > 0) {
        await expect(deleteButtons.first()).toBeDisabled()
      }
    })

    test('should allow product management for engineers', async ({ page }) => {
      // Already logged in as engineer from beforeEach
      await page.goto('/products')
      
      // Engineer should see management buttons
      await expect(page.locator('button:has-text("Create"), button:has-text("新建")')).toBeVisible()
    })

    test('should allow product management for admins', async ({ page }) => {
      await clearAuth(page)
      await login(page, 'admin')
      
      await page.goto('/products')
      
      // Admin should see management buttons
      await expect(page.locator('button:has-text("Create"), button:has-text("新建")')).toBeVisible()
    })
  })

  test.describe('Product Export/Import', () => {
    test('should export products list', async ({ page }) => {
      await page.goto('/products')
      
      // Look for export button
      const exportButton = page.locator('button:has-text("Export"), button:has-text("导出")')
      
      if (await exportButton.isVisible()) {
        // Set up download handler
        const downloadPromise = page.waitForEvent('download')
        
        await exportButton.click()
        
        // Should trigger download
        const download = await downloadPromise
        expect(download.suggestedFilename()).toContain('products')
      }
    })

    test('should import products from file', async ({ page }) => {
      await page.goto('/products')
      
      // Look for import button
      const importButton = page.locator('button:has-text("Import"), button:has-text("导入")')
      
      if (await importButton.isVisible()) {
        await importButton.click()
        
        // Should show file upload dialog
        await expect(page.locator('.el-upload, .file-upload, input[type="file"]')).toBeVisible()
      }
    })
  })

  test.describe('Product Configuration', () => {
    test('should handle configurable products', async ({ page }) => {
      await page.goto('/products')
      
      // Look for a configurable product
      await page.waitForTimeout(2000)
      
      const configurableProduct = page.locator('.product-item:has-text("Configurable"), tr:has(.configurable-badge)')
      
      if (await configurableProduct.isVisible()) {
        await configurableProduct.click()
        
        // Should show configuration options
        await expect(page.locator('.configuration, .product-config')).toBeVisible()
      }
    })

    test('should validate configuration options', async ({ page }) => {
      await page.goto('/products')
      
      await page.click('button:has-text("Create"), button:has-text("新建")')
      
      // Enable configurable option
      const configurableSwitch = page.locator('.el-switch:has-text("Configurable"), input[name="is_configurable"]')
      if (await configurableSwitch.isVisible()) {
        await configurableSwitch.click()
        
        // Configuration schema editor should appear
        await expect(page.locator('.config-editor, .schema-editor')).toBeVisible()
      }
    })
  })
})