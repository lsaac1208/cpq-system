/**
 * Quotes API简化测试
 * 测试报价相关API功能
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { quotesApi, multiQuotesApi, unifiedQuotesApi } from '../quotes'

// Mock http module
vi.mock('../http', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn()
  }
}))

// Import the mocked http for assertions
import http from '../http'
const mockedHttp = vi.mocked(http)

describe('Quotes API - Simple Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('quotesApi (单产品报价)', () => {
    it('应该获取报价列表', async () => {
      const mockResponse = {
        data: {
          quotes: [
            { id: 1, title: 'Quote 1', status: 'draft' },
            { id: 2, title: 'Quote 2', status: 'sent' }
          ],
          pagination: { page: 1, per_page: 20, total: 2, pages: 1 }
        }
      }

      mockedHttp.get.mockResolvedValueOnce(mockResponse)

      const result = await quotesApi.getQuotes({ page: 1, per_page: 20 })

      expect(mockedHttp.get).toHaveBeenCalledWith('/quotes', { 
        params: { page: 1, per_page: 20 } 
      })
      expect(result).toEqual(mockResponse.data)
    })

    it('应该获取单个报价', async () => {
      const mockResponse = {
        data: {
          quote: { id: 1, title: 'Test Quote', status: 'draft' }
        }
      }

      mockedHttp.get.mockResolvedValueOnce(mockResponse)

      const result = await quotesApi.getQuote(1)

      expect(mockedHttp.get).toHaveBeenCalledWith('/quotes/1')
      expect(result).toEqual(mockResponse.data)
    })

    it('应该创建新报价', async () => {
      const mockResponse = {
        data: {
          quote: { id: 1, title: 'New Quote', status: 'draft' },
          message: '报价创建成功'
        }
      }

      const createData = {
        title: 'New Quote',
        product_id: 1,
        quantity: 10
      }

      mockedHttp.post.mockResolvedValueOnce(mockResponse)

      const result = await quotesApi.createQuote(createData)

      expect(mockedHttp.post).toHaveBeenCalledWith('/quotes', createData)
      expect(result).toEqual(mockResponse.data)
    })

    it('应该更新报价状态', async () => {
      const mockResponse = {
        data: {
          quote: { id: 1, title: 'Test Quote', status: 'sent' },
          message: '状态更新成功'
        }
      }

      const statusData = { status: 'sent' }

      mockedHttp.patch.mockResolvedValueOnce(mockResponse)

      const result = await quotesApi.updateQuoteStatus(1, statusData)

      expect(mockedHttp.patch).toHaveBeenCalledWith('/quotes/1/status', statusData)
      expect(result).toEqual(mockResponse.data)
    })

    it('应该删除报价', async () => {
      const mockResponse = {
        data: { message: '报价删除成功' }
      }

      mockedHttp.delete.mockResolvedValueOnce(mockResponse)

      const result = await quotesApi.deleteQuote(1)

      expect(mockedHttp.delete).toHaveBeenCalledWith('/quotes/1')
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('multiQuotesApi (多产品报价)', () => {
    it('应该获取多产品报价列表', async () => {
      const mockResponse = {
        data: {
          quotes: [
            { id: 1, title: 'Multi Quote 1', items: [{ product_id: 1, quantity: 5 }] }
          ]
        }
      }

      mockedHttp.get.mockResolvedValueOnce(mockResponse)

      const result = await multiQuotesApi.getMultiQuotes()

      expect(mockedHttp.get).toHaveBeenCalledWith('/multi-quotes', { params: undefined })
      expect(result).toEqual(mockResponse.data)
    })

    it('应该创建多产品报价', async () => {
      const mockResponse = {
        data: {
          quote: { id: 1, title: 'New Multi Quote', items: [] },
          message: '多产品报价创建成功'
        }
      }

      const createData = {
        title: 'New Multi Quote',
        items: [
          { product_id: 1, quantity: 5 },
          { product_id: 2, quantity: 3 }
        ]
      }

      mockedHttp.post.mockResolvedValueOnce(mockResponse)

      const result = await multiQuotesApi.createMultiQuote(createData)

      expect(mockedHttp.post).toHaveBeenCalledWith('/multi-quotes', createData)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('unifiedQuotesApi (统一API)', () => {
    it('应该获取所有报价(单产品和多产品)', async () => {
      const singleQuotesResponse = {
        quotes: [{ id: 1, title: 'Single Quote', created_at: '2024-01-01' }],
        pagination: { total: 1 }
      }

      const multiQuotesResponse = {
        quotes: [{ id: 2, title: 'Multi Quote', created_at: '2024-01-02' }],
        pagination: { total: 1 }
      }

      // Mock both API calls
      vi.spyOn(quotesApi, 'getQuotes').mockResolvedValueOnce(singleQuotesResponse)
      vi.spyOn(multiQuotesApi, 'getMultiQuotes').mockResolvedValueOnce(multiQuotesResponse)

      const result = await unifiedQuotesApi.getAllQuotes()

      expect(result.quotes).toHaveLength(2)
      expect(result.pagination.total).toBe(2)
      // Should be sorted by created_at (newest first)
      expect(result.quotes[0].title).toBe('Multi Quote')
      expect(result.quotes[1].title).toBe('Single Quote')
    })

    it('应该智能创建报价 - 有items使用多产品API', async () => {
      const mockResponse = {
        quote: { id: 1, title: 'Smart Quote', items: [] },
        message: '创建成功'
      }

      const createData = {
        title: 'Smart Quote',
        items: [{ product_id: 1, quantity: 5 }]
      }

      vi.spyOn(multiQuotesApi, 'createMultiQuote').mockResolvedValueOnce(mockResponse)

      const result = await unifiedQuotesApi.createQuote(createData)

      expect(multiQuotesApi.createMultiQuote).toHaveBeenCalledWith(createData)
      expect(result).toEqual(mockResponse)
    })

    it('应该智能创建报价 - 有product_id使用单产品API', async () => {
      const mockResponse = {
        quote: { id: 1, title: 'Single Quote', product_id: 1 },
        message: '创建成功'
      }

      const createData = {
        title: 'Single Quote',
        product_id: 1,
        quantity: 10
      }

      vi.spyOn(quotesApi, 'createQuote').mockResolvedValueOnce(mockResponse)

      const result = await unifiedQuotesApi.createQuote(createData)

      expect(quotesApi.createQuote).toHaveBeenCalledWith(createData)
      expect(result).toEqual(mockResponse)
    })

    it('应该智能获取报价 - 先尝试多产品，失败后使用单产品', async () => {
      const singleQuoteResponse = {
        quote: { id: 1, title: 'Single Quote', product_id: 1 }
      }

      // Mock multi-product API to fail with 404
      vi.spyOn(multiQuotesApi, 'getMultiQuote')
        .mockRejectedValueOnce({ response: { status: 404 } })
      
      // Mock single-product API to succeed
      vi.spyOn(quotesApi, 'getQuote')
        .mockResolvedValueOnce(singleQuoteResponse)

      const result = await unifiedQuotesApi.getQuote(1)

      expect(multiQuotesApi.getMultiQuote).toHaveBeenCalledWith(1)
      expect(quotesApi.getQuote).toHaveBeenCalledWith(1)
      expect(result).toEqual(singleQuoteResponse)
    })
  })

  describe('API方法存在性验证', () => {
    it('quotesApi应该具有所有必需的方法', () => {
      expect(typeof quotesApi.getQuotes).toBe('function')
      expect(typeof quotesApi.getQuote).toBe('function')
      expect(typeof quotesApi.createQuote).toBe('function')
      expect(typeof quotesApi.updateQuote).toBe('function')
      expect(typeof quotesApi.updateQuoteStatus).toBe('function')
      expect(typeof quotesApi.deleteQuote).toBe('function')
    })

    it('multiQuotesApi应该具有所有必需的方法', () => {
      expect(typeof multiQuotesApi.getMultiQuotes).toBe('function')
      expect(typeof multiQuotesApi.getMultiQuote).toBe('function')
      expect(typeof multiQuotesApi.createMultiQuote).toBe('function')
      expect(typeof multiQuotesApi.updateMultiQuote).toBe('function')
      expect(typeof multiQuotesApi.updateMultiQuoteStatus).toBe('function')
      expect(typeof multiQuotesApi.deleteMultiQuote).toBe('function')
    })

    it('unifiedQuotesApi应该具有所有必需的方法', () => {
      expect(typeof unifiedQuotesApi.getAllQuotes).toBe('function')
      expect(typeof unifiedQuotesApi.createQuote).toBe('function')
      expect(typeof unifiedQuotesApi.getQuote).toBe('function')
      expect(typeof unifiedQuotesApi.updateQuote).toBe('function')
      expect(typeof unifiedQuotesApi.updateQuoteStatus).toBe('function')
      expect(typeof unifiedQuotesApi.deleteQuote).toBe('function')
    })

    it('API方法应该返回Promise', () => {
      // Setup mocks
      mockedHttp.get.mockResolvedValue({ data: {} })
      mockedHttp.post.mockResolvedValue({ data: {} })
      mockedHttp.put.mockResolvedValue({ data: {} })
      mockedHttp.patch.mockResolvedValue({ data: {} })
      mockedHttp.delete.mockResolvedValue({ data: {} })

      const getQuotesPromise = quotesApi.getQuotes()
      const createQuotePromise = quotesApi.createQuote({ title: 'test', product_id: 1, quantity: 1 })
      const getMultiQuotesPromise = multiQuotesApi.getMultiQuotes()

      expect(getQuotesPromise).toBeInstanceOf(Promise)
      expect(createQuotePromise).toBeInstanceOf(Promise)
      expect(getMultiQuotesPromise).toBeInstanceOf(Promise)

      return Promise.all([getQuotesPromise, createQuotePromise, getMultiQuotesPromise])
    })
  })

  describe('错误处理', () => {
    it('应该传递网络错误', async () => {
      const networkError = {
        code: 'NETWORK_ERROR',
        message: 'Network Error'
      }

      mockedHttp.get.mockRejectedValueOnce(networkError)

      await expect(quotesApi.getQuotes())
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

      await expect(quotesApi.createQuote({ title: 'test', product_id: 1, quantity: 1 }))
        .rejects.toEqual(httpError)
    })

    it('统一API应该处理部分失败的情况', async () => {
      // Mock single quotes API to fail
      vi.spyOn(quotesApi, 'getQuotes')
        .mockRejectedValueOnce(new Error('Single quotes failed'))
      
      // Mock multi quotes API to succeed
      vi.spyOn(multiQuotesApi, 'getMultiQuotes').mockResolvedValueOnce({
        quotes: [{ id: 1, title: 'Multi Quote', created_at: '2024-01-01' }],
        pagination: { total: 1 }
      })

      const result = await unifiedQuotesApi.getAllQuotes()

      expect(result.quotes).toHaveLength(1)
      expect(result.quotes[0].title).toBe('Multi Quote')
      expect(result.pagination.total).toBe(1)
    })
  })
})