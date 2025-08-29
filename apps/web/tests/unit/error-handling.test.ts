/**
 * 错误处理功能单元测试
 * 测试改进后的前端错误处理逻辑
 */

import { describe, it, expect, vi } from 'vitest'

// 模拟 showMessage 工具
const mockShowMessage = {
  success: vi.fn(),
  error: vi.fn(),
  info: vi.fn(),
  warning: vi.fn()
}

// 模拟 API 函数
const mockAPI = {
  clearBatchHistory: vi.fn(),
  deleteBatchRecord: vi.fn(),
  getBatchHistory: vi.fn()
}

// 模拟 BatchHistory 组件的错误处理逻辑
class BatchHistoryErrorHandler {
  private showMessage: any

  constructor(showMessage: any) {
    this.showMessage = showMessage
  }

  async clearHistory(clearBatchHistoryFn: Function) {
    try {
      console.log('🗑️ 正在清空历史记录...')
      
      const response = await clearBatchHistoryFn()
      
      if (response && response.success) {
        const deletedCount = response.deleted_count || 0
        let message = response.message || '历史记录已清空'
        
        if (deletedCount === 0) {
          message = '没有找到需要清空的历史记录'
          this.showMessage.info(message)
        } else {
          message = `已成功清空 ${deletedCount} 条历史记录`
          this.showMessage.success(message)
        }
        
        return { success: true, message }
      } else {
        throw new Error(response?.error || '清空历史记录失败')
      }
    } catch (error: any) {
      if (error.message !== 'cancel') {
        let errorMessage = '清空历史记录失败'
        
        // 根据不同的错误类型提供更具体的错误信息
        if (error?.response?.status === 403) {
          errorMessage = '权限不足，无法清空历史记录'
        } else if (error?.response?.status === 404) {
          errorMessage = '清空历史服务暂不可用'
        } else if (error?.response?.status === 500) {
          errorMessage = '服务器内部错误，清空操作失败'
        } else if (error?.response?.data?.error) {
          errorMessage = error.response.data.error
        } else if (error?.message && error.message !== '清空历史记录失败') {
          errorMessage = `操作失败: ${error.message}`
        }
        
        const friendlyMessage = `${errorMessage}。请稍后重试，如问题持续存在，请联系管理员。`
        this.showMessage.error(friendlyMessage)
        
        throw error
      }
    }
  }

  async deleteRecord(deleteBatchRecordFn: Function, record: any) {
    try {
      console.log('🗑️ 正在删除记录:', record.id, '任务ID:', record.job_id)
      
      const response = await deleteBatchRecordFn(record.id)
      
      if (response && response.success) {
        const jobName = record.job_name || `任务 #${record.job_id}`
        this.showMessage.success(`"${jobName}" 记录已删除`)
        return { success: true }
      } else {
        throw new Error(response?.error || '删除记录失败')
      }
    } catch (error: any) {
      let errorMessage = '删除记录失败'
      const jobName = record.job_name || `任务 #${record.job_id}`
      
      // 根据不同的错误状态码提供具体的错误信息
      if (error?.response?.status === 403) {
        errorMessage = '权限不足，无法删除此记录'
      } else if (error?.response?.status === 404) {
        errorMessage = '记录不存在或已被删除'
      } else if (error?.response?.status === 400) {
        errorMessage = '无法删除正在处理中的任务，请等待任务完成后再试'
      } else if (error?.response?.data?.error) {
        errorMessage = error.response.data.error
      } else if (error?.message && error.message !== '删除记录失败') {
        errorMessage = `删除失败: ${error.message}`
      }
      
      const friendlyMessage = `删除 "${jobName}" 失败: ${errorMessage}。如问题持续存在，请联系管理员。`
      this.showMessage.error(friendlyMessage)
      
      throw error
    }
  }

  async loadHistory(getBatchHistoryFn: Function, params: any = {}) {
    try {
      const response = await getBatchHistoryFn(params)
      
      if (response && response.success) {
        const records = Array.isArray(response.records) ? response.records : []
        const total = response.total || 0
        return { success: true, records, total }
      } else {
        const errorMessage = response?.error || '加载历史记录失败'
        console.warn('❌ 批量历史加载失败:', errorMessage)
        this.showMessage.error(errorMessage)
        return { success: false, records: [], total: 0 }
      }
    } catch (error: any) {
      console.error('💥 Load history error:', error)
      
      let message = '加载历史记录失败'
      if (error?.response?.status === 404) {
        message = '批量分析服务暂不可用'
      } else if (error?.message) {
        message = error.message
      }
      
      this.showMessage.error(message)
      return { success: false, records: [], total: 0 }
    }
  }
}

describe('错误处理功能测试', () => {
  let errorHandler: BatchHistoryErrorHandler

  beforeEach(() => {
    vi.clearAllMocks()
    errorHandler = new BatchHistoryErrorHandler(mockShowMessage)
  })

  describe('清空历史记录错误处理', () => {
    it('应该处理成功清空多条记录', async () => {
      const mockClearFn = vi.fn().mockResolvedValue({
        success: true,
        deleted_count: 5,
        message: '历史记录已清空'
      })

      const result = await errorHandler.clearHistory(mockClearFn)

      expect(result.success).toBe(true)
      expect(mockShowMessage.success).toHaveBeenCalledWith('已成功清空 5 条历史记录')
      expect(mockShowMessage.error).not.toHaveBeenCalled()
    })

    it('应该处理没有记录需要清空的情况', async () => {
      const mockClearFn = vi.fn().mockResolvedValue({
        success: true,
        deleted_count: 0,
        message: '没有历史记录'
      })

      const result = await errorHandler.clearHistory(mockClearFn)

      expect(result.success).toBe(true)
      expect(mockShowMessage.info).toHaveBeenCalledWith('没有找到需要清空的历史记录')
      expect(mockShowMessage.error).not.toHaveBeenCalled()
    })

    it('应该处理权限不足错误(403)', async () => {
      const mockError = {
        response: { status: 403 }
      }
      const mockClearFn = vi.fn().mockRejectedValue(mockError)

      await expect(errorHandler.clearHistory(mockClearFn)).rejects.toThrow()

      expect(mockShowMessage.error).toHaveBeenCalledWith(
        '权限不足，无法清空历史记录。请稍后重试，如问题持续存在，请联系管理员。'
      )
    })

    it('应该处理服务不可用错误(404)', async () => {
      const mockError = {
        response: { status: 404 }
      }
      const mockClearFn = vi.fn().mockRejectedValue(mockError)

      await expect(errorHandler.clearHistory(mockClearFn)).rejects.toThrow()

      expect(mockShowMessage.error).toHaveBeenCalledWith(
        '清空历史服务暂不可用。请稍后重试，如问题持续存在，请联系管理员。'
      )
    })

    it('应该处理服务器内部错误(500)', async () => {
      const mockError = {
        response: { status: 500 }
      }
      const mockClearFn = vi.fn().mockRejectedValue(mockError)

      await expect(errorHandler.clearHistory(mockClearFn)).rejects.toThrow()

      expect(mockShowMessage.error).toHaveBeenCalledWith(
        '服务器内部错误，清空操作失败。请稍后重试，如问题持续存在，请联系管理员。'
      )
    })

    it('应该处理后端返回的具体错误信息', async () => {
      const mockError = {
        response: { 
          data: { error: '数据库连接失败' }
        }
      }
      const mockClearFn = vi.fn().mockRejectedValue(mockError)

      await expect(errorHandler.clearHistory(mockClearFn)).rejects.toThrow()

      expect(mockShowMessage.error).toHaveBeenCalledWith(
        '数据库连接失败。请稍后重试，如问题持续存在，请联系管理员。'
      )
    })

    it('应该处理网络错误', async () => {
      const mockError = new Error('Network Error')
      const mockClearFn = vi.fn().mockRejectedValue(mockError)

      await expect(errorHandler.clearHistory(mockClearFn)).rejects.toThrow()

      expect(mockShowMessage.error).toHaveBeenCalledWith(
        '操作失败: Network Error。请稍后重试，如问题持续存在，请联系管理员。'
      )
    })
  })

  describe('删除记录错误处理', () => {
    const mockRecord = {
      id: 123,
      job_id: 'job-456',
      job_name: '测试任务'
    }

    it('应该处理成功删除记录', async () => {
      const mockDeleteFn = vi.fn().mockResolvedValue({
        success: true
      })

      const result = await errorHandler.deleteRecord(mockDeleteFn, mockRecord)

      expect(result.success).toBe(true)
      expect(mockShowMessage.success).toHaveBeenCalledWith('"测试任务" 记录已删除')
    })

    it('应该处理权限不足错误(403)', async () => {
      const mockError = {
        response: { status: 403 }
      }
      const mockDeleteFn = vi.fn().mockRejectedValue(mockError)

      await expect(errorHandler.deleteRecord(mockDeleteFn, mockRecord)).rejects.toThrow()

      expect(mockShowMessage.error).toHaveBeenCalledWith(
        '删除 "测试任务" 失败: 权限不足，无法删除此记录。如问题持续存在，请联系管理员。'
      )
    })

    it('应该处理记录不存在错误(404)', async () => {
      const mockError = {
        response: { status: 404 }
      }
      const mockDeleteFn = vi.fn().mockRejectedValue(mockError)

      await expect(errorHandler.deleteRecord(mockDeleteFn, mockRecord)).rejects.toThrow()

      expect(mockShowMessage.error).toHaveBeenCalledWith(
        '删除 "测试任务" 失败: 记录不存在或已被删除。如问题持续存在，请联系管理员。'
      )
    })

    it('应该处理任务正在处理中的错误(400)', async () => {
      const mockError = {
        response: { status: 400 }
      }
      const mockDeleteFn = vi.fn().mockRejectedValue(mockError)

      await expect(errorHandler.deleteRecord(mockDeleteFn, mockRecord)).rejects.toThrow()

      expect(mockShowMessage.error).toHaveBeenCalledWith(
        '删除 "测试任务" 失败: 无法删除正在处理中的任务，请等待任务完成后再试。如问题持续存在，请联系管理员。'
      )
    })

    it('应该处理没有任务名称的记录', async () => {
      const mockRecordWithoutName = {
        id: 123,
        job_id: 'job-456'
      }
      
      const mockDeleteFn = vi.fn().mockResolvedValue({
        success: true
      })

      const result = await errorHandler.deleteRecord(mockDeleteFn, mockRecordWithoutName)

      expect(result.success).toBe(true)
      expect(mockShowMessage.success).toHaveBeenCalledWith('"任务 #job-456" 记录已删除')
    })
  })

  describe('加载历史记录错误处理', () => {
    it('应该处理成功加载历史记录', async () => {
      const mockData = {
        success: true,
        records: [
          { id: 1, job_name: '任务1' },
          { id: 2, job_name: '任务2' }
        ],
        total: 2
      }
      const mockLoadFn = vi.fn().mockResolvedValue(mockData)

      const result = await errorHandler.loadHistory(mockLoadFn)

      expect(result.success).toBe(true)
      expect(result.records).toHaveLength(2)
      expect(result.total).toBe(2)
      expect(mockShowMessage.error).not.toHaveBeenCalled()
    })

    it('应该处理API返回失败响应', async () => {
      const mockResponse = {
        success: false,
        error: '查询数据库失败'
      }
      const mockLoadFn = vi.fn().mockResolvedValue(mockResponse)

      const result = await errorHandler.loadHistory(mockLoadFn)

      expect(result.success).toBe(false)
      expect(result.records).toEqual([])
      expect(result.total).toBe(0)
      expect(mockShowMessage.error).toHaveBeenCalledWith('查询数据库失败')
    })

    it('应该处理服务不可用错误(404)', async () => {
      const mockError = {
        response: { status: 404 }
      }
      const mockLoadFn = vi.fn().mockRejectedValue(mockError)

      const result = await errorHandler.loadHistory(mockLoadFn)

      expect(result.success).toBe(false)
      expect(result.records).toEqual([])
      expect(mockShowMessage.error).toHaveBeenCalledWith('批量分析服务暂不可用')
    })

    it('应该处理网络错误', async () => {
      const mockError = new Error('Network timeout')
      const mockLoadFn = vi.fn().mockRejectedValue(mockError)

      const result = await errorHandler.loadHistory(mockLoadFn)

      expect(result.success).toBe(false)
      expect(result.records).toEqual([])
      expect(mockShowMessage.error).toHaveBeenCalledWith('Network timeout')
    })

    it('应该处理records不是数组的情况', async () => {
      const mockResponse = {
        success: true,
        records: null, // 不是数组
        total: 0
      }
      const mockLoadFn = vi.fn().mockResolvedValue(mockResponse)

      const result = await errorHandler.loadHistory(mockLoadFn)

      expect(result.success).toBe(true)
      expect(result.records).toEqual([]) // 应该转换为空数组
      expect(result.total).toBe(0)
    })
  })

  describe('错误消息格式化测试', () => {
    it('应该在错误消息中包含建议的解决方案', async () => {
      const mockError = {
        response: { status: 500 }
      }
      const mockClearFn = vi.fn().mockRejectedValue(mockError)

      await expect(errorHandler.clearHistory(mockClearFn)).rejects.toThrow()

      const calledMessage = mockShowMessage.error.mock.calls[0][0]
      expect(calledMessage).toContain('请稍后重试，如问题持续存在，请联系管理员。')
    })

    it('应该在删除错误消息中包含任务名称', async () => {
      const mockRecord = {
        id: 123,
        job_id: 'job-456',
        job_name: '重要任务'
      }
      const mockError = {
        response: { status: 403 }
      }
      const mockDeleteFn = vi.fn().mockRejectedValue(mockError)

      await expect(errorHandler.deleteRecord(mockDeleteFn, mockRecord)).rejects.toThrow()

      const calledMessage = mockShowMessage.error.mock.calls[0][0]
      expect(calledMessage).toContain('删除 "重要任务" 失败')
      expect(calledMessage).toContain('权限不足')
    })
  })

  describe('边界情况测试', () => {
    it('应该处理空响应对象', async () => {
      const mockClearFn = vi.fn().mockResolvedValue(null)

      await expect(errorHandler.clearHistory(mockClearFn)).rejects.toThrow()

      expect(mockShowMessage.error).toHaveBeenCalledWith(
        '清空历史记录失败。请稍后重试，如问题持续存在，请联系管理员。'
      )
    })

    it('应该处理undefined响应', async () => {
      const mockClearFn = vi.fn().mockResolvedValue(undefined)

      await expect(errorHandler.clearHistory(mockClearFn)).rejects.toThrow()

      expect(mockShowMessage.error).toHaveBeenCalledWith(
        '清空历史记录失败。请稍后重试，如问题持续存在，请联系管理员。'
      )
    })

    it('应该处理记录对象缺失字段的情况', async () => {
      const incompleteRecord = { id: 123 } // 缺少 job_id 和 job_name
      const mockDeleteFn = vi.fn().mockResolvedValue({ success: true })

      const result = await errorHandler.deleteRecord(mockDeleteFn, incompleteRecord)

      expect(result.success).toBe(true)
      expect(mockShowMessage.success).toHaveBeenCalledWith('"任务 #undefined" 记录已删除')
    })
  })
})