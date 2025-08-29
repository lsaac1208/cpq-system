<template>
  <div class="batch-history">
    <div class="history-header">
      <div class="header-info">
        <h3>批量分析历史</h3>
        <p>查看和管理历史批量分析记录</p>
      </div>
      <div class="header-actions">
        <el-button :icon="Refresh" @click="loadHistory">刷新</el-button>
        <el-button type="danger" :icon="Delete" @click="clearHistory">清空历史</el-button>
      </div>
    </div>
    
    <!-- 筛选和搜索 -->
    <div class="history-filters">
      <el-row :gutter="15">
        <el-col :span="6">
          <el-select v-model="filters.status" placeholder="状态筛选" clearable @change="applyFilters">
            <el-option label="全部状态" value="" />
            <el-option label="已完成" value="completed" />
            <el-option label="已失败" value="failed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filters.analysis_type" placeholder="分析类型" clearable @change="applyFilters">
            <el-option label="全部类型" value="" />
            <el-option label="产品信息提取" value="product_extraction" />
            <el-option label="文档分类" value="document_classification" />
            <el-option label="质量评估" value="quality_assessment" />
            <el-option label="综合分析" value="comprehensive" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="applyFilters"
          />
        </el-col>
        <el-col :span="6">
          <el-input
            v-model="filters.search"
            placeholder="搜索任务名称"
            :prefix-icon="Search"
            clearable
            @input="debounceSearch"
          />
        </el-col>
      </el-row>
    </div>
    
    <!-- 统计信息 -->
    <div class="history-stats">
      <el-row :gutter="15">
        <el-col :span="6">
          <el-statistic title="总任务数" :value="stats.total" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="成功率" :value="stats.successRate" suffix="%" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="处理文件数" :value="stats.totalFiles" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="平均处理时间" :value="stats.avgProcessingTime" suffix="分钟" />
        </el-col>
      </el-row>
    </div>
    
    <!-- 历史记录表格 -->
    <div class="history-table">
      <el-table
        v-loading="loading"
        :data="filteredHistory"
        stripe
        border
        style="width: 100%"
        :default-sort="{ prop: 'created_at', order: 'descending' }"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="job_id" label="任务ID" width="80" sortable />
        
        <el-table-column prop="job_name" label="任务名称" min-width="150">
          <template #default="{ row }">
            <div class="job-name-cell">
              <span class="name">{{ row.job_name || `任务 #${row.job_id}` }}</span>
              <span v-if="row.description" class="description">{{ row.description }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="analysis_type" label="分析类型" width="120">
          <template #default="{ row }">
            {{ getAnalysisTypeText(row.analysis_type) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="file_count" label="文件数" width="80" sortable />
        
        <el-table-column prop="success_count" label="成功/失败" width="100">
          <template #default="{ row }">
            <span class="success-count">{{ row.success_count }}</span>
            /
            <span class="fail-count">{{ row.fail_count }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="processing_time" label="处理时间" width="100" sortable>
          <template #default="{ row }">
            {{ formatDuration(row.processing_time) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="160" sortable>
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button
                text
                size="small"
                :icon="View"
                @click="viewDetails(row)"
              >
                详情
              </el-button>
              
              <el-button
                v-if="row.status === 'completed'"
                text
                size="small"
                :icon="Download"
                @click="downloadResults(row)"
              >
                下载
              </el-button>
              
              <el-button
                v-if="canRetry(row.status)"
                text
                size="small"
                :icon="Refresh"
                @click="retryJob(row)"
              >
                重试
              </el-button>
              
              <el-popconfirm
                title="确定删除这条记录吗？"
                @confirm="deleteRecord(row)"
              >
                <template #reference>
                  <el-button
                    text
                    size="small"
                    :icon="Delete"
                    class="danger-button"
                  >
                    删除
                  </el-button>
                </template>
              </el-popconfirm>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>
    
    <!-- 下载格式选择对话框 -->
    <el-dialog
      v-model="showDownloadDialog"
      title="选择下载格式"
      width="400px"
    >
      <div class="download-options">
        <el-radio-group v-model="downloadFormat">
          <el-radio value="json">JSON 格式</el-radio>
          <el-radio value="excel">Excel 表格</el-radio>
          <el-radio value="csv">CSV 文件</el-radio>
          <el-radio value="pdf">PDF 报告</el-radio>
        </el-radio-group>
      </div>
      
      <template #footer>
        <el-button @click="showDownloadDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmDownload">确定下载</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, inject, watch } from 'vue'
import { ElMessageBox } from 'element-plus'
import { showMessage } from '@/utils/message'
import {
  Refresh,
  Delete,
  Search,
  View,
  Download
} from '@element-plus/icons-vue'
import { 
  getBatchHistory, 
  deleteBatchRecord, 
  clearBatchHistory,
  downloadBatchResults,
  retryBatchJob 
} from '@/api/batch-analysis'
import type { BatchJobRecord } from '@/types/batch-analysis'

const emit = defineEmits<{
  jobSelected: [record: BatchJobRecord]
  jobDeleted: []
  downloadResults: [jobId: string | number, format: string]
}>()

// 响应式数据
const loading = ref(false)
const history = ref<BatchJobRecord[]>([])
const filteredHistory = ref<BatchJobRecord[]>([])
const showDownloadDialog = ref(false)
const downloadFormat = ref('json')
const selectedRecord = ref<BatchJobRecord | null>(null)

// 搜索防抖定时器
let searchTimer: number | null = null

// 筛选条件
const filters = reactive({
  status: '',
  analysis_type: '',
  dateRange: [] as string[],
  search: ''
})

// 分页配置
const pagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0
})

// 统计信息
const stats = computed(() => {
  // 确保 history.value 是一个数组
  const historyArray = Array.isArray(history.value) ? history.value : []
  
  const total = historyArray.length
  const completed = historyArray.filter(item => item?.status === 'completed').length
  const successRate = total > 0 ? Math.round((completed / total) * 100) : 0
  const totalFiles = historyArray.reduce((sum, item) => sum + (item?.file_count || 0), 0)
  const avgTime = historyArray.length > 0 
    ? Math.round(historyArray.reduce((sum, item) => sum + (item?.processing_time || 0), 0) / historyArray.length / 60)
    : 0
  
  return {
    total,
    successRate,
    totalFiles,
    avgProcessingTime: avgTime
  }
})

// 状态标签类型
const getStatusTagType = (status: string) => {
  const statusMap: Record<string, string> = {
    completed: 'success',
    failed: 'danger',
    cancelled: 'info'
  }
  return statusMap[status] || 'info'
}

// 状态文本
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    completed: '已完成',
    failed: '已失败',
    cancelled: '已取消'
  }
  return statusMap[status] || status
}

// 分析类型文本
const getAnalysisTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    product_extraction: '产品信息提取',
    document_classification: '文档分类',
    quality_assessment: '质量评估',
    comprehensive: '综合分析'
  }
  return typeMap[type] || type
}

// 判断是否可以重试
const canRetry = (status: string) => {
  return ['failed', 'cancelled'].includes(status)
}

// 时间格式化
const formatTime = (timestamp: string | number) => {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN')
}

// 持续时间格式化
const formatDuration = (seconds: number) => {
  if (seconds < 60) return `${seconds}秒`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`
  return `${Math.floor(seconds / 3600)}小时${Math.floor((seconds % 3600) / 60)}分钟`
}

// 加载历史记录
const loadHistory = async () => {
  loading.value = true
  
  try {
    const response = await getBatchHistory({
      page: pagination.currentPage,
      page_size: pagination.pageSize,
      status: filters.status,
      analysis_type: filters.analysis_type,
      start_date: filters.dateRange[0],
      end_date: filters.dateRange[1],
      search: filters.search
    })
    
    console.log('📊 BatchHistory API 响应:', response)
    
    if (response && response.success) {
      // 确保 records 是一个数组
      history.value = Array.isArray(response.records) ? response.records : []
      pagination.total = response.total || 0
      applyFilters()
    } else {
      // 如果响应失败，设置为空数组
      history.value = []
      pagination.total = 0
      const errorMessage = response?.error || '加载历史记录失败'
      console.warn('❌ 批量历史加载失败:', errorMessage)
      showMessage.error(errorMessage)
    }
  } catch (error: any) {
    console.error('💥 Load history error:', error)
    // 发生错误时，确保设置为安全的默认值
    history.value = []
    pagination.total = 0
    
    let message = '加载历史记录失败'
    if (error?.response?.status === 404) {
      message = '批量分析服务暂不可用'
    } else if (error?.message) {
      message = error.message
    }
    
    showMessage.error(message)
  } finally {
    loading.value = false
  }
}

// 应用筛选
const applyFilters = () => {
  // 确保 history.value 是数组
  const historyArray = Array.isArray(history.value) ? history.value : []
  let filtered = [...historyArray]
  
  // 状态筛选
  if (filters.status) {
    filtered = filtered.filter(item => item?.status === filters.status)
  }
  
  // 分析类型筛选
  if (filters.analysis_type) {
    filtered = filtered.filter(item => item?.analysis_type === filters.analysis_type)
  }
  
  // 日期范围筛选
  if (filters.dateRange && filters.dateRange.length === 2) {
    const startDate = new Date(filters.dateRange[0])
    const endDate = new Date(filters.dateRange[1])
    endDate.setHours(23, 59, 59, 999)
    
    filtered = filtered.filter(item => {
      if (!item?.created_at) return false
      const itemDate = new Date(item.created_at)
      return itemDate >= startDate && itemDate <= endDate
    })
  }
  
  // 搜索筛选
  if (filters.search) {
    const searchLower = filters.search.toLowerCase()
    filtered = filtered.filter(item => {
      if (!item) return false
      const name = item.job_name || `任务 #${item.job_id || ''}`
      const description = item.description || ''
      return name.toLowerCase().includes(searchLower) ||
             description.toLowerCase().includes(searchLower)
    })
  }
  
  filteredHistory.value = filtered
}

// 防抖搜索
const debounceSearch = () => {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  
  searchTimer = window.setTimeout(() => {
    applyFilters()
  }, 300)
}

// 排序处理
const handleSortChange = ({ prop, order }: any) => {
  // 这里可以实现客户端排序或调用API进行服务端排序
  loadHistory()
}

// 分页处理
const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.currentPage = 1
  loadHistory()
}

const handleCurrentChange = (page: number) => {
  pagination.currentPage = page
  loadHistory()
}

// 查看详情
const viewDetails = (record: BatchJobRecord) => {
  emit('jobSelected', record)
}

// 下载结果
const downloadResults = (record: BatchJobRecord) => {
  selectedRecord.value = record
  showDownloadDialog.value = true
}

// 确认下载
const confirmDownload = () => {
  if (!selectedRecord.value) return
  
  emit('downloadResults', selectedRecord.value.job_id, downloadFormat.value)
  showDownloadDialog.value = false
  selectedRecord.value = null
}

// 重试任务
const retryJob = async (record: BatchJobRecord) => {
  try {
    const confirmResult = await ElMessageBox.confirm(
      `确定要重试任务 "${record.job_name || `#${record.job_id}`}" 吗？`,
      '重试任务',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    
    if (confirmResult !== 'confirm') return
    
    const response = await retryBatchJob(String(record.job_id))
    
    if (response.success) {
      showMessage.success(`任务已重新提交，新任务ID: ${response.new_job_id}`)
      loadHistory()
    } else {
      throw new Error(response.error || '重试任务失败')
    }
    
  } catch (error: any) {
    if (error.message !== 'cancel') {
      console.error('Retry job error:', error)
      showMessage.error(error.message || '重试任务失败')
    }
  }
}

// 删除记录
const deleteRecord = async (record: BatchJobRecord) => {
  try {
    console.log('🗑️ 正在删除记录:', record.id, '任务ID:', record.job_id)
    
    const response = await deleteBatchRecord(record.id)
    
    console.log('📝 删除响应:', response)
    
    if (response && response.success) {
      const jobName = record.job_name || `任务 #${record.job_id}`
      showMessage.success(`"${jobName}" 记录已删除`)
      await loadHistory()
      emit('jobDeleted')
    } else {
      throw new Error(response?.error || '删除记录失败')
    }
  } catch (error: any) {
    console.error('💥 删除记录错误:', error)
    
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
    
    // 显示更详细和友好的错误信息
    const friendlyMessage = `删除 "${jobName}" 失败: ${errorMessage}。如问题持续存在，请联系管理员。`
    showMessage.error(friendlyMessage)
  }
}

// 清空历史
const clearHistory = async () => {
  try {
    const confirmResult = await ElMessageBox.confirm(
      '确定要清空所有历史记录吗？此操作不可撤销！',
      '清空历史',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    if (confirmResult !== 'confirm') return
    
    console.log('🗑️ 正在清空历史记录...')
    
    // 调用清空历史的API
    const response = await clearBatchHistory()
    
    console.log('📝 清空历史响应:', response)
    
    if (response && response.success) {
      // 根据删除的记录数量显示不同的消息
      const deletedCount = response.deleted_count || 0
      let message = response.message || '历史记录已清空'
      
      if (deletedCount === 0) {
        message = '没有找到需要清空的历史记录'
        showMessage.info(message)
      } else {
        message = `已成功清空 ${deletedCount} 条历史记录`
        showMessage.success(message)
      }
      
      // 刷新列表
      await loadHistory()
      emit('jobDeleted')
    } else {
      throw new Error(response?.error || '清空历史记录失败')
    }
    
  } catch (error: any) {
    if (error.message !== 'cancel') {
      console.error('💥 清空历史错误:', error)
      
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
      
      // 显示更友好的错误信息，并提供可能的解决方案
      const friendlyMessage = `${errorMessage}。请稍后重试，如问题持续存在，请联系管理员。`
      showMessage.error(friendlyMessage)
    }
  }
}

// 监听全局刷新触发器
const refreshTrigger = inject<any>('refreshTrigger')

// 监听刷新触发器变化
if (refreshTrigger) {
  watch(refreshTrigger, () => {
    loadHistory()
  })
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.batch-history {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #ebeef5;
  background: #fafafa;
}

.header-info h3 {
  margin: 0 0 5px 0;
  color: #303133;
  font-size: 18px;
  font-weight: 600;
}

.header-info p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.history-filters {
  padding: 20px;
  border-bottom: 1px solid #ebeef5;
}

.history-stats {
  padding: 20px;
  border-bottom: 1px solid #ebeef5;
  background: #f9f9f9;
}

.history-table {
  padding: 20px;
}

.job-name-cell .name {
  display: block;
  font-weight: 500;
  color: #303133;
}

.job-name-cell .description {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.success-count {
  color: #67c23a;
  font-weight: 500;
}

.fail-count {
  color: #f56c6c;
  font-weight: 500;
}

.action-buttons {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}

.danger-button {
  color: #f56c6c !important;
}

.danger-button:hover {
  color: #f56c6c !important;
  background-color: #fef0f0 !important;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.download-options {
  padding: 20px;
}

:deep(.el-table .cell) {
  padding: 8px;
}

:deep(.el-statistic__head) {
  font-size: 14px;
  color: #909399;
}

:deep(.el-statistic__content) {
  font-size: 20px;
  color: #303133;
  font-weight: 600;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .history-header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }
  
  .header-actions {
    width: 100%;
    justify-content: space-between;
  }
  
  .action-buttons {
    flex-direction: column;
    gap: 2px;
  }
  
  :deep(.el-table__body-wrapper) {
    overflow-x: auto;
  }
}
</style>