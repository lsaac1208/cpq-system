<template>
  <div class="ai-document-upload">
    <!-- AI服务状态组件 -->
    <AIServiceStatus class="service-status" />
    
    <el-card class="upload-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon><Document /></el-icon>
            AI文档分析
          </span>
          <el-tag v-if="!aiAvailable" type="warning" size="small">
            AI服务不可用
          </el-tag>
        </div>
      </template>

      <!-- 上传区域 -->
      <div class="upload-area">
        <el-upload
          ref="uploadRef"
          class="document-upload"
          drag
          action=""
          :auto-upload="false"
          :show-file-list="true"
          :accept="acceptedFormats"
          :before-upload="beforeUpload"
          :on-change="handleFileChange"
          :on-remove="handleFileRemove"
          :disabled="uploading || !aiAvailable"
        >
          <div class="upload-content">
            <el-icon class="upload-icon"><UploadFilled /></el-icon>
            <div class="upload-text">
              <p>拖拽文件到这里，或<em>点击选择文件</em></p>
              <p class="upload-hint">
                支持格式: {{ supportedFormats.join(', ') }}
              </p>
              <p class="upload-size">文件大小限制: 10MB</p>
            </div>
          </div>
        </el-upload>

        <!-- 分析按钮 -->
        <div v-if="selectedFile" class="upload-actions">
          <el-button
            type="primary"
            size="large"
            :loading="uploading"
            :disabled="!selectedFile || !aiAvailable"
            @click="startAnalysis"
          >
            <el-icon><MagicStick /></el-icon>
            {{ uploading ? '正在分析中...' : '开始AI分析' }}
          </el-button>
          
          <el-button
            v-if="!uploading"
            size="large"
            @click="clearFile"
          >
            清除文件
          </el-button>
        </div>

        <!-- 分析进度 -->
        <div v-if="uploading" class="analysis-progress">
          <el-progress
            :percentage="progress"
            :show-text="false"
            :stroke-width="8"
            color="#409EFF"
          />
          <p class="progress-text">{{ progressText }}</p>
          
          <div class="progress-steps">
            <el-steps :active="currentStep" align-center>
              <el-step title="上传文件" icon="Upload" />
              <el-step title="文档解析" icon="Reading" />
              <el-step title="AI分析" icon="MagicStick" />
              <el-step title="完成" icon="Check" />
            </el-steps>
          </div>
        </div>
      </div>

      <!-- 支持格式信息 -->
      <div class="format-info">
        <el-collapse v-model="showFormatDetails">
          <el-collapse-item title="支持的文档格式" name="formats">
            <div class="format-details">
              <div class="format-category">
                <h4><el-icon><Document /></el-icon>文本文档</h4>
                <el-tag
                  v-for="format in documentFormats"
                  :key="format.ext"
                  :type="format.available ? 'success' : 'info'"
                  size="small"
                  class="format-tag"
                >
                  {{ format.ext.toUpperCase() }}
                  <span class="format-desc">{{ format.description }}</span>
                </el-tag>
              </div>
              
              <div v-if="ocrAvailable" class="format-category">
                <h4><el-icon><Picture /></el-icon>图片文档 (OCR)</h4>
                <el-tag
                  v-for="format in imageFormats"
                  :key="format"
                  type="warning"
                  size="small"
                  class="format-tag"
                >
                  {{ format.toUpperCase() }}
                </el-tag>
                <p class="format-note">
                  <el-icon><InfoFilled /></el-icon>
                  图片将通过OCR技术提取文字内容进行分析
                </p>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </el-card>

    <!-- 增强的错误提示 -->
    <div v-if="errorInfo" class="error-container">
      <el-alert
        :title="errorInfo.title || '文档分析失败'"
        type="error"
        :closable="true"
        @close="clearError"
        class="error-alert"
        show-icon
      >
        <div class="error-content">
          <p class="error-message">{{ errorInfo.message }}</p>
          
          <!-- 错误详情 -->
          <el-collapse v-if="errorInfo.details" class="error-details">
            <el-collapse-item title="错误详情" name="details">
              <ul class="error-detail-list">
                <li v-for="detail in errorInfo.details" :key="detail">
                  {{ detail }}
                </li>
              </ul>
            </el-collapse-item>
          </el-collapse>
          
          <!-- 解决建议 -->
          <div v-if="errorInfo.suggestions" class="error-suggestions">
            <h4><el-icon><QuestionFilled /></el-icon>解决建议：</h4>
            <ul class="suggestion-list">
              <li v-for="suggestion in errorInfo.suggestions" :key="suggestion">
                {{ suggestion }}
              </li>
            </ul>
          </div>
          
          <!-- 快速操作 -->
          <div class="error-actions">
            <el-button type="primary" size="small" @click="retryAnalysis" :disabled="!selectedFile">
              <el-icon><RefreshRight /></el-icon>
              重新尝试
            </el-button>
            <el-button size="small" @click="clearFile">
              <el-icon><Delete /></el-icon>
              清除文件
            </el-button>
            <el-button size="small" @click="contactSupport">
              <el-icon><Service /></el-icon>
              联系支持
            </el-button>
          </div>
        </div>
      </el-alert>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessageBox, type UploadFile, type UploadFiles, type UploadRawFile } from 'element-plus'
import { showMessage } from '@/utils/message'
import { Document, UploadFilled, MagicStick, Picture, InfoFilled, QuestionFilled, RefreshRight, Delete, Service } from '@element-plus/icons-vue'
import type { AIAnalysisResult, DocumentFormats } from '@/types/ai-analysis'
import { analyzeDocument, getSupportedFormats } from '@/api/ai-analysis'
import { useAIAnalysisStatus } from '@/composables/useAIAnalysisStatus'
import AIServiceStatus from './AIServiceStatus.vue'

interface Props {
  disabled?: boolean
  maxSize?: number // MB
}

interface Emits {
  (e: 'analysis-start'): void
  (e: 'analysis-success', result: AIAnalysisResult): void
  (e: 'analysis-error', error: string): void
  (e: 'analysis-complete'): void
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  maxSize: 10
})

const emit = defineEmits<Emits>()

// AI状态管理
const {
  serviceStatus,
  analysisStatus,
  isServiceAvailable,
  serviceStatusText,
  estimateAnalysisTime,
  startAnalysisTimer,
  stopAnalysisTimer,
  getRetryRecommendation,
  formatTime
} = useAIAnalysisStatus()

// 响应式数据
const uploadRef = ref()
const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const progress = ref(0)
const progressText = ref('')
const currentStep = ref(0)
const errorMessage = ref('')
const errorInfo = ref<any>(null)
const showFormatDetails = ref([])
const smartRetryTimer = ref<number | null>(null)

// 格式支持信息
const formatInfo = ref<DocumentFormats | null>(null)
const aiAvailable = computed(() => 
  (formatInfo.value?.ai_available || false) && isServiceAvailable.value
)
const ocrAvailable = computed(() => formatInfo.value?.document_formats?.availability?.ocr || false)

const documentFormats = computed(() => {
  if (!formatInfo.value) return []
  
  const availability = formatInfo.value.document_formats.availability
  return [
    { ext: 'txt', description: '纯文本文件', available: true },
    { ext: 'pdf', description: 'PDF文档', available: availability.pdf },
    { ext: 'docx', description: 'Word文档', available: availability.docx },
    { ext: 'doc', description: '旧版Word文档', available: availability.docx }
  ]
})

const imageFormats = computed(() => ['png', 'jpg', 'jpeg'])

const supportedFormats = computed(() => {
  const formats = ['TXT']
  if (formatInfo.value?.document_formats?.availability?.pdf) formats.push('PDF')
  if (formatInfo.value?.document_formats?.availability?.docx) formats.push('DOCX', 'DOC')
  if (ocrAvailable.value) formats.push(...imageFormats.value.map(f => f.toUpperCase()))
  return formats
})

const acceptedFormats = computed(() => {
  const extensions = ['.txt']
  if (formatInfo.value?.document_formats?.availability?.pdf) extensions.push('.pdf')
  if (formatInfo.value?.document_formats?.availability?.docx) extensions.push('.docx', '.doc')
  if (ocrAvailable.value) extensions.push('.png', '.jpg', '.jpeg')
  return extensions.join(',')
})

// 生命周期
onMounted(async () => {
  await loadSupportedFormats()
})

// 方法
const loadSupportedFormats = async () => {
  try {
    const response = await getSupportedFormats()
    formatInfo.value = response.formats
    
    if (!response.formats.ai_available) {
      showMessage.warning('AI分析服务当前不可用，请检查配置')
    }
  } catch (error) {
    console.error('Failed to load supported formats:', error)
    showMessage.error('获取支持格式失败')
  }
}

const beforeUpload = (rawFile: UploadRawFile) => {
  // 检查文件大小
  const maxSizeBytes = props.maxSize * 1024 * 1024
  if (rawFile.size > maxSizeBytes) {
    showMessage.error(`文件大小不能超过 ${props.maxSize}MB`)
    return false
  }

  // 检查文件格式
  const fileExt = rawFile.name.split('.').pop()?.toLowerCase()
  const allowedExts = ['txt', 'pdf', 'docx', 'doc', 'png', 'jpg', 'jpeg']
  
  if (!fileExt || !allowedExts.includes(fileExt)) {
    showMessage.error('不支持的文件格式')
    return false
  }

  return true
}

const handleFileChange = (file: UploadFile, fileList: UploadFiles) => {
  if (file.raw) {
    selectedFile.value = file.raw
    clearError()
  }
}

const handleFileRemove = () => {
  selectedFile.value = null
  clearError()
}

const clearFile = () => {
  uploadRef.value?.clearFiles()
  selectedFile.value = null
  clearError()
  clearSmartRetry()
  stopAnalysisTimer()
  resetProgress()
}

const clearError = () => {
  errorMessage.value = ''
  errorInfo.value = null
}

const resetProgress = () => {
  progress.value = 0
  currentStep.value = 0
  progressText.value = ''
}

const updateProgress = (step: number, text: string, percentage?: number) => {
  currentStep.value = step
  progressText.value = text
  
  if (percentage !== undefined) {
    progress.value = percentage
  } else {
    // 根据步骤自动计算进度
    const stepProgress = [10, 40, 85, 100]
    progress.value = stepProgress[step] || 0
  }
}

const startAnalysis = async () => {
  if (!selectedFile.value || !aiAvailable.value) return

  uploading.value = true
  resetProgress()
  emit('analysis-start')

  // 🧠 智能时间估算
  const fileExt = selectedFile.value.name.split('.').pop()?.toLowerCase() || ''
  const estimatedTime = estimateAnalysisTime(selectedFile.value.size, fileExt)
  
  // 显示等待时间信息
  if (serviceStatus.value.estimated_wait_time && serviceStatus.value.estimated_wait_time > 10) {
    showMessage.info(`当前队列较长，预计等待 ${formatTime(serviceStatus.value.estimated_wait_time)}`)
  }

  // 启动智能计时器
  startAnalysisTimer(selectedFile.value.size, fileExt)

  try {
    // 步骤1: 上传文件
    updateProgress(0, '准备上传文件...')
    await new Promise(resolve => setTimeout(resolve, 500))

    // 步骤2: 文档解析
    updateProgress(1, '正在解析文档内容...')
    
    // 步骤3: AI分析
    const analysisText = serviceStatus.value.status === 'degraded' 
      ? '正在进行AI分析 (降级模式)...' 
      : '正在进行AI智能分析...'
    updateProgress(2, analysisText)

    // 调用API进行分析
    const result = await analyzeDocument(selectedFile.value)

    // 步骤4: 完成
    updateProgress(3, '分析完成！', 100)
    
    await new Promise(resolve => setTimeout(resolve, 500))

    if (result.success) {
      stopAnalysisTimer() // 停止计时器
      showMessage.success('文档分析完成！')
      emit('analysis-success', result)
    } else {
      throw new Error(result.error || '分析失败')
    }

  } catch (error: any) {
    stopAnalysisTimer() // 确保停止计时器
    
    // 🧠 智能错误处理和重试建议
    const responseData = error.response?.data || {}
    const errorType = getErrorType(error)
    const retryRec = getRetryRecommendation(errorType)
    
    if (responseData.error_type && responseData.error_details) {
      // 使用后端返回的详细错误信息
      errorInfo.value = {
        title: responseData.error_details?.title || '文档分析失败',
        message: responseData.error || '分析过程中出现错误',
        details: responseData.error_details?.details || [],
        suggestions: [...(responseData.error_details?.suggestions || []), retryRec.reason],
        error_type: responseData.error_type,
        retry_recommendation: retryRec
      }
    } else {
      // 回退到基本错误信息
      const errorMsg = responseData.error || error.message || '分析过程中出现错误'
      errorInfo.value = {
        title: '文档分析失败',
        message: errorMsg,
        details: ['系统遇到了预期之外的问题'],
        suggestions: [
          retryRec.reason,
          '检查文档是否正常',
          '尝试其他格式的文档',
          '联系技术支持'
        ],
        error_type: errorType,
        retry_recommendation: retryRec
      }
    }
    
    // 🤖 智能重试机制
    if (retryRec.shouldRetry && retryRec.retryDelay > 0) {
      setupSmartRetry(retryRec.retryDelay)
    }
    
    showMessage.error(errorInfo.value.message)
    emit('analysis-error', errorInfo.value.message)
    resetProgress()
  } finally {
    uploading.value = false
    emit('analysis-complete')
  }
}

// 🧠 智能错误分析
const getErrorType = (error: any): string => {
  if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
    return 'timeout'
  }
  if (error.code === 'NETWORK_ERROR' || !navigator.onLine) {
    return 'network'
  }
  if (error.response?.status >= 500) {
    return 'server'
  }
  if (error.response?.status === 429) {
    return 'rate_limit'
  }
  return 'unknown'
}

// 🤖 智能重试机制
const setupSmartRetry = (delay: number) => {
  // 清除现有的重试计时器
  if (smartRetryTimer.value) {
    clearTimeout(smartRetryTimer.value)
  }
  
  // 显示倒计时提示
  let countdown = Math.ceil(delay / 1000)
  const countdownInterval = setInterval(() => {
    if (countdown > 0) {
      showMessage.info(`将在 ${countdown} 秒后自动重试...`, { duration: 1000 })
      countdown--
    } else {
      clearInterval(countdownInterval)
    }
  }, 1000)
  
  // 设置重试
  smartRetryTimer.value = window.setTimeout(() => {
    clearInterval(countdownInterval)
    if (selectedFile.value && errorInfo.value?.retry_recommendation?.shouldRetry) {
      showMessage.info('正在自动重试...')
      retryAnalysis()
    }
  }, delay)
}

const retryAnalysis = () => {
  if (selectedFile.value) {
    clearError()
    clearSmartRetry()
    startAnalysis()
  }
}

const clearSmartRetry = () => {
  if (smartRetryTimer.value) {
    clearTimeout(smartRetryTimer.value)
    smartRetryTimer.value = null
  }
}

const contactSupport = () => {
  ElMessageBox.alert(
    '请联系技术支持并提供以下信息：\n\n' +
    `• 错误类型: ${errorInfo.value?.error_type || '未知'}\n` +
    `• 文件名称: ${selectedFile.value?.name || '未知'}\n` +
    `• 文件大小: ${selectedFile.value ? (selectedFile.value.size / 1024 / 1024).toFixed(2) + 'MB' : '未知'}\n` +
    `• 错误信息: ${errorInfo.value?.message || '未知'}\n\n` +
    '技术支持邮箱: support@example.com\n' +
    '技术支持QQ群: 123456789',
    '联系技术支持',
    {
      confirmButtonText: '复制信息',
      showCancelButton: true,
      cancelButtonText: '关闭',
      type: 'info'
    }
  ).then(() => {
    // 复制错误信息到剪贴板
    const supportInfo = `错误类型: ${errorInfo.value?.error_type || '未知'}\n` +
                       `文件名称: ${selectedFile.value?.name || '未知'}\n` +
                       `文件大小: ${selectedFile.value ? (selectedFile.value.size / 1024 / 1024).toFixed(2) + 'MB' : '未知'}\n` +
                       `错误信息: ${errorInfo.value?.message || '未知'}`
    
    if (navigator.clipboard) {
      navigator.clipboard.writeText(supportInfo).then(() => {
        showMessage.success('错误信息已复制到剪贴板')
      })
    } else {
      showMessage.info('请手动复制错误信息')
    }
  }).catch(() => {
    // 用户取消
  })
}

// 暴露方法给父组件
defineExpose({
  clearFile,
  startAnalysis,
  retryAnalysis
})
</script>

<style scoped>
.ai-document-upload {
  width: 100%;
}

.service-status {
  margin-bottom: 20px;
}

.upload-card {
  border: 2px dashed #d9d9d9;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.upload-card:hover {
  border-color: #409EFF;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.upload-area {
  padding: 20px 0;
}

.document-upload {
  width: 100%;
}

.document-upload :deep(.el-upload) {
  width: 100%;
}

.document-upload :deep(.el-upload-dragger) {
  width: 100%;
  height: 200px;
  background: linear-gradient(145deg, #f8fafc 0%, #e2e8f0 100%);
  border: 2px dashed #cbd5e0;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.document-upload :deep(.el-upload-dragger:hover) {
  border-color: #409EFF;
  background: linear-gradient(145deg, #f0f8ff 0%, #e1f5fe 100%);
}

.upload-content {
  text-align: center;
  padding: 20px;
}

.upload-icon {
  font-size: 48px;
  color: #409EFF;
  margin-bottom: 16px;
}

.upload-text p {
  margin: 8px 0;
  color: #606266;
  font-size: 14px;
}

.upload-text em {
  color: #409EFF;
  font-style: normal;
  font-weight: 500;
}

.upload-hint {
  font-size: 12px !important;
  color: #909399 !important;
}

.upload-size {
  font-size: 12px !important;
  color: #F56C6C !important;
}

.upload-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 24px;
}

.analysis-progress {
  margin-top: 32px;
  padding: 24px;
  background: linear-gradient(145deg, #f8fafc 0%, #e2e8f0 100%);
  border-radius: 12px;
  text-align: center;
}

.progress-text {
  margin: 16px 0 24px 0;
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.progress-steps {
  margin-top: 24px;
}

.progress-steps :deep(.el-step__title) {
  font-size: 12px;
}

.format-info {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}

.format-details {
  padding: 16px 0;
}

.format-category {
  margin-bottom: 20px;
}

.format-category h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #303133;
}

.format-tag {
  margin: 0 8px 8px 0;
  position: relative;
}

.format-desc {
  font-size: 10px;
  margin-left: 4px;
  opacity: 0.8;
}

.format-note {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

.error-container {
  margin-top: 16px;
  animation: errorSlideIn 0.3s ease-out;
}

.error-alert {
  border-radius: 8px;
  border: 1px solid #fbc4c4;
  background: linear-gradient(145deg, #fef2f2 0%, #fff5f5 100%);
}

.error-content {
  margin-top: 12px;
}

.error-message {
  font-size: 14px;
  color: #e53e3e;
  font-weight: 500;
  margin: 0 0 16px 0;
  line-height: 1.4;
}

.error-details {
  margin: 16px 0;
}

.error-details :deep(.el-collapse-item__header) {
  font-size: 13px;
  color: #9ca3af;
  background: none;
  border: none;
  padding: 8px 0;
}

.error-detail-list {
  margin: 0;
  padding-left: 20px;
  color: #6b7280;
}

.error-detail-list li {
  margin: 4px 0;
  font-size: 13px;
  line-height: 1.4;
}

.error-suggestions {
  margin: 16px 0;
  padding: 12px;
  background: rgba(59, 130, 246, 0.05);
  border-radius: 6px;
  border-left: 3px solid #3b82f6;
}

.error-suggestions h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #1e40af;
  display: flex;
  align-items: center;
  gap: 6px;
}

.suggestion-list {
  margin: 0;
  padding-left: 20px;
  color: #374151;
}

.suggestion-list li {
  margin: 6px 0;
  font-size: 13px;
  line-height: 1.4;
}

.error-actions {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.error-actions .el-button {
  font-size: 12px;
}

/* 响应式样式 */
@media (max-width: 768px) {
  .upload-actions {
    flex-direction: column;
  }
  
  .upload-actions .el-button {
    width: 100%;
  }
  
  .document-upload :deep(.el-upload-dragger) {
    height: 150px;
  }
  
  .upload-content {
    padding: 10px;
  }
  
  .upload-icon {
    font-size: 36px;
  }
}

/* 动画效果 */
.upload-card {
  animation: fadeInUp 0.5s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.analysis-progress {
  animation: slideInDown 0.3s ease-out;
}

@keyframes slideInDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes errorSlideIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>