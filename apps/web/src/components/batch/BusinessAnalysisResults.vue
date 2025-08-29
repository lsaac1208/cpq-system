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
                <CustomerRequirementsView 
                  v-if="result.business_insights?.customer_requirements"
                  :data="result.business_insights.customer_requirements"
                />
                
                <!-- 竞品分析结果 -->
                <CompetitorAnalysisView 
                  v-if="result.business_insights?.competitor_analysis"
                  :data="result.business_insights.competitor_analysis"
                />
                
                <!-- 项目洞察结果 -->
                <ProjectInsightsView 
                  v-if="result.business_insights?.project_insights"
                  :data="result.business_insights.project_insights"
                />
                
              </div>
            </el-card>
          </div>
        </div>
        
        <!-- 分页 -->
        <div v-if="filteredResults.length > pageSize" class="pagination-section">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50]"
            :total="filteredResults.length"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { ArrowDown } from '@element-plus/icons-vue'
import { showMessage } from '@/utils/message'
import type { BatchJobResult, BusinessAnalysisResult } from '@/types/batch-analysis'
import CustomerRequirementsView from './CustomerRequirementsView.vue'
import CompetitorAnalysisView from './CompetitorAnalysisView.vue'
import ProjectInsightsView from './ProjectInsightsView.vue'

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

const paginatedResults = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredResults.value.slice(start, end)
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

const handleSizeChange = (val: number) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
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

.pagination-section {
  display: flex;
  justify-content: center;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
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