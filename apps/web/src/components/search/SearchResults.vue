<template>
  <div class="search-results">
    <!-- 搜索结果头部 -->
    <div class="results-header">
      <div class="results-info">
        <template v-if="searchResult?.search_info">
          找到 <strong>{{ searchResult.pagination.total }}</strong> 个产品
          <span v-if="searchResult.search_info.query" class="search-query">
            ，关键词：<strong>"{{ searchResult.search_info.query }}"</strong>
          </span>
        </template>
      </div>
      
      <div class="results-controls">
        <!-- 排序选择 -->
        <el-select
          v-model="currentSort"
          placeholder="排序方式"
          size="small"
          style="width: 140px"
          @change="handleSortChange"
        >
          <el-option
            v-for="option in sortOptions"
            :key="option.value"
            :label="option.label"
            :value="option.value"
          />
        </el-select>
        
        <!-- 视图切换 -->
        <el-button-group class="view-toggle">
          <el-button
            :type="viewMode === 'grid' ? 'primary' : 'default'"
            size="small"
            @click="setViewMode('grid')"
          >
            <el-icon><Grid /></el-icon>
          </el-button>
          <el-button
            :type="viewMode === 'list' ? 'primary' : 'default'"
            size="small"
            @click="setViewMode('list')"
          >
            <el-icon><Menu /></el-icon>
          </el-button>
        </el-button-group>
      </div>
    </div>
    
    <!-- 搜索结果加载状态 -->
    <div v-if="loading" class="results-loading">
      <el-skeleton :rows="6" animated />
    </div>
    
    <!-- 无搜索结果 -->
    <div v-else-if="!searchResult || !searchResult.products || searchResult.products.length === 0" class="results-empty">
      <div class="empty-icon">
        <el-icon size="64"><Search /></el-icon>
      </div>
      <h3>未找到相关产品</h3>
      <p>尝试使用不同的关键词或调整筛选条件</p>
      
      <div class="search-suggestions">
        <h4>搜索建议：</h4>
        <ul>
          <li>检查拼写是否正确</li>
          <li>尝试使用更通用的关键词</li>
          <li>减少筛选条件</li>
          <li>尝试搜索产品分类或型号</li>
        </ul>
      </div>
    </div>
    
    <!-- 搜索结果列表 -->
    <div v-else class="results-container" :class="viewMode">
      <ProductCard
        v-for="product in searchResult.products"
        :key="product.id"
        :product="product"
        :view-mode="viewMode"
        :search-query="searchResult.search_info.query"
        @select="handleProductSelect"
        @add-to-quote="handleAddToQuote"
        @view-details="handleViewDetails"
      />
    </div>
    
    <!-- 分页 -->
    <div
      v-if="searchResult && searchResult.pagination.pages > 1"
      class="results-pagination"
    >
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="searchResult.pagination.per_page"
        :total="searchResult.pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        :small="false"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElSelect, ElOption, ElButton, ElButtonGroup, ElIcon, ElSkeleton, ElPagination } from 'element-plus'
import { Grid, Search } from '@element-plus/icons-vue'
import type { SearchResult, Product } from '@/api/search'
import ProductCard from './ProductCard.vue'

// Props
interface Props {
  searchResult?: SearchResult | null
  loading?: boolean
  viewMode?: 'grid' | 'list'
  sort?: string
}

const props = withDefaults(defineProps<Props>(), {
  searchResult: null,
  loading: false,
  viewMode: 'grid',
  sort: 'relevance'
})

// Emits
interface Emits {
  (e: 'update:viewMode', value: 'grid' | 'list'): void
  (e: 'update:sort', value: string): void
  (e: 'page-change', page: number): void
  (e: 'size-change', size: number): void
  (e: 'product-select', product: Product): void
  (e: 'add-to-quote', product: Product): void
  (e: 'view-details', product: Product): void
}

const emit = defineEmits<Emits>()

// 状态
const currentSort = ref(props.sort)
const currentPage = ref(1)

// 排序选项
const sortOptions = [
  { label: '相关性', value: 'relevance' },
  { label: '名称', value: 'name' },
  { label: '价格从低到高', value: 'price' },
  { label: '价格从高到低', value: 'price_desc' },
  { label: '最新', value: 'newest' },
  { label: '最旧', value: 'oldest' }
]

// 计算属性
const viewMode = computed({
  get: () => props.viewMode,
  set: (value) => emit('update:viewMode', value)
})

// 监听属性变化
watch(() => props.sort, (newSort) => {
  currentSort.value = newSort
})

watch(() => props.searchResult, (newResult) => {
  if (newResult) {
    currentPage.value = newResult.pagination.page
  }
})

// 事件处理
const handleSortChange = (sort: string) => {
  emit('update:sort', sort)
}

const setViewMode = (mode: 'grid' | 'list') => {
  emit('update:viewMode', mode)
}

const handlePageChange = (page: number) => {
  emit('page-change', page)
}

const handleSizeChange = (size: number) => {
  emit('size-change', size)
}

const handleProductSelect = (product: Product) => {
  emit('product-select', product)
}

const handleAddToQuote = (product: Product) => {
  emit('add-to-quote', product)
}

const handleViewDetails = (product: Product) => {
  emit('view-details', product)
}
</script>

<style scoped>
.search-results {
  width: 100%;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 16px 0;
  border-bottom: 1px solid #e4e7ed;
}

.results-info {
  font-size: 16px;
  color: #303133;
}

.search-query {
  color: #606266;
}

.results-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.view-toggle {
  border-radius: 6px;
}

.results-loading {
  padding: 24px 0;
}

.results-empty {
  text-align: center;
  padding: 80px 20px;
  color: #909399;
}

.empty-icon {
  margin-bottom: 24px;
  color: #c0c4cc;
}

.results-empty h3 {
  font-size: 20px;
  color: #606266;
  margin: 0 0 12px 0;
  font-weight: 500;
}

.results-empty p {
  font-size: 14px;
  margin: 0 0 32px 0;
  line-height: 1.6;
}

.search-suggestions {
  text-align: left;
  max-width: 400px;
  margin: 0 auto;
  padding: 24px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.search-suggestions h4 {
  font-size: 16px;
  color: #409eff;
  margin: 0 0 16px 0;
  font-weight: 600;
}

.search-suggestions ul {
  margin: 0;
  padding-left: 20px;
  color: #606266;
  line-height: 1.8;
}

.search-suggestions li {
  font-size: 14px;
  margin-bottom: 8px;
}

.results-container {
  margin-bottom: 32px;
}

.results-container.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

.results-container.list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.results-pagination {
  display: flex;
  justify-content: center;
  padding: 32px 0;
  border-top: 1px solid #e4e7ed;
}

@media (max-width: 1200px) {
  .results-container.grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 20px;
  }
}

@media (max-width: 768px) {
  .results-header {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }
  
  .results-controls {
    justify-content: space-between;
  }
  
  .results-container.grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .results-pagination {
    padding: 24px 0;
  }
  
  .results-pagination :deep(.el-pagination) {
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .results-empty {
    padding: 60px 16px;
  }
  
  .search-suggestions {
    padding: 20px;
  }
}
</style>