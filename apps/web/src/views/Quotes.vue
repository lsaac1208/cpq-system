<template>
  <div class="quotes">
    <div class="page-header">
      <h1>报价管理</h1>
      <div class="header-actions">
        <router-link to="/quotes/create">
          <el-button type="primary" size="large">
            <el-icon><Plus /></el-icon>
            创建报价
          </el-button>
        </router-link>
      </div>
    </div>

    <!-- Search and Filters -->
    <el-card class="filter-card">
      <!-- Search Bar -->
      <el-row :gutter="20" class="search-row">
        <el-col :span="24">
          <el-input
            v-model="searchQuery"
            placeholder="按报价单号、客户姓名、公司或邮箱搜索..."
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

      <!-- Filters -->
      <el-row :gutter="20" class="filter-row">
        <el-col :span="4">
          <el-select 
            v-model="filters.status" 
            placeholder="所有状态" 
            clearable 
            @change="loadQuotes"
            style="width: 100%"
          >
            <el-option label="所有状态" value="" />
            <el-option label="草稿" value="draft" />
            <el-option label="待审批" value="pending" />
            <el-option label="已审批" value="approved" />
            <el-option label="已拒绝" value="rejected" />
            <el-option label="已过期" value="expired" />
          </el-select>
        </el-col>
        <el-col :span="5">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            @change="handleDateRangeChange"
            style="width: 100%"
          />
        </el-col>
        <el-col :span="4">
          <el-input-number
            v-model="filters.min_amount"
            placeholder="最小金额"
            :min="0"
            :precision="2"
            @change="loadQuotes"
            style="width: 100%"
          />
        </el-col>
        <el-col :span="4">
          <el-input-number
            v-model="filters.max_amount"
            placeholder="最大金额"
            :min="0"
            :precision="2"  
            @change="loadQuotes"
            style="width: 100%"
          />
        </el-col>
        <el-col :span="4">
          <el-select
            v-model="filters.created_by"
            placeholder="查看范围"
            @change="loadQuotes"
            style="width: 100%"
          >
            <el-option label="我的报价" :value="currentUserId" />
            <el-option v-if="authStore.isAdmin" label="所有报价" value="all" />
            <!-- Additional admin options would be loaded from API -->
          </el-select>
        </el-col>
        <el-col :span="3">
          <el-select
            v-model="sortConfig.field"
            placeholder="排序方式"
            @change="loadQuotes"
            style="width: 100%"
          >
            <el-option label="创建日期" value="created_at" />
            <el-option label="金额" value="total_price" />
            <el-option label="客户" value="customer_name" />
            <el-option label="报价单号" value="quote_number" />
          </el-select>
        </el-col>
      </el-row>

      <!-- Filter Actions -->
      <el-row :gutter="20" class="action-row">
        <el-col :span="12">
          <el-button @click="resetFilters" icon="Refresh">重置筛选</el-button>
          <el-button @click="toggleSortOrder" link>
            <el-icon>
              <component :is="sortConfig.order === 'asc' ? 'SortUp' : 'SortDown'" />
            </el-icon>
            {{ sortConfig.order === 'asc' ? '升序' : '降序' }}
          </el-button>
        </el-col>
        <el-col :span="12" class="text-right">
          <span class="result-count">找到 {{ total }} 个报价</span>
          <el-button @click="exportQuotes" link icon="Download">导出</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- Quotes Table -->
    <el-card>
      <el-table 
        :data="quotes" 
        v-loading="loading" 
        style="width: 100%"
        @sort-change="handleSortChange"
        stripe
      >
        <el-table-column prop="quote_number" label="报价单号" width="140" sortable="custom">
          <template #default="{ row }">
            <router-link :to="`/quotes/${row.id}`" class="quote-link">
              <strong>{{ row.quote_number }}</strong>
            </router-link>
          </template>
        </el-table-column>
        
        <el-table-column label="客户" min-width="200" sortable="custom" prop="customer_name">
          <template #default="{ row }">
            <div class="customer-info">
              <strong>{{ row.customer_name }}</strong>
              <div class="customer-details">
                <div v-if="row.customer_company" class="company">{{ row.customer_company }}</div>
                <div class="email">{{ row.customer_email }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="130" sortable="custom">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="large">
              {{ formatStatus(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="项目" width="80" align="center">
          <template #default="{ row }">
            <el-badge :value="getItemCount(row)" type="primary">
              <el-icon><Menu /></el-icon>
            </el-badge>
          </template>
        </el-table-column>
        
        <el-table-column prop="total_price" label="金额" width="140" sortable="custom" align="right">
          <template #default="{ row }">
            <span class="amount">
              ${{ formatCurrency(row.total_price) }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="120" sortable="custom">
          <template #default="{ row }">
            <div class="date-info">
              <div>{{ formatDate(row.created_at) }}</div>
              <div class="created-by">{{ getUserName(row) }}</div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="有效期" width="120">
          <template #default="{ row }">
            <div class="validity-info">
              <div>{{ formatDate(row.valid_until) }}</div>
              <div :class="['validity-status', getValidityStatus(row.valid_until)]">
                {{ getValidityText(row.valid_until) }}
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <router-link :to="`/quotes/${row.id}`">
                <el-button size="small" type="primary" link icon="View">查看</el-button>
              </router-link>
              
              <el-button 
                v-if="row.status === 'draft' && canEditQuote(row)" 
                size="small" 
                type="primary" 
                @click="editQuote(row)"
                icon="Edit"
              >
                编辑
              </el-button>
              
              <el-dropdown 
                trigger="click"
                @command="handleQuoteAction"
              >
                <el-button size="small" type="info" icon="MoreFilled" />
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item 
                      :command="{ action: 'duplicate', quote: row }"
                      icon="DocumentCopy"
                    >
                      复制
                    </el-dropdown-item>
                    <el-dropdown-item 
                      :command="{ action: 'pdf', quote: row }"
                      icon="Download"
                    >
                      导出PDF
                    </el-dropdown-item>
                    <el-dropdown-item 
                      v-if="canDeleteQuote(row)"
                      :command="{ action: 'delete', quote: row }"
                      icon="Delete"
                      divided
                    >
                      删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="handlePageChange"
          @size-change="handlePageSizeChange"
        />
      </div>
    </el-card>

    <!-- Enhanced Empty State -->
    <el-empty 
      v-if="!loading && quotes.length === 0"
      :description="getEmptyStateMessage()"
      :image-size="200"
    >
      <template #default>
        <p v-if="!hasFilters && filters.created_by === currentUserId">
          创建您的第一个报价单开始使用
        </p>
        <p v-else-if="hasFilters">
          尝试调整筛选条件或清除筛选查看更多结果
        </p>
        <p v-else>
          系统中暂时没有报价单
        </p>
      </template>
      <template #extra>
        <router-link to="/quotes/create" v-if="getEmptyStateAction() === '创建报价'">
          <el-button type="primary">{{ getEmptyStateAction() }}</el-button>
        </router-link>
        <el-button v-else @click="resetFilters" type="primary">
          {{ getEmptyStateAction() }}
        </el-button>
      </template>
    </el-empty>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { unifiedQuotesApi, quotesApi } from '@/api/quotes'
import { useAuthStore } from '@/stores/auth'
import { ElMessageBox } from 'element-plus'
import { showMessage } from '@/utils/message'
import { 
  Plus, 
  Search, 
  View, 
  Edit, 
  MoreFilled,
  SortUp,
  SortDown
} from '@element-plus/icons-vue'
import { unifiedChinesePDFGenerator, createQuotePDFDataFromSettings } from '@/utils/unifiedChinesePDFGenerator'
import type { Quote, QuoteSearchParams } from '@/types/quote'

const router = useRouter()
const authStore = useAuthStore()

const quotes = ref<Quote[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchQuery = ref('')
const dateRange = ref<[Date, Date] | null>(null)
const searchTimeout = ref<NodeJS.Timeout>()

const currentUserId = computed(() => authStore.user?.id)

const filters = reactive<QuoteSearchParams>({
  search: '',
  status: '',
  min_amount: null,
  max_amount: null,
  date_from: '',
  date_to: '',
  created_by: null, // Will be set to currentUserId in onMounted for non-admin users
  page: 1,
  per_page: 20
})

const sortConfig = reactive({
  field: 'created_at',
  order: 'desc' as 'asc' | 'desc'
})

const hasFilters = computed(() => {
  return !!(
    filters.search ||
    filters.status ||
    filters.min_amount ||
    filters.max_amount ||
    filters.date_from ||
    filters.date_to ||
    // Don't count default user filter as an active filter for UX
    (filters.created_by && filters.created_by !== currentUserId.value)
  )
})

// Enhanced empty state messages based on user context
const getEmptyStateMessage = () => {
  const isShowingPersonalQuotes = filters.created_by === currentUserId.value
  
  if (isShowingPersonalQuotes && !hasFilters.value) {
    return "您还没有创建任何报价单"
  } else if (isShowingPersonalQuotes && hasFilters.value) {
    return "没有找到符合条件的报价单"
  } else if (!isShowingPersonalQuotes && authStore.isAdmin) {
    return "系统中暂无报价单"
  } else {
    return "没有找到符合条件的报价单"
  }
}

const getEmptyStateAction = () => {
  const isShowingPersonalQuotes = filters.created_by === currentUserId.value
  
  if (isShowingPersonalQuotes && !hasFilters.value) {
    return "创建报价"
  } else if (hasFilters.value) {
    return "清除筛选"
  } else {
    return "创建报价"
  }
}

// Status and formatting functions
const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    draft: 'info',
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    expired: 'warning'
  }
  return types[status] || 'info'
}

const formatStatus = (status: string) => {
  const statusMap: Record<string, string> = {
    draft: '草稿',
    pending: '待审批',
    approved: '已审批',
    rejected: '已拒绝',
    expired: '已过期'
  }
  return statusMap[status] || status.charAt(0).toUpperCase() + status.slice(1)
}

const formatDate = (dateString?: string) => {
  if (!dateString) return '无'
  return new Date(dateString).toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}

const getValidityStatus = (validUntil?: string) => {
  if (!validUntil) return 'unknown'
  
  const expiryDate = new Date(validUntil)
  const today = new Date()
  const diffTime = expiryDate.getTime() - today.getTime()
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  
  if (diffDays < 0) return 'expired'
  if (diffDays <= 7) return 'expiring'
  return 'valid'
}

const getValidityText = (validUntil?: string) => {
  if (!validUntil) return 'No expiry'
  
  const expiryDate = new Date(validUntil)
  const today = new Date()
  const diffTime = expiryDate.getTime() - today.getTime()
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  
  if (diffDays < 0) return 'Expired'
  if (diffDays === 0) return 'Today'
  if (diffDays <= 7) return `${diffDays}d left`
  return 'Valid'
}

// Permission checks
const canEditQuote = (quote: Quote) => {
  return quote.created_by === currentUserId.value || authStore.isAdmin
}

const canDeleteQuote = (quote: Quote) => {
  return quote.created_by === currentUserId.value || authStore.isAdmin
}

// Helper function to get item count for both single and multi-product quotes
const getItemCount = (quote: Quote) => {
  // For multi-product quotes, return items array length
  if (quote.items && Array.isArray(quote.items)) {
    return quote.items.length
  }
  // For single-product quotes, return 1 if product_id exists, 0 otherwise
  if (quote.product_id || quote.product) {
    return 1
  }
  return 0
}

// Helper function to format currency safely
const formatCurrency = (amount?: number) => {
  if (typeof amount !== 'number' || isNaN(amount)) {
    return '0.00'
  }
  return amount.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

// Helper function to get user name safely
const getUserName = (quote: Quote) => {
  return quote.created_by_user?.name || 'Unknown User'
}

// Search and filter functions
const handleSearch = () => {
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value)
  }
  
  searchTimeout.value = setTimeout(() => {
    filters.search = searchQuery.value
    currentPage.value = 1
    loadQuotes()
  }, 300)
}

const handleSearchClear = () => {
  searchQuery.value = ''
  filters.search = ''
  loadQuotes()
}

const handleDateRangeChange = (dates: [Date, Date] | null) => {
  if (dates) {
    filters.date_from = dates[0].toISOString().split('T')[0]
    filters.date_to = dates[1].toISOString().split('T')[0]
  } else {
    filters.date_from = ''
    filters.date_to = ''
  }
  loadQuotes()
}

const resetFilters = () => {
  searchQuery.value = ''
  dateRange.value = null
  Object.assign(filters, {
    search: '',
    status: '',
    min_amount: null,
    max_amount: null,
    date_from: '',
    date_to: '',
    created_by: null
  })
  currentPage.value = 1
  loadQuotes()
}

const toggleSortOrder = () => {
  sortConfig.order = sortConfig.order === 'asc' ? 'desc' : 'asc'
  loadQuotes()
}

const handleSortChange = ({ prop, order }: { prop: string; order: string | null }) => {
  if (prop && order) {
    sortConfig.field = prop
    sortConfig.order = order === 'ascending' ? 'asc' : 'desc'
    loadQuotes()
  }
}

// Data loading - 重写为直接API调用
const loadQuotes = async () => {
  loading.value = true
  try {
    // 构建查询参数
    const queryParams = new URLSearchParams()
    if (filters.search) queryParams.append('search', filters.search)
    if (filters.status) queryParams.append('status', filters.status)
    if (filters.date_from) queryParams.append('date_from', filters.date_from)
    if (filters.date_to) queryParams.append('date_to', filters.date_to)
    if (filters.created_by) queryParams.append('created_by', filters.created_by.toString())
    queryParams.append('page', currentPage.value.toString())
    queryParams.append('per_page', pageSize.value.toString())
    queryParams.append('sort_by', sortConfig.field)
    queryParams.append('sort_order', sortConfig.order)

    console.log('🔍 API调用参数:', queryParams.toString())

    // 直接使用fetch调用API
    const token = localStorage.getItem('cpq_access_token')
    if (!token) {
      throw new Error('用户未登录')
    }

    const response = await fetch(`/api/v1/quotes?${queryParams}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      throw new Error(`API调用失败: ${response.status}`)
    }

    const data = await response.json()
    console.log('📊 API原始响应:', data)

    // 直接处理响应数据
    if (data && data.quotes && Array.isArray(data.quotes)) {
      quotes.value = data.quotes
      total.value = data.pagination?.total || data.quotes.length
      console.log(`✅ 成功加载${quotes.value.length}个报价，总计${total.value}个`)
    } else {
      console.warn('⚠️ API响应格式异常:', data)
      quotes.value = []
      total.value = 0
      showMessage.warning('无法加载报价数据，请检查服务器连接')
    }
  } catch (error: any) {
    console.error('Error loading quotes:', error)
    quotes.value = []
    total.value = 0
    
    // Provide more specific error messages
    if (error.response) {
      const status = error.response.status
      const message = error.response.data?.message || error.message
      console.error('API Error:', { status, message, data: error.response.data })
      
      if (status === 404) {
        showMessage.error('Quotes endpoint not found. Please check API configuration.')
      } else if (status >= 500) {
        showMessage.error('Server error. Please try again later.')
      } else {
        showMessage.error(`Failed to load quotes: ${message}`)
      }
    } else if (error.request) {
      console.error('Network Error:', error.request)
      showMessage.error('Network error. Please check your connection.')
    } else {
      console.error('Error:', error.message)
      showMessage.error('Failed to load quotes')
    }
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  loadQuotes()
}

const handlePageSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadQuotes()
}

// Quote actions
const editQuote = (quote: Quote) => {
  router.push(`/quotes/${quote.id}/edit`)
}

const handleQuoteAction = async ({ action, quote }: { action: string; quote: Quote }) => {
  switch (action) {
    case 'duplicate':
      await duplicateQuote(quote)
      break
    case 'pdf':
      await exportQuotePDF(quote)
      break
    case 'delete':
      await deleteQuote(quote)
      break
  }
}

const duplicateQuote = async (quote: Quote) => {
  try {
    await ElMessageBox.confirm(
      'This will create a new quote with the same items and customer information. Continue?',
      'Duplicate Quote',
      {
        confirmButtonText: 'Create Duplicate',
        cancelButtonText: 'Cancel',
        type: 'info'
      }
    )
    
    showMessage.info('Duplicate functionality will be implemented in the next phase')
  } catch {
    // User cancelled
  }
}

const exportQuotePDF = async (quote: Quote) => {
  try {
    const pdfData = await createQuotePDFDataFromSettings(quote)
    await unifiedChinesePDFGenerator.downloadPDF(pdfData, `报价单-${quote.quote_number}`)
    showMessage.success('PDF导出成功')
  } catch (error) {
    console.error('PDF export error:', error)
    showMessage.error('PDF导出失败')
  }
}

const deleteQuote = async (quote: Quote) => {
  try {
    // Provide different confirmation messages based on quote status
    const statusWarnings: Record<string, string> = {
      'approved': '此报价已通过审批，删除后将无法恢复。',
      'pending': '此报价正在等待审批，删除后将无法恢复。',
      'rejected': '此报价已被拒绝，确认删除？',
      'expired': '此报价已过期，确认删除？',
      'draft': '确认删除此草稿报价？'
    }
    
    const warningMessage = statusWarnings[quote.status] || '确认删除此报价？'
    const statusText = formatStatus(quote.status)
    
    await ElMessageBox.confirm(
      `${warningMessage}\n\n报价单号: ${quote.quote_number}\n状态: ${statusText}\n\n此操作不可撤销，请谨慎操作。`,
      '删除报价确认',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        type: 'warning',
        dangerouslyUseHTMLString: false
      }
    )
    
    const response = await unifiedQuotesApi.deleteQuote(quote.id)
    
    // Use the message from backend if available
    const successMessage = response.message || '报价删除成功'
    showMessage.success(successMessage)
    
    // Reload the quotes list
    loadQuotes()
  } catch (error: any) {
    // User cancelled the confirmation dialog
    if (error === 'cancel') {
      return
    }
    
    // Handle API errors with better user feedback
    console.error('Error deleting quote:', error)
    
    let errorMessage = '删除报价失败'
    
    if (error.response) {
      const status = error.response.status
      const backendMessage = error.response.data?.error || error.response.data?.message
      
      switch (status) {
        case 403:
          errorMessage = '权限不足：' + (backendMessage || '您没有权限删除这个报价')
          break
        case 404:
          errorMessage = '报价不存在或已被删除'
          break
        case 500:
          errorMessage = '服务器错误：' + (backendMessage || '请稍后重试')
          break
        default:
          errorMessage = backendMessage || `删除失败 (错误代码: ${status})`
      }
    } else if (error.request) {
      errorMessage = '网络连接错误，请检查网络后重试'
    } else {
      errorMessage = error.message || '未知错误'
    }
    
    showMessage.error(errorMessage)
  }
}

const exportQuotes = () => {
  showMessage.info('Bulk export functionality will be implemented in the next phase')
}

onMounted(() => {
  // 🎯 修复：管理员默认查看所有报价，解决"No Data"问题
  if (!authStore.isAdmin) {
    filters.created_by = currentUserId.value
  } else {
    // 管理员默认查看所有报价（不设置created_by筛选）
    filters.created_by = null
  }
  
  loadQuotes()
})
</script>

<style scoped>
.quotes {
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
  gap: 12px;
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
  margin-right: 12px;
}

.quote-link {
  text-decoration: none;
  color: #409EFF;
}

.quote-link:hover {
  color: #66b1ff;
}

.customer-info {
  line-height: 1.4;
}

.customer-details {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.company {
  font-weight: 500;
  color: #606266;
}

.email {
  margin-top: 1px;
}

.amount {
  font-weight: 600;
  color: #67C23A;
}

.date-info {
  line-height: 1.4;
}

.created-by {
  font-size: 11px;
  color: #909399;
  margin-top: 1px;
}

.validity-info {
  line-height: 1.4;
}

.validity-status {
  font-size: 11px;
  margin-top: 1px;
}

.validity-status.valid {
  color: #67C23A;
}

.validity-status.expiring {
  color: #E6A23C;
}

.validity-status.expired {
  color: #F56C6C;
}

.validity-status.unknown {
  color: #909399;
}

.action-buttons {
  display: flex;
  gap: 4px;
  align-items: center;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
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
  
  .action-buttons {
    flex-direction: column;
    gap: 2px;
  }
  
  .action-buttons .el-button {
    font-size: 12px;
    padding: 4px 8px;
  }
}
</style>