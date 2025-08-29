<template>
  <div class="business-analysis-results">
    <el-card class="results-card">
      <template #header>
        <div class="card-header">
          <span class="header-title">业务分析结果</span>
          <div class="header-actions">
            <el-dropdown @command="handleExport">
              <el-button type="primary" size="small">
                导出 <el-icon><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="pdf">导出PDF报告</el-dropdown-item>
                  <el-dropdown-item command="excel">导出Excel表格</el-dropdown-item>
                  <el-dropdown-item command="json">导出JSON数据</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </template>
      
      <div v-if="!results || results.length === 0" class="empty-state">
        <el-empty description="暂无分析结果" />
      </div>
      
      <div v-else class="results-content">
        <div class="summary-section">
          <el-row :gutter="20">
            <el-col :span="6">
              <el-statistic title="总文件数" :value="totalFiles" />
            </el-col>
            <el-col :span="6">
              <el-statistic title="成功分析" :value="successfulFiles" />
            </el-col>
            <el-col :span="6">
              <el-statistic title="失败文件" :value="failedFiles" />
            </el-col>
            <el-col :span="6">
              <el-statistic title="成功率" :value="successRate" suffix="%" />
            </el-col>
          </el-row>
        </div>
        
        <el-divider />
        
        <div class="filter-section">
          <el-row :gutter="20" justify="space-between" align="middle">
            <el-col :span="12">
              <el-input
                v-model="searchText"
                placeholder="搜索文件名或分析内容..."
                clearable
                prefix-icon="Search"
              />
            </el-col>
            <el-col :span="8">
              <el-select v-model="filterType" placeholder="筛选分析类型" clearable>
                <el-option label="全部" value="" />
                <el-option label="客户需求分析" value="customer_requirements" />
                <el-option label="竞品分析" value="competitor_analysis" />
                <el-option label="项目挖掘" value="project_mining" />
              </el-select>
            </el-col>
            <el-col :span="4">
              <el-select v-model="filterStatus" placeholder="状态" clearable>
                <el-option label="全部" value="" />
                <el-option label="成功" value="success" />
                <el-option label="失败" value="failed" />
              </el-select>
            </el-col>
          </el-row>
        </div>
        
        <div class="results-list">
          <div v-for="result in filteredResults" :key="result.file_name" class="result-item">
            <el-card class="result-card" shadow="hover">
              <div class="result-header">
                <div class="file-info">
                  <h4 class="file-name">{{ result.file_name }}</h4>
                  <div class="file-meta">
                    <el-tag :type="getStatusType(result.status)" size="small">
                      {{ getStatusText(result.status) }}
                    </el-tag>
                    <span class="file-size">{{ formatFileSize(result.file_size) }}</span>
                    <span class="processing-time">{{ result.processing_time.toFixed(2) }}s</span>
                    <span v-if="result.confidence_score" class="confidence">
                      置信度: {{ (result.confidence_score * 100).toFixed(1) }}%
                    </span>
                  </div>
                </div>
                <div class="result-actions">
                  <el-button 
                    v-if="result.status === 'success'" 
                    type="text" 
                    @click="toggleResultExpansion(result.file_name)"
                  >
                    {{ expandedResults[result.file_name] ? '收起' : '展开' }}
                  </el-button>
                </div>
              </div>
              
              <!-- 错误信息 -->
              <div v-if="result.status === 'failed' && result.error_message" class="error-section">
                <el-alert
                  :title="result.error_message"
                  type="error"
                  show-icon
                  :closable="false"
                />
              </div>
              
              <!-- 分析结果详情 -->
              <div v-if="result.status === 'success' && expandedResults[result.file_name]" class="analysis-details">
                
                <!-- 客户需求分析结果 -->
                <div v-if="result.business_insights?.customer_requirements" class="insights-section">
                  <h4>客户需求分析</h4>
                  <div class="insights-content">
                    <div v-if="result.business_insights.customer_requirements.technical_requirements" class="insight-group">
                      <strong>技术需求:</strong>
                      <p class="insight-text">{{ getInsightSummary(result.business_insights.customer_requirements.technical_requirements) }}</p>
                    </div>
                    <div v-if="result.business_insights.customer_requirements.business_requirements" class="insight-group">
                      <strong>商务需求:</strong>
                      <p class="insight-text">{{ getInsightSummary(result.business_insights.customer_requirements.business_requirements) }}</p>
                    </div>
                    <div v-if="result.business_insights.customer_requirements.risk_assessment" class="insight-group">
                      <strong>风险评估:</strong>
                      <el-tag :type="getRiskType(result.business_insights.customer_requirements.risk_assessment.overall_risk_level)">
                        {{ result.business_insights.customer_requirements.risk_assessment.overall_risk_level || '未评估' }}
                      </el-tag>
                    </div>
                  </div>
                </div>

                <!-- 竞品分析结果 -->
                <div v-if="result.business_insights?.competitor_analysis" class="insights-section">
                  <h4>竞品分析</h4>
                  <div class="insights-content">
                    <div v-if="result.business_insights.competitor_analysis.competitor_info" class="insight-group">
                      <strong>竞争对手信息:</strong>
                      <p class="insight-text">{{ getInsightSummary(result.business_insights.competitor_analysis.competitor_info) }}</p>
                    </div>
                    <div v-if="result.business_insights.competitor_analysis.pricing_analysis" class="insight-group">
                      <strong>价格分析:</strong>
                      <p class="insight-text">{{ getInsightSummary(result.business_insights.competitor_analysis.pricing_analysis) }}</p>
                    </div>
                  </div>
                </div>

                <!-- 项目洞察结果 -->
                <div v-if="result.business_insights?.project_insights" class="insights-section">
                  <h4>历史项目洞察</h4>
                  <div class="insights-content">
                    <div v-if="result.business_insights.project_insights.project_metadata" class="insight-group">
                      <strong>项目信息:</strong>
                      <p class="insight-text">{{ getInsightSummary(result.business_insights.project_insights.project_metadata) }}</p>
                    </div>
                    <div v-if="result.business_insights.project_insights.success_patterns" class="insight-group">
                      <strong>成功模式:</strong>
                      <p class="insight-text">{{ getInsightSummary(result.business_insights.project_insights.success_patterns) }}</p>
                    </div>
                  </div>
                </div>

                <!-- 产品信息提取结果 -->
                <div v-if="result.business_insights?.product_extraction" class="insights-section">
                  <h4>产品信息提取</h4>
                  <div class="insights-content">
                    <div v-if="result.business_insights.product_extraction.basic_info" class="insight-group">
                      <strong>基本信息:</strong>
                      <p class="insight-text">{{ getInsightSummary(result.business_insights.product_extraction.basic_info) }}</p>
                    </div>
                    <div v-if="result.business_insights.product_extraction.technical_specs" class="insight-group">
                      <strong>技术规格:</strong>
                      <p class="insight-text">{{ getInsightSummary(result.business_insights.product_extraction.technical_specs) }}</p>
                    </div>
                    <div v-if="result.business_insights.product_extraction.business_info" class="insight-group">
                      <strong>商务信息:</strong>
                      <p class="insight-text">{{ getInsightSummary(result.business_insights.product_extraction.business_info) }}</p>
                    </div>
                  </div>
                </div>

                <!-- 文档分类结果 -->
                <div v-if="result.business_insights?.document_classification" class="insights-section">
                  <h4>文档分类</h4>
                  <div class="insights-content">
                    <div v-if="result.business_insights.document_classification.document_type" class="insight-group">
                      <strong>文档类型:</strong>
                      <p class="insight-text">{{ getInsightSummary(result.business_insights.document_classification.document_type) }}</p>
                    </div>
                    <div v-if="result.business_insights.document_classification.business_classification" class="insight-group">
                      <strong>业务分类:</strong>
                      <p class="insight-text">{{ getInsightSummary(result.business_insights.document_classification.business_classification) }}</p>
                    </div>
                  </div>
                </div>

                <!-- 质量评估结果 -->
                <div v-if="result.business_insights?.quality_assessment" class="insights-section">
                  <h4>质量评估</h4>
                  <div class="insights-content">
                    <div v-if="result.business_insights.quality_assessment.overall_score" class="insight-group">
                      <strong>总体评分:</strong>
                      <el-rate :value="result.business_insights.quality_assessment.overall_score / 2" disabled show-score />
                    </div>
                    <div v-if="result.business_insights.quality_assessment.content_quality" class="insight-group">
                      <strong>内容质量:</strong>
                      <p class="insight-text">{{ getInsightSummary(result.business_insights.quality_assessment.content_quality) }}</p>
                    </div>
                  </div>
                </div>

                <!-- 综合分析结果 -->
                <div v-if="result.business_insights?.comprehensive_analysis" class="insights-section">
                  <h4>综合分析</h4>
                  <div class="insights-content">
                    <div v-if="result.business_insights.comprehensive_analysis.strategic_value" class="insight-group">
                      <strong>战略价值:</strong>
                      <p class="insight-text">{{ getInsightSummary(result.business_insights.comprehensive_analysis.strategic_value) }}</p>
                    </div>
                    <div v-if="result.business_insights.comprehensive_analysis.operational_analysis" class="insight-group">
                      <strong>操作分析:</strong>
                      <p class="insight-text">{{ getInsightSummary(result.business_insights.comprehensive_analysis.operational_analysis) }}</p>
                    </div>
                    <div v-if="result.business_insights.comprehensive_analysis.executive_summary" class="insight-group">
                      <strong>执行摘要:</strong>
                      <p class="insight-text">{{ result.business_insights.comprehensive_analysis.executive_summary }}</p>
                    </div>
                  </div>
                </div>
                
              </div>
            </el-card>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { ArrowDown } from '@element-plus/icons-vue'
import { showMessage } from '@/utils/message'
import type { BatchJobResult } from '@/types/batch-analysis'

interface Props {
  results: BatchJobResult[]
  analysisType?: string
}

const props = withDefaults(defineProps<Props>(), {
  results: () => [],
  analysisType: ''
})

// 响应式数据
const searchText = ref('')
const filterType = ref('')
const filterStatus = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const expandedResults = reactive<Record<string, boolean>>({})

// 计算属性
const totalFiles = computed(() => props.results.length)
const successfulFiles = computed(() => props.results.filter(r => r.status === 'success').length)
const failedFiles = computed(() => props.results.filter(r => r.status === 'failed').length)
const successRate = computed(() => {
  if (totalFiles.value === 0) return 0
  return Math.round((successfulFiles.value / totalFiles.value) * 100)
})

const filteredResults = computed(() => {
  let filtered = props.results
  
  // 搜索过滤
  if (searchText.value) {
    const searchLower = searchText.value.toLowerCase()
    filtered = filtered.filter(result => 
      result.file_name.toLowerCase().includes(searchLower)
    )
  }
  
  // 类型过滤
  if (filterType.value) {
    filtered = filtered.filter(result => {
      if (!result.business_insights) return false
      
      switch (filterType.value) {
        case 'customer_requirements':
          return !!result.business_insights.customer_requirements
        case 'competitor_analysis':
          return !!result.business_insights.competitor_analysis
        case 'project_mining':
          return !!result.business_insights.project_insights
        default:
          return true
      }
    })
  }
  
  // 状态过滤
  if (filterStatus.value) {
    filtered = filtered.filter(result => result.status === filterStatus.value)
  }
  
  return filtered
})

// 方法
const getStatusType = (status: string) => {
  switch (status) {
    case 'success': return 'success'
    case 'failed': return 'danger'
    case 'skipped': return 'warning'
    default: return 'info'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'success': return '成功'
    case 'failed': return '失败'
    case 'skipped': return '跳过'
    default: return status
  }
}

const formatFileSize = (size: number): string => {
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB'
  if (size < 1024 * 1024 * 1024) return (size / (1024 * 1024)).toFixed(1) + ' MB'
  return (size / (1024 * 1024 * 1024)).toFixed(1) + ' GB'
}

const toggleResultExpansion = (fileName: string) => {
  expandedResults[fileName] = !expandedResults[fileName]
}

const handleExport = (command: string) => {
  showMessage.info(`导出${command}功能开发中...`)
}

const getInsightSummary = (insightData: any): string => {
  if (!insightData) return '暂无数据'
  
  // 如果有summary字段，直接返回
  if (insightData.summary) {
    return insightData.summary
  }
  
  // 如果是对象，尝试提取关键信息
  if (typeof insightData === 'object') {
    const keyValuePairs = Object.entries(insightData)
      .filter(([key, value]) => value !== null && value !== undefined && key !== 'extracted_from_text')
      .slice(0, 3) // 只显示前3个字段
      .map(([key, value]) => `${key}: ${value}`)
    
    if (keyValuePairs.length > 0) {
      return keyValuePairs.join('; ')
    }
  }
  
  // 如果是字符串，直接返回（限制长度）
  if (typeof insightData === 'string') {
    return insightData.length > 200 ? insightData.substring(0, 200) + '...' : insightData
  }
  
  return '数据格式无法解析'
}

const getRiskType = (riskLevel: string): string => {
  switch (riskLevel?.toLowerCase()) {
    case 'low': return 'success'
    case 'medium': return 'warning'
    case 'high': return 'danger'
    default: return 'info'
  }
}
</script>

<style scoped>
.business-analysis-results {
  max-width: 1200px;
  margin: 0 auto;
}

.results-card {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  font-weight: 600;
  font-size: 18px;
  color: #303133;
}

.summary-section {
  margin-bottom: 20px;
}

.filter-section {
  margin-bottom: 20px;
}

.results-list {
  min-height: 400px;
}

.result-item {
  margin-bottom: 15px;
}

.result-card {
  border: 1px solid #e4e7ed;
  transition: all 0.3s;
}

.result-card:hover {
  border-color: #409eff;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.file-info {
  flex: 1;
}

.file-name {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.file-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: #909399;
}

.file-meta .el-tag {
  margin-right: 0;
}

.confidence {
  font-weight: 500;
  color: #67c23a;
}

.result-actions {
  flex-shrink: 0;
}

.error-section {
  margin-top: 15px;
}

.analysis-details {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
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

.insight-group {
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.insight-group:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.insight-text {
  margin: 4px 0 0 0;
  color: #606266;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .result-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .result-actions {
    margin-top: 10px;
    align-self: stretch;
  }
  
  .file-meta {
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .filter-section .el-row {
    flex-direction: column;
    gap: 15px;
  }
  
  .summary-section .el-col {
    margin-bottom: 15px;
  }
}
</style>