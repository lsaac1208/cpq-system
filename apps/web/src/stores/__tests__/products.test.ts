/**
 * Unit tests for Products Store
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useProductsStore } from '../products'
import { mockProductsApi, mockProduct, mockProducts } from '@/test/mocks/api'

// Mock the products API
vi.mock('@/api/products', () => ({
  productsApi: mockProductsApi
}))

describe('Products Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const productsStore = useProductsStore()

      expect(productsStore.products).toEqual([])
      expect(productsStore.currentProduct).toBeNull()
      expect(productsStore.categories).toEqual([])
      expect(productsStore.loading).toBe(false)
      expect(productsStore.total).toBe(0)
      expect(productsStore.currentPage).toBe(1)
      expect(productsStore.pageSize).toBe(20)
    })
  })

  describe('Actions', () => {
    describe('loadProducts', () => {
      it('should load products successfully', async () => {
        const productsStore = useProductsStore()
        const mockResponse = {
          products: mockProducts,
          pagination: {
            page: 1,
            per_page: 20,
            total: mockProducts.length,
            pages: 1
          }
        }

        const result = await productsStore.loadProducts()

        expect(mockProductsApi.getProducts).toHaveBeenCalledWith(undefined)
        expect(productsStore.loading).toBe(false)
        expect(productsStore.products).toEqual(mockProducts)
        expect(productsStore.total).toBe(mockProducts.length)
        expect(productsStore.currentPage).toBe(1)
        expect(result).toEqual(mockResponse)
      })

      it('should load products with parameters', async () => {
        const productsStore = useProductsStore()
        const params = {
          category: 'Testing',
          is_active: true,
          page: 2,
          per_page: 10
        }

        await productsStore.loadProducts(params)

        expect(mockProductsApi.getProducts).toHaveBeenCalledWith(params)
      })

      it('should handle load products error', async () => {
        const productsStore = useProductsStore()
        const error = new Error('Failed to load products')
        mockProductsApi.getProducts.mockRejectedValueOnce(error)

        await expect(productsStore.loadProducts()).rejects.toThrow('Failed to load products')
        expect(productsStore.loading).toBe(false)
      })

      it('should set loading state during load', async () => {
        const productsStore = useProductsStore()

        // Make API call hang to test loading state
        let resolveLoad: (value: any) => void
        const loadPromise = new Promise(resolve => {
          resolveLoad = resolve
        })
        mockProductsApi.getProducts.mockReturnValueOnce(loadPromise)

        const resultPromise = productsStore.loadProducts()
        
        // Should be loading
        expect(productsStore.loading).toBe(true)

        // Resolve the promise
        const mockResponse = {
          products: mockProducts,
          pagination: { page: 1, per_page: 20, total: 2, pages: 1 }
        }
        resolveLoad!(mockResponse)
        await resultPromise

        // Should not be loading anymore
        expect(productsStore.loading).toBe(false)
      })
    })

    describe('loadProduct', () => {
      it('should load single product successfully', async () => {
        const productsStore = useProductsStore()
        const productId = 1

        const result = await productsStore.loadProduct(productId)

        expect(mockProductsApi.getProduct).toHaveBeenCalledWith(productId)
        expect(productsStore.loading).toBe(false)
        expect(productsStore.currentProduct).toEqual(mockProduct)
        expect(result).toEqual(mockProduct)
      })

      it('should handle load product error', async () => {
        const productsStore = useProductsStore()
        const productId = 999
        const error = new Error('Product not found')
        mockProductsApi.getProduct.mockRejectedValueOnce(error)

        await expect(productsStore.loadProduct(productId)).rejects.toThrow('Product not found')
        expect(productsStore.loading).toBe(false)
      })
    })

    describe('createProduct', () => {
      it('should create product successfully', async () => {
        const productsStore = useProductsStore()
        const productData = {
          name: 'New Product',
          code: 'NEW-001',
          category: 'New Category',
          base_price: 1999.99
        }

        // Initialize with existing products
        productsStore.$patch({ products: [...mockProducts] })

        const result = await productsStore.createProduct(productData)

        expect(mockProductsApi.createProduct).toHaveBeenCalledWith(productData)
        expect(productsStore.loading).toBe(false)
        expect(productsStore.products[0]).toEqual(mockProduct) // New product added to beginning
        expect(result).toEqual({ product: mockProduct })
      })

      it('should handle create product error', async () => {
        const productsStore = useProductsStore()
        const productData = { name: 'Invalid Product' }
        const error = new Error('Validation failed')
        mockProductsApi.createProduct.mockRejectedValueOnce(error)

        await expect(productsStore.createProduct(productData)).rejects.toThrow('Validation failed')
        expect(productsStore.loading).toBe(false)
      })
    })

    describe('updateProduct', () => {
      it('should update product successfully', async () => {
        const productsStore = useProductsStore()
        const productId = 1
        const productData = { name: 'Updated Product' }
        const updatedProduct = { ...mockProduct, name: 'Updated Product' }
        
        mockProductsApi.updateProduct.mockResolvedValueOnce({ product: updatedProduct })

        // Initialize with existing products
        productsStore.$patch({ 
          products: [...mockProducts],
          currentProduct: mockProduct
        })

        const result = await productsStore.updateProduct(productId, productData)

        expect(mockProductsApi.updateProduct).toHaveBeenCalledWith(productId, productData)
        expect(productsStore.loading).toBe(false)
        
        // Check that product was updated in the list
        const updatedInList = productsStore.products.find(p => p.id === productId)
        expect(updatedInList).toEqual(updatedProduct)
        
        // Check that current product was updated
        expect(productsStore.currentProduct).toEqual(updatedProduct)
        
        expect(result).toEqual({ product: updatedProduct })
      })

      it('should handle update product error', async () => {
        const productsStore = useProductsStore()
        const productId = 1
        const productData = { name: '' } // Invalid data
        const error = new Error('Validation failed')
        mockProductsApi.updateProduct.mockRejectedValueOnce(error)

        await expect(productsStore.updateProduct(productId, productData)).rejects.toThrow('Validation failed')
        expect(productsStore.loading).toBe(false)
      })

      it('should not update current product if different ID', async () => {
        const productsStore = useProductsStore()
        const productId = 2
        const productData = { name: 'Updated Product' }
        const updatedProduct = { ...mockProducts[1], name: 'Updated Product' }
        
        mockProductsApi.updateProduct.mockResolvedValueOnce({ product: updatedProduct })

        // Initialize with current product ID 1, but updating product ID 2
        productsStore.$patch({ 
          products: [...mockProducts],
          currentProduct: mockProduct // ID 1
        })

        await productsStore.updateProduct(productId, productData)

        // Current product should remain unchanged
        expect(productsStore.currentProduct).toEqual(mockProduct)
      })
    })

    describe('deleteProduct', () => {
      it('should delete product successfully', async () => {
        const productsStore = useProductsStore()
        const productId = 1

        // Initialize with existing products
        productsStore.$patch({ products: [...mockProducts] })

        const result = await productsStore.deleteProduct(productId)

        expect(mockProductsApi.deleteProduct).toHaveBeenCalledWith(productId)
        expect(productsStore.loading).toBe(false)
        
        // Check that product was marked as inactive
        const product = productsStore.products.find(p => p.id === productId)
        expect(product?.is_active).toBe(false)
        
        expect(result).toEqual({ message: 'Product deleted successfully' })
      })

      it('should handle delete product error', async () => {
        const productsStore = useProductsStore()
        const productId = 999
        const error = new Error('Product not found')
        mockProductsApi.deleteProduct.mockRejectedValueOnce(error)

        await expect(productsStore.deleteProduct(productId)).rejects.toThrow('Product not found')
        expect(productsStore.loading).toBe(false)
      })
    })

    describe('loadCategories', () => {
      it('should load categories successfully', async () => {
        const productsStore = useProductsStore()
        const mockCategories = ['Testing', 'Hardware', 'Software']

        const result = await productsStore.loadCategories()

        expect(mockProductsApi.getCategories).toHaveBeenCalled()
        expect(productsStore.categories).toEqual(mockCategories)
        expect(result).toEqual(mockCategories)
      })

      it('should handle load categories error', async () => {
        const productsStore = useProductsStore()
        const error = new Error('Failed to load categories')
        mockProductsApi.getCategories.mockRejectedValueOnce(error)

        // Should not throw, but return empty array
        const result = await productsStore.loadCategories()

        expect(result).toEqual([])
        expect(productsStore.categories).toEqual([])
      })
    })

    describe('clearCurrentProduct', () => {
      it('should clear current product', () => {
        const productsStore = useProductsStore()
        
        // Set current product
        productsStore.$patch({ currentProduct: mockProduct })
        expect(productsStore.currentProduct).toEqual(mockProduct)

        // Clear current product
        productsStore.clearCurrentProduct()
        expect(productsStore.currentProduct).toBeNull()
      })
    })

    describe('getProductById', () => {
      it('should return product by ID', () => {
        const productsStore = useProductsStore()
        
        // Initialize with products
        productsStore.$patch({ products: mockProducts })

        const result = productsStore.getProductById(1)
        expect(result).toEqual(mockProduct)

        const notFound = productsStore.getProductById(999)
        expect(notFound).toBeUndefined()
      })

      it('should return undefined for non-existent product', () => {
        const productsStore = useProductsStore()
        
        // Initialize with empty products
        productsStore.$patch({ products: [] })

        const result = productsStore.getProductById(1)
        expect(result).toBeUndefined()
      })
    })
  })
})