<template>
  <div class="business-rules-form">
    <h3 class="form-title">业务规则</h3>
    <p class="form-description">
      配置系统的业务逻辑和规则，影响报价流程和用户权限。
    </p>
    
    <form @submit.prevent="handleSubmit" class="form">
      <div class="rules-grid">
        <!-- Auto Quote Numbering -->
        <div class="rule-group">
          <div class="rule-header">
            <div class="checkbox-wrapper">
              <input
                id="auto-quote-numbering"
                v-model="form.auto_quote_numbering"
                type="checkbox"
                class="form-checkbox"
              />
              <label for="auto-quote-numbering" class="rule-title">
                自动生成报价单号
              </label>
            </div>
          </div>
          <p class="rule-description">
            启用后，系统将自动为新的报价单分配唯一编号。
          </p>
        </div>

        <!-- Require Customer Approval -->
        <div class="rule-group">
          <div class="rule-header">
            <div class="checkbox-wrapper">
              <input
                id="require-customer-approval"
                v-model="form.require_customer_approval"
                type="checkbox"
                class="form-checkbox"
              />
              <label for="require-customer-approval" class="rule-title">
                需要客户确认
              </label>
            </div>
          </div>
          <p class="rule-description">
            启用后，报价单需要客户确认后才能生效。
          </p>
        </div>

        <!-- Max Discount Percentage -->
        <div class="rule-group">
          <div class="rule-header">
            <label for="max-discount" class="rule-title">
              最大折扣百分比
            </label>
          </div>
          <div class="discount-input-wrapper">
            <input
              id="max-discount"
              v-model.number="form.max_discount_percentage"
              type="number"
              min="0"
              max="100"
              step="0.01"
              required
              class="form-input discount-input"
              placeholder="20.00"
            />
            <span class="discount-unit">%</span>
          </div>
          <p class="rule-description">
            设置用户可以应用的最大折扣百分比。
          </p>
          <div v-if="errors.max_discount_percentage" class="form-error">
            {{ errors.max_discount_percentage }}
          </div>
        </div>
      </div>

      <!-- Additional Rules Section -->
      <div class="additional-rules">
        <h4 class="section-title">高级设置</h4>
        <div class="info-box">
          <p>更多业务规则和权限控制功能正在开发中...</p>
        </div>
      </div>

      <!-- Form Actions -->
      <div class="form-actions">
        <button
          type="button"
          @click="handleReset"
          :disabled="loading"
          class="reset-button"
        >
          重置
        </button>
        
        <button
          type="submit"
          :disabled="loading || !isFormValid"
          class="submit-button"
        >
          <span v-if="loading" class="loading-spinner"></span>
          {{ loading ? '保存中...' : '保存更改' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { reactive, computed, watch } from 'vue'
import type { BusinessRules } from '@/types/settings'

// Props
interface Props {
  businessRules?: BusinessRules
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

// Emits
interface Emits {
  (e: 'update', businessRules: BusinessRules): void
}

const emit = defineEmits<Emits>()

// Form data
const form = reactive<BusinessRules>({
  auto_quote_numbering: true,
  require_customer_approval: false,
  max_discount_percentage: 20
})

// Form errors
const errors = reactive<Partial<Record<keyof BusinessRules, string>>>({})

// Form validation
const isFormValid = computed(() => {
  return form.max_discount_percentage >= 0 && 
         form.max_discount_percentage <= 100 && 
         Object.keys(errors).length === 0
})

// Initialize form with props data
const initializeForm = () => {
  if (props.businessRules) {
    Object.assign(form, {
      auto_quote_numbering: props.businessRules.auto_quote_numbering ?? true,
      require_customer_approval: props.businessRules.require_customer_approval ?? false,
      max_discount_percentage: props.businessRules.max_discount_percentage ?? 20
    })
  }
}

// Validate form fields
const validateField = (field: keyof BusinessRules, value: any) => {
  switch (field) {
    case 'max_discount_percentage':
      if (value < 0 || value > 100) {
        errors[field] = '折扣百分比必须在0-100之间'
      } else {
        delete errors[field]
      }
      break

    default:
      delete errors[field]
  }
}

// Watch form fields for validation
watch(() => form.max_discount_percentage, (value) => validateField('max_discount_percentage', value))

// Watch props changes
watch(
  () => props.businessRules,
  () => {
    initializeForm()
  },
  { immediate: true, deep: true }
)

// Handle form submission
const handleSubmit = () => {
  // Validate all fields
  validateField('max_discount_percentage', form.max_discount_percentage)

  if (isFormValid.value) {
    emit('update', { ...form })
  }
}

// Handle form reset
const handleReset = () => {
  initializeForm()
  Object.keys(errors).forEach(key => {
    delete errors[key as keyof BusinessRules]
  })
}
</script>

<style scoped>
.business-rules-form {
  max-width: 800px;
}

.form-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 0.5rem 0;
}

.form-description {
  color: #6b7280;
  margin: 0 0 2rem 0;
  line-height: 1.5;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.rules-grid {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.rule-group {
  padding: 1.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  background-color: #fafafa;
}

.rule-header {
  margin-bottom: 0.5rem;
}

.checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.form-checkbox {
  width: 1.25rem;
  height: 1.25rem;
  accent-color: #3b82f6;
}

.rule-title {
  font-size: 1rem;
  font-weight: 500;
  color: #1f2937;
  cursor: pointer;
}

.rule-description {
  color: #6b7280;
  font-size: 0.875rem;
  margin: 0;
  line-height: 1.4;
}

.discount-input-wrapper {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0.75rem 0;
}

.discount-input {
  width: 120px;
}

.discount-unit {
  font-weight: 500;
  color: #374151;
}

.form-input {
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 1rem;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-error {
  color: #dc2626;
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

.additional-rules {
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.section-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 1rem 0;
}

.info-box {
  padding: 1rem;
  background-color: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 0.375rem;
}

.info-box p {
  margin: 0;
  color: #0369a1;
  font-size: 0.875rem;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.reset-button,
.submit-button {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.reset-button {
  background-color: #f3f4f6;
  color: #374151;
}

.reset-button:hover:not(:disabled) {
  background-color: #e5e7eb;
}

.submit-button {
  background-color: #3b82f6;
  color: white;
}

.submit-button:hover:not(:disabled) {
  background-color: #2563eb;
}

.reset-button:disabled,
.submit-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading-spinner {
  width: 1rem;
  height: 1rem;
  border: 2px solid transparent;
  border-top: 2px solid currentColor;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .form-actions {
    flex-direction: column;
  }
}
</style>