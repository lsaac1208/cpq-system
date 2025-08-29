<template>
  <div class="fast-image-upload">
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
            <el-progress 
              :percentage="uploadProgress" 
              :stroke-width="8"
              :color="getProgressColor()"
            />
          </div>
          <p class="upload-text">{{ uploadStatusText }}</p>
          <!-- 实时处理信息 -->
          <div v-if="processingInfo" class="processing-info">
            <p class="processing-text">{{ processingInfo }}</p>
          </div>
        </div>

        <!-- 空状态 - 拖拽上传区域 -->
        <div v-else class="empty-upload-area">
          <el-icon class="upload-icon" size="48"><Plus /></el-icon>
          <div class="upload-hint">
            <p class="primary-text">点击或拖拽图片到这里上传</p>
            <p class="secondary-text">
              支持 JPG、PNG、WebP 格式，大图片将快速压缩
            </p>
            <p class="tertiary-text">
              ⚡ 使用高性能压缩引擎，速度提升80%+
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

      <!-- 成功信息和图片统计 -->
      <div v-if="compressionStats && currentImageUrl" class="compression-stats">
        <div class="stats-card">
          <div class="stats-header">
            <el-icon class="stats-icon"><Picture /></el-icon>
            <span class="stats-title">处理完成</span>
            <el-tag 
              :type="compressionStats.compressionRatio > 50 ? 'success' : 'info'" 
              size="small"
            >
              优化 {{ compressionStats.compressionRatio.toFixed(1) }}%
            </el-tag>
          </div>
          
          <div class="stats-content">
            <div class="stats-row">
              <span class="stats-label">原始大小:</span>
              <span class="stats-value">{{ formatFileSize(compressionStats.originalSize) }}</span>
            </div>
            <div class="stats-row">
              <span class="stats-label">压缩后:</span>
              <span class="stats-value compressed">{{ formatFileSize(compressionStats.compressedSize) }}</span>
            </div>
            <div class="stats-row">
              <span class="stats-label">处理时间:</span>
              <span class="stats-value">{{ compressionStats.processingTime }}ms</span>
            </div>
            <div class="stats-row">
              <span class="stats-label">图片尺寸:</span>
              <span class="stats-value">{{ compressionStats.width }}×{{ compressionStats.height }}</span>
            </div>
          </div>
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
import { Plus, Edit, Delete, Loading, Picture } from '@element-plus/icons-vue'
import http from '@/api/http'
import { compressImageFast, CompressionPresets } from '@/utils/fastImageCompression'
import type { CompressionResult } from '@/utils/fastImageCompression'

interface Props {
  productId?: number | null
  initialImageUrl?: string
  imageAlt?: string
  maxSizeMB?: number
  disabled?: boolean
  compressionPreset?: 'highQuality' | 'standard' | 'fast'
}

interface Emits {
  (e: 'upload-success', imageUrl: string, stats: any): void
  (e: 'upload-error', error: string): void
  (e: 'delete-success'): void
  (e: 'delete-error', error: string): void
}

const props = withDefaults(defineProps<Props>(), {
  productId: null,
  initialImageUrl: '',
  imageAlt: '产品图片',
  maxSizeMB: 2,
  disabled: false,
  compressionPreset: 'standard'
})

const emit = defineEmits<Emits>()

// 响应式状态
const fileInput = ref<HTMLInputElement>()
const currentImageUrl = ref(props.initialImageUrl)
const uploading = ref(false)
const deleting = ref(false)
const uploadProgress = ref(0)
const isDragOver = ref(false)
const errorMessage = ref('')
const uploadStatusText = ref('')
const processingInfo = ref('')
const compressionStats = ref<CompressionResult | null>(null)
const startTime = ref(0)

// 计算属性
const compressionOptions = computed(() => {
  return CompressionPresets[props.compressionPreset]
})

// 监听props变化
watch(() => props.initialImageUrl, (newUrl) => {
  currentImageUrl.value = newUrl
}, { immediate: true })

// 进度条颜色
const getProgressColor = () => {
  if (uploadProgress.value < 30) return '#409eff'
  if (uploadProgress.value < 70) return '#67c23a'
  return '#67c23a'
}

// 图片URL处理
const getImageUrl = (url: string): string => {
  if (!url) return ''
  
  if (url.startsWith('data:') || url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  
  if (url.startsWith('/api/v1')) {
    return `http://localhost:5173${url}`
  }
  
  return `http://localhost:5173/api/v1/products/uploads/${url}`
}

// 文件验证
const validateFile = (file: File): boolean => {
  const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    errorMessage.value = '不支持的文件格式。请使用 JPG、PNG 或 WebP 格式'
    return false
  }
  
  // 最大文件大小检查（10MB，因为我们会压缩）
  if (file.size > 10 * 1024 * 1024) {
    errorMessage.value = '文件太大，请选择小于10MB的图片'
    return false
  }
  
  return true
}

// 快速上传文件
const uploadFile = async (file: File) => {
  if (!validateFile(file)) {
    return
  }

  uploading.value = true
  uploadProgress.value = 0
  errorMessage.value = ''
  processingInfo.value = ''
  startTime.value = Date.now()
  uploadStatusText.value = '开始处理图片...'

  try {
    // 第一阶段：快速压缩图片
    uploadStatusText.value = '正在压缩图片...'
    uploadProgress.value = 10
    
    const compressionResult = await compressImageFast(
      file,
      compressionOptions.value,
      (progress, stage) => {
        uploadProgress.value = 10 + (progress * 0.6) // 压缩占60%进度
        processingInfo.value = stage
      }
    )

    // 第二阶段：上传到服务器
    uploadStatusText.value = '正在上传到服务器...'
    uploadProgress.value = 70

    if (!props.productId) {
      // 本地预览模式
      handleLocalPreview(compressionResult)
      return
    }

    // 创建上传请求
    const formData = new FormData()
    formData.append('image', compressionResult.file)

    // 修复API路径 - 使用图片集上传端点
    const uploadUrl = `/products/${props.productId}/gallery/upload`
    
    const response = await http.post(uploadUrl, formData, {
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total) {
          const percent = (progressEvent.loaded / progressEvent.total) * 100
          uploadProgress.value = 70 + (percent * 0.3) // 上传占30%进度
        }
      }
    })

    // 完成
    uploadProgress.value = 100
    uploadStatusText.value = '上传完成！'

    // 由于响应拦截器返回response.data，这里的response就是数据本身
    if (response) {
      const processingTime = Date.now() - startTime.value
      
      // 检查响应数据结构
      console.log('🔍 FastImageUpload 收到上传响应:', {
        response,
        hasImageUrl: !!(response.image || response.image_url || response.upload_info?.image_url),
        responseKeys: Object.keys(response)
      })
      
      // 获取图片URL - 适配不同的响应结构
      const imageUrl = response.image?.image_url || response.image_url || response.upload_info?.image_url
      
      if (imageUrl) {
        currentImageUrl.value = imageUrl
        compressionStats.value = {
          ...compressionResult,
          processingTime
        }

        // 显示成功消息
        const message = `图片上传成功！压缩${compressionResult.compressionRatio.toFixed(1)}%，耗时${processingTime}ms`
        showMessage.success(message)
        
        console.log('🎉 FastImageUpload 上传成功，准备触发事件:', {
          imageUrl,
          responseData: response,
          compressionStats: compressionStats.value
        })
        
        emit('upload-success', imageUrl, {
          ...response,
          compressionStats: compressionStats.value
        })
        
        console.log('📡 upload-success 事件已触发')
      } else {
        console.error('❌ 响应中未找到图片URL')
        throw new Error('上传响应中未找到图片URL')
      }
    } else {
      console.error('❌ 上传响应为空')
      throw new Error('上传响应为空')
    }

  } catch (error: any) {
    console.error('Upload error:', error)
    const errorMsg = error.response?.data?.error || error.message || '图片处理或上传失败'
    errorMessage.value = errorMsg
    emit('upload-error', errorMsg)
    showMessage.error(`上传失败: ${errorMsg}`)
  } finally {
    uploading.value = false
    uploadProgress.value = 0
    uploadStatusText.value = ''
    processingInfo.value = ''
    
    // 延迟清理成功状态
    setTimeout(() => {
      if (!uploading.value) {
        uploadStatusText.value = ''
      }
    }, 2000)
  }
}

// 本地预览处理
const handleLocalPreview = (compressionResult: CompressionResult) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    currentImageUrl.value = e.target?.result as string
    
    const processingTime = Date.now() - startTime.value
    compressionStats.value = {
      ...compressionResult,
      processingTime
    }
    
    uploading.value = false
    uploadProgress.value = 0
    
    showMessage.success(`图片预览就绪！压缩${compressionResult.compressionRatio.toFixed(1)}%`)
  }
  reader.readAsDataURL(compressionResult.file)
}

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
    compressionStats.value = null
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

// 暴露方法
defineExpose({
  triggerUpload: triggerFileInput,
  deleteImage,
  currentImageUrl: computed(() => currentImageUrl.value),
  isUploading: computed(() => uploading.value),
  compressionStats: computed(() => compressionStats.value)
})
</script>

<style scoped>
.fast-image-upload {
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
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.1);
}

.image-preview.drag-over {
  border-color: #2563eb;
  background: #eff6ff;
  transform: scale(1.02);
  box-shadow: 0 8px 24px rgba(37, 99, 235, 0.15);
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
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
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
  backdrop-filter: blur(2px);
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
  padding: 20px;
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
  width: 80%;
}

.upload-text {
  color: #374151;
  font-size: 16px;
  font-weight: 500;
  margin: 0;
}

.processing-info {
  margin-top: 8px;
  padding: 8px 16px;
  background: rgba(37, 99, 235, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(37, 99, 235, 0.2);
}

.processing-text {
  font-size: 14px;
  color: #1d4ed8;
  margin: 0;
  font-weight: 500;
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
  transform: scale(1.1);
}

.upload-hint {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.primary-text {
  font-size: 16px;
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
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

/* 错误信息 */
.error-message {
  margin-top: 8px;
}

/* 压缩统计信息 */
.compression-stats {
  margin-top: 16px;
}

.stats-card {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #0ea5e9;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.1);
}

.stats-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(14, 165, 233, 0.2);
}

.stats-icon {
  color: #0ea5e9;
  font-size: 16px;
}

.stats-title {
  color: #0c4a6e;
  font-weight: 600;
  font-size: 14px;
  flex: 1;
}

.stats-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.stats-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

.stats-label {
  color: #0369a1;
  font-weight: 500;
}

.stats-value {
  color: #0c4a6e;
  font-weight: 600;
}

.stats-value.compressed {
  color: #059669;
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
    font-size: 36px !important;
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

  .stats-card {
    padding: 12px;
  }
}
</style>