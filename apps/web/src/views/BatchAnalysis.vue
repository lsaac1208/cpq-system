<template>
  <div class="batch-analysis">
    <div class="page-header">
      <h1>批量文档分析</h1>
      <p class="page-description">高效批量处理多个文档，支持大规模数据分析和自动化处理流程</p>
    </div>

    <el-tabs v-model="activeTab" class="batch-tabs">
      <!-- 新建批量任务 -->
      <el-tab-pane label="新建任务" name="create">
        <BatchAnalysisForm 
          @job-submitted="handleJobSubmitted"
          @submission-error="handleSubmissionError"
        />
      </el-tab-pane>

      <!-- 任务监控 -->
      <el-tab-pane label="任务监控" name="monitor">
        <BatchJobMonitor 
          :jobs="activeJobs"
          @job-cancelled="handleJobCancelled"
          @job-retried="handleJobRetried"
          @job-details="handleJobDetails"
        />
      </el-tab-pane>

      <!-- 批量历史 -->
      <el-tab-pane label="批量历史" name="history">
        <BatchHistory 
          @job-selected="handleHistorySelected"
          @job-deleted="handleJobDeleted"
          @download-results="handleDownloadResults"
        />
      </el-tab-pane>

      <!-- 统计分析 -->
      <el-tab-pane label="统计分析" name="metrics">
        <BatchMetrics />
      </el-tab-pane>

      <!-- 系统状态 -->
      <el-tab-pane label="系统状态" name="status">
        <SystemStatus />
      </el-tab-pane>
    </el-tabs>

    <!-- 任务详情对话框 -->
    <el-dialog
      v-model="showJobDialog"
      title="批量任务详情"
      width="80%"
      top="5vh"
    >
      <BatchJobDetails
        v-if="selectedJob"
        :job="selectedJob"
        @job-cancelled="handleJobCancelled"
        @job-retried="handleJobRetried"
        @close="showJobDialog = false"
      />
    </el-dialog>

    <!-- 实时通知 -->
    <BatchNotification
      :notifications="notifications"
      @notification-dismissed="handleNotificationDismissed"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, provide } from 'vue'
import { ElNotification } from 'element-plus'
import { showMessage } from '@/utils/message'
import BatchAnalysisForm from '@/components/batch/BatchAnalysisForm.vue'
import BatchJobMonitor from '@/components/batch/BatchJobMonitor.vue'
import BatchHistory from '@/components/batch/BatchHistory.vue'
import BatchMetrics from '@/components/batch/BatchMetrics.vue'
import SystemStatus from '@/components/batch/SystemStatus.vue'
import BatchJobDetails from '@/components/batch/BatchJobDetails.vue'
import BatchNotification from '@/components/batch/BatchNotification.vue'
import { getBatchJobStatus, getBatchHistory, startBatchJob } from '@/api/batch-analysis'
import type { 
  BatchJobStatus,
  BatchJobRecord 
} from '@/types/batch-analysis'

const activeTab = ref('create')
const showJobDialog = ref(false)
const selectedJob = ref<BatchJobStatus | null>(null)

// 活跃任务列表
const activeJobs = ref<BatchJobStatus[]>([])

// 通知列表
const notifications = ref<Array<{
  id: string
  type: 'success' | 'warning' | 'error' | 'info'
  title: string
  message: string
  timestamp: number
}>>([])

// 轮询定时器
let pollingTimer: number | null = null

// 提供全局状态管理
const refreshTrigger = ref(0)
provide('refreshTrigger', refreshTrigger)

const handleJobSubmitted = async (jobId: string) => {
  activeTab.value = 'monitor'
  
  ElNotification({
    title: '任务提交成功',
    message: `批量分析任务 #${jobId} 已提交，正在启动处理...`,
    type: 'success',
    duration: 5000
  })
  
  try {
    // 自动启动任务
    const startResponse = await startBatchJob(jobId)
    
    if (startResponse.success) {
      console.log('✅ Batch job started successfully:', jobId)
      
      ElNotification({
        title: '任务已启动',
        message: `批量分析任务 #${jobId} 已开始处理`,
        type: 'info',
        duration: 3000
      })
    } else {
      console.warn('⚠️ Failed to start batch job:', startResponse)
    }
  } catch (error) {
    console.error('💥 Error starting batch job:', error)
  }
  
  // 添加到活跃任务列表
  await loadJobStatus(jobId)
  
  // 开始轮询
  startPolling()
  
  refreshTrigger.value++
}

const handleSubmissionError = (error: string) => {
  showMessage.error(`任务提交失败: ${error}`)
}

const handleJobCancelled = (jobId: string | number) => {
  showMessage.warning(`任务 #${jobId} 已取消`)
  
  // 从活跃任务列表中移除
  activeJobs.value = activeJobs.value.filter(job => job.job_id !== jobId)
  
  refreshTrigger.value++
}

const handleJobRetried = (newJobId: string | number) => {
  showMessage.success(`任务已重新提交，新任务ID: #${newJobId}`)
  
  // 加载新任务状态
  loadJobStatus(newJobId)
  
  refreshTrigger.value++
}

const handleJobDetails = (job: BatchJobStatus) => {
  selectedJob.value = job
  showJobDialog.value = true
}

const handleHistorySelected = async (record: BatchJobRecord) => {
  try {
    // 根据历史记录加载详细状态
    const response = await getBatchJobStatus(String(record.job_id))
    
    if (response && response.success && response.status) {
      // 如果成功获取到状态，使用API返回的数据
      selectedJob.value = response.status
    } else {
      // 如果API调用失败，将历史记录转换为BatchJobStatus格式
      const convertedJob: BatchJobStatus = {
        success: true,
        job_id: record.job_id,
        job_name: record.job_name || `任务 #${record.job_id}`,
        description: record.description || '',
        status: record.status,
        analysis_type: record.analysis_type,
        processing_priority: 'balanced',
        created_at: record.created_at,
        started_at: record.started_at,
        completed_at: record.completed_at,
        total_processing_time: record.total_processing_time,
        progress: {
          total_files: record.file_count,
          processed_files: record.success_count + record.fail_count,
          successful_files: record.success_count,
          failed_files: record.fail_count,
          percentage: record.file_count > 0 ? ((record.success_count + record.fail_count) / record.file_count) * 100 : 0,
          estimated_remaining_time: 0
        },
        results: [],
        summary: {
          success_rate: record.success_rate,
          average_confidence: record.average_confidence,
          total_cost: record.actual_cost,
          quality_score: 85
        }
      }
      selectedJob.value = convertedJob
    }
    
    showJobDialog.value = true
  } catch (error) {
    console.error('Failed to load job details:', error)
    showMessage.error('无法加载任务详情')
  }
}

const handleJobDeleted = () => {
  showMessage.success('任务记录已删除')
  refreshTrigger.value++
}

const handleDownloadResults = (jobId: string | number, format: string) => {
  showMessage.success(`开始下载任务 #${jobId} 的${format.toUpperCase()}结果文件`)
}

const handleNotificationDismissed = (notificationId: string) => {
  notifications.value = notifications.value.filter(n => n.id !== notificationId)
}

// 加载任务状态
const loadJobStatus = async (jobId: string | number) => {
  try {
    const response = await getBatchJobStatus(String(jobId))
    
    if (response && response.success && response.status) {
      const jobStatus = response.status
      const currentStatus = jobStatus.status
      
      // 更新或添加到活跃任务列表
      const existingIndex = activeJobs.value.findIndex(job => job.job_id === jobId)
      if (existingIndex >= 0) {
        const oldStatus = activeJobs.value[existingIndex].status
        activeJobs.value[existingIndex] = jobStatus
        
        // 只在状态改变时记录日志
        if (oldStatus !== currentStatus) {
          console.log(`📊 Job ${jobId} status changed: ${oldStatus} → ${currentStatus}`)
        }
      } else {
        // 只有在状态为 pending 或 processing 时才添加到活跃列表
        if (['pending', 'processing'].includes(currentStatus)) {
          activeJobs.value.push(jobStatus)
          console.log(`📊 Added job ${jobId} to active list with status: ${currentStatus}`)
        }
      }
      
      // 如果是完成或失败状态，从活跃列表移除
      if (['completed', 'failed', 'cancelled'].includes(currentStatus)) {
        setTimeout(() => {
          activeJobs.value = activeJobs.value.filter(job => job.job_id !== jobId)
          console.log(`📊 Removed completed job ${jobId} from active list`)
        }, 5000) // 5秒后移除
        
        // 添加完成通知
        addNotification({
          type: currentStatus === 'completed' ? 'success' : 'error',
          title: currentStatus === 'completed' ? '任务完成' : '任务失败',
          message: `批量分析任务 #${jobId} ${currentStatus === 'completed' ? '已完成' : '执行失败'}`
        })
      }
      
      // 更新选中的任务（如果是同一个）
      if (selectedJob.value?.job_id === jobId) {
        selectedJob.value = jobStatus
      }
    } else {
      console.warn(`❌ Job ${jobId} not found or no status available`)
      // 如果任务不存在，从活跃列表中移除
      activeJobs.value = activeJobs.value.filter(job => job.job_id !== jobId)
    }
  } catch (error: any) {
    console.error(`💥 Error loading job status for ${jobId}:`, error)
    
    // 如果是404错误，说明任务不存在，从活跃列表中移除
    if (error?.response?.status === 404) {
      activeJobs.value = activeJobs.value.filter(job => job.job_id !== jobId)
    }
  }
}

// 开始轮询活跃任务
const startPolling = () => {
  if (pollingTimer) return
  
  pollingTimer = window.setInterval(async () => {
    const activeJobsToCheck = activeJobs.value.filter(job => 
      ['pending', 'processing'].includes(job.status)
    )
    
    if (activeJobsToCheck.length === 0) {
      stopPolling()
      return
    }
    
    console.log(`🔄 Polling ${activeJobsToCheck.length} active jobs...`)
    
    // 轮询所有活跃任务
    const promises = activeJobsToCheck.map(job => loadJobStatus(job.job_id))
    
    await Promise.allSettled(promises)
  }, 10000) // 每10秒轮询一次，减少频率
}

// 停止轮询
const stopPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
}

// 添加通知
const addNotification = (notification: {
  type: 'success' | 'warning' | 'error' | 'info'
  title: string
  message: string
}) => {
  const id = `notification-${Date.now()}-${Math.random()}`
  notifications.value.push({
    id,
    ...notification,
    timestamp: Date.now()
  })
  
  // 5秒后自动移除
  setTimeout(() => {
    handleNotificationDismissed(id)
  }, 5000)
}

// 加载当前用户的活跃任务
const loadActiveJobs = async () => {
  try {
    // 从历史记录中获取所有未完成的任务
    const response = await getBatchHistory({
      page: 1,
      page_size: 50,
      status: '' // 获取所有状态
    })
    
    if (response && response.success && response.records) {
      // 筛选出未完成的任务
      const activeJobIds = response.records
        .filter(record => ['pending', 'processing'].includes(record.status))
        .map(record => record.job_id)
      
      console.log('🔄 Loading active jobs:', activeJobIds)
      
      // 加载每个活跃任务的详细状态
      for (const jobId of activeJobIds) {
        await loadJobStatus(jobId)
      }
      
      // 如果有活跃任务，开始轮询
      if (activeJobIds.length > 0) {
        startPolling()
      }
    }
  } catch (error) {
    console.error('Failed to load active jobs:', error)
  }
}

onMounted(async () => {
  showMessage.info('批量分析系统已就绪')
  // 加载当前活跃的任务
  await loadActiveJobs()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.batch-analysis {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
  position: relative;
}

.page-header {
  margin-bottom: 30px;
  text-align: center;
}

.page-header h1 {
  color: #303133;
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 10px;
}

.page-description {
  color: #909399;
  font-size: 16px;
  margin: 0;
  line-height: 1.5;
}

.batch-tabs {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 20px;
}

:deep(.el-tabs__header) {
  margin-bottom: 25px;
}

:deep(.el-tabs__item) {
  font-size: 16px;
  font-weight: 500;
  padding: 0 25px;
}

:deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background-color: #e4e7ed;
}

:deep(.el-dialog__body) {
  padding: 20px;
  max-height: 70vh;
  overflow-y: auto;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .batch-analysis {
    padding: 15px;
  }
  
  .page-header h1 {
    font-size: 24px;
  }
  
  .page-description {
    font-size: 14px;
  }
  
  .batch-tabs {
    padding: 15px;
  }
  
  :deep(.el-tabs__item) {
    font-size: 14px;
    padding: 0 15px;
  }
  
  :deep(.el-dialog) {
    width: 95% !important;
    margin-top: 5vh !important;
  }
}
</style>