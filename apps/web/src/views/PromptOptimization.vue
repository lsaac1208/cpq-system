<template>
  <div class="prompt-optimization">
    <div class="page-header">
      <h1>Prompt优化管理</h1>
      <p class="page-description">基于历史数据优化AI提示词，提升分析准确性和用户满意度</p>
    </div>

    <el-tabs v-model="activeTab" class="optimization-tabs">
      <!-- Prompt优化 -->
      <el-tab-pane label="智能优化" name="optimize">
        <PromptOptimizer 
          @optimization-success="handleOptimizationSuccess"
          @optimization-error="handleOptimizationError"
        />
      </el-tab-pane>

      <!-- 模板管理 -->
      <el-tab-pane label="模板管理" name="templates">
        <PromptTemplateManager 
          @template-saved="handleTemplateSaved"
          @template-deleted="loadTemplates"
        />
      </el-tab-pane>

      <!-- 优化历史 -->
      <el-tab-pane label="优化历史" name="history">
        <OptimizationHistory 
          @record-selected="handleRecordSelected"
        />
      </el-tab-pane>

      <!-- 效果统计 -->
      <el-tab-pane label="效果统计" name="metrics">
        <OptimizationMetrics />
      </el-tab-pane>
    </el-tabs>

    <!-- 优化结果详情对话框 -->
    <el-dialog
      v-model="showResultDialog"
      title="优化结果详情"
      width="80%"
      :before-close="handleCloseDialog"
    >
      <OptimizationResult
        v-if="currentOptimizationResult"
        :result="currentOptimizationResult"
        @apply-suggestions="handleApplySuggestions"
        @save-template="handleSaveAsTemplate"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, provide } from 'vue'
import { ElNotification } from 'element-plus'
import { showMessage } from '@/utils/message'
import PromptOptimizer from '@/components/prompt/PromptOptimizer.vue'
import PromptTemplateManager from '@/components/prompt/PromptTemplateManager.vue'
import OptimizationHistory from '@/components/prompt/OptimizationHistory.vue'
import OptimizationMetrics from '@/components/prompt/OptimizationMetrics.vue'
import OptimizationResult from '@/components/prompt/OptimizationResult.vue'
import type { 
  PromptOptimizationResponse, 
  PromptTemplate, 
  OptimizationRecord 
} from '@/types/prompt-optimization'

const activeTab = ref('optimize')
const showResultDialog = ref(false)
const currentOptimizationResult = ref<PromptOptimizationResponse | null>(null)

// 提供全局状态管理
const refreshTrigger = ref(0)
provide('refreshTrigger', refreshTrigger)

const handleOptimizationSuccess = (result: PromptOptimizationResponse) => {
  currentOptimizationResult.value = result
  showResultDialog.value = true
  
  ElNotification({
    title: '优化完成',
    message: `成功生成 ${result.suggestions.length} 条优化建议`,
    type: 'success',
    duration: 4000
  })
  
  // 刷新历史记录
  refreshTrigger.value++
}

const handleOptimizationError = (error: string) => {
  showMessage.error(`优化失败: ${error}`)
}

const handleTemplateSaved = (template: PromptTemplate) => {
  showMessage.success(`模板 "${template.name}" 保存成功`)
  refreshTrigger.value++
}

const handleRecordSelected = (record: OptimizationRecord) => {
  // 构造优化结果对象用于显示
  currentOptimizationResult.value = {
    success: true,
    optimization_id: record.id,
    suggestions: [],
    optimized_prompt: record.optimized_prompt,
    improvement_score: record.improvement_score,
    risk_assessment: {
      overall_risk: 'low',
      risk_factors: [],
      mitigation_suggestions: []
    },
    metadata: {
      analysis_duration: 0,
      total_suggestions: record.suggestions_applied.length,
      high_impact_suggestions: 0
    }
  }
  showResultDialog.value = true
}

const handleApplySuggestions = (optimizedPrompt: string) => {
  showMessage.success('优化建议已应用')
  showResultDialog.value = false
  refreshTrigger.value++
}

const handleSaveAsTemplate = (template: Partial<PromptTemplate>) => {
  showMessage.success('已保存为模板')
  activeTab.value = 'templates'
  showResultDialog.value = false
  refreshTrigger.value++
}

const handleCloseDialog = () => {
  showResultDialog.value = false
  currentOptimizationResult.value = null
}

const loadTemplates = () => {
  refreshTrigger.value++
}

onMounted(() => {
  showMessage.info('Prompt优化系统已就绪，请选择功能开始使用')
})
</script>

<style scoped>
.prompt-optimization {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
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

.optimization-tabs {
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
  padding: 10px 20px 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .prompt-optimization {
    padding: 15px;
  }
  
  .page-header h1 {
    font-size: 24px;
  }
  
  .page-description {
    font-size: 14px;
  }
  
  .optimization-tabs {
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