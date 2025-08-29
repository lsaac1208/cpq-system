import { defineStore } from 'pinia'
import { ref, readonly } from 'vue'
import { productsApi } from '@/api/products'
import type { Product } from '@/types/product'

export const useProductsStore = defineStore('products', () => {
  // State
  const products = ref<Product[]>([])
  const currentProduct = ref<Product | null>(null)
  const categories = ref<string[]>([])
  const loading = ref(false)
  const total = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(20)

  // Actions
  const loadProducts = async (params?: {
    category?: string
    is_active?: boolean
    configurable?: string
    search?: string
    page?: number
    per_page?: number
  }) => {
    loading.value = true
    try {
      console.log('🔄 Loading products with params:', params)
      const response = await productsApi.getProducts(params)
      console.log('📦 Products response:', response)
      
      // Handle response data structure
      if (response && typeof response === 'object') {
        products.value = response.products || []
        total.value = response.pagination?.total || 0
        currentPage.value = response.pagination?.page || 1
        pageSize.value = response.pagination?.per_page || 20
        
        console.log(`✅ Loaded ${products.value.length} products, total: ${total.value}`)
        return response
      } else {
        console.warn('⚠️ Invalid products response format:', response)
        products.value = []
        total.value = 0
        return { products: [], pagination: { total: 0, page: 1, per_page: 20 } }
      }
    } catch (error) {
      console.error('❌ Error loading products:', error)
      products.value = []
      total.value = 0
      throw error
    } finally {
      loading.value = false
    }
  }

  const loadProduct = async (id: number) => {
    loading.value = true
    try {
      console.log(`🔄 Loading product ${id}`)
      const response = await productsApi.getProduct(id)
      console.log('📦 Product response:', response)
      
      if (response && response.product) {
        currentProduct.value = response.product
        console.log(`✅ Loaded product: ${response.product.name}`)
        return response.product
      } else {
        console.warn('⚠️ Invalid product response format:', response)
        currentProduct.value = null
        throw new Error('Invalid product data received')
      }
    } catch (error) {
      console.error(`❌ Error loading product ${id}:`, error)
      currentProduct.value = null
      throw error
    } finally {
      loading.value = false
    }
  }

  const createProduct = async (productData: any) => {
    loading.value = true
    try {
      console.log('🔄 Creating product:', productData?.name || 'Unknown')
      const response = await productsApi.createProduct(productData)
      console.log('📦 Create product response:', response)
      
      if (response && response.product) {
        // Add to products list at the beginning
        products.value.unshift(response.product)
        total.value = total.value + 1
        
        console.log(`✅ Product created: ${response.product.name}`)
        return response
      } else {
        console.warn('⚠️ Invalid create product response:', response)
        throw new Error('Invalid product creation response')
      }
    } catch (error) {
      console.error('❌ Error creating product:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const updateProduct = async (id: number, productData: any) => {
    loading.value = true
    try {
      const response = await productsApi.updateProduct(id, productData)
      // Update in products list
      const index = products.value.findIndex(p => p.id === id)
      if (index !== -1) {
        products.value[index] = response.product
      }
      // Update current product if it's the same
      if (currentProduct.value?.id === id) {
        currentProduct.value = response.product
      }
      return response
    } finally {
      loading.value = false
    }
  }

  const deleteProduct = async (id: number) => {
    loading.value = true
    try {
      const response = await productsApi.deleteProduct(id)
      // Remove from products list or mark as inactive
      const index = products.value.findIndex(p => p.id === id)
      if (index !== -1) {
        products.value[index].is_active = false
      }
      return response
    } finally {
      loading.value = false
    }
  }

  const loadCategories = async () => {
    try {
      const response = await productsApi.getCategories()
      categories.value = response?.categories || []
      return response?.categories || []
    } catch (error) {
      console.error('Failed to load categories:', error)
      categories.value = []
      return []
    }
  }

  const loadAllProductsForCatalog = async () => {
    loading.value = true
    try {
      // Load all products for catalog generation
      const response = await productsApi.getProducts({ 
        is_active: true, 
        per_page: 1000 // Large number to get all products
      })
      return response.products
    } finally {
      loading.value = false
    }
  }

  const clearCurrentProduct = () => {
    currentProduct.value = null
  }

  const getProductById = (id: number): Product | undefined => {
    return products.value.find(p => p.id === id)
  }

  // Force refresh products list (useful after create/update operations)
  const refreshProducts = async (customParams?: {
    category?: string
    is_active?: boolean
    configurable?: string
    search?: string
    page?: number
    per_page?: number
  }) => {
    console.log('🔄 Force refreshing products list')
    const currentParams = customParams || {
      category: '',
      is_active: true,
      page: currentPage.value,
      per_page: pageSize.value
    }
    return await loadProducts(currentParams)
  }

  // Reset all state to initial values
  const resetStore = () => {
    console.log('🔄 Resetting products store')
    products.value = []
    currentProduct.value = null
    categories.value = []
    total.value = 0
    currentPage.value = 1
    pageSize.value = 20
    loading.value = false
  }

  return {
    // State
    products: readonly(products),
    currentProduct: readonly(currentProduct),
    categories: readonly(categories),
    loading: readonly(loading),
    total: readonly(total),
    currentPage: readonly(currentPage),
    pageSize: readonly(pageSize),
    
    // Actions
    loadProducts,
    loadProduct,
    createProduct,
    updateProduct,
    deleteProduct,
    loadCategories,
    loadAllProductsForCatalog,
    clearCurrentProduct,
    getProductById,
    refreshProducts,
    resetStore
  }
})