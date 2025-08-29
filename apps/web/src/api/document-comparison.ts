// 多文档对比分析API接口

import http from './http'
import type {
  DocumentComparisonRequest,
  DocumentComparisonResponse,
  ComparisonHistoryResponse,
  ComparisonMetricsResponse,
  ExportComparisonRequest,
  ExportComparisonResponse
} from '@/types/document-comparison'

const BASE_URL = '/document-comparison'

/**
 * 提交文档对比分析请求
 */
export const submitDocumentComparison = (
  data: DocumentComparisonRequest
): Promise<DocumentComparisonResponse> => {
  const formData = new FormData()
  
  // 添加文档文件
  data.documents.forEach((doc, index: number) => {
    formData.append(`document_${index}`, doc.file)
    formData.append(`document_${index}_name`, doc.name || doc.file.name)
    if (doc.description) {
      formData.append(`document_${index}_description`, doc.description)
    }
  })
  
  // 添加对比配置
  formData.append('comparison_config', JSON.stringify(data.comparison_config))
  
  if (data.analysis_focus) {
    formData.append('analysis_focus', JSON.stringify(data.analysis_focus))
  }
  
  return http.post(`${BASE_URL}/compare`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    timeout: 300000 // 5分钟超时
  })
}

/**
 * 获取对比结果
 */
export const getComparisonResult = (comparisonId: number): Promise<DocumentComparisonResponse> => {
  return http.get(`${BASE_URL}/result/${comparisonId}`)
}

/**
 * 获取对比历史记录
 */
export const getComparisonHistory = (params?: {
  page?: number
  per_page?: number
  start_date?: string
  end_date?: string
  status?: 'completed' | 'failed' | 'processing'
}): Promise<ComparisonHistoryResponse> => {
  return http.get(`${BASE_URL}/history`, { params })
}

/**
 * 获取对比统计信息
 */
export const getComparisonMetrics = (params?: {
  days?: number
}): Promise<ComparisonMetricsResponse> => {
  return http.get(`${BASE_URL}/metrics`, { params })
}

/**
 * 导出对比结果
 */
export const exportComparisonResult = (
  data: ExportComparisonRequest
): Promise<ExportComparisonResponse> => {
  return http.post(`${BASE_URL}/export`, data, {
    responseType: 'blob'
  })
}

/**
 * 删除对比记录
 */
export const deleteComparisonRecord = (comparisonId: number): Promise<{success: boolean, message: string}> => {
  return http.delete(`${BASE_URL}/record/${comparisonId}`)
}

/**
 * 获取支持的对比维度
 */
export const getSupportedDimensions = (): Promise<{
  success: boolean
  dimensions: Array<{
    key: string
    name: string
    description: string
    available: boolean
  }>
}> => {
  return http.get(`${BASE_URL}/dimensions`)
}