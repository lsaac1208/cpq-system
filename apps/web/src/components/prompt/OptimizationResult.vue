<template>
  <div class="optimization-result">
    <div class="result-header">
      <div class="result-title">
        <h3>优化结果</h3>
        <el-tag :type="result.success ? 'success' : 'danger'" size="large">
          {{ result.success ? '优化成功' : '优化失败' }}
        </el-tag>
      </div>
      <div class="result-meta">
        <span>优化ID: {{ result.optimization_id }}</span>
        <span>改进评分: {{ result.improvement_score }}%</span>
        <span>处理时长: {{ result.metadata.analysis_duration }}s</span>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="result-tabs">
      <!-- 优化建议 -->
      <el-tab-pane label="优化建议" name="suggestions">
        <div class="suggestions-section">
          <div class="suggestions-header">
            <h4>AI生成的优化建议 ({{ result.suggestions.length }}条)</h4>
            <div class="suggestion-stats">
              <el-tag type="danger" size="small">
                高影响: {{ result.metadata.high_impact_suggestions }}条
              </el-tag>
            </div>
          </div>
          
          <div class="suggestions-list">
            <div 
              v-for="(suggestion, index) in result.suggestions" 
              :key="index"
              class="suggestion-card"
              :class="{ 'high-impact': suggestion.impact_score >= 8 }"
            >
              <div class="suggestion-header">
                <div class="suggestion-type">
                  <el-tag :type="getSuggestionTypeColor(suggestion.type)" size="small">
                    {{ suggestion.type }}
                  </el-tag>
                  <span class="impact-score">
                    影响力: {{ suggestion.impact_score }}/10
                  </span>
                </div>
                <div class="suggestion-toggle">
                  <el-switch
                    v-model="suggestion.selected"
                    @change="updateSelectedSuggestions"
                  />
                </div>
              </div>
              
              <div class="suggestion-content">
                <h5>{{ suggestion.title }}</h5>
                <p class="suggestion-description">{{ suggestion.description }}</p>
                
                <div class="suggestion-details">
                  <div class="detail-item">
                    <label>原始文本:</label>
                    <code class="code-block">{{ suggestion.original_text }}</code>
                  </div>
                  <div class="detail-item">
                    <label>建议修改:</label>
                    <code class="code-block improved">{{ suggestion.suggested_text }}</code>
                  </div>
                  <div class="detail-item">
                    <label>预期效果:</label>
                    <span class="expected-effect">{{ suggestion.expected_improvement }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 优化后的Prompt -->
      <el-tab-pane label="优化结果" name="optimized">
        <div class="optimized-section">
          <div class="prompt-comparison">
            <div class="prompt-block">
              <h4>原始Prompt</h4>
              <el-input
                v-model="originalPrompt"
                type="textarea"
                :rows="8"
                readonly
                class="prompt-textarea"
              />
            </div>
            
            <div class="prompt-arrow">
              <el-icon size="24"><Right /></el-icon>
            </div>
            
            <div class="prompt-block">
              <h4>优化后Prompt</h4>
              <el-input
                v-model="result.optimized_prompt"
                type="textarea"
                :rows="8"
                readonly
                class="prompt-textarea optimized"
              />
            </div>
          </div>
          
          <div class="improvement-summary">
            <el-card>
              <template #header>
                <h4>改进摘要</h4>
              </template>
              <div class="improvement-stats">
                <div class="stat-item">
                  <label>改进评分:</label>
                  <el-progress
                    :percentage="result.improvement_score"
                    :color="getScoreColor(result.improvement_score)"
                    :stroke-width="8"
                  />
                </div>
                <div class="stat-item">
                  <label>应用建议:</label>
                  <span>{{ selectedSuggestions.length }}/{{ result.suggestions.length }} 条</span>
                </div>
                <div class="stat-item">
                  <label>预期提升:</label>
                  <span>{{ calculateExpectedImprovement() }}%</span>
                </div>
              </div>
            </el-card>
          </div>
        </div>
      </el-tab-pane>

      <!-- 风险评估 -->
      <el-tab-pane label="风险评估" name="risk">
        <div class="risk-section">
          <div class="risk-overview">
            <el-card>
              <template #header>
                <h4>整体风险评估</h4>
              </template>
              <div class="risk-level">
                <el-tag 
                  :type="getRiskTypeColor(result.risk_assessment.overall_risk)" 
                  size="large"
                >
                  {{ getRiskText(result.risk_assessment.overall_risk) }}
                </el-tag>
                <p class="risk-description">
                  基于优化内容和历史数据，该优化的风险级别为{{ getRiskText(result.risk_assessment.overall_risk) }}
                </p>
              </div>
            </el-card>
          </div>
          
          <div class="risk-factors" v-if="result.risk_assessment.risk_factors.length > 0">
            <h4>风险因子</h4>
            <div 
              v-for="(factor, index) in result.risk_assessment.risk_factors" 
              :key="index"
              class="risk-factor-item"
            >
              <div class="factor-header">
                <el-tag :type="getRiskTypeColor(factor.level)" size="small">
                  {{ factor.category }}
                </el-tag>
                <span class="factor-score">{{ factor.score }}/10</span>
              </div>
              <p class="factor-description">{{ factor.description }}</p>
            </div>
          </div>
          
          <div class="mitigation-suggestions" v-if="result.risk_assessment.mitigation_suggestions.length > 0">
            <h4>风险缓解建议</h4>
            <ul class="mitigation-list">
              <li 
                v-for="(suggestion, index) in result.risk_assessment.mitigation_suggestions" 
                :key="index"
                class="mitigation-item"
              >
                {{ suggestion }}
              </li>
            </ul>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 操作按钮 -->
    <div class="result-actions">
      <el-button @click="$emit('close')">
        关闭
      </el-button>
      <el-button type="info" @click="saveAsTemplate">
        保存为模板
      </el-button>
      <el-button 
        type="primary" 
        @click="applySuggestions"
        :disabled="selectedSuggestions.length === 0"
      >
        应用选中建议 ({{ selectedSuggestions.length }})
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessageBox } from 'element-plus'
import { showMessage } from '@/utils/message'
import { Right } from '@element-plus/icons-vue'

const props = defineProps<{
  result: {
    success: boolean
    optimization_id: number
    suggestions: Array<{
      type: string
      title: string
      description: string
      original_text: string
      suggested_text: string
      expected_improvement: string
      impact_score: number
      selected?: boolean
    }>
    optimized_prompt: string
    improvement_score: number
    risk_assessment: {
      overall_risk: string
      risk_factors: Array<{
        category: string
        level: string
        score: number
        description: string
      }>
      mitigation_suggestions: string[]
    }
    metadata: {
      analysis_duration: number
      total_suggestions: number
      high_impact_suggestions: number
    }
  }
}>()

const emit = defineEmits(['apply-suggestions', 'save-template', 'close'])

const activeTab = ref('suggestions')
const originalPrompt = ref('请分析以下产品文档，提取产品的基本信息、技术规格、产品特性等关键信息。')

// 计算属性
const selectedSuggestions = computed(() => {
  return props.result.suggestions.filter(s => s.selected)
})

// 方法
const getSuggestionTypeColor = (type: string) => {
  const typeColors: Record<string, string> = {
    '清晰度': 'primary',
    '完整性': 'success',
    '具体化': 'warning',
    '结构化': 'info',
    '上下文': 'danger'
  }
  return typeColors[type] || 'info'
}

const getScoreColor = (score: number) => {
  if (score >= 80) return '#67C23A'
  if (score >= 60) return '#E6A23C'
  return '#F56C6C'
}

const getRiskTypeColor = (risk: string) => {
  const riskColors: Record<string, string> = {
    low: 'success',
    medium: 'warning',
    high: 'danger'
  }
  return riskColors[risk] || 'info'
}

const getRiskText = (risk: string) => {
  const riskTexts: Record<string, string> = {
    low: '低风险',
    medium: '中等风险',
    high: '高风险'
  }
  return riskTexts[risk] || risk
}

const calculateExpectedImprovement = () => {
  if (selectedSuggestions.value.length === 0) return 0
  const total = selectedSuggestions.value.reduce((sum, s) => sum + s.impact_score, 0)
  return Math.round(total / selectedSuggestions.value.length * 10)
}

const updateSelectedSuggestions = () => {
  // 触发重新计算
}

const applySuggestions = async () => {
  if (selectedSuggestions.value.length === 0) {
    showMessage.warning('请至少选择一条优化建议')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要应用选中的 ${selectedSuggestions.value.length} 条优化建议吗？`,
      '确认应用',
      {
        confirmButtonText: '应用',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    emit('apply-suggestions', props.result.optimized_prompt)
  } catch {
    // 用户取消
  }
}

const saveAsTemplate = async () => {
  try {
    await ElMessageBox.prompt(
      '请输入模板名称',
      '保存为模板',
      {
        confirmButtonText: '保存',
        cancelButtonText: '取消',
        inputPattern: /\S+/,
        inputErrorMessage: '模板名称不能为空'
      }
    )
    
    const template = {
      name: '基于优化结果的模板',
      content: props.result.optimized_prompt,
      type: 'optimized',
      description: `基于优化ID ${props.result.optimization_id} 生成的模板`
    }
    
    emit('save-template', template)
  } catch {
    // 用户取消
  }
}

onMounted(() => {
  // 默认选中高影响力的建议
  props.result.suggestions.forEach(suggestion => {
    if (suggestion.impact_score >= 8) {
      suggestion.selected = true
    }
  })
})
</script>

<style scoped>
.optimization-result {
  padding: 20px;
}

.result-header {
  margin-bottom: 24px;
}

.result-title {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}

.result-title h3 {
  margin: 0;
  color: #303133;
}

.result-meta {
  display: flex;
  gap: 24px;
  color: #909399;
  font-size: 14px;
}

.result-tabs {
  margin-bottom: 24px;
}

.suggestions-section {
  padding: 20px 0;
}

.suggestions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.suggestions-header h4 {
  margin: 0;
  color: #303133;
}

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.suggestion-card {
  border: 1px solid #EBEEF5;
  border-radius: 8px;
  padding: 16px;
  background-color: #FAFAFA;
  transition: all 0.2s;
}

.suggestion-card.high-impact {
  border-color: #F56C6C;
  background-color: #FEF0F0;
}

.suggestion-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.suggestion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.suggestion-type {
  display: flex;
  align-items: center;
  gap: 12px;
}

.impact-score {
  font-size: 12px;
  color: #909399;
}

.suggestion-content h5 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 16px;
}

.suggestion-description {
  color: #606266;
  margin-bottom: 12px;
  line-height: 1.6;
}

.suggestion-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.detail-item label {
  font-weight: 500;
  color: #606266;
  min-width: 80px;
  font-size: 14px;
}

.code-block {
  background-color: #F5F7FA;
  padding: 8px 12px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  flex: 1;
  border-left: 3px solid #E4E7ED;
}

.code-block.improved {
  background-color: #F0F9FF;
  border-left-color: #409EFF;
}

.expected-effect {
  color: #67C23A;
  font-weight: 500;
}

.optimized-section {
  padding: 20px 0;
}

.prompt-comparison {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 20px;
  margin-bottom: 24px;
}

.prompt-block h4 {
  margin: 0 0 12px 0;
  color: #303133;
}

.prompt-textarea {
  width: 100%;
}

.prompt-textarea.optimized :deep(.el-textarea__inner) {
  background-color: #F0F9FF;
  border-color: #409EFF;
}

.prompt-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #409EFF;
}

.improvement-summary {
  margin-top: 24px;
}

.improvement-stats {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-item label {
  font-weight: 500;
  color: #606266;
  min-width: 80px;
}

.risk-section {
  padding: 20px 0;
}

.risk-overview {
  margin-bottom: 24px;
}

.risk-level {
  text-align: center;
  padding: 20px;
}

.risk-description {
  color: #606266;
  margin: 12px 0 0 0;
  line-height: 1.6;
}

.risk-factors {
  margin-bottom: 24px;
}

.risk-factors h4 {
  margin: 0 0 16px 0;
  color: #303133;
}

.risk-factor-item {
  padding: 12px;
  background-color: #FAFAFA;
  border-radius: 4px;
  margin-bottom: 8px;
}

.factor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.factor-score {
  font-weight: 500;
  color: #606266;
}

.factor-description {
  color: #606266;
  margin: 0;
  line-height: 1.6;
}

.mitigation-suggestions h4 {
  margin: 0 0 16px 0;
  color: #303133;
}

.mitigation-list {
  margin: 0;
  padding-left: 20px;
}

.mitigation-item {
  color: #606266;
  line-height: 1.6;
  margin-bottom: 8px;
}

.result-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid #EBEEF5;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .prompt-comparison {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .prompt-arrow {
    transform: rotate(90deg);
  }
  
  .result-meta {
    flex-direction: column;
    gap: 8px;
  }
}
</style>