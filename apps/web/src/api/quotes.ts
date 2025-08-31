import http from './http'
import type { 
  Quote, 
  QuoteListResponse,
  CreateQuoteRequest,
  UpdateQuoteRequest,
  UpdateQuoteStatusRequest,
  QuoteSearchParams
} from '@/types/quote'

// Single-product quotes API (legacy)
export const quotesApi = {
  // Get quotes list
  getQuotes(params?: QuoteSearchParams): Promise<QuoteListResponse> {
    return http.get('/quotes', { params })
  },

  // Get quote by ID
  getQuote(id: number): Promise<{ quote: Quote }> {
    return http.get(`/quotes/${id}`).then(response => response.data)
  },

  // Create quote
  createQuote(data: CreateQuoteRequest): Promise<{ quote: Quote; message: string }> {
    return http.post('/quotes', data)
  },

  // Update quote
  updateQuote(id: number, data: UpdateQuoteRequest): Promise<{ quote: Quote; message: string }> {
    return http.put(`/quotes/${id}`, data)
  },

  // Update quote status
  updateQuoteStatus(id: number, data: UpdateQuoteStatusRequest): Promise<{ quote: Quote; message: string }> {
    return http.patch(`/quotes/${id}/status`, data)
  },

  // Delete quote
  deleteQuote(id: number): Promise<{ message: string }> {
    return http.delete(`/quotes/${id}`)
  }
}

// Multi-product quotes API (new)
export const multiQuotesApi = {
  // Get multi-product quotes list
  getMultiQuotes(params?: QuoteSearchParams): Promise<QuoteListResponse> {
    return http.get('/multi-quotes', { params })
  },

  // Get multi-product quote by ID
  getMultiQuote(id: number): Promise<{ quote: Quote }> {
    return http.get(`/multi-quotes/${id}`).then(response => response.data)
  },

  // Create multi-product quote
  createMultiQuote(data: CreateQuoteRequest): Promise<{ quote: Quote; message: string }> {
    return http.post('/multi-quotes', data)
  },

  // Update multi-product quote
  updateMultiQuote(id: number, data: UpdateQuoteRequest): Promise<{ quote: Quote; message: string }> {
    return http.put(`/multi-quotes/${id}`, data)
  },

  // Update multi-product quote status
  updateMultiQuoteStatus(id: number, data: UpdateQuoteStatusRequest): Promise<{ quote: Quote; message: string }> {
    return http.put(`/multi-quotes/${id}/status`, data)
  },

  // Delete multi-product quote
  deleteMultiQuote(id: number): Promise<{ message: string }> {
    return http.delete(`/multi-quotes/${id}`)
  }
}

// Unified quotes API that combines both single and multi-product quotes
export const unifiedQuotesApi = {
  // Get all quotes (both single and multi-product)
  async getAllQuotes(params?: QuoteSearchParams): Promise<QuoteListResponse> {
    console.log('🚀 統一API開始執行 getAllQuotes，參數:', params)
    
    const singleQuotes: Quote[] = []
    const multiQuotes: Quote[] = []
    let totalSingle = 0
    let totalMulti = 0

    try {
      // Fetch both single-product and multi-product quotes in parallel
      console.log('📞 开始调用API...')
    const [singleResponse, multiResponse] = await Promise.allSettled([
      quotesApi.getQuotes(params).then(result => {
        console.log('✅ Single quotes API success:', result)
        return result
      }).catch(error => {
        console.error('❌ Single quotes API failed:', error)
        return null
      }),
      multiQuotesApi.getMultiQuotes(params).then(result => {
        console.log('✅ Multi quotes API success:', result)
        return result
      }).catch(error => {
        console.error('❌ Multi quotes API failed:', error)
        return null
      })
    ])
    
    console.log('📊 Promise.allSettled results:')
    console.log('- singleResponse:', singleResponse)
    console.log('- multiResponse:', multiResponse)

    // Process single quotes response and normalize data structure
    console.log('📋 处理单产品报价响应...')
    if (singleResponse.status === 'fulfilled') {
      console.log('✅ 单产品报价Promise fulfilled:', singleResponse.value)
      if (singleResponse.value && singleResponse.value.data && singleResponse.value.data.quotes && Array.isArray(singleResponse.value.data.quotes)) {
        const response = singleResponse.value.data
        console.log(`📊 单产品报价数据: ${response.quotes.length}条`)
        
        // Normalize single quotes to match unified structure
        const normalizedSingleQuotes = response.quotes.map((quote: any) => ({
          ...quote,
          // Add missing subtotal field for single quotes (use total_price as subtotal)
          subtotal: quote.total_price || quote.final_price || 0,
          // Ensure we have all required fields
          items: quote.product_id ? [{
            product_id: quote.product_id,
            product: quote.product,
            quantity: quote.quantity || 1,
            unit_price: quote.unit_price || 0,
            line_total: quote.total_price || quote.final_price || 0,
            configuration: quote.configuration
          }] : [],
          version: 1 // Default version for single quotes
        }))
        
        singleQuotes.push(...normalizedSingleQuotes)
        totalSingle = response.pagination?.total || response.quotes.length
        console.log(`✅ 成功添加${singleQuotes.length}条单产品报价`)
      } else {
        console.warn('⚠️ 单产品报价响应格式异常:', singleResponse.value)
      }
    } else {
      console.error('❌ 单产品报价Promise rejected:', singleResponse)
    }

    // Process multi quotes response
    if (multiResponse.status === 'fulfilled' && multiResponse.value) {
      const response = multiResponse.value.data || multiResponse.value
      if (response.quotes && Array.isArray(response.quotes)) {
        multiQuotes.push(...response.quotes)
        // Handle consistent pagination structure
        totalMulti = response.pagination?.total || response.quotes.length
      } else if (Array.isArray(response)) {
        // Handle direct array response
        multiQuotes.push(...response)
        totalMulti = response.length
      }
    }

    // Debug logging
    console.log('🔍 Debug API Response Processing:')
    console.log('- Single quotes count:', singleQuotes.length)
    console.log('- Multi quotes count:', multiQuotes.length)
    console.log('- Total single:', totalSingle)
    console.log('- Total multi:', totalMulti)
    console.log('- Sample single quote:', singleQuotes[0])
    console.log('- Sample multi quote:', multiQuotes[0])

    // Combine quotes from both APIs
    const allQuotes = [...singleQuotes, ...multiQuotes]
    const totalQuotes = totalSingle + totalMulti

    console.log('- Combined quotes count:', allQuotes.length)
    console.log('- Total calculated:', totalQuotes)

    // Sort by creation date (newest first) to maintain consistency
    allQuotes.sort((a, b) => {
      const dateA = new Date(a.created_at || 0).getTime()
      const dateB = new Date(b.created_at || 0).getTime()
      return dateB - dateA
    })

    // Apply pagination to combined results
    const page = params?.page || 1
    const perPage = params?.per_page || 20
    const startIndex = (page - 1) * perPage
    const endIndex = startIndex + perPage
    const paginatedQuotes = allQuotes.slice(startIndex, endIndex)

    // Final result to return
    const result = {
      quotes: paginatedQuotes,
      pagination: {
        page: page,
        per_page: perPage,
        total: totalQuotes,
        pages: Math.ceil(totalQuotes / perPage)
      }
    } as QuoteListResponse

    console.log('🎉 統一API最終返回結果:', result)
    console.log('🎉 最終報價數量:', result.quotes.length)
    console.log('🎉 分頁信息:', result.pagination)

    return result
    
  } catch (error) {
      console.error('❌ 統一API執行失敗:', error)
      // 返回空結果而不是拋出錯誤
      return {
        quotes: [],
        pagination: {
          page: params?.page || 1,
          per_page: params?.per_page || 20,
          total: 0,
          pages: 0
        }
      } as QuoteListResponse
    }
  },

  // Create a quote (automatically use multi-product API for items array)
  async createQuote(data: CreateQuoteRequest): Promise<{ quote: Quote; message: string }> {
    // If the request has items, use multi-product API
    if (data.items && data.items.length > 0) {
      return multiQuotesApi.createMultiQuote(data)
    }
    // Otherwise, use single-product API for backward compatibility
    else if (data.product_id) {
      return quotesApi.createQuote(data)
    }
    else {
      throw new Error('Quote must have either items array or product_id')
    }
  },

  // Get quote by ID (try multi-product first, fallback to single-product)
  async getQuote(id: number): Promise<{ quote: Quote }> {
    try {
      return await multiQuotesApi.getMultiQuote(id)
    } catch (error: any) {
      // If multi-product quote not found, try single-product
      if (error.response?.status === 404) {
        return quotesApi.getQuote(id)
      }
      throw error
    }
  },

  // Update quote (determine type based on existing quote data)
  async updateQuote(id: number, data: UpdateQuoteRequest): Promise<{ quote: Quote; message: string }> {
    try {
      // Try multi-product update first
      return await multiQuotesApi.updateMultiQuote(id, data)
    } catch (error: any) {
      // If multi-product quote not found, try single-product
      if (error.response?.status === 404) {
        return quotesApi.updateQuote(id, data)
      }
      throw error
    }
  },

  // Update quote status
  async updateQuoteStatus(id: number, data: UpdateQuoteStatusRequest): Promise<{ quote: Quote; message: string }> {
    try {
      return await multiQuotesApi.updateMultiQuoteStatus(id, data)
    } catch (error: any) {
      if (error.response?.status === 404) {
        return quotesApi.updateQuoteStatus(id, data)
      }
      throw error
    }
  },

  // Delete quote
  async deleteQuote(id: number): Promise<{ message: string }> {
    try {
      return await multiQuotesApi.deleteMultiQuote(id)
    } catch (error: any) {
      if (error.response?.status === 404) {
        return quotesApi.deleteQuote(id)
      }
      throw error
    }
  }
}