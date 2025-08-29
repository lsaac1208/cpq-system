<template>
  <div class="document-comparison">
    <!-- 创建对比分析 -->
    <el-card v-if="!selectedComparison" class="create-comparison-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon><Connection /></el-icon>
            创建文档对比分析
          </span>
        </div>
      </template>
      
      <el-form 
        ref="comparisonFormRef"
        :model="comparisonForm" 
        :rules="comparisonRules" 
        label-width="120px"
      >
        <el-form-item label="对比名称" prop="name">
          <el-input 
            v-model="comparisonForm.name" 
            placeholder="输入对比分析名称"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="对比描述">
          <el-input 
            v-model="comparisonForm.description"
            type="textarea"
            :rows="3"
            placeholder="输入对比分析描述（可选）"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="对比类型" prop="comparison_type">
          <el-select v-model="comparisonForm.config.comparison_type" placeholder="选择对比类型">
            <el-option label="产品规格对比" value="product_specs" />
            <el-option label="价格分析对比" value="price_analysis" />
            <el-option label="功能特性矩阵" value="feature_matrix" />
            <el-option label="竞品分析" value="competitive_analysis" />
            <el-option label="自定义对比" value="custom" />
          </el-select>
        </el-form-item>
        
        <!-- 文档选择 -->
        <el-form-item label="选择文档" prop="documents" class="documents-form-item">
          <div class="documents-selection">
            <div class="documents-header">
              <span>已选择 {{ comparisonForm.documents.length }} 个文档 (至少需要2个)</span>
              <el-button @click="showDocumentSelector = true" type="primary" size="small">
                <el-icon><Plus /></el-icon>
                添加文档
              </el-button>
            </div>
            
            <div v-if="comparisonForm.documents.length > 0" class="selected-documents">
              <div 
                v-for="(doc, index) in comparisonForm.documents" 
                :key="doc.analysis_record_id"
                class="document-item"
                :class="{ 'primary-doc': doc.role === 'primary' }"
              >
                <div class="doc-info">
                  <div class="doc-header">
                    <el-icon class="doc-icon">
                      <Document v-if="doc.file_type === 'txt'" />
                      <Picture v-else-if="['jpg', 'jpeg', 'png'].includes(doc.file_type)" />
                      <Files v-else />
                    </el-icon>
                    <div class="doc-details">
                      <div class="doc-filename">{{ doc.filename }}</div>
                      <div class="doc-meta">
                        ID: {{ doc.analysis_record_id }} • 
                        {{ formatFileType(doc.file_type) }} •
                        {{ formatTime(doc.upload_time) }}
                      </div>
                    </div>
                  </div>
                  
                  <div class="doc-config">
                    <el-input 
                      v-model="doc.label" 
                      placeholder="文档标签" 
                      size="small"
                      style="width: 150px; margin-right: 10px;"
                    />
                    <el-select 
                      v-model="doc.role" 
                      placeholder="角色" 
                      size="small"
                      style="width: 100px; margin-right: 10px;"
                    >
                      <el-option label="主要" value="primary" />
                      <el-option label="次要" value="secondary" />
                      <el-option label="参考" value="reference" />
                    </el-select>
                    <el-input-number
                      v-model="doc.weight"
                      :min="0.1"
                      :max="10"
                      :step="0.1"
                      size="small"
                      style="width: 100px; margin-right: 10px;"
                      placeholder="权重"
                    />
                  </div>
                </div>
                
                <div class="doc-actions">
                  <el-button 
                    @click="removeDocument(index)"
                    type="danger"
                    size="small"
                    text
                  >
                    <el-icon><Delete /></el-icon>
                    移除
                  </el-button>
                </div>
              </div>
            </div>
            
            <el-empty v-else description="请添加要对比的文档" />
          </div>
        </el-form-item>
        
        <!-- 高级设置 -->
        <el-form-item>
          <el-collapse v-model="activeCollapse">
            <el-collapse-item title="高级设置" name="advanced">
              <div class="advanced-settings">
                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item label="关注领域">
                      <el-select
                        v-model="comparisonForm.config.focus_areas"
                        multiple
                        filterable
                        allow-create
                        placeholder="选择或输入关注的对比领域"
                        style="width: 100%"
                      >
                        <el-option label="价格" value="价格" />
                        <el-option label="规格" value="规格" />
                        <el-option label="功能" value="功能" />
                        <el-option label="性能" value="性能" />
                        <el-option label="尺寸" value="尺寸" />
                        <el-option label="重量" value="重量" />
                        <el-option label="材质" value="材质" />
                        <el-option label="颜色" value="颜色" />
                        <el-option label="品牌" value="品牌" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                  
                  <el-col :span="12">
                    <el-form-item label="置信度阈值">
                      <el-slider
                        v-model="comparisonForm.config.min_confidence_threshold"
                        :min="0"
                        :max="1"
                        :step="0.1"
                        :format-tooltip="formatConfidence"
                        show-stops
                      />
                    </el-form-item>
                  </el-col>
                </el-row>
                
                <el-row :gutter="20">
                  <el-col :span="8">
                    <el-checkbox v-model="comparisonForm.config.include_similarities">
                      包含相似性分析
                    </el-checkbox>
                  </el-col>
                  <el-col :span="8">
                    <el-checkbox v-model="comparisonForm.config.include_differences">
                      包含差异分析
                    </el-checkbox>
                  </el-col>
                  <el-col :span="8">
                    <el-checkbox v-model="comparisonForm.config.enable_insights">
                      生成智能洞察
                    </el-checkbox>
                  </el-col>
                </el-row>
                
                <el-form-item label="重要性阈值">
                  <el-slider
                    v-model="comparisonForm.config.importance_threshold"
                    :min="0"
                    :max="1"
                    :step="0.1"
                    :format-tooltip="formatImportance"
                    show-stops
                  />
                  <span class="help-text">低于此分数的结果将被标记为不重要</span>
                </el-form-item>
              </div>
            </el-collapse-item>
          </el-collapse>
        </el-form-item>
        
        <el-form-item class="form-actions">
          <el-button 
            type="primary" 
            @click="createComparison"
            :loading="creating"
            :disabled="comparisonForm.documents.length < 2"
          >
            <el-icon><MagicStick /></el-icon>
            开始对比分析
          </el-button>
          <el-button @click="resetForm">重置</el-button>
          <el-button @click="showComparisonList = true">查看历史</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 对比结果展示 -->
    <div v-if="selectedComparison" class="comparison-results">
      <ComparisonResults 
        :comparison="selectedComparison"
        @back="selectedComparison = null"
        @refresh="refreshComparison"
      />
    </div>
    
    <!-- 文档选择器弹窗 -->
    <DocumentSelector
      v-if="showDocumentSelector"
      @close="showDocumentSelector = false"
      @select="addDocuments"
    />
    
    <!-- 对比历史列表弹窗 -->
    <ComparisonHistoryDialog
      v-if="showComparisonList"
      @close="showComparisonList = false"
      @select="selectComparison"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessageBox, ElNotification } from 'element-plus'
import { showMessage } from '@/utils/message'
import { Plus, Document, Picture, Files, Delete, MagicStick
} from '@element-plus/icons-vue'
import ComparisonResults from './ComparisonResults.vue'
import DocumentSelector from './DocumentSelector.vue'
import ComparisonHistoryDialog from './ComparisonHistoryDialog.vue'

// Types
interface DocumentInfo {
  analysis_record_id: number
  label: string
  filename: string
  file_type: string
  upload_time: string
  role: 'primary' | 'secondary' | 'reference'
  weight: number
}

interface ComparisonConfig {
  comparison_type: string
  focus_areas: string[]
  include_similarities: boolean
  include_differences: boolean
  min_confidence_threshold: number
  importance_threshold: number
  max_results_per_category: number
  enable_insights: boolean
  custom_fields: string[]
}

interface ComparisonForm {
  name: string
  description: string
  documents: DocumentInfo[]
  config: ComparisonConfig
}

// Reactive data
const comparisonFormRef = ref()
const creating = ref(false)
const selectedComparison = ref(null)
const showDocumentSelector = ref(false)
const showComparisonList = ref(false)
const activeCollapse = ref([])

const comparisonForm = reactive<ComparisonForm>({
  name: '',
  description: '',
  documents: [],
  config: {
    comparison_type: 'product_specs',
    focus_areas: [],
    include_similarities: true,
    include_differences: true,
    min_confidence_threshold: 0.6,
    importance_threshold: 0.5,
    max_results_per_category: 50,
    enable_insights: true,
    custom_fields: []
  }
})

// Form validation rules
const comparisonRules = {
  name: [
    { required: true, message: '请输入对比名称', trigger: 'blur' },
    { min: 1, max: 200, message: '长度在 1 到 200 个字符', trigger: 'blur' }
  ],
  comparison_type: [
    { required: true, message: '请选择对比类型', trigger: 'change' }
  ],
  documents: [
    {
      validator: (rule: any, value: any, callback: any) => {
        if (comparisonForm.documents.length < 2) {
          callback(new Error('至少需要选择2个文档进行对比'))
        } else if (comparisonForm.documents.length > 10) {
          callback(new Error('最多可以对比10个文档'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ]
}

// Methods
const createComparison = async () => {
  try {
    await comparisonFormRef.value?.validate()
    
    creating.value = true
    
    const response = await fetch('/api/v1/document-comparison/create', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`
      },
      body: JSON.stringify(comparisonForm)
    })
    
    const result = await response.json()
    
    if (result.success) {
      ElNotification({
        title: '对比分析已创建',
        message: `对比分析 "${comparisonForm.name}" 已创建，正在启动分析...`,
        type: 'success',
        duration: 3000
      })
      
      // 自动启动分析
      await startComparison(result.comparison_id)
      
    } else {
      throw new Error(result.error || '创建失败')
    }
    
  } catch (error: any) {
    showMessage.error(`创建对比分析失败: ${error.message}`)
  } finally {
    creating.value = false
  }
}

const startComparison = async (comparisonId: string) => {
  try {
    const response = await fetch(`/api/v1/document-comparison/${comparisonId}/start`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    })
    
    const result = await response.json()
    
    if (result.success) {
      showMessage.success('对比分析已启动')
      // 跳转到结果页面
      selectedComparison.value = { comparison_id: comparisonId }
    } else {
      throw new Error(result.error || '启动失败')
    }
    
  } catch (error: any) {
    showMessage.error(`启动对比分析失败: ${error.message}`)
  }
}

const addDocuments = (documents: DocumentInfo[]) => {
  documents.forEach(doc => {
    // 检查是否已存在
    const exists = comparisonForm.documents.some(
      existing => existing.analysis_record_id === doc.analysis_record_id
    )
    
    if (!exists) {
      // 设置默认标签
      if (!doc.label) {
        doc.label = doc.filename.split('.')[0]
      }
      
      // 第一个文档设为主要文档
      if (comparisonForm.documents.length === 0) {
        doc.role = 'primary'
      }
      
      comparisonForm.documents.push(doc)
    }
  })
  
  // 确保只有一个主要文档
  ensureSinglePrimaryDocument()
  
  showDocumentSelector.value = false
  showMessage.success(`已添加 ${documents.length} 个文档`)
}

const removeDocument = (index: number) => {
  const doc = comparisonForm.documents[index]
  comparisonForm.documents.splice(index, 1)
  
  // 如果删除的是主要文档，将第一个文档设为主要
  if (doc.role === 'primary' && comparisonForm.documents.length > 0) {
    comparisonForm.documents[0].role = 'primary'
  }
  
  showMessage.info('已移除文档')
}

const ensureSinglePrimaryDocument = () => {
  const primaryDocs = comparisonForm.documents.filter(doc => doc.role === 'primary')
  
  if (primaryDocs.length > 1) {
    // 只保留第一个为主要，其他设为次要
    comparisonForm.documents.forEach((doc, index) => {
      if (doc.role === 'primary' && index > 0) {
        doc.role = 'secondary'
      }
    })
  } else if (primaryDocs.length === 0 && comparisonForm.documents.length > 0) {
    // 如果没有主要文档，将第一个设为主要
    comparisonForm.documents[0].role = 'primary'
  }
}

const selectComparison = (comparison: any) => {
  selectedComparison.value = comparison
  showComparisonList.value = false
}

const refreshComparison = () => {
  // 刷新当前对比结果
  // ComparisonResults 组件会自己处理刷新
}

const resetForm = () => {
  comparisonFormRef.value?.resetFields()
  comparisonForm.documents = []
  comparisonForm.config = {
    comparison_type: 'product_specs',
    focus_areas: [],
    include_similarities: true,
    include_differences: true,
    min_confidence_threshold: 0.6,
    importance_threshold: 0.5,
    max_results_per_category: 50,
    enable_insights: true,
    custom_fields: []
  }
}

// Utility methods
const getAuthToken = () => {
  return localStorage.getItem('auth_token') || ''
}

const formatTime = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const formatFileType = (type: string) => {
  const types: Record<string, string> = {
    'txt': '文本文档',
    'pdf': 'PDF文档',
    'docx': 'Word文档',
    'png': 'PNG图片',
    'jpg': 'JPEG图片',
    'jpeg': 'JPEG图片'
  }
  return types[type.toLowerCase()] || type.toUpperCase()
}

const formatConfidence = (value: number) => {
  return `${Math.round(value * 100)}%`
}

const formatImportance = (value: number) => {
  const levels = ['很低', '低', '中等', '较高', '高', '很高']
  const index = Math.floor(value * (levels.length - 1))
  return levels[index] || '中等'
}

// Lifecycle
onMounted(() => {
  // 可以在这里加载用户的历史对比或模板
})
</script>

<style scoped>
.document-comparison {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.create-comparison-card {
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.documents-form-item :deep(.el-form-item__content) {
  flex-direction: column;
  align-items: stretch;
}

.documents-selection {
  width: 100%;
  min-height: 200px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  padding: 16px;
}

.documents-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  font-weight: 500;
  color: #606266;
}

.selected-documents {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.document-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  background: #fafafa;
  transition: all 0.3s ease;
}

.document-item:hover {
  border-color: #c6e2ff;
  background: #ecf5ff;
}

.document-item.primary-doc {
  border-color: #409eff;
  background: #f0f9ff;
}

.doc-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.doc-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.doc-icon {
  font-size: 24px;
  color: #909399;
}

.doc-details {
  flex: 1;
}

.doc-filename {
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.doc-meta {
  font-size: 12px;
  color: #909399;
}

.doc-config {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.doc-actions {
  flex-shrink: 0;
  margin-left: 16px;
}

.advanced-settings {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 6px;
}

.help-text {
  font-size: 12px;
  color: #909399;
  margin-left: 8px;
}

.form-actions {
  text-align: center;
  margin-top: 24px;
}

.form-actions :deep(.el-form-item__content) {
  justify-content: center;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .document-comparison {
    padding: 16px;
  }
  
  .doc-config {
    flex-direction: column;
    align-items: stretch;
  }
  
  .doc-config > * {
    width: 100% !important;
    margin: 4px 0 !important;
  }
  
  .documents-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .form-actions :deep(.el-form-item__content) {
    flex-direction: column;
  }
}
</style>