<template>
  <div class="products">
    <div class="page-header">
      <h1>产品管理</h1>
      <div class="header-actions">
        <!-- Quote Creation Actions -->
        <div v-if="selectedProducts.length > 0" class="quote-actions">
          <el-button type="success" @click="createQuoteFromSelected" size="large">
            <el-icon><Document /></el-icon>
            创建报价 (已选择{{ selectedProducts.length }}个)
          </el-button>
          <el-button type="info" @click="clearSelection" size="large">
            清除选择
          </el-button>
        </div>
        
        <!-- Product Management Actions -->
        <el-button 
          v-if="authStore.canEditProducts"
          type="primary" 
          @click="showCreateDialog = true"
        >
          <el-icon><Plus /></el-icon>
          添加产品
        </el-button>
        <el-button 
          type="success" 
          @click="exportProductCatalog"
          :loading="exportingCatalog"
          icon="Download"
        >
          导出产品目录
        </el-button>
      </div>
    </div>

    <!-- Search and Filters -->
    <el-card class="filter-card">
      <!-- Search Bar -->
      <el-row :gutter="20" class="search-row">
        <el-col :span="24">
          <el-input
            v-model="searchQuery"
            placeholder="按产品名称、SKU或描述搜索..."
            clearable
            size="large"
            @input="handleSearch"
            @clear="handleSearchClear"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
      </el-row>

      <!-- Advanced Filters -->
      <el-row :gutter="20" class="filter-row">
        <el-col :span="6">
          <el-select 
            v-model="filters.category" 
            placeholder="所有分类" 
            clearable 
            @change="loadProducts"
            style="width: 100%"
          >
            <el-option label="所有分类" value="" />
            <el-option 
              v-for="category in categories"
              :key="category"
              :label="category"
              :value="category"
            />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select 
            v-model="filters.is_active" 
            placeholder="状态" 
            @change="loadProducts"
            style="width: 100%"
          >
            <el-option label="所有状态" value="" />
            <el-option label="活跃" :value="true" />
            <el-option label="非活跃" :value="false" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select 
            v-model="filters.configurable" 
            placeholder="可配置性" 
            clearable
            @change="loadProducts"
            style="width: 100%"
          >
            <el-option label="所有类型" value="" />
            <el-option label="可配置" :value="true" />
            <el-option label="标准" :value="false" />
          </el-select>
        </el-col>
        <el-col :span="5">
          <el-input-number
            v-model="filters.min_price"
            placeholder="最低价格"
            :min="0"
            :precision="2"
            @change="loadProducts"
            style="width: 100%"
          />
        </el-col>
        <el-col :span="5">
          <el-input-number
            v-model="filters.max_price"
            placeholder="最高价格"
            :min="0"
            :precision="2"
            @change="loadProducts"
            style="width: 100%"
          />
        </el-col>
      </el-row>

      <!-- Filter Actions -->
      <el-row :gutter="20" class="action-row">
        <el-col :span="12">
          <el-button @click="resetFilters" icon="Refresh">重置筛选</el-button>
          <el-button @click="toggleAdvancedFilters" link>
            {{ showAdvancedFilters ? '隐藏' : '显示' }}高级筛选
          </el-button>
        </el-col>
        <el-col :span="12" class="text-right">
          <span class="result-count">找到 {{ productsStore.total }} 个产品</span>
        </el-col>
      </el-row>

      <!-- Technical Specifications Filter (Advanced) -->
      <div v-if="showAdvancedFilters" class="advanced-filters">
        <el-divider content-position="left">技术规格</el-divider>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-select
              v-model="specFilter.key"
              placeholder="选择规格"
              clearable
              @change="loadSpecValues"
              style="width: 100%"
            >
              <el-option
                v-for="spec in availableSpecs"
                :key="spec.key"
                :label="spec.label"
                :value="spec.key"
              />
            </el-select>
          </el-col>
          <el-col :span="8">
            <el-select
              v-model="specFilter.value"
              placeholder="选择值"
              clearable
              :disabled="!specFilter.key"
              @change="applySpecFilter"
              style="width: 100%"
            >
              <el-option
                v-for="value in specValues"
                :key="value"
                :label="value"
                :value="value"
              />
            </el-select>
          </el-col>
          <el-col :span="8">
            <el-button @click="clearSpecFilter" icon="Close">清除</el-button>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- Products Table -->
    <el-card>
      <el-table 
        :data="productsStore.products" 
        v-loading="productsStore.loading" 
        style="width: 100%"
        @selection-change="handleSelectionChange"
        ref="productTable"
      >
        <!-- Selection Column -->
        <el-table-column
          type="selection"
          width="55"
          :selectable="row => row.is_active"
        />
        
        <el-table-column prop="code" label="产品代码" width="120" />
        <el-table-column prop="name" label="产品名称" min-width="200">
          <template #default="{ row }">
            <div class="product-name">
              <strong>{{ row.name }}</strong>
              <div class="product-description" v-if="row.description">
                {{ row.description }}
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="120" />
        <el-table-column prop="base_price" label="基础价格" width="120">
          <template #default="{ row }">
            ${{ row.base_price?.toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="is_configurable" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_configurable ? 'warning' : 'info'" size="small">
              {{ row.is_configurable ? '可配置' : '标准' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '活跃' : '非活跃' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="viewProduct(row)">查看详情</el-button>
            <el-button 
              v-if="authStore.canEditProducts"
              size="small" 
              type="primary" 
              @click="editProduct(row)"
            >
              快速编辑
            </el-button>
            <el-popconfirm
              v-if="authStore.canDeleteProducts"
              title="确定要停用该产品吗？"
              confirm-button-text="确定"
              cancel-button-text="取消"
              @confirm="deleteProduct(row.id)"
            >
              <template #reference>
                <el-button 
                  size="small" 
                  type="danger"
                  :disabled="!row.is_active"
                >
                  删除
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="productsStore.total"
          layout="total, prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingProduct ? '编辑产品' : '创建产品'"
      width="90%"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <ProductForm
        ref="productFormRef"
        :product="editingProduct"
        :categories="categories"
        :loading="productsStore.loading"
        @submit="saveProduct"
        @cancel="closeDialog"
      />
    </el-dialog>

    <!-- Product Detail Dialog -->
    <el-dialog
      v-model="showDetailDialog"
      :title="currentProduct?.name"
      width="80%"
    >
      <div v-if="currentProduct" class="product-detail">
        <el-descriptions title="基本信息" :column="2" border>
          <el-descriptions-item label="产品代码">
            {{ currentProduct.code }}
          </el-descriptions-item>
          <el-descriptions-item label="分类">
            {{ currentProduct.category }}
          </el-descriptions-item>
          <el-descriptions-item label="基础价格">
            ${{ currentProduct.base_price?.toLocaleString() }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="currentProduct.is_active ? 'success' : 'danger'">
              {{ currentProduct.is_active ? '活跃' : '非活跃' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="可配置">
            <el-tag :type="currentProduct.is_configurable ? 'success' : 'info'">
              {{ currentProduct.is_configurable ? '是' : '否' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ currentProduct.description || '暂无描述' }}
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="currentProduct.specifications && Object.keys(currentProduct.specifications).length > 0" class="mt-4">
          <h3>技术规格</h3>
          <el-table :data="specificationsTableData" style="width: 100%">
            <el-table-column prop="name" label="规格" />
            <el-table-column prop="value" label="值" />
            <el-table-column prop="unit" label="单位" />
            <el-table-column prop="description" label="描述" />
          </el-table>
        </div>

        <div v-if="currentProduct.configuration_schema && Object.keys(currentProduct.configuration_schema).length > 0" class="mt-4">
          <h3>配置字段</h3>
          <el-table :data="configSchemaTableData" style="width: 100%">
            <el-table-column prop="name" label="字段名" />
            <el-table-column prop="label" label="标签" />
            <el-table-column prop="type" label="类型" />
            <el-table-column prop="required" label="必填">
              <template #default="{ row }">
                <el-tag :type="row.required ? 'success' : 'info'">
                  {{ row.required ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" />
          </el-table>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, reactive, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useProductsStore } from '@/stores/products'
import { useAuthStore } from '@/stores/auth'
// ElMessage removed
import { showMessage } from '@/utils/message'
import { Plus, Search } from '@element-plus/icons-vue'
import ProductForm from '@/components/ProductForm.vue'
import { generateProductCatalogPDF } from '@/utils/productCatalogGenerator'
import type { Product, ProductFormData } from '@/types/product'

const router = useRouter()
const productsStore = useProductsStore()
const authStore = useAuthStore()

const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const editingProduct = ref<Product | null>(null)
const currentProduct = ref<Product | null>(null)
const categories = ref<string[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const productTable = ref()

// Search and filter state
const searchQuery = ref('')
const showAdvancedFilters = ref(false)
const selectedProducts = ref<Product[]>([])
const exportingCatalog = ref(false)
const searchTimeout = ref<NodeJS.Timeout>()

const filters = reactive({
  category: '',
  is_active: true,
  configurable: '',
  min_price: null as number | null,
  max_price: null as number | null,
  search: ''
})

// Advanced specification filter
const specFilter = reactive({
  key: '',
  value: ''
})

const availableSpecs = ref<{ key: string, label: string }[]>([])
const specValues = ref<string[]>([])

// Computed properties for product detail tables
const specificationsTableData = computed(() => {
  if (!currentProduct.value?.specifications) return []
  return Object.entries(currentProduct.value.specifications).map(([name, spec]) => ({
    name,
    value: typeof spec === 'object' ? spec.value : spec,
    unit: typeof spec === 'object' ? spec.unit : '',
    description: typeof spec === 'object' ? spec.description : ''
  }))
})

const configSchemaTableData = computed(() => {
  if (!currentProduct.value?.configuration_schema) return []
  return Object.entries(currentProduct.value.configuration_schema).map(([name, field]) => ({
    name,
    label: (field as any).label || name,
    type: (field as any).type || 'text',
    required: (field as any).required || false,
    description: (field as any).description || ''
  }))
})

// Search and filter functions
const handleSearch = () => {
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value)
  }
  
  searchTimeout.value = setTimeout(() => {
    filters.search = searchQuery.value
    currentPage.value = 1
    loadProducts()
  }, 300) // Debounce search for 300ms
}

const handleSearchClear = () => {
  searchQuery.value = ''
  filters.search = ''
  loadProducts()
}

const toggleAdvancedFilters = () => {
  showAdvancedFilters.value = !showAdvancedFilters.value
  if (showAdvancedFilters.value) {
    loadAvailableSpecs()
  }
}

const resetFilters = () => {
  searchQuery.value = ''
  filters.category = ''
  filters.is_active = true
  filters.configurable = ''
  filters.min_price = null
  filters.max_price = null
  filters.search = ''
  specFilter.key = ''
  specFilter.value = ''
  currentPage.value = 1
  loadProducts()
}

// Product selection functions
const handleSelectionChange = (selection: Product[]) => {
  selectedProducts.value = selection
}

const clearSelection = () => {
  selectedProducts.value = []
  if (productTable.value) {
    productTable.value.clearSelection()
  }
}

const createQuoteFromSelected = () => {
  if (selectedProducts.value.length === 0) {
    showMessage.warning('Please select at least one product')
    return
  }

  // Navigate to create quote page with selected products
  const productIds = selectedProducts.value.map(p => p.id)
  router.push({
    name: 'CreateQuote',
    query: {
      products: productIds.join(',')
    }
  })
}

// Advanced specification filter functions
const loadAvailableSpecs = async () => {
  try {
    // Extract unique specifications from all products
    const specs = new Map<string, string>()
    
    productsStore.products.forEach(product => {
      if (product.specifications) {
        Object.keys(product.specifications).forEach(key => {
          if (!specs.has(key)) {
            specs.set(key, key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' '))
          }
        })
      }
    })

    availableSpecs.value = Array.from(specs.entries()).map(([key, label]) => ({ key, label }))
  } catch (error) {
    console.error('Failed to load specifications:', error)
  }
}

const loadSpecValues = () => {
  if (!specFilter.key) {
    specValues.value = []
    return
  }

  const values = new Set<string>()
  productsStore.products.forEach(product => {
    if (product.specifications && product.specifications[specFilter.key]) {
      const spec = product.specifications[specFilter.key]
      const value = typeof spec === 'object' ? spec.value : spec
      if (value) {
        values.add(String(value))
      }
    }
  })

  specValues.value = Array.from(values).sort()
}

const applySpecFilter = () => {
  // This would typically be handled by the backend API
  // For now, we'll reload products with the spec filter
  loadProducts()
}

const clearSpecFilter = () => {
  specFilter.key = ''
  specFilter.value = ''
  specValues.value = []
  loadProducts()
}

const loadProducts = async () => {
  try {
    await productsStore.loadProducts({
      ...filters,
      page: currentPage.value,
      per_page: pageSize.value
    })
  } catch (error) {
    showMessage.error('Failed to load products')
  }
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  loadProducts()
}

const viewProduct = (product: Product) => {
  // 跳转到统一的产品详情页面
  router.push(`/products/${product.id}`)
}

const editProduct = (product: Product) => {
  // 快速编辑（弹窗模式）
  editingProduct.value = product
  showCreateDialog.value = true
}

const productFormRef = ref<any>(null)

const saveProduct = async (formData: ProductFormData, pendingImage?: File) => {
  try {
    if (editingProduct.value) {
      await productsStore.updateProduct(editingProduct.value.id, formData)
      showMessage.success('产品更新成功')
    } else {
      // 创建产品
      const response = await productsStore.createProduct(formData)
      
      // 如果有待上传的图片，在产品创建后上传
      if (pendingImage && response.product?.id && productFormRef.value) {
        await productFormRef.value.uploadImageAfterCreate(response.product.id.toString())
      } else {
        showMessage.success('产品创建成功')
      }
    }
    
    closeDialog()
    loadProducts()
  } catch (error) {
    showMessage.error('保存产品失败')
  }
}

const deleteProduct = async (productId: number) => {
  try {
    await productsStore.deleteProduct(productId)
    showMessage.success('Product deactivated successfully')
    loadProducts()
  } catch (error) {
    showMessage.error('Failed to delete product')
  }
}

const closeDialog = () => {
  showCreateDialog.value = false
  editingProduct.value = null
}

// Product catalog export
const exportProductCatalog = async () => {
  try {
    exportingCatalog.value = true
    
    // Get all products (not just current page)
    const allProducts = await productsStore.loadAllProductsForCatalog()
    
    if (allProducts.length === 0) {
      showMessage.warning('没有可导出的产品')
      return
    }
    
    await generateProductCatalogPDF(allProducts)
    showMessage.success('产品目录导出成功')
  } catch (error) {
    console.error('导出产品目录失败:', error)
    showMessage.error('导出产品目录失败')
  } finally {
    exportingCatalog.value = false
  }
}

onMounted(async () => {
  try {
    await loadProducts()
    const loadedCategories = await productsStore.loadCategories()
    categories.value = Array.isArray(loadedCategories) ? loadedCategories : []
  } catch (error) {
    console.error('Failed to load data:', error)
    categories.value = []
  }
})
</script>

<style scoped>
.products {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 16px;
}

.page-header h1 {
  margin: 0;
  color: #303133;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.quote-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #f0f9ff;
  border: 1px solid #e1f5fe;
  border-radius: 8px;
}

.filter-card {
  margin-bottom: 20px;
}

.search-row {
  margin-bottom: 16px;
}

.filter-row {
  margin-bottom: 12px;
}

.action-row {
  margin-bottom: 8px;
}

.text-right {
  text-align: right;
}

.result-count {
  color: #606266;
  font-size: 14px;
}

.advanced-filters {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.product-detail h3 {
  margin: 24px 0 16px 0;
  color: #303133;
  font-size: 18px;
  font-weight: 600;
}

.product-name {
  line-height: 1.4;
}

.product-name strong {
  color: #303133;
  font-size: 14px;
}

.product-description {
  color: #909399;
  font-size: 12px;
  margin-top: 4px;
  line-height: 1.3;
}

.mt-4 {
  margin-top: 24px;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: center;
  }
  
  .quote-actions {
    flex-direction: column;
    gap: 8px;
  }
  
  .filter-row .el-col {
    margin-bottom: 12px;
  }
  
  .action-row .el-col {
    text-align: center;
  }
  
  .result-count {
    text-align: center;
    margin-top: 8px;
  }
}
</style>