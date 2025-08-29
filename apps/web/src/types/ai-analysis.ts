// AI分析相关类型定义

export interface DocumentFormats {
  ai_available: boolean
  document_formats: {
    mimetypes: string[]
    extensions: string[]
    availability: {
      pdf: boolean
      docx: boolean
      ocr: boolean
    }
  }
  features: {
    pdf_extraction: boolean
    docx_extraction: boolean
    ocr_extraction: boolean
    ai_analysis: boolean
  }
}

export interface DocumentInfo {
  filename: string
  mimetype: string
  size: number
  type: string
  text_length?: number
  word_count?: number
  analysis_duration?: number
  truncated?: boolean
}

export interface ConfidenceScores {
  basic_info: number
  specifications: number
  features: number
  application_scenarios?: number
  certificates?: number
  overall: number
}

export interface ProductBasicInfo {
  name: string
  code: string
  category: string
  base_price: number
  description: string
  is_active?: boolean
  is_configurable?: boolean
}

export interface ProductSpecification {
  value: string
  unit: string
  description: string
}

export interface ProductFeature {
  title: string
  description: string
  icon?: string
  sort_order?: number
}

export interface ApplicationScenario {
  name: string
  icon?: string
  sort_order?: number
}

export interface ProductAccessory {
  name: string
  description: string
  type: 'standard' | 'optional'
  sort_order?: number
}

export interface ProductCertificate {
  name: string
  type: 'quality' | 'safety' | 'compliance' | 'metrology' | 'other'
  certificate_number?: string
  description: string
  sort_order?: number
}

export interface WarrantyInfo {
  period: string
  coverage: string
  terms: string[]
}

export interface ContactInfo {
  sales_phone?: string
  sales_email?: string
  support_phone?: string
  support_email?: string
  service_wechat?: string
}

export interface SupportInfo {
  warranty: WarrantyInfo
  contact_info: ContactInfo
  service_promises: string[]
}

export interface ExtractedProductData {
  basic_info: ProductBasicInfo
  specifications: Record<string, ProductSpecification>
  features: ProductFeature[]
  application_scenarios: ApplicationScenario[]
  accessories: ProductAccessory[]
  certificates: ProductCertificate[]
  support_info: SupportInfo
  configuration_schema?: Record<string, any>
  detailed_description?: string
}

export interface ValidationResult {
  valid: boolean
  warnings: string[]
  suggestions: string[]
  completeness_score: number
}

export interface AIAnalysisResult {
  success: boolean
  analysis_id?: number
  document_info: DocumentInfo
  extracted_data: ExtractedProductData
  confidence_scores: ConfidenceScores
  validation: ValidationResult
  summary: string
  text_preview: string
  analysis_timestamp: number
  error?: string
}

export interface AIAnalysisRecord {
  id: number
  document_name: string
  document_type: string
  document_size: number
  text_length: number
  word_count: number
  extracted_data: ExtractedProductData
  confidence_scores: ConfidenceScores
  analysis_summary: string
  user_modifications: Record<string, any>
  final_data: ExtractedProductData
  created_product_id?: number
  user_id: number
  analysis_duration: number
  api_tokens_used?: number
  api_cost?: number
  status: 'completed' | 'failed'
  success: boolean
  error_message?: string
  modification_rate: number
  overall_confidence: number
  created_at: string
  updated_at: string
  created_product?: {
    id: number
    name: string
    code: string
  }
}

export interface CreateProductFromAnalysisRequest {
  analysis_id: number
  product_data: ExtractedProductData
  user_modifications: Record<string, any>
}

export interface CreateProductFromAnalysisResponse {
  success: boolean
  message: string
  product: any // 使用已有的Product类型
  analysis_id: number
  error?: string
}

export interface AnalysisHistoryResponse {
  success: boolean
  records: AIAnalysisRecord[]
  pagination: {
    page: number
    per_page: number
    total: number
    pages: number
  }
}

export interface AnalysisStatistics {
  total_analyses: number
  successful_analyses: number
  success_rate: number
  average_confidence: number
  period_days: number
}

export interface AnalysisStatisticsResponse {
  success: boolean
  statistics: AnalysisStatistics
  recent_analyses: AIAnalysisRecord[]
}

// API响应基础类型
export interface BaseAPIResponse {
  success: boolean
  error?: string
}

export interface SupportedFormatsResponse extends BaseAPIResponse {
  formats: DocumentFormats
}

export interface AnalysisResponse extends BaseAPIResponse {
  analysis_id?: number
  document_info: DocumentInfo
  extracted_data: ExtractedProductData
  confidence_scores: ConfidenceScores
  validation: ValidationResult
  summary: string
  text_preview: string
  analysis_timestamp: number
}

export interface GetAnalysisResponse extends BaseAPIResponse {
  analysis: AIAnalysisRecord
}

export interface UpdateAnalysisResponse extends BaseAPIResponse {
  message: string
  analysis: AIAnalysisRecord
}

export interface DeleteAnalysisResponse extends BaseAPIResponse {
  message: string
}

// 组件事件类型
export interface AIDocumentUploadEvents {
  'analysis-start': () => void
  'analysis-success': (result: AIAnalysisResult) => void
  'analysis-error': (error: string) => void
  'analysis-complete': () => void
}

export interface AIAnalysisPreviewEvents {
  'product-created': (productId: number) => void
  'cancel': () => void
  'field-modified': (field: string, value: any) => void
}