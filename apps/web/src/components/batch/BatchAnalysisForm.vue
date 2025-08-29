<template>
  <div class="batch-analysis-form">
    <el-card class="form-card">
      <template #header>
        <div class="card-header">
          <span>批量文档分析配置</span>
          <el-button text @click="resetForm">重置</el-button>
        </div>
      </template>
      
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        label-position="left"
      >
        <!-- 基本信息 -->
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="任务名称" prop="batch_name">
              <el-input
                v-model="form.batch_name"
                placeholder="输入批量分析任务名称"
                maxlength="100"
                show-word-limit
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="分析类型" prop="analysis_config.analysis_type">
              <el-select 
                v-model="form.analysis_config.analysis_type" 
                placeholder="选择分析类型"
                @change="handleAnalysisTypeChange"
              >
                <el-option
                  v-for="type in analysisTypes"
                  :key="type.value"
                  :label="type.label"
                  :value="type.value"
                >
                  <div class="analysis-type-option">
                    <div class="option-label">{{ type.label }}</div>
                    <div v-if="type.description" class="option-description">{{ type.description }}</div>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="任务描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="描述此批量分析任务的目的和要求..."
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        
        <!-- 文档上传 -->
        <el-form-item label="文档文件" prop="documents">
          <div class="upload-area">
            <el-upload
              ref="uploadRef"
              class="document-upload"
              :file-list="fileList"
              :before-upload="beforeUpload"
              :on-change="handleFileChange"
              :on-remove="handleFileRemove"
              :auto-upload="false"
              multiple
              drag
              accept=".pdf,.doc,.docx,.txt,.xlsx,.xls"
            >
              <el-icon class="upload-icon"><UploadFilled /></el-icon>
              <div class="upload-text">
                <p>拖拽文件到此处，或<em>点击上传</em></p>
                <p class="upload-hint">支持 PDF、Word、Excel、Text 格式，单文件最大 50MB</p>
              </div>
            </el-upload>
            
            <div v-if="fileList.length > 0" class="file-summary">
              <el-divider />
              <div class="summary-info">
                <el-tag type="info">已选择 {{ fileList.length }} 个文件</el-tag>
                <el-tag type="warning">总大小 {{ formatFileSize(totalSize) }}</el-tag>
                <el-button type="danger" size="small" @click="clearFiles">清空</el-button>
              </div>
            </div>
          </div>
        </el-form-item>
        
        <!-- 分析配置 -->
        <el-divider content-position="left">分析配置</el-divider>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="处理优先级">
              <el-radio-group v-model="form.analysis_config.processing_priority">
                <el-radio value="speed">速度优先</el-radio>
                <el-radio value="accuracy">准确性优先</el-radio>
                <el-radio value="balanced">平衡模式</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="自动重试">
              <el-switch
                v-model="form.analysis_config.auto_retry_failed"
                active-text="开启"
                inactive-text="关闭"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="最大重试次数">
              <el-input-number
                v-model="form.analysis_config.max_retries"
                :min="0"
                :max="5"
                :disabled="!form.analysis_config.auto_retry_failed"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <!-- 业务上下文配置 -->
        <div v-if="showBusinessContext" class="business-context-section">
          <el-divider content-position="left">业务上下文配置</el-divider>
          
          <!-- 客户需求分析配置 -->
          <div v-if="form.analysis_config.analysis_type === 'customer_requirements'">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="行业领域">
                  <el-select v-model="form.analysis_config.business_context.industry" placeholder="选择行业">
                    <el-option label="制造业" value="manufacturing" />
                    <el-option label="IT/软件" value="it_software" />
                    <el-option label="电信" value="telecommunications" />
                    <el-option label="金融" value="finance" />
                    <el-option label="能源" value="energy" />
                    <el-option label="医疗" value="healthcare" />
                    <el-option label="其他" value="other" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="需求类型">
                  <el-select v-model="form.analysis_config.business_context.requirements_type" placeholder="选择需求类型">
                    <el-option label="技术需求" value="technical" />
                    <el-option label="功能需求" value="functional" />
                    <el-option label="商务需求" value="business" />
                    <el-option label="混合需求" value="mixed" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="项目类型">
                  <el-input v-model="form.analysis_config.business_context.project_type" placeholder="如：ERP系统、网络设备等" />
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-form-item label="分析重点">
              <el-checkbox-group v-model="form.analysis_config.business_context.analysis_focus">
                <el-checkbox value="technical_specs">技术规格</el-checkbox>
                <el-checkbox value="budget_analysis">预算分析</el-checkbox>
                <el-checkbox value="timeline_requirements">时间要求</el-checkbox>
                <el-checkbox value="compliance_standards">合规标准</el-checkbox>
                <el-checkbox value="risk_assessment">风险评估</el-checkbox>
                <el-checkbox value="decision_factors">决策因素</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </div>
          
          <!-- 竞品分析配置 -->
          <div v-if="form.analysis_config.analysis_type === 'competitor_analysis'">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="竞品类别">
                  <el-input v-model="form.analysis_config.business_context.competitor_category" placeholder="如：网络设备、软件系统等" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="行业领域">
                  <el-select v-model="form.analysis_config.business_context.industry" placeholder="选择行业">
                    <el-option label="制造业" value="manufacturing" />
                    <el-option label="IT/软件" value="it_software" />
                    <el-option label="电信" value="telecommunications" />
                    <el-option label="金融" value="finance" />
                    <el-option label="能源" value="energy" />
                    <el-option label="医疗" value="healthcare" />
                    <el-option label="其他" value="other" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-form-item label="分析重点">
              <el-checkbox-group v-model="form.analysis_config.business_context.analysis_focus">
                <el-checkbox value="pricing_analysis">价格分析</el-checkbox>
                <el-checkbox value="technical_comparison">技术对比</el-checkbox>
                <el-checkbox value="market_position">市场定位</el-checkbox>
                <el-checkbox value="feature_analysis">功能分析</el-checkbox>
                <el-checkbox value="competitive_advantages">竞争优势</el-checkbox>
                <el-checkbox value="weakness_identification">弱点识别</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </div>
          
          <!-- 项目挖掘配置 -->
          <div v-if="form.analysis_config.analysis_type === 'project_mining'">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="项目阶段">
                  <el-select v-model="form.analysis_config.business_context.project_phase" placeholder="选择项目阶段">
                    <el-option label="规划阶段" value="planning" />
                    <el-option label="执行阶段" value="execution" />
                    <el-option label="完成阶段" value="completion" />
                    <el-option label="评估阶段" value="evaluation" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="项目类型">
                  <el-input v-model="form.analysis_config.business_context.project_type" placeholder="如：系统集成、产品开发等" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="行业领域">
                  <el-select v-model="form.analysis_config.business_context.industry" placeholder="选择行业">
                    <el-option label="制造业" value="manufacturing" />
                    <el-option label="IT/软件" value="it_software" />
                    <el-option label="电信" value="telecommunications" />
                    <el-option label="金融" value="finance" />
                    <el-option label="能源" value="energy" />
                    <el-option label="医疗" value="healthcare" />
                    <el-option label="其他" value="other" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-form-item label="分析重点">
              <el-checkbox-group v-model="form.analysis_config.business_context.analysis_focus">
                <el-checkbox value="success_patterns">成功模式</el-checkbox>
                <el-checkbox value="best_practices">最佳实践</el-checkbox>
                <el-checkbox value="lessons_learned">经验教训</el-checkbox>
                <el-checkbox value="risk_factors">风险因素</el-checkbox>
                <el-checkbox value="resource_allocation">资源配置</el-checkbox>
                <el-checkbox value="reusable_assets">可复用资产</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </div>
        </div>
        
        <!-- 通知设置 -->
        <el-divider content-position="left">通知设置</el-divider>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="完成通知">
              <el-switch
                v-model="form.analysis_config.notification_settings.email_on_completion"
                active-text="邮件通知"
                inactive-text="关闭"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="失败通知">
              <el-switch
                v-model="form.analysis_config.notification_settings.email_on_failure"
                active-text="邮件通知"
                inactive-text="关闭"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="Webhook URL">
          <el-input
            v-model="form.analysis_config.notification_settings.webhook_url"
            placeholder="可选：任务完成后的 Webhook 回调地址"
          />
        </el-form-item>
        
        <!-- 提交按钮 -->
        <el-divider />
        
        <div class="submit-section">
          <div class="cost-estimation" v-if="estimatedCost">
            <el-alert
              :title="`预估费用: ${estimatedCost.cost} 元`"
              :description="`处理 ${estimatedCost.file_count} 个文件，预计 ${estimatedCost.time} 分钟完成`"
              type="info"
              show-icon
              :closable="false"
            />
          </div>
          
          <div class="submit-buttons">
            <el-button @click="resetForm">重置</el-button>
            <el-button
              type="primary"
              :loading="submitting"
              :disabled="fileList.length === 0"
              @click="submitAnalysis"
            >
              {{ submitting ? '提交中...' : '提交批量分析' }}
            </el-button>
          </div>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessageBox } from 'element-plus'
import { showMessage } from '@/utils/message'
import { UploadFilled } from '@element-plus/icons-vue'
import { submitBatchAnalysis } from '@/api/batch-analysis'
import type { FormInstance, UploadProps, UploadUserFile } from 'element-plus'
import type { BatchAnalysisRequest, BatchAnalysisConfig } from '@/types/batch-analysis'

const emit = defineEmits<{
  jobSubmitted: [jobId: string]
  submissionError: [error: string]
}>()

const formRef = ref<FormInstance>()
const uploadRef = ref()

// 分析类型选项
const analysisTypes = [
  { 
    value: 'customer_requirements', 
    label: '客户需求分析',
    description: '分析客户需求文档，提取技术参数、商务要求等关键信息'
  },
  { 
    value: 'competitor_analysis', 
    label: '竞品资料分析',
    description: '分析竞争对手产品资料，提取价格、规格等市场情报'
  },
  { 
    value: 'project_mining', 
    label: '历史项目挖掘',
    description: '分析历史项目文档，提取成功模式和最佳实践'
  },
  { value: 'product_extraction', label: '产品信息提取' },
  { value: 'document_classification', label: '文档分类' },
  { value: 'quality_assessment', label: '质量评估' },
  { value: 'comprehensive', label: '综合分析' }
]

// 表单数据
const form = reactive<BatchAnalysisRequest>({
  documents: [],
  batch_name: '',
  description: '',
  analysis_config: {
    analysis_type: 'customer_requirements',
    processing_priority: 'balanced',
    auto_retry_failed: true,
    max_retries: 2,
    business_context: {
      industry: '',
      project_type: '',
      analysis_focus: [],
      requirements_type: 'mixed',
      competitor_category: '',
      project_phase: 'planning'
    },
    notification_settings: {
      email_on_completion: true,
      email_on_failure: true,
      webhook_url: ''
    }
  }
})

// 文件列表
const fileList = ref<UploadUserFile[]>([])
const submitting = ref(false)

// 控制业务上下文配置显示
const showBusinessContext = computed(() => {
  const businessTypes = ['customer_requirements', 'competitor_analysis', 'project_mining']
  return businessTypes.includes(form.analysis_config.analysis_type)
})

// 处理分析类型变更
const handleAnalysisTypeChange = (value: string) => {
  // 重置业务上下文配置
  if (form.analysis_config.business_context) {
    form.analysis_config.business_context.analysis_focus = []
    
    // 根据分析类型设置默认值
    switch (value) {
      case 'customer_requirements':
        form.analysis_config.business_context.requirements_type = 'mixed'
        break
      case 'competitor_analysis':
        form.analysis_config.business_context.competitor_category = ''
        break
      case 'project_mining':
        form.analysis_config.business_context.project_phase = 'planning'
        break
    }
  }
}

// 表单验证规则
const rules = {
  batch_name: [
    { required: true, message: '请输入任务名称', trigger: 'blur' },
    { min: 2, max: 100, message: '任务名称长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  'analysis_config.analysis_type': [
    { required: true, message: '请选择分析类型', trigger: 'change' }
  ],
  documents: [
    { required: true, message: '请上传至少一个文档文件', trigger: 'change' }
  ]
}

// 计算属性
const totalSize = computed(() => {
  return fileList.value.reduce((total, file) => total + (file.size || 0), 0)
})

const estimatedCost = ref<{
  cost: string
  file_count: number
  time: number
} | null>(null)

// 文件大小格式化
const formatFileSize = (size: number): string => {
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB'
  if (size < 1024 * 1024 * 1024) return (size / (1024 * 1024)).toFixed(1) + ' MB'
  return (size / (1024 * 1024 * 1024)).toFixed(1) + ' GB'
}

// 文件上传前检查
const beforeUpload = (file: File) => {
  const allowedTypes = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  ]
  
  if (!allowedTypes.includes(file.type)) {
    showMessage.error('只支持 PDF、Word、Excel、Text 格式文件')
    return false
  }
  
  const maxSize = 50 * 1024 * 1024 // 50MB
  if (file.size > maxSize) {
    showMessage.error('文件大小不能超过 50MB')
    return false
  }
  
  return false // 阻止自动上传
}

// 文件变更处理
const handleFileChange: UploadProps['onChange'] = (file, files) => {
  fileList.value = files
  form.documents = files.map(f => f.raw!).filter(f => f)
  
  // 更新费用估算
  updateCostEstimation()
}

// 文件移除处理
const handleFileRemove: UploadProps['onRemove'] = (file, files) => {
  fileList.value = files
  form.documents = files.map(f => f.raw!).filter(f => f)
  
  // 更新费用估算
  updateCostEstimation()
}

// 清空文件
const clearFiles = () => {
  fileList.value = []
  form.documents = []
  uploadRef.value?.clearFiles()
  estimatedCost.value = null
}

// 更新费用估算
const updateCostEstimation = () => {
  if (fileList.value.length === 0) {
    estimatedCost.value = null
    return
  }
  
  // 简单的费用估算逻辑
  const fileCount = fileList.value.length
  const avgCostPerFile = 0.5 // 0.5元/文件
  const avgTimePerFile = 1.5 // 1.5分钟/文件
  
  estimatedCost.value = {
    cost: (fileCount * avgCostPerFile).toFixed(2),
    file_count: fileCount,
    time: Math.ceil(fileCount * avgTimePerFile)
  }
}

// 提交分析
const submitAnalysis = async () => {
  if (!formRef.value) return
  
  try {
    const valid = await formRef.value.validate()
    if (!valid) return
    
    if (form.documents.length === 0) {
      showMessage.error('请至少上传一个文档文件')
      return
    }
    
    // 确认提交
    const confirmResult = await ElMessageBox.confirm(
      `确定提交批量分析任务吗？包含 ${form.documents.length} 个文件，预估费用 ${estimatedCost.value?.cost || '未知'} 元。`,
      '确认提交',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    
    if (confirmResult !== 'confirm') return
    
    submitting.value = true
    
    const response = await submitBatchAnalysis(form)
    
    if (response.success) {
      showMessage.success(`任务提交成功！任务ID: ${response.job_id}`)
      emit('jobSubmitted', response.job_id)
      resetForm()
    } else {
      throw new Error(response.error || '提交失败')
    }
    
  } catch (error: any) {
    console.error('Batch analysis submission error:', error)
    const errorMessage = error.message || '提交批量分析任务失败'
    showMessage.error(errorMessage)
    emit('submissionError', errorMessage)
  } finally {
    submitting.value = false
  }
}

// 重置表单
const resetForm = () => {
  formRef.value?.resetFields()
  clearFiles()
  
  // 重置为默认值
  Object.assign(form, {
    documents: [],
    batch_name: '',
    description: '',
    analysis_config: {
      analysis_type: 'product_extraction',
      processing_priority: 'balanced',
      auto_retry_failed: true,
      max_retries: 2,
      notification_settings: {
        email_on_completion: true,
        email_on_failure: true,
        webhook_url: ''
      }
    }
  })
}

// 监听文件数量变化，验证表单
watch(() => form.documents.length, (newCount) => {
  if (formRef.value) {
    formRef.value.validateField('documents')
  }
})
</script>

<style scoped>
.batch-analysis-form {
  max-width: 1000px;
  margin: 0 auto;
}

.form-card {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 16px;
}

.upload-area {
  width: 100%;
}

.document-upload {
  width: 100%;
}

:deep(.el-upload-dragger) {
  width: 100%;
  height: 180px;
  border: 2px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: all 0.3s;
}

:deep(.el-upload-dragger:hover) {
  border-color: #409eff;
}

.upload-icon {
  font-size: 67px;
  color: #c0c4cc;
  margin-top: 40px;
}

.upload-text {
  color: #606266;
  margin-top: 15px;
}

.upload-text p {
  margin: 0;
  line-height: 1.4;
}

.upload-text em {
  color: #409eff;
  font-style: normal;
}

.upload-hint {
  font-size: 12px;
  color: #c0c4cc;
  margin-top: 5px !important;
}

.file-summary {
  margin-top: 15px;
}

.summary-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.cost-estimation {
  margin-bottom: 20px;
}

.submit-section {
  text-align: center;
}

.submit-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 20px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #303133;
}

:deep(.el-divider__text) {
  background-color: #fff;
  font-weight: 600;
  color: #303133;
}

.business-context-section {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin: 20px 0;
  border: 1px solid #e9ecef;
}

.analysis-type-option {
  padding: 5px 0;
}

.option-label {
  font-weight: 500;
  color: #303133;
}

.option-description {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
  line-height: 1.4;
}

:deep(.el-checkbox-group) {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}

:deep(.el-checkbox) {
  margin-right: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .batch-analysis-form {
    padding: 0 10px;
  }
  
  .submit-buttons {
    flex-direction: column;
    align-items: center;
  }
  
  .summary-info {
    justify-content: center;
  }
}
</style>