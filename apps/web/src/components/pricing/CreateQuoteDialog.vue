<template>
  <el-dialog
    v-model="dialogVisible"
    title="基于推荐创建报价"
    width="800px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div v-if="productRecommendation" class="create-quote-form">
      <!-- 产品信息展示 -->
      <div class="product-section">
        <el-card class="product-info-card">
          <template #header>
            <span>推荐产品信息</span>
          </template>
          
          <div class="product-details">
            <div class="product-basic">
              <h3>{{ productRecommendation.product.name }}</h3>
              <p class="product-code">型号: {{ productRecommendation.product.code }}</p>
              <p class="product-category">类别: {{ productRecommendation.product.category }}</p>
            </div>
            
            <div class="product-pricing">
              <div class="price-item">
                <span class="price-label">基础价格:</span>
                <span class="price-value">¥{{ formatPrice(productRecommendation.recommended_price.base_price) }}</span>
              </div>
              <div class="price-item">
                <span class="price-label">推荐价格:</span>
                <span class="price-value recommended">¥{{ formatPrice(productRecommendation.recommended_price.recommended_price) }}</span>
              </div>
              <div class="price-item">
                <span class="price-label">调整幅度:</span>
                <span 
                  class="price-change"
                  :class="productRecommendation.recommended_price.price_change_percentage >= 0 ? 'positive' : 'negative'"
                >
                  {{ productRecommendation.recommended_price.price_change_percentage > 0 ? '+' : '' }}{{ productRecommendation.recommended_price.price_change_percentage }}%
                </span>
              </div>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 报价表单 -->
      <div class="quote-form-section">
        <el-form 
          ref="quoteFormRef"
          :model="quoteForm" 
          :rules="formRules"
          label-width="120px"
        >
          <!-- 客户信息 -->
          <el-divider content-position="left">客户信息</el-divider>
          
          <el-form-item label="客户姓名" prop="customer_name">
            <el-input v-model="quoteForm.customer_name" placeholder="请输入客户姓名" />
          </el-form-item>
          
          <el-form-item label="客户邮箱" prop="customer_email">
            <el-input v-model="quoteForm.customer_email" placeholder="请输入客户邮箱" />
          </el-form-item>
          
          <el-form-item label="客户公司" prop="customer_company">
            <el-input v-model="quoteForm.customer_company" placeholder="请输入客户公司（可选）" />
          </el-form-item>

          <!-- 产品配置 -->
          <el-divider content-position="left">产品配置</el-divider>
          
          <el-form-item label="数量" prop="quantity">
            <el-input-number 
              v-model="quoteForm.quantity" 
              :min="1" 
              :max="9999"
              @change="updateTotalPrice"
            />
          </el-form-item>
          
          <el-form-item label="单价" prop="unit_price">
            <el-input-number 
              v-model="quoteForm.unit_price" 
              :precision="2"
              :min="0"
              @change="updateTotalPrice"
            />
            <span class="price-tip">建议价格: ¥{{ formatPrice(productRecommendation.recommended_price.recommended_price) }}</span>
          </el-form-item>
          
          <el-form-item label="折扣" prop="discount_percentage">
            <el-input-number 
              v-model="quoteForm.discount_percentage" 
              :precision="2"
              :min="0" 
              :max="50"
              @change="updateTotalPrice"
            />
            <span class="discount-tip">%</span>
          </el-form-item>

          <!-- 配置建议 -->
          <el-form-item 
            v-if="Object.keys(productRecommendation.config_recommendations).length > 0"
            label="配置建议"
          >
            <div class="config-recommendations">
              <el-alert 
                title="AI推荐配置"
                type="info"
                :closable="false"
                show-icon
              >
                <ul class="config-list">
                  <li v-for="(value, key) in productRecommendation.config_recommendations" :key="key">
                    <strong>{{ key }}:</strong> {{ value }}
                  </li>
                </ul>
              </el-alert>
            </div>
          </el-form-item>

          <!-- 总价显示 -->
          <el-form-item label="总价">
            <div class="total-price-display">
              <div class="price-calculation">
                <div class="calc-line">
                  <span>小计: ¥{{ formatPrice(subtotal) }}</span>
                </div>
                <div v-if="quoteForm.discount_percentage > 0" class="calc-line discount">
                  <span>折扣 ({{ quoteForm.discount_percentage }}%): -¥{{ formatPrice(discountAmount) }}</span>
                </div>
                <div class="calc-line total">
                  <span>总计: ¥{{ formatPrice(totalPrice) }}</span>
                </div>
              </div>
            </div>
          </el-form-item>

          <!-- 备注信息 -->
          <el-divider content-position="left">备注信息</el-divider>
          
          <el-form-item label="报价备注">
            <el-input 
              v-model="quoteForm.notes"
              type="textarea"
              :rows="3"
              placeholder="请输入报价相关备注信息"
            />
          </el-form-item>
          
          <el-form-item label="条款条件">
            <el-input 
              v-model="quoteForm.terms_conditions"
              type="textarea"
              :rows="3"
              placeholder="请输入条款和条件"
            />
          </el-form-item>
        </el-form>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button 
          type="primary" 
          @click="handleSubmit"
          :loading="submitting"
        >
          创建报价
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, defineProps, defineEmits } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { pricingDecisionApi, type ProductRecommendation, type CreateQuoteRequest } from '@/api/pricing-decision'

// 定义属性和事件
const props = defineProps<{
  visible: boolean
  productRecommendation: ProductRecommendation | null
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'quote-created': [quote: any]
}>()

// 响应式数据
const quoteFormRef = ref<FormInstance>()
const submitting = ref(false)

// 对话框可见性
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

// 报价表单
const quoteForm = reactive<CreateQuoteRequest>({
  product_id: 0,
  customer_name: '',
  customer_email: '',
  customer_company: '',
  recommended_price: 0,
  quantity: 1,
  discount_percentage: 0,
  notes: '',
  terms_conditions: ''
})

// 表单验证规则
const formRules: FormRules = {
  customer_name: [
    { required: true, message: '请输入客户姓名', trigger: 'blur' }
  ],
  customer_email: [
    { required: true, message: '请输入客户邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  quantity: [
    { required: true, message: '请输入数量', trigger: 'blur' },
    { type: 'number', min: 1, message: '数量必须大于0', trigger: 'blur' }
  ],
  unit_price: [
    { required: true, message: '请输入单价', trigger: 'blur' },
    { type: 'number', min: 0, message: '单价不能为负数', trigger: 'blur' }
  ]
}

// 计算属性
const subtotal = computed(() => {
  return quoteForm.quantity * quoteForm.unit_price
})

const discountAmount = computed(() => {
  return subtotal.value * (quoteForm.discount_percentage / 100)
})

const totalPrice = computed(() => {
  return subtotal.value - discountAmount.value
})

// 监听产品推荐变化，初始化表单
watch(() => props.productRecommendation, (newRec) => {
  if (newRec) {
    quoteForm.product_id = newRec.product.id
    quoteForm.recommended_price = newRec.recommended_price.recommended_price
    quoteForm.unit_price = newRec.recommended_price.recommended_price
    
    // 重置其他字段
    quoteForm.customer_name = ''
    quoteForm.customer_email = ''
    quoteForm.customer_company = ''
    quoteForm.quantity = 1
    quoteForm.discount_percentage = 0
    quoteForm.notes = ''
    quoteForm.terms_conditions = ''
  }
}, { immediate: true })

// 更新总价
const updateTotalPrice = () => {
  // 总价会通过计算属性自动更新
}

// 处理提交
const handleSubmit = async () => {
  if (!quoteFormRef.value) return
  
  try {
    const valid = await quoteFormRef.value.validate()
    if (!valid) return
    
    submitting.value = true
    
    const response = await pricingDecisionApi.createQuoteFromRecommendation(quoteForm)
    
    if (response.success) {
      ElMessage.success('报价创建成功')
      emit('quote-created', response.data.quote)
      handleClose()
    } else {
      ElMessage.error(response.error || '创建报价失败')
    }
  } catch (error) {
    console.error('Failed to create quote:', error)
    ElMessage.error('创建报价失败')
  } finally {
    submitting.value = false
  }
}

// 处理关闭
const handleClose = () => {
  dialogVisible.value = false
  // 清空表单验证
  if (quoteFormRef.value) {
    quoteFormRef.value.clearValidate()
  }
}

// 格式化价格
const formatPrice = (price: number): string => {
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(price)
}
</script>

<style scoped>
.create-quote-form {
  max-height: 70vh;
  overflow-y: auto;
}

.product-section {
  margin-bottom: 24px;
}

.product-info-card {
  background: #f8f9fa;
  border: 1px solid #e1f5fe;
}

.product-details {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
}

.product-basic {
  flex: 1;
}

.product-basic h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: #303133;
}

.product-code,
.product-category {
  margin: 4px 0;
  color: #606266;
  font-size: 14px;
}

.product-pricing {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 200px;
}

.price-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: white;
  border-radius: 4px;
}

.price-label {
  color: #909399;
  font-size: 13px;
}

.price-value {
  font-weight: 600;
  color: #303133;
}

.price-value.recommended {
  color: #409eff;
  font-size: 16px;
}

.price-change {
  font-weight: 600;
  font-size: 14px;
}

.price-change.positive {
  color: #67c23a;
}

.price-change.negative {
  color: #f56c6c;
}

.quote-form-section {
  margin-top: 16px;
}

.price-tip,
.discount-tip {
  margin-left: 8px;
  color: #909399;
  font-size: 12px;
}

.config-recommendations {
  width: 100%;
}

.config-list {
  margin: 8px 0 0 0;
  padding-left: 20px;
}

.config-list li {
  margin-bottom: 4px;
  color: #606266;
  font-size: 13px;
}

.total-price-display {
  width: 100%;
}

.price-calculation {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
}

.calc-line {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.calc-line:last-child {
  margin-bottom: 0;
}

.calc-line.discount {
  color: #67c23a;
}

.calc-line.total {
  font-weight: 600;
  font-size: 16px;
  color: #303133;
  padding-top: 8px;
  border-top: 1px solid #e4e7ed;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 768px) {
  .product-details {
    flex-direction: column;
  }

  .product-pricing {
    min-width: auto;
    width: 100%;
  }

  .price-calculation {
    padding: 12px;
  }
}
</style>