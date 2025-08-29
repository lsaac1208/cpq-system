import http from './http'
import type { 
  Product, 
  ProductListResponse,
  CreateProductRequest,
  UpdateProductRequest
} from '@/types/product'

export const productsApi = {
  // Get products list with proper response handling
  async getProducts(params?: {
    category?: string
    is_active?: boolean
    configurable?: string
    search?: string
    page?: number
    per_page?: number
  }): Promise<ProductListResponse> {
    try {
      const response = await http.get('/products', { params })
      // Handle axios response wrapper
      return response.data || response
    } catch (error) {
      console.error('API Error - getProducts:', error)
      throw error
    }
  },

  // Get product by ID with proper response handling
  async getProduct(id: number): Promise<{ product: Product }> {
    try {
      const response = await http.get(`/products/${id}`)
      // Handle axios response wrapper
      return response.data || response
    } catch (error) {
      console.error(`API Error - getProduct(${id}):`, error)
      throw error
    }
  },

  // Create product with proper response handling
  async createProduct(data: CreateProductRequest): Promise<{ product: Product; message: string }> {
    try {
      const response = await http.post('/products', data)
      return response.data || response
    } catch (error) {
      console.error('API Error - createProduct:', error)
      throw error
    }
  },

  // Update product with proper response handling
  async updateProduct(id: number, data: UpdateProductRequest): Promise<{ product: Product; message: string }> {
    try {
      const response = await http.put(`/products/${id}`, data)
      return response.data || response
    } catch (error) {
      console.error(`API Error - updateProduct(${id}):`, error)
      throw error
    }
  },

  // Delete product (soft delete) with proper response handling
  async deleteProduct(id: number): Promise<{ message: string }> {
    try {
      const response = await http.delete(`/products/${id}`)
      return response.data || response
    } catch (error) {
      console.error(`API Error - deleteProduct(${id}):`, error)
      throw error
    }
  },

  // Get product categories with proper response handling
  async getCategories(): Promise<{ categories: string[] }> {
    try {
      const response = await http.get('/products/categories')
      return response.data || response
    } catch (error) {
      console.error('API Error - getCategories:', error)
      // Return empty array as fallback
      return { categories: [] }
    }
  },

  // Upload product image
  uploadImage(id: number, formData: FormData): Promise<{
    message: string
    image_url: string
    thumbnail_url: string
    file_info: {
      filename: string
      file_size: number
      original_filename: string
    }
  }> {
    return http.post(`/products/${id}/gallery/upload`, formData).then(res => res.data)
  },

  // Delete product image
  deleteImage(id: number): Promise<{ message: string }> {
    return http.delete(`/products/${id}/delete-image`).then(res => res.data)
  }
}