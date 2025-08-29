<template>
  <el-dialog
    v-model="visible"
    title="图片管理"
    width="80%"
    class="gallery-manager-dialog"
    :before-close="handleClose"
  >
    <div class="gallery-manager">
      <!-- 工具栏 -->
      <div class="toolbar">
        <div class="toolbar-left">
          <el-button
            type="primary"
            :icon="Plus"
            @click="showUploadDialog = true"
          >
            添加图片
          </el-button>
          
          <el-button
            :icon="Upload"
            @click="showBatchUploadDialog = true"
          >
            批量上传
          </el-button>
          
          <el-button
            v-if="selectedImages.length > 0"
            type="danger"
            :icon="Delete"
            @click="deleteSelectedImages"
          >
            删除选中 ({{ selectedImages.length }})
          </el-button>
        </div>

        <div class="toolbar-right">
          <el-select
            v-model="filterType"
            placeholder="筛选图片类型"
            clearable
            style="width: 140px"
          >
            <el-option label="产品图" value="product" />
            <el-option label="细节图" value="detail" />
            <el-option label="使用图" value="usage" />
            <el-option label="对比图" value="comparison" />
          </el-select>

          <el-button
            :icon="Refresh"
            @click="loadImages"
            :loading="loading"
          >
            刷新
          </el-button>
        </div>
      </div>

      <!-- 统计信息 -->
      <div v-if="stats" class="stats-bar">
        <el-card class="stats-card" shadow="never">
          <div class="stats-content">
            <div class="stat-item">
              <span class="stat-label">总图片:</span>
              <span class="stat-value">{{ stats.total_images }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">总大小:</span>
              <span class="stat-value">{{ formatFileSize(stats.total_size) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">主图:</span>
              <span class="stat-value" :class="{ 'text-success': stats.has_primary, 'text-warning': !stats.has_primary }">
                {{ stats.has_primary ? '已设置' : '未设置' }}
              </span>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 图片网格 -->
      <div class="images-grid" v-loading="loading">
        <div
          v-for="image in filteredImages"
          :key="image.id"
          class="image-card"
          :class="{
            selected: selectedImages.includes(image.id),
            primary: image.is_primary
          }"
        >
          <!-- 图片选择框 -->
          <div class="selection-checkbox">
            <el-checkbox
              :model-value="selectedImages.includes(image.id)"
              @change="toggleImageSelection(image.id)"
            />
          </div>

          <!-- 主图标识 -->
          <div v-if="image.is_primary" class="primary-badge">
            <el-icon><Star /></el-icon>
            主图
          </div>

          <!-- 图片展示 -->
          <div class="image-preview" @click="previewImage(image)">
            <img
              :src="getImageUrl(image.thumbnail_url || image.image_url)"
              :alt="image.title"
              class="preview-img"
              @error="onImageError"
            />
            
            <div class="image-overlay">
              <el-button-group>
                <el-button size="small" :icon="ZoomIn">预览</el-button>
                <el-button size="small" :icon="Edit" @click.stop="editImage(image)">编辑</el-button>
              </el-button-group>
            </div>
          </div>

          <!-- 图片信息 -->
          <div class="image-info">
            <div class="image-title">
              {{ image.title || image.filename }}
            </div>
            <div class="image-meta">
              <el-tag
                size="small"
                :type="getImageTypeTagType(image.image_type)"
              >
                {{ getImageTypeLabel(image.image_type) }}
              </el-tag>
              <span class="file-size">{{ formatFileSize(image.file_size || 0) }}</span>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="image-actions">
            <el-button-group>
              <el-button
                v-if="!image.is_primary"
                size="small"
                type="warning"
                @click="setPrimaryImage(image.id)"
              >
                设为主图
              </el-button>
              <el-button
                size="small"
                :icon="Edit"
                @click="editImage(image)"
              >
                编辑
              </el-button>
              <el-button
                size="small"
                type="danger"
                :icon="Delete"
                @click="deleteImage(image.id)"
              >
                删除
              </el-button>
            </el-button-group>
          </div>

          <!-- 拖拽排序手柄 -->
          <div class="drag-handle">
            <el-icon><Rank /></el-icon>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="!loading && filteredImages.length === 0" class="empty-state">
          <el-empty description="暂无图片" />
        </div>
      </div>
    </div>

    <!-- 上传图片对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传图片"
      width="600px"
      :before-close="() => showUploadDialog = false"
    >
      <FastImageUpload
        :product-id="productId"
        @upload-success="handleUploadSuccess"
        @upload-error="handleUploadError"
      />
    </el-dialog>

    <!-- 批量上传对话框 -->
    <el-dialog
      v-model="showBatchUploadDialog"
      title="批量上传图片"
      width="700px"
      :before-close="() => showBatchUploadDialog = false"
    >
      <BatchImageUpload
        :product-id="productId"
        @upload-complete="handleBatchUploadComplete"
      />
    </el-dialog>

    <!-- 编辑图片对话框 -->
    <el-dialog
      v-model="showEditDialog"
      title="编辑图片信息"
      width="500px"
      :before-close="() => showEditDialog = false"
    >
      <el-form
        v-if="editingImage"
        :model="editForm"
        label-width="80px"
        @submit.prevent="saveImageEdit"
      >
        <el-form-item label="标题">
          <el-input v-model="editForm.title" placeholder="图片标题" />
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="3"
            placeholder="图片描述"
          />
        </el-form-item>
        
        <el-form-item label="替代文本">
          <el-input v-model="editForm.alt_text" placeholder="用于屏幕阅读器" />
        </el-form-item>
        
        <el-form-item label="图片类型">
          <el-select v-model="editForm.image_type" style="width: 100%">
            <el-option label="产品图" value="product" />
            <el-option label="细节图" value="detail" />
            <el-option label="使用图" value="usage" />
            <el-option label="对比图" value="comparison" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="设为主图">
          <el-switch v-model="editForm.is_primary" />
        </el-form-item>
        
        <div class="dialog-footer">
          <el-button @click="showEditDialog = false">取消</el-button>
          <el-button type="primary" @click="saveImageEdit">保存</el-button>
        </div>
      </el-form>
    </el-dialog>

    <!-- 图片预览对话框 -->
    <el-dialog
      v-model="showPreviewDialog"
      :title="previewingImage?.title || '图片预览'"
      width="80%"
      class="preview-dialog"
      :before-close="() => showPreviewDialog = false"
    >
      <div v-if="previewingImage" class="preview-content">
        <img
          :src="getImageUrl(previewingImage.image_url)"
          :alt="previewingImage.title"
          class="preview-image"
        />
        
        <div class="preview-info">
          <h4>{{ previewingImage.title || previewingImage.filename }}</h4>
          <p v-if="previewingImage.description">{{ previewingImage.description }}</p>
          
          <div class="preview-meta">
            <div class="meta-item">
              <span class="meta-label">类型:</span>
              <el-tag :type="getImageTypeTagType(previewingImage.image_type)">
                {{ getImageTypeLabel(previewingImage.image_type) }}
              </el-tag>
            </div>
            <div class="meta-item">
              <span class="meta-label">尺寸:</span>
              <span>{{ previewingImage.width }}×{{ previewingImage.height }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">大小:</span>
              <span>{{ formatFileSize(previewingImage.file_size || 0) }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">格式:</span>
              <span>{{ previewingImage.format?.toUpperCase() }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessageBox } from 'element-plus'
import { showMessage } from '@/utils/message'
import {
  Plus, Upload, Delete, Refresh, Star, ZoomIn, Edit, Rank
} from '@element-plus/icons-vue'
import http from '@/api/http'
import FastImageUpload from './FastImageUpload.vue'
import BatchImageUpload from './BatchImageUpload.vue'
// import Sortable from 'sortablejs' // 暂时注释掉，手动排序

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
  images?: ProductImage[]
}

interface Emits {
  (e: 'refresh'): void
  (e: 'update:visible', visible: boolean): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 响应式状态
const visible = defineModel<boolean>('visible', { default: false })
const loading = ref(false)
const images = ref<ProductImage[]>([])
const selectedImages = ref<number[]>([])
const stats = ref<GalleryStats | null>(null)
const filterType = ref<string>('')

// 对话框状态
const showUploadDialog = ref(false)
const showBatchUploadDialog = ref(false)
const showEditDialog = ref(false)
const showPreviewDialog = ref(false)

// 编辑相关
const editingImage = ref<ProductImage | null>(null)
const editForm = ref({
  title: '',
  description: '',
  alt_text: '',
  image_type: 'product',
  is_primary: false
})

// 预览相关
const previewingImage = ref<ProductImage | null>(null)

// 计算属性
const filteredImages = computed(() => {
  if (!filterType.value) return images.value
  return images.value.filter(img => img.image_type === filterType.value)
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

const getImageTypeTagType = (type: string): string => {
  const types: Record<string, string> = {
    'product': 'primary',
    'detail': 'success',
    'usage': 'warning',
    'comparison': 'info'
  }
  return types[type] || 'primary'
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const loadImages = async () => {
  if (!props.productId) return
  
  console.log('🔄 ProductGalleryManager 开始加载图片', { productId: props.productId })
  loading.value = true
  
  try {
    const [galleryResponse, statsResponse] = await Promise.all([
      http.get(`/products/${props.productId}/gallery`),
      http.get(`/products/${props.productId}/gallery/stats`)
    ])
    
    console.log('📋 ProductGalleryManager 收到API响应:', {
      galleryResponse,
      statsResponse
    })
    
    images.value = galleryResponse.images || []
    stats.value = statsResponse
    
    console.log('📊 ProductGalleryManager 图片数据已更新:', {
      imageCount: images.value.length,
      images: images.value.map(img => ({ id: img.id, filename: img.filename, is_primary: img.is_primary }))
    })
    
    // 清空选择
    selectedImages.value = []
    
  } catch (error: any) {
    console.error('❌ ProductGalleryManager 加载图片失败:', error)
    console.error('📊 错误详情:', {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status,
      url: error.config?.url
    })
    showMessage.error(error.response?.data?.error || '加载图片失败')
  } finally {
    loading.value = false
    console.log('🏁 ProductGalleryManager 加载图片流程结束')
  }
}

const toggleImageSelection = (imageId: number) => {
  const index = selectedImages.value.indexOf(imageId)
  if (index > -1) {
    selectedImages.value.splice(index, 1)
  } else {
    selectedImages.value.push(imageId)
  }
}

const setPrimaryImage = async (imageId: number) => {
  try {
    await http.post(`/products/${props.productId}/gallery/${imageId}/set-primary`)
    showMessage.success('主图设置成功')
    await loadImages()
    emit('refresh')
  } catch (error: any) {
    console.error('设置主图失败:', error)
    showMessage.error(error.response?.data?.error || '设置主图失败')
  }
}

const editImage = (image: ProductImage) => {
  editingImage.value = image
  editForm.value = {
    title: image.title || '',
    description: image.description || '',
    alt_text: image.alt_text || '',
    image_type: image.image_type,
    is_primary: image.is_primary
  }
  showEditDialog.value = true
}

const saveImageEdit = async () => {
  if (!editingImage.value) return
  
  try {
    await http.put(`/products/${props.productId}/gallery/${editingImage.value.id}`, editForm.value)
    showMessage.success('图片信息已更新')
    showEditDialog.value = false
    await loadImages()
    emit('refresh')
  } catch (error: any) {
    console.error('更新图片信息失败:', error)
    showMessage.error(error.response?.data?.error || '更新失败')
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
    
    await http.delete(`/products/${props.productId}/gallery/${imageId}`)
    showMessage.success('图片删除成功')
    await loadImages()
    emit('refresh')
    
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除图片失败:', error)
      showMessage.error(error.response?.data?.error || '删除失败')
    }
  }
}

const deleteSelectedImages = async () => {
  if (selectedImages.value.length === 0) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedImages.value.length} 张图片吗？删除后无法恢复。`,
      '批量删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )
    
    // 并发删除选中的图片
    const deletePromises = selectedImages.value.map(imageId =>
      http.delete(`/products/${props.productId}/gallery/${imageId}`)
    )
    
    await Promise.all(deletePromises)
    showMessage.success(`成功删除 ${selectedImages.value.length} 张图片`)
    
    selectedImages.value = []
    await loadImages()
    emit('refresh')
    
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
      showMessage.error(error.response?.data?.error || '批量删除失败')
    }
  }
}

const previewImage = (image: ProductImage) => {
  previewingImage.value = image
  showPreviewDialog.value = true
}

const handleUploadSuccess = (imageUrl: string, uploadData: any) => {
  console.log('🎉 ProductGalleryManager 收到上传成功事件:', {
    imageUrl,
    uploadData
  })
  
  showMessage.success('图片上传成功')
  showUploadDialog.value = false
  
  console.log('🔄 开始重新加载图片列表...')
  loadImages()
  
  console.log('📡 触发refresh事件通知父组件...')
  emit('refresh')
  
  console.log('✅ ProductGalleryManager 上传成功处理完成')
}

const handleUploadError = (error: string) => {
  showMessage.error(`上传失败: ${error}`)
}

const handleBatchUploadComplete = (results: any) => {
  const successCount = results.filter((r: any) => r.success).length
  showMessage.success(`批量上传完成，成功上传 ${successCount} 张图片`)
  showBatchUploadDialog.value = false
  loadImages()
  emit('refresh')
}

const onImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.src = '/images/default-product.svg'
}

const handleClose = () => {
  visible.value = false
}

// 初始化拖拽排序（暂时禁用，使用手动排序）
const initDragSort = () => {
  // const el = document.querySelector('.images-grid')
  // if (el) {
  //   Sortable.create(el as HTMLElement, {
  //     animation: 150,
  //     handle: '.drag-handle',
  //     onEnd: async (evt) => {
  //       // 排序逻辑
  //     }
  //   })
  // }
}

// 监听visible变化，对话框打开时加载数据
watch(visible, (newVisible) => {
  if (newVisible) {
    loadImages()
    // 延迟初始化拖拽，确保DOM已渲染
    setTimeout(initDragSort, 100)
  }
})

onMounted(() => {
  if (props.images) {
    images.value = props.images
  }
})
</script>

<style scoped>
.gallery-manager-dialog {
  --el-dialog-content-font-size: 16px;
}

.gallery-manager {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 工具栏 */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* 统计信息 */
.stats-bar {
  margin: -8px 0;
}

.stats-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
}

.stats-card :deep(.el-card__body) {
  padding: 16px 24px;
}

.stats-content {
  display: flex;
  gap: 32px;
  align-items: center;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  opacity: 0.8;
  font-weight: 500;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
}

.text-success {
  color: #10b981;
}

.text-warning {
  color: #f59e0b;
}

/* 图片网格 */
.images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  min-height: 400px;
}

.image-card {
  position: relative;
  background: white;
  border-radius: 12px;
  border: 2px solid #e5e7eb;
  transition: all 0.3s ease;
  overflow: hidden;
}

.image-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.15);
  transform: translateY(-2px);
}

.image-card.selected {
  border-color: #2563eb;
  box-shadow: 0 8px 24px rgba(37, 99, 235, 0.25);
}

.image-card.primary {
  border-color: #f59e0b;
  box-shadow: 0 8px 24px rgba(245, 158, 11, 0.15);
}

/* 选择框 */
.selection-checkbox {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 10;
  background: rgba(255, 255, 255, 0.9);
  padding: 4px;
  border-radius: 4px;
  backdrop-filter: blur(4px);
}

/* 主图标识 */
.primary-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 10;
  background: #f59e0b;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 图片预览 */
.image-preview {
  position: relative;
  height: 200px;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  overflow: hidden;
}

.preview-img {
  max-width: 100%;
  max-height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.image-card:hover .preview-img {
  transform: scale(1.05);
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

.image-preview:hover .image-overlay {
  opacity: 1;
}

/* 图片信息 */
.image-info {
  padding: 16px;
  border-bottom: 1px solid #f3f4f6;
}

.image-title {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.image-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.file-size {
  font-size: 12px;
  color: #6b7280;
}

/* 操作按钮 */
.image-actions {
  padding: 12px 16px;
  background: #fafafa;
  display: flex;
  justify-content: center;
}

.image-actions .el-button-group {
  width: 100%;
}

.image-actions .el-button {
  flex: 1;
  font-size: 12px;
}

/* 拖拽手柄 */
.drag-handle {
  position: absolute;
  top: 50%;
  right: 8px;
  transform: translateY(-50%);
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  padding: 8px;
  cursor: grab;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.image-card:hover .drag-handle {
  opacity: 1;
}

.drag-handle:active {
  cursor: grabbing;
}

/* 空状态 */
.empty-state {
  grid-column: 1 / -1;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

/* 对话框通用样式 */
.dialog-footer {
  text-align: right;
  margin-top: 24px;
}

/* 预览对话框 */
.preview-dialog {
  --el-dialog-content-font-size: 16px;
}

.preview-content {
  display: flex;
  gap: 24px;
}

.preview-image {
  max-width: 60%;
  max-height: 70vh;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.preview-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.preview-info h4 {
  margin: 0;
  font-size: 18px;
  color: #374151;
}

.preview-info p {
  margin: 0;
  color: #6b7280;
  line-height: 1.6;
}

.preview-meta {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.meta-label {
  font-weight: 600;
  color: #374151;
  min-width: 60px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .toolbar-left,
  .toolbar-right {
    justify-content: center;
  }

  .stats-content {
    gap: 16px;
  }

  .images-grid {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 16px;
  }

  .image-preview {
    height: 160px;
  }

  .preview-content {
    flex-direction: column;
  }

  .preview-image {
    max-width: 100%;
  }
}
</style>