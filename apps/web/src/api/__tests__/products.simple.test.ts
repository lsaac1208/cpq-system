/**
 * Products API简化测试
 * 测试产品相关API功能
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { productsApi } from '../products'

// Mock http module
vi.mock('../http', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

// Import the mocked http for assertions
import http from '../http'
const mockedHttp = vi.mocked(http)

describe('Products API - Simple Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('productsApi.getProducts', () => {
    it('应该获取产品列表', async () => {
      const mockResponse = {
        products: [
          { id: 1, name: 'Product 1', category: 'Electronics', is_active: true },
          { id: 2, name: 'Product 2', category: 'Tools', is_active: true }
        ],
        pagination: { page: 1, per_page: 20, total: 2, pages: 1 }
      }

      mockedHttp.get.mockResolvedValueOnce(mockResponse)

      const result = await productsApi.getProducts({ page: 1, per_page: 20 })

      expect(mockedHttp.get).toHaveBeenCalledWith('/products', { 
        params: { page: 1, per_page: 20 } 
      })
      expect(result).toEqual(mockResponse)
    })

    it('应该支持分类过滤', async () => {
      const mockResponse = {
        products: [
          { id: 1, name: 'Electronics Product', category: 'Electronics', is_active: true }
        ]
      }

      mockedHttp.get.mockResolvedValueOnce(mockResponse)

      const result = await productsApi.getProducts({ 
        category: 'Electronics', 
        is_active: true 
      })

      expect(mockedHttp.get).toHaveBeenCalledWith('/products', { 
        params: { category: 'Electronics', is_active: true } 
      })
      expect(result).toEqual(mockResponse)
    })

    it('应该处理空参数', async () => {
      const mockResponse = { products: [] }

      mockedHttp.get.mockResolvedValueOnce(mockResponse)

      const result = await productsApi.getProducts()

      expect(mockedHttp.get).toHaveBeenCalledWith('/products', { params: undefined })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('productsApi.getProduct', () => {
    it('应该获取单个产品详情', async () => {
      const mockResponse = {
        product: { 
          id: 1, 
          name: 'Test Product', 
          category: 'Electronics',
          price: 999.99,
          description: 'Test description'
        }
      }

      mockedHttp.get.mockResolvedValueOnce(mockResponse)

      const result = await productsApi.getProduct(1)

      expect(mockedHttp.get).toHaveBeenCalledWith('/products/1')
      expect(result).toEqual(mockResponse)
    })

    it('应该处理产品不存在的错误', async () => {
      const notFoundError = {
        response: {
          status: 404,
          data: { error: 'Product not found' }
        }
      }

      mockedHttp.get.mockRejectedValueOnce(notFoundError)

      await expect(productsApi.getProduct(999))
        .rejects.toEqual(notFoundError)
    })
  })

  describe('productsApi.createProduct', () => {
    it('应该创建新产品', async () => {
      const mockResponse = {
        product: { 
          id: 1, 
          name: 'New Product', 
          category: 'Electronics',
          price: 199.99
        },
        message: '产品创建成功'
      }

      const createData = {
        name: 'New Product',
        category: 'Electronics',
        price: 199.99,
        description: 'New product description'
      }

      mockedHttp.post.mockResolvedValueOnce(mockResponse)

      const result = await productsApi.createProduct(createData)

      expect(mockedHttp.post).toHaveBeenCalledWith('/products', createData)
      expect(result).toEqual(mockResponse)
    })

    it('应该处理创建验证错误', async () => {
      const validationError = {
        response: {
          status: 422,
          data: { 
            errors: {
              name: ['产品名称不能为空'],
              price: ['价格必须大于0']
            }
          }
        }
      }

      const invalidData = {
        name: '',
        category: 'Electronics',
        price: -1
      }

      mockedHttp.post.mockRejectedValueOnce(validationError)

      await expect(productsApi.createProduct(invalidData))
        .rejects.toEqual(validationError)
    })
  })

  describe('productsApi.updateProduct', () => {
    it('应该更新产品信息', async () => {
      const mockResponse = {
        product: { 
          id: 1, 
          name: 'Updated Product', 
          category: 'Electronics',
          price: 299.99
        },
        message: '产品更新成功'
      }

      const updateData = {
        name: 'Updated Product',
        price: 299.99
      }

      mockedHttp.put.mockResolvedValueOnce(mockResponse)

      const result = await productsApi.updateProduct(1, updateData)

      expect(mockedHttp.put).toHaveBeenCalledWith('/products/1', updateData)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('productsApi.deleteProduct', () => {
    it('应该删除产品(软删除)', async () => {
      const mockResponse = {
        message: '产品删除成功'
      }

      mockedHttp.delete.mockResolvedValueOnce(mockResponse)

      const result = await productsApi.deleteProduct(1)

      expect(mockedHttp.delete).toHaveBeenCalledWith('/products/1')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('productsApi.getCategories', () => {
    it('应该获取产品分类列表', async () => {
      const mockResponse = {
        categories: ['Electronics', 'Tools', 'Accessories', 'Software']
      }

      mockedHttp.get.mockResolvedValueOnce(mockResponse)

      const result = await productsApi.getCategories()

      expect(mockedHttp.get).toHaveBeenCalledWith('/products/categories')
      expect(result).toEqual(mockResponse)
    })

    it('应该处理空分类列表', async () => {
      const mockResponse = {
        categories: []
      }

      mockedHttp.get.mockResolvedValueOnce(mockResponse)

      const result = await productsApi.getCategories()

      expect(result.categories).toEqual([])
    })
  })

  describe('productsApi图片管理', () => {
    it('应该上传产品图片', async () => {
      const mockResponse = {
        data: {
          message: '图片上传成功',
          image_url: '/uploads/products/1/image.jpg',
          thumbnail_url: '/uploads/products/1/thumb_image.jpg',
          file_info: {
            filename: 'image_123.jpg',
            file_size: 102400,
            original_filename: 'product_image.jpg'
          }
        }
      }

      const formData = new FormData()
      formData.append('image', new File(['test'], 'test.jpg', { type: 'image/jpeg' }))

      mockedHttp.post.mockResolvedValueOnce(mockResponse)

      const result = await productsApi.uploadImage(1, formData)

      expect(mockedHttp.post).toHaveBeenCalledWith('/products/1/gallery/upload', formData)
      expect(result).toEqual(mockResponse.data)
    })

    it('应该删除产品图片', async () => {
      const mockResponse = {
        data: {
          message: '图片删除成功'
        }
      }

      mockedHttp.delete.mockResolvedValueOnce(mockResponse)

      const result = await productsApi.deleteImage(1)

      expect(mockedHttp.delete).toHaveBeenCalledWith('/products/1/delete-image')
      expect(result).toEqual(mockResponse.data)
    })

    it('应该处理图片上传失败', async () => {
      const uploadError = {
        response: {
          status: 413,
          data: { error: '文件太大，最大支持5MB' }
        }
      }

      const formData = new FormData()
      formData.append('image', new File(['large file'], 'large.jpg'))

      mockedHttp.post.mockRejectedValueOnce(uploadError)

      await expect(productsApi.uploadImage(1, formData))
        .rejects.toEqual(uploadError)
    })
  })

  describe('API方法存在性验证', () => {
    it('应该具有所有必需的API方法', () => {
      expect(typeof productsApi.getProducts).toBe('function')
      expect(typeof productsApi.getProduct).toBe('function')
      expect(typeof productsApi.createProduct).toBe('function')
      expect(typeof productsApi.updateProduct).toBe('function')
      expect(typeof productsApi.deleteProduct).toBe('function')
      expect(typeof productsApi.getCategories).toBe('function')
      expect(typeof productsApi.uploadImage).toBe('function')
      expect(typeof productsApi.deleteImage).toBe('function')
    })

    it('API方法应该返回Promise', () => {
      // Setup mocks
      mockedHttp.get.mockResolvedValue({})
      mockedHttp.post.mockResolvedValue({})
      mockedHttp.put.mockResolvedValue({})
      mockedHttp.delete.mockResolvedValue({})

      const getProductsPromise = productsApi.getProducts()
      const getProductPromise = productsApi.getProduct(1)
      const createProductPromise = productsApi.createProduct({ 
        name: 'test', 
        category: 'test', 
        price: 100 
      })
      const getCategoriesPromise = productsApi.getCategories()

      expect(getProductsPromise).toBeInstanceOf(Promise)
      expect(getProductPromise).toBeInstanceOf(Promise)
      expect(createProductPromise).toBeInstanceOf(Promise)
      expect(getCategoriesPromise).toBeInstanceOf(Promise)

      // Ensure all promises can resolve
      return Promise.all([
        getProductsPromise, 
        getProductPromise, 
        createProductPromise, 
        getCategoriesPromise
      ])
    })
  })

  describe('错误处理', () => {
    it('应该传递网络错误', async () => {
      const networkError = {
        code: 'NETWORK_ERROR',
        message: 'Network Error'
      }

      mockedHttp.get.mockRejectedValueOnce(networkError)

      await expect(productsApi.getProducts())
        .rejects.toEqual(networkError)
    })

    it('应该传递HTTP错误', async () => {
      const httpError = {
        response: {
          status: 500,
          data: { error: 'Internal Server Error' }
        }
      }

      mockedHttp.post.mockRejectedValueOnce(httpError)

      await expect(productsApi.createProduct({ 
        name: 'test', 
        category: 'test', 
        price: 100 
      })).rejects.toEqual(httpError)
    })

    it('应该传递权限错误', async () => {
      const authError = {
        response: {
          status: 403,
          data: { error: 'Forbidden' }
        }
      }

      mockedHttp.delete.mockRejectedValueOnce(authError)

      await expect(productsApi.deleteProduct(1))
        .rejects.toEqual(authError)
    })
  })
})