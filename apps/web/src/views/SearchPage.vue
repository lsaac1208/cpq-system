<template>
  <div class="search-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="container">
        <div class="header-content">
          <h1 class="page-title">产品搜索</h1>
          <p class="page-description">
            快速找到您需要的产品，支持按名称、型号、规格等多维度搜索
          </p>
        </div>
      </div>
    </div>

    <!-- 搜索区域 -->
    <div class="search-section">
      <div class="container">
        <SearchBox
          v-model="searchQuery"
          :show-hot-searches="!hasSearched"
          size="large"
          @search="handleSearch"
          @select-suggestion="handleSuggestionSelect"
        />
        
        <!-- 搜索历史 -->
        <div v-if="searchHistory.length > 0 && !hasSearched" class="search-history">
          <div class="history-header">
            <span class="history-title">搜索历史</span>
            <el-button 
              link 
              size="small" 
              @click="clearSearchHistory"
              class="clear-history"
            >
              清空
            </el-button>
          </div>
          <div class="history-list">
            <el-tag
              v-for="(history, index) in searchHistory"
              :key="index"
              class="history-tag"
              @click="selectHistorySearch(history)"
              closable
              @close="removeHistoryItem(index)"
            >
              {{ history }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>

    <!-- 搜索结果区域 -->
    <div class="results-section">
      <div class="container">
        <SearchResults
          :search-result="searchResult"
          :loading="searchLoading"
          :view-mode="viewMode"
          :sort="sortBy"
          @update:view-mode="viewMode = $event"
          @update:sort="handleSortChange"
          @page-change="handlePageChange"
          @size-change="handleSizeChange"
          @product-select="handleProductSelect"
          @add-to-quote="handleAddToQuote"
          @view-details="handleViewDetails"
        />
      </div>
    </div>

    <!-- 批量搜索功能 -->
    <div v-if="!hasSearched" class="batch-search-section">
      <div class="container">
        <div class="batch-search-card">
          <div class="batch-header">
            <div class="batch-icon">
              <el-icon><Upload /></el-icon>
            </div>
            <div class="batch-content">
              <h3>批量搜索</h3>
              <p>上传CSV文件批量搜索多个产品，提高工作效率</p>
            </div>
            <div class="batch-actions">
              <el-button 
                type="primary"
                @click="showBatchDialog = true"
              >
                开始批量搜索
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 批量搜索对话框 -->
    <el-dialog
      v-model="showBatchDialog"
      title="批量搜索产品"
      width="600px"
      :close-on-click-modal="false"
    >
      <div class="batch-dialog">
        <el-steps :active="batchStep" align-center>
          <el-step title="上传文件" />
          <el-step title="处理中" />
          <el-step title="查看结果" />
        </el-steps>

        <!-- 步骤1: 文件上传 -->
        <div v-if="batchStep === 0" class="batch-upload">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :on-change="handleFileChange"
            :before-remove="handleFileRemove"
            accept=".csv"
            drag
            class="upload-area"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              将CSV文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                只能上传CSV文件，文件大小不超过10MB
              </div>
            </template>
          </el-upload>

          <div class="upload-config">
            <el-form :model="batchConfig" label-width="120px">
              <el-form-item label="查询列名">
                <el-input
                  v-model="batchConfig.query_column"
                  placeholder="包含搜索关键词的列名 (如: product_name)"
                />
              </el-form-item>
              <el-form-item label="每个查询返回">
                <el-input-number
                  v-model="batchConfig.per_query"
                  :min="1"
                  :max="50"
                />
                <span class="form-tip">个结果</span>
              </el-form-item>
            </el-form>
          </div>

          <div class="batch-actions">
            <el-button @click="showBatchDialog = false">取消</el-button>
            <el-button 
              type="primary"
              :disabled="!selectedFile"
              @click="startBatchSearch"
            >
              开始处理
            </el-button>
          </div>
        </div>

        <!-- 步骤2: 处理中 -->
        <div v-if="batchStep === 1" class="batch-processing">
          <div class="processing-content">
            <el-icon class="processing-icon"><Loading /></el-icon>
            <h3>正在处理批量搜索...</h3>
            <p>请稍等，正在处理您的文件</p>
          </div>
        </div>

        <!-- 步骤3: 结果展示 -->
        <div v-if="batchStep === 2" class="batch-results">
          <div class="results-summary">
            <div class="summary-item">
              <span class="label">总查询数:</span>
              <span class="value">{{ batchResult?.summary.total_queries || 0 }}</span>
            </div>
            <div class="summary-item">
              <span class="label">成功:</span>
              <span class="value success">{{ batchResult?.summary.successful || 0 }}</span>
            </div>
            <div class="summary-item">
              <span class="label">失败:</span>
              <span class="value error">{{ batchResult?.summary.failed || 0 }}</span>
            </div>
            <div class="summary-item">
              <span class="label">找到产品:</span>
              <span class="value">{{ batchResult?.summary.total_products_found || 0 }}</span>
            </div>
          </div>

          <div class="batch-actions">
            <el-button @click="resetBatchDialog">重新开始</el-button>
            <el-button 
              type="primary"
              @click="exportBatchResults"
              :loading="exportLoading"
            >
              导出结果
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { showMessage } from '@/utils/message'
import { Upload, UploadFilled, Loading } from '@element-plus/icons-vue'
import SearchBox from '@/components/search/SearchBox.vue'
import SearchResults from '@/components/search/SearchResults.vue'
import { SearchAPI, type SearchResult, type SearchOptions, type Product, type SearchSuggestion, type BatchSearchResult } from '@/api/search'

// 路由
const router = useRouter()
const route = useRoute()

// 搜索状态
const searchQuery = ref('')
const searchResult = ref<SearchResult | null>(null)
const searchLoading = ref(false)
const hasSearched = ref(false)

// 视图控制
const viewMode = ref<'grid' | 'list'>('grid')
const sortBy = ref('relevance')

// 搜索历史
const searchHistory = ref<string[]>([])
const maxHistoryItems = 10

// 批量搜索
const showBatchDialog = ref(false)
const batchStep = ref(0)
const selectedFile = ref<File | null>(null)
const batchConfig = reactive({
  query_column: 'product_name',
  per_query: 5
})
const batchResult = ref<BatchSearchResult | null>(null)
const exportLoading = ref(false)

// 分页参数
const currentPage = ref(1)
const pageSize = ref(20)

// 初始化
onMounted(() => {
  loadSearchHistory()
  
  // 从URL参数初始化搜索
  const queryParam = route.query.q as string
  if (queryParam) {
    searchQuery.value = queryParam
    performSearch()
  }
})

// 监听路由变化
watch(() => route.query.q, (newQuery) => {
  if (newQuery && newQuery !== searchQuery.value) {
    searchQuery.value = newQuery as string
    performSearch()
  }
})

// 加载搜索历史
const loadSearchHistory = () => {
  const stored = localStorage.getItem('search_history')
  if (stored) {
    try {
      searchHistory.value = JSON.parse(stored).slice(0, maxHistoryItems)
    } catch (error) {
      console.error('解析搜索历史失败:', error)
      searchHistory.value = []
    }
  }
}

// 保存搜索历史
const saveSearchHistory = (query: string) => {
  if (!query.trim()) return
  
  // 移除已存在的相同查询
  const index = searchHistory.value.indexOf(query)
  if (index > -1) {
    searchHistory.value.splice(index, 1)
  }
  
  // 添加到开头
  searchHistory.value.unshift(query)
  
  // 限制数量
  if (searchHistory.value.length > maxHistoryItems) {
    searchHistory.value = searchHistory.value.slice(0, maxHistoryItems)
  }
  
  // 保存到localStorage
  localStorage.setItem('search_history', JSON.stringify(searchHistory.value))
}

// 执行搜索
const performSearch = async () => {
  const query = searchQuery.value.trim()
  if (!query) return

  searchLoading.value = true
  hasSearched.value = true

  try {
    const options: SearchOptions = {
      query,
      sort: sortBy.value as any,
      page: currentPage.value,
      per_page: pageSize.value
    }

    const result = await SearchAPI.searchProducts(options)
    console.log('搜索API原始响应:', result)
    
    searchResult.value = result
    
    // 保存搜索历史
    saveSearchHistory(query)
    
    // 更新URL
    await router.replace({
      query: { 
        ...route.query, 
        q: query,
        page: currentPage.value > 1 ? currentPage.value : undefined,
        sort: sortBy.value !== 'relevance' ? sortBy.value : undefined
      }
    })

  } catch (error) {
    console.error('搜索失败:', error)
    showMessage.error('搜索失败，请稍后重试')
    searchResult.value = null
  } finally {
    searchLoading.value = false
  }
}

// 搜索事件处理
const handleSearch = (query: string) => {
  searchQuery.value = query
  currentPage.value = 1
  performSearch()
}

const handleSuggestionSelect = (suggestion: SearchSuggestion) => {
  searchQuery.value = suggestion.text
  currentPage.value = 1
  performSearch()
}

// 搜索历史操作
const selectHistorySearch = (query: string) => {
  searchQuery.value = query
  currentPage.value = 1
  performSearch()
}

const removeHistoryItem = (index: number) => {
  searchHistory.value.splice(index, 1)
  saveSearchHistory('')
}

const clearSearchHistory = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有搜索历史吗？', '确认清空', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    searchHistory.value = []
    localStorage.removeItem('search_history')
    showMessage.success('搜索历史已清空')
  } catch (error) {
    // 用户取消
  }
}

// 排序和分页
const handleSortChange = (sort: string) => {
  sortBy.value = sort
  currentPage.value = 1
  performSearch()
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  performSearch()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  performSearch()
}

// 产品操作
const handleProductSelect = (product: Product) => {
  // 跳转到产品详情页
  router.push(`/products/${product.id}`)
}

const handleAddToQuote = (product: Product) => {
  // 添加到询价单逻辑
  showMessage.success(`产品 "${product.name}" 已添加到询价单`)
}

const handleViewDetails = (product: Product) => {
  // 跳转到产品详情展示页（客户视角）
  router.push(`/products/${product.id}`)
}

// 批量搜索
const handleFileChange = (file: any) => {
  selectedFile.value = file.raw
}

const handleFileRemove = () => {
  selectedFile.value = null
}

const startBatchSearch = async () => {
  if (!selectedFile.value) return

  batchStep.value = 1

  try {
    batchResult.value = await SearchAPI.batchSearchFromFile(
      selectedFile.value,
      batchConfig
    )
    
    batchStep.value = 2
    showMessage.success('批量搜索完成')
  } catch (error) {
    console.error('批量搜索失败:', error)
    showMessage.error('批量搜索失败，请检查文件格式')
    resetBatchDialog()
  }
}

const resetBatchDialog = () => {
  batchStep.value = 0
  selectedFile.value = null
  batchResult.value = null
}

const exportBatchResults = async () => {
  if (!batchResult.value) return

  exportLoading.value = true

  try {
    const blob = await SearchAPI.exportBatchResults(batchResult.value.results)
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `batch_search_results_${new Date().getTime()}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    showMessage.success('结果导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    showMessage.error('导出失败')
  } finally {
    exportLoading.value = false
  }
}
</script>

<style scoped>
.search-page {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

/* 页面头部 */
.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 40px 0 60px;
}

.header-content {
  text-align: center;
}

.page-title {
  font-size: 32px;
  font-weight: 600;
  margin: 0 0 12px 0;
}

.page-description {
  font-size: 16px;
  opacity: 0.9;
  margin: 0;
  line-height: 1.6;
}

/* 搜索区域 */
.search-section {
  background: white;
  padding: 40px 0;
  margin-top: -40px;
  border-radius: 12px 12px 0 0;
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.1);
}

.search-history {
  margin-top: 24px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.history-title {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.clear-history {
  font-size: 12px;
  padding: 0;
}

.history-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.history-tag {
  cursor: pointer;
  transition: all 0.2s ease;
}

.history-tag:hover {
  background-color: #409eff;
  color: white;
}

/* 结果区域 */
.results-section {
  background: white;
  min-height: 400px;
  padding: 0 0 40px 0;
}

/* 批量搜索区域 */
.batch-search-section {
  background: white;
  padding: 40px 0;
  border-top: 1px solid #e4e7ed;
}

.batch-search-card {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  border-radius: 12px;
  color: white;
  overflow: hidden;
}

.batch-header {
  display: flex;
  align-items: center;
  padding: 32px;
  gap: 20px;
}

.batch-icon {
  font-size: 40px;
  opacity: 0.9;
}

.batch-content {
  flex: 1;
}

.batch-content h3 {
  font-size: 20px;
  margin: 0 0 8px 0;
  font-weight: 600;
}

.batch-content p {
  font-size: 14px;
  margin: 0;
  opacity: 0.9;
  line-height: 1.5;
}

.batch-actions .el-button {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
  color: white;
}

.batch-actions .el-button:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
}

/* 批量搜索对话框 */
.batch-dialog {
  padding: 20px 0;
}

.batch-upload {
  margin-top: 30px;
}

.upload-area {
  margin-bottom: 24px;
}

.upload-config {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 24px;
}

.form-tip {
  margin-left: 8px;
  font-size: 12px;
  color: #909399;
}

.batch-processing {
  text-align: center;
  padding: 40px 0;
}

.processing-icon {
  font-size: 48px;
  color: #409eff;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.processing-content h3 {
  font-size: 18px;
  color: #303133;
  margin: 0 0 8px 0;
}

.processing-content p {
  color: #606266;
  margin: 0;
}

.batch-results {
  margin-top: 30px;
}

.results-summary {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.summary-item .label {
  font-size: 14px;
  color: #606266;
}

.summary-item .value {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.summary-item .value.success {
  color: #67c23a;
}

.summary-item .value.error {
  color: #f56c6c;
}

.batch-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .container {
    padding: 0 16px;
  }
  
  .page-header {
    padding: 30px 0 50px;
  }
  
  .page-title {
    font-size: 24px;
  }
  
  .page-description {
    font-size: 14px;
  }
  
  .search-section {
    padding: 30px 0;
    margin-top: -30px;
  }
  
  .batch-header {
    flex-direction: column;
    text-align: center;
    gap: 16px;
  }
  
  .results-summary {
    grid-template-columns: 1fr;
  }
  
  .batch-actions {
    flex-direction: column;
  }
}

@media (max-width: 480px) {
  .history-list {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .batch-header {
    padding: 24px 20px;
  }
}
</style>