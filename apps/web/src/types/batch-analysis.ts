// 批量分析类型定义

export interface BatchAnalysisConfig {
  analysis_type: 'customer_requirements' | 'competitor_analysis' | 'project_mining' | 'product_extraction' | 'document_classification' | 'quality_assessment' | 'comprehensive'
  extraction_schema?: Record<string, any>
  quality_criteria?: string[]
  processing_priority: 'speed' | 'accuracy' | 'balanced'
  auto_retry_failed: boolean
  max_retries: number
  business_context?: {
    industry?: string
    project_type?: string
    analysis_focus?: string[]
    requirements_type?: 'technical' | 'functional' | 'business' | 'mixed'
    competitor_category?: string
    project_phase?: 'planning' | 'execution' | 'completion' | 'evaluation'
  }
  notification_settings: {
    email_on_completion: boolean
    email_on_failure: boolean
    webhook_url?: string
  }
}

export interface BatchAnalysisRequest {
  documents: File[]
  batch_name?: string
  description?: string
  analysis_config: BatchAnalysisConfig
}

export interface BatchAnalysisResponse {
  success: boolean
  job_id: number
  estimated_completion_time: number
  estimated_cost?: number
  queue_position: number
  message: string
  error?: string
}

export interface BatchJobProgress {
  total_files: number
  processed_files: number
  successful_files: number
  failed_files: number
  current_file?: string
  percentage: number
  estimated_remaining_time: number
}

export interface BatchJobResult {
  file_name: string
  file_size: number
  status: 'success' | 'failed' | 'skipped'
  analysis_result?: any
  business_insights?: BusinessAnalysisResult
  error_message?: string
  processing_time: number
  confidence_score?: number
}

// 业务分析结果类型
export interface BusinessAnalysisResult {
  customer_requirements?: CustomerRequirementsAnalysis
  competitor_analysis?: CompetitorAnalysis
  project_insights?: ProjectInsights
}

// 客户需求分析结果
export interface CustomerRequirementsAnalysis {
  technical_requirements: {
    performance_specs?: Record<string, string>
    functional_requirements?: string[]
    technical_constraints?: string[]
    compliance_standards?: string[]
  }
  business_requirements: {
    budget_range?: string
    timeline?: string
    delivery_terms?: string
    support_needs?: string[]
  }
  decision_factors: {
    key_criteria?: string[]
    priority_ranking?: Array<{factor: string, weight: number}>
    deal_breakers?: string[]
  }
  contact_info?: {
    decision_makers?: string[]
    technical_contacts?: string[]
    procurement_contacts?: string[]
  }
  risk_assessment: {
    technical_risks?: string[]
    commercial_risks?: string[]
    timeline_risks?: string[]
    overall_risk_level: 'low' | 'medium' | 'high'
  }
}

// 竞品分析结果
export interface CompetitorAnalysis {
  competitor_info: {
    company_name?: string
    product_name?: string
    market_position?: string
    key_strengths?: string[]
    weaknesses?: string[]
  }
  pricing_analysis: {
    base_price?: number
    pricing_model?: string
    discount_structure?: string
    total_cost_of_ownership?: number
  }
  technical_comparison: {
    specifications?: Record<string, any>
    performance_benchmarks?: Record<string, number>
    feature_matrix?: Record<string, boolean | string>
    technology_stack?: string[]
  }
  market_intelligence: {
    market_share?: number
    customer_feedback?: string[]
    recent_updates?: string[]
    strategic_direction?: string
  }
  competitive_positioning: {
    differentiators?: string[]
    advantages?: string[]
    threats?: string[]
    opportunities?: string[]
  }
}

// 历史项目洞察
export interface ProjectInsights {
  project_metadata: {
    project_type?: string
    industry_sector?: string
    project_scale?: string
    duration?: string
    outcome?: 'successful' | 'partially_successful' | 'failed' | 'cancelled'
  }
  success_patterns: {
    key_success_factors?: string[]
    best_practices?: string[]
    critical_milestones?: string[]
    resource_allocation?: Record<string, number>
  }
  lessons_learned: {
    what_worked_well?: string[]
    challenges_faced?: string[]
    solutions_applied?: string[]
    recommendations?: string[]
  }
  reusable_assets: {
    templates?: string[]
    configurations?: Record<string, any>
    process_workflows?: string[]
    technical_solutions?: string[]
  }
  risk_indicators: {
    early_warning_signs?: string[]
    mitigation_strategies?: string[]
    contingency_plans?: string[]
  }
}

export interface BatchJobStatus {
  success: boolean
  job_id: number
  job_name?: string
  description?: string
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
  analysis_type: string
  processing_priority: string
  progress?: BatchJobProgress
  results?: BatchJobResult[]
  created_at: string
  started_at?: string
  completed_at?: string
  total_processing_time?: number
  error_message?: string
  error_details?: string
  error_timestamp?: string
  auto_retry_failed?: boolean
  max_retries?: number
  queue_position?: number
  notification_settings?: {
    email_on_completion: boolean
    email_on_failure: boolean
    webhook_url?: string
  }
  summary?: {
    success_rate: number
    average_confidence: number
    total_cost?: number
    quality_score: number
  }
  error?: string
}

export interface BatchJobCancelRequest {
  job_id: number
  reason?: string
  cleanup_partial_results: boolean
}

export interface BatchJobRecord {
  id: number
  job_id: number
  job_name?: string
  description?: string
  file_count: number
  success_count: number
  fail_count: number
  processing_time: number
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
  analysis_type: string
  analysis_config: BatchAnalysisConfig
  created_at: string
  started_at?: string
  completed_at?: string
  total_processing_time?: number
  estimated_cost?: number
  actual_cost?: number
  user_id: number
  queue_position?: number
  success_rate: number
  average_confidence: number
  user_rating?: number
  user_feedback?: string
}

export interface BatchHistoryResponse {
  success: boolean
  records: BatchJobRecord[]
  total: number
  pagination: {
    page: number
    per_page: number
    total: number
    pages: number
  }
  statistics: {
    total_jobs: number
    completed_jobs: number
    overall_success_rate: number
    total_files_processed: number
  }
}

export interface BatchMetrics {
  period_days: number
  total_jobs: number
  total_files_processed: number
  overall_success_rate: number
  average_processing_time_per_file: number
  cost_statistics: {
    total_cost: number
    average_cost_per_file: number
    cost_trend: 'increasing' | 'decreasing' | 'stable'
  }
  performance_trends: Array<{
    date: string
    jobs_count: number
    files_processed: number
    success_rate: number
    average_processing_time: number
  }>
  popular_analysis_types: Array<{
    analysis_type: string
    usage_count: number
    success_rate: number
  }>
}

export interface BatchMetricsResponse {
  success: boolean
  data: {
    totalJobs: number
    successRate: number
    totalFiles: number
    avgProcessingTime: number
    statusDistribution: Array<{
      status: string
      count: number
    }>
    typeDistribution: Array<{
      analysis_type: string
      count: number
    }>
    timeSeriesData: Array<{
      date: string
      job_count: number
      avg_processing_time: number
    }>
    fileSizeDistribution: Array<{
      size_range: string
      count: number
    }>
    errorTypeDistribution: Array<{
      error_type: string
      count: number
    }>
    dailyStats: Array<{
      date: string
      total_jobs: number
      completed_jobs: number
      failed_jobs: number
      success_rate: number
      total_files: number
      avg_processing_time: number
    }>
    performance: {
      minProcessingTime: number
      maxProcessingTime: number
      avgQueueTime: number
      avgConcurrency: number
      peakThroughput: number
      avgThroughput: number
    }
    cost: {
      totalCost: number
      avgCostPerJob: number
      avgCostPerFile: number
    }
  }
  metrics?: BatchMetrics
  insights?: string[]
  recommendations?: string[]
  system_health?: {
    queue_length: number
    average_wait_time: number
    processing_capacity: number
    system_load: 'low' | 'medium' | 'high'
  }
}

export interface BatchCapabilities {
  max_files_per_batch: number
  max_file_size: number
  supported_formats: string[]
  concurrent_jobs_limit: number
  estimated_processing_time_per_file: number
  queue_management: {
    priority_levels: string[]
    max_queue_size: number
    average_wait_time: number
  }
  cost_structure: {
    base_cost_per_file: number
    priority_multiplier: Record<string, number>
    bulk_discounts: Array<{
      min_files: number
      discount_percentage: number
    }>
  }
}

// 组件事件类型
export interface BatchAnalysisEvents {
  'job-submitted': (jobId: number) => void
  'job-progress': (progress: BatchJobProgress) => void
  'job-completed': (results: BatchJobStatus) => void
  'job-failed': (error: string) => void
  'job-cancelled': (jobId: number) => void
  'file-processed': (result: BatchJobResult) => void
}

// 批量任务状态管理
export interface BatchJobState {
  jobId: number
  status: string
  progress: BatchJobProgress
  results: BatchJobResult[]
  error?: string
}

// 批量上传组件配置
export interface BatchUploadConfig {
  maxFiles: number
  maxFileSize: number
  acceptedTypes: string[]
  autoStart: boolean
  showProgress: boolean
  allowRetry: boolean
}