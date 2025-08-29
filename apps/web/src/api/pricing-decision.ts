/**
 * 报价决策支持API客户端
 * 基于批量分析结果提供智能报价建议
 */
import http from './http'

// 报价建议响应接口
export interface PricingRecommendation {
  job_id: string
  generated_at: string
  user_id: number
  market_context: MarketContext
  product_recommendations: ProductRecommendation[]
  pricing_strategies: PricingStrategies
  risk_opportunity_analysis: RiskOpportunityAnalysis
  summary: string
  confidence_score: number
}

// 市场环境分析
export interface MarketContext {
  competition_intensity: {
    level: 'low' | 'medium' | 'high'
    score: number
    competitor_count: number
    analysis: {
      large_enterprises: number
      pricing_aggressive: number
      technology_advanced: number
    }
  }
  market_opportunities: {
    level: 'low' | 'medium' | 'high'
    score: number
    total_opportunities: number
    high_value_opportunities: number
    opportunities: any[]
  }
  price_sensitivity: {
    level: 'low' | 'medium' | 'high'
    score: number
    budget_mentions: number
    cost_concerns: number
    indicators: any[]
  }
  demand_heat: {
    level: 'low' | 'medium' | 'high'
    score: number
    total_demands: number
    product_categories: Record<string, number>
    trending_products: [string, number][]
  }
  market_trend: 'growing' | 'stable' | 'declining'
}

// 产品推荐
export interface ProductRecommendation {
  product: {
    id: number
    name: string
    code: string
    description: string
    category: string
    base_price: number
    specifications: Record<string, any>
    features: string[]
    [key: string]: any
  }
  match_score: number
  match_reasons: string[]
  config_recommendations: Record<string, any>
  recommended_price: {
    base_price: number
    recommended_price: number
    adjustment_factor: number
    price_change_percentage: number
    adjustment_reasons: string[]
  }
  pricing_strategy: {
    recommended_strategies: Array<{
      name: string
      description: string
      risk_level: string
    }>
    primary_strategy: {
      name: string
      description: string
      risk_level: string
    } | null
  }
}

// 定价策略
export interface PricingStrategies {
  overall_strategy: {
    strategy: string
    description: string
    success_probability: number
  }
  bundle_opportunities: Array<{
    category: string
    products: string[]
    estimated_discount: string
    value_proposition: string
  }>
  discount_recommendations: {
    volume_discount: {
      threshold: number
      discount_range: string
    }
    early_bird_discount: {
      duration: string
      discount: string
    }
    conditions: string[]
  }
  timing_considerations: {
    optimal_timing: string
    market_window: string
    seasonal_factors: string
    urgency_indicators: string[]
  }
}

// 风险机会分析
export interface RiskOpportunityAnalysis {
  opportunities: Array<{
    type: string
    description: string
    impact: string
  }>
  risks: Array<{
    type: string
    description: string
    probability: string
    impact: string
  }>
  mitigation_strategies: string[]
}

// 批量任务信息
export interface BatchJob {
  id: number
  job_id: string
  job_name: string
  user_id: number
  status: string
  total_files: number
  processed_files: number
  successful_files: number
  failed_files: number
  progress_percentage: number
  start_time: string | null
  end_time: string | null
  created_at: string
  has_pricing_recommendations?: boolean
}

// 创建报价请求
export interface CreateQuoteRequest {
  product_id: number
  customer_name: string
  customer_email: string
  customer_company?: string
  recommended_price: number
  quantity: number
  discount_percentage?: number
  configuration?: Record<string, any>
  notes?: string
  terms_conditions?: string
}

// 报价决策支持API
export const pricingDecisionApi = {
  /**
   * 基于批量分析结果生成报价建议
   */
  async generateRecommendations(jobId: string): Promise<PricingRecommendation> {
    const response = await http.get(`/pricing-decision/recommendations/${jobId}`)
    return response.data
  },

  /**
   * 获取市场分析报告
   */
  async getMarketAnalysis(jobId: string) {
    const response = await http.get(`/pricing-decision/market-analysis/${jobId}`)
    return response.data
  },

  /**
   * 获取产品推荐
   */
  async getProductRecommendations(jobId: string): Promise<{
    job_id: string
    recommendations: ProductRecommendation[]
    market_context: MarketContext
    total_recommendations: number
  }> {
    const response = await http.get(`/pricing-decision/product-recommendations/${jobId}`)
    return response.data
  },

  /**
   * 获取定价策略建议
   */
  async getPricingStrategies(jobId: string): Promise<{
    job_id: string
    pricing_strategies: PricingStrategies
    market_context: MarketContext
  }> {
    const response = await http.get(`/pricing-decision/pricing-strategies/${jobId}`)
    return response.data
  },

  /**
   * 获取已完成的批量分析任务列表
   */
  async getCompletedJobs(): Promise<{
    jobs: BatchJob[]
    total: number
  }> {
    const response = await http.get('/pricing-decision/batch-jobs')
    return response.data
  },

  /**
   * 基于报价建议创建正式报价
   */
  async createQuoteFromRecommendation(data: CreateQuoteRequest) {
    const response = await http.post('/pricing-decision/create-quote', data)
    return response.data
  },

  /**
   * 导出报价建议报告
   */
  async exportRecommendations(jobId: string) {
    const response = await http.get(`/pricing-decision/export-recommendations/${jobId}`)
    return response.data
  }
}

export default pricingDecisionApi