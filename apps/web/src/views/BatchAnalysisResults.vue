<template>
  <div class="batch-analysis-results-page">
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1>分析结果查看</h1>
          <p class="page-description">查看和分析批量文档处理的详细结果</p>
        </div>
        <div class="header-right">
          <el-button @click="goBack" icon="ArrowLeft">返回</el-button>
          <el-button type="primary" @click="refreshResults" icon="Refresh">刷新</el-button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading-container">
      <el-loading text="正在加载分析结果..." />
    </div>

    <div v-else-if="error" class="error-container">
      <el-alert
        title="加载失败"
        :description="error"
        type="error"
        show-icon
        :closable="false"
      />
      <el-button @click="refreshResults" style="margin-top: 15px;">重试</el-button>
    </div>

    <div v-else class="results-container">
      <!-- 任务信息摘要 -->
      <el-card v-if="jobInfo" class="job-summary-card">
        <template #header>
          <div class="card-header">
            <span class="header-title">任务信息</span>
            <el-tag :type="getStatusType(jobInfo.status)">
              {{ getStatusText(jobInfo.status) }}
            </el-tag>
          </div>
        </template>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="summary-item">
              <span class="summary-label">任务名称:</span>
              <span class="summary-value">{{ jobInfo.job_name || `批量分析任务 #${jobInfo.job_id}` }}</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="summary-item">
              <span class="summary-label">分析类型:</span>
              <span class="summary-value">{{ getAnalysisTypeText(jobInfo.analysis_type) }}</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="summary-item">
              <span class="summary-label">创建时间:</span>
              <span class="summary-value">{{ formatDateTime(jobInfo.created_at) }}</span>
            </div>
          </el-col>
        </el-row>
        
        <el-row :gutter="20" style="margin-top: 15px;">
          <el-col :span="8">
            <div class="summary-item">
              <span class="summary-label">完成时间:</span>
              <span class="summary-value">{{ jobInfo.completed_at ? formatDateTime(jobInfo.completed_at) : '未完成' }}</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="summary-item">
              <span class="summary-label">处理时长:</span>
              <span class="summary-value">{{ formatDuration(jobInfo.total_processing_time) }}</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="summary-item">
              <span class="summary-label">成功率:</span>
              <span class="summary-value">{{ jobInfo.summary?.success_rate?.toFixed(1) || 0 }}%</span>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 业务分析结果 -->
      <BusinessAnalysisResultsFixed 
        v-if="results && results.length > 0"
        :results="results"
        :analysis-type="jobInfo?.analysis_type"
        class="business-results"
      />
      
      <!-- 无结果状态 -->
      <el-card v-else class="no-results-card">
        <el-empty description="暂无分析结果" />
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Refresh } from '@element-plus/icons-vue'
import { showMessage } from '@/utils/message'
import { getBatchJobStatus, getBatchJobResults } from '@/api/batch-analysis'
import BusinessAnalysisResultsFixed from '@/components/batch/BusinessAnalysisResultsFixed.vue'
import type { BatchJobStatus, BatchJobResult } from '@/types/batch-analysis'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const error = ref('')
const jobInfo = ref<BatchJobStatus | null>(null)
const results = ref<BatchJobResult[]>([])

const jobId = computed(() => route.params.jobId as string)

const loadResults = async () => {
  if (!jobId.value) {
    error.value = '缺少任务ID参数'
    loading.value = false
    return
  }

  try {
    loading.value = true
    error.value = ''

    console.log('Loading results for job:', jobId.value)

    // 加载任务信息
    const statusResponse = await getBatchJobStatus(jobId.value)
    console.log('Status response:', statusResponse)
    
    if (statusResponse && statusResponse.success) {
      jobInfo.value = statusResponse.status || statusResponse
    } else {
      throw new Error(statusResponse?.error || '加载任务信息失败')
    }

    // 加载分析结果
    const resultsResponse = await getBatchJobResults(jobId.value)
    console.log('Results response:', resultsResponse)
    
    if (resultsResponse && resultsResponse.success) {
      // 正确处理API返回的数据结构
      const rawResults = resultsResponse.results?.results || resultsResponse.results || []
      console.log('Raw results:', rawResults)
      
      // 将API返回的数据格式转换为前端期望的格式
      results.value = rawResults.map((item: any) => ({
        file_name: item.filename || item.original_filename || 'unknown_file',
        file_size: item.file_size || 0,
        status: item.status === 'completed' ? 'success' : (item.status === 'failed' ? 'failed' : item.status),
        analysis_result: item.analysis_result,
        business_insights: item.analysis_result?.business_insights || {},
        error_message: item.error_message,
        processing_time: item.processing_duration || item.analysis_result?.processing_time || 0,
        confidence_score: item.confidence_score || item.analysis_result?.confidence_scores?.overall || 0
      }))
      
      console.log('Processed results:', results.value)
    } else {
      throw new Error(resultsResponse?.error || '加载分析结果失败')
    }

  } catch (err: any) {
    console.error('Failed to load batch results:', err)
    error.value = err.message || '加载失败'
    showMessage.error(error.value)
  } finally {
    loading.value = false
  }
}

const refreshResults = () => {
  loadResults()
}

const goBack = () => {
  router.go(-1)
}

const getStatusType = (status: string) => {
  switch (status) {
    case 'completed': return 'success'
    case 'failed': return 'danger'
    case 'processing': return 'warning'
    case 'cancelled': return 'info'
    default: return 'info'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'completed': return '已完成'
    case 'failed': return '失败'
    case 'processing': return '处理中'
    case 'pending': return '等待中'
    case 'cancelled': return '已取消'
    default: return status
  }
}

const getAnalysisTypeText = (type: string) => {
  switch (type) {
    case 'customer_requirements': return '客户需求分析'
    case 'competitor_analysis': return '竞品资料分析'
    case 'project_mining': return '历史项目挖掘'
    case 'product_extraction': return '产品信息提取'
    case 'document_classification': return '文档分类'
    case 'quality_assessment': return '质量评估'
    case 'comprehensive': return '综合分析'
    default: return type
  }
}

const formatDateTime = (dateStr: string | undefined) => {
  if (!dateStr) return '未知'
  try {
    return new Date(dateStr).toLocaleString('zh-CN')
  } catch {
    return dateStr
  }
}

const formatDuration = (seconds: number | undefined) => {
  if (!seconds) return '未知'
  
  if (seconds < 60) {
    return `${seconds.toFixed(1)}秒`
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}分${remainingSeconds.toFixed(0)}秒`
  } else {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${hours}小时${minutes}分`
  }
}

onMounted(() => {
  loadResults()
})
</script>

<style scoped>
.batch-analysis-results-page {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
  min-height: 100vh;
  background: #f5f7fa;
}

.page-header {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.header-left h1 {
  color: #303133;
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.page-description {
  color: #909399;
  font-size: 14px;
  margin: 0;
  line-height: 1.5;
}

.header-right {
  display: flex;
  gap: 10px;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  background: white;
  border-radius: 8px;
}

.error-container {
  padding: 40px;
  text-align: center;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.results-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.job-summary-card {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  font-weight: 600;
  font-size: 16px;
  color: #303133;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.summary-label {
  color: #909399;
  font-size: 13px;
  font-weight: 500;
}

.summary-value {
  color: #303133;
  font-size: 14px;
  font-weight: 500;
}

.business-results {
  flex: 1;
}

.no-results-card {
  text-align: center;
  padding: 60px 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .batch-analysis-results-page {
    padding: 15px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }
  
  .header-right {
    align-self: flex-end;
  }
  
  .header-left h1 {
    font-size: 20px;
  }
  
  .summary-item {
    margin-bottom: 15px;
  }
  
  .summary-item:last-child {
    margin-bottom: 0;
  }
}
</style>