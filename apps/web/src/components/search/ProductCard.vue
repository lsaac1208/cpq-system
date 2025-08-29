<template>
  <div
    class="product-card"
    :class="{ 
      [`product-card--${viewMode}`]: true,
      'product-card--hover': !loading
    }"
    @click="handleProductClick"
  >
    <!-- 产品图片 -->
    <div class="product-image">
      <img
        :src="productImageSrc"
        :alt="product.name"
        loading="lazy"
        @error="handleImageError"
      />
      
      <!-- 库存状态 -->
      <div v-if="stockStatus" class="stock-badge" :class="stockStatus.class">
        {{ stockStatus.text }}
      </div>
      
      <!-- 相关性分数 -->
      <div v-if="product.relevance_score && showRelevanceScore" class="relevance-badge">
        匹配度: {{ product.relevance_score }}%
      </div>
    </div>
    
    <!-- 产品信息 -->
    <div class="product-info">
      <!-- 产品名称 -->
      <h3 
        class="product-name"
        v-html="highlightedName"
        :title="product.name"
      />
      
      <!-- 产品元信息 -->
      <div class="product-meta">
        <span class="product-code">
          <el-icon><Postcard /></el-icon>
          {{ product.code }}
        </span>
        <span class="product-category">
          <el-icon><Folder /></el-icon>
          <span v-html="highlightedCategory" />
        </span>
      </div>
      
      <!-- 产品描述 -->
      <div
        v-if="product.description"
        class="product-description"
        v-html="highlightedDescription"
        :title="product.description"
      />
      
      <!-- 产品规格 -->
      <div v-if="displaySpecs.length > 0" class="product-specs">
        <div
          v-for="spec in displaySpecs"
          :key="spec.key"
          class="spec-item"
        >
          <span class="spec-label">{{ spec.label }}:</span>
          <span class="spec-value">{{ spec.value }}</span>
        </div>
      </div>
      
      <!-- 产品底部 -->
      <div class="product-footer">
        <!-- 价格信息 -->
        <div class="product-price">
          <span class="price-label">价格:</span>
          <span class="price-value">¥{{ formatPrice(product.base_price) }}</span>
          <span v-if="product.is_configurable" class="price-note">起</span>
        </div>
        
        <!-- 操作按钮 -->
        <div class="product-actions">
          <el-button
            type="primary"
            size="small"
            :loading="addingToQuote"
            @click.stop="handleAddToQuote"
          >
            <el-icon><Plus /></el-icon>
            加入询价单
          </el-button>
          <el-button
            size="small"
            @click.stop="handleViewDetails"
          >
            查看详情
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElButton, ElIcon } from 'element-plus'
import { Postcard, Folder, Plus } from '@element-plus/icons-vue'
import type { Product } from '@/api/search'

// Props
interface Props {
  product: Product
  viewMode?: 'grid' | 'list'
  searchQuery?: string
  showRelevanceScore?: boolean
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  viewMode: 'grid',
  searchQuery: '',
  showRelevanceScore: false,
  loading: false
})

// Emits
interface Emits {
  (e: 'select', product: Product): void
  (e: 'add-to-quote', product: Product): void
  (e: 'view-details', product: Product): void
}

const emit = defineEmits<Emits>()

// 状态
const addingToQuote = ref(false)
const defaultProductImage = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE1MCIgdmlld0JveD0iMCAwIDIwMCAxNTAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMTUwIiBmaWxsPSIjRjVGN0ZBIi8+CjxwYXRoIGQ9Ik03NyA2N0g4M1Y3M0g3N1Y2N1pNODMgNjFINzdWNjdIODNWNjFaTTc3IDczSDgzVjc5SDc3VjczWk04OSA2N0g5NVY3M0g4OVY2N1pNOTUgNjFIOTlWNjdIOTVWNjFaTTEwMSA2N0gxMDdWNzNIMTAxVjY3Wk0xMDcgNjFIMTEzVjY3SDEwN1Y2MVpNMTEzIDY3SDExOVY3M0gxMTNWNjdaTTExOSA2MUgxMjVWNjdIMTE5VjYxWiIgZmlsbD0iI0MwQzRDQyIvPgo8dGV4dCB4PSIxMDAiIHk9IjkwIiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM5MDkzOTkiIHRleHQtYW5jaG9yPSJtaWRkbGUiPueUn+WTgeWbvueJhzwvdGV4dD4KPC9zdmc+'

// 计算属性
const highlightedName = computed(() => {
  return props.product.match_highlights?.name || props.product.name
})

const highlightedCategory = computed(() => {
  return props.product.match_highlights?.category || props.product.category
})

const highlightedDescription = computed(() => {
  const description = props.product.description || ''
  const highlighted = props.product.match_highlights?.description
  
  if (highlighted) {
    return highlighted
  }
  
  // 截取描述文本
  const maxLength = props.viewMode === 'grid' ? 100 : 200
  if (description.length > maxLength) {
    return description.substring(0, maxLength) + '...'
  }
  
  return description
})

const stockStatus = computed(() => {
  // 这里可以根据库存数量显示不同状态
  // 目前数据库中没有库存字段，暂时返回null
  return null
})

const productImageSrc = computed(() => {
  // Handle different possible image property names
  const imageUrl = (props.product as any).image_url || 
                   (props.product as any).image || 
                   (props.product as any).photo_url ||
                   null
  
  if (imageUrl && typeof imageUrl === 'string' && imageUrl.trim()) {
    // If it's a relative path, make it absolute
    if (imageUrl.startsWith('/')) {
      return imageUrl
    }
    // If it's already a full URL, use it
    if (imageUrl.startsWith('http')) {
      return imageUrl
    }
    // If it's a filename, construct the path
    return `/images/products/${imageUrl}`
  }
  
  return defaultProductImage
})

const displaySpecs = computed(() => {
  if (!props.product.specifications) {
    return []
  }
  
  const specs = props.product.specifications
  const maxSpecs = props.viewMode === 'grid' ? 3 : 5
  
  return Object.entries(specs)
    .slice(0, maxSpecs)
    .map(([key, value]) => ({
      key,
      label: formatSpecLabel(key),
      value: formatSpecValue(value)
    }))
})

// 方法
const formatPrice = (price: string | number): string => {
  const numPrice = typeof price === 'string' ? parseFloat(price) : price
  return numPrice.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

const formatSpecLabel = (key: string): string => {
  // 格式化规格键名
  const labelMap: Record<string, string> = {
    power: '功率',
    voltage: '电压',
    speed: '转速',
    efficiency: '效率',
    weight: '重量',
    dimensions: '尺寸',
    protection: '防护等级',
    mounting: '安装方式',
    cooling: '冷却方式'
  }
  
  return labelMap[key] || key.charAt(0).toUpperCase() + key.slice(1)
}

const formatSpecValue = (value: any): string => {
  if (value === null || value === undefined) {
    return '-'
  }
  
  if (typeof value === 'object') {
    // Handle arrays
    if (Array.isArray(value)) {
      return value.join(', ')
    }
    
    // Handle objects - try to extract meaningful information
    if (typeof value === 'object') {
      // Check for common patterns in specifications
      if (value.value !== undefined) {
        return `${value.value}${value.unit ? value.unit : ''}`
      }
      if (value.min !== undefined && value.max !== undefined) {
        return `${value.min}-${value.max}${value.unit ? value.unit : ''}`
      }
      if (value.nominal !== undefined) {
        return `${value.nominal}${value.unit ? value.unit : ''}`
      }
      
      // For other objects, try to create a readable string
      const entries = Object.entries(value)
      if (entries.length <= 3) {
        return entries.map(([k, v]) => `${k}: ${v}`).join(', ')
      }
      
      // Fallback for complex objects
      return '详见详情页'
    }
  }
  
  if (typeof value === 'boolean') {
    return value ? '是' : '否'
  }
  
  return String(value)
}

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.src = defaultProductImage
}

const handleProductClick = () => {
  if (!props.loading) {
    emit('select', props.product)
  }
}

const handleAddToQuote = async () => {
  if (addingToQuote.value) return
  
  addingToQuote.value = true
  
  try {
    emit('add-to-quote', props.product)
    // 这里可以添加成功提示
  } catch (error) {
    console.error('加入询价单失败:', error)
  } finally {
    addingToQuote.value = false
  }
}

const handleViewDetails = () => {
  emit('view-details', props.product)
}
</script>

<style scoped>
.product-card {
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: pointer;
}

.product-card--hover:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #409eff;
  transform: translateY(-2px);
}

/* 网格视图 */
.product-card--grid {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.product-card--grid .product-image {
  height: 200px;
  position: relative;
  overflow: hidden;
}

.product-card--grid .product-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
}

.product-card--grid .product-footer {
  margin-top: auto;
}

/* 列表视图 */
.product-card--list {
  display: flex;
  flex-direction: row;
  align-items: stretch;
}

.product-card--list .product-image {
  width: 200px;
  height: 150px;
  flex-shrink: 0;
  position: relative;
  overflow: hidden;
}

.product-card--list .product-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.product-card--list .product-footer {
  margin-top: auto;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
}

/* 产品图片 */
.product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.product-card--hover:hover .product-image img {
  transform: scale(1.05);
}

.stock-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  color: white;
}

.stock-badge.in-stock {
  background-color: #67c23a;
}

.stock-badge.low-stock {
  background-color: #e6a23c;
}

.stock-badge.out-of-stock {
  background-color: #f56c6c;
}

.relevance-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background-color: rgba(64, 158, 255, 0.9);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

/* 产品信息 */
.product-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 12px 0;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.product-name :deep(mark) {
  background-color: #409eff;
  color: white;
  padding: 1px 4px;
  border-radius: 2px;
  font-weight: 600;
}

.product-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
  font-size: 13px;
  color: #909399;
}

.product-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.product-meta .el-icon {
  font-size: 14px;
}

.product-description {
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
  margin-bottom: 16px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.product-description :deep(mark) {
  background-color: #409eff;
  color: white;
  padding: 1px 3px;
  border-radius: 2px;
}

.product-specs {
  margin-bottom: 16px;
}

.spec-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  font-size: 13px;
  border-bottom: 1px solid #f5f7fa;
}

.spec-item:last-child {
  border-bottom: none;
}

.spec-label {
  color: #909399;
  font-weight: 500;
}

.spec-value {
  color: #606266;
  text-align: right;
  max-width: 60%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 产品底部 */
.product-footer {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.product-price {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.price-label {
  font-size: 14px;
  color: #909399;
}

.price-value {
  font-size: 18px;
  font-weight: 600;
  color: #f56c6c;
}

.price-note {
  font-size: 12px;
  color: #909399;
}

.product-actions {
  display: flex;
  gap: 8px;
}

.product-actions .el-button {
  flex: 1;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .product-card--list {
    flex-direction: column;
  }
  
  .product-card--list .product-image {
    width: 100%;
    height: 160px;
  }
  
  .product-actions {
    flex-direction: column;
  }
}

@media (max-width: 480px) {
  .product-card--grid .product-image {
    height: 160px;
  }
  
  .product-card--grid .product-info {
    padding: 12px;
  }
  
  .product-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .spec-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .spec-value {
    max-width: 100%;
    text-align: left;
  }
}
</style>