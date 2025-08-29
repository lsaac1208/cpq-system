<template>
  <div class="quote-detail">
    <div class="page-header">
      <h1>报价详情</h1>
      <div class="header-actions">
        <el-button @click="$router.go(-1)">返回</el-button>
        <el-button 
          v-if="quote?.status === 'draft'" 
          type="primary" 
          @click="editQuote"
        >
          编辑
        </el-button>
        <el-button 
          type="success" 
          @click="generatePDF"
          :loading="generatingPDF"
          icon="Download"
        >
          导出PDF
        </el-button>
      </div>
    </div>

    <div v-if="quote" class="quote-content">
      <!-- Quote Header Information -->
      <el-row :gutter="20">
        <el-col :span="16">
          <el-card class="quote-info-card">
            <template #header>
              <div class="card-header">
                <span class="card-title">报价信息</span>
                <el-tag :type="getStatusType(quote.status)" size="large">
                  {{ formatStatus(quote.status) }}
                </el-tag>
              </div>
            </template>
            
            <el-descriptions :column="2" border>
              <el-descriptions-item label="报价单号">
                <strong>{{ quote.quote_number }}</strong>
              </el-descriptions-item>
              <el-descriptions-item label="版本">
                {{ quote.version || 1 }}
              </el-descriptions-item>
              <el-descriptions-item label="创建日期">
                {{ formatDate(quote.created_at) }}
              </el-descriptions-item>
              <el-descriptions-item label="有效期至">
                {{ formatDate(quote.valid_until) }}
              </el-descriptions-item>
              <el-descriptions-item label="创建人">
                {{ quote.created_by_user?.name || '未知' }}
              </el-descriptions-item>
              <el-descriptions-item label="总金额">
                <strong class="total-amount">${{ quote.total_price?.toLocaleString() }}</strong>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>

          <!-- Customer Information -->
          <el-card class="customer-info-card">
            <template #header>
              <span class="card-title">客户信息</span>
            </template>
            
            <el-descriptions :column="2" border>
              <el-descriptions-item label="客户名称">
                {{ quote.customer_name }}
              </el-descriptions-item>
              <el-descriptions-item label="邮箱">
                {{ quote.customer_email }}
              </el-descriptions-item>
              <el-descriptions-item label="公司">
                {{ quote.customer_company || '暂无' }}
              </el-descriptions-item>
              <el-descriptions-item label="电话">
                {{ quote.customer_phone || '暂无' }}
              </el-descriptions-item>
              <el-descriptions-item label="地址" :span="2">
                {{ quote.customer_address || '暂无' }}
              </el-descriptions-item>
            </el-descriptions>
          </el-card>

          <!-- Quote Items -->
          <el-card class="items-card">
            <template #header>
              <span class="card-title">报价项目</span>
            </template>
            
            <el-table 
              :data="quote.items || []" 
              style="width: 100%"
              class="items-table"
            >
              <el-table-column label="产品" min-width="200">
                <template #default="{ row }">
                  <div class="product-info">
                    <strong>{{ row.product?.name }}</strong>
                    <div class="product-code">{{ row.product?.code }}</div>
                    <div v-if="row.product?.description" class="product-description">
                      {{ row.product.description }}
                    </div>
                  </div>
                </template>
              </el-table-column>
              
              <el-table-column label="数量" width="100" align="center">
                <template #default="{ row }">
                  {{ row.quantity }}
                </template>
              </el-table-column>
              
              <el-table-column label="单价" width="120" align="right">
                <template #default="{ row }">
                  ${{ row.unit_price?.toLocaleString() }}
                </template>
              </el-table-column>
              
              <el-table-column label="折扣" width="100" align="center">
                <template #default="{ row }">
                  {{ row.discount_percentage ? `${row.discount_percentage}%` : '-' }}
                </template>
              </el-table-column>
              
              <el-table-column label="小计" width="120" align="right">
                <template #default="{ row }">
                  <span class="line-total">
                    ${{ row.line_total?.toLocaleString() }}
                  </span>
                </template>
              </el-table-column>
            </el-table>

            <!-- Quote Totals -->
            <div class="quote-totals">
              <el-row>
                <el-col :span="12" :offset="12">
                  <div class="totals-section">
                    <div class="total-row">
                      <span>小计:</span>
                      <span>${{ quote.subtotal?.toLocaleString() }}</span>
                    </div>
                    <div v-if="quote.discount_amount && quote.discount_amount > 0" class="total-row">
                      <span>整单折扣 ({{ quote.discount_percentage }}%):</span>
                      <span>-${{ quote.discount_amount.toLocaleString() }}</span>
                    </div>
                    <div v-if="quote.tax_amount && quote.tax_amount > 0" class="total-row">
                      <span>税费:</span>
                      <span>${{ quote.tax_amount.toLocaleString() }}</span>
                    </div>
                    <div class="total-row final-total">
                      <span>总计:</span>
                      <span>${{ quote.total_price?.toLocaleString() }}</span>
                    </div>
                  </div>
                </el-col>
              </el-row>
            </div>
          </el-card>

          <!-- Notes and Terms -->
          <div v-if="quote.notes || quote.terms_conditions">
            <el-card v-if="quote.notes" class="notes-card">
              <template #header>
                <span class="card-title">备注</span>
              </template>
              <p class="notes-content">{{ quote.notes }}</p>
            </el-card>

            <el-card v-if="quote.terms_conditions" class="terms-card">
              <template #header>
                <span class="card-title">条款和条件</span>
              </template>
              <p class="terms-content">{{ quote.terms_conditions }}</p>
            </el-card>
          </div>
        </el-col>

        <!-- Actions Sidebar -->
        <el-col :span="8">
          <el-card class="actions-card">
            <template #header>
              <span class="card-title">操作</span>
            </template>
            
            <div class="action-buttons">
              <!-- Status Change Actions -->
              <el-button 
                v-if="quote.status === 'draft'" 
                type="warning" 
                @click="updateStatus('pending')"
                :loading="updatingStatus"
                block
              >
                提交审批
              </el-button>
              
              <el-button 
                v-if="quote.status === 'pending'" 
                type="success" 
                @click="updateStatus('approved')"
                :loading="updatingStatus"
                block
              >
                批准报价
              </el-button>
              
              <el-button 
                v-if="quote.status === 'pending'" 
                type="danger" 
                @click="updateStatus('rejected')"
                :loading="updatingStatus"
                block
              >
                拒绝报价
              </el-button>

              <!-- PDF Export -->
              <el-button 
                type="primary" 
                @click="generatePDF"
                :loading="generatingPDF"
                icon="Download"
                block
              >
                下载PDF
              </el-button>

              <!-- Email Quote (Future feature) -->
              <el-button 
                type="info" 
                disabled
                icon="Message"
                block
              >
                邮件报价
              </el-button>

              <!-- Duplicate Quote -->
              <el-button 
                type="default" 
                @click="duplicateQuote"
                icon="DocumentCopy"
                block
              >
                复制报价
              </el-button>
            </div>
          </el-card>

          <!-- Quote Statistics (if available) -->
          <el-card v-if="quoteStats" class="stats-card">
            <template #header>
              <span class="card-title">统计信息</span>
            </template>
            
            <div class="stats-content">
              <div class="stat-item">
                <span class="stat-label">Items Count:</span>
                <span class="stat-value">{{ quote.items?.length || 0 }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Days Valid:</span>
                <span class="stat-value">{{ getDaysUntilExpiry() }}</span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- Loading State -->
    <div v-else-if="loading" class="loading">
      <el-skeleton :rows="10" animated />
    </div>

    <!-- Error State -->
    <div v-else class="error">
      <el-result 
        icon="error" 
        title="Quote not found" 
        sub-title="The quote you're looking for doesn't exist or you don't have permission to view it."
      >
        <template #extra>
          <el-button @click="$router.push('/quotes')">Back to Quotes</el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { unifiedQuotesApi } from '@/api/quotes'
import { ElMessageBox } from 'element-plus'
import { showMessage } from '@/utils/message'
import { unifiedChinesePDFGenerator, createQuotePDFDataFromSettings } from '@/utils/unifiedChinesePDFGenerator'
import type { Quote } from '@/types/quote'

const route = useRoute()
const router = useRouter()

const quote = ref<Quote | null>(null)
const loading = ref(false)
const generatingPDF = ref(false)
const updatingStatus = ref(false)
const quoteStats = ref(true) // Enable stats display

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
  if (!dateString) return '暂无'
  return new Date(dateString).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const getStatusAction = (status: string) => {
  const actionMap: Record<string, string> = {
    pending: '提交审批',
    approved: '批准',
    rejected: '拒绝'
  }
  return actionMap[status] || status
}

const getDaysUntilExpiry = () => {
  if (!quote.value?.valid_until) return '暂无'
  
  const expiryDate = new Date(quote.value.valid_until)
  const today = new Date()
  const diffTime = expiryDate.getTime() - today.getTime()
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  
  if (diffDays < 0) return '已过期'
  if (diffDays === 0) return '今天'
  return `${diffDays}天`
}

const updateStatus = async (newStatus: string) => {
  if (!quote.value) return
  
  try {
    const confirmMessage = `您确定要${getStatusAction(newStatus)}这个报价吗？`
    await ElMessageBox.confirm(confirmMessage, '确认状态变更', {
      confirmButtonText: '确定',
      cancelButtonText: '取消', 
      type: 'warning'
    })
    
    updatingStatus.value = true
    // Create a proper update request with the status
    const updateRequest = { status: newStatus as any }
    await unifiedQuotesApi.updateQuote(quote.value.id, updateRequest)
    quote.value.status = newStatus as any
    showMessage.success(`报价${getStatusAction(newStatus)}成功`)
  } catch (error: any) {
    if (error !== 'cancel') {
      showMessage.error('更新报价状态失败')
    }
  } finally {
    updatingStatus.value = false
  }
}

const editQuote = () => {
  if (quote.value) {
    router.push(`/quotes/${quote.value.id}/edit`)
  }
}

const duplicateQuote = async () => {
  if (!quote.value) return
  
  try {
    await ElMessageBox.confirm(
      '这将创建一个具有相同项目和客户信息的新报价单。继续吗？',
      '复制报价',
      {
        confirmButtonText: '创建复制',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    
    // Navigate to create quote page with pre-filled data
    // This would require implementing duplicate functionality
    showMessage.info('复制功能将在下一个版本中实现')
  } catch {
    // User cancelled
  }
}

const generatePDF = async () => {
  if (!quote.value) return
  
  try {
    generatingPDF.value = true
    
    // Create PDF data from quote with system settings
    const pdfData = await createQuotePDFDataFromSettings(quote.value)
    
    // Generate and download PDF using true Chinese PDF generator
    await unifiedChinesePDFGenerator.downloadPDF(pdfData, `报价单-${quote.value.quote_number}`)
    
    showMessage.success('PDF生成成功')
  } catch (error) {
    console.error('PDF generation error:', error)
    showMessage.error('生成PDF失败')
  } finally {
    generatingPDF.value = false
  }
}

const loadQuote = async () => {
  const quoteId = parseInt(route.params.id as string)
  
  if (isNaN(quoteId)) {
    showMessage.error('无效的报价ID')
    router.push('/quotes')
    return
  }
  
  loading.value = true
  try {
    const response = await unifiedQuotesApi.getQuote(quoteId)
    quote.value = response.quote
  } catch (error: any) {
    console.error('Error loading quote:', error)
    showMessage.error('加载报价失败')
    quote.value = null
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadQuote()
})
</script>

<style scoped>
.quote-detail {
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
  flex-wrap: wrap;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-weight: 600;
  color: #303133;
}

.quote-info-card,
.customer-info-card,
.items-card,
.notes-card,
.terms-card {
  margin-bottom: 20px;
}

.total-amount {
  font-size: 18px;
  color: #67C23A;
}

.product-info {
  line-height: 1.4;
}

.product-code {
  color: #909399;
  font-size: 12px;
}

.product-description {
  color: #606266;
  font-size: 12px;
  margin-top: 4px;
}

.line-total {
  font-weight: 600;
  color: #67C23A;
}

.quote-totals {
  border-top: 1px solid #ebeef5;
  padding-top: 16px;
  margin-top: 16px;
}

.totals-section {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
}

.total-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.final-total {
  border-top: 1px solid #ddd;
  padding-top: 8px;
  margin-top: 8px;
  font-weight: 600;
  font-size: 16px;
  color: #303133;
}

.actions-card,
.stats-card {
  margin-bottom: 20px;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stats-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  color: #606266;
  font-size: 14px;
}

.stat-value {
  font-weight: 600;
  color: #303133;
}

.notes-content,
.terms-content {
  line-height: 1.6;
  color: #606266;
  margin: 0;
  white-space: pre-wrap;
}

.loading, .error {
  margin-top: 50px;
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
  
  .items-table .el-table__body-wrapper {
    overflow-x: auto;
  }
  
  .totals-section {
    font-size: 14px;
  }
  
  .action-buttons .el-button {
    font-size: 14px;
  }
}
</style>