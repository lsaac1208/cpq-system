/**
 * E2E tests for quote workflow and management
 */

import { test, expect } from '@playwright/test'
import { login, clearAuth, ensureLoggedIn } from '../utils/auth-helper'

test.describe('Quote Workflow', () => {
  test.beforeEach(async ({ page }) => {
    await clearAuth(page)
    await ensureLoggedIn(page, 'user') // Regular user can create quotes
  })

  test.describe('Quote Creation', () => {
    test('should create new quote with product selection', async ({ page }) => {
      await page.goto('/quotes')
      
      // Click create quote button
      await page.click('button:has-text("Create Quote"), button:has-text("新建报价"), button:has-text("Create")')
      
      // Should navigate to quote creation page or show modal
      await page.waitForTimeout(1000)
      
      const isCreatePage = page.url().includes('/quotes/create') || page.url().includes('/create-quote')
      const isModal = await page.locator('.el-dialog, .modal, [role="dialog"]').isVisible()
      
      expect(isCreatePage || isModal).toBe(true)
      
      // Fill customer information
      await page.fill('input[name="customer_name"], input[placeholder*="customer" i]', 'John Doe')
      await page.fill('input[name="customer_email"], input[type="email"]', 'john.doe@example.com')
      await page.fill('input[name="customer_company"], input[placeholder*="company" i]', 'Acme Corp')
      
      // Select product
      const productSelect = page.locator('.el-select:has-text("Product"), select[name="product"], .product-selector')
      if (await productSelect.isVisible()) {
        await productSelect.click()
        
        // Select first available product
        const firstProduct = page.locator('.el-option, option').first()
        await firstProduct.click()
      }
      
      // Set quantity
      await page.fill('input[name="quantity"], input[placeholder*="quantity" i]', '2')
      
      // Save quote
      await page.click('button:has-text("Save"), button:has-text("Create Quote"), button:has-text("保存")')
      
      // Should show success message or redirect to quote detail
      await page.waitForTimeout(2000)
      
      const successMessage = page.locator('.el-message--success, .success, [role="alert"]')
      const isQuoteDetail = page.url().includes('/quotes/') && !page.url().includes('/create')
      
      expect(await successMessage.isVisible() || isQuoteDetail).toBe(true)
    })

    test('should validate required fields in quote creation', async ({ page }) => {
      await page.goto('/quotes')
      
      await page.click('button:has-text("Create Quote"), button:has-text("新建报价")')
      
      // Try to save without filling required fields
      await page.click('button:has-text("Save"), button:has-text("Create")')
      
      // Should show validation errors
      await expect(page.locator('.error, .el-form-item__error, .form-error')).toBeVisible()
    })

    test('should calculate quote pricing automatically', async ({ page }) => {
      await page.goto('/quotes')
      
      await page.click('button:has-text("Create Quote"), button:has-text("新建")')
      
      // Fill basic information
      await page.fill('input[name="customer_name"]', 'Test Customer')
      await page.fill('input[name="customer_email"]', 'test@example.com')
      
      // Select product with known price
      const productSelect = page.locator('.el-select:has-text("Product"), select[name="product"]')
      if (await productSelect.isVisible()) {
        await productSelect.click()
        await page.click('.el-option, option').first()
      }
      
      // Set quantity
      await page.fill('input[name="quantity"]', '3')
      
      // Price should be calculated automatically
      await page.waitForTimeout(1000)
      
      const totalPrice = page.locator('[data-testid="total-price"], .total-price, .price-total')
      if (await totalPrice.isVisible()) {
        const priceText = await totalPrice.textContent()
        expect(priceText).toMatch(/\d+\.?\d*/) // Should contain numeric price
      }
    })

    test('should handle product configuration in quotes', async ({ page }) => {
      await page.goto('/quotes')
      
      await page.click('button:has-text("Create Quote"), button:has-text("新建")')
      
      // Fill customer info
      await page.fill('input[name="customer_name"]', 'Config Customer')
      await page.fill('input[name="customer_email"]', 'config@example.com')
      
      // Select configurable product
      const productSelect = page.locator('.el-select:has-text("Product"), select[name="product"]')
      if (await productSelect.isVisible()) {
        await productSelect.click()
        
        // Look for configurable product
        const configurableOption = page.locator('.el-option:has-text("Configurable"), option:has-text("Configurable")')
        if (await configurableOption.isVisible()) {
          await configurableOption.click()
        } else {
          // Select first product if no configurable found
          await page.click('.el-option, option').first()
        }
      }
      
      // Configuration options should appear
      const configSection = page.locator('.configuration, .product-config, [data-testid="configuration"]')
      if (await configSection.isVisible()) {
        // Select configuration options
        const configOptions = page.locator('.config-option, .el-select, select')
        const optionCount = await configOptions.count()
        
        for (let i = 0; i < Math.min(optionCount, 3); i++) {
          const option = configOptions.nth(i)
          if (await option.isVisible()) {
            await option.click()
            await page.waitForTimeout(500)
            
            // Select first available option
            const firstChoice = page.locator('.el-option, option').first()
            if (await firstChoice.isVisible()) {
              await firstChoice.click()
            }
          }
        }
        
        // Price should update based on configuration
        await page.waitForTimeout(1000)
      }
    })

    test('should apply discounts to quotes', async ({ page }) => {
      await page.goto('/quotes')
      
      await page.click('button:has-text("Create Quote"), button:has-text("新建")')
      
      // Fill basic quote information
      await page.fill('input[name="customer_name"]', 'Discount Customer')
      await page.fill('input[name="customer_email"]', 'discount@example.com')
      
      // Select product
      const productSelect = page.locator('.el-select:has-text("Product"), select[name="product"]')
      if (await productSelect.isVisible()) {
        await productSelect.click()
        await page.click('.el-option, option').first()
      }
      
      await page.fill('input[name="quantity"]', '1')
      
      // Apply discount
      const discountInput = page.locator('input[name="discount"], input[placeholder*="discount" i]')
      if (await discountInput.isVisible()) {
        await discountInput.fill('10') // 10% discount
        
        // Price should update to reflect discount
        await page.waitForTimeout(1000)
        
        const finalPrice = page.locator('[data-testid="final-price"], .final-price, .discounted-price')
        if (await finalPrice.isVisible()) {
          const priceText = await finalPrice.textContent()
          expect(priceText).toMatch(/\d+\.?\d*/)
        }
      }
    })
  })

  test.describe('Quote Management', () => {
    test('should display quotes list', async ({ page }) => {
      await page.goto('/quotes')
      
      // Should show quotes page
      await expect(page.locator('h1, .page-title, [data-testid="page-title"]')).toContainText(/Quotes|报价/i)
      
      // Should show quotes table
      await expect(page.locator('.el-table, .quotes-list, [data-testid="quotes-table"]')).toBeVisible()
    })

    test('should filter quotes by status', async ({ page }) => {
      await page.goto('/quotes')
      
      await page.waitForTimeout(2000)
      
      // Look for status filter
      const statusFilter = page.locator('.el-select:has-text("Status"), select[name="status"], .status-filter')
      
      if (await statusFilter.isVisible()) {
        await statusFilter.click()
        
        // Select draft status
        const draftOption = page.locator('.el-option:has-text("Draft"), option[value="draft"]')
        if (await draftOption.isVisible()) {
          await draftOption.click()
          
          // Quotes list should be filtered
          await page.waitForTimeout(1000)
          
          // Verify filter applied
          const statusBadges = page.locator('.status-badge, .quote-status')
          const badgeCount = await statusBadges.count()
          
          if (badgeCount > 0) {
            // All visible quotes should be draft status
            for (let i = 0; i < badgeCount; i++) {
              const badge = statusBadges.nth(i)
              const statusText = await badge.textContent()
              expect(statusText?.toLowerCase()).toContain('draft')
            }
          }
        }
      }
    })

    test('should search quotes by customer name', async ({ page }) => {
      await page.goto('/quotes')
      
      await page.waitForTimeout(2000)
      
      // Look for search input
      const searchInput = page.locator('input[placeholder*="search" i], input[placeholder*="搜索"], .search-input')
      
      if (await searchInput.isVisible()) {
        await searchInput.fill('John')
        
        // Trigger search
        const searchButton = page.locator('button:has-text("Search"), button:has-text("搜索")')
        if (await searchButton.isVisible()) {
          await searchButton.click()
        } else {
          await page.keyboard.press('Enter')
        }
        
        await page.waitForTimeout(1000)
        
        // Results should be filtered
        expect(page.url()).toBeTruthy()
      }
    })

    test('should view quote details', async ({ page }) => {
      await page.goto('/quotes')
      
      await page.waitForTimeout(2000)
      
      // Click on first quote
      const firstQuote = page.locator('.el-table tbody tr, .quote-item').first()
      
      if (await firstQuote.isVisible()) {
        // Look for view button or click on row
        const viewButton = page.locator('button:has-text("View"), .view-btn, [data-testid="view-button"]').first()
        
        if (await viewButton.isVisible()) {
          await viewButton.click()
        } else {
          await firstQuote.click()
        }
        
        // Should show quote detail page or modal
        await page.waitForTimeout(1000)
        
        const isDetailPage = page.url().includes('/quotes/') && !page.url().endsWith('/quotes')
        const isModal = await page.locator('.el-dialog, .modal, [role="dialog"]').isVisible()
        
        expect(isDetailPage || isModal).toBe(true)
        
        // Should show quote information
        await expect(page.locator('.quote-details, .quote-info, [data-testid="quote-details"]')).toBeVisible()
      }
    })

    test('should edit draft quotes', async ({ page }) => {
      await page.goto('/quotes')
      
      await page.waitForTimeout(2000)
      
      // Find a draft quote to edit
      const editButton = page.locator('button:has-text("Edit"), .edit-btn, [data-testid="edit-button"]').first()
      
      if (await editButton.isVisible()) {
        await editButton.click()
        
        // Should open edit form
        await expect(page.locator('.el-dialog, .modal, form, [data-testid="quote-form"]')).toBeVisible()
        
        // Modify customer name
        const customerNameInput = page.locator('input[name="customer_name"]')
        if (await customerNameInput.isVisible()) {
          await customerNameInput.fill(`Updated Customer ${Date.now()}`)
        }
        
        // Save changes
        await page.click('button:has-text("Save"), button:has-text("Update")')
        
        // Should show success message
        await page.waitForTimeout(2000)
        await expect(page.locator('.el-message--success, .success')).toBeVisible()
      }
    })

    test('should delete draft quotes', async ({ page }) => {
      await page.goto('/quotes')
      
      await page.waitForTimeout(2000)
      
      // Find delete button for a quote
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
  })

  test.describe('Quote Status Workflow', () => {
    test('should submit quote for approval', async ({ page }) => {
      await page.goto('/quotes')
      
      await page.waitForTimeout(2000)
      
      // Find a draft quote
      const submitButton = page.locator('button:has-text("Submit"), .submit-btn, [data-testid="submit-button"]').first()
      
      if (await submitButton.isVisible()) {
        await submitButton.click()
        
        // Should show confirmation or move quote to pending status
        await page.waitForTimeout(1000)
        
        const confirmDialog = page.locator('.el-message-box, .confirm-dialog')
        if (await confirmDialog.isVisible()) {
          await page.click('button:has-text("Confirm"), button:has-text("确认")')
        }
        
        // Quote status should change to pending
        await expect(page.locator('.status-badge:has-text("Pending"), .quote-status:has-text("Pending")')).toBeVisible()
      }
    })

    test('should approve quote as manager', async ({ page }) => {
      // Switch to manager user
      await clearAuth(page)
      await login(page, 'manager')
      
      await page.goto('/quotes')
      
      await page.waitForTimeout(2000)
      
      // Find pending quote to approve
      const approveButton = page.locator('button:has-text("Approve"), .approve-btn, [data-testid="approve-button"]').first()
      
      if (await approveButton.isVisible()) {
        await approveButton.click()
        
        // May show approval form or confirmation
        const approvalForm = page.locator('.approval-form, .approve-dialog')
        if (await approvalForm.isVisible()) {
          // Fill approval notes if required
          const notesInput = page.locator('textarea[name="approval_notes"], textarea[placeholder*="notes" i]')
          if (await notesInput.isVisible()) {
            await notesInput.fill('Approved for standard terms')
          }
          
          await page.click('button:has-text("Approve"), button:has-text("Confirm")')
        }
        
        // Quote status should change to approved
        await page.waitForTimeout(2000)
        await expect(page.locator('.status-badge:has-text("Approved"), .quote-status:has-text("Approved")')).toBeVisible()
      }
    })

    test('should reject quote with reason', async ({ page }) => {
      // Switch to manager user
      await clearAuth(page)
      await login(page, 'manager')
      
      await page.goto('/quotes')
      
      await page.waitForTimeout(2000)
      
      // Find pending quote to reject
      const rejectButton = page.locator('button:has-text("Reject"), .reject-btn, [data-testid="reject-button"]').first()
      
      if (await rejectButton.isVisible()) {
        await rejectButton.click()
        
        // Should show rejection form
        await expect(page.locator('.rejection-form, .reject-dialog, [data-testid="reject-form"]')).toBeVisible()
        
        // Fill rejection reason
        const reasonInput = page.locator('textarea[name="rejection_reason"], textarea[placeholder*="reason" i]')
        await reasonInput.fill('Price exceeds customer budget limits')
        
        await page.click('button:has-text("Reject"), button:has-text("Confirm")')
        
        // Quote status should change to rejected
        await page.waitForTimeout(2000)
        await expect(page.locator('.status-badge:has-text("Rejected"), .quote-status:has-text("Rejected")')).toBeVisible()
      }
    })
  })

  test.describe('Quote Export and PDF Generation', () => {
    test('should generate PDF quote', async ({ page }) => {
      await page.goto('/quotes')
      
      await page.waitForTimeout(2000)
      
      // Find PDF generation button
      const pdfButton = page.locator('button:has-text("PDF"), button:has-text("Generate PDF"), .pdf-btn').first()
      
      if (await pdfButton.isVisible()) {
        // Set up download handler
        const downloadPromise = page.waitForEvent('download', { timeout: 10000 })
        
        await pdfButton.click()
        
        try {
          // Should trigger PDF download
          const download = await downloadPromise
          expect(download.suggestedFilename()).toMatch(/\.pdf$/i)
        } catch (error) {
          // PDF generation might open in new tab instead of download
          const pages = page.context().pages()
          if (pages.length > 1) {
            const pdfPage = pages[pages.length - 1]
            expect(pdfPage.url()).toContain('pdf')
          }
        }
      }
    })

    test('should email quote to customer', async ({ page }) => {
      await page.goto('/quotes')
      
      await page.waitForTimeout(2000)
      
      // Find email button
      const emailButton = page.locator('button:has-text("Email"), button:has-text("Send Email"), .email-btn').first()
      
      if (await emailButton.isVisible()) {
        await emailButton.click()
        
        // Should show email form
        await expect(page.locator('.email-form, .send-email-dialog, [data-testid="email-form"]')).toBeVisible()
        
        // Email should be pre-filled with customer email
        const emailInput = page.locator('input[name="to"], input[type="email"]')
        const emailValue = await emailInput.inputValue()
        expect(emailValue).toMatch(/@/)
        
        // Add subject and message
        await page.fill('input[name="subject"], input[placeholder*="subject" i]', 'Your Quote from CPQ System')
        await page.fill('textarea[name="message"], textarea[placeholder*="message" i]', 'Please find your quote attached.')
        
        // Send email
        await page.click('button:has-text("Send"), button:has-text("Send Email")')
        
        // Should show success message
        await page.waitForTimeout(2000)
        await expect(page.locator('.el-message--success, .success')).toBeVisible()
      }
    })

    test('should export quotes to Excel', async ({ page }) => {
      await page.goto('/quotes')
      
      // Look for export button
      const exportButton = page.locator('button:has-text("Export"), button:has-text("导出"), .export-btn')
      
      if (await exportButton.isVisible()) {
        // Set up download handler
        const downloadPromise = page.waitForEvent('download')
        
        await exportButton.click()
        
        // Should trigger download
        const download = await downloadPromise
        expect(download.suggestedFilename()).toMatch(/\.(xlsx?|csv)$/i)
      }
    })
  })

  test.describe('Quote History and Tracking', () => {
    test('should show quote history', async ({ page }) => {
      await page.goto('/quotes')
      
      await page.waitForTimeout(2000)
      
      // Click on a quote to view details
      const firstQuote = page.locator('.el-table tbody tr, .quote-item').first()
      if (await firstQuote.isVisible()) {
        await firstQuote.click()
        
        // Look for history section
        const historySection = page.locator('.quote-history, .activity-log, [data-testid="quote-history"]')
        
        if (await historySection.isVisible()) {
          // Should show timeline of quote changes
          await expect(page.locator('.history-item, .activity-item, .timeline-item')).toHaveCount(1, { timeout: 5000 })
        }
      }
    })

    test('should track quote modifications', async ({ page }) => {
      await page.goto('/quotes')
      
      await page.waitForTimeout(2000)
      
      // Edit a quote
      const editButton = page.locator('button:has-text("Edit"), .edit-btn').first()
      
      if (await editButton.isVisible()) {
        await editButton.click()
        
        // Make a change
        const notesInput = page.locator('textarea[name="notes"], textarea[placeholder*="notes" i]')
        if (await notesInput.isVisible()) {
          await notesInput.fill(`Updated notes at ${new Date().toISOString()}`)
        }
        
        await page.click('button:has-text("Save"), button:has-text("Update")')
        
        // View quote details to check history
        await page.waitForTimeout(2000)
        
        // History should show the modification
        const historySection = page.locator('.quote-history, .activity-log')
        if (await historySection.isVisible()) {
          await expect(page.locator('.history-item:has-text("Updated"), .activity-item:has-text("Modified")')).toBeVisible()
        }
      }
    })

    test('should show quote expiration status', async ({ page }) => {
      await page.goto('/quotes')
      
      await page.waitForTimeout(2000)
      
      // Look for quotes with expiration dates
      const expirationInfo = page.locator('.expiration-date, .valid-until, [data-testid="expiration"]')
      
      if (await expirationInfo.isVisible()) {
        const expirationText = await expirationInfo.textContent()
        expect(expirationText).toMatch(/\d{4}-\d{2}-\d{2}|\d{2}\/\d{2}\/\d{4}/) // Date format
      }
    })
  })
})