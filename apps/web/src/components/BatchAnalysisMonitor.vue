<template>
  <div class="batch-analysis-monitor">
    <!-- 任务列表 -->
    <el-card class="jobs-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon><Menu /></el-icon>
            批量分析任务
          </span>
          <div class="header-actions">
            <el-button-group size="small">
              <el-button 
                @click="refreshJobs" 
                :loading="loading"
                :disabled="autoRefresh"
              >
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
              <el-button 
                @click="toggleAutoRefresh"
                :type="autoRefresh ? 'success' : ''"
              >
                <el-icon><Timer /></el-icon>
                {{ autoRefresh ? '自动刷新中' : '启用自动刷新' }}
              </el-button>
            </el-button-group>
          </div>
        </div>
      </template>
      
      <!-- 过滤器 -->
      <div class="filters">
        <el-select
          v-model="statusFilter"
          placeholder="按状态筛选"
          clearable
          @change="refreshJobs"
        >
          <el-option label="全部状态" value="" />
          <el-option label="等待中" value="pending" />
          <el-option label="处理中" value="processing" />
          <el-option label="已完成" value="completed" />
          <el-option label="已失败" value="failed" />
          <el-option label="已取消" value="cancelled" />
        </el-select>
      </div>
      
      <!-- 任务列表 -->
      <div v-if="jobs.length === 0 && !loading" class="empty-state">
        <el-empty description="暂无批量分析任务">
          <el-button type="primary" @click="$emit('create-job')">
            创建新任务
          </el-button>
        </el-empty>
      </div>
      
      <div v-else class="jobs-list">
        <div
          v-for="job in jobs"
          :key="job.job_id"
          class="job-item"
          :class="[`job-${job.status}`, { 'job-active': selectedJobId === job.job_id }]"
          @click="selectJob(job.job_id)"
        >
          <!-- 任务基本信息 -->
          <div class="job-info">
            <div class="job-header">
              <div class="job-title">
                <span class="job-id">{{ job.job_id }}</span>
                <el-tag
                  :type="getStatusType(job.status)"
                  size="small"
                >
                  {{ getStatusText(job.status) }}
                </el-tag>
              </div>
              <div class="job-meta">
                <span>{{ formatTime(job.created_at) }}</span>
                <span v-if="job.actual_duration">
                  耗时: {{ formatDuration(job.actual_duration) }}
                </span>
              </div>
            </div>
            
            <!-- 进度信息 -->
            <div class="job-progress">
              <div class="progress-info">
                <span>
                  进度: {{ job.processed_files }}/{{ job.total_files }}
                  ({{ job.progress_percentage.toFixed(1) }}%)
                </span>
                <span class="file-stats">
                  成功: {{ job.successful_files }}
                  失败: {{ job.failed_files }}
                </span>
              </div>
              
              <el-progress
                :percentage="job.progress_percentage"
                :status="getProgressStatus(job.status)"
                :stroke-width="6"
                striped
                :striped-flow="job.status === 'processing'"
              />
            </div>
          </div>
          
          <!-- 任务操作 -->
          <div class="job-actions">
            <el-button-group size="small">
              <el-button
                v-if="job.status === 'pending'"
                type="success"
                @click.stop="startJob(job.job_id)"
                :loading="jobOperations[job.job_id] === 'starting'"
              >
                开始
              </el-button>
              
              <el-button
                v-if="job.status === 'processing'"
                type="warning"
                @click.stop="cancelJob(job.job_id)"
                :loading="jobOperations[job.job_id] === 'cancelling'"
              >
                取消
              </el-button>
              
              <el-button
                v-if="['completed', 'failed'].includes(job.status)"
                type="primary"
                @click.stop="viewResults(job.job_id)"
              >
                查看结果
              </el-button>
              
              <el-button
                @click.stop="viewDetails(job.job_id)"
              >
                详情
              </el-button>
            </el-button-group>
          </div>
        </div>
      </div>
      
      <!-- 分页 -->
      <div v-if="pagination.total > 0" class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="refreshJobs"
          @current-change="refreshJobs"
        />
      </div>
    </el-card>
    
    <!-- 详细信息面板 -->
    <el-card v-if="selectedJob" class="details-card">
      <template #header>
        <div class="card-title">
          <el-icon><InfoFilled /></el-icon>
          任务详情: {{ selectedJob.job_id }}
        </div>
      </template>
      
      <BatchJobDetails
        :job="selectedJob"
        :files="selectedJobFiles"
        @refresh="refreshJobDetails"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { ElMessageBox, ElNotification } from 'element-plus'
import { showMessage } from '@/utils/message'
import { Refresh, Timer, InfoFilled
} from '@element-plus/icons-vue'
import BatchJobDetails from './BatchJobDetails.vue'

// Types
interface BatchJob {
  id: number
  job_id: string
  user_id: number
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
  total_files: number
  processed_files: number
  successful_files: number
  failed_files: number
  progress_percentage: number
  estimated_duration?: number
  actual_duration?: number
  start_time?: string
  end_time?: string
  created_at: string
  error_message?: string
}

interface BatchFile {
  id: number
  file_id: string
  filename: string
  status: string
  processing_duration?: number
  error_message?: string
  confidence_score?: number
}

// Emits
const emit = defineEmits<{
  'create-job': []
  'job-selected': [jobId: string]
}>()

// Reactive data
const jobs = ref<BatchJob[]>([])
const selectedJobId = ref<string>('')
const selectedJob = ref<BatchJob | null>(null)
const selectedJobFiles = ref<BatchFile[]>([])
const loading = ref(false)
const autoRefresh = ref(false)
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(20)

const pagination = reactive({
  total: 0,
  pages: 0
})

const jobOperations = reactive<Record<string, string>>({})

let refreshTimer: number | null = null

// Computed
const filteredJobs = computed(() => {
  if (!statusFilter.value) return jobs.value
  return jobs.value.filter(job => job.status === statusFilter.value)
})

// Methods
const refreshJobs = async () => {
  if (loading.value) return
  
  loading.value = true
  
  try {
    const params = new URLSearchParams({
      page: currentPage.value.toString(),
      per_page: pageSize.value.toString()
    })
    
    if (statusFilter.value) {
      params.append('status', statusFilter.value)
    }
    
    const response = await fetch(`/api/v1/batch-analysis/jobs?${params}`, {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    })
    
    const result = await response.json()
    
    if (result.success) {
      jobs.value = result.jobs
      pagination.total = result.pagination.total
      pagination.pages = result.pagination.pages
      
      // 如果当前选中的任务仍在列表中，更新其状态
      if (selectedJobId.value) {
        const currentJob = jobs.value.find(j => j.job_id === selectedJobId.value)
        if (currentJob) {
          selectedJob.value = currentJob
        }
      }
    } else {
      throw new Error(result.error || '获取任务列表失败')
    }
  } catch (error: any) {
    showMessage.error(`获取任务列表失败: ${error.message}`)
  } finally {
    loading.value = false
  }
}

const selectJob = async (jobId: string) => {
  selectedJobId.value = jobId
  emit('job-selected', jobId)
  
  const job = jobs.value.find(j => j.job_id === jobId)
  if (job) {
    selectedJob.value = job
    await refreshJobDetails()
  }
}

const refreshJobDetails = async () => {
  if (!selectedJobId.value) return
  
  try {
    // 获取任务详细状态
    const statusResponse = await fetch(`/api/v1/batch-analysis/jobs/${selectedJobId.value}/status`, {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    })
    
    const statusResult = await statusResponse.json()
    
    if (statusResult.success) {
      selectedJob.value = statusResult.status
      selectedJobFiles.value = statusResult.status.files_status || []
    }
  } catch (error: any) {
    console.error('Failed to refresh job details:', error)
  }
}

const startJob = async (jobId: string) => {
  jobOperations[jobId] = 'starting'
  
  try {
    const response = await fetch(`/api/v1/batch-analysis/jobs/${jobId}/start`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
        'Content-Type': 'application/json'
      }
    })
    
    const result = await response.json()
    
    if (result.success) {
      showMessage.success('任务已开始处理')
      await refreshJobs()
    } else {
      throw new Error(result.error || '启动任务失败')
    }
  } catch (error: any) {
    showMessage.error(`启动任务失败: ${error.message}`)
  } finally {
    delete jobOperations[jobId]
  }
}

const cancelJob = async (jobId: string) => {
  try {
    await ElMessageBox.confirm(
      '确定要取消这个批量分析任务吗？',
      '确认取消',
      {
        confirmButtonText: '确定取消',
        cancelButtonText: '继续处理',
        type: 'warning'
      }
    )
    
    jobOperations[jobId] = 'cancelling'
    
    const response = await fetch(`/api/v1/batch-analysis/jobs/${jobId}/cancel`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    })
    
    const result = await response.json()
    
    if (result.success) {
      showMessage.success('任务已取消')
      await refreshJobs()
    } else {
      throw new Error(result.error || '取消任务失败')
    }
  } catch (error: any) {
    if (error.message) {
      showMessage.error(`取消任务失败: ${error.message}`)
    }
  } finally {
    delete jobOperations[jobId]
  }
}

const viewResults = async (jobId: string) => {
  // 这里可以打开结果查看弹窗或跳转到结果页面
  ElNotification({
    title: '查看结果',
    message: `正在打开任务 ${jobId} 的结果页面...`,
    type: 'info'
  })
  
  // TODO: 实现结果查看功能
}

const viewDetails = (jobId: string) => {
  selectJob(jobId)
}

const toggleAutoRefresh = () => {
  autoRefresh.value = !autoRefresh.value
  
  if (autoRefresh.value) {
    startAutoRefresh()
    showMessage.success('已启用自动刷新 (30秒间隔)')
  } else {
    stopAutoRefresh()
    showMessage.info('已停止自动刷新')
  }
}

const startAutoRefresh = () => {
  if (refreshTimer) return
  
  refreshTimer = window.setInterval(() => {
    refreshJobs()
  }, 30000) // 30秒刷新一次
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// Utility methods
const getAuthToken = () => {
  return localStorage.getItem('auth_token') || ''
}

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    'pending': 'info',
    'processing': 'warning',
    'completed': 'success',
    'failed': 'danger',
    'cancelled': 'info'
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    'pending': '等待中',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '已失败',
    'cancelled': '已取消'
  }
  return texts[status] || status
}

const getProgressStatus = (status: string) => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  return undefined
}

const formatTime = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const formatDuration = (seconds: number) => {
  if (seconds < 60) return `${Math.round(seconds)}秒`
  if (seconds < 3600) return `${Math.round(seconds / 60)}分钟`
  return `${Math.round(seconds / 3600)}小时`
}

// Lifecycle
onMounted(() => {
  refreshJobs()
})

onUnmounted(() => {
  stopAutoRefresh()
})

// Watch for status changes to update auto-refresh
watch(jobs, (newJobs) => {
  const hasActiveJobs = newJobs.some(job => job.status === 'processing')
  
  if (hasActiveJobs && !autoRefresh.value) {
    // 如果有活跃任务但未开启自动刷新，提示用户
    setTimeout(() => {
      ElNotification({
        title: '建议启用自动刷新',
        message: '检测到有正在处理的任务，建议启用自动刷新以实时查看进度',
        type: 'info',
        duration: 5000
      })
    }, 1000)
  }
}, { deep: true })
</script>

<style scoped>
.batch-analysis-monitor {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}

@media (min-width: 1200px) {
  .batch-analysis-monitor {
    grid-template-columns: 2fr 1fr;
  }
}

.jobs-card, .details-card {
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  flex-shrink: 0;
}

.filters {
  margin-bottom: 16px;
  display: flex;
  gap: 12px;
}

.jobs-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.job-item {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.job-item:hover {
  border-color: #c6e2ff;
  background: #ecf5ff;
}

.job-item.job-active {
  border-color: #409eff;
  background: #ecf5ff;
}

.job-item.job-processing {
  border-left: 4px solid #e6a23c;
}

.job-item.job-completed {
  border-left: 4px solid #67c23a;
}

.job-item.job-failed {
  border-left: 4px solid #f56c6c;
}

.job-info {
  margin-bottom: 12px;
}

.job-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.job-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.job-id {
  font-weight: 600;
  color: #303133;
  font-family: monospace;
}

.job-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 12px;
  color: #909399;
  text-align: right;
}

.job-progress {
  margin-bottom: 8px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
}

.file-stats {
  font-size: 12px;
  color: #909399;
}

.job-actions {
  display: flex;
  justify-content: flex-end;
}

.pagination {
  margin-top: 20px;
  text-align: center;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .batch-analysis-monitor {
    padding: 16px;
    grid-template-columns: 1fr;
  }
  
  .job-header {
    flex-direction: column;
    gap: 8px;
  }
  
  .job-meta {
    text-align: left;
  }
  
  .progress-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .filters {
    flex-direction: column;
  }
}
</style>