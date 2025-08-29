<template>
  <div class="create-quote">
    <div class="page-header">
      <h1>{{ isEditing ? '编辑报价' : '创建报价' }}</h1>
      <div class="header-actions">
        <el-button @click="$router.go(-1)">取消</el-button>
        <el-button type="primary" @click="saveQuote" :loading="saving">
          {{ isEditing ? '更新报价' : '保存报价' }}
        </el-button>
      </div>
    </div>

    <el-form 
      ref="quoteFormRef" 
      :model="quoteForm" 
      :rules="formRules"
      label-width="140px"
    >
      <!-- Customer Information -->
      <el-card class="form-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">客户信息</span>
          </div>
        </template>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="客户名称" prop="customer_name">
              <el-input 
                v-model="quoteForm.customer_name" 
                placeholder="请输入客户名称"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="客户邮箱" prop="customer_email">
              <el-input 
                v-model="quoteForm.customer_email" 
                placeholder="请输入客户邮箱"
                type="email"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="公司">
              <el-input 
                v-model="quoteForm.customer_company" 
                placeholder="请输入公司名称"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="电话">
              <el-input 
                v-model="quoteForm.customer_phone" 
                placeholder="请输入电话号码"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="地址">
          <el-input 
            v-model="quoteForm.customer_address" 
            type="textarea"
            :rows="2"
            placeholder="请输入客户地址"
          />
        </el-form-item>
      </el-card>

      <!-- Quote Items -->
      <el-card class="form-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">报价项目</span>
            <el-button 
              type="primary" 
              size="small"
              @click="showAddItemDialog = true"
              icon="Plus"
            >
              添加项目
            </el-button>
          </div>
        </template>

        <div v-if="quoteForm.items.length === 0" class="empty-items">
          <el-empty description="尚未添加项目">
            <el-button type="primary" @click="showAddItemDialog = true">
              添加第一个项目
            </el-button>
          </el-empty>
        </div>

        <el-table 
          v-else
          :data="quoteForm.items" 
          style="width: 100%"
          class="quote-items-table"
        >
          <el-table-column label="产品" min-width="200">
            <template #default="{ row }">
              <div class="product-info">
                <strong>{{ row.product?.name }}</strong>
                <div class="product-code">{{ row.product?.code }}</div>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column label="数量" width="120">
            <template #default="{ row, $index }">
              <el-input-number
                v-model="row.quantity"
                :min="1"
                :max="9999"
                size="small"
                @change="updateItemTotal($index)"
              />
            </template>
          </el-table-column>
          
          <el-table-column label="单价" width="140">
            <template #default="{ row, $index }">
              <el-input-number
                v-model="row.unit_price"
                :precision="2"
                :min="0"
                size="small"
                @change="updateItemTotal($index)"
              >
                <template #prefix>$</template>
              </el-input-number>
            </template>
          </el-table-column>
          
          <el-table-column label="折扣%" width="120">
            <template #default="{ row, $index }">
              <el-input-number
                v-model="row.discount_percentage"
                :precision="2"
                :min="0"
                :max="100"
                size="small"
                @change="updateItemTotal($index)"
              >
                <template #suffix>%</template>
              </el-input-number>
            </template>
          </el-table-column>
          
          <el-table-column label="小计" width="140">
            <template #default="{ row }">
              <span class="line-total">${{ row.line_total.toLocaleString() }}</span>
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="100">
            <template #default="{ $index }">
              <el-button
                type="danger"
                size="small"
                icon="Delete"
                @click="removeItem($index)"
                circle
              />
            </template>
          </el-table-column>
        </el-table>

        <!-- Quote Totals -->
        <div v-if="quoteForm.items.length > 0" class="quote-totals">
          <el-row :gutter="20">
            <el-col :span="12" :offset="12">
              <div class="totals-section">
                <div class="total-row">
                  <span>小计:</span>
                  <span>${{ quoteTotals.subtotal.toLocaleString() }}</span>
                </div>
                <div class="total-row" v-if="quoteTotals.discount_amount > 0">
                  <span>折扣:</span>
                  <span>-${{ quoteTotals.discount_amount.toLocaleString() }}</span>
                </div>
                <div class="total-row" v-if="quoteTotals.tax_amount > 0">
                  <span>税费:</span>
                  <span>${{ quoteTotals.tax_amount.toLocaleString() }}</span>
                </div>
                <div class="total-row final-total">
                  <span>总计:</span>
                  <span>${{ quoteTotals.total.toLocaleString() }}</span>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
      </el-card>

      <!-- Quote Settings -->
      <el-card class="form-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">报价设置</span>
          </div>
        </template>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="整单折扣%">
              <el-input-number
                v-model="quoteForm.discount_percentage"
                :precision="2"
                :min="0"
                :max="100"
                @change="calculateTotals"
              >
                <template #suffix>%</template>
              </el-input-number>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="税率%">
              <el-input-number
                v-model="quoteForm.tax_percentage"
                :precision="2"
                :min="0"
                :max="100"
                @change="calculateTotals"
              >
                <template #suffix>%</template>
              </el-input-number>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="有效期至">
              <el-date-picker
                v-model="validUntilDate"
                type="date"
                placeholder="选择日期"
                style="width: 100%"
                :disabled-date="disabledDate"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="备注">
          <el-input 
            v-model="quoteForm.notes" 
            type="textarea" 
            :rows="3"
            placeholder="添加备注或特殊说明..."
          />
        </el-form-item>
        
        <el-form-item label="条款和条件">
          <el-input 
            v-model="quoteForm.terms_conditions" 
            type="textarea" 
            :rows="3"
            placeholder="添加条款和条件..."
          />
        </el-form-item>
      </el-card>
    </el-form>

    <!-- Add Item Dialog -->
    <el-dialog
      v-model="showAddItemDialog"
      title="添加报价项目"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="itemFormRef"
        :model="newItemForm"
        :rules="itemFormRules"
        label-width="120px"
      >
        <el-form-item label="产品" prop="product_id">
          <el-select
            v-model="newItemForm.product_id"
            placeholder="选择产品"
            style="width: 100%"
            filterable
            @change="onProductSelect"
          >
            <el-option
              v-for="product in availableProducts"
              :key="product.id"
              :label="`${product.name} (${product.code})`"
              :value="product.id"
              :disabled="isProductAlreadyAdded(product.id)"
            >
              <div class="product-option">
                <span class="product-name">{{ product.name }}</span>
                <span class="product-price">${{ product.base_price?.toLocaleString() }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        
        <div v-if="selectedNewProduct" class="product-preview">
          <h4>产品详情</h4>
          <p><strong>描述:</strong> {{ selectedNewProduct.description }}</p>
          <p><strong>基础价格:</strong> ${{ selectedNewProduct.base_price?.toLocaleString() }}</p>
        </div>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="数量" prop="quantity">
              <el-input-number
                v-model="newItemForm.quantity"
                :min="1"
                :max="9999"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="单价" prop="unit_price">
              <el-input-number
                v-model="newItemForm.unit_price"
                :precision="2"
                :min="0"
                style="width: 100%"
              >
                <template #prefix>$</template>
              </el-input-number>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="项目折扣%">
          <el-input-number
            v-model="newItemForm.discount_percentage"
            :precision="2"
            :min="0"
            :max="100"
            style="width: 200px"
          >
            <template #suffix>%</template>
          </el-input-number>
        </el-form-item>
        
        <el-form-item label="备注">
          <el-input
            v-model="newItemForm.notes"
            type="textarea"
            :rows="2"
            placeholder="添加项目备注..."
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAddItemDialog = false">取消</el-button>
          <el-button type="primary" @click="addItem">添加项目</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, reactive, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { unifiedQuotesApi } from '@/api/quotes'
import { useProductsStore } from '@/stores/products'
import { ElMessageBox } from 'element-plus'
import { showMessage } from '@/utils/message'
import type { 
  CreateQuoteRequest, 
  CreateQuoteItemRequest, 
  Product, 
  Quote,
  QuoteItem 
} from '@/types'

const route = useRoute()
const router = useRouter()
const productsStore = useProductsStore()

const saving = ref(false)
const showAddItemDialog = ref(false)
const validUntilDate = ref<Date>(new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)) // 30 days from now
const quoteFormRef = ref()
const itemFormRef = ref()

// Check if we're editing an existing quote
const isEditing = computed(() => !!route.params.id)
const existingQuote = ref<Quote | null>(null)

// Available products for selection
const availableProducts = ref<Product[]>([])

// Form data
const quoteForm = reactive<CreateQuoteRequest>({
  customer_name: '',
  customer_email: '',
  customer_company: '',
  customer_phone: '',
  customer_address: '',
  items: [],
  discount_percentage: 0,
  tax_percentage: 0,
  notes: '',
  terms_conditions: ''
})

// New item form
const newItemForm = reactive<CreateQuoteItemRequest>({
  product_id: 0,
  quantity: 1,
  unit_price: 0,
  discount_percentage: 0,
  notes: ''
})

// Form validation rules
const formRules = {
  customer_name: [
    { required: true, message: '请输入客户名称', trigger: 'blur' }
  ],
  customer_email: [
    { required: true, message: '请输入客户邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ]
}

const itemFormRules = {
  product_id: [
    { required: true, message: '请选择产品', trigger: 'change' }
  ],
  quantity: [
    { required: true, message: '请输入数量', trigger: 'blur' }
  ],
  unit_price: [
    { required: true, message: '请输入单价', trigger: 'blur' }
  ]
}

// Computed properties
const selectedNewProduct = computed(() => {
  return availableProducts.value.find(p => p.id === newItemForm.product_id)
})

const quoteTotals = computed(() => {
  const subtotal = quoteForm.items.reduce((sum, item) => sum + item.line_total, 0)
  const discount_amount = subtotal * (quoteForm.discount_percentage || 0) / 100
  const subtotal_after_discount = subtotal - discount_amount
  const tax_amount = subtotal_after_discount * (quoteForm.tax_percentage || 0) / 100
  const total = subtotal_after_discount + tax_amount

  return {
    subtotal,
    discount_amount,
    tax_amount,
    total
  }
})

// Watch for route params to handle preselected products
watch(() => route.query.products, (productIds) => {
  if (productIds && typeof productIds === 'string') {
    const ids = productIds.split(',').map(id => parseInt(id, 10))
    preAddProducts(ids)
  }
}, { immediate: true })

// Watch for valid until date changes
watch(validUntilDate, (newDate) => {
  if (newDate) {
    quoteForm.valid_until = newDate.toISOString().split('T')[0]
  }
})

// Methods
const disabledDate = (date: Date) => {
  return date < new Date()
}

const preAddProducts = async (productIds: number[]) => {
  await loadProducts()
  
  for (const productId of productIds) {
    const product = availableProducts.value.find(p => p.id === productId)
    if (product && !isProductAlreadyAdded(productId)) {
      const item: CreateQuoteItemRequest & { product?: Product; line_total: number } = {
        product_id: productId,
        product: product,
        quantity: 1,
        unit_price: product.base_price || 0,
        discount_percentage: 0,
        notes: '',
        line_total: product.base_price || 0
      }
      quoteForm.items.push(item)
    }
  }
  
  calculateTotals()
}

const isProductAlreadyAdded = (productId: number) => {
  return quoteForm.items.some(item => item.product_id === productId)
}

const onProductSelect = () => {
  const product = selectedNewProduct.value
  if (product) {
    newItemForm.unit_price = product.base_price || 0
  }
}

const addItem = async () => {
  if (!itemFormRef.value) return
  
  try {
    await itemFormRef.value.validate()
    
    const product = selectedNewProduct.value
    if (!product) {
      showMessage.error('产品未找到')
      return
    }

    const lineTotal = calculateLineTotal(
      newItemForm.quantity,
      newItemForm.unit_price || 0,
      newItemForm.discount_percentage || 0
    )

    const item: CreateQuoteItemRequest & { product?: Product; line_total: number } = {
      ...newItemForm,
      product: product,
      line_total: lineTotal
    }

    quoteForm.items.push(item)
    
    // Reset form
    Object.assign(newItemForm, {
      product_id: 0,
      quantity: 1,
      unit_price: 0,
      discount_percentage: 0,
      notes: ''
    })
    
    showAddItemDialog.value = false
    calculateTotals()
    
    showMessage.success('项目添加成功')
  } catch (error) {
    // Validation failed
  }
}

const removeItem = async (index: number) => {
  try {
    await ElMessageBox.confirm(
      '您确定要删除这个项目吗？',
      '确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    quoteForm.items.splice(index, 1)
    calculateTotals()
    showMessage.success('项目已删除')
  } catch {
    // User cancelled
  }
}

const updateItemTotal = (index: number) => {
  const item = quoteForm.items[index]
  if (item) {
    item.line_total = calculateLineTotal(
      Number(item.quantity) || 1,
      Number(item.unit_price) || 0,
      Number(item.discount_percentage) || 0
    )
    calculateTotals()
  }
}

const calculateLineTotal = (quantity: number, unitPrice: number, discountPercentage: number = 0) => {
  const subtotal = Number(quantity) * Number(unitPrice)
  const discount = subtotal * Number(discountPercentage) / 100
  return Number((subtotal - discount).toFixed(2))
}

const calculateTotals = () => {
  // Totals are computed automatically via the computed property
  // This method can be used to trigger reactivity if needed
}

const loadProducts = async () => {
  try {
    await productsStore.loadProducts({ is_active: true, per_page: 100 })
    availableProducts.value = productsStore.products
  } catch (error) {
    showMessage.error('加载产品失败')
  }
}

const loadExistingQuote = async (quoteId: string) => {
  try {
    // Load existing quote for editing
    // This would be implemented when the backend supports it
    showMessage.info('报价编辑功能将在下一个版本中实现')
  } catch (error) {
    showMessage.error('加载报价失败')
    router.push('/quotes')
  }
}

const saveQuote = async () => {
  if (!quoteFormRef.value) return
  
  try {
    await quoteFormRef.value.validate()
    
    if (quoteForm.items.length === 0) {
      showMessage.error('请至少添加一个项目到报价单')
      return
    }
    
    saving.value = true
    
    // 确保数据类型正确
    const submitData = {
      customer_name: quoteForm.customer_name,
      customer_email: quoteForm.customer_email,
      customer_company: quoteForm.customer_company || undefined,
      customer_phone: quoteForm.customer_phone || undefined,
      customer_address: quoteForm.customer_address || undefined,
      // 确保数值字段为数字类型
      discount_percentage: Number(quoteForm.discount_percentage) || 0,
      tax_percentage: Number(quoteForm.tax_percentage) || 0,
      valid_until: validUntilDate.value ? validUntilDate.value.toISOString().split('T')[0] : undefined,
      notes: quoteForm.notes || undefined,
      terms_conditions: quoteForm.terms_conditions || undefined,
      items: quoteForm.items.map(item => ({
        product_id: Number(item.product_id),
        quantity: Number(item.quantity) || 1,
        unit_price: Number(item.unit_price) || 0,
        discount_percentage: Number(item.discount_percentage) || 0,
        notes: item.notes || undefined
        // line_total is calculated by backend, don't send it
      }))
    }
    
    console.log('提交的数据:', submitData) // 调试用
    console.log('数据类型检查:', {
      discount_percentage: typeof submitData.discount_percentage,
      tax_percentage: typeof submitData.tax_percentage,
      items: submitData.items.map(item => ({
        product_id: typeof item.product_id,
        quantity: typeof item.quantity,
        unit_price: typeof item.unit_price,
        discount_percentage: typeof item.discount_percentage
      }))
    })
    
    const response = await unifiedQuotesApi.createQuote(submitData)
    showMessage.success('报价创建成功')
    router.push('/quotes')
  } catch (error: any) {
    console.error('创建报价错误:', error)
    console.error('错误响应:', error.response)
    
    if (error.response?.data) {
      const errorData = error.response.data
      console.error('详细错误信息:', errorData)
      
      if (errorData.details) {
        // 如果有验证详情，显示具体错误
        const detailsMessage = Object.entries(errorData.details)
          .map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(', ') : messages}`)
          .join('\n')
        showMessage.error(`数据验证错误:\n${detailsMessage}`)
      } else if (errorData.error) {
        showMessage.error(errorData.error)
      } else {
        showMessage.error('创建报价失败')
      }
    } else {
      showMessage.error(error.message || '创建报价失败')
    }
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await loadProducts()
  
  if (isEditing.value) {
    await loadExistingQuote(route.params.id as string)
  }
})
</script>

<style scoped>
.create-quote {
  max-width: 1000px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.form-card {
  margin-bottom: 20px;
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

.empty-items {
  text-align: center;
  padding: 40px 20px;
}

.quote-items-table {
  margin-bottom: 20px;
}

.product-info {
  line-height: 1.4;
}

.product-code {
  color: #909399;
  font-size: 12px;
}

.line-total {
  font-weight: 600;
  color: #67C23A;
}

.quote-totals {
  border-top: 1px solid #ebeef5;
  padding-top: 20px;
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

.product-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.product-name {
  font-weight: 500;
}

.product-price {
  color: #67C23A;
  font-weight: 600;
}

.product-preview {
  background: #f8f9fa;
  padding: 12px;
  border-radius: 6px;
  margin: 12px 0;
}

.product-preview h4 {
  margin: 0 0 8px 0;
  color: #303133;
}

.product-preview p {
  margin: 4px 0;
  font-size: 14px;
  color: #606266;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .header-actions {
    justify-content: center;
  }
  
  .quote-items-table .el-table__body-wrapper {
    overflow-x: auto;
  }
  
  .totals-section {
    font-size: 14px;
  }
}
</style>