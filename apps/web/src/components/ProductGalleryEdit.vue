<template>
  <div class="product-gallery-edit">
    <!-- 主图展示区域 -->
    <div class="main-display">
      <div class="main-image-container">
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
          <div v-if="!editMode && showImageInfo && currentImage" class="image-overlay">
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
          <div v-if="!editMode && images.length > 1" class="navigation-arrows">
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
          <div v-if="images.length > 1" class="image-counter">
            {{ currentIndex + 1 }} / {{ images.length }}
          </div>
        </div>

        <!-- 空状态或拖拽上传区域 -->
        <div 
          v-else 
          class="empty-upload-area"
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
            <el-icon class="upload-icon" size="48">
              <Picture v-if="!editMode" />
              <Plus v-else />
            </el-icon>
            <div class="upload-hint">
              <p class="primary-text">
                {{ editMode ? '点击或拖拽图片到这里上传' : '暂无产品图片' }}
              </p>
              <p v-if="editMode" class="secondary-text">
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
              v-if="images.length > 0"
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
    <div v-if="images.length > 0" class="thumbnails-section">
      <h4 class="thumbnails-title">
        {{ editMode ? '管理图片' : '所有图片' }} ({{ images.length }})
        <el-tag v-if="stats" size="small" type="info">
          {{ formatFileSize(stats.total_size) }}
        </el-tag>
      </h4>
      
      <div class="thumbnails-container" :class="{ 'sort-mode': sortMode }">
        <div class="thumbnails-scroll">
          <!-- 编辑模式排序支持 -->
          <Sortable
            v-if="editMode"
            v-model="sortableImages"
            item-key="id"
            :options="sortableOptions"
            @end="onSortEnd"
            class="sortable-container"
          >
            <template #item="{ element: image, index }">
              <div
                class="thumbnail-item"
                :class="{
                  active: index === currentIndex,
                  primary: image.is_primary,
                  'edit-mode': editMode,
                  'sort-mode': sortMode
                }"
                @click="!sortMode && selectImage(index)"
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
                    />
                    <el-button
                      size="small"
                      type="danger"
                      :icon="Delete"
                      @click.stop="deleteImage(image.id)"
                      :disabled="deleting"
                      title="删除图片"
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
          </Sortable>
          
          <!-- 查看模式普通显示 -->
          <div
            v-else
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
        </div>
        
        <!-- 滚动控制按钮 -->
        <button
          v-if="showScrollControls && !editMode"
          class="scroll-control left"
          @click="scrollThumbnails('left')"
        >
          <el-icon><ArrowLeft /></el-icon>
        </button>
        <button
          v-if="showScrollControls && !editMode"
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
        <div v-if="images.length > 1" class="preview-navigation">
          <el-button
            :disabled="currentIndex === 0"
            @click="prevImage"
          >
            <el-icon><ArrowLeft /></el-icon>
            上一张
          </el-button>
          <span class="preview-counter">
            {{ currentIndex + 1 }} / {{ images.length }}
          </span>
          <el-button
            :disabled="currentIndex === images.length - 1"
            @click="nextImage"
          >
            下一张
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </div>
    </el-dialog>

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
import { Sortable } from '@shopify/draggable'
import http from '@/api/http'
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

// 排序相关
const sortableImages = ref<ProductImage[]>([])
const sortableOptions = {
  animation: 150,
  handle: '.sort-handle',
  ghostClass: 'sortable-ghost',
  chosenClass: 'sortable-chosen',
  dragClass: 'sortable-drag'
}

// 监听images变化
watch(() => images.value, (newImages) => {
  sortableImages.value = [...newImages]
}, { deep: true })

// 计算属性
const currentImage = computed(() => {
  return images.value[currentIndex.value] || null
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
  
  if (url.startsWith('data:') || url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  
  if (url.startsWith('/api/v1')) {
    return `http://localhost:5173${url}`
  }
  
  return `http://localhost:5173/api/v1/products/uploads/${url}`
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

// 加载图片集
const loadGallery = async () => {
  if (!props.productId) return
  
  loading.value = true
  
  try {
    const response = await http.get(`/products/${props.productId}/gallery`)
    images.value = response.data.images || []
    
    // 如果有主图，设置为当前显示图片
    if (response.data.primary_image) {
      const primaryIndex = images.value.findIndex(img => img.is_primary)
      if (primaryIndex >= 0) {
        currentIndex.value = primaryIndex
      }
    }
    
    // 加载统计信息
    const statsResponse = await http.get(`/products/${props.productId}/gallery/stats`)
    stats.value = statsResponse.data
    
    emit('imagesUpdate', images.value)
    
  } catch (error: any) {
    console.error('加载图片集失败:', error)
    showMessage.error(error.response?.data?.error || '加载图片集失败')
  } finally {
    loading.value = false
  }
}

// 文件上传处理
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
  const validFiles = Array.from(files).filter(validateFile)
  if (validFiles.length === 0) return

  uploading.value = true
  uploadProgress.value = 0
  processingInfo.value = ''
  uploadStatusText.value = '开始处理图片...'

  try {
    const uploadPromises = validFiles.map(async (file, index) => {
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

      // 上传到服务器
      const formData = new FormData()
      formData.append('image', compressionResult.file)
      formData.append('image_type', 'product')

      const response = await http.post(
        `/products/${props.productId}/gallery/upload`, 
        formData
      )

      return response.data
    })

    await Promise.all(uploadPromises)
    
    uploadProgress.value = 100
    uploadStatusText.value = '上传完成！'
    
    showMessage.success(`成功上传 ${validFiles.length} 张图片`)
    
    // 重新加载图片集
    await loadGallery()

  } catch (error: any) {
    console.error('批量上传失败:', error)
    showMessage.error(error.response?.data?.error || '图片上传失败')
  } finally {
    uploading.value = false
    uploadProgress.value = 0
    uploadStatusText.value = ''
    processingInfo.value = ''
  }
}

// 文件输入事件
const triggerFileInput = () => {
  if (!props.editMode || uploading.value) return
  fileInput.value?.click()
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = target.files
  
  if (files && files.length > 0) {
    uploadFiles(files)
  }
  
  target.value = ''
}

// 拖拽上传
const handleDragOver = (event: DragEvent) => {
  if (!props.editMode || uploading.value) return
  event.preventDefault()
  isDragOver.value = true
}

const handleDragLeave = () => {
  isDragOver.value = false
}

const handleDrop = (event: DragEvent) => {
  if (!props.editMode || uploading.value) return
  
  event.preventDefault()
  isDragOver.value = false
  
  const files = event.dataTransfer?.files
  if (files && files.length > 0) {
    uploadFiles(files)
  }
}

// 图片操作
const selectImage = (index: number) => {
  if (index >= 0 && index < images.value.length) {
    currentIndex.value = index
    const image = images.value[index]
    if (image) {
      emit('imageChange', image.image_url)
    }
  }
}

const prevImage = () => {
  if (currentIndex.value > 0) {
    selectImage(currentIndex.value - 1)
  }
}

const nextImage = () => {
  if (currentIndex.value < images.value.length - 1) {
    selectImage(currentIndex.value + 1)
  }
}

const setAsPrimary = async (imageId: number) => {
  try {
    await http.put(`/products/${props.productId}/gallery/${imageId}/primary`)
    showMessage.success('主图设置成功')
    await loadGallery()
  } catch (error: any) {
    showMessage.error(error.response?.data?.error || '设置主图失败')
  }
}

const deleteImage = async (imageId: number) => {
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
    await loadGallery()

  } catch (error: any) {
    if (error !== 'cancel') {
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

// 排序功能
const toggleSortMode = () => {
  sortMode.value = !sortMode.value
  if (sortMode.value) {
    showMessage.info('拖拽图片进行排序，完成后点击"完成排序"')
  }
}

const onSortEnd = async (evt: any) => {
  if (evt.oldIndex !== evt.newIndex) {
    try {
      // 更新排序
      const sortedIds = sortableImages.value.map(img => img.id)
      await http.put(`/products/${props.productId}/gallery/sort`, {
        image_ids: sortedIds
      })
      
      showMessage.success('图片顺序更新成功')
      await loadGallery()
      
    } catch (error: any) {
      showMessage.error(error.response?.data?.error || '排序更新失败')
      // 恢复原顺序
      sortableImages.value = [...images.value]
    }
  }
}

// 预览功能
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
  img.src = '/images/default-product.svg'
}

const onThumbnailError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.src = '/images/default-product.svg'
}

// 生命周期
onMounted(async () => {
  if (props.autoLoad) {
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

// 暴露方法给父组件
defineExpose({
  loadGallery,
  selectImage,
  openPreview,
  currentImage,
  images
})
</script>

<style scoped>
.product-gallery-edit {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 24px;
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

/* 信息覆盖层 */
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

/* 空状态/上传区域 */
.empty-upload-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
  padding: 40px;
  text-align: center;
  transition: all 0.3s ease;
}

.empty-upload-area.edit-mode {
  cursor: pointer;
  border: 2px dashed #d1d5db;
  border-radius: 12px;
  margin: 16px;
  height: calc(100% - 32px);
}

.empty-upload-area.edit-mode:hover {
  border-color: #2563eb;
  background: #f8fafc;
}

.empty-upload-area.drag-over {
  border-color: #2563eb;
  background: #eff6ff;
  transform: scale(1.02);
}

.empty-upload-area.uploading {
  border-color: #2563eb;
  background: #f0f9ff;
}

.upload-icon {
  color: #9ca3af;
  transition: all 0.3s ease;
}

.empty-upload-area.edit-mode:hover .upload-icon {
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
}

.thumbnails-container {
  position: relative;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  background: white;
  padding: 12px;
}

.thumbnails-container.sort-mode {
  background: #f8fafc;
  border-color: #2563eb;
}

.thumbnails-scroll {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  scrollbar-width: thin;
  scrollbar-color: #d1d5db transparent;
  padding: 8px 0;
}

.sortable-container {
  display: flex;
  gap: 12px;
}

.thumbnail-item {
  flex-shrink: 0;
  width: 120px;
  cursor: pointer;
  border-radius: 8px;
  border: 2px solid transparent;
  overflow: hidden;
  transition: all 0.3s ease;
  position: relative;
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

.thumbnail-item.edit-mode {
  cursor: default;
}

.thumbnail-item.sort-mode {
  cursor: grab;
}

.thumbnail-item.sort-mode:active {
  cursor: grabbing;
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

.sort-handle {
  position: absolute;
  top: 4px;
  left: 4px;
  width: 20px;
  height: 20px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: grab;
  z-index: 10;
}

.sort-handle:active {
  cursor: grabbing;
}

.thumbnail-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: cover;
}

.thumbnail-controls {
  position: absolute;
  top: 4px;
  right: 4px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.thumbnail-item:hover .thumbnail-controls {
  opacity: 1;
}

.thumbnail-controls .el-button {
  min-height: 20px;
  padding: 2px 4px;
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

.thumbnail-meta {
  margin-top: 4px;
  font-size: 11px;
  color: #6b7280;
}

.file-size {
  font-weight: 500;
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

/* 拖拽排序样式 */
.sortable-ghost {
  opacity: 0.5;
}

.sortable-chosen {
  transform: scale(1.05);
}

.sortable-drag {
  transform: rotate(5deg);
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

/* 响应式设计 */
@media (max-width: 768px) {
  .main-image-container {
    height: 250px;
  }

  .thumbnails-scroll, .sortable-container {
    gap: 8px;
  }

  .thumbnail-item {
    width: 80px;
  }

  .thumbnail-wrapper {
    height: 60px;
  }

  .edit-actions {
    gap: 8px;
  }

  .edit-actions .el-button {
    font-size: 12px;
    padding: 8px 12px;
  }

  .navigation-arrows {
    left: 8px;
    right: 8px;
  }

  .nav-arrow {
    width: 32px;
    height: 32px;
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