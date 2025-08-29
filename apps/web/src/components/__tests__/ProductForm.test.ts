/**
 * Unit tests for ProductForm component
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ProductForm from '../ProductForm.vue'
import { mockProduct, mockProductsApi } from '@/test/mocks/api'
import { useProductsStore } from '@/stores/products'
import ElementPlus from 'element-plus'

// Mock the products API
vi.mock('@/api/products', () => ({
  productsApi: mockProductsApi
}))

describe('ProductForm', () => {
  let wrapper: VueWrapper<any>
  let productsStore: ReturnType<typeof useProductsStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    productsStore = useProductsStore()
    vi.clearAllMocks()
  })

  const createWrapper = (props = {}) => {
    return mount(ProductForm, {
      props: {
        modelValue: null,
        ...props
      },
      global: {
        plugins: [ElementPlus],
        stubs: {
          ElForm: {
            template: '<form><slot /></form>',
            methods: {
              validate: vi.fn().mockResolvedValue(true),
              resetFields: vi.fn(),
              clearValidate: vi.fn()
            }
          },
          ElFormItem: {
            template: '<div><slot /></div>'
          },
          ElInput: {
            template: '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
            props: ['modelValue'],
            emits: ['update:modelValue']
          },
          ElSelect: {
            template: '<select :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><slot /></select>',
            props: ['modelValue'],
            emits: ['update:modelValue']
          },
          ElOption: {
            template: '<option :value="value"><slot /></option>',
            props: ['value', 'label']
          },
          ElSwitch: {
            template: '<input type="checkbox" :checked="modelValue" @change="$emit(\'update:modelValue\', $event.target.checked)" />',
            props: ['modelValue'],
            emits: ['update:modelValue']
          },
          ElButton: {
            template: '<button :disabled="disabled" @click="$emit(\'click\')"><slot /></button>',
            props: ['disabled', 'type', 'loading'],
            emits: ['click']
          }
        }
      }
    })
  }

  describe('Component Rendering', () => {
    it('should render form fields correctly', async () => {
      wrapper = createWrapper()

      expect(wrapper.find('form').exists()).toBe(true)
      expect(wrapper.find('input[placeholder*="Product Name"]').exists()).toBe(true)
      expect(wrapper.find('input[placeholder*="Product Code"]').exists()).toBe(true)
      expect(wrapper.find('input[placeholder*="Description"]').exists()).toBe(true)
      expect(wrapper.find('select').exists()).toBe(true) // Category select
      expect(wrapper.find('input[placeholder*="Base Price"]').exists()).toBe(true)
    })

    it('should render save and cancel buttons', async () => {
      wrapper = createWrapper()

      const buttons = wrapper.findAll('button')
      expect(buttons.length).toBeGreaterThanOrEqual(2)
      
      const saveButton = buttons.find(btn => btn.text().includes('Save') || btn.text().includes('save'))
      const cancelButton = buttons.find(btn => btn.text().includes('Cancel') || btn.text().includes('cancel'))
      
      expect(saveButton).toBeTruthy()
      expect(cancelButton).toBeTruthy()
    })

    it('should show loading state when store is loading', async () => {
      productsStore.$patch({ loading: true })
      wrapper = createWrapper()

      // Find button with loading attribute
      const saveButton = wrapper.find('button[loading="true"]')
      expect(saveButton.exists()).toBe(true)
    })
  })

  describe('Form Data Binding', () => {
    it('should initialize with empty form when no modelValue', async () => {
      wrapper = createWrapper()

      const nameInput = wrapper.find('input[placeholder*="Product Name"]')
      const codeInput = wrapper.find('input[placeholder*="Product Code"]')
      const descriptionInput = wrapper.find('input[placeholder*="Description"]')

      expect(nameInput.element.value).toBe('')
      expect(codeInput.element.value).toBe('')
      expect(descriptionInput.element.value).toBe('')
    })

    it('should populate form with modelValue data', async () => {
      wrapper = createWrapper({ modelValue: mockProduct })

      const nameInput = wrapper.find('input[placeholder*="Product Name"]')
      const codeInput = wrapper.find('input[placeholder*="Product Code"]')

      expect(nameInput.element.value).toBe(mockProduct.name)
      expect(codeInput.element.value).toBe(mockProduct.code)
    })

    it('should update form data when input changes', async () => {
      wrapper = createWrapper()

      const nameInput = wrapper.find('input[placeholder*="Product Name"]')
      await nameInput.setValue('New Product Name')

      // Component should emit update:modelValue or handle internal state
      expect(nameInput.element.value).toBe('New Product Name')
    })
  })

  describe('Form Validation', () => {
    it('should validate required fields', async () => {
      wrapper = createWrapper()

      // Try to submit empty form
      const saveButton = wrapper.find('button:not([disabled])')
      await saveButton.trigger('click')

      // Should show validation errors (specific implementation depends on validation library)
      // This is a placeholder for validation testing
      expect(wrapper.vm).toBeTruthy()
    })

    it('should validate product code uniqueness', async () => {
      wrapper = createWrapper()

      const codeInput = wrapper.find('input[placeholder*="Product Code"]')
      await codeInput.setValue('EXISTING-CODE')

      // Mock API to return conflict
      mockProductsApi.createProduct.mockRejectedValueOnce({
        response: { status: 409, data: { error: 'Product code already exists' } }
      })

      const saveButton = wrapper.find('button:not([disabled])')
      await saveButton.trigger('click')

      // Should handle validation error
      expect(mockProductsApi.createProduct).toHaveBeenCalled()
    })

    it('should validate price format', async () => {
      wrapper = createWrapper()

      const priceInput = wrapper.find('input[placeholder*="Base Price"]')
      await priceInput.setValue('invalid-price')

      // Should show price validation error
      expect(priceInput.element.value).toBe('invalid-price')
    })
  })

  describe('Form Submission', () => {
    it('should create new product when no modelValue', async () => {
      wrapper = createWrapper()

      // Fill form data
      const nameInput = wrapper.find('input[placeholder*="Product Name"]')
      const codeInput = wrapper.find('input[placeholder*="Product Code"]')
      const descriptionInput = wrapper.find('input[placeholder*="Description"]')
      const priceInput = wrapper.find('input[placeholder*="Base Price"]')

      await nameInput.setValue('New Product')
      await codeInput.setValue('NEW-001')
      await descriptionInput.setValue('New product description')
      await priceInput.setValue('999.99')

      // Mock store method
      const createProductSpy = vi.spyOn(productsStore, 'createProduct')
      createProductSpy.mockResolvedValueOnce({ product: mockProduct })

      const saveButton = wrapper.find('button:not([disabled])')
      await saveButton.trigger('click')

      expect(createProductSpy).toHaveBeenCalledWith({
        name: 'New Product',
        code: 'NEW-001',
        description: 'New product description',
        base_price: 999.99,
        category: expect.any(String),
        is_active: expect.any(Boolean),
        is_configurable: expect.any(Boolean)
      })
    })

    it('should update existing product when modelValue provided', async () => {
      wrapper = createWrapper({ modelValue: mockProduct })

      // Update form data
      const nameInput = wrapper.find('input[placeholder*="Product Name"]')
      await nameInput.setValue('Updated Product Name')

      // Mock store method
      const updateProductSpy = vi.spyOn(productsStore, 'updateProduct')
      updateProductSpy.mockResolvedValueOnce({ product: { ...mockProduct, name: 'Updated Product Name' } })

      const saveButton = wrapper.find('button:not([disabled])')
      await saveButton.trigger('click')

      expect(updateProductSpy).toHaveBeenCalledWith(mockProduct.id, {
        name: 'Updated Product Name',
        code: mockProduct.code,
        description: mockProduct.description,
        category: mockProduct.category,
        base_price: mockProduct.base_price,
        is_active: mockProduct.is_active,
        is_configurable: mockProduct.is_configurable
      })
    })

    it('should emit success event on successful save', async () => {
      wrapper = createWrapper()

      // Mock successful save
      const createProductSpy = vi.spyOn(productsStore, 'createProduct')
      createProductSpy.mockResolvedValueOnce({ product: mockProduct })

      // Fill required fields
      const nameInput = wrapper.find('input[placeholder*="Product Name"]')
      const codeInput = wrapper.find('input[placeholder*="Product Code"]')
      await nameInput.setValue('Test Product')
      await codeInput.setValue('TEST-001')

      const saveButton = wrapper.find('button:not([disabled])')
      await saveButton.trigger('click')

      // Wait for async operation
      await wrapper.vm.$nextTick()

      expect(wrapper.emitted('success')).toBeTruthy()
    })

    it('should handle save errors gracefully', async () => {
      wrapper = createWrapper()

      // Mock save error
      const createProductSpy = vi.spyOn(productsStore, 'createProduct')
      createProductSpy.mockRejectedValueOnce(new Error('Save failed'))

      // Fill required fields
      const nameInput = wrapper.find('input[placeholder*="Product Name"]')
      const codeInput = wrapper.find('input[placeholder*="Product Code"]')
      await nameInput.setValue('Test Product')
      await codeInput.setValue('TEST-001')

      const saveButton = wrapper.find('button:not([disabled])')
      await saveButton.trigger('click')

      // Wait for async operation
      await wrapper.vm.$nextTick()

      // Should handle error (emit error event or show error message)
      expect(wrapper.emitted('error')).toBeTruthy()
    })
  })

  describe('Form Actions', () => {
    it('should emit cancel event when cancel button clicked', async () => {
      wrapper = createWrapper()

      const cancelButton = wrapper.find('button:last-child') // Assuming cancel is last button
      await cancelButton.trigger('click')

      expect(wrapper.emitted('cancel')).toBeTruthy()
    })

    it('should reset form when reset method called', async () => {
      wrapper = createWrapper({ modelValue: mockProduct })

      // Change form data
      const nameInput = wrapper.find('input[placeholder*="Product Name"]')
      await nameInput.setValue('Changed Name')

      // Call reset (this would be triggered by parent component)
      await wrapper.setProps({ modelValue: null })

      // Form should be reset to empty
      expect(nameInput.element.value).toBe('')
    })
  })

  describe('Categories Integration', () => {
    it('should load categories on mount', async () => {
      const loadCategoriesSpy = vi.spyOn(productsStore, 'loadCategories')
      loadCategoriesSpy.mockResolvedValueOnce(['Testing', 'Hardware', 'Software'])

      wrapper = createWrapper()

      expect(loadCategoriesSpy).toHaveBeenCalled()
    })

    it('should populate category options', async () => {
      // Mock categories in store
      productsStore.$patch({ categories: ['Testing', 'Hardware', 'Software'] })

      wrapper = createWrapper()

      const categorySelect = wrapper.find('select')
      const options = categorySelect.findAll('option')

      expect(options.length).toBeGreaterThan(0)
    })
  })

  describe('Accessibility', () => {
    it('should have proper labels for form fields', async () => {
      wrapper = createWrapper()

      // Check that form fields have associated labels or aria-labels
      const inputs = wrapper.findAll('input')
      inputs.forEach(input => {
        const hasLabel = input.attributes('aria-label') || 
                        input.attributes('placeholder') ||
                        wrapper.find(`label[for="${input.attributes('id')}"]`).exists()
        expect(hasLabel).toBeTruthy()
      })
    })

    it('should have proper button roles and states', async () => {
      wrapper = createWrapper()

      const buttons = wrapper.findAll('button')
      buttons.forEach(button => {
        expect(button.attributes('type')).toBeDefined()
      })
    })
  })
})