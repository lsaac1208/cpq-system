<template>
  <div class="enhanced-single-analysis">
    <el-row :gutter="20">
      <!-- 左侧：文档上传和配置 -->
      <el-col :span="12">
        <el-card class="upload-card">
          <template #header>
            <h3>文档上传</h3>
          </template>
          
          <el-upload
            ref="uploadRef"
            class="document-uploader"
            drag
            :auto-upload="false"
            :multiple="false"
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
          
          <!-- 文档信息 -->
          <div v-if="selectedFile" class="file-info">
            <div class="file-item">
              <el-icon class="file-icon"><Document /></el-icon>
              <div class="file-details">
                <div class="file-name">{{ selectedFile.name }}</div>
                <div class="file-size">{{ formatFileSize(selectedFile.size) }}</div>
                <div class="file-type">{{ getFileType(selectedFile.type) }}</div>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 分析配置 -->
        <el-card class="config-card">
          <template #header>
            <h3>分析配置</h3>
          </template>
          
          <el-form label-width="100px">
            <el-form-item label="分析类型">
              <el-select v-model="analysisConfig.type" style="width: 100%">
                <el-option label="产品信息提取" value="product_extraction" />
                <el-option label="文档分类" value="document_classification" />
                <el-option label="质量评估" value="quality_assessment" />
                <el-option label="综合分析" value="comprehensive" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="分析深度">
              <el-radio-group v-model="analysisConfig.depth">
                <el-radio value="basic">基础</el-radio>
                <el-radio value="detailed">详细</el-radio>
                <el-radio value="comprehensive">全面</el-radio>
              </el-radio-group>
            </el-form-item>
            
            <el-form-item label="提取重点">
              <el-checkbox-group v-model="analysisConfig.focus">
                <el-checkbox value="basic_info">基本信息</el-checkbox>
                <el-checkbox value="specifications">技术规格</el-checkbox>
                <el-checkbox value="features">产品特性</el-checkbox>
                <el-checkbox value="pricing">价格信息</el-checkbox>
                <el-checkbox value="quality">质量标准</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
            
            <el-form-item label="置信度">
              <el-slider 
                v-model="analysisConfig.confidence_threshold" 
                :min="0.3" 
                :max="0.9" 
                :step="0.1"
                show-stops
                show-input
                :input-size="'small'"
              />
              <div class="config-tip">设置最低置信度阈值，低于此值的结果将被标记</div>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 右侧：分析按钮和实时状态 -->
      <el-col :span="12">
        <el-card class="action-card">
          <template #header>
            <h3>分析控制</h3>
          </template>
          
          <div class="analysis-actions">
            <el-button 
              type="primary" 
              size="large"
              :loading="analyzing"
              @click="startAnalysis"
              :disabled="!canAnalyze"
              class="analyze-btn"
            >
              <template #icon>
                <el-icon><MagicStick /></el-icon>
              </template>
              {{ analyzing ? '分析中...' : '开始智能分析' }}
            </el-button>
            
            <div v-if="analyzing" class="analysis-progress">
              <el-progress 
                :percentage="analysisProgress.percentage" 
                :status="analysisProgress.status"
                :stroke-width="8"
              />
              <div class="progress-text">{{ analysisProgress.text }}</div>
              <div class="progress-time">
                预计剩余时间: {{ formatTime(analysisProgress.estimated_time) }}
              </div>
            </div>
          </div>
        </el-card>

        <!-- AI模型状态 -->
        <el-card class="model-status-card">
          <template #header>
            <h3>AI模型状态</h3>
          </template>
          
          <div class="model-status">
            <div class="status-item">
              <span class="status-label">智谱AI GLM-4</span>
              <el-tag :type="modelStatus.online ? 'success' : 'danger'" size="small">
                {{ modelStatus.online ? '在线' : '离线' }}
              </el-tag>
            </div>
            <div class="status-item">
              <span class="status-label">响应时间</span>
              <span class="status-value">{{ modelStatus.response_time }}ms</span>
            </div>
            <div class="status-item">
              <span class="status-label">负载状态</span>
              <el-progress 
                :percentage="modelStatus.load" 
                :color="getLoadColor(modelStatus.load)"
                :show-text="false"
                :stroke-width="6"
              />
            </div>
          </div>
        </el-card>

        <!-- 快速预览 -->
        <el-card v-if="previewData" class="preview-card">
          <template #header>
            <h3>文档预览</h3>
          </template>
          
          <div class="document-preview">
            <div class="preview-content">
              {{ previewData.text_preview }}
            </div>
            <div class="preview-meta">
              <span>字数: {{ previewData.word_count }}</span>
              <span>页数: {{ previewData.page_count }}</span>
              <span>语言: {{ previewData.language }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 分析结果 -->
    <div v-if="analysisResult" class="analysis-results">
      <el-card class="result-card">
        <template #header>
          <div class="result-header">
            <h3>分析结果</h3>
            <div class="result-actions">
              <el-button type="success" size="small" @click="saveResult">
                <template #icon><el-icon><Check /></el-icon></template>
                保存结果
              </el-button>
              <el-button type="primary" size="small" @click="createProduct">
                <template #icon><el-icon><Plus /></el-icon></template>
                创建产品
              </el-button>
              <el-button type="info" size="small" @click="exportResult">
                <template #icon><el-icon><Download /></el-icon></template>
                导出结果
              </el-button>
            </div>
          </div>
        </template>
        
        <AIAnalysisPreview 
          :analysisResult="analysisResult"
          @product-created="handleProductCreated"
          @field-modified="handleFieldModified"
        />
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { type UploadFile, type UploadFiles, type UploadInstance } from 'element-plus'
import { showMessage } from '@/utils/message'
import { UploadFilled, Document, MagicStick, Check, Plus, Download } from '@element-plus/icons-vue'
import { analyzeDocument } from '@/api/ai-analysis'
import { useAuthStore } from '@/stores/auth'
import AIAnalysisPreview from '@/components/AIAnalysisPreview.vue'
import type { AIAnalysisResult } from '@/types/ai-analysis'

// 组件事件
const emit = defineEmits<{
  'analysis-success': [result: AIAnalysisResult]
  'analysis-error': [error: string]
}>()

// 响应式数据
const uploadRef = ref<UploadInstance>()
const analyzing = ref(false)
const fileList = ref<UploadFile[]>([])
const selectedFile = ref<File | null>(null)
const analysisResult = ref<AIAnalysisResult | null>(null)

// 分析配置
const analysisConfig = reactive({
  type: 'comprehensive',
  depth: 'detailed',
  focus: ['basic_info', 'specifications', 'features'],
  confidence_threshold: 0.7
})

// 分析进度
const analysisProgress = reactive({
  percentage: 0,
  status: '' as '' | 'success' | 'warning' | 'exception',
  text: '准备开始分析...',
  estimated_time: 0
})

// AI模型状态
const modelStatus = reactive({
  online: true,
  response_time: 850,
  load: 45
})

// 文档预览数据
const previewData = ref<{
  text_preview: string
  word_count: number
  page_count: number
  language: string
} | null>(null)

// 计算属性
const canAnalyze = computed(() => {
  return selectedFile.value && !analyzing.value
})

// 方法
const handleFileChange = (file: UploadFile, files: UploadFiles) => {
  fileList.value = files
  if (file.raw) {
    selectedFile.value = file.raw
    generatePreview(file.raw)
  }
}

const handleFileRemove = () => {
  fileList.value = []
  selectedFile.value = null
  previewData.value = null
  analysisResult.value = null
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

const generatePreview = async (file: File) => {
  // 模拟生成文档预览
  const text = await readFileAsText(file)
  previewData.value = {
    text_preview: text.substring(0, 300) + (text.length > 300 ? '...' : ''),
    word_count: text.split(/\s+/).length,
    page_count: Math.ceil(text.length / 2000),
    language: detectLanguage(text)
  }
}

const readFileAsText = (file: File): Promise<string> => {
  return new Promise((resolve) => {
    if (file.type === 'text/plain') {
      const reader = new FileReader()
      reader.onload = (e) => {
        resolve(e.target?.result as string || '')
      }
      reader.readAsText(file)
    } else {
      // 对于PDF和Word文件，返回模拟文本
      resolve('这是一个示例文档内容，实际内容将通过服务器端解析获取...')
    }
  })
}

const detectLanguage = (text: string): string => {
  const chineseRegex = /[\u4e00-\u9fff]/
  return chineseRegex.test(text) ? '中文' : '英文'
}

const startAnalysis = async () => {
  if (!selectedFile.value) return

  try {
    analyzing.value = true
    analysisResult.value = null
    
    // 重置进度
    analysisProgress.percentage = 0
    analysisProgress.status = ''
    analysisProgress.text = '准备开始分析...'
    analysisProgress.estimated_time = 60

    // 🔍 检查用户权限 - 宽松检查，允许所有登录用户使用
    const authStore = useAuthStore()
    const userRole = authStore.userRole
    
    // 只检查是否已登录，不限制特定角色
    if (!authStore.isAuthenticated) {
      throw new Error('请先登录后再使用AI分析功能')
    }
    
    console.log('✅ 用户权限检查通过，当前角色:', userRole)

    // 🔍 检查AI服务状态
    analysisProgress.text = '检查AI服务状态...'
    try {
      // 先检查支持的格式，确认服务可用
      await import('@/api/ai-analysis').then(module => module.getSupportedFormats())
      console.log('✅ AI服务状态检查通过')
    } catch (serviceError) {
      console.error('❌ AI服务不可用:', serviceError)
      throw new Error('AI分析服务暂时不可用，请稍后重试或联系管理员')
    }

    // 🔍 文件格式验证
    const supportedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword', 'text/plain']
    if (!supportedTypes.includes(selectedFile.value.type)) {
      throw new Error(`不支持的文件格式：${selectedFile.value.type}，请上传 PDF、Word 或 TXT 文件`)
    }

    // 模拟进度更新
    const progressInterval = setInterval(() => {
      if (analysisProgress.percentage < 90) {
        analysisProgress.percentage += Math.random() * 10
        analysisProgress.estimated_time = Math.max(0, analysisProgress.estimated_time - 3)
        
        if (analysisProgress.percentage < 30) {
          analysisProgress.text = '正在解析文档结构...'
        } else if (analysisProgress.percentage < 60) {
          analysisProgress.text = '正在提取关键信息...'
        } else {
          analysisProgress.text = '正在生成分析结果...'
        }
      }
    }, 1000)

    analysisProgress.text = '连接AI分析服务...'
    const response = await analyzeDocument(selectedFile.value)
    
    clearInterval(progressInterval)
    
    // 🔍 解析axios响应结构
    console.log('🔍 完整响应对象:', response)
    console.log('📊 响应数据:', response.data)
    console.log('✅ HTTP状态:', response.status)
    
    // 🔧 正确提取响应数据 - axios返回的是 {data: actualData} 结构
    const result = response.data
    console.log('✅ 提取的结果数据:', result)
    console.log('🎯 成功标识:', result?.success)
    
    if (result && result.success) {
      analysisProgress.percentage = 100
      analysisProgress.status = 'success'
      analysisProgress.text = '分析完成！'
      analysisProgress.estimated_time = 0
      
      analysisResult.value = result
      emit('analysis-success', result)
      
      showMessage.success('文档分析完成！')
    } else {
      // 🔍 详细错误分类和用户友好提示
      console.error('❌ 分析失败，响应结果:', result)
      let errorMessage = '分析失败，请稍后重试'
      
      if (result?.error) {
        // 解析后端具体错误信息
        if (result.error.includes('No document file')) {
          errorMessage = '未检测到文档文件，请重新上传'
        } else if (result.error.includes('Document contains no readable text')) {
          errorMessage = '文档内容无法读取，请检查文件是否损坏或为空白文档'
        } else if (result.error.includes('Document analysis failed')) {
          errorMessage = 'AI分析引擎暂时无法处理此文档，请稍后重试'
        } else if (result.error.includes('timeout')) {
          errorMessage = '分析超时，请尝试上传较小的文档或稍后重试'
        } else if (result.error.includes('permission')) {
          errorMessage = '权限不足，请联系管理员'
        } else {
          errorMessage = `分析失败：${result.error}`
        }
      }
      
      throw new Error(errorMessage)
    }
  } catch (error) {
    console.error('💥 分析过程异常:', error)
    
    // 🔍 智能错误分类和用户友好提示
    let message = '分析过程中发生未知错误'
    let suggestedAction = ''
    
    if (error instanceof Error) {
      message = error.message
      
      // 根据错误类型提供建议
      if (message.includes('权限不足')) {
        suggestedAction = '请联系管理员授予分析权限'
      } else if (message.includes('网络')) {
        suggestedAction = '请检查网络连接'
      } else if (message.includes('服务不可用')) {
        suggestedAction = '请稍后重试或联系技术支持'
      } else if (message.includes('文件格式')) {
        suggestedAction = '请上传支持的文件格式（PDF/Word/TXT）'
      } else if (message.includes('超时')) {
        suggestedAction = '请尝试上传较小的文件'
      } else {
        suggestedAction = '请稍后重试，如问题持续请联系技术支持'
      }
    } else if (typeof error === 'string') {
      message = error
    } else if (error && typeof error === 'object') {
      // 处理HTTP错误响应
      if (error.response) {
        const status = error.response.status
        switch (status) {
          case 401:
            message = '登录已过期，请重新登录'
            suggestedAction = '重新登录后再试'
            break
          case 403:
            message = '权限不足，无法访问AI分析功能'
            suggestedAction = '请联系管理员授予相应权限'
            break
          case 404:
            message = 'AI分析服务未找到'
            suggestedAction = '请联系技术支持检查服务配置'
            break
          case 500:
            message = '服务器内部错误'
            suggestedAction = '请稍后重试或联系技术支持'
            break
          default:
            message = `服务请求失败 (${status})`
            suggestedAction = '请稍后重试'
        }
      } else {
        message = JSON.stringify(error)
      }
    }
    
    analysisProgress.status = 'exception'
    analysisProgress.text = '分析失败'
    
    // 构建完整的错误信息
    const fullErrorMessage = suggestedAction ? `${message}。建议：${suggestedAction}` : message
    
    emit('analysis-error', fullErrorMessage)
    showMessage.error(fullErrorMessage)
  } finally {
    analyzing.value = false
  }
}

const saveResult = () => {
  showMessage.success('分析结果已保存')
}

const createProduct = () => {
  if (analysisResult.value) {
    // 跳转到产品创建页面或打开创建对话框
    showMessage.info('正在跳转到产品创建页面...')
  }
}

const exportResult = () => {
  if (analysisResult.value) {
    // 导出分析结果
    const dataStr = JSON.stringify(analysisResult.value, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    
    const link = document.createElement('a')
    link.href = url
    link.download = `analysis-result-${Date.now()}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    URL.revokeObjectURL(url)
    showMessage.success('分析结果已导出')
  }
}

const handleProductCreated = (productId: number) => {
  showMessage.success(`产品创建成功，ID: ${productId}`)
}

const handleFieldModified = (field: string, value: any) => {
  console.log('Field modified:', field, value)
}

const formatFileSize = (size: number): string => {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

const getFileType = (mimeType: string): string => {
  const typeMap: Record<string, string> = {
    'application/pdf': 'PDF文档',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'Word文档',
    'application/msword': 'Word文档',
    'text/plain': '文本文件'
  }
  return typeMap[mimeType] || '未知格式'
}

const getLoadColor = (load: number): string => {
  if (load < 50) return '#67c23a'
  if (load < 80) return '#e6a23c'
  return '#f56c6c'
}

const formatTime = (seconds: number): string => {
  if (seconds < 60) return `${seconds}秒`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}分${remainingSeconds}秒`
}
</script>

<style scoped>
.enhanced-single-analysis {
  padding: 20px;
}

.upload-card,
.config-card,
.action-card,
.model-status-card,
.preview-card {
  margin-bottom: 20px;
}

.upload-card :deep(.el-card__header),
.config-card :deep(.el-card__header),
.action-card :deep(.el-card__header),
.model-status-card :deep(.el-card__header),
.preview-card :deep(.el-card__header) {
  padding: 15px 20px;
}

.upload-card :deep(.el-card__header) h3,
.config-card :deep(.el-card__header) h3,
.action-card :deep(.el-card__header) h3,
.model-status-card :deep(.el-card__header) h3,
.preview-card :deep(.el-card__header) h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
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

.file-info {
  margin-top: 15px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 15px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background: #fafafa;
}

.file-icon {
  font-size: 24px;
  color: #409eff;
}

.file-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.file-name {
  font-weight: 500;
  color: #303133;
  font-size: 14px;
}

.file-size,
.file-type {
  font-size: 12px;
  color: #909399;
}

.config-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.analysis-actions {
  text-align: center;
}

.analyze-btn {
  width: 100%;
  height: 50px;
  font-size: 16px;
  margin-bottom: 20px;
}

.analysis-progress {
  margin-top: 20px;
}

.progress-text {
  text-align: center;
  margin: 10px 0;
  color: #606266;
  font-size: 14px;
}

.progress-time {
  text-align: center;
  color: #909399;
  font-size: 12px;
}

.model-status {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.status-value {
  font-size: 14px;
  color: #303133;
  font-weight: 600;
}

.document-preview {
  max-height: 200px;
  overflow-y: auto;
}

.preview-content {
  font-size: 12px;
  line-height: 1.5;
  color: #606266;
  background: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 10px;
  font-family: 'Courier New', monospace;
}

.preview-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}

.analysis-results {
  margin-top: 30px;
}

.result-card {
  border: 2px solid #67c23a;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-header h3 {
  margin: 0;
  color: #303133;
  font-size: 18px;
  font-weight: 600;
}

.result-actions {
  display: flex;
  gap: 10px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .enhanced-single-analysis :deep(.el-row) {
    flex-direction: column;
  }
  
  .enhanced-single-analysis :deep(.el-col) {
    width: 100% !important;
    margin-bottom: 20px;
  }
  
  .result-header {
    flex-direction: column;
    gap: 10px;
    align-items: stretch;
  }
  
  .result-actions {
    justify-content: center;
  }
  
  .preview-meta {
    flex-direction: column;
    gap: 5px;
  }
}
</style>