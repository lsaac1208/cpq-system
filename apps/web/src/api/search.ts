/**
 * 产品搜索API客户端
 * 提供完整的搜索功能接口
 */

import http from './http'

// 搜索类型定义
export interface SearchFilters {
  category?: string
  price_min?: number
  price_max?: number
  is_configurable?: boolean
  is_active?: boolean
  specs?: Record<string, any>
}

export interface SearchOptions {
  query?: string
  filters?: SearchFilters
  sort?: 'relevance' | 'name' | 'price' | 'price_desc' | 'newest' | 'oldest'
  page?: number
  per_page?: number
}

export interface SearchResult {
  products: Product[]
  pagination: {
    page: number
    per_page: number
    total: number
    pages: number
  }
  search_info: {
    query: string
    total_results: number
    search_time: string
    filters_applied: SearchFilters
  }
}

export interface Product {
  id: number
  name: string
  code: string
  description?: string
  category: string
  base_price: string
  configuration_schema?: Record<string, any>
  specifications?: Record<string, any>
  is_active: boolean
  is_configurable: boolean
  created_at: string
  updated_at: string
  relevance_score?: number
  match_highlights?: {
    name?: string
    description?: string
    category?: string
  }
}

export interface SearchSuggestion {
  type: 'product' | 'code' | 'category'
  text: string
  highlighted?: string
  category?: string
  product_id?: number
  count?: number
}

export interface BatchSearchItem {
  index: number
  query: string
  success: boolean
  results?: Product[]
  total_found?: number
  error?: string
  timestamp: string
  metadata?: Record<string, any>
}

export interface BatchSearchResult {
  results: BatchSearchItem[]
  summary: {
    total_queries: number
    successful: number
    failed: number
    total_products_found: number
  }
}

export interface HotSearch {
  query: string
  count: number
  trend: 'up' | 'down' | 'stable'
}

export interface SearchStats {
  period_days: number
  total_searches: number
  no_result_searches: number
  no_result_rate: number
  average_results: number
}

/**
 * 搜索API服务类
 */
export class SearchAPI {
  
  /**
   * 搜索产品
   */
  static async searchProducts(options: SearchOptions = {}): Promise<SearchResult> {
    const params = new URLSearchParams()
    
    if (options.query) {
      params.append('query', options.query)
    }
    
    if (options.filters) {
      Object.entries(options.filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, String(value))
        }
      })
    }
    
    if (options.sort && options.sort !== 'relevance') {
      params.append('sort', options.sort)
    }
    
    if (options.page && options.page > 1) {
      params.append('page', String(options.page))
    }
    
    if (options.per_page && options.per_page !== 20) {
      params.append('per_page', String(options.per_page))
    }
    
    const response = await http.get(`/search/products?${params.toString()}`)
    
    // HTTP interceptor returns response.data directly, but backend wraps in {success: true, data: {...}}
    let data = response
    
    // Handle the actual backend response structure
    if (response && response.success && response.data) {
      data = response.data  // Extract the actual search data
    }
    
    // Ensure we have the expected structure
    if (!data || typeof data !== 'object') {
      console.error('Invalid search response structure:', response)
      throw new Error('Invalid response format from search API')
    }
    
    // Return the data with fallback structure
    return {
      products: data.products || [],
      pagination: data.pagination || {
        page: 1,
        per_page: 20,
        total: 0,
        pages: 0
      },
      search_info: data.search_info || {
        query: options.query || '',
        total_results: 0,
        search_time: new Date().toISOString(),
        filters_applied: options.filters || {}
      }
    }
  }
  
  /**
   * 获取搜索建议
   */
  static async getSearchSuggestions(query: string, limit: number = 10): Promise<SearchSuggestion[]> {
    if (!query || query.length < 2) {
      return []
    }
    
    const response = await http.get('/search/products/suggestions', {
      params: { query, limit }
    })
    
    return response.suggestions || []
  }
  
  /**
   * 获取热门搜索
   */
  static async getHotSearches(limit: number = 10, days: number = 7): Promise<HotSearch[]> {
    const response = await http.get('/search/products/hot', {
      params: { limit, days }
    })
    
    return response.hot_searches || []
  }
  
  /**
   * 批量搜索产品
   */
  static async batchSearchProducts(
    queries: string[], 
    options: { per_query?: number; filters?: SearchFilters } = {}
  ): Promise<BatchSearchResult> {
    const response = await http.post('/search/products/batch', {
      queries,
      options
    })
    
    return response
  }
  
  /**
   * 文件批量搜索
   */
  static async batchSearchFromFile(
    file: File,
    options: {
      query_column?: string
      per_query?: number
    } = {}
  ): Promise<BatchSearchResult> {
    const formData = new FormData()
    formData.append('file', file)
    
    if (options.query_column) {
      formData.append('query_column', options.query_column)
    }
    
    if (options.per_query) {
      formData.append('per_query', String(options.per_query))
    }
    
    const response = await http.post('/search/products/batch/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    return response
  }
  
  /**
   * 导出批量搜索结果
   */
  static async exportBatchResults(results: BatchSearchItem[]): Promise<Blob> {
    const response = await http.post('/search/products/batch/export', {
      results
    }, {
      responseType: 'blob'
    })
    
    return response
  }
  
  /**
   * 获取搜索统计
   */
  static async getSearchStats(days: number = 30): Promise<SearchStats> {
    const response = await http.get('/search/stats', {
      params: { days }
    })
    
    return response.stats
  }
}

// 默认导出
export default SearchAPI