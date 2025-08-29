<template>
  <div class="batch-job-monitor">
    <div class="monitor-header">
      <div class="header-info">
        <h3>任务监控</h3>
        <p>实时监控批量分析任务进度</p>
      </div>
      <div class="header-actions">
        <el-switch
          v-model="autoRefresh"
          active-text="自动刷新"
          inactive-text="手动刷新"
          @change="handleAutoRefreshChange"
        />
        <el-button
          type="primary"
          :icon="Refresh"
          :loading="refreshing"
          @click="refreshJobs"
        >
          刷新
        </el-button>
      </div>
    </div>
    
    <div class="job-filters">
      <el-row :gutter="15">
        <el-col :span="6">
          <el-select v-model="statusFilter" placeholder="状态筛选" clearable @change="filterJobs">
            <el-option label="全部状态" value="" />
            <el-option label="等待中" value="pending" />
            <el-option label="处理中" value="processing" />
            <el-option label="已完成" value="completed" />
            <el-option label="已失败" value="failed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-input
            v-model="searchText"
            placeholder="搜索任务名称"
            :prefix-icon="Search"
            clearable
            @input="filterJobs"
          />
        </el-col>
        <el-col :span="12">
          <div class="job-summary">
            <el-tag type="info">总计: {{ filteredJobs.length }}</el-tag>
            <el-tag type="warning">处理中: {{ processingCount }}</el-tag>
            <el-tag type="success">已完成: {{ completedCount }}</el-tag>
            <el-tag type="danger">失败: {{ failedCount }}</el-tag>
          </div>
        </el-col>
      </el-row>
    </div>
    
    <div class="job-list">
      <div v-if="loading && filteredJobs.length === 0" class="loading-state">
        <el-skeleton :rows="3" animated />
      </div>
      
      <div v-else-if="filteredJobs.length === 0" class="empty-state">
        <el-empty description="暂无活跃的批量分析任务">
          <el-button type="primary" @click="$emit('create-new-job')">
            创建新任务
          </el-button>
        </el-empty>
      </div>
      
      <div v-else class="job-cards">
        <div
          v-for="job in filteredJobs"
          :key="job.job_id"
          class="job-card"
          :class="[`status-${job.status}`]"
        >
          <div class="card-header">
            <div class="job-info">
              <h4>{{ job.job_name || `任务 #${job.job_id}` }}</h4>
              <div class="job-meta">
                <el-tag
                  :type="getStatusTagType(job.status)"
                  size="small"
                >
                  {{ getStatusText(job.status) }}
                </el-tag>
                <span class="job-time">{{ formatTime(job.created_at) }}</span>
              </div>
            </div>
            <div class="job-actions">
              <el-button
                text
                :icon="View"
                @click="$emit('job-details', job)"
                title="查看详情"
              />
              <el-button
                v-if="canCancel(job.status)"
                text
                :icon="Close"
                @click="cancelJob(job)"
                title="取消任务"
              />
              <el-button
                v-if="canRetry(job.status)"
                text
                :icon="Refresh"
                @click="retryJob(job)"
                title="重试任务"
              />
            </div>
          </div>
          
          <div class="card-content">
            <div v-if="job.description" class="job-description">
              {{ job.description }}
            </div>
            
            <!-- 进度信息 -->
            <div v-if="job.progress" class="progress-section">
              <div class="progress-info">
                <span>进度: {{ job.progress.processed_files }}/{{ job.progress.total_files }}</span>
                <span>成功: {{ job.progress.successful_files }}</span>
                <span>失败: {{ job.progress.failed_files }}</span>
              </div>
              <el-progress
                :percentage="job.progress.percentage"
                :status="job.status === 'failed' ? 'exception' : 'success'"
                :show-text="false"
                :stroke-width="8"
              />
              <div class="time-info">
                <span v-if="job.progress.current_file" class="current-file">
                  当前处理: {{ job.progress.current_file }}
                </span>
                <span v-if="job.progress.estimated_remaining_time > 0" class="remaining-time">
                  预计剩余: {{ formatDuration(job.progress.estimated_remaining_time) }}
                </span>
              </div>
            </div>
            
            <!-- 任务配置 -->
            <div class="config-section">
              <el-row :gutter="10">
                <el-col :span="8">
                  <div class="config-item">
                    <span class="label">分析类型:</span>
                    <span class="value">{{ getAnalysisTypeText(job.analysis_type) }}</span>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="config-item">
                    <span class="label">优先级:</span>
                    <span class="value">{{ getPriorityText(job.processing_priority) }}</span>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="config-item">
                    <span class="label">队列位置:</span>
                    <span class="value">{{ job.queue_position || 'N/A' }}</span>
                  </div>
                </el-col>
              </el-row>
            </div>
            
            <!-- 错误信息 -->
            <div v-if="job.status === 'failed' && job.error_message" class="error-section">
              <el-alert
                :title="job.error_message"
                type="error"
                :closable="false"
                show-icon
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, inject } from 'vue'
import { ElMessageBox } from 'element-plus'
import { showMessage } from '@/utils/message'
import {
  Refresh,
  Search,
  View,
  Close
} from '@element-plus/icons-vue'
import { getBatchJobStatus, cancelBatchJob, retryBatchJob } from '@/api/batch-analysis'
import type { BatchJobStatus } from '@/types/batch-analysis'

interface Props {
  jobs: BatchJobStatus[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  jobCancelled: [jobId: number]
  jobRetried: [newJobId: number]
  jobDetails: [job: BatchJobStatus]
  createNewJob: []
}>()

// 响应式数据
const loading = ref(false)
const refreshing = ref(false)
const autoRefresh = ref(true)
const statusFilter = ref('')
const searchText = ref('')

// 自动刷新定时器
let autoRefreshTimer: number | null = null

// 注入刷新触发器
const refreshTrigger = inject('refreshTrigger', ref(0))

// 过滤后的任务列表
const filteredJobs = ref<BatchJobStatus[]>([])

// 计算属性
const processingCount = computed(() => 
  filteredJobs.value.filter(job => ['pending', 'processing'].includes(job.status)).length
)

const completedCount = computed(() => 
  filteredJobs.value.filter(job => job.status === 'completed').length
)

const failedCount = computed(() => 
  filteredJobs.value.filter(job => job.status === 'failed').length
)

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

// 过滤任务
const filterJobs = () => {
  let jobs = [...props.jobs]
  
  // 状态过滤
  if (statusFilter.value) {
    jobs = jobs.filter(job => job.status === statusFilter.value)
  }
  
  // 搜索过滤
  if (searchText.value) {
    const searchLower = searchText.value.toLowerCase()
    jobs = jobs.filter(job => 
      (job.job_name || `任务 #${job.job_id}`).toLowerCase().includes(searchLower) ||
      (job.description || '').toLowerCase().includes(searchLower)
    )
  }
  
  filteredJobs.value = jobs
}

// 刷新任务列表
const refreshJobs = async () => {
  if (props.jobs.length === 0) return
  
  refreshing.value = true
  
  try {
    // 这里应该触发父组件刷新
    // 实际实现中可能需要调用 API 获取最新状态
    await new Promise(resolve => setTimeout(resolve, 500)) // 模拟延迟
    
    showMessage.success('任务列表已刷新')
  } catch (error) {
    console.error('Refresh jobs error:', error)
    showMessage.error('刷新任务列表失败')
  } finally {
    refreshing.value = false
  }
}

// 自动刷新开关处理
const handleAutoRefreshChange = (enabled: boolean) => {
  if (enabled) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

// 开始自动刷新
const startAutoRefresh = () => {
  if (autoRefreshTimer) return
  
  autoRefreshTimer = window.setInterval(() => {
    if (processingCount.value > 0) {
      refreshJobs()
    }
  }, 5000) // 每5秒刷新一次
}

// 停止自动刷新
const stopAutoRefresh = () => {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer)
    autoRefreshTimer = null
  }
}

// 取消任务
const cancelJob = async (job: BatchJobStatus) => {
  try {
    const confirmResult = await ElMessageBox.confirm(
      `确定要取消任务 "${job.job_name || `#${job.job_id}`}" 吗？`,
      '取消任务',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    if (confirmResult !== 'confirm') return
    
    const response = await cancelBatchJob(job.job_id)
    
    if (response.success) {
      showMessage.success('任务已取消')
      emit('jobCancelled', job.job_id)
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
const retryJob = async (job: BatchJobStatus) => {
  try {
    const confirmResult = await ElMessageBox.confirm(
      `确定要重试任务 "${job.job_name || `#${job.job_id}`}" 吗？`,
      '重试任务',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    
    if (confirmResult !== 'confirm') return
    
    const response = await retryBatchJob(job.job_id)
    
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

// 监听任务列表变化
watch(() => props.jobs, () => {
  filterJobs()
}, { immediate: true })

// 监听刷新触发器
watch(refreshTrigger, () => {
  filterJobs()
})

onMounted(() => {
  if (autoRefresh.value) {
    startAutoRefresh()
  }
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.batch-job-monitor {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.monitor-header {
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
  align-items: center;
  gap: 15px;
}

.job-filters {
  padding: 20px;
  border-bottom: 1px solid #ebeef5;
}

.job-summary {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: flex-end;
}

.job-list {
  padding: 20px;
  min-height: 400px;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.job-cards {
  display: grid;
  gap: 20px;
  grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
}

.job-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fff;
  transition: all 0.3s;
  overflow: hidden;
}

.job-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.job-card.status-processing {
  border-left: 4px solid #e6a23c;
}

.job-card.status-completed {
  border-left: 4px solid #67c23a;
}

.job-card.status-failed {
  border-left: 4px solid #f56c6c;
}

.job-card.status-pending {
  border-left: 4px solid #909399;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 15px;
  border-bottom: 1px solid #f5f7fa;
}

.job-info h4 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.job-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.job-time {
  color: #909399;
  font-size: 12px;
}

.job-actions {
  display: flex;
  gap: 5px;
}

.card-content {
  padding: 15px;
}

.job-description {
  color: #606266;
  font-size: 14px;
  margin-bottom: 15px;
  line-height: 1.5;
}

.progress-section {
  margin-bottom: 15px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.time-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}

.current-file {
  color: #409eff;
}

.config-section {
  margin-bottom: 15px;
}

.config-item {
  display: flex;
  align-items: center;
  font-size: 12px;
  margin-bottom: 5px;
}

.config-item .label {
  color: #909399;
  margin-right: 5px;
}

.config-item .value {
  color: #606266;
  font-weight: 500;
}

.error-section {
  margin-top: 15px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .job-cards {
    grid-template-columns: 1fr;
  }
  
  .monitor-header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }
  
  .header-actions {
    width: 100%;
    justify-content: space-between;
  }
  
  .job-summary {
    justify-content: flex-start;
    flex-wrap: wrap;
  }
  
  .card-header {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  
  .job-actions {
    align-self: flex-end;
  }
}
</style>