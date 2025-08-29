<template>
  <div class="product-gallery" :class="{ 'edit-mode': editMode }">
    <!-- 主图展示区域 -->
    <div class="main-display">
      <div class="main-image-container" :class="{ 'edit-mode': editMode }">
        <!-- 图片加载状态 -->
        <div v-if="loading" class="image-loading">
          <el-skeleton animated>
            <template #template>
              <el-skeleton-item variant="image" style="width: 100%; height: 400px;" />
            </template>
          </el-skeleton>
        </div>

        <!-- 主图显示 -->
        <div v-else-if="currentImage" class="main-image-wrapper">
          <img
            :src="getImageUrl(currentImage.image_url)"
            :alt="currentImage.alt_text || currentImage.title || '产品图片'"
            class="main-image"
            :class="{ 'edit-mode': editMode }"
            @load="onImageLoad"
            @error="onImageError"
            @click="!editMode && openPreview()"
          />
          
          <!-- 编辑模式覆盖层 -->
          <div v-if="editMode && currentImage" class="edit-overlay">
            <div class="edit-actions">
              <el-button 
                type="primary" 
                size="small"
                :icon="Edit"
                @click.stop="replaceMainImage"
              >
                更换主图
              </el-button>
              <el-button 
                type="warning" 
                size="small"
                :icon="Star"
                v-if="!currentImage.is_primary"
                @click.stop="setAsPrimary(currentImage.id)"
              >
                设为主图
              </el-button>
              <el-button 
                type="danger" 
                size="small"
                :icon="Delete"
                @click.stop="deleteImage(currentImage.id)"
                :disabled="deleting"
              >
                删除
              </el-button>
            </div>
          </div>

          <!-- 图片信息覆盖层（查看模式） -->
          <div v-else-if="!editMode && showImageInfo && currentImage" class="image-overlay">
            <div class="image-info">
              <h4 v-if="currentImage.title">{{ currentImage.title }}</h4>
              <p v-if="currentImage.description">{{ currentImage.description }}</p>
              <div class="image-meta">
                <span class="image-type">{{ getImageTypeLabel(currentImage.image_type) }}</span>
                <span v-if="currentImage.is_primary" class="primary-badge">主图</span>
              </div>
            </div>
          </div>

          <!-- 导航箭头（查看模式） -->
          <div v-if="!editMode && Array.isArray(images) && images.length > 1" class="navigation-arrows">
            <button
              class="nav-arrow prev"
              :disabled="currentIndex === 0"
              @click="prevImage"
            >
              <el-icon><ArrowLeft /></el-icon>
            </button>
            <button
              class="nav-arrow next"
              :disabled="currentIndex === images.length - 1"
              @click="nextImage"
            >
              <el-icon><ArrowRight /></el-icon>
            </button>
          </div>

          <!-- 图片计数器 -->
          <div v-if="Array.isArray(images) && images.length > 1" class="image-counter">
            {{ currentIndex + 1 }} / {{ images.length }}
          </div>
        </div>

        <!-- 空状态或拖拽上传区域 -->
        <div 
          v-else 
          class="empty-state"
          :class="{ 
            'edit-mode': editMode,
            'drag-over': isDragOver,
            'uploading': uploading 
          }"
          @dragover.prevent="editMode && handleDragOver"
          @dragleave.prevent="editMode && handleDragLeave"
          @drop.prevent="editMode && handleDrop"
          @click="editMode && triggerFileInput"
        >
          <!-- 上传中状态 -->
          <div v-if="uploading" class="uploading-state">
            <el-icon class="uploading-icon"><Loading /></el-icon>
            <div class="upload-progress">
              <el-progress 
                :percentage="uploadProgress" 
                :stroke-width="8"
                color="#2563eb"
              />
            </div>
            <p class="upload-text">{{ uploadStatusText }}</p>
            <div v-if="processingInfo" class="processing-info">
              <p class="processing-text">{{ processingInfo }}</p>
            </div>
          </div>
          
          <!-- 空状态 -->
          <div v-else>
            <el-icon class="empty-icon" size="48">
              <Picture v-if="!editMode" />
              <Plus v-else />
            </el-icon>
            <div class="empty-hint">
              <p class="empty-text">
                {{ editMode ? '点击或拖拽图片到这里上传' : '暂无产品图片' }}
              </p>
              <p v-if="editMode" class="upload-hint">
                支持 JPG、PNG、WebP 格式，大图片将快速压缩
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="main-actions">
        <el-button-group>
          <!-- 查看模式按钮 -->
          <template v-if="!editMode">
            <el-button
              v-if="currentImage"
              :icon="ZoomIn"
              @click="openPreview"
            >
              放大查看
            </el-button>
            <el-button
              :icon="InfoFilled"
              @click="toggleImageInfo"
            >
              {{ showImageInfo ? '隐藏信息' : '显示信息' }}
            </el-button>
            <el-button
              v-if="canEdit"
              :icon="Edit"
              @click="openManageDialog"
            >
              管理图片
            </el-button>
          </template>
          
          <!-- 编辑模式按钮 -->
          <template v-else>
            <el-button
              :icon="Plus"
              @click="triggerFileInput"
            >
              添加图片
            </el-button>
            <el-button
              v-if="Array.isArray(images) && images.length > 0"
              :icon="Sort"
              @click="toggleSortMode"
            >
              {{ sortMode ? '完成排序' : '排序图片' }}
            </el-button>
            <el-button
              v-if="stats"
              :icon="InfoFilled"
              @click="showGalleryStats = true"
            >
              统计信息
            </el-button>
          </template>
        </el-button-group>
      </div>
    </div>

    <!-- 缩略图区域 -->
    <div v-if="Array.isArray(images) && images.length > 0" class="thumbnails-section">
      <h4 class="thumbnails-title" :class="{ 'edit-mode': editMode }">
        {{ editMode ? '管理图片' : '所有图片' }} ({{ Array.isArray(images) ? images.length : 0 }})
        <el-tag v-if="stats" size="small" type="info">
          {{ formatFileSize(stats.total_size) }}
        </el-tag>
      </h4>
      
      <div class="thumbnails-container" :class="{ 'sort-mode': sortMode, 'edit-mode': editMode }">
        <!-- 编辑模式提示 -->
        <div v-if="editMode && !uploading && Array.isArray(images) && images.length > 0" class="edit-mode-hint">
          <el-icon><InfoFilled /></el-icon>
          <span>
            {{ sortMode ? '拖拽图片进行排序，完成后点击“完成排序”' : '点击图片上的按钮进行编辑操作' }}
          </span>
        </div>
        
        <div class="thumbnails-scroll" :class="{ 'edit-mode': editMode }">
          <!-- 编辑模式：支持拖拽排序 -->
          <template v-if="editMode">
            <div
              v-for="(image, index) in images"
              :key="image.id"
              class="thumbnail-item"
              :class="{
                active: index === currentIndex,
                primary: image.is_primary,
                'edit-mode': true,
                'sort-mode': sortMode
              }"
              @click="!sortMode && selectImage(index)"
              :draggable="sortMode"
              @dragstart="onDragStart(index, $event)"
              @dragover="onDragOver($event)"
              @drop="onDrop(index, $event)"
              @dragend="onDragEnd"
            >
              <div class="thumbnail-wrapper">
                <!-- 拖拽手柄 -->
                <div v-if="sortMode" class="sort-handle">
                  <el-icon><Rank /></el-icon>
                </div>
                
                <!-- 缩略图 -->
                <img
                  :src="getImageUrl(image.thumbnail_url || image.image_url)"
                  :alt="image.title || `图片 ${index + 1}`"
                  class="thumbnail-image"
                  @error="onThumbnailError"
                />
                
                <!-- 编辑模式控制按钮 -->
                <div v-if="editMode && !sortMode" class="thumbnail-controls">
                  <el-button
                    size="small"
                    type="primary"
                    :icon="Star"
                    v-if="!image.is_primary"
                    @click.stop="setAsPrimary(image.id)"
                    title="设为主图"
                    class="control-btn"
                  />
                  <el-button
                    size="small"
                    type="danger"
                    :icon="Delete"
                    @click.stop="deleteImage(image.id)"
                    :disabled="deleting"
                    title="删除图片"
                    class="control-btn"
                  />
                </div>

                <!-- 主图标识 -->
                <div v-if="image.is_primary" class="primary-indicator">
                  <el-icon><Star /></el-icon>
                </div>

                <!-- 图片类型标识 -->
                <div class="type-indicator">
                  {{ getImageTypeLabel(image.image_type) }}
                </div>
              </div>
              
              <!-- 缩略图信息 -->
              <div class="thumbnail-info">
                <span class="thumbnail-title">{{ image.title || `图片 ${index + 1}` }}</span>
                <div v-if="editMode" class="thumbnail-meta">
                  <span class="file-size">{{ formatFileSize(image.file_size || 0) }}</span>
                </div>
              </div>
            </div>
          </template>
          
          <!-- 查看模式：普通显示 -->
          <template v-else>
            <div
              v-for="(image, index) in images"
              :key="image.id"
              class="thumbnail-item"
              :class="{
                active: index === currentIndex,
                primary: image.is_primary
              }"
              @click="selectImage(index)"
            >
              <div class="thumbnail-wrapper">
                <img
                  :src="getImageUrl(image.thumbnail_url || image.image_url)"
                  :alt="image.title || `图片 ${index + 1}`"
                  class="thumbnail-image"
                  @error="onThumbnailError"
                />
                
                <!-- 主图标识 -->
                <div v-if="image.is_primary" class="primary-indicator">
                  <el-icon><Star /></el-icon>
                </div>

                <!-- 图片类型标识 -->
                <div class="type-indicator">
                  {{ getImageTypeLabel(image.image_type) }}
                </div>
              </div>
              
              <div class="thumbnail-info">
                <span class="thumbnail-title">{{ image.title || `图片 ${index + 1}` }}</span>
              </div>
            </div>
          </template>
        </div>
        
        <!-- 滚动控制按钮 -->
        <button
          v-if="showScrollControls"
          class="scroll-control left"
          @click="scrollThumbnails('left')"
        >
          <el-icon><ArrowLeft /></el-icon>
        </button>
        <button
          v-if="showScrollControls"
          class="scroll-control right"
          @click="scrollThumbnails('right')"
        >
          <el-icon><ArrowRight /></el-icon>
        </button>
      </div>
    </div>

    <!-- 全屏预览对话框 -->
    <el-dialog
      v-model="previewVisible"
      :title="currentImage?.title || '图片预览'"
      width="90%"
      align-center
      class="preview-dialog"
      :before-close="closePreview"
    >
      <div class="preview-content">
        <div class="preview-image-container">
          <img
            v-if="currentImage"
            :src="getImageUrl(currentImage.image_url)"
            :alt="currentImage.alt_text || currentImage.title"
            class="preview-image"
            :style="previewImageStyle"
            @wheel="onPreviewWheel"
            @mousedown="startDrag"
            @mousemove="onDrag"
            @mouseup="endDrag"
            @mouseleave="endDrag"
          />
        </div>

        <!-- 预览控制栏 -->
        <div class="preview-controls">
          <el-button-group>
            <el-button :icon="ZoomIn" @click="zoomIn">放大</el-button>
            <el-button :icon="ZoomOut" @click="zoomOut">缩小</el-button>
            <el-button :icon="RefreshRight" @click="resetZoom">重置</el-button>
            <el-button :icon="Download" @click="downloadImage">下载</el-button>
          </el-button-group>

          <div class="zoom-info">
            {{ Math.round(zoomLevel * 100) }}%
          </div>
        </div>

        <!-- 预览导航 -->
        <div v-if="Array.isArray(images) && images.length > 1" class="preview-navigation">
          <el-button
            :disabled="currentIndex === 0"
            @click="prevImage"
          >
            <el-icon><ArrowLeft /></el-icon>
            上一张
          </el-button>
          <span class="preview-counter">
            {{ currentIndex + 1 }} / {{ Array.isArray(images) ? images.length : 0 }}
          </span>
          <el-button
            :disabled="!Array.isArray(images) || currentIndex === images.length - 1"
            @click="nextImage"
          >
            下一张
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 图片管理对话框 -->
    <ProductGalleryManager
      v-if="manageDialogVisible"
      v-model:visible="manageDialogVisible"
      :product-id="productId"
      :images="images"
      @refresh="refreshGallery"
    />

    <!-- 统计信息对话框 -->
    <el-dialog
      v-model="showGalleryStats"
      title="图片集统计"
      width="500px"
      align-center
    >
      <div v-if="stats" class="stats-content">
        <div class="stats-item">
          <span class="stats-label">图片总数：</span>
          <span class="stats-value">{{ stats.total_images }} 张</span>
        </div>
        <div class="stats-item">
          <span class="stats-label">总大小：</span>
          <span class="stats-value">{{ formatFileSize(stats.total_size) }}</span>
        </div>
        <div class="stats-item">
          <span class="stats-label">主图设置：</span>
          <span class="stats-value">{{ stats.has_primary ? '已设置' : '未设置' }}</span>
        </div>
        <div class="stats-item">
          <span class="stats-label">图片类型：</span>
          <div class="type-breakdown">
            <div v-for="(count, type) in stats.by_type" :key="type" class="type-item">
              <el-tag size="small">{{ getImageTypeLabel(type) }}</el-tag>
              <span>{{ count }} 张</span>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

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
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessageBox } from 'element-plus'
import { showMessage } from '@/utils/message'
import {
  ArrowLeft, ArrowRight, Picture, ZoomIn, ZoomOut, RefreshRight,
  Download, Star, Edit, InfoFilled, Plus, Delete, Loading, Sort, Rank
} from '@element-plus/icons-vue'
import http from '@/api/http'
import ProductGalleryManager from './ProductGalleryManager.vue'
import { compressImageFast, CompressionPresets } from '@/utils/fastImageCompression'
import type { CompressionResult } from '@/utils/fastImageCompression'

interface ProductImage {
  id: number
  product_id: number
  filename: string
  original_filename?: string
  image_url: string
  thumbnail_url?: string
  title?: string
  description?: string
  alt_text?: string
  file_size?: number
  width?: number
  height?: number
  format?: string
  sort_order: number
  is_primary: boolean
  is_active: boolean
  image_type: string
  created_at: string
  updated_at: string
}

interface GalleryStats {
  total_images: number
  total_size: number
  by_type: Record<string, number>
  has_primary: boolean
  primary_image_id?: number
}

interface Props {
  productId: number
  editMode?: boolean
  autoLoad?: boolean
  showControls?: boolean
  canEdit?: boolean
  height?: string | number
}

const props = withDefaults(defineProps<Props>(), {
  editMode: false,
  autoLoad: true,
  showControls: true,
  canEdit: false,
  height: '400px'
})

const emit = defineEmits<{
  refresh: []
  imageChange: [imageUrl: string]
  imagesUpdate: [images: ProductImage[]]
}>()

// 响应式状态
const loading = ref(false)
const images = ref<ProductImage[]>([])
const currentIndex = ref(0)
const stats = ref<GalleryStats | null>(null)
const showImageInfo = ref(false)
const previewVisible = ref(false)
const manageDialogVisible = ref(false)
const showGalleryStats = ref(false)
const sortMode = ref(false)

// 上传相关状态
const uploading = ref(false)
const deleting = ref(false)
const uploadProgress = ref(0)
const isDragOver = ref(false)
const uploadStatusText = ref('')
const processingInfo = ref('')
const fileInput = ref<HTMLInputElement>()

// 预览相关状态
const zoomLevel = ref(1)
const previewOffset = ref({ x: 0, y: 0 })
const isDragging = ref(false)
const lastMousePos = ref({ x: 0, y: 0 })

// 缩略图滚动控制
const showScrollControls = ref(false)

// 排序相关状态

// 计算属性
const currentImage = computed(() => {
  if (!Array.isArray(images.value) || images.value.length === 0) {
    return null
  }
  
  const index = currentIndex.value
  if (index < 0 || index >= images.value.length) {
    return null
  }
  
  return images.value[index] || null
})

const previewImageStyle = computed(() => {
  return {
    transform: `scale(${zoomLevel.value}) translate(${previewOffset.value.x}px, ${previewOffset.value.y}px)`,
    cursor: isDragging.value ? 'grabbing' : 'grab'
  }
})

// 方法
const getImageUrl = (url: string): string => {
  if (!url) return '/images/default-product.svg'
  
  // 如果是完整的URL，直接返回
  if (url.startsWith('data:') || url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  
  // 如果是API路径，直接返回让Vite代理处理
  if (url.startsWith('/api/v1')) {
    return url
  }
  
  // 如果是相对路径的文件名，构造完整的API路径
  if (!url.startsWith('/')) {
    return `/api/v1/products/uploads/${url}`
  }
  
  return url
}

const getImageTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    'product': '产品图',
    'detail': '细节图',
    'usage': '使用图',
    'comparison': '对比图'
  }
  return labels[type] || '产品图'
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const loadGallery = async () => {
  if (!props.productId) {
    console.warn('⚠️ 加载图片集: productId 未提供')
    return
  }
  
  console.log('🔄 开始加载图片集', { productId: props.productId })
  loading.value = true
  
  try {
    const response = await http.get(`/products/${props.productId}/gallery`)
    
    // 由于响应拦截器返回response.data，这里的response就是数据本身
    const responseData = response
    const responseImages = responseData?.images
    
    console.log('🔍 API响应数据:', {
      hasResponseData: !!responseData,
      responseDataKeys: responseData ? Object.keys(responseData) : [],
      responseImagesType: typeof responseImages,
      responseImagesLength: Array.isArray(responseImages) ? responseImages.length : 'not array',
      sampleImage: Array.isArray(responseImages) && responseImages.length > 0 ? responseImages[0] : null
    })
    
    images.value = Array.isArray(responseImages) ? responseImages : []
    
    console.log('📋 图片集加载结果:', {
      imageCount: images.value.length,
      images: images.value.map(img => ({ id: img.id, filename: img.filename, is_primary: img.is_primary }))
    })
    
    // 如果有主图，设置为当前显示图片
    if (responseData?.primary_image && images.value.length > 0) {
      const primaryIndex = images.value.findIndex(img => img && img.is_primary)
      if (primaryIndex >= 0) {
        currentIndex.value = primaryIndex
        console.log('🎯 设置主图索引:', primaryIndex)
      }
    }
    
    // 加载统计信息
    try {
      const statsResponse = await http.get(`/products/${props.productId}/gallery/stats`)
      stats.value = statsResponse || null
      console.log('📊 统计信息加载成功:', stats.value)
    } catch (statsError) {
      console.warn('📊 加载统计信息失败:', statsError)
      stats.value = null
    }
    
    emit('imagesUpdate', images.value)
    console.log('✅ 图片集数据已更新，事件已触发')
    
    // 强制触发响应式更新
    await nextTick()
    console.log('🔄 响应式更新完成，当前images长度:', images.value.length)
    
  } catch (error: any) {
    console.error('❌ 加载图片集失败:', error)
    console.error('📊 错误详情:', {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status,
      url: error.config?.url
    })
    
    // 确保images始终是数组
    images.value = []
    emit('imagesUpdate', [])
    
    // 只在非404错误时显示错误信息
    if (error.response?.status !== 404) {
      showMessage.error(error.response?.data?.error || '加载图片集失败')
    } else {
      console.log('ℹ️ 图片集不存在或为空 (404)，这是正常情况')
    }
  } finally {
    loading.value = false
    console.log('🏁 图片集加载流程结束')
  }
}

const selectImage = (index: number) => {
  if (!Array.isArray(images.value) || index < 0 || index >= images.value.length) {
    return
  }
  
  currentIndex.value = index
  const image = images.value[index]
  if (image && image.image_url) {
    emit('imageChange', image.image_url)
  }
}

const prevImage = () => {
  if (!Array.isArray(images.value) || images.value.length === 0) {
    return
  }
  
  if (currentIndex.value > 0) {
    currentIndex.value--
  }
}

const nextImage = () => {
  if (!Array.isArray(images.value) || images.value.length === 0) {
    return
  }
  
  if (currentIndex.value < images.value.length - 1) {
    currentIndex.value++
  }
}

const openPreview = () => {
  if (currentImage.value) {
    previewVisible.value = true
    resetZoom()
  }
}

const closePreview = () => {
  previewVisible.value = false
  resetZoom()
}

const toggleImageInfo = () => {
  showImageInfo.value = !showImageInfo.value
}

const openManageDialog = () => {
  manageDialogVisible.value = true
}

// 编辑模式方法
const validateFile = (file: File): boolean => {
  const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    showMessage.error('不支持的文件格式。请使用 JPG、PNG 或 WebP 格式')
    return false
  }
  
  if (file.size > 10 * 1024 * 1024) {
    showMessage.error('文件太大，请选择小于10MB的图片')
    return false
  }
  
  return true
}

const uploadFiles = async (files: FileList) => {
  console.log('🚀 开始批量上传文件', {
    totalFiles: files.length,
    productId: props.productId,
    editMode: props.editMode
  })

  const validFiles = Array.from(files).filter(validateFile)
  console.log('📋 文件验证结果:', {
    original: files.length,
    valid: validFiles.length,
    validNames: validFiles.map(f => f.name)
  })
  
  if (validFiles.length === 0) {
    console.warn('⚠️ 没有有效的文件可上传')
    showMessage.warning('请选择有效的图片文件')
    return
  }

  uploading.value = true
  uploadProgress.value = 0
  processingInfo.value = ''
  uploadStatusText.value = '开始处理图片...'

  try {
    console.log('📦 开始处理', validFiles.length, '个文件')
    
    const uploadPromises = validFiles.map(async (file, index) => {
      console.log(`📸 处理文件 ${index + 1}/${validFiles.length}:`, file.name)
      uploadStatusText.value = `正在处理图片 ${index + 1}/${validFiles.length}...`
      
      // 压缩图片
      const compressionResult = await compressImageFast(
        file,
        CompressionPresets.standard,
        (progress, stage) => {
          const baseProgress = (index / validFiles.length) * 100
          const currentProgress = (progress / validFiles.length) * 60
          uploadProgress.value = baseProgress + currentProgress
          processingInfo.value = stage
        }
      )

      console.log(`✅ 文件压缩完成:`, file.name, {
        originalSize: file.size,
        compressedSize: compressionResult.file.size,
        compressionRatio: ((1 - compressionResult.file.size / file.size) * 100).toFixed(1) + '%'
      })

      // 上传到服务器
      const formData = new FormData()
      formData.append('image', compressionResult.file)
      formData.append('image_type', 'product')

      console.log(`🌐 开始上传文件:`, file.name, 'to', `/products/${props.productId}/gallery/upload`)

      const response = await http.post(
        `/products/${props.productId}/gallery/upload`, 
        formData
      )

      console.log(`✅ 文件上传成功:`, file.name, response.data)
      return response.data
    })

    const results = await Promise.all(uploadPromises)
    console.log('🎉 所有文件上传完成:', results)
    
    uploadProgress.value = 100
    uploadStatusText.value = '上传完成！'
    
    showMessage.success(`成功上传 ${validFiles.length} 张图片`)
    
    // 重新加载图片集
    console.log('🔄 重新加载图片集...')
    await loadGallery()
    console.log('✅ 图片集重新加载完成')
    
    // 触发刷新事件，通知父组件
    emit('refresh')
    console.log('📡 已触发refresh事件通知父组件')

  } catch (error: any) {
    console.error('❌ 批量上传失败:', error)
    console.error('📊 错误详情:', {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status,
      url: error.config?.url
    })
    
    const errorMessage = error.response?.data?.error || error.message || '图片上传失败'
    showMessage.error(errorMessage)
  } finally {
    uploading.value = false
    uploadProgress.value = 0
    uploadStatusText.value = ''
    processingInfo.value = ''
    console.log('🏁 上传流程结束')
  }
}

const triggerFileInput = () => {
  console.log('🔍 triggerFileInput 调用', {
    editMode: props.editMode,
    uploading: uploading.value,
    fileInputRef: !!fileInput.value
  })
  
  if (!props.editMode) {
    console.warn('⚠️ 编辑模式未开启，无法上传文件')
    return
  }
  
  if (uploading.value) {
    console.warn('⚠️ 正在上传中，请等待当前上传完成')
    return
  }
  
  if (!fileInput.value) {
    console.error('❌ 文件输入元素未找到')
    return
  }
  
  fileInput.value.click()
}

const handleFileSelect = (event: Event) => {
  console.log('📁 文件选择事件触发')
  
  const target = event.target as HTMLInputElement
  const files = target.files
  
  console.log('📋 选择的文件信息:', {
    fileCount: files?.length || 0,
    files: files ? Array.from(files).map(f => ({ name: f.name, size: f.size, type: f.type })) : []
  })
  
  if (files && files.length > 0) {
    uploadFiles(files)
  } else {
    console.warn('⚠️ 未选择任何文件')
  }
  
  // 清空文件输入，允许重复选择同一文件
  target.value = ''
}

const handleDragOver = (event: DragEvent) => {
  if (!props.editMode) {
    console.log('🚫 拖拽被阻止: 编辑模式未开启')
    return
  }
  
  if (uploading.value) {
    console.log('🚫 拖拽被阻止: 正在上传中')
    return
  }
  
  event.preventDefault()
  isDragOver.value = true
  console.log('✅ 拖拽悬停状态激活')
}

const handleDragLeave = () => {
  isDragOver.value = false
  console.log('📤 拖拽离开区域')
}

const handleDrop = (event: DragEvent) => {
  console.log('🎯 拖拽放置事件触发', {
    editMode: props.editMode,
    uploading: uploading.value
  })
  
  if (!props.editMode) {
    console.warn('⚠️ 拖拽放置被阻止: 编辑模式未开启')
    return
  }
  
  if (uploading.value) {
    console.warn('⚠️ 拖拽放置被阻止: 正在上传中')
    return
  }
  
  event.preventDefault()
  isDragOver.value = false
  
  const files = event.dataTransfer?.files
  console.log('📦 拖拽的文件信息:', {
    fileCount: files?.length || 0,
    files: files ? Array.from(files).map(f => ({ name: f.name, size: f.size, type: f.type })) : []
  })
  
  if (files && files.length > 0) {
    uploadFiles(files)
  } else {
    console.warn('⚠️ 拖拽放置: 未检测到文件')
  }
}

const setAsPrimary = async (imageId: number) => {
  console.log('🎯 设置主图:', { imageId, productId: props.productId })
  
  try {
    await http.put(`/products/${props.productId}/gallery/${imageId}/primary`)
    showMessage.success('主图设置成功')
    
    console.log('✅ 主图设置成功，重新加载图片集')
    await loadGallery()
    
    // 触发刷新事件
    emit('refresh')
    console.log('📡 已触发refresh事件')
    
  } catch (error: any) {
    console.error('❌ 设置主图失败:', error)
    showMessage.error(error.response?.data?.error || '设置主图失败')
  }
}

const deleteImage = async (imageId: number) => {
  console.log('🗑️ 删除图片:', { imageId, productId: props.productId })
  
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

    await http.delete(`/products/${props.productId}/gallery/${imageId}`)
    
    showMessage.success('图片删除成功')
    console.log('✅ 图片删除成功，重新加载图片集')
    await loadGallery()
    
    // 触发刷新事件
    emit('refresh')
    console.log('📡 已触发refresh事件')

  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('❌ 删除图片失败:', error)
      showMessage.error(error.response?.data?.error || '图片删除失败')
    }
  } finally {
    deleting.value = false
  }
}

const replaceMainImage = () => {
  // 触发文件选择来替换当前主图
  triggerFileInput()
}

const toggleSortMode = () => {
  sortMode.value = !sortMode.value
  if (sortMode.value) {
    showMessage.info('拖拽图片进行排序，完成后点击“完成排序”')
  }
}

// 原生拖拽排序支持
let draggedIndex = -1

const onDragStart = (index: number, event: DragEvent) => {
  if (!sortMode.value) return
  draggedIndex = index
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/html', '')
  }
}

const onDragOver = (event: DragEvent) => {
  if (!sortMode.value) return
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
  }
}

const onDrop = async (targetIndex: number, event: DragEvent) => {
  if (!sortMode.value || draggedIndex === -1 || draggedIndex === targetIndex) return
  if (!Array.isArray(images.value) || images.value.length === 0) return
  
  event.preventDefault()
  
  try {
    // 更新本地数据
    const newImages = [...images.value]
    const [movedImage] = newImages.splice(draggedIndex, 1)
    newImages.splice(targetIndex, 0, movedImage)
    images.value = newImages
    
    // 更新当前索引
    if (draggedIndex === currentIndex.value) {
      currentIndex.value = targetIndex
    } else if (draggedIndex < currentIndex.value && targetIndex >= currentIndex.value) {
      currentIndex.value--
    } else if (draggedIndex > currentIndex.value && targetIndex <= currentIndex.value) {
      currentIndex.value++
    }
    
    // 同步到服务器
    const sortedIds = newImages.map(img => img.id)
    await http.put(`/products/${props.productId}/gallery/sort`, {
      image_ids: sortedIds
    })
    
    showMessage.success('图片顺序更新成功')
    
  } catch (error: any) {
    showMessage.error(error.response?.data?.error || '排序更新失败')
    // 恢复原顺序
    await loadGallery()
  }
  
  draggedIndex = -1
}

const onDragEnd = () => {
  draggedIndex = -1
}

// 预览控制
const zoomIn = () => {
  zoomLevel.value = Math.min(zoomLevel.value * 1.2, 5)
}

const zoomOut = () => {
  zoomLevel.value = Math.max(zoomLevel.value / 1.2, 0.1)
}

const resetZoom = () => {
  zoomLevel.value = 1
  previewOffset.value = { x: 0, y: 0 }
}

const onPreviewWheel = (event: WheelEvent) => {
  event.preventDefault()
  
  if (event.deltaY < 0) {
    zoomIn()
  } else {
    zoomOut()
  }
}

const startDrag = (event: MouseEvent) => {
  if (zoomLevel.value <= 1) return
  
  isDragging.value = true
  lastMousePos.value = { x: event.clientX, y: event.clientY }
}

const onDrag = (event: MouseEvent) => {
  if (!isDragging.value || zoomLevel.value <= 1) return
  
  const deltaX = event.clientX - lastMousePos.value.x
  const deltaY = event.clientY - lastMousePos.value.y
  
  previewOffset.value.x += deltaX
  previewOffset.value.y += deltaY
  
  lastMousePos.value = { x: event.clientX, y: event.clientY }
}

const endDrag = () => {
  isDragging.value = false
}

const downloadImage = () => {
  if (!currentImage.value) return
  
  const link = document.createElement('a')
  link.href = getImageUrl(currentImage.value.image_url)
  link.download = currentImage.value.original_filename || currentImage.value.filename
  link.target = '_blank'
  link.click()
}

// 缩略图滚动控制
const scrollThumbnails = (direction: 'left' | 'right') => {
  const container = document.querySelector('.thumbnails-scroll') as HTMLElement
  if (!container) return
  
  const scrollAmount = 200
  const newScrollLeft = direction === 'left' 
    ? container.scrollLeft - scrollAmount
    : container.scrollLeft + scrollAmount
  
  container.scrollTo({
    left: newScrollLeft,
    behavior: 'smooth'
  })
}

// 事件处理
const onImageLoad = () => {
  // 图片加载完成
}

const onImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  const originalSrc = img.src
  console.warn('图片加载失败:', originalSrc)
  
  if (!img.src.includes('default-product.svg')) {
    img.src = '/images/default-product.svg'
    showMessage.warning('图片加载失败，已显示默认图片')
  }
}

const onThumbnailError = (event: Event) => {
  const img = event.target as HTMLImageElement
  const originalSrc = img.src
  console.warn('缩略图加载失败:', originalSrc)
  
  if (!img.src.includes('default-product.svg')) {
    img.src = '/images/default-product.svg'
  }
}

const refreshGallery = async () => {
  console.log('🔄 ProductGallery refreshGallery 被调用')
  await loadGallery()
  console.log('✅ ProductGallery refreshGallery 完成')
}

// 生命周期
onMounted(async () => {
  console.log('🏗️ ProductGallery 组件已挂载', {
    productId: props.productId,
    editMode: props.editMode,
    autoLoad: props.autoLoad,
    canEdit: props.canEdit
  })
  
  if (props.autoLoad) {
    console.log('🔄 自动加载图片集...')
    await loadGallery()
  }
  
  // 检查是否需要显示缩略图滚动控制
  await nextTick()
  const container = document.querySelector('.thumbnails-scroll') as HTMLElement
  const wrapper = document.querySelector('.thumbnails-container') as HTMLElement
  
  if (container && wrapper) {
    showScrollControls.value = container.scrollWidth > wrapper.clientWidth
  }
})

// 键盘导航支持
const handleKeydown = (event: KeyboardEvent) => {
  if (!previewVisible.value) return
  
  switch (event.key) {
    case 'ArrowLeft':
      prevImage()
      break
    case 'ArrowRight':
      nextImage()
      break
    case 'Escape':
      closePreview()
      break
    case '+':
    case '=':
      zoomIn()
      break
    case '-':
      zoomOut()
      break
    case '0':
      resetZoom()
      break
  }
}

// 暴露方法给父组件
defineExpose({
  loadGallery,
  selectImage,
  openPreview,
  currentImage,
  images
})

// 监听productId变化
watch(() => props.productId, (newProductId, oldProductId) => {
  console.log('🔄 ProductGallery productId 变化', {
    oldProductId,
    newProductId,
    autoLoad: props.autoLoad
  })
  
  if (newProductId && newProductId !== oldProductId && props.autoLoad) {
    console.log('🔄 重新加载图片集...')
    loadGallery()
  }
}, { immediate: false })

// 监听键盘事件
onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.product-gallery {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 24px;
  transition: all 0.3s ease;
}

.product-gallery.edit-mode {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #e2e8f0;
}

/* 主图展示区域 */
.main-display {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.main-image-container {
  position: relative;
  width: 100%;
  height: v-bind('typeof height === "number" ? height + "px" : height');
  border-radius: 12px;
  overflow: hidden;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
}

.main-image-container.edit-mode {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
}

.image-loading {
  width: 100%;
  height: 100%;
  padding: 20px;
}

.main-image-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.main-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  cursor: pointer;
  transition: transform 0.3s ease;
}

.main-image:hover {
  transform: scale(1.02);
}

.main-image.edit-mode {
  cursor: default;
}

.main-image.edit-mode:hover {
  transform: none;
}

.image-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
  color: white;
  padding: 24px;
  transition: opacity 0.3s ease;
}

.image-info h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
}

.image-info p {
  margin: 0 0 12px 0;
  font-size: 14px;
  opacity: 0.9;
}

.image-meta {
  display: flex;
  gap: 12px;
  align-items: center;
}

.image-type {
  background: rgba(255, 255, 255, 0.2);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.primary-badge {
  background: #f59e0b;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

/* 编辑覆盖层 */
.edit-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
  backdrop-filter: blur(2px);
}

.main-image-wrapper:hover .edit-overlay {
  opacity: 1;
}

.edit-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

/* 导航箭头 */
.navigation-arrows {
  position: absolute;
  top: 50%;
  left: 16px;
  right: 16px;
  transform: translateY(-50%);
  display: flex;
  justify-content: space-between;
  pointer-events: none;
}

.nav-arrow {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.5);
  color: white;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  pointer-events: all;
}

.nav-arrow:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.7);
  transform: scale(1.1);
}

.nav-arrow:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.image-counter {
  position: absolute;
  top: 16px;
  right: 16px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 14px;
  font-weight: 500;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
  color: #9ca3af;
  transition: all 0.3s ease;
}

.empty-state.edit-mode {
  cursor: pointer;
  border: 2px dashed #d1d5db;
  border-radius: 12px;
  margin: 16px;
  height: calc(100% - 32px);
}

.empty-state.edit-mode:hover {
  border-color: #2563eb;
  background: #f8fafc;
}

.empty-state.drag-over {
  border-color: #2563eb;
  background: #eff6ff;
  transform: scale(1.02);
}

.empty-state.uploading {
  border-color: #2563eb;
  background: #f0f9ff;
}

.empty-icon {
  opacity: 0.5;
}

.empty-text {
  font-size: 16px;
  margin: 0;
  font-weight: 600;
  color: #374151;
}

.empty-hint {
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-align: center;
}

.upload-hint {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.empty-state.edit-mode:hover .empty-icon {
  color: #2563eb;
  transform: scale(1.1);
}

/* 上传状态 */
.uploading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
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

/* 操作按钮 */
.main-actions {
  display: flex;
  justify-content: center;
}

/* 缩略图部分 */
.thumbnails-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.thumbnails-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #374151;
  transition: color 0.3s ease;
}

.thumbnails-title.edit-mode {
  color: #2563eb;
}

.thumbnails-container {
  position: relative;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  background: white;
  padding: 12px;
}

.thumbnails-scroll {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  scrollbar-width: thin;
  scrollbar-color: #d1d5db transparent;
  padding: 8px 0;
}

.thumbnails-scroll::-webkit-scrollbar {
  height: 4px;
}

.thumbnails-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.thumbnails-scroll::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 2px;
}

.thumbnail-item {
  flex-shrink: 0;
  width: 120px;
  cursor: pointer;
  border-radius: 8px;
  border: 2px solid transparent;
  overflow: hidden;
  transition: all 0.3s ease;
}

.thumbnail-item:hover {
  border-color: #3b82f6;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
}

.thumbnail-item.active {
  border-color: #2563eb;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
}

.thumbnail-item.primary {
  border-color: #f59e0b;
}

.thumbnail-wrapper {
  position: relative;
  width: 100%;
  height: 80px;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
}

.thumbnail-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: cover;
}

.primary-indicator {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  background: #f59e0b;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
}

.type-indicator {
  position: absolute;
  bottom: 4px;
  left: 4px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 10px;
  font-weight: 500;
}

.thumbnail-info {
  padding: 8px;
  background: white;
  border-top: 1px solid #e5e7eb;
}

.thumbnail-title {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: #374151;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 滚动控制按钮 */
.scroll-control {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #e5e7eb;
  color: #6b7280;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 10;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.scroll-control:hover {
  background: white;
  color: #374151;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.scroll-control.left {
  left: 8px;
}

.scroll-control.right {
  right: 8px;
}

/* 全屏预览对话框 */
.preview-dialog {
  --el-dialog-content-font-size: 16px;
}

.preview-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: 80vh;
}

.preview-image-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: #000;
  border-radius: 8px;
  position: relative;
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  transition: transform 0.1s ease;
}

.preview-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
}

.zoom-info {
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
}

.preview-navigation {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}

.preview-counter {
  font-size: 16px;
  font-weight: 500;
  color: #374151;
}

/* 拖拽效果 */
.thumbnail-item[draggable="true"]:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.thumbnail-item.dragging {
  opacity: 0.5;
  transform: scale(0.95);
}

.thumbnail-item.drag-over {
  border-color: #2563eb;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
}

/* 统计对话框 */
.stats-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stats-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #e5e7eb;
}

.stats-item:last-child {
  border-bottom: none;
}

.stats-label {
  font-weight: 600;
  color: #374151;
}

.stats-value {
  color: #1e293b;
  font-weight: 500;
}

.type-breakdown {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-end;
}

.type-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .main-image-container {
    height: 250px;
  }

  .thumbnails-scroll {
    gap: 8px;
  }

  .thumbnail-item {
    width: 80px;
  }

  .thumbnail-wrapper {
    height: 60px;
  }

  .navigation-arrows {
    left: 8px;
    right: 8px;
  }

  .nav-arrow {
    width: 32px;
    height: 32px;
  }

  .thumbnail-controls {
    position: relative;
    flex-direction: row;
    justify-content: center;
    opacity: 1;
    margin-top: 4px;
  }

  .control-btn {
    min-height: 24px !important;
    padding: 4px 8px !important;
    font-size: 12px !important;
  }

  .preview-content {
    height: 70vh;
  }

  .preview-navigation {
    flex-direction: column;
    gap: 16px;
  }
}
</style>