// 多文档对比分析类型定义

export interface DocumentForComparison {
  file: File
  name?: string
  description?: string
  metadata?: Record<string, any>
}

export interface ComparisonConfig {
  dimensions: string[] // ['content', 'structure', 'features', 'specifications', 'quality']
  analysis_depth: 'basic' | 'detailed' | 'comprehensive'
  include_similarities: boolean
  include_differences: boolean
  generate_recommendations: boolean
  custom_criteria?: Array<{
    name: string
    description: string
    weight: number
  }>
}

export interface AnalysisFocus {
  focus_areas: string[] // ['technical_specs', 'pricing', 'features', 'quality', 'compliance']
  priority_weights: Record<string, number>
  specific_requirements?: string[]
}

export interface DocumentComparisonRequest {
  documents: DocumentForComparison[]
  comparison_config: ComparisonConfig
  analysis_focus?: AnalysisFocus
}

export interface ComparisonDimension {
  dimension: string
  similarities: Array<{
    aspect: string
    description: string
    confidence: number
    details: string[]
  }>
  differences: Array<{
    aspect: string
    document_variations: Record<string, any>
    significance: 'low' | 'medium' | 'high'
    impact_assessment: string
  }>
  recommendations: string[]
}

export interface DocumentAnalysisResult {
  document_name: string
  key_features: string[]
  technical_specifications: Record<string, any>
  quality_indicators: Record<string, number>
  unique_aspects: string[]
  potential_issues: string[]
  overall_assessment: {
    score: number
    strengths: string[]
    weaknesses: string[]
  }
}

export interface ComparisonSummary {
  total_documents: number
  comparison_dimensions: number
  overall_similarity_score: number
  key_insights: string[]
  recommended_choice?: {
    document_name: string
    reasons: string[]
    score: number
  }
  risk_factors: string[]
}

export interface DocumentComparisonResult {
  comparison_id: number
  documents_analyzed: DocumentAnalysisResult[]
  dimension_analysis: ComparisonDimension[]
  comparison_summary: ComparisonSummary
  detailed_matrix: Record<string, Record<string, any>>
  generated_report: string
  analysis_metadata: {
    analysis_duration: number
    dimensions_analyzed: string[]
    quality_score: number
    completeness_score: number
  }
}

export interface DocumentComparisonResponse {
  success: boolean
  comparison_id: number
  status: 'processing' | 'completed' | 'failed'
  result?: DocumentComparisonResult
  progress?: {
    current_step: string
    percentage: number
    estimated_remaining_time: number
  }
  error?: string
  error_details?: string[]
}

export interface ComparisonRecord {
  id: number
  document_names: string[]
  document_count: number
  comparison_config: ComparisonConfig
  analysis_focus?: AnalysisFocus
  status: 'processing' | 'completed' | 'failed'
  overall_similarity_score?: number
  recommended_choice?: string
  created_at: string
  completed_at?: string
  analysis_duration?: number
  user_id: number
  user_rating?: number
  user_feedback?: string
}

export interface ComparisonHistoryResponse {
  success: boolean
  records: ComparisonRecord[]
  pagination: {
    page: number
    per_page: number
    total: number
    pages: number
  }
  statistics: {
    total_comparisons: number
    average_documents_per_comparison: number
    success_rate: number
  }
}

export interface ComparisonMetrics {
  period_days: number
  total_comparisons: number
  successful_comparisons: number
  success_rate: number
  average_documents_per_comparison: number
  most_compared_dimensions: Array<{
    dimension: string
    usage_count: number
    average_effectiveness: number
  }>
  trend_data: Array<{
    date: string
    comparisons_count: number
    success_rate: number
    average_similarity: number
  }>
}

export interface ComparisonMetricsResponse {
  success: boolean
  metrics: ComparisonMetrics
  insights: string[]
  popular_dimensions: string[]
}

export interface ExportComparisonRequest {
  comparison_id: number
  format: 'pdf' | 'excel' | 'word' | 'json'
  include_detailed_analysis: boolean
  include_charts: boolean
  custom_template?: string
}

export interface ExportComparisonResponse {
  success: boolean
  download_url?: string
  file_name: string
  file_size: number
  expires_at: string
  error?: string
}

// 组件事件类型
export interface DocumentComparisonEvents {
  'comparison-start': () => void
  'comparison-progress': (progress: { percentage: number; step: string }) => void
  'comparison-success': (result: DocumentComparisonResult) => void
  'comparison-error': (error: string) => void
  'document-added': (document: DocumentForComparison) => void
  'document-removed': (index: number) => void
  'config-changed': (config: ComparisonConfig) => void
}