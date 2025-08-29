<template>
  <div class="batch-document-upload">
    <!-- 批量上传区域 -->
    <el-card class="upload-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon><UploadFilled /></el-icon>
            批量文档上传
          </span>
          <span class="file-count" v-if="selectedFiles.length > 0">
            已选择 {{ selectedFiles.length }} 个文件
          </span>
        </div>
      </template>
      
      <!-- 拖拽上传区域 -->
      <el-upload
        ref="uploadRef"
        class="batch-upload-dragger"
        drag
        multiple
        :auto-upload="false"
        :accept="acceptedFormats"
        :file-list="fileList"
        :on-change="handleFileChange"
        :on-remove="handleFileRemove"
        :before-upload="beforeUpload"
        :limit="maxFiles"
        :on-exceed="handleExceed"
      >
        <div class="upload-content">
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <div class="upload-text">
            <p class="primary-text">将文件拖拽到此处，或<em>点击上传</em></p>
            <p class="secondary-text">
              支持 {{ formatsList }} 格式，单个文件最大 {{ maxFileSizeMB }}MB，最多上传 {{ maxFiles }} 个文件
            </p>
          </div>
        </div>
      </el-upload>
      
      <!-- 文件列表 -->
      <div v-if="selectedFiles.length > 0" class="file-list-container">
        <div class="file-list-header">
          <span>文件列表</span>
          <el-button-group size="small">
            <el-button @click="selectAllFiles" :disabled="allSelected">全选</el-button>
            <el-button @click="clearAllFiles">清空</el-button>
          </el-button-group>
        </div>
        
        <div class="file-list">
          <div
            v-for="(file, index) in selectedFiles"
            :key="index"
            class="file-item"
            :class="{ 'file-error': file.status === 'error' }"
          >
            <div class="file-info">
              <el-checkbox
                v-model="file.selected"
                @change="updateSelectedCount"
              />
              <el-icon class="file-icon">
                <Document v-if="isDocumentFile(file.name)" />
                <Picture v-else-if="isImageFile(file.name)" />
                <Files v-else />
              </el-icon>
              <div class="file-details">
                <span class="file-name" :title="file.name">{{ file.name }}</span>
                <span class="file-meta">
                  {{ formatFileSize(file.size) }} • {{ getFileType(file.name) }}
                </span>
              </div>
            </div>
            
            <div class="file-actions">
              <el-tag
                v-if="file.status === 'error'"
                type="danger"
                size="small"
                :title="file.error"
              >
                错误
              </el-tag>
              <el-tag v-else-if="file.status === 'ready'" type="success" size="small">
                就绪
              </el-tag>
              <el-tag v-else type="info" size="small">待检查</el-tag>
              
              <el-button
                link
                size="small"
                @click="removeFile(index)"
                class="remove-btn"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
        
        <!-- 批量操作栏 -->
        <div class="batch-actions">
          <div class="summary-info">
            <span>已选择 {{ selectedCount }} / {{ selectedFiles.length }} 个文件</span>
            <span>总大小：{{ formatFileSize(totalSize) }}</span>
            <span v-if="estimatedTime > 0">预计处理时间：{{ formatDuration(estimatedTime) }}</span>
          </div>
          
          <div class="action-buttons">
            <el-button @click="validateAllFiles" :disabled="processing">
              <el-icon><Check /></el-icon>
              验证文件
            </el-button>
            
            <el-button
              type="primary"
              @click="startBatchAnalysis"
              :disabled="selectedCount === 0 || processing"
              :loading="processing"
            >
              <el-icon><MagicStick /></el-icon>
              开始批量分析 ({{ selectedCount }})
            </el-button>
          </div>
        </div>
      </div>
    </el-card>
    
    <!-- 批量分析设置 -->
    <el-card v-if="selectedFiles.length > 0" class="settings-card">
      <template #header>
        <div class="card-title">
          <el-icon><Setting /></el-icon>
          批量分析设置
        </div>
      </template>
      
      <el-form :model="batchSettings" label-width="120px">
        <el-form-item label="处理优先级">
          <el-select v-model="batchSettings.priority" placeholder="选择优先级">
            <el-option label="普通" value="0" />
            <el-option label="高优先级" value="5" />
            <el-option label="紧急" value="10" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="并发处理">
          <el-switch
            v-model="batchSettings.parallel"
            active-text="启用"
            inactive-text="禁用"
          />
          <span class="help-text">启用后可同时处理多个文件，但会消耗更多资源</span>
        </el-form-item>
        
        <el-form-item label="自动创建产品">
          <el-switch
            v-model="batchSettings.autoCreateProducts"
            active-text="启用"
            inactive-text="禁用"
          />
          <span class="help-text">分析完成后自动创建产品记录</span>
        </el-form-item>
        
        <el-form-item label="质量阈值">
          <el-slider
            v-model="batchSettings.confidenceThreshold"
            :min="0.3"
            :max="1.0"
            :step="0.1"
            :format-tooltip="formatConfidence"
            show-stops
          />
          <span class="help-text">低于此置信度的分析结果将被标记</span>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, nextTick } from 'vue'
import { ElMessageBox, ElNotification } from 'element-plus'
import { showMessage } from '@/utils/message'
import {
  UploadFilled, Document, Picture, Files, Delete, Check,
  MagicStick, Setting
} from '@element-plus/icons-vue'
import type { UploadFile, UploadFiles, UploadRawFile } from 'element-plus'

// Props and Emits
const emit = defineEmits<{
  'analysis-started': [jobId: string]
  'files-selected': [files: File[]]
}>()

// Refs
const uploadRef = ref()
const processing = ref(false)

// 文件管理
const fileList = ref<UploadFiles>([])
const selectedFiles = ref<Array<{
  file: File
  name: string
  size: number
  type: string
  selected: boolean
  status: 'pending' | 'ready' | 'error'
  error?: string
}>>([])

// 批量设置
const batchSettings = reactive({
  priority: '0',
  parallel: true,
  autoCreateProducts: false,
  confidenceThreshold: 0.6
})

// 配置
const maxFiles = 50
const maxFileSize = 10 * 1024 * 1024 // 10MB
const maxFileSizeMB = 10
const supportedFormats = ['txt', 'pdf', 'docx', 'png', 'jpg', 'jpeg']
const acceptedFormats = supportedFormats.map(f => `.${f}`).join(',')
const formatsList = supportedFormats.join(', ')

// 计算属性
const selectedCount = computed(() => 
  selectedFiles.value.filter(f => f.selected).length
)

const totalSize = computed(() => 
  selectedFiles.value
    .filter(f => f.selected)
    .reduce((sum, f) => sum + f.size, 0)
)

const estimatedTime = computed(() => {
  if (selectedCount.value === 0) return 0
  // 估算每个文件15秒处理时间
  return selectedCount.value * 15
})

const allSelected = computed(() => 
  selectedFiles.value.length > 0 && 
  selectedFiles.value.every(f => f.selected)
)

// 文件处理方法
const handleFileChange = (file: UploadFile, files: UploadFiles) => {
  const rawFile = file.raw
  if (!rawFile) return
  
  // 验证文件
  const validation = validateFile(rawFile)
  
  const fileItem = {
    file: rawFile,
    name: rawFile.name,
    size: rawFile.size,
    type: rawFile.type,
    selected: validation.valid,
    status: validation.valid ? 'pending' as const : 'error' as const,
    error: validation.error
  }
  
  selectedFiles.value.push(fileItem)
  
  if (!validation.valid) {
    showMessage.warning(`文件 ${rawFile.name} 验证失败：${validation.error}`)
  }
  
  nextTick(() => {
    updateSelectedCount()
  })
}

const handleFileRemove = (file: UploadFile) => {
  const index = selectedFiles.value.findIndex(f => f.name === file.name)
  if (index !== -1) {
    removeFile(index)
  }
}

const removeFile = (index: number) => {
  selectedFiles.value.splice(index, 1)
  updateSelectedCount()
}

const beforeUpload = (file: UploadRawFile) => {
  // 阻止自动上传
  return false
}

const handleExceed = (files: File[]) => {
  showMessage.warning(`最多只能选择 ${maxFiles} 个文件，当前选择了 ${files.length} 个文件`)
}

// 文件验证
const validateFile = (file: File) => {
  // 检查文件大小
  if (file.size > maxFileSize) {
    return {
      valid: false,
      error: `文件大小超出限制 (${maxFileSizeMB}MB)`
    }
  }
  
  // 检查文件格式
  const extension = getFileExtension(file.name).toLowerCase()
  if (!supportedFormats.includes(extension)) {
    return {
      valid: false,
      error: `不支持的文件格式 (${extension})`
    }
  }
  
  // 检查文件名
  if (file.name.length > 255) {
    return {
      valid: false,
      error: '文件名过长'
    }
  }
  
  return { valid: true }
}

// 批量操作
const selectAllFiles = () => {
  selectedFiles.value.forEach(file => {
    if (file.status !== 'error') {
      file.selected = true
    }
  })
  updateSelectedCount()
}

const clearAllFiles = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有文件吗？此操作不可撤销。',
      '确认清空',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    selectedFiles.value = []
    fileList.value = []
    uploadRef.value?.clearFiles()
    
    showMessage.success('已清空所有文件')
  } catch {
    // 用户取消
  }
}

const updateSelectedCount = () => {
  const selected = selectedFiles.value.filter(f => f.selected)
  emit('files-selected', selected.map(f => f.file))
}

const validateAllFiles = async () => {
  processing.value = true
  
  try {
    let validCount = 0
    let errorCount = 0
    
    selectedFiles.value.forEach(file => {
      if (file.status === 'pending') {
        const validation = validateFile(file.file)
        if (validation.valid) {
          file.status = 'ready'
          validCount++
        } else {
          file.status = 'error'
          file.error = validation.error
          file.selected = false
          errorCount++
        }
      } else if (file.status === 'ready') {
        validCount++
      } else {
        errorCount++
      }
    })
    
    if (errorCount > 0) {
      showMessage.warning(`验证完成：${validCount} 个文件就绪，${errorCount} 个文件有错误`)
    } else {
      showMessage.success(`验证完成：所有 ${validCount} 个文件都已就绪`)
    }
    
    updateSelectedCount()
  } finally {
    processing.value = false
  }
}

const startBatchAnalysis = async () => {
  if (selectedCount.value === 0) {
    showMessage.warning('请至少选择一个文件进行分析')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要开始批量分析 ${selectedCount.value} 个文件吗？\n预计处理时间：${formatDuration(estimatedTime.value)}`,
      '确认批量分析',
      {
        confirmButtonText: '开始分析',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    
    processing.value = true
    
    // 准备提交数据
    const selectedFileList = selectedFiles.value
      .filter(f => f.selected && f.status === 'ready')
      .map(f => f.file)
    
    const formData = new FormData()
    
    // 添加文件
    selectedFileList.forEach(file => {
      formData.append('files', file)
    })
    
    // 添加设置
    formData.append('settings', JSON.stringify({
      priority: parseInt(batchSettings.priority),
      parallel: batchSettings.parallel,
      autoCreateProducts: batchSettings.autoCreateProducts,
      confidenceThreshold: batchSettings.confidenceThreshold
    }))
    
    // 提交批量分析任务
    const response = await fetch('/api/v1/batch-analysis/submit', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`
      },
      body: formData
    })
    
    const result = await response.json()
    
    if (result.success) {
      ElNotification({
        title: '批量分析已开始',
        message: `任务ID: ${result.job_id}，预计完成时间: ${formatDuration(result.estimated_duration)}`,
        type: 'success',
        duration: 5000
      })
      
      // 自动开始处理
      await startProcessing(result.job_id)
      
      emit('analysis-started', result.job_id)
      
      // 清空文件列表
      setTimeout(() => {
        clearAllFiles()
      }, 1000)
      
    } else {
      throw new Error(result.error || '提交失败')
    }
    
  } catch (error: any) {
    showMessage.error(`批量分析失败: ${error.message}`)
  } finally {
    processing.value = false
  }
}

const startProcessing = async (jobId: string) => {
  try {
    const response = await fetch(`/api/v1/batch-analysis/jobs/${jobId}/start`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
        'Content-Type': 'application/json'
      }
    })
    
    const result = await response.json()
    
    if (!result.success) {
      throw new Error(result.error || '启动处理失败')
    }
    
  } catch (error: any) {
    showMessage.error(`启动处理失败: ${error.message}`)
  }
}

// 工具方法
const getAuthToken = () => {
  return localStorage.getItem('auth_token') || ''
}

const formatFileSize = (size: number) => {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

const formatDuration = (seconds: number) => {
  if (seconds < 60) return `${seconds} 秒`
  if (seconds < 3600) return `${Math.round(seconds / 60)} 分钟`
  return `${Math.round(seconds / 3600)} 小时`
}

const formatConfidence = (value: number) => {
  return `${Math.round(value * 100)}%`
}

const getFileExtension = (filename: string) => {
  return filename.split('.').pop() || ''
}

const getFileType = (filename: string) => {
  const ext = getFileExtension(filename).toLowerCase()
  const types: Record<string, string> = {
    'txt': '文本文档',
    'pdf': 'PDF文档',
    'docx': 'Word文档',
    'png': 'PNG图片',
    'jpg': 'JPEG图片',
    'jpeg': 'JPEG图片'
  }
  return types[ext] || ext.toUpperCase()
}

const isDocumentFile = (filename: string) => {
  const ext = getFileExtension(filename).toLowerCase()
  return ['txt', 'pdf', 'docx'].includes(ext)
}

const isImageFile = (filename: string) => {
  const ext = getFileExtension(filename).toLowerCase()
  return ['png', 'jpg', 'jpeg'].includes(ext)
}
</script>

<style scoped>
.batch-document-upload {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.upload-card, .settings-card {
  margin-bottom: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
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

.file-count {
  color: #909399;
  font-size: 14px;
}

.batch-upload-dragger {
  width: 100%;
}

.batch-upload-dragger :deep(.el-upload-dragger) {
  width: 100%;
  height: 180px;
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  background: #fafafa;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.batch-upload-dragger :deep(.el-upload-dragger:hover) {
  border-color: #409eff;
  background: #f0f9ff;
}

.upload-content {
  text-align: center;
}

.upload-icon {
  font-size: 48px;
  color: #c0c4cc;
  margin-bottom: 16px;
}

.primary-text {
  font-size: 16px;
  color: #606266;
  margin: 0 0 8px 0;
}

.primary-text em {
  color: #409eff;
  font-style: normal;
}

.secondary-text {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.file-list-container {
  margin-top: 24px;
  border-top: 1px solid #ebeef5;
  padding-top: 20px;
}

.file-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  font-weight: 600;
  color: #303133;
}

.file-list {
  max-height: 400px;
  overflow-y: auto;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  margin-bottom: 8px;
  transition: all 0.3s ease;
}

.file-item:hover {
  background: #f5f7fa;
  border-color: #d3d4d6;
}

.file-item.file-error {
  border-color: #f56c6c;
  background: #fef0f0;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.file-icon {
  font-size: 20px;
  color: #909399;
  flex-shrink: 0;
}

.file-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  flex: 1;
}

.file-name {
  font-weight: 500;
  color: #303133;
  truncate;
  word-break: break-all;
}

.file-meta {
  font-size: 12px;
  color: #909399;
}

.file-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.remove-btn {
  color: #f56c6c;
  padding: 4px;
}

.batch-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.summary-info {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: #606266;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.help-text {
  font-size: 12px;
  color: #909399;
  margin-left: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .batch-document-upload {
    padding: 16px;
  }
  
  .batch-actions {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .summary-info {
    flex-direction: column;
    gap: 8px;
  }
  
  .action-buttons {
    justify-content: stretch;
  }
  
  .action-buttons .el-button {
    flex: 1;
  }
}
</style>