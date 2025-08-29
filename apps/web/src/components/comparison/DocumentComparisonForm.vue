<template>
  <div class="comparison-form">
    <el-card class="form-card">
      <template #header>
        <div class="card-header">
          <h3>文档对比配置</h3>
          <p>上传多个文档进行智能对比分析</p>
        </div>
      </template>

      <el-form 
        ref="formRef" 
        :model="formData" 
        :rules="formRules" 
        label-width="140px"
        class="comparison-form-content"
      >
        <!-- 文档上传区域 -->
        <el-form-item label="待对比文档" prop="documents" required>
          <div class="document-upload-area">
            <el-upload
              ref="uploadRef"
              class="document-uploader"
              drag
              :auto-upload="false"
              :multiple="true"
              :file-list="fileList"
              :on-change="handleFileChange"
              :on-remove="handleFileRemove"
              :before-upload="beforeUpload"
              accept=".pdf,.docx,.doc,.txt"
            >
              <div class="upload-content">
                <el-icon class="upload-icon"><UploadFilled /></el-icon>
                <div class="upload-text">
                  <p>将文档拖拽到此处或<em>点击上传</em></p>
                  <p class="upload-tip">支持 PDF、Word、TXT 格式，单个文件不超过10MB</p>
                </div>
              </div>
            </el-upload>
            
            <!-- 文档列表 -->
            <div v-if="formData.documents.length > 0" class="document-list">
              <h4>已选择的文档 ({{ formData.documents.length }})</h4>
              <div 
                v-for="(doc, index) in formData.documents" 
                :key="index"
                class="document-item"
              >
                <div class="document-info">
                  <el-icon class="file-icon"><Document /></el-icon>
                  <div class="file-details">
                    <div class="file-name">{{ doc.file.name }}</div>
                    <div class="file-size">{{ formatFileSize(doc.file.size) }}</div>
                  </div>
                </div>
                
                <div class="document-meta">
                  <el-input
                    v-model="doc.name"
                    placeholder="文档别名（可选）"
                    size="small"
                    style="width: 150px; margin-right: 10px"
                  />
                  <el-input
                    v-model="doc.description"
                    placeholder="文档描述（可选）"
                    size="small"
                    style="width: 200px; margin-right: 10px"
                  />
                  <el-button 
                    type="danger" 
                    size="small" 
                    text
                    @click="removeDocument(index)"
                    :icon="Delete"
                  >
                    移除
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-form-item>

        <!-- 对比配置 -->
        <el-form-item label="对比维度" prop="dimensions" required>
          <el-checkbox-group v-model="formData.comparison_config.dimensions" class="dimension-checkboxes">
            <el-checkbox label="content">内容对比</el-checkbox>
            <el-checkbox label="structure">结构对比</el-checkbox>
            <el-checkbox label="features">特性对比</el-checkbox>
            <el-checkbox label="specifications">规格对比</el-checkbox>
            <el-checkbox label="quality">质量对比</el-checkbox>
            <el-checkbox label="compliance">合规性对比</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <!-- 分析深度 -->
        <el-form-item label="分析深度" prop="analysis_depth" required>
          <el-radio-group v-model="formData.comparison_config.analysis_depth" class="depth-radios">
            <el-radio value="basic">
              <div class="radio-content">
                <div class="radio-title">基础分析</div>
                <div class="radio-desc">快速对比主要差异，适合初步了解</div>
              </div>
            </el-radio>
            <el-radio value="detailed">
              <div class="radio-content">
                <div class="radio-title">详细分析</div>
                <div class="radio-desc">深入分析各个维度，提供详细报告</div>
              </div>
            </el-radio>
            <el-radio value="comprehensive">
              <div class="radio-content">
                <div class="radio-title">全面分析</div>
                <div class="radio-desc">最深入的分析，包含所有可能的对比维度</div>
              </div>
            </el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 对比选项 -->
        <el-form-item label="对比选项">
          <div class="comparison-options">
            <el-checkbox v-model="formData.comparison_config.include_similarities">
              包含相似性分析
            </el-checkbox>
            <el-checkbox v-model="formData.comparison_config.include_differences">
              包含差异性分析
            </el-checkbox>
            <el-checkbox v-model="formData.comparison_config.generate_recommendations">
              生成建议报告
            </el-checkbox>
          </div>
        </el-form-item>

        <!-- 分析焦点 -->
        <el-form-item label="分析焦点">
          <el-checkbox-group v-model="analysisFocus" class="focus-checkboxes">
            <el-checkbox label="technical_specs">技术规格</el-checkbox>
            <el-checkbox label="pricing">价格信息</el-checkbox>
            <el-checkbox label="features">功能特性</el-checkbox>
            <el-checkbox label="quality">质量标准</el-checkbox>
            <el-checkbox label="compliance">合规要求</el-checkbox>
            <el-checkbox label="performance">性能指标</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <!-- 权重配置 -->
        <el-form-item label="权重配置">
          <div class="weight-config">
            <div 
              v-for="focus in analysisFocus" 
              :key="focus"
              class="weight-item"
            >
              <span class="weight-label">{{ getFocusLabel(focus) }}</span>
              <el-slider 
                v-model="priorityWeights[focus]" 
                :min="0" 
                :max="1" 
                :step="0.1"
                show-stops
                show-input
                :input-size="'small'"
                style="width: 250px"
              />
            </div>
          </div>
        </el-form-item>

        <!-- 自定义标准 -->
        <el-form-item label="自定义标准">
          <div class="custom-criteria">
            <div class="criteria-header">
              <span>自定义对比标准</span>
              <el-button 
                type="primary" 
                size="small"
                @click="addCustomCriteria"
                :icon="Plus"
              >
                添加标准
              </el-button>
            </div>
            
            <div 
              v-for="(criteria, index) in formData.comparison_config.custom_criteria" 
              :key="index"
              class="criteria-item"
            >
              <el-input
                v-model="criteria.name"
                placeholder="标准名称"
                style="width: 150px; margin-right: 10px"
              />
              <el-input
                v-model="criteria.description"
                placeholder="标准描述"
                style="width: 200px; margin-right: 10px"
              />
              <el-input-number
                v-model="criteria.weight"
                :min="0"
                :max="1"
                :step="0.1"
                placeholder="权重"
                style="width: 100px; margin-right: 10px"
              />
              <el-button 
                type="danger" 
                size="small" 
                text
                @click="removeCustomCriteria(index)"
                :icon="Delete"
              >
                删除
              </el-button>
            </div>
          </div>
        </el-form-item>

        <!-- 操作按钮 -->
        <el-form-item>
          <div class="action-buttons">
            <el-button 
              type="primary" 
              size="large"
              :loading="loading"
              @click="startComparison"
              :disabled="!canSubmit"
            >
              <template #icon>
                <el-icon><Connection /></el-icon>
              </template>
              开始对比分析
            </el-button>
            
            <el-button 
              size="large" 
              @click="resetForm"
            >
              重置表单
            </el-button>
            
            <el-button 
              type="success" 
              size="large"
              @click="saveAsTemplate"
              :disabled="!hasValidConfig"
            >
              <template #icon>
                <el-icon><Document /></el-icon>
              </template>
              保存配置模板
            </el-button>
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 预设配置 -->
    <el-card class="preset-card">
      <template #header>
        <h3>快速配置</h3>
      </template>
      
      <div class="presets">
        <div 
          v-for="preset in presets" 
          :key="preset.name"
          class="preset-item"
          @click="loadPreset(preset)"
        >
          <h4>{{ preset.name }}</h4>
          <p>{{ preset.description }}</p>
          <div class="preset-tags">
            <el-tag 
              v-for="tag in preset.tags" 
              :key="tag"
              size="small" 
              type="info"
            >
              {{ tag }}
            </el-tag>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessageBox, type FormInstance, type FormRules, type UploadFile, type UploadFiles, type UploadInstance } from 'element-plus'
import { showMessage } from '@/utils/message'
import { UploadFilled, Document, Delete, Plus} from '@element-plus/icons-vue'
import { submitDocumentComparison } from '@/api/document-comparison'
import type { 
  DocumentComparisonRequest,
  DocumentComparisonResult,
  DocumentForComparison 
} from '@/types/document-comparison'

// 组件事件
const emit = defineEmits<{
  'comparison-start': []
  'comparison-success': [result: DocumentComparisonResult]
  'comparison-error': [error: string]
}>()

// 响应式数据
const formRef = ref<FormInstance>()
const uploadRef = ref<UploadInstance>()
const loading = ref(false)
const fileList = ref<UploadFile[]>([])

// 表单数据
const formData = reactive<DocumentComparisonRequest>({
  documents: [],
  comparison_config: {
    dimensions: ['content', 'structure'],
    analysis_depth: 'detailed',
    include_similarities: true,
    include_differences: true,
    generate_recommendations: true,
    custom_criteria: []
  },
  analysis_focus: {
    focus_areas: [],
    priority_weights: {},
    specific_requirements: []
  }
})

// 分析焦点和权重
const analysisFolder = ref<string[]>([])
const priorityWeights = ref<Record<string, number>>({})

// 表单验证规则
const formRules: FormRules = {
  documents: [
    { required: true, message: '请至少上传2个文档', trigger: 'change', validator: validateDocuments }
  ],
  dimensions: [
    { required: true, message: '请选择至少一个对比维度', trigger: 'change' }
  ],
  analysis_depth: [
    { required: true, message: '请选择分析深度', trigger: 'change' }
  ]
}

// 预设配置
const presets = [
  {
    name: '产品规格对比',
    description: '专门用于产品技术规格和功能特性的对比分析',
    tags: ['产品', '技术规格', '功能'],
    config: {
      dimensions: ['specifications', 'features', 'quality'],
      analysis_depth: 'detailed',
      focus_areas: ['technical_specs', 'features', 'performance']
    }
  },
  {
    name: '价格方案对比',
    description: '针对不同供应商价格方案的全面对比分析',
    tags: ['价格', '成本', '供应商'],
    config: {
      dimensions: ['content', 'quality'],
      analysis_depth: 'comprehensive',
      focus_areas: ['pricing', 'quality']
    }
  },
  {
    name: '合规性对比',
    description: '重点关注文档的合规性和标准符合度对比',
    tags: ['合规', '标准', '认证'],
    config: {
      dimensions: ['compliance', 'quality', 'structure'],
      analysis_depth: 'comprehensive',
      focus_areas: ['compliance', 'quality']
    }
  }
]

// 计算属性
const canSubmit = computed(() => {
  return formData.documents.length >= 2 && 
         formData.comparison_config.dimensions.length > 0
})

const hasValidConfig = computed(() => {
  return formData.comparison_config.dimensions.length > 0 &&
         formData.comparison_config.analysis_depth
})

// 方法
function validateDocuments(rule: any, value: any, callback: any) {
  if (!value || value.length < 2) {
    callback(new Error('请至少上传2个文档进行对比'))
  } else if (value.length > 10) {
    callback(new Error('最多支持同时对比10个文档'))
  } else {
    callback()
  }
}

const handleFileChange = (file: UploadFile, files: UploadFiles) => {
  fileList.value = files
  
  const validFiles = files.filter(f => f.raw).map(f => ({
    file: f.raw!,
    name: f.name,
    description: ''
  }))
  
  formData.documents = validFiles
}

const handleFileRemove = (file: UploadFile, files: UploadFiles) => {
  fileList.value = files
  
  const validFiles = files.filter(f => f.raw).map(f => ({
    file: f.raw!,
    name: f.name,
    description: ''
  }))
  
  formData.documents = validFiles
}

const beforeUpload = (file: File) => {
  const isValidType = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword', 'text/plain'].includes(file.type)
  const isValidSize = file.size / 1024 / 1024 < 10

  if (!isValidType) {
    showMessage.error('只支持 PDF、Word、TXT 格式的文件')
    return false
  }
  if (!isValidSize) {
    showMessage.error('文件大小不能超过 10MB')
    return false
  }
  return false // 阻止自动上传
}

const removeDocument = (index: number) => {
  formData.documents.splice(index, 1)
  // 同步更新 fileList
  fileList.value.splice(index, 1)
}

const addCustomCriteria = () => {
  formData.comparison_config.custom_criteria = formData.comparison_config.custom_criteria || []
  formData.comparison_config.custom_criteria.push({
    name: '',
    description: '',
    weight: 0.5
  })
}

const removeCustomCriteria = (index: number) => {
  formData.comparison_config.custom_criteria?.splice(index, 1)
}

const getFocusLabel = (focus: string): string => {
  const labels: Record<string, string> = {
    technical_specs: '技术规格',
    pricing: '价格信息',
    features: '功能特性',
    quality: '质量标准',
    compliance: '合规要求',
    performance: '性能指标'
  }
  return labels[focus] || focus
}

const formatFileSize = (size: number): string => {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

const startComparison = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    // 准备请求数据
    const requestData: DocumentComparisonRequest = {
      ...formData,
      analysis_focus: {
        focus_areas: analysisFolder.value,
        priority_weights: priorityWeights.value,
        specific_requirements: []
      }
    }
    
    loading.value = true
    emit('comparison-start')
    
    const result = await submitDocumentComparison(requestData)
    
    if (result.success && result.result) {
      emit('comparison-success', result.result)
      showMessage.success('文档对比分析完成！')
    } else {
      throw new Error(result.error || '对比分析失败')
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : '对比分析过程中发生错误'
    emit('comparison-error', message)
    showMessage.error(message)
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  ElMessageBox.confirm('确定要重置表单吗？所有输入的数据将丢失。', '确认重置', {
    type: 'warning'
  }).then(() => {
    formRef.value?.resetFields()
    formData.documents = []
    formData.comparison_config.custom_criteria = []
    analysisFolder.value = []
    priorityWeights.value = {}
    fileList.value = []
    uploadRef.value?.clearFiles()
    showMessage.success('表单已重置')
  }).catch(() => {
    // 用户取消
  })
}

const saveAsTemplate = () => {
  showMessage.info('配置模板保存功能即将推出')
}

const loadPreset = (preset: any) => {
  ElMessageBox.confirm(`确定要加载预设配置"${preset.name}"吗？当前配置将被替换。`, '确认加载预设', {
    type: 'info'
  }).then(() => {
    formData.comparison_config.dimensions = preset.config.dimensions
    formData.comparison_config.analysis_depth = preset.config.analysis_depth
    analysisFolder.value = preset.config.focus_areas
    
    // 初始化权重
    preset.config.focus_areas.forEach((focus: string) => {
      priorityWeights.value[focus] = 0.5
    })
    
    showMessage.success(`已加载预设配置：${preset.name}`)
  }).catch(() => {
    // 用户取消
  })
}

// 监听分析焦点变化，同步权重配置
watch(analysisFolder, (newFocusAreas) => {
  // 移除不再选中的焦点权重
  Object.keys(priorityWeights.value).forEach(key => {
    if (!newFocusAreas.includes(key)) {
      delete priorityWeights.value[key]
    }
  })
  
  // 为新选中的焦点添加默认权重
  newFocusAreas.forEach(focus => {
    if (!(focus in priorityWeights.value)) {
      priorityWeights.value[focus] = 0.5
    }
  })
}, { deep: true })
</script>

<style scoped>
.comparison-form {
  space-y: 20px;
}

.form-card {
  margin-bottom: 20px;
}

.card-header h3 {
  margin: 0 0 5px 0;
  color: #303133;
  font-size: 18px;
  font-weight: 600;
}

.card-header p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.document-upload-area {
  width: 100%;
}

.document-uploader {
  width: 100%;
  margin-bottom: 20px;
}

.upload-content {
  text-align: center;
  padding: 40px 0;
}

.upload-icon {
  font-size: 48px;
  color: #c0c4cc;
  margin-bottom: 15px;
}

.upload-text p {
  margin: 5px 0;
  color: #606266;
}

.upload-tip {
  font-size: 12px;
  color: #909399;
}

.document-list h4 {
  margin: 0 0 15px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 500;
}

.document-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  margin-bottom: 10px;
  background: #fafafa;
}

.document-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.file-icon {
  font-size: 24px;
  color: #409eff;
}

.file-details {
  display: flex;
  flex-direction: column;
}

.file-name {
  font-weight: 500;
  color: #303133;
}

.file-size {
  font-size: 12px;
  color: #909399;
}

.document-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.dimension-checkboxes,
.focus-checkboxes {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 10px;
}

.depth-radios {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.radio-content {
  margin-left: 10px;
}

.radio-title {
  font-weight: 500;
  color: #303133;
}

.radio-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.comparison-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.weight-config {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.weight-item {
  display: flex;
  align-items: center;
  gap: 15px;
}

.weight-label {
  min-width: 80px;
  font-weight: 500;
}

.custom-criteria {
  width: 100%;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 15px;
  background-color: #fafafa;
}

.criteria-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  font-weight: 500;
  color: #303133;
}

.criteria-item {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  padding: 10px;
  background: #fff;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

.action-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 20px;
}

.preset-card {
  margin-top: 20px;
}

.presets {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 15px;
}

.preset-item {
  padding: 15px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
}

.preset-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
}

.preset-item h4 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 16px;
}

.preset-item p {
  margin: 0 0 10px 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.4;
}

.preset-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .comparison-form-content {
    :deep(.el-form-item__label) {
      width: auto !important;
      text-align: left;
      margin-bottom: 5px;
    }
    
    :deep(.el-form-item__content) {
      margin-left: 0 !important;
    }
  }
  
  .document-item {
    flex-direction: column;
    align-items: stretch;
    gap: 15px;
  }
  
  .document-meta {
    flex-direction: column;
    align-items: stretch;
  }
  
  .dimension-checkboxes,
  .focus-checkboxes {
    grid-template-columns: 1fr;
  }
  
  .weight-config {
    grid-template-columns: 1fr;
  }
  
  .weight-item {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  
  .action-buttons {
    flex-direction: column;
    align-items: stretch;
  }
  
  .presets {
    grid-template-columns: 1fr;
  }
  
  .criteria-item {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>