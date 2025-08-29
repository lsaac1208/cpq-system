<template>
  <div class="comparison-results">
    <!-- 头部信息 -->
    <el-card class="header-card">
      <template #header>
        <div class="header-actions">
          <el-button @click="$emit('back')" link size="large">
            <el-icon><ArrowLeft /></el-icon>
            返回
          </el-button>
          <div class="header-title">
            <h2>{{ comparison?.name || '文档对比分析结果' }}</h2>
            <div class="header-meta">
              <el-tag :type="getStatusType(comparison?.status)">
                {{ getStatusText(comparison?.status) }}
              </el-tag>
              <span class="meta-item">
                创建时间: {{ formatTime(comparison?.created_at) }}
              </span>
              <span class="meta-item" v-if="comparison?.processing_duration">
                处理耗时: {{ formatDuration(comparison.processing_duration) }}
              </span>
            </div>
          </div>
          <div class="header-actions-right">
            <el-button @click="refreshResults" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button @click="exportResults" type="primary">
              <el-icon><Download /></el-icon>
              导出结果
            </el-button>
          </div>
        </div>
      </template>
      
      <!-- 对比概要 -->
      <div v-if="results" class="comparison-summary">
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-value">{{ results.summary?.total_differences || 0 }}</div>
              <div class="summary-label">总差异数</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-value significant">
                {{ results.summary?.significant_differences || 0 }}
              </div>
              <div class="summary-label">重要差异</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-value">{{ results.summary?.similarities_count || 0 }}</div>
              <div class="summary-label">相似项</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-value">{{ results.summary?.insights_count || 0 }}</div>
              <div class="summary-label">智能洞察</div>
            </div>
          </el-col>
        </el-row>
      </div>
      
      <!-- 参与对比的文档 -->
      <div v-if="results?.documents" class="documents-info">
        <h4>参与对比的文档 ({{ results.documents.length }})</h4>
        <div class="documents-list">
          <div 
            v-for="doc in results.documents" 
            :key="doc.analysis_record_id"
            class="document-card"
            :class="{ 'primary-document': doc.document_role === 'primary' }"
          >
            <div class="doc-icon">
              <el-icon>
                <Document v-if="doc.file_type === 'txt'" />
                <Picture v-else-if="['jpg', 'jpeg', 'png'].includes(doc.file_type)" />
                <Files v-else />
              </el-icon>
            </div>
            <div class="doc-info">
              <div class="doc-name">{{ doc.document_label }}</div>
              <div class="doc-filename">{{ doc.filename }}</div>
              <div class="doc-role">
                <el-tag size="small" :type="getRoleType(doc.document_role)">
                  {{ getRoleText(doc.document_role) }}
                </el-tag>
                <span class="doc-weight">权重: {{ doc.comparison_weight }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>
    
    <!-- 处理中状态 -->
    <div v-if="comparison?.status === 'processing'" class="processing-status">
      <el-card>
        <div class="processing-content">
          <el-icon class="processing-icon"><Loading /></el-icon>
          <h3>正在进行对比分析...</h3>
          <p>AI正在深度分析文档内容，识别差异和相似性，请耐心等待</p>
          <el-progress :percentage="processingProgress" :show-text="false" />
        </div>
      </el-card>
    </div>
    
    <!-- 分析结果 -->
    <div v-else-if="results?.results" class="results-content">
      <el-tabs v-model="activeTab" type="card">
        <!-- 差异分析 -->
        <el-tab-pane 
          label="差异分析" 
          name="differences"
          :disabled="!results.results.differences?.length"
        >
          <template #label>
            差异分析 
            <el-badge 
              :value="results.results.differences?.length || 0" 
              :max="99"
              class="tab-badge"
            />
          </template>
          
          <DifferencesAnalysis 
            v-if="results.results.differences" 
            :differences="results.results.differences"
            :documents="results.documents"
          />
        </el-tab-pane>
        
        <!-- 相似性分析 -->
        <el-tab-pane 
          label="相似性分析" 
          name="similarities"
          :disabled="!results.results.similarities?.length"
        >
          <template #label>
            相似性分析 
            <el-badge 
              :value="results.results.similarities?.length || 0" 
              :max="99"
              class="tab-badge"
            />
          </template>
          
          <SimilaritiesAnalysis 
            v-if="results.results.similarities" 
            :similarities="results.results.similarities"
            :documents="results.documents"
          />
        </el-tab-pane>
        
        <!-- 智能洞察 -->
        <el-tab-pane 
          label="智能洞察" 
          name="insights"
          :disabled="!results.results.insights?.length"
        >
          <template #label>
            智能洞察 
            <el-badge 
              :value="results.results.insights?.length || 0" 
              :max="99"
              class="tab-badge"
            />
          </template>
          
          <InsightsAnalysis 
            v-if="results.results.insights" 
            :insights="results.results.insights"
          />
        </el-tab-pane>
        
        <!-- 对比矩阵 -->
        <el-tab-pane label="对比矩阵" name="matrix">
          <ComparisonMatrix 
            v-if="results" 
            :results="results"
          />
        </el-tab-pane>
      </el-tabs>
    </div>
    
    <!-- 错误状态 -->
    <div v-else-if="comparison?.status === 'failed'" class="error-status">
      <el-card>
        <el-result
          icon="error"
          title="分析失败"
          :sub-title="comparison?.error_message || '对比分析过程中发生错误'"
        >
          <template #extra>
            <el-button type="primary" @click="retryAnalysis">重试分析</el-button>
            <el-button @click="$emit('back')">返回</el-button>
          </template>
        </el-result>
      </el-card>
    </div>
    
    <!-- 空状态 -->
    <div v-else class="empty-status">
      <el-card>
        <el-empty description="暂无对比结果">
          <el-button type="primary" @click="refreshResults">刷新结果</el-button>
        </el-empty>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElNotification } from 'element-plus'
import { showMessage } from '@/utils/message'
import {
  ArrowLeft, Refresh, Download, Loading, Document, Picture, Files
} from '@element-plus/icons-vue'
import DifferencesAnalysis from './analysis/DifferencesAnalysis.vue'
import SimilaritiesAnalysis from './analysis/SimilaritiesAnalysis.vue'
import InsightsAnalysis from './analysis/InsightsAnalysis.vue'
import ComparisonMatrix from './analysis/ComparisonMatrix.vue'

// Props
const props = defineProps<{
  comparison: {
    comparison_id: string
    name?: string
    status?: string
    created_at?: string
    processing_duration?: number
    error_message?: string
  }
}>()

// Emits
const emit = defineEmits<{
  back: []
  refresh: []
}>()

// Reactive data
const loading = ref(false)
const results = ref(null)
const activeTab = ref('differences')
const processingProgress = ref(0)

// Auto refresh timer for processing status
let refreshTimer: number | null = null

// Computed
const comparison = computed(() => props.comparison)

// Methods
const refreshResults = async () => {
  if (!comparison.value?.comparison_id) return
  
  loading.value = true
  
  try {
    // 获取状态
    const statusResponse = await fetch(
      `/api/v1/document-comparison/${comparison.value.comparison_id}/status`,
      {
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`
        }
      }
    )
    
    const statusResult = await statusResponse.json()
    
    if (statusResult.success) {
      // 更新comparison状态
      Object.assign(comparison.value, statusResult.status)
      
      // 如果已完成，获取结果
      if (statusResult.status.status === 'completed') {
        const resultsResponse = await fetch(
          `/api/v1/document-comparison/${comparison.value.comparison_id}/results`,
          {
            headers: {
              'Authorization': `Bearer ${getAuthToken()}`
            }
          }
        )
        
        const resultsResult = await resultsResponse.json()
        
        if (resultsResult.success) {
          results.value = resultsResult.results
        }
      }
    }
    
  } catch (error: any) {
    showMessage.error(`刷新结果失败: ${error.message}`)
  } finally {
    loading.value = false
  }
}

const exportResults = async () => {
  if (!comparison.value?.comparison_id || !results.value) {
    showMessage.warning('暂无可导出的结果')
    return
  }
  
  try {
    const response = await fetch(
      `/api/v1/document-comparison/${comparison.value.comparison_id}/export`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAuthToken()}`
        },
        body: JSON.stringify({
          format: 'json'
        })
      }
    )
    
    const result = await response.json()
    
    if (result.success) {
      // 创建下载链接
      const blob = new Blob([JSON.stringify(result.export_data, null, 2)], {
        type: 'application/json'
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = result.filename
      a.click()
      URL.revokeObjectURL(url)
      
      showMessage.success('结果已导出')
    } else {
      throw new Error(result.error || '导出失败')
    }
    
  } catch (error: any) {
    showMessage.error(`导出失败: ${error.message}`)
  }
}

const retryAnalysis = async () => {
  if (!comparison.value?.comparison_id) return
  
  try {
    const response = await fetch(
      `/api/v1/document-comparison/${comparison.value.comparison_id}/start`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`
        }
      }
    )
    
    const result = await response.json()
    
    if (result.success) {
      showMessage.success('已重新启动分析')
      comparison.value.status = 'processing'
      startAutoRefresh()
    } else {
      throw new Error(result.error || '重试失败')
    }
    
  } catch (error: any) {
    showMessage.error(`重试失败: ${error.message}`)
  }
}

const startAutoRefresh = () => {
  if (refreshTimer) return
  
  refreshTimer = window.setInterval(() => {
    if (comparison.value?.status === 'processing') {
      refreshResults()
      processingProgress.value = Math.min(processingProgress.value + 5, 95)
    } else {
      stopAutoRefresh()
    }
  }, 5000) // 5秒刷新一次
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
    'processing': '分析中',
    'completed': '已完成',
    'failed': '失败',
    'cancelled': '已取消'
  }
  return texts[status] || status
}

const getRoleType = (role: string) => {
  const types: Record<string, string> = {
    'primary': 'success',
    'secondary': '',
    'reference': 'info'
  }
  return types[role] || ''
}

const getRoleText = (role: string) => {
  const texts: Record<string, string> = {
    'primary': '主要文档',
    'secondary': '对比文档',
    'reference': '参考文档'
  }
  return texts[role] || role
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

// Watch for comparison changes
watch(() => comparison.value?.comparison_id, (newId) => {
  if (newId) {
    refreshResults()
    if (comparison.value?.status === 'processing') {
      startAutoRefresh()
    }
  }
}, { immediate: true })

// Lifecycle
onMounted(() => {
  if (comparison.value?.comparison_id) {
    refreshResults()
    if (comparison.value.status === 'processing') {
      startAutoRefresh()
    }
  }
})

// Cleanup on unmount
const cleanup = () => {
  stopAutoRefresh()
}

// Make sure to cleanup when component is destroyed
onBeforeUnmount(() => {
  cleanup()
})
</script>

<style scoped>
.comparison-results {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.header-actions {
  display: flex;
  align-items: flex-start;
  gap: 20px;
}

.header-title {
  flex: 1;
}

.header-title h2 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 20px;
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 14px;
  color: #606266;
}

.meta-item {
  display: flex;
  align-items: center;
}

.header-actions-right {
  display: flex;
  gap: 12px;
}

.comparison-summary {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #ebeef5;
}

.summary-item {
  text-align: center;
  padding: 20px;
  border-radius: 8px;
  background: #f8f9fa;
  border: 1px solid #ebeef5;
}

.summary-value {
  font-size: 32px;
  font-weight: 600;
  color: #409eff;
  margin-bottom: 8px;
}

.summary-value.significant {
  color: #e6a23c;
}

.summary-label {
  font-size: 14px;
  color: #606266;
}

.documents-info {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #ebeef5;
}

.documents-info h4 {
  margin: 0 0 16px 0;
  color: #303133;
}

.documents-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.document-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  background: #fafafa;
  transition: all 0.3s ease;
}

.document-card:hover {
  border-color: #c6e2ff;
  background: #ecf5ff;
}

.document-card.primary-document {
  border-color: #409eff;
  background: #f0f9ff;
}

.doc-icon {
  font-size: 32px;
  color: #909399;
}

.doc-info {
  flex: 1;
}

.doc-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.doc-filename {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.doc-role {
  display: flex;
  align-items: center;
  gap: 8px;
}

.doc-weight {
  font-size: 12px;
  color: #909399;
}

.processing-status, .error-status, .empty-status {
  margin-top: 20px;
}

.processing-content {
  text-align: center;
  padding: 40px 20px;
}

.processing-icon {
  font-size: 48px;
  color: #409eff;
  margin-bottom: 16px;
  animation: spin 2s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.processing-content h3 {
  margin: 0 0 8px 0;
  color: #303133;
}

.processing-content p {
  margin: 0 0 24px 0;
  color: #606266;
}

.results-content {
  margin-top: 20px;
}

.tab-badge {
  margin-left: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .comparison-results {
    padding: 16px;
  }
  
  .header-actions {
    flex-direction: column;
    gap: 16px;
  }
  
  .header-actions-right {
    align-self: stretch;
  }
  
  .header-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .documents-list {
    grid-template-columns: 1fr;
  }
  
  .comparison-summary .el-row {
    flex-direction: column;
  }
  
  .comparison-summary .el-col {
    width: 100% !important;
    margin-bottom: 16px;
  }
}
</style>