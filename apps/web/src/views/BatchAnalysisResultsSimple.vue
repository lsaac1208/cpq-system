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
      </el-card>

      <!-- 简化的业务分析结果 -->
      <el-card v-if="results && results.length > 0" class="business-results">
        <template #header>
          <div class="card-header">
            <span class="header-title">业务分析结果</span>
            <el-tag type="success">{{ results.length }} 个文档</el-tag>
          </div>
        </template>
        
        <div class="results-list">
          <div v-for="(result, index) in results" :key="index" class="result-item">
            <div class="file-info">
              <el-icon><Document /></el-icon>
              <span class="file-name">{{ result.filename || result.file_name || result.original_filename || '未知文件' }}</span>
            </div>
            
            <div v-if="result.analysis_result" class="analysis-content">
              <!-- 客户需求分析 -->
              <div v-if="result.analysis_result.business_insights?.customer_requirements" class="insights-section">
                <h4>客户需求分析</h4>
                <div class="insights-content">
                  <div v-if="result.analysis_result.business_insights.customer_requirements.raw_analysis">
                    <div class="business-analysis">
                      <p><strong>技术需求:</strong> {{ extractTechnicalRequirements(result.analysis_result.business_insights.customer_requirements.raw_analysis) }}</p>
                      <p><strong>预算范围:</strong> {{ extractBudgetRange(result.analysis_result.business_insights.customer_requirements.raw_analysis) }}</p>
                      <p><strong>时间要求:</strong> {{ extractTimeline(result.analysis_result.business_insights.customer_requirements.raw_analysis) }}</p>
                      <p><strong>风险等级:</strong> {{ result.analysis_result.business_insights.customer_requirements.risk_assessment?.overall_risk_level || '未评估' }}</p>
                    </div>
                  </div>
                  <div v-else>
                    <p><strong>风险等级:</strong> {{ result.analysis_result.business_insights.customer_requirements.risk_assessment?.overall_risk_level || '未评估' }}</p>
                  </div>
                </div>
              </div>

              <!-- 竞品分析 -->
              <div v-if="result.analysis_result.business_insights?.competitor_analysis" class="insights-section">
                <h4>竞品分析</h4>
                <div class="insights-content">
                  <div v-if="result.analysis_result.business_insights.competitor_analysis.raw_analysis">
                    <div class="business-analysis">
                      <p><strong>产品信息:</strong> {{ extractCompetitorProduct(result.analysis_result.business_insights.competitor_analysis.raw_analysis) }}</p>
                      <p><strong>价格信息:</strong> {{ extractCompetitorPrice(result.analysis_result.business_insights.competitor_analysis.raw_analysis) }}</p>
                    </div>
                  </div>
                  <div v-else>
                    <p><strong>产品名称:</strong> {{ result.analysis_result.business_insights.competitor_analysis.competitor_info?.product_name || '未识别' }}</p>
                    <p><strong>市场地位:</strong> {{ result.analysis_result.business_insights.competitor_analysis.competitor_info?.market_position || '未知' }}</p>
                  </div>
                </div>
              </div>

              <!-- 历史项目洞察 -->
              <div v-if="result.analysis_result.business_insights?.project_insights" class="insights-section">
                <h4>历史项目洞察</h4>
                <div class="insights-content">
                  <div v-if="result.analysis_result.business_insights.project_insights.raw_analysis">
                    <div class="business-analysis">
                      <p><strong>项目信息:</strong> {{ extractProjectInfo(result.analysis_result.business_insights.project_insights.raw_analysis) }}</p>
                      <p><strong>成功经验:</strong> {{ extractSuccessPatterns(result.analysis_result.business_insights.project_insights.raw_analysis) }}</p>
                    </div>
                  </div>
                  <div v-else>
                    <p><strong>项目类型:</strong> {{ result.analysis_result.business_insights.project_insights.project_overview?.project_type || '未分类' }}</p>
                    <p><strong>成功状态:</strong> {{ result.analysis_result.business_insights.project_insights.project_overview?.success_status || '未评估' }}</p>
                  </div>
                </div>
              </div>

              <!-- 产品信息提取 -->
              <div v-if="result.analysis_result.business_insights?.product_extraction" class="insights-section">
                <h4>产品信息提取</h4>
                <div class="insights-content">
                  <div v-if="result.analysis_result.business_insights.product_extraction.raw_analysis">
                    <div class="business-analysis">
                      <p><strong>产品详情:</strong> {{ extractProductDetails(result.analysis_result.business_insights.product_extraction.raw_analysis) }}</p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 文档分类 -->
              <div v-if="result.analysis_result.business_insights?.document_classification" class="insights-section">
                <h4>文档分类</h4>
                <div class="insights-content">
                  <div v-if="result.analysis_result.business_insights.document_classification.raw_analysis">
                    <div class="business-analysis">
                      <p><strong>分类结果:</strong> {{ extractDocumentCategory(result.analysis_result.business_insights.document_classification.raw_analysis) }}</p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 质量评估 -->
              <div v-if="result.analysis_result.business_insights?.quality_assessment" class="insights-section">
                <h4>质量评估</h4>
                <div class="insights-content">
                  <div v-if="result.analysis_result.business_insights.quality_assessment.raw_analysis">
                    <div class="business-analysis">
                      <p><strong>质量评分:</strong> {{ extractQualityScore(result.analysis_result.business_insights.quality_assessment.raw_analysis) }}</p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 综合分析 -->
              <div v-if="result.analysis_result.business_insights?.comprehensive" class="insights-section">
                <h4>综合分析</h4>
                <div class="insights-content">
                  <div v-if="result.analysis_result.business_insights.comprehensive.raw_analysis">
                    <div class="business-analysis">
                      <p><strong>综合评估:</strong> {{ extractComprehensiveInsights(result.analysis_result.business_insights.comprehensive.raw_analysis) }}</p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 置信度得分 -->
              <div v-if="result.analysis_result.confidence_scores" class="insights-section">
                <h4>分析置信度</h4>
                <div class="insights-content">
                  <p><strong>整体置信度:</strong> {{ (result.analysis_result.confidence_scores.overall * 100).toFixed(1) }}%</p>
                  <p><strong>质量评级:</strong> {{ getConfidenceLevelText(result.analysis_result.confidence_scores.level) }}</p>
                </div>
              </div>

              <!-- 原始数据展示 (fallback) -->
              <div v-if="!result.analysis_result.business_insights && !result.analysis_result.confidence_scores" class="raw-data">
                <h4>分析结果</h4>
                <pre>{{ JSON.stringify(result.analysis_result, null, 2) }}</pre>
              </div>
            </div>
          </div>
        </div>
      </el-card>
      
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
import { ArrowLeft, Refresh, Document } from '@element-plus/icons-vue'
import { showMessage } from '@/utils/message'
import { getBatchJobStatus, getBatchJobResults } from '@/api/batch-analysis'
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
      results.value = resultsResponse.results?.results || resultsResponse.results || []
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

// 数据提取方法
const extractJsonFromRawAnalysis = (rawAnalysis: string) => {
  try {
    // 从markdown JSON代码块中提取JSON
    const jsonMatch = rawAnalysis.match(/```json\s*([\s\S]*?)\s*```/)
    if (jsonMatch) {
      return JSON.parse(jsonMatch[1])
    }
    // 尝试直接解析JSON
    return JSON.parse(rawAnalysis)
  } catch {
    return null
  }
}

const extractTechnicalRequirements = (rawAnalysis: string) => {
  const data = extractJsonFromRawAnalysis(rawAnalysis)
  if (data?.技术需求?.性能规格要求) {
    return data.技术需求.性能规格要求.slice(0, 3).join(', ') + (data.技术需求.性能规格要求.length > 3 ? '...' : '')
  }
  return '未提取到技术需求信息'
}

const extractBudgetRange = (rawAnalysis: string) => {
  const data = extractJsonFromRawAnalysis(rawAnalysis)
  return data?.商务需求?.预算范围 || data?.预算范围 || '未指定'
}

const extractTimeline = (rawAnalysis: string) => {
  const data = extractJsonFromRawAnalysis(rawAnalysis)
  return data?.商务需求?.项目时间线 || data?.项目时间线 || data?.时间要求 || '未指定'
}

const extractCompetitorProduct = (rawAnalysis: string) => {
  const data = extractJsonFromRawAnalysis(rawAnalysis)
  return data?.产品信息?.产品名称 || data?.competitor_product || '未识别产品'
}

const extractCompetitorPrice = (rawAnalysis: string) => {
  const data = extractJsonFromRawAnalysis(rawAnalysis)
  return data?.价格信息?.价格范围 || data?.price_info || '未获取价格信息'
}

const extractProjectInfo = (rawAnalysis: string) => {
  const data = extractJsonFromRawAnalysis(rawAnalysis)
  return data?.项目信息?.项目类型 || data?.project_type || '未分类项目'
}

const extractSuccessPatterns = (rawAnalysis: string) => {
  const data = extractJsonFromRawAnalysis(rawAnalysis)
  if (data?.成功经验 && Array.isArray(data.成功经验)) {
    return data.成功经验.slice(0, 2).join('; ')
  }
  return data?.success_patterns || '未发现明显成功模式'
}

const extractProductDetails = (rawAnalysis: string) => {
  const data = extractJsonFromRawAnalysis(rawAnalysis)
  if (data?.产品信息?.产品名称) {
    return `${data.产品信息.产品名称} - ${data.产品信息.产品描述 || '无描述'}`
  }
  return data?.product_name || '未提取到产品信息'
}

const extractDocumentCategory = (rawAnalysis: string) => {
  const data = extractJsonFromRawAnalysis(rawAnalysis)
  return data?.文档类型 || data?.document_category || '未分类'
}

const extractQualityScore = (rawAnalysis: string) => {
  const data = extractJsonFromRawAnalysis(rawAnalysis)
  const score = data?.质量评分 || data?.quality_score
  return score ? `${score}/100` : '未评分'
}

const extractComprehensiveInsights = (rawAnalysis: string) => {
  const data = extractJsonFromRawAnalysis(rawAnalysis)
  if (data?.综合评估?.关键发现) {
    return data.综合评估.关键发现.slice(0, 2).join('; ')
  }
  return data?.key_insights || '综合分析结果'
}

const getConfidenceLevelText = (level: string) => {
  const levelMap: Record<string, string> = {
    very_high: '非常高',
    high: '高',
    medium: '中等',
    low: '低',
    very_low: '很低'
  }
  return levelMap[level] || level
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

.results-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.result-item {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 20px;
  background: #fafafa;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e4e7ed;
}

.file-name {
  font-weight: 500;
  color: #303133;
  font-size: 14px;
}

.analysis-content {
  padding-top: 10px;
}

.insights-section {
  margin-bottom: 20px;
}

.insights-section h4 {
  color: #409eff;
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 10px 0;
  padding-bottom: 5px;
  border-bottom: 1px solid #e4e7ed;
}

.insights-content {
  background: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  border-left: 3px solid #409eff;
}

.insights-content p {
  color: #606266;
  font-size: 13px;
  line-height: 1.6;
  margin: 5px 0;
}

.business-analysis p {
  color: #606266;
  font-size: 13px;
  line-height: 1.6;
  margin: 8px 0;
  padding: 4px 0;
}

.raw-data {
  margin-top: 15px;
}

.raw-data h4 {
  color: #409eff;
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 10px 0;
}

.raw-data pre {
  background: #f5f5f5;
  padding: 15px;
  border-radius: 4px;
  overflow-x: auto;
  color: #606266;
  font-size: 12px;
  line-height: 1.4;
  max-height: 300px;
  overflow-y: auto;
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