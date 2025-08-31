<template>
  <div class="recent-analysis-results">
    <div v-if="results.length === 0" class="empty-state">
      <el-empty description="暂无分析结果">
        <el-button type="primary" @click="$emit('start-analysis')">开始分析</el-button>
      </el-empty>
    </div>
    
    <div v-else class="results-list">
      <div 
        v-for="(result, index) in results" 
        :key="index"
        class="result-item"
        @click="$emit('result-selected', result)"
      >
        <div class="result-header">
          <div class="result-title">
            <el-icon class="result-icon">
              <Document v-if="result.success" />
              <WarningFilled v-else />
            </el-icon>
            <span class="document-name">
              {{ result.document_info.filename }}
            </span>
          </div>
          <div class="result-status">
            <el-tag 
              :type="result.success ? 'success' : 'danger'" 
              size="small"
            >
              {{ result.success ? '成功' : '失败' }}
            </el-tag>
          </div>
        </div>
        
        <div v-if="result.success" class="result-content">
          <div class="result-summary">
            {{ result.summary }}
          </div>
          
          <div class="result-details">
            <div class="detail-item">
              <span class="detail-label">产品名称:</span>
              <span class="detail-value" :class="getValueClass(result.extracted_data?.basic_info?.name)">
                {{ getDisplayValue(result.extracted_data?.basic_info?.name, '产品名称待确认') }}
              </span>
            </div>
            <div class="detail-item">
              <span class="detail-label">产品代码:</span>
              <span class="detail-value" :class="getValueClass(result.extracted_data?.basic_info?.code)">
                {{ getDisplayValue(result.extracted_data?.basic_info?.code, '代码待确认') }}
              </span>
            </div>
            <div class="detail-item">
              <span class="detail-label">产品分类:</span>
              <span class="detail-value" :class="getValueClass(result.extracted_data?.basic_info?.category)">
                {{ getDisplayValue(result.extracted_data?.basic_info?.category, '分类待确认') }}
              </span>
            </div>
          </div>
          
          <div class="result-metrics">
            <div class="metric-item">
              <span class="metric-label">整体置信度:</span>
              <el-progress 
                :percentage="Math.round((result.confidence_scores?.overall || 0) * 100)"
                :color="getConfidenceColor(result.confidence_scores?.overall || 0)"
                :stroke-width="6"
                :show-text="false"
                style="width: 80px"
              />
              <span class="metric-value">
                {{ Math.round((result.confidence_scores?.overall || 0) * 100) }}%
              </span>
            </div>
            
            <div class="metric-item">
              <span class="metric-label">完整性:</span>
              <el-progress 
                :percentage="Math.round((result.validation?.completeness_score || 0) * 100)"
                :color="getCompletenessColor(result.validation?.completeness_score || 0)"
                :stroke-width="6"
                :show-text="false"
                style="width: 80px"
              />
              <span class="metric-value">
                {{ Math.round((result.validation?.completeness_score || 0) * 100) }}%
              </span>
            </div>
          </div>
          
          <div class="result-features">
            <div class="feature-count">
              <el-icon><Menu /></el-icon>
              <span>规格 {{ Object.keys(result.extracted_data?.specifications || {}).length }} 项</span>
            </div>
            <div class="feature-count">
              <el-icon><Star /></el-icon>
              <span>特性 {{ result.extracted_data?.features?.length || 0 }} 项</span>
            </div>
            <div class="feature-count">
              <el-icon><Trophy /></el-icon>
              <span>认证 {{ result.extracted_data?.certificates?.length || 0 }} 项</span>
            </div>
          </div>
        </div>
        
        <div v-else class="result-error">
          <el-alert
            :title="result.error || '分析失败'"
            type="error"
            :closable="false"
            show-icon
          />
        </div>
        
        <div class="result-footer">
          <div class="result-meta">
            <span class="meta-item">
              <el-icon><Timer /></el-icon>
              {{ formatTime(result.analysis_timestamp) }}
            </span>
            <span class="meta-item">
              <el-icon><Document /></el-icon>
              {{ formatFileSize(result.document_info.size) }}
            </span>
            <span v-if="result.document_info.analysis_duration" class="meta-item">
              <el-icon><Stopwatch /></el-icon>
              {{ result.document_info.analysis_duration }}s
            </span>
          </div>
          
          <div class="result-actions">
            <el-button 
              v-if="result.success"
              type="primary" 
              size="small" 
              text
              @click.stop="viewDetails(result)"
            >
              查看详情
            </el-button>
            <el-button 
              v-if="result.success"
              type="success" 
              size="small" 
              text
              @click.stop="createProduct(result)"
            >
              创建产品
            </el-button>
            <el-button 
              type="info" 
              size="small" 
              text
              @click.stop="exportResult(result)"
            >
              导出结果
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { showMessage } from '@/utils/message'
import { 
  Document, 
  WarningFilled, 
  Star, 
  Trophy, 
  Timer, 
  Stopwatch,
  Menu
} from '@element-plus/icons-vue'
import type { AIAnalysisResult } from '@/types/ai-analysis'

// 组件属性
interface Props {
  results: AIAnalysisResult[]
}

defineProps<Props>()

// 组件事件
const emit = defineEmits<{
  'result-selected': [result: AIAnalysisResult]
  'start-analysis': []
}>()

// 方法
const getConfidenceColor = (confidence: number): string => {
  if (confidence >= 0.8) return '#67c23a'
  if (confidence >= 0.6) return '#e6a23c'
  return '#f56c6c'
}

const getCompletenessColor = (completeness: number): string => {
  if (completeness >= 0.9) return '#67c23a'
  if (completeness >= 0.7) return '#e6a23c'
  return '#f56c6c'
}

const formatTime = (timestamp: number): string => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  
  return date.toLocaleDateString('zh-CN')
}

const formatFileSize = (size: number): string => {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

const viewDetails = (result: AIAnalysisResult) => {
  emit('result-selected', result)
}

const createProduct = (result: AIAnalysisResult) => {
  showMessage.info('跳转到产品创建页面...')
}

const exportResult = (result: AIAnalysisResult) => {
  const dataStr = JSON.stringify(result, null, 2)
  const dataBlob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(dataBlob)
  
  const link = document.createElement('a')
  link.href = url
  link.download = `analysis-${result.document_info.filename}-${Date.now()}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  URL.revokeObjectURL(url)
  showMessage.success('分析结果已导出')
}

// 智能显示值方法 - 根据内容质量动态显示
const getDisplayValue = (value: any, fallback: string = '待确认'): string => {
  // 如果值为空或无效
  if (!value || (typeof value === 'string' && !value.trim())) {
    return fallback
  }
  
  // 字符串值处理
  if (typeof value === 'string') {
    const trimmed = value.trim()
    
    // 过滤明显的无效值
    const invalidValues = ['未识别', '未知', 'unknown', 'N/A', 'null', 'undefined', '待定', '无']
    if (invalidValues.some(invalid => trimmed.toLowerCase().includes(invalid.toLowerCase()))) {
      return fallback
    }
    
    // 检查是否为有效的技术信息
    if (trimmed.length < 2) {
      return fallback
    }
    
    return trimmed
  }
  
  // 数字值处理
  if (typeof value === 'number') {
    return value.toString()
  }
  
  // 对象/数组等复杂类型
  if (typeof value === 'object') {
    if (Array.isArray(value)) {
      return value.length > 0 ? `${value.length}项` : fallback
    }
    if (value.value !== undefined) {
      return getDisplayValue(value.value, fallback)
    }
  }
  
  return String(value) || fallback
}

// 智能样式类方法 - 根据内容质量设置样式
const getValueClass = (value: any): string => {
  const displayValue = getDisplayValue(value, '')
  
  // 如果显示为fallback值，使用警告样式
  if (!value || displayValue.includes('待确认') || displayValue.includes('待定')) {
    return 'value-pending'
  }
  
  // 如果是有效值，使用正常样式
  if (typeof value === 'string' && value.trim().length >= 2) {
    return 'value-valid'
  }
  
  // 如果是数字且大于0
  if (typeof value === 'number' && value > 0) {
    return 'value-valid'
  }
  
  // 默认样式
  return 'value-normal'
}
</script>

<style scoped>
.recent-analysis-results {
  min-height: 200px;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.result-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 15px;
  cursor: pointer;
  transition: all 0.3s;
  background: #fff;
}

.result-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.result-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.result-icon {
  font-size: 18px;
  color: #409eff;
}

.document-name {
  font-weight: 500;
  color: #303133;
  font-size: 15px;
}

.result-content {
  margin-bottom: 15px;
}

.result-summary {
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 10px;
}

.result-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 8px;
  margin-bottom: 10px;
}

.detail-item {
  font-size: 13px;
}

.detail-label {
  color: #909399;
  margin-right: 5px;
}

.detail-value {
  color: #303133;
  font-weight: 500;
}

/* 智能值显示样式 */
.detail-value.value-valid {
  color: #67c23a;
  font-weight: 600;
}

.detail-value.value-pending {
  color: #e6a23c;
  font-style: italic;
}

.detail-value.value-normal {
  color: #606266;
  font-weight: 400;
}

.result-metrics {
  display: flex;
  gap: 20px;
  margin-bottom: 10px;
}

.metric-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.metric-label {
  color: #909399;
  min-width: 60px;
}

.metric-value {
  color: #303133;
  font-weight: 500;
  min-width: 35px;
}

.result-features {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.feature-count {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #606266;
}

.feature-count .el-icon {
  font-size: 14px;
  color: #909399;
}

.result-error {
  margin-bottom: 15px;
}

.result-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 10px;
  border-top: 1px solid #f0f0f0;
}

.result-meta {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
}

.meta-item .el-icon {
  font-size: 13px;
}

.result-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .result-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .result-details {
    grid-template-columns: 1fr;
  }
  
  .result-metrics {
    flex-direction: column;
    gap: 8px;
  }
  
  .result-features {
    flex-direction: column;
    gap: 8px;
  }
  
  .result-footer {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .result-meta {
    flex-direction: column;
    gap: 5px;
  }
  
  .result-actions {
    align-self: stretch;
    justify-content: center;
  }
}
</style>