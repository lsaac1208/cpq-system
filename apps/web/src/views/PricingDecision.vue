<template>
  <div class="pricing-decision-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <el-row :gutter="20" align="middle">
        <el-col :span="16">
          <h1>
            <el-icon><TrendCharts /></el-icon>
            智能报价决策支持
          </h1>
          <p class="page-description">
            基于批量分析结果，为您提供数据驱动的报价建议和市场洞察
          </p>
        </el-col>
        <el-col :span="8" class="text-right">
          <el-button 
            type="primary" 
            @click="refreshJobs"
            :loading="loading"
            icon="Refresh"
          >
            刷新任务列表
          </el-button>
        </el-col>
      </el-row>
    </div>

    <!-- 任务选择区域 -->
    <div class="job-selection-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>选择批量分析任务</span>
            <el-tag type="info">{{ completedJobs.length }} 个已完成任务</el-tag>
          </div>
        </template>

        <div v-if="loading" class="text-center">
          <el-skeleton :rows="3" animated />
        </div>

        <div v-else-if="completedJobs.length === 0" class="empty-state">
          <el-empty description="暂无已完成的批量分析任务">
            <el-button type="primary" @click="$router.push('/batch-analysis')">
              去创建批量分析任务
            </el-button>
          </el-empty>
        </div>

        <div v-else class="jobs-grid">
          <el-card 
            v-for="job in completedJobs" 
            :key="job.job_id"
            class="job-card"
            :class="{ 'selected': selectedJobId === job.job_id }"
            @click="selectJob(job)"
            shadow="hover"
          >
            <div class="job-card-content">
              <div class="job-header">
                <h3>{{ job.job_name || `任务 ${job.job_id}` }}</h3>
                <el-tag 
                  :type="job.has_pricing_recommendations ? 'success' : 'info'"
                  size="small"
                >
                  {{ job.has_pricing_recommendations ? '已生成建议' : '待生成' }}
                </el-tag>
              </div>
              
              <div class="job-stats">
                <div class="stat-item">
                  <span class="label">文件数量:</span>
                  <span class="value">{{ job.total_files }}</span>
                </div>
                <div class="stat-item">
                  <span class="label">成功率:</span>
                  <span class="value">{{ job.progress_percentage }}%</span>
                </div>
                <div class="stat-item">
                  <span class="label">完成时间:</span>
                  <span class="value">{{ formatDate(job.end_time) }}</span>
                </div>
              </div>

              <div class="job-actions">
                <el-button 
                  type="primary" 
                  size="small"
                  @click.stop="generateRecommendations(job.job_id)"
                  :loading="generating && selectedJobId === job.job_id"
                >
                  {{ job.has_pricing_recommendations ? '查看建议' : '生成建议' }}
                </el-button>
              </div>
            </div>
          </el-card>
        </div>
      </el-card>
    </div>

    <!-- 报价建议展示区域 -->
    <div v-if="recommendations" class="recommendations-section">
      <!-- 执行摘要 -->
      <el-card class="summary-card">
        <template #header>
          <div class="card-header">
            <span>执行摘要</span>
            <el-tag :type="getConfidenceType(recommendations.confidence_score)">
              置信度: {{ (recommendations.confidence_score * 100).toFixed(1) }}%
            </el-tag>
          </div>
        </template>
        
        <div class="summary-content">
          <p class="summary-text">{{ recommendations.summary }}</p>
          <div class="key-metrics">
            <div class="metric">
              <span class="metric-label">市场趋势:</span>
              <el-tag :type="getTrendType(recommendations.market_context.market_trend)">
                {{ getTrendText(recommendations.market_context.market_trend) }}
              </el-tag>
            </div>
            <div class="metric">
              <span class="metric-label">竞争强度:</span>
              <el-tag :type="getIntensityType(recommendations.market_context.competition_intensity.level)">
                {{ getIntensityText(recommendations.market_context.competition_intensity.level) }}
              </el-tag>
            </div>
            <div class="metric">
              <span class="metric-label">推荐产品:</span>
              <span class="metric-value">{{ recommendations.product_recommendations.length }} 个</span>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 详细内容标签页 -->
      <el-card class="details-card">
        <el-tabs v-model="activeTab" type="border-card">
          <!-- 产品推荐 -->
          <el-tab-pane label="产品推荐" name="products">
            <ProductRecommendations 
              :recommendations="recommendations.product_recommendations"
              @create-quote="handleCreateQuote"
            />
          </el-tab-pane>

          <!-- 市场分析 -->
          <el-tab-pane label="市场分析" name="market">
            <MarketAnalysis :market-context="recommendations.market_context" />
          </el-tab-pane>

          <!-- 定价策略 -->
          <el-tab-pane label="定价策略" name="pricing">
            <PricingStrategies :strategies="recommendations.pricing_strategies" />
          </el-tab-pane>

          <!-- 风险机会 -->
          <el-tab-pane label="风险与机会" name="risks">
            <RiskOpportunityAnalysis :analysis="recommendations.risk_opportunity_analysis" />
          </el-tab-pane>
        </el-tabs>
      </el-card>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <el-button 
          type="primary" 
          @click="exportReport"
          :loading="exporting"
          icon="Download"
        >
          导出报告
        </el-button>
        <el-button 
          @click="shareRecommendations"
          icon="Share"
        >
          分享建议
        </el-button>
      </div>
    </div>

    <!-- 创建报价对话框 -->
    <CreateQuoteDialog
      v-model:visible="showCreateQuoteDialog"
      :product-recommendation="selectedProductRecommendation"
      @quote-created="handleQuoteCreated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { TrendCharts, Refresh, Download, Share } from '@element-plus/icons-vue'
import { pricingDecisionApi, type BatchJob, type PricingRecommendation, type ProductRecommendation } from '@/api/pricing-decision'
import ProductRecommendations from '@/components/pricing/ProductRecommendations.vue'
import MarketAnalysis from '@/components/pricing/MarketAnalysis.vue'
import PricingStrategies from '@/components/pricing/PricingStrategies.vue'
import RiskOpportunityAnalysis from '@/components/pricing/RiskOpportunityAnalysis.vue'
import CreateQuoteDialog from '@/components/pricing/CreateQuoteDialog.vue'

// 响应式数据
const loading = ref(false)
const generating = ref(false)
const exporting = ref(false)
const completedJobs = ref<BatchJob[]>([])
const selectedJobId = ref<string>('')
const recommendations = ref<PricingRecommendation | null>(null)
const activeTab = ref('products')
const showCreateQuoteDialog = ref(false)
const selectedProductRecommendation = ref<ProductRecommendation | null>(null)

// 页面加载时获取任务列表
onMounted(() => {
  loadCompletedJobs()
})

// 加载已完成的任务
const loadCompletedJobs = async () => {
  loading.value = true
  try {
    const response = await pricingDecisionApi.getCompletedJobs()
    completedJobs.value = response.jobs
  } catch (error) {
    console.error('Failed to load completed jobs:', error)
    ElMessage.error('加载任务列表失败')
  } finally {
    loading.value = false
  }
}

// 刷新任务列表
const refreshJobs = () => {
  loadCompletedJobs()
}

// 选择任务
const selectJob = (job: BatchJob) => {
  selectedJobId.value = job.job_id
  if (job.has_pricing_recommendations) {
    generateRecommendations(job.job_id)
  }
}

// 生成报价建议
const generateRecommendations = async (jobId: string) => {
  generating.value = true
  selectedJobId.value = jobId
  
  try {
    const response = await pricingDecisionApi.generateRecommendations(jobId)
    recommendations.value = response
    
    // 更新任务状态
    const job = completedJobs.value.find(j => j.job_id === jobId)
    if (job) {
      job.has_pricing_recommendations = true
    }
    
    ElMessage.success('报价建议生成成功')
  } catch (error) {
    console.error('Failed to generate recommendations:', error)
    ElMessage.error('生成报价建议失败')
  } finally {
    generating.value = false
  }
}

// 创建报价
const handleCreateQuote = (productRecommendation: ProductRecommendation) => {
  selectedProductRecommendation.value = productRecommendation
  showCreateQuoteDialog.value = true
}

// 报价创建成功处理
const handleQuoteCreated = (quote: any) => {
  ElMessage.success('报价创建成功')
  showCreateQuoteDialog.value = false
  // 可以跳转到报价详情页
  // router.push(`/quotes/${quote.id}`)
}

// 导出报告
const exportReport = async () => {
  if (!selectedJobId.value) return
  
  exporting.value = true
  try {
    const response = await pricingDecisionApi.exportRecommendations(selectedJobId.value)
    
    // 创建下载链接
    const blob = new Blob([JSON.stringify(response, null, 2)], { 
      type: 'application/json' 
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `pricing-recommendations-${selectedJobId.value}.json`
    link.click()
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('报告导出成功')
  } catch (error) {
    console.error('Failed to export report:', error)
    ElMessage.error('导出报告失败')
  } finally {
    exporting.value = false
  }
}

// 分享建议
const shareRecommendations = () => {
  ElMessageBox.alert('分享功能正在开发中', '提示', {
    confirmButtonText: '确定'
  })
}

// 格式化日期
const formatDate = (dateStr: string | null) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

// 获取置信度类型
const getConfidenceType = (score: number) => {
  if (score >= 0.8) return 'success'
  if (score >= 0.6) return 'warning'
  return 'danger'
}

// 获取趋势类型和文本
const getTrendType = (trend: string) => {
  switch (trend) {
    case 'growing': return 'success'
    case 'stable': return 'info'
    case 'declining': return 'warning'
    default: return 'info'
  }
}

const getTrendText = (trend: string) => {
  switch (trend) {
    case 'growing': return '增长'
    case 'stable': return '稳定'
    case 'declining': return '下降'
    default: return '未知'
  }
}

// 获取竞争强度类型和文本
const getIntensityType = (level: string) => {
  switch (level) {
    case 'low': return 'success'
    case 'medium': return 'warning'
    case 'high': return 'danger'
    default: return 'info'
  }
}

const getIntensityText = (level: string) => {
  switch (level) {
    case 'low': return '低'
    case 'medium': return '中等'
    case 'high': return '高'
    default: return '未知'
  }
}
</script>

<style scoped>
.pricing-decision-page {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-description {
  margin: 8px 0 0 0;
  color: #606266;
  font-size: 14px;
}

.job-selection-section {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.jobs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.job-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.job-card:hover {
  transform: translateY(-2px);
}

.job-card.selected {
  border-color: #409eff;
}

.job-card-content {
  padding: 8px;
}

.job-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.job-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.job-stats {
  margin-bottom: 16px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
  font-size: 13px;
}

.stat-item .label {
  color: #909399;
}

.stat-item .value {
  color: #303133;
  font-weight: 500;
}

.job-actions {
  text-align: right;
}

.empty-state {
  text-align: center;
  padding: 40px;
}

.recommendations-section {
  margin-top: 24px;
}

.summary-card {
  margin-bottom: 24px;
}

.summary-content {
  padding: 16px 0;
}

.summary-text {
  font-size: 16px;
  color: #303133;
  margin-bottom: 16px;
  line-height: 1.6;
}

.key-metrics {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.metric {
  display: flex;
  align-items: center;
  gap: 8px;
}

.metric-label {
  color: #909399;
  font-size: 14px;
}

.metric-value {
  color: #303133;
  font-weight: 500;
}

.details-card {
  margin-bottom: 24px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.text-right {
  text-align: right;
}

.text-center {
  text-align: center;
}
</style>