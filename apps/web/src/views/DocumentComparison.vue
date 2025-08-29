<template>
  <div class="document-comparison">
    <div class="page-header">
      <h1>多文档对比分析</h1>
      <p class="page-description">智能对比分析多个文档，识别相似性、差异性，并提供专业建议</p>
    </div>

    <el-tabs v-model="activeTab" class="comparison-tabs">
      <!-- 文档对比 -->
      <el-tab-pane label="开始对比" name="compare">
        <DocumentComparisonForm 
          @comparison-start="handleComparisonStart"
          @comparison-success="handleComparisonSuccess"
          @comparison-error="handleComparisonError"
        />
      </el-tab-pane>

      <!-- 对比结果 -->
      <el-tab-pane label="对比结果" name="results" :disabled="!currentComparison">
        <ComparisonResults
          v-if="currentComparison"
          :comparison-result="currentComparison"
          @export-result="handleExportResult"
          @save-analysis="handleSaveAnalysis"
        />
        <div v-else class="empty-results">
          <el-empty description="还没有对比结果">
            <el-button type="primary" @click="activeTab = 'compare'">开始对比</el-button>
          </el-empty>
        </div>
      </el-tab-pane>

      <!-- 对比历史 -->
      <el-tab-pane label="对比历史" name="history">
        <ComparisonHistory 
          @comparison-selected="handleHistorySelected"
          @comparison-deleted="handleComparisonDeleted"
        />
      </el-tab-pane>

      <!-- 对比统计 -->
      <el-tab-pane label="对比统计" name="metrics">
        <ComparisonMetrics />
      </el-tab-pane>
    </el-tabs>

    <!-- 实时进度对话框 -->
    <el-dialog
      v-model="showProgressDialog"
      title="文档对比分析中"
      width="600px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <ComparisonProgress
        v-if="comparisonProgress"
        :progress="comparisonProgress"
        @cancel-comparison="handleCancelComparison"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, provide } from 'vue'
import { ElNotification } from 'element-plus'
import { showMessage } from '@/utils/message'
import DocumentComparisonForm from '@/components/comparison/DocumentComparisonForm.vue'
import ComparisonResults from '@/components/comparison/ComparisonResults.vue'
import ComparisonHistory from '@/components/comparison/ComparisonHistory.vue'
import ComparisonMetrics from '@/components/comparison/ComparisonMetrics.vue'
import ComparisonProgress from '@/components/comparison/ComparisonProgress.vue'
import type { 
  DocumentComparisonResult,
  ComparisonRecord
} from '@/types/document-comparison'

const activeTab = ref('compare')
const showProgressDialog = ref(false)
const currentComparison = ref<DocumentComparisonResult | null>(null)

const comparisonProgress = ref<{
  current_step: string
  percentage: number
  estimated_remaining_time: number
} | null>(null)

// 提供全局状态管理
const refreshTrigger = ref(0)
provide('refreshTrigger', refreshTrigger)

const handleComparisonStart = () => {
  showProgressDialog.value = true
  comparisonProgress.value = {
    current_step: '准备分析...',
    percentage: 0,
    estimated_remaining_time: 0
  }
  
  showMessage.info('开始文档对比分析')
}

const handleComparisonSuccess = (result: DocumentComparisonResult) => {
  showProgressDialog.value = false
  currentComparison.value = result
  activeTab.value = 'results'
  
  ElNotification({
    title: '对比分析完成',
    message: `成功对比 ${result.documents_analyzed.length} 个文档`,
    type: 'success',
    duration: 5000
  })
  
  // 刷新历史记录
  refreshTrigger.value++
}

const handleComparisonError = (error: string) => {
  showProgressDialog.value = false
  comparisonProgress.value = null
  showMessage.error(`对比分析失败: ${error}`)
}

const handleExportResult = (format: string) => {
  showMessage.success(`开始导出${format.toUpperCase()}格式报告`)
}

const handleSaveAnalysis = () => {
  showMessage.success('分析结果已保存')
  refreshTrigger.value++
}

const handleHistorySelected = (record: ComparisonRecord) => {
  // 这里需要根据record ID获取详细结果
  showMessage.info(`正在加载对比记录: ${record.document_names.join(', ')}`)
  activeTab.value = 'results'
}

const handleComparisonDeleted = () => {
  showMessage.success('对比记录已删除')
  refreshTrigger.value++
}

const handleCancelComparison = () => {
  showMessage.warning('对比分析已取消')
  showProgressDialog.value = false
  comparisonProgress.value = null
}

onMounted(() => {
  showMessage.info('多文档对比分析系统已就绪')
})
</script>

<style scoped>
.document-comparison {
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

.comparison-tabs {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 20px;
}

.empty-results {
  text-align: center;
  padding: 60px 20px;
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
}

/* 响应式设计 */
@media (max-width: 768px) {
  .document-comparison {
    padding: 15px;
  }
  
  .page-header h1 {
    font-size: 24px;
  }
  
  .page-description {
    font-size: 14px;
  }
  
  .comparison-tabs {
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