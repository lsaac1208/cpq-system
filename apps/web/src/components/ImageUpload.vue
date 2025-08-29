<template>
  <div class="image-upload-container">
    <!-- 图片预览区域 -->
    <div class="image-preview-area">
      <div 
        class="image-preview" 
        :class="{ 
          'has-image': currentImageUrl, 
          'drag-over': isDragOver,
          'uploading': uploading 
        }"
        @dragover.prevent="handleDragOver"
        @dragleave.prevent="handleDragLeave"
        @drop.prevent="handleDrop"
        @click="triggerFileInput"
      >
        <!-- 已有图片显示 -->
        <div v-if="currentImageUrl && !uploading" class="image-display">
          <img 
            :src="getImageUrl(currentImageUrl)" 
            :alt="imageAlt || '产品图片'"
            class="preview-image"
            @error="handleImageError"
          />
          <div class="image-overlay">
            <div class="overlay-actions">
              <el-button 
                type="primary" 
                size="small" 
                @click.stop="triggerFileInput"
              >
                <el-icon><Edit /></el-icon>
                更换图片
              </el-button>
              <el-button 
                type="danger" 
                size="small" 
                @click.stop="deleteImage"
                :disabled="deleting"
              >
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </div>
          </div>
        </div>

        <!-- 上传中状态 -->
        <div v-else-if="uploading" class="uploading-state">
          <el-icon class="uploading-icon"><Loading /></el-icon>
          <div class="upload-progress">
            <el-progress :percentage="Math.min(100, Math.max(0, Math.floor(uploadProgress || 0)))" />
          </div>
          <p class="upload-text">{{ uploadStatusText }}</p>
          <!-- 压缩信息显示 -->
          <div v-if="compressionInfo" class="compression-info">
            <p class="compression-text">{{ compressionInfo }}</p>
          </div>
        </div>

        <!-- 空状态 - 拖拽上传区域 -->
        <div v-else class="empty-upload-area">
          <el-icon class="upload-icon" size="48"><Plus /></el-icon>
          <div class="upload-hint">
            <p class="primary-text">点击或拖拽图片到这里上传</p>
            <p class="secondary-text">
              支持 JPG、PNG、WebP 格式，大图片将自动压缩
            </p>
            <p class="tertiary-text">
              推荐上传高质量图片，系统会自动优化
            </p>
          </div>
        </div>
      </div>

      <!-- 错误信息 -->
      <div v-if="errorMessage" class="error-message">
        <el-alert
          :title="errorMessage"
          type="error"
          :closable="true"
          @close="errorMessage = ''"
          show-icon
        />
      </div>

      <!-- 图片信息 -->
      <div v-if="imageInfo && currentImageUrl" class="image-info">
        <div class="info-item">
          <span class="info-label">文件名:</span>
          <span class="info-value">{{ imageInfo.original_filename }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">文件大小:</span>
          <span class="info-value">{{ formatFileSize(imageInfo.file_size) }}</span>
        </div>
        <div v-if="imageInfo.compressed_size && imageInfo.original_size !== imageInfo.compressed_size" class="info-item compression-summary">
          <span class="info-label">压缩信息:</span>
          <span class="info-value">
            {{ formatFileSize(imageInfo.original_size) }} → 
            {{ formatFileSize(imageInfo.compressed_size) }}
            <span class="compression-ratio">({{ imageInfo.compression_ratio }})</span>
          </span>
        </div>
        <div class="info-item">
          <span class="info-label">上传时间:</span>
          <span class="info-value">{{ formatDate(imageInfo.upload_time) }}</span>
        </div>
      </div>
    </div>

    <!-- 隐藏的文件输入 -->
    <input
      ref="fileInput"
      type="file"
      accept="image/jpeg,image/jpg,image/png,image/webp"
      @change="handleFileSelect"
      style="display: none"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessageBox } from 'element-plus'
import { showMessage } from '@/utils/message'
import { Plus, Edit, Delete, Loading } from '@element-plus/icons-vue'
import http from '@/api/http'
import imageCompression from 'browser-image-compression'

interface Props {
  productId?: number | null
  initialImageUrl?: string
  imageAlt?: string
  maxSizeMB?: number
  disabled?: boolean
}

interface Emits {
  (e: 'upload-success', imageUrl: string, imageInfo: any): void
  (e: 'upload-error', error: string): void
  (e: 'delete-success'): void
  (e: 'delete-error', error: string): void
  (e: 'file-selected', file: File): void
}

const props = withDefaults(defineProps<Props>(), {
  productId: null,
  initialImageUrl: '',
  imageAlt: '产品图片',
  maxSizeMB: 2,
  disabled: false
})

const emit = defineEmits<Emits>()

// 响应式状态
const fileInput = ref<HTMLInputElement>()
const currentImageUrl = ref(props.initialImageUrl)
const uploading = ref(false)
const deleting = ref(false)
const uploadProgress = ref(0) // 确保初始化为数值 0-100
const isDragOver = ref(false)
const errorMessage = ref('')
const imageInfo = ref<any>(null)
const isCompressing = ref(false)
const uploadStatusText = ref('正在上传图片...')
const compressionInfo = ref('')

// 计算属性
const maxFileSize = computed(() => props.maxSizeMB * 1024 * 1024) // 转换为字节

// 监听props变化
watch(() => props.initialImageUrl, (newUrl) => {
  currentImageUrl.value = newUrl
}, { immediate: true })

// 图片URL处理
const getImageUrl = (url: string): string => {
  if (!url) return ''
  
  // 如果是Base64数据URL，直接返回（用于本地预览）
  if (url.startsWith('data:')) {
    return url
  }
  
  // 如果是完整URL，直接返回
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  
  // 如果是API路径（以/api/v1开头），直接返回完整URL
  if (url.startsWith('/api/v1')) {
    return `${http.defaults.baseURL.replace('/api/v1', '')}${url}`
  }
  
  // 如果是相对路径（以/uploads开头），构建完整URL
  if (url.startsWith('/uploads')) {
    return `${http.defaults.baseURL}${url}`
  }
  
  // 默认情况：假设是文件名，构建完整路径
  return `${http.defaults.baseURL}/uploads/products/compressed/${url}`
}

// 文件验证（仅验证格式，大小问题通过压缩解决）
const validateFile = (file: File): boolean => {
  // 检查文件类型
  const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    errorMessage.value = '不支持的文件格式。请使用 JPG、PNG 或 WebP 格式'
    return false
  }

  return true
}

// 图片压缩函数
const compressImage = async (file: File): Promise<File> => {
  // 如果文件已经小于2MB，直接返回
  if (file.size <= maxFileSize.value) {
    return file
  }

  isCompressing.value = true
  uploadStatusText.value = '正在压缩图片...'
  
  const originalSize = (file.size / (1024 * 1024)).toFixed(2)
  compressionInfo.value = `原文件大小: ${originalSize}MB`

  try {
    const options = {
      maxSizeMB: props.maxSizeMB, // 最大文件大小
      maxWidthOrHeight: 1920, // 最大宽度或高度
      useWebWorker: true, // 使用Web Worker避免阻塞主线程
      quality: 0.8, // 压缩质量
      fileType: file.type, // 保持原格式
      onProgress: (progress: number) => {
        // 压缩进度更新
        uploadProgress.value = Math.floor(progress * 40) // 压缩占40%进度
        uploadStatusText.value = `正在压缩图片... ${Math.floor(progress * 100)}%`
      }
    }

    const compressedFile = await imageCompression(file, options)
    const compressedSize = (compressedFile.size / (1024 * 1024)).toFixed(2)
    const compressionRatio = ((1 - compressedFile.size / file.size) * 100).toFixed(1)
    
    compressionInfo.value = `压缩完成: ${originalSize}MB → ${compressedSize}MB (减少${compressionRatio}%)`
    
    // 如果压缩后仍然超过大小限制，尝试更激进的压缩
    if (compressedFile.size > maxFileSize.value) {
      const aggressiveOptions = {
        maxSizeMB: props.maxSizeMB * 0.8, // 更严格的大小限制
        maxWidthOrHeight: 1600, // 更小的尺寸
        useWebWorker: true,
        quality: 0.7, // 更低的质量
        fileType: 'image/jpeg', // 强制转换为JPEG格式以获得更好的压缩
        onProgress: (progress: number) => {
          uploadProgress.value = 40 + Math.floor(progress * 30) // 二次压缩占30%进度
          uploadStatusText.value = `正在进一步压缩... ${Math.floor(progress * 100)}%`
        }
      }
      
      const finalCompressed = await imageCompression(file, aggressiveOptions)
      const finalSize = (finalCompressed.size / (1024 * 1024)).toFixed(2)
      const finalRatio = ((1 - finalCompressed.size / file.size) * 100).toFixed(1)
      
      compressionInfo.value = `深度压缩完成: ${originalSize}MB → ${finalSize}MB (减少${finalRatio}%)`
      
      return finalCompressed
    }
    
    return compressedFile
  } catch (error) {
    console.error('压缩图片失败:', error)
    throw new Error('图片压缩失败，请尝试选择更小的图片')
  } finally {
    isCompressing.value = false
    uploadProgress.value = 70 // 压缩完成，进入上传阶段
    uploadStatusText.value = '压缩完成，开始上传...'
  }
}

// 上传文件
const uploadFile = async (file: File) => {
  if (!validateFile(file)) {
    return
  }

  uploading.value = true
  uploadProgress.value = 0
  errorMessage.value = ''
  compressionInfo.value = ''
  uploadStatusText.value = '开始处理图片...'

  try {
    // 压缩图片（如果需要）
    const processedFile = await compressImage(file)
    
    // 如果没有产品ID，先本地预览，等产品创建后再上传
    if (!props.productId) {
      handleLocalPreview(processedFile)
      return
    }

    // 上传阶段
    uploadStatusText.value = '正在上传到服务器...'
    uploadProgress.value = 70

    // 创建上传进度模拟
    const progressInterval = setInterval(() => {
      if (uploadProgress.value < 95) {
        uploadProgress.value += Math.random() * 5
      }
    }, 200)

    const formData = new FormData()
    formData.append('image', processedFile)

    const response = await http.post(
      `/products/${props.productId}/gallery/upload`,
      formData
      // Note: Content-Type header is automatically handled by request interceptor for FormData
    )

    // 完成进度
    uploadProgress.value = 100
    uploadStatusText.value = '上传完成！'

    if (response.data) {
      currentImageUrl.value = response.data.image_url
      imageInfo.value = {
        ...response.data.file_info,
        upload_time: new Date().toISOString(),
        original_size: file.size,
        compressed_size: processedFile.size,
        compression_ratio: processedFile.size !== file.size ? 
          ((1 - processedFile.size / file.size) * 100).toFixed(1) + '%' : '无压缩'
      }

      // 显示成功消息，包含压缩信息
      const message = processedFile.size !== file.size ? 
        `图片上传成功！压缩比例: ${((1 - processedFile.size / file.size) * 100).toFixed(1)}%` :
        '图片上传成功！'
      
      showMessage.success(message)
      emit('upload-success', response.data.image_url, response.data)
    }

    clearInterval(progressInterval)
    
  } catch (error: any) {
    console.error('Upload error:', error)
    const errorMsg = error.message || error.response?.data?.error || '图片处理或上传失败'
    errorMessage.value = errorMsg
    emit('upload-error', errorMsg)
    showMessage.error(errorMsg)
  } finally {
    uploading.value = false
    uploadProgress.value = 0
    uploadStatusText.value = '正在上传图片...'
    compressionInfo.value = ''
    // 延迟清理，让用户看到完成状态
    setTimeout(() => {
      if (!uploading.value) {
        uploadStatusText.value = '正在上传图片...'
      }
    }, 2000)
  }
}

// 本地预览处理（创建模式）
const pendingFile = ref<File | null>(null)

const handleLocalPreview = (file: File) => {
  pendingFile.value = file
  
  // 创建本地预览URL
  const reader = new FileReader()
  reader.onload = (e) => {
    currentImageUrl.value = e.target?.result as string
    imageInfo.value = {
      original_filename: file.name,
      file_size: file.size,
      upload_time: new Date().toISOString()
    }
    
    uploading.value = false
    uploadProgress.value = 0
    uploadStatusText.value = '正在上传图片...'
    compressionInfo.value = ''
    
    // 通知父组件有文件待上传
    emit('file-selected', file)
  }
  reader.readAsDataURL(file)
}

// 当产品创建后，上传暂存的文件
const uploadPendingFile = async (productId: string) => {
  if (!pendingFile.value) return
  
  const formData = new FormData()
  formData.append('image', pendingFile.value)
  
  try {
    const response = await http.post(
      `/products/${productId}/gallery/upload`,
      formData
      // Note: Content-Type header is automatically handled by request interceptor for FormData
    )
    
    if (response.data) {
      currentImageUrl.value = response.data.image_url
      pendingFile.value = null
      return response.data.image_url
    }
  } catch (error) {
    console.error('上传暂存文件失败:', error)
    throw error
  }
}

// 暂时移除，将在文件末尾统一处理

// 删除图片
const deleteImage = async () => {
  if (!props.productId || !currentImageUrl.value) {
    return
  }

  try {
    await ElMessageBox.confirm(
      '确定要删除这张图片吗？删除后无法恢复。',
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )

    deleting.value = true

    await http.delete(`/products/${props.productId}/delete-image`)

    currentImageUrl.value = ''
    imageInfo.value = null
    errorMessage.value = ''

    showMessage.success('图片删除成功')
    emit('delete-success')

  } catch (error: any) {
    if (error !== 'cancel') {
      const errorMsg = error.response?.data?.error || '图片删除失败'
      errorMessage.value = errorMsg
      emit('delete-error', errorMsg)
      showMessage.error(errorMsg)
    }
  } finally {
    deleting.value = false
  }
}

// 事件处理
const triggerFileInput = () => {
  if (props.disabled || uploading.value) return
  fileInput.value?.click()
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  
  if (file) {
    uploadFile(file)
  }
  
  // 重置文件输入
  target.value = ''
}

const handleDragOver = (event: DragEvent) => {
  if (props.disabled || uploading.value) return
  
  event.preventDefault()
  isDragOver.value = true
}

const handleDragLeave = () => {
  isDragOver.value = false
}

const handleDrop = (event: DragEvent) => {
  if (props.disabled || uploading.value) return
  
  event.preventDefault()
  isDragOver.value = false
  
  const files = event.dataTransfer?.files
  if (files && files.length > 0) {
    uploadFile(files[0])
  }
}

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.src = '/images/default-product.svg'
}

// 工具函数
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleString('zh-CN')
}

// 暴露方法供父组件调用
defineExpose({
  triggerUpload: triggerFileInput,
  deleteImage,
  uploadPendingFile,
  currentImageUrl: computed(() => currentImageUrl.value),
  isUploading: computed(() => uploading.value)
})
</script>

<style scoped>
.image-upload-container {
  width: 100%;
}

.image-preview-area {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.image-preview {
  position: relative;
  width: 100%;
  height: 280px;
  border: 2px dashed #d1d5db;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fafafa;
}

.image-preview:hover {
  border-color: #2563eb;
  background: #f8fafc;
}

.image-preview.drag-over {
  border-color: #2563eb;
  background: #eff6ff;
  transform: scale(1.02);
}

.image-preview.has-image {
  border: 1px solid #e5e7eb;
  cursor: default;
}

.image-preview.uploading {
  border-color: #2563eb;
  background: #f0f9ff;
}

/* 图片显示 */
.image-display {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 8px;
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.image-display:hover .image-overlay {
  opacity: 1;
}

.overlay-actions {
  display: flex;
  gap: 12px;
}

/* 上传中状态 */
.uploading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
}

.uploading-icon {
  font-size: 32px;
  color: #2563eb;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.upload-progress {
  width: 60%;
}

.upload-text {
  color: #374151;
  font-size: 14px;
  margin: 0;
}

/* 空状态 */
.empty-upload-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
  padding: 40px;
  text-align: center;
}

.upload-icon {
  color: #9ca3af;
  transition: color 0.3s ease;
}

.image-preview:hover .upload-icon {
  color: #2563eb;
}

.upload-hint {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.primary-text {
  font-size: 16px;
  color: #374151;
  font-weight: 500;
  margin: 0;
}

.secondary-text {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.tertiary-text {
  font-size: 12px;
  color: #9ca3af;
  margin: 4px 0 0 0;
  font-style: italic;
}

/* 错误信息 */
.error-message {
  margin-top: 8px;
}

/* 图片信息 */
.image-info {
  background: #f9fafb;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #e5e7eb;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  font-size: 14px;
}

.info-item:not(:last-child) {
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 8px;
  margin-bottom: 4px;
}

.info-label {
  color: #6b7280;
  font-weight: 500;
}

.info-value {
  color: #374151;
  font-weight: 400;
}

/* 压缩信息样式 */
.compression-info {
  margin-top: 8px;
  padding: 8px 12px;
  background: #f0f9ff;
  border-radius: 6px;
  border-left: 3px solid #3b82f6;
}

.compression-text {
  font-size: 12px;
  color: #1e40af;
  margin: 0;
  font-weight: 500;
}

.compression-summary {
  background: #f0f9ff;
  padding: 8px 12px;
  border-radius: 6px;
  border-left: 3px solid #10b981;
}

.compression-summary .info-label {
  color: #059669;
}

.compression-summary .info-value {
  color: #065f46;
  font-weight: 500;
}

.compression-ratio {
  color: #10b981;
  font-weight: 600;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .image-preview {
    height: 200px;
  }

  .empty-upload-area {
    padding: 30px 20px;
  }

  .upload-icon {
    font-size: 36px;
  }

  .primary-text {
    font-size: 14px;
  }

  .secondary-text {
    font-size: 12px;
  }

  .overlay-actions {
    flex-direction: column;
    gap: 8px;
  }
}
</style>