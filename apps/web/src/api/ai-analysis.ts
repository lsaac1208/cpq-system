// AI分析相关API接口

import http from './http'
import type {
  SupportedFormatsResponse,
  AIAnalysisResult,
  GetAnalysisResponse,
  UpdateAnalysisResponse,
  CreateProductFromAnalysisRequest,
  CreateProductFromAnalysisResponse,
  AnalysisHistoryResponse,
  AnalysisStatisticsResponse,
  DeleteAnalysisResponse
} from '@/types/ai-analysis'

const BASE_URL = '/ai-analysis'

/**
 * 获取支持的文档格式信息
 */
export const getSupportedFormats = (): Promise<SupportedFormatsResponse> => {
  return http.get(`${BASE_URL}/supported-formats`)
}

/**
 * 分析产品文档
 */
export const analyzeDocument = (file: File): Promise<AIAnalysisResult> => {
  const formData = new FormData()
  formData.append('document', file)
  
  return http.post(`${BASE_URL}/analyze-document`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    timeout: 180000, // 增加到3分钟超时，确保AI分析有足够时间
    // 添加重试机制
    'axios-retry': {
      retries: 1,
      retryDelay: (retryCount) => retryCount * 2000,
      retryCondition: (error) => {
        // 只在网络错误或5xx错误时重试，不在超时时重试
        return error.code === 'ECONNABORTED' || 
               (error.response && error.response.status >= 500)
      }
    }
  })
}

/**
 * 获取分析结果
 */
export const getAnalysisResult = (analysisId: number): Promise<GetAnalysisResponse> => {
  return http.get(`${BASE_URL}/analysis/${analysisId}`)
}

/**
 * 更新分析记录的用户修正信息
 */
export const updateAnalysisModifications = (
  analysisId: number,
  data: {
    user_modifications?: Record<string, any>
    final_data?: Record<string, any>
  }
): Promise<UpdateAnalysisResponse> => {
  return http.put(`${BASE_URL}/analysis/${analysisId}`, data)
}

/**
 * 基于AI分析结果创建产品
 */
export const createProductFromAnalysis = (
  data: CreateProductFromAnalysisRequest
): Promise<CreateProductFromAnalysisResponse> => {
  return http.post(`${BASE_URL}/create-product`, data)
}

/**
 * 获取AI分析历史记录
 */
export const getAnalysisHistory = (params?: {
  page?: number
  per_page?: number
  status?: 'completed' | 'failed'
}): Promise<AnalysisHistoryResponse> => {
  return http.get(`${BASE_URL}/history`, { params })
}

/**
 * 获取AI分析统计信息 (管理员)
 */
export const getAnalysisStatistics = (days: number = 30): Promise<AnalysisStatisticsResponse> => {
  return http.get(`${BASE_URL}/statistics?days=${days}`)
}

/**
 * 删除分析记录 (管理员)
 */
export const deleteAnalysisRecord = (analysisId: number): Promise<DeleteAnalysisResponse> => {
  return http.delete(`${BASE_URL}/analysis/${analysisId}`)
}

/**
 * 批量分析文档
 */
export const batchAnalyzeDocuments = async (
  files: File[],
  onProgress?: (completed: number, total: number, current?: string) => void
): Promise<AIAnalysisResult[]> => {
  const results: AIAnalysisResult[] = []
  
  for (let i = 0; i < files.length; i++) {
    const file = files[i]
    
    try {
      if (onProgress) {
        onProgress(i, files.length, file.name)
      }
      
      const result = await analyzeDocument(file)
      results.push(result)
      
    } catch (error) {
      // 记录错误但继续处理其他文件
      console.error(`Failed to analyze ${file.name}:`, error)
      results.push({
        success: false,
        document_info: {
          filename: file.name,
          mimetype: file.type,
          size: file.size,
          type: file.name.split('.').pop() || 'unknown'
        },
        extracted_data: {
          basic_info: {
            name: '',
            code: '',
            category: '',
            base_price: 0,
            description: ''
          },
          specifications: {},
          features: [],
          application_scenarios: [],
          accessories: [],
          certificates: [],
          support_info: {
            warranty: { period: '', coverage: '', terms: [] },
            contact_info: {},
            service_promises: []
          }
        },
        confidence_scores: {
          basic_info: 0,
          specifications: 0,
          features: 0,
          overall: 0
        },
        validation: {
          valid: false,
          warnings: [],
          suggestions: [],
          completeness_score: 0
        },
        summary: 'Analysis failed',
        text_preview: '',
        analysis_timestamp: Date.now(),
        error: error instanceof Error ? error.message : 'Unknown error'
      })
    }
  }
  
  if (onProgress) {
    onProgress(files.length, files.length)
  }
  
  return results
}

/**
 * 验证AI分析结果
 */
export const validateAnalysisResult = (result: AIAnalysisResult): {
  isValid: boolean
  errors: string[]
  warnings: string[]
} => {
  const errors: string[] = []
  const warnings: string[] = []
  
  // 检查基础信息
  const basicInfo = result.extracted_data?.basic_info
  if (!basicInfo?.name?.trim()) {
    errors.push('产品名称不能为空')
  }
  if (!basicInfo?.code?.trim()) {
    errors.push('产品代码不能为空')
  }
  if (!basicInfo?.category?.trim()) {
    errors.push('产品分类不能为空')
  }
  
  // 检查置信度
  const overallConfidence = result.confidence_scores?.overall || 0
  if (overallConfidence < 0.5) {
    warnings.push(`总体置信度较低 (${(overallConfidence * 100).toFixed(0)}%)`)
  }
  
  // 检查完整性
  const hasSpecs = Object.keys(result.extracted_data?.specifications || {}).length > 0
  const hasFeatures = (result.extracted_data?.features || []).length > 0
  
  if (!hasSpecs && !hasFeatures) {
    warnings.push('未提取到技术规格和产品特性信息')
  }
  
  return {
    isValid: errors.length === 0,
    errors,
    warnings
  }
}

/**
 * 格式化分析结果摘要
 */
export const formatAnalysisSummary = (result: AIAnalysisResult): string => {
  if (!result.success) {
    return `分析失败: ${result.error || '未知错误'}`
  }
  
  const basicInfo = result.extracted_data?.basic_info
  const confidence = result.confidence_scores?.overall || 0
  
  const parts = []
  
  if (basicInfo?.name) {
    parts.push(`产品: ${basicInfo.name}`)
  }
  
  if (basicInfo?.code) {
    parts.push(`型号: ${basicInfo.code}`)
  }
  
  if (basicInfo?.category) {
    parts.push(`分类: ${basicInfo.category}`)
  }
  
  const specsCount = Object.keys(result.extracted_data?.specifications || {}).length
  if (specsCount > 0) {
    parts.push(`规格: ${specsCount}项`)
  }
  
  const featuresCount = result.extracted_data?.features?.length || 0
  if (featuresCount > 0) {
    parts.push(`特性: ${featuresCount}项`)
  }
  
  parts.push(`置信度: ${(confidence * 100).toFixed(0)}%`)
  
  return parts.join(' | ') || '分析完成但信息有限'
}

/**
 * 导出分析结果为JSON
 */
export const exportAnalysisResult = (
  result: AIAnalysisResult,
  filename?: string
): void => {
  const data = JSON.stringify(result, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  
  const link = document.createElement('a')
  link.href = url
  link.download = filename || `analysis-${Date.now()}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  URL.revokeObjectURL(url)
}

/**
 * 计算分析统计信息
 */
export const calculateAnalysisStats = (results: AIAnalysisResult[]): {
  total: number
  successful: number
  failed: number
  successRate: number
  avgConfidence: number
  avgDuration: number
} => {
  const total = results.length
  const successful = results.filter(r => r.success).length
  const failed = total - successful
  const successRate = total > 0 ? successful / total : 0
  
  const successfulResults = results.filter(r => r.success)
  const avgConfidence = successfulResults.length > 0
    ? successfulResults.reduce((sum, r) => sum + (r.confidence_scores?.overall || 0), 0) / successfulResults.length
    : 0
  
  const avgDuration = results.length > 0
    ? results.reduce((sum, r) => sum + (r.document_info?.analysis_duration || 0), 0) / results.length
    : 0
  
  return {
    total,
    successful,
    failed,
    successRate,
    avgConfidence,
    avgDuration
  }
}


/**
 * 获取最近的分析结果列表
 */
export const getRecentAnalysisResults = (limit: number = 10): Promise<{
  success: boolean
  results: Array<{
    id: number
    document_name: string
    analysis_date: string
    status: string
    success: boolean
    confidence: {
      overall: number
      basic_info: number
      specifications: number
      features: number
    }
    product_info: {
      name: string
      code: string
      category: string
      specs_count: number
    }
    analysis_duration: number
    created_product_id: number | null
  }>
  total_count: number
}> => {
  return http.get(`${BASE_URL}/recent-results?limit=${limit}`)
}