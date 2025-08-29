<template>
  <div class="batch-job-details">
    <div class="details-header">
      <div class="job-title">
        <h3>{{ job.job_name || `任务 #${job.job_id}` }}</h3>
        <el-tag :type="getStatusTagType(job.status)" size="large">
          {{ getStatusText(job.status) }}
        </el-tag>
      </div>
      <div class="job-actions">
        <el-button
          v-if="canCancel(job.status)"
          type="warning"
          :icon="Close"
          @click="cancelJob"
        >
          取消任务
        </el-button>
        <el-button
          v-if="canRetry(job.status)"
          type="primary"
          :icon="Refresh"
          @click="retryJob"
        >
          重试任务
        </el-button>
        <el-button
          v-if="job.status === 'completed'"
          type="primary"
          :icon="View"
          @click="viewDetailedResults"
        >
          查看详细结果
        </el-button>
        <el-button
          v-if="job.status === 'completed'"
          type="success"
          :icon="Download"
          @click="downloadResults"
        >
          下载结果
        </el-button>
        <el-button @click="$emit('close')">关闭</el-button>
      </div>
    </div>
    
    <!-- 基本信息 -->
    <div class="job-overview">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-card header="基本信息">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="任务ID">
                {{ job.job_id }}
              </el-descriptions-item>
              <el-descriptions-item label="任务名称">
                {{ job.job_name || '未命名' }}
              </el-descriptions-item>
              <el-descriptions-item label="分析类型">
                {{ getAnalysisTypeText(job.analysis_type) }}
              </el-descriptions-item>
              <el-descriptions-item label="处理优先级">
                {{ getPriorityText(job.processing_priority) }}
              </el-descriptions-item>
              <el-descriptions-item label="创建时间">
                {{ formatTime(job.created_at) }}
              </el-descriptions-item>
              <el-descriptions-item label="开始时间">
                {{ job.started_at ? formatTime(job.started_at) : '未开始' }}
              </el-descriptions-item>
              <el-descriptions-item label="完成时间">
                {{ job.completed_at ? formatTime(job.completed_at) : '未完成' }}
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
        
        <el-col :span="12">
          <el-card header="进度统计">
            <div class="progress-overview">
              <div class="progress-item">
                <div class="progress-label">总体进度</div>
                <el-progress
                  :percentage="job.progress?.percentage || 0"
                  :status="job.status === 'failed' ? 'exception' : 'success'"
                  :stroke-width="12"
                />
              </div>
              
              <div class="stats-grid">
                <div class="stat-item">
                  <div class="stat-value">{{ job.progress?.total_files || 0 }}</div>
                  <div class="stat-label">总文件数</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ job.progress?.processed_files || 0 }}</div>
                  <div class="stat-label">已处理</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ job.progress?.successful_files || 0 }}</div>
                  <div class="stat-label">成功</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ job.progress?.failed_files || 0 }}</div>
                  <div class="stat-label">失败</div>
                </div>
              </div>
              
              <div v-if="job.progress?.current_file" class="current-processing">
                <el-icon class="processing-icon"><Loading /></el-icon>
                <span>当前处理: {{ job.progress.current_file }}</span>
              </div>
              
              <div v-if="job.progress?.estimated_remaining_time > 0" class="time-info">
                <el-icon><Clock /></el-icon>
                <span>预计剩余时间: {{ formatDuration(job.progress.estimated_remaining_time) }}</span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
    
    <!-- 任务描述 -->
    <div v-if="job.description" class="job-description">
      <el-card header="任务描述">
        <p>{{ job.description }}</p>
      </el-card>
    </div>
    
    <!-- 文件处理详情 -->
    <div class="file-details">
      <el-card header="文件处理详情">
        <div class="file-filters">
          <el-radio-group v-model="fileFilter" @change="filterFiles">
            <el-radio-button value="all">全部文件</el-radio-button>
            <el-radio-button value="success">成功</el-radio-button>
            <el-radio-button value="failed">失败</el-radio-button>
            <el-radio-button value="processing">处理中</el-radio-button>
          </el-radio-group>
          
          <el-input
            v-model="fileSearch"
            placeholder="搜索文件名"
            :prefix-icon="Search"
            clearable
            @input="filterFiles"
            style="width: 200px;"
          />
        </div>
        
        <el-table
          :data="filteredFileResults"
          stripe
          border
          style="width: 100%; margin-top: 15px;"
          :default-sort="{ prop: 'processing_time', order: 'descending' }"
        >
          <el-table-column prop="file_name" label="文件名" min-width="200">
            <template #default="{ row }">
              <div class="file-name-cell">
                <el-icon><Document /></el-icon>
                <span>{{ row.file_name }}</span>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="file_size" label="文件大小" width="100">
            <template #default="{ row }">
              {{ formatFileSize(row.file_size) }}
            </template>
          </el-table-column>
          
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getFileStatusType(row.status)" size="small">
                {{ getFileStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="processing_time" label="处理时间" width="100" sortable>
            <template #default="{ row }">
              {{ formatDuration(row.processing_time) }}
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button
                v-if="row.status === 'success'"
                text
                size="small"
                @click="viewFileResult(row)"
              >
                查看结果
              </el-button>
              <el-button
                v-if="row.status === 'failed'"
                text
                size="small"
                @click="viewFileError(row)"
              >
                查看错误
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
    
    <!-- 错误信息 -->
    <div v-if="job.status === 'failed' && job.error_message" class="error-details">
      <el-card header="错误信息">
        <el-alert
          :title="job.error_message"
          type="error"
          :closable="false"
          show-icon
        >
          <template #default>
            <div class="error-content">
              <p><strong>错误详情:</strong></p>
              <pre>{{ job.error_details || job.error_message }}</pre>
              
              <div v-if="job.error_timestamp" class="error-meta">
                <p><strong>错误时间:</strong> {{ formatTime(job.error_timestamp) }}</p>
              </div>
            </div>
          </template>
        </el-alert>
      </el-card>
    </div>
    
    <!-- 配置信息 -->
    <div class="config-details">
      <el-card header="配置信息">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="自动重试">
            {{ job.auto_retry_failed ? '已启用' : '已禁用' }}
          </el-descriptions-item>
          <el-descriptions-item label="最大重试次数">
            {{ job.max_retries || 0 }}
          </el-descriptions-item>
          <el-descriptions-item label="完成通知">
            {{ job.notification_settings?.email_on_completion ? '已启用' : '已禁用' }}
          </el-descriptions-item>
          <el-descriptions-item label="失败通知">
            {{ job.notification_settings?.email_on_failure ? '已启用' : '已禁用' }}
          </el-descriptions-item>
          <el-descriptions-item label="Webhook" span="2">
            {{ job.notification_settings?.webhook_url || '未配置' }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>
    </div>
    
    <!-- 文件结果查看对话框 -->
    <el-dialog
      v-model="showResultDialog"
      title="文件分析结果"
      width="80%"
      top="5vh"
    >
      <div v-if="selectedFileResult" class="file-result-content">
        <h4>{{ selectedFileResult.file_name }}</h4>
        <el-divider />
        <pre>{{ JSON.stringify(selectedFileResult.analysis_result, null, 2) }}</pre>
      </div>
    </el-dialog>
    
    <!-- 文件错误查看对话框 -->
    <el-dialog
      v-model="showErrorDialog"
      title="文件处理错误"
      width="60%"
    >
      <div v-if="selectedFileError" class="file-error-content">
        <h4>{{ selectedFileError.file_name }}</h4>
        <el-divider />
        <el-alert
          :title="selectedFileError.error_message"
          type="error"
          :closable="false"
          show-icon
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { showMessage } from '@/utils/message'
import {
  Close,
  Refresh,
  Download,
  Search,
  Document,
  Loading,
  Clock,
  View
} from '@element-plus/icons-vue'
import { cancelBatchJob, retryBatchJob } from '@/api/batch-analysis'
import type { BatchJobStatus, BatchJobResult } from '@/types/batch-analysis'

interface Props {
  job: BatchJobStatus
}

const props = defineProps<Props>()
const router = useRouter()

const emit = defineEmits<{
  jobCancelled: [jobId: number]
  jobRetried: [newJobId: number]
  close: []
}>()

// 响应式数据
const fileFilter = ref('all')
const fileSearch = ref('')
const showResultDialog = ref(false)
const showErrorDialog = ref(false)
const selectedFileResult = ref<BatchJobResult | null>(null)
const selectedFileError = ref<BatchJobResult | null>(null)

// 过滤后的文件结果
const filteredFileResults = computed(() => {
  let results = props.job.results || []
  
  // 状态过滤
  if (fileFilter.value !== 'all') {
    results = results.filter(result => result.status === fileFilter.value)
  }
  
  // 搜索过滤
  if (fileSearch.value) {
    const searchLower = fileSearch.value.toLowerCase()
    results = results.filter(result => 
      result.file_name.toLowerCase().includes(searchLower)
    )
  }
  
  return results
})

// 状态标签类型
const getStatusTagType = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info'
  }
  return statusMap[status] || 'info'
}

// 状态文本
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    failed: '已失败',
    cancelled: '已取消'
  }
  return statusMap[status] || status
}

// 分析类型文本
const getAnalysisTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    customer_requirements: '客户需求分析',
    competitor_analysis: '竞品资料分析',
    project_mining: '历史项目挖掘',
    product_extraction: '产品信息提取',
    document_classification: '文档分类',
    quality_assessment: '质量评估',
    comprehensive: '综合分析'
  }
  return typeMap[type] || type
}

// 优先级文本
const getPriorityText = (priority: string) => {
  const priorityMap: Record<string, string> = {
    speed: '速度优先',
    accuracy: '准确性优先',
    balanced: '平衡模式'
  }
  return priorityMap[priority] || priority
}

// 文件状态类型
const getFileStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    success: 'success',
    failed: 'danger',
    processing: 'warning',
    skipped: 'info'
  }
  return statusMap[status] || 'info'
}

// 文件状态文本
const getFileStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    success: '成功',
    failed: '失败',
    processing: '处理中',
    skipped: '跳过'
  }
  return statusMap[status] || status
}

// 判断是否可以取消
const canCancel = (status: string) => {
  return ['pending', 'processing'].includes(status)
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

// 文件大小格式化
const formatFileSize = (size: number): string => {
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB'
  if (size < 1024 * 1024 * 1024) return (size / (1024 * 1024)).toFixed(1) + ' MB'
  return (size / (1024 * 1024 * 1024)).toFixed(1) + ' GB'
}

// 过滤文件
const filterFiles = () => {
  // 过滤逻辑在 computed 中处理
}

// 取消任务
const cancelJob = async () => {
  try {
    const confirmResult = await ElMessageBox.confirm(
      `确定要取消任务 "${props.job.job_name || `#${props.job.job_id}`}" 吗？`,
      '取消任务',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    if (confirmResult !== 'confirm') return
    
    const response = await cancelBatchJob(props.job.job_id)
    
    if (response.success) {
      showMessage.success('任务已取消')
      emit('jobCancelled', props.job.job_id)
    } else {
      throw new Error(response.error || '取消任务失败')
    }
    
  } catch (error: any) {
    if (error.message !== 'cancel') {
      console.error('Cancel job error:', error)
      showMessage.error(error.message || '取消任务失败')
    }
  }
}

// 重试任务
const retryJob = async () => {
  try {
    const confirmResult = await ElMessageBox.confirm(
      `确定要重试任务 "${props.job.job_name || `#${props.job.job_id}`}" 吗？`,
      '重试任务',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    
    if (confirmResult !== 'confirm') return
    
    const response = await retryBatchJob(props.job.job_id)
    
    if (response.success) {
      showMessage.success(`任务已重新提交，新任务ID: ${response.new_job_id}`)
      emit('jobRetried', response.new_job_id)
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

// 查看详细结果
const viewDetailedResults = () => {
  router.push(`/batch-analysis/results/${props.job.job_id}`)
  emit('close')
}

// 下载结果
const downloadResults = () => {
  showMessage.info('开始下载结果文件...')
  // 这里应该调用下载API
}

// 查看文件结果
const viewFileResult = (result: BatchJobResult) => {
  selectedFileResult.value = result
  showResultDialog.value = true
}

// 查看文件错误
const viewFileError = (result: BatchJobResult) => {
  selectedFileError.value = result
  showErrorDialog.value = true
}
</script>

<style scoped>
.batch-job-details {
  padding: 20px;
}

.details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 15px;
  border-bottom: 2px solid #ebeef5;
}

.job-title {
  display: flex;
  align-items: center;
  gap: 15px;
}

.job-title h3 {
  margin: 0;
  color: #303133;
  font-size: 20px;
  font-weight: 600;
}

.job-actions {
  display: flex;
  gap: 10px;
}

.job-overview {
  margin-bottom: 30px;
}

.progress-overview {
  padding: 20px;
}

.progress-item {
  margin-bottom: 20px;
}

.progress-label {
  color: #606266;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 10px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
  margin: 20px 0;
}

.stat-item {
  text-align: center;
  padding: 15px;
  background: #f9f9f9;
  border-radius: 6px;
}

.stat-value {
  color: #303133;
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 5px;
}

.stat-label {
  color: #909399;
  font-size: 12px;
}

.current-processing {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #409eff;
  font-size: 14px;
  margin-bottom: 10px;
}

.processing-icon {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.time-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #909399;
  font-size: 14px;
}

.job-description {
  margin-bottom: 30px;
}

.job-description p {
  color: #606266;
  line-height: 1.6;
  margin: 0;
}

.file-details {
  margin-bottom: 30px;
}

.file-filters {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.file-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.error-details {
  margin-bottom: 30px;
}

.error-content {
  margin-top: 15px;
}

.error-content pre {
  background: #f5f5f5;
  padding: 15px;
  border-radius: 4px;
  overflow-x: auto;
  color: #606266;
  font-size: 12px;
  line-height: 1.4;
}

.error-meta {
  margin-top: 15px;
  color: #909399;
  font-size: 12px;
}

.config-details {
  margin-bottom: 20px;
}

.file-result-content {
  max-height: 60vh;
  overflow-y: auto;
}

.file-result-content h4 {
  margin: 0 0 15px 0;
  color: #303133;
  font-size: 16px;
}

.file-result-content pre {
  background: #f5f5f5;
  padding: 20px;
  border-radius: 6px;
  overflow-x: auto;
  color: #606266;
  font-size: 12px;
  line-height: 1.4;
  max-height: 400px;
  overflow-y: auto;
}

.file-error-content h4 {
  margin: 0 0 15px 0;
  color: #303133;
  font-size: 16px;
}

:deep(.el-card__header) {
  background: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
  font-weight: 600;
}

:deep(.el-progress-bar__outer) {
  background-color: #ebeef5;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .details-header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }
  
  .job-actions {
    width: 100%;
    justify-content: space-between;
    flex-wrap: wrap;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .file-filters {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }
}
</style>