<template>
  <div class="batch-image-upload">
    <!-- 批量上传配置 -->
    <div class="upload-config">
      <el-form :model="config" label-width="100px" size="small">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="图片类型">
              <el-select v-model="config.image_type" style="width: 100%">
                <el-option label="产品图" value="product" />
                <el-option label="细节图" value="detail" />
                <el-option label="使用图" value="usage" />
                <el-option label="对比图" value="comparison" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="自动主图">
              <el-switch
                v-model="config.auto_set_primary"
                active-text="首张设为主图"
                inactive-text="不设主图"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </div>

    <!-- 拖拽上传区域 -->
    <div 
      class="upload-area"
      :class="{ 
        'drag-over': isDragOver,
        'uploading': uploading
      }"
      @drop="handleDrop"
      @dragover.prevent="handleDragOver"
      @dragleave.prevent="handleDragLeave"
      @click="triggerFileInput"
    >
      <div v-if="!uploading && files.length === 0" class="upload-hint">
        <el-icon class="upload-icon" size="48"><Plus /></el-icon>
        <div class="hint-text">
          <p class="primary-text">拖拽多张图片到这里或点击选择</p>
          <p class="secondary-text">支持 JPG、PNG、WebP 格式，最多同时上传10张</p>
          <p class="tertiary-text">批量上传将自动压缩优化，提升加载速度</p>
        </div>
      </div>

      <div v-else-if="uploading" class="uploading-state">
        <el-icon class="uploading-icon" size="32"><Loading /></el-icon>
        <div class="upload-progress">
          <el-progress 
            :percentage="overallProgress"
            :stroke-width="8"
            color="#67c23a"
          />
        </div>
        <p class="upload-text">{{ uploadStatus }}</p>
      </div>

      <div v-else class="files-preview">
        <h4>待上传文件 ({{ files.length }}/10)</h4>
        
        <div class="files-grid">
          <div
            v-for="(file, index) in files"
            :key="index"
            class="file-item"
            :class="{ 
              'uploading': file.uploading,
              'success': file.success,
              'error': file.error
            }"
          >
            <div class="file-preview">
              <img
                v-if="file.preview"
                :src="file.preview"
                :alt="file.name"
                class="preview-image"
              />
              <div v-else class="no-preview">
                <el-icon><Picture /></el-icon>
              </div>
              
              <!-- 状态覆盖层 -->
              <div v-if="file.uploading" class="status-overlay uploading">
                <el-icon class="status-icon"><Loading /></el-icon>
                <span class="status-text">处理中...</span>
              </div>
              
              <div v-else-if="file.success" class="status-overlay success">
                <el-icon class="status-icon"><Check /></el-icon>
                <span class="status-text">成功</span>
              </div>
              
              <div v-else-if="file.error" class="status-overlay error">
                <el-icon class="status-icon"><Close /></el-icon>
                <span class="status-text">失败</span>
              </div>
            </div>

            <div class="file-info">
              <div class="file-name">{{ file.name }}</div>
              <div class="file-meta">
                <span class="file-size">{{ formatFileSize(file.size) }}</span>
                <el-button
                  v-if="!uploading"
                  type="danger"
                  size="small"
                  text
                  @click="removeFile(index)"
                >
                  移除
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="upload-actions">
          <el-button @click="addMoreFiles">
            <el-icon><Plus /></el-icon>
            继续添加
          </el-button>
          <el-button @click="clearFiles">
            <el-icon><Delete /></el-icon>
            清空全部
          </el-button>
          <el-button 
            type="primary" 
            :loading="uploading"
            @click="startUpload"
            :disabled="files.length === 0"
          >
            <el-icon><Upload /></el-icon>
            开始上传 ({{ files.length }})
          </el-button>
        </div>
      </div>
    </div>

    <!-- 上传结果 -->
    <div v-if="uploadResults.length > 0" class="upload-results">
      <h4>上传结果</h4>
      
      <div class="results-summary">
        <el-alert
          :title="`上传完成: 成功 ${successCount} 个，失败 ${failedCount} 个`"
          :type="failedCount === 0 ? 'success' : 'warning'"
          :closable="false"
          show-icon
        />
      </div>

      <div class="results-detail">
        <el-collapse>
          <el-collapse-item title="查看详细结果" name="details">
            <div class="results-list">
              <div
                v-for="(result, index) in uploadResults"
                :key="index"
                class="result-item"
                :class="{ success: result.success, error: !result.success }"
              >
                <div class="result-icon">
                  <el-icon v-if="result.success" class="success-icon"><Check /></el-icon>
                  <el-icon v-else class="error-icon"><Close /></el-icon>
                </div>
                <div class="result-content">
                  <div class="result-filename">{{ result.filename }}</div>
                  <div v-if="result.success" class="result-success">
                    上传成功
                    <el-tag v-if="result.image?.is_primary" size="small" type="warning">主图</el-tag>
                  </div>
                  <div v-else class="result-error">{{ result.error }}</div>
                </div>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </div>

    <!-- 隐藏的文件输入 -->
    <input
      ref="fileInput"
      type="file"
      accept="image/jpeg,image/jpg,image/png,image/webp"
      multiple
      @change="handleFileSelect"
      style="display: none"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
// ElMessage removed
import { showMessage } from '@/utils/message'
import {
  Plus, Loading, Picture, Check, Close, Upload, Delete
} from '@element-plus/icons-vue'
import http from '@/api/http'

interface UploadFile {
  file: File
  name: string
  size: number
  preview?: string
  uploading?: boolean
  success?: boolean
  error?: string
}

interface UploadResult {
  filename: string
  success: boolean
  error?: string
  image?: any
}

interface Props {
  productId: number
  maxFiles?: number
}

interface Emits {
  (e: 'upload-complete', results: UploadResult[]): void
}

const props = withDefaults(defineProps<Props>(), {
  maxFiles: 10
})

const emit = defineEmits<Emits>()

// 响应式状态
const fileInput = ref<HTMLInputElement>()
const files = ref<UploadFile[]>([])
const uploading = ref(false)
const uploadResults = ref<UploadResult[]>([])
const isDragOver = ref(false)
const overallProgress = ref(0)
const uploadStatus = ref('')

// 配置
const config = ref({
  image_type: 'product',
  auto_set_primary: false
})

// 计算属性
const successCount = computed(() => uploadResults.value.filter(r => r.success).length)
const failedCount = computed(() => uploadResults.value.filter(r => !r.success).length)

// 方法
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const validateFile = (file: File): boolean => {
  const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
  
  if (!allowedTypes.includes(file.type)) {
    showMessage.error(`文件 ${file.name} 格式不支持，请选择 JPG、PNG 或 WebP 格式`)
    return false
  }
  
  if (file.size > 10 * 1024 * 1024) {
    showMessage.error(`文件 ${file.name} 过大，请选择小于10MB的图片`)
    return false
  }
  
  return true
}

const createFilePreview = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => resolve(e.target?.result as string)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

const addFiles = async (newFiles: File[]) => {
  const validFiles: File[] = []
  
  // 验证文件
  for (const file of newFiles) {
    if (validateFile(file)) {
      validFiles.push(file)
    }
  }
  
  // 检查总数限制
  const totalFiles = files.value.length + validFiles.length
  if (totalFiles > props.maxFiles) {
    const allowedCount = props.maxFiles - files.value.length
    validFiles.splice(allowedCount)
    showMessage.warning(`最多只能上传 ${props.maxFiles} 张图片，已自动限制为 ${allowedCount} 张`)
  }
  
  // 添加文件并生成预览
  for (const file of validFiles) {
    const uploadFile: UploadFile = {
      file,
      name: file.name,
      size: file.size
    }
    
    try {
      uploadFile.preview = await createFilePreview(file)
    } catch (error) {
      console.warn(`生成预览失败: ${file.name}`)
    }
    
    files.value.push(uploadFile)
  }
  
  if (validFiles.length > 0) {
    showMessage.success(`添加了 ${validFiles.length} 张图片`)
  }
}

const removeFile = (index: number) => {
  files.value.splice(index, 1)
}

const clearFiles = () => {
  files.value = []
  uploadResults.value = []
  overallProgress.value = 0
  uploadStatus.value = ''
}

const addMoreFiles = () => {
  triggerFileInput()
}

const triggerFileInput = () => {
  if (uploading.value) return
  fileInput.value?.click()
}

const handleFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const selectedFiles = Array.from(target.files || [])
  
  if (selectedFiles.length > 0) {
    await addFiles(selectedFiles)
  }
  
  target.value = ''
}

const handleDragOver = (event: DragEvent) => {
  if (uploading.value) return
  event.preventDefault()
  isDragOver.value = true
}

const handleDragLeave = () => {
  isDragOver.value = false
}

const handleDrop = async (event: DragEvent) => {
  if (uploading.value) return
  
  event.preventDefault()
  isDragOver.value = false
  
  const droppedFiles = Array.from(event.dataTransfer?.files || [])
  if (droppedFiles.length > 0) {
    await addFiles(droppedFiles)
  }
}

const startUpload = async () => {
  if (files.value.length === 0) return
  
  uploading.value = true
  uploadResults.value = []
  overallProgress.value = 0
  uploadStatus.value = '准备上传...'
  
  try {
    // 准备FormData
    const formData = new FormData()
    
    files.value.forEach((uploadFile) => {
      formData.append('images', uploadFile.file)
    })
    
    // 添加配置参数
    formData.append('image_type', config.value.image_type)
    formData.append('auto_set_primary', config.value.auto_set_primary.toString())
    
    uploadStatus.value = '上传中...'
    
    // 发送批量上传请求
    const response = await http.post(
      `/products/${props.productId}/gallery/batch-upload`,
      formData,
      {
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percent = (progressEvent.loaded / progressEvent.total) * 100
            overallProgress.value = Math.round(percent)
            uploadStatus.value = `上传中... ${Math.round(percent)}%`
          }
        }
      }
    )
    
    uploadStatus.value = '处理完成'
    overallProgress.value = 100
    
    // 处理结果
    uploadResults.value = response.data.results || []
    
    // 更新文件状态
    files.value.forEach((uploadFile, index) => {
      const result = uploadResults.value.find(r => r.filename === uploadFile.file.name)
      if (result) {
        uploadFile.success = result.success
        uploadFile.error = result.error
      }
    })
    
    // 显示结果消息
    const message = response.data.message || `上传完成: 成功 ${successCount.value} 个，失败 ${failedCount.value} 个`
    
    if (failedCount.value === 0) {
      showMessage.success(message)
    } else {
      showMessage.warning(message)
    }
    
    // 通知父组件
    emit('upload-complete', uploadResults.value)
    
  } catch (error: any) {
    console.error('批量上传失败:', error)
    uploadStatus.value = '上传失败'
    
    const errorMessage = error.response?.data?.error || '批量上传失败'
    showMessage.error(errorMessage)
    
    // 标记所有文件为失败
    files.value.forEach(uploadFile => {
      uploadFile.error = errorMessage
    })
    
  } finally {
    uploading.value = false
    
    setTimeout(() => {
      if (!uploading.value) {
        uploadStatus.value = ''
      }
    }, 3000)
  }
}
</script>

<style scoped>
.batch-image-upload {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 配置区域 */
.upload-config {
  background: #f8fafc;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

/* 上传区域 */
.upload-area {
  min-height: 300px;
  border: 2px dashed #d1d5db;
  border-radius: 12px;
  background: #fafafa;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  padding: 24px;
}

.upload-area:hover {
  border-color: #2563eb;
  background: #f8fafc;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.1);
}

.upload-area.drag-over {
  border-color: #2563eb;
  background: #eff6ff;
  transform: scale(1.02);
  box-shadow: 0 8px 24px rgba(37, 99, 235, 0.15);
}

.upload-area.uploading {
  border-color: #10b981;
  background: #f0fdf4;
  cursor: default;
}

/* 上传提示 */
.upload-hint {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.upload-icon {
  color: #9ca3af;
  transition: color 0.3s ease;
}

.upload-area:hover .upload-icon {
  color: #2563eb;
  transform: scale(1.1);
}

.hint-text {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.primary-text {
  font-size: 18px;
  color: #374151;
  font-weight: 600;
  margin: 0;
}

.secondary-text {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.tertiary-text {
  font-size: 12px;
  color: #10b981;
  margin: 4px 0 0 0;
  font-weight: 500;
}

/* 上传中状态 */
.uploading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  text-align: center;
}

.uploading-icon {
  color: #10b981;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.upload-progress {
  width: 300px;
}

.upload-text {
  color: #374151;
  font-size: 16px;
  font-weight: 500;
  margin: 0;
}

/* 文件预览 */
.files-preview {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.files-preview h4 {
  margin: 0;
  font-size: 16px;
  color: #374151;
  text-align: center;
}

.files-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.file-item {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.file-item:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
}

.file-item.success {
  border-color: #10b981;
}

.file-item.error {
  border-color: #ef4444;
}

.file-preview {
  position: relative;
  height: 120px;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: cover;
}

.no-preview {
  color: #9ca3af;
  font-size: 32px;
}

/* 状态覆盖层 */
.status-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: white;
  font-size: 12px;
  font-weight: 600;
}

.status-overlay.uploading {
  background: rgba(16, 185, 129, 0.8);
}

.status-overlay.success {
  background: rgba(16, 185, 129, 0.8);
}

.status-overlay.error {
  background: rgba(239, 68, 68, 0.8);
}

.status-icon {
  font-size: 20px;
}

.status-text {
  text-align: center;
}

/* 文件信息 */
.file-info {
  padding: 12px;
}

.file-name {
  font-size: 12px;
  font-weight: 500;
  color: #374151;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}

.file-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.file-size {
  font-size: 11px;
  color: #6b7280;
}

/* 操作按钮 */
.upload-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

/* 上传结果 */
.upload-results {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.upload-results h4 {
  margin: 0;
  font-size: 16px;
  color: #374151;
}

.results-summary {
  margin-bottom: 8px;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 6px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
}

.result-item.success {
  border-color: #10b981;
  background: #f0fdf4;
}

.result-item.error {
  border-color: #ef4444;
  background: #fef2f2;
}

.result-icon {
  flex-shrink: 0;
}

.success-icon {
  color: #10b981;
}

.error-icon {
  color: #ef4444;
}

.result-content {
  flex: 1;
  min-width: 0;
}

.result-filename {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.result-success {
  font-size: 12px;
  color: #10b981;
  display: flex;
  align-items: center;
  gap: 8px;
}

.result-error {
  font-size: 12px;
  color: #ef4444;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .upload-area {
    min-height: 200px;
    padding: 16px;
  }

  .files-grid {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 12px;
  }

  .file-preview {
    height: 80px;
  }

  .upload-actions {
    justify-content: stretch;
  }

  .upload-actions .el-button {
    flex: 1;
  }
}
</style>