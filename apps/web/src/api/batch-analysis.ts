// 批量分析API接口

import http from './http'
import type {
  BatchAnalysisRequest,
  BatchAnalysisResponse,
  BatchJobStatus,
  BatchHistoryResponse,
  BatchMetricsResponse
} from '@/types/batch-analysis'

const BASE_URL = '/batch-analysis'

/**
 * 提交批量分析任务
 */
export const submitBatchAnalysis = (
  data: BatchAnalysisRequest
): Promise<BatchAnalysisResponse> => {
  const formData = new FormData()
  
  // 添加文档文件（后端期望字段名为 'files'）
  data.documents.forEach((file: File) => {
    formData.append('files', file)
  })
  
  // 添加配置（后端期望字段名为 'settings'）
  formData.append('settings', JSON.stringify(data.analysis_config))
  
  // 添加优先级
  formData.append('priority', '0')
  
  if (data.batch_name) {
    formData.append('batch_name', data.batch_name)
  }
  
  if (data.description) {
    formData.append('description', data.description)
  }
  
  return http.post(`${BASE_URL}/submit`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    timeout: 60000 // 1分钟超时（仅提交任务）
  })
}

/**
 * 获取批量任务状态
 */
export const getBatchJobStatus = (jobId: string): Promise<BatchJobStatus> => {
  return http.get(`${BASE_URL}/jobs/${jobId}/status`)
}

/**
 * 取消批量任务
 */
export const cancelBatchJob = (jobId: string): Promise<{success: boolean, message: string, error?: string}> => {
  return http.post(`${BASE_URL}/jobs/${jobId}/cancel`)
}

/**
 * 获取批量分析历史
 */
export const getBatchHistory = (params?: {
  page?: number
  page_size?: number
  status?: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
  analysis_type?: string
  start_date?: string
  end_date?: string
  search?: string
}): Promise<BatchHistoryResponse> => {
  return http.get(`${BASE_URL}/history`, { params })
}

/**
 * 获取批量分析统计
 */
export const getBatchMetrics = (params?: {
  days?: number
}): Promise<BatchMetricsResponse> => {
  return http.get(`${BASE_URL}/statistics`, { params })
}

/**
 * 获取批量任务结果
 */
export const getBatchJobResults = (jobId: string): Promise<{
  success: boolean
  results: any
}> => {
  return http.get(`${BASE_URL}/jobs/${jobId}/results`)
}

/**
 * 启动批量任务
 */
export const startBatchJob = (jobId: string): Promise<{
  success: boolean
  message: string
  job_id: string
}> => {
  return http.post(`${BASE_URL}/jobs/${jobId}/start`)
}

/**
 * 重试失败的批量任务
 */
export const retryBatchJob = (
  jobId: string,
  retryConfig?: {
    retry_failed_only: boolean
    max_retries: number
  }
): Promise<{success: boolean, message: string, new_job_id: string, error?: string}> => {
  return http.post(`${BASE_URL}/retry/${jobId}`, retryConfig)
}

/**
 * 下载批量分析结果
 */
export const downloadBatchResults = (
  jobId: string,
  format: 'json' | 'excel' | 'csv' = 'json'
): Promise<Blob> => {
  return http.get(`${BASE_URL}/jobs/${jobId}/results`, {
    params: { format },
    responseType: 'blob'
  })
}

/**
 * 获取批量任务详细信息
 */
export const getBatchJobDetails = (jobId: number): Promise<{
  success: boolean
  job_info: any
  results: any[]
  statistics: any
}> => {
  return http.get(`${BASE_URL}/details/${jobId}`)
}

/**
 * 删除批量任务记录
 */
export const deleteBatchJob = (jobId: number): Promise<{success: boolean, message: string}> => {
  return http.delete(`${BASE_URL}/job/${jobId}`)
}

/**
 * 获取系统批量处理能力信息
 */
export const getBatchCapabilities = (): Promise<{
  success: boolean
  capabilities: {
    max_files_per_batch: number
    max_file_size: number
    supported_formats: string[]
    concurrent_jobs_limit: number
    estimated_processing_time_per_file: number
  }
}> => {
  return http.get(`${BASE_URL}/capabilities`)
}

/**
 * 删除批量任务记录
 */
export const deleteBatchRecord = (jobId: number): Promise<{success: boolean, message: string, error?: string}> => {
  return http.delete(`${BASE_URL}/record/${jobId}`)
}

/**
 * 清空批量分析历史记录
 */
export const clearBatchHistory = (): Promise<{success: boolean, message: string, deleted_count: number, error?: string}> => {
  return http.delete(`${BASE_URL}/history/clear`)
}

/**
 * 获取系统状态
 */
export const getSystemStatus = (): Promise<{
  success: boolean
  data: {
    health: { overall: 'healthy' | 'warning' | 'error' }
    metrics: {
      queueLength: number
      activeTasks: number
      cpuUsage: number
      memoryUsage: number
      diskUsage: number
      networkUsage: number
    }
    services: Array<{
      name: string
      description: string
      status: 'running' | 'warning' | 'error' | 'stopped'
      responseTime: number
    }>
    queueStats: {
      pending: number
      processing: number
      avgWaitTime: number
    }
    queueItems: Array<{
      jobId: number
      name: string
      priority: 'high' | 'medium' | 'low'
      waitTime: number
    }>
  }
}> => {
  return http.get(`${BASE_URL}/system/status`)
}