// 历史数据优化Prompt系统API接口

import http from './http'
import type {
  PromptOptimizationRequest,
  PromptOptimizationResponse,
  PromptTemplateResponse,
  PromptHistoryResponse,
  OptimizationMetricsResponse,
  SavePromptTemplateRequest,
  SavePromptTemplateResponse
} from '@/types/prompt-optimization'

const BASE_URL = '/prompt-optimization'

/**
 * 获取优化建议
 */
export const getOptimizationSuggestions = (
  data: PromptOptimizationRequest
): Promise<PromptOptimizationResponse> => {
  return http.post(`${BASE_URL}/optimize`, data)
}

/**
 * 获取Prompt模板列表
 */
export const getPromptTemplates = (params?: {
  category?: string
  tag?: string
  page?: number
  per_page?: number
}): Promise<PromptTemplateResponse> => {
  return http.get(`${BASE_URL}/templates`, { params })
}

/**
 * 保存Prompt模板
 */
export const savePromptTemplate = (
  data: SavePromptTemplateRequest
): Promise<SavePromptTemplateResponse> => {
  return http.post(`${BASE_URL}/templates`, data)
}

/**
 * 获取优化历史记录
 */
export const getOptimizationHistory = (params?: {
  page?: number
  per_page?: number
  start_date?: string
  end_date?: string
}): Promise<PromptHistoryResponse> => {
  return http.get(`${BASE_URL}/history`, { params })
}

/**
 * 获取优化效果统计
 */
export const getOptimizationMetrics = (params?: {
  days?: number
}): Promise<OptimizationMetricsResponse> => {
  return http.get(`${BASE_URL}/metrics`, { params })
}

/**
 * 删除Prompt模板
 */
export const deletePromptTemplate = (templateId: number): Promise<{success: boolean, message: string}> => {
  return http.delete(`${BASE_URL}/templates/${templateId}`)
}

/**
 * 应用优化建议
 */
export const applyOptimization = (
  optimizationId: number,
  selectedSuggestions: string[]
): Promise<{success: boolean, message: string, optimized_prompt: string}> => {
  return http.post(`${BASE_URL}/apply/${optimizationId}`, {
    selected_suggestions: selectedSuggestions
  })
}