// 历史数据优化Prompt系统类型定义

export interface PromptOptimizationRequest {
  current_prompt: string
  historical_data: {
    success_cases: Array<{
      prompt: string
      result_quality: number
      user_feedback: string
      metadata?: Record<string, any>
    }>
    failure_cases: Array<{
      prompt: string
      issues: string[]
      user_feedback: string
      metadata?: Record<string, any>
    }>
  }
  optimization_goals: string[]
  target_domain?: string
  priority_weights?: {
    accuracy: number
    clarity: number
    efficiency: number
    user_satisfaction: number
  }
}

export interface PromptOptimizationResponse {
  success: boolean
  optimization_id: number
  suggestions: Array<{
    id: string
    type: 'structure' | 'content' | 'parameters' | 'context'
    title: string
    description: string
    before: string
    after: string
    confidence_score: number
    impact_level: 'low' | 'medium' | 'high'
    reasoning: string
  }>
  optimized_prompt: string
  improvement_score: number
  risk_assessment: {
    overall_risk: 'low' | 'medium' | 'high'
    risk_factors: string[]
    mitigation_suggestions: string[]
  }
  metadata: {
    analysis_duration: number
    total_suggestions: number
    high_impact_suggestions: number
  }
  error?: string
}

export interface PromptTemplate {
  id: number
  name: string
  description: string
  template_content: string
  category: string
  tags: string[]
  usage_count: number
  success_rate: number
  average_rating: number
  created_by: number
  is_public: boolean
  created_at: string
  updated_at: string
  version: string
  example_usage?: string
  parameters?: Array<{
    name: string
    type: string
    description: string
    required: boolean
    default_value?: any
  }>
}

export interface PromptTemplateResponse {
  success: boolean
  templates: PromptTemplate[]
  pagination: {
    page: number
    per_page: number
    total: number
    pages: number
  }
  categories: string[]
  popular_tags: string[]
}

export interface SavePromptTemplateRequest {
  name: string
  description: string
  template_content: string
  category: string
  tags: string[]
  is_public: boolean
  example_usage?: string
  parameters?: Array<{
    name: string
    type: string
    description: string
    required: boolean
    default_value?: any
  }>
}

export interface SavePromptTemplateResponse {
  success: boolean
  message: string
  template: PromptTemplate
  error?: string
}

export interface OptimizationRecord {
  id: number
  original_prompt: string
  optimized_prompt: string
  suggestions_applied: string[]
  improvement_score: number
  user_rating?: number
  user_feedback?: string
  usage_success: boolean
  metadata: Record<string, any>
  created_at: string
  updated_at: string
}

export interface PromptHistoryResponse {
  success: boolean
  records: OptimizationRecord[]
  pagination: {
    page: number
    per_page: number
    total: number
    pages: number
  }
  statistics: {
    total_optimizations: number
    average_improvement: number
    success_rate: number
  }
}

export interface OptimizationMetrics {
  period_days: number
  total_optimizations: number
  average_improvement_score: number
  user_satisfaction_rate: number
  most_common_improvements: Array<{
    type: string
    count: number
    average_impact: number
  }>
  trend_data: Array<{
    date: string
    optimizations_count: number
    average_score: number
    success_rate: number
  }>
}

export interface OptimizationMetricsResponse {
  success: boolean
  metrics: OptimizationMetrics
  insights: string[]
  recommendations: string[]
}

// 组件事件类型
export interface PromptOptimizationEvents {
  'optimization-start': () => void
  'optimization-success': (result: PromptOptimizationResponse) => void
  'optimization-error': (error: string) => void
  'template-saved': (template: PromptTemplate) => void
  'suggestions-applied': (optimizedPrompt: string) => void
}