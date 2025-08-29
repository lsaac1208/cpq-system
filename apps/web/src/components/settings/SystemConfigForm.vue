<template>
  <div class="system-config-form">
    <h3 class="form-title">系统配置</h3>
    <p class="form-description">
      配置系统的基本参数，包括默认货币、税率等。
    </p>
    
    <form @submit.prevent="handleSubmit" class="form">
      <div class="form-grid">
        <!-- Default Currency -->
        <div class="form-group">
          <label for="default-currency" class="form-label required">
            默认货币
          </label>
          <select
            id="default-currency"
            v-model="form.default_currency"
            required
            class="form-select"
          >
            <option v-for="currency in currencyOptions" :key="currency.code" :value="currency.code">
              {{ currency.code }} - {{ currency.name }} ({{ currency.symbol }})
            </option>
          </select>
          <div v-if="errors.default_currency" class="form-error">
            {{ errors.default_currency }}
          </div>
        </div>

        <!-- Default Tax Rate -->
        <div class="form-group">
          <label for="default-tax-rate" class="form-label">
            默认税率 (%)
          </label>
          <input
            id="default-tax-rate"
            v-model.number="form.default_tax_rate"
            type="number"
            min="0"
            max="100"
            step="0.01"
            class="form-input"
            placeholder="0.00"
          />
          <div v-if="errors.default_tax_rate" class="form-error">
            {{ errors.default_tax_rate }}
          </div>
        </div>

        <!-- Quote Validity Days -->
        <div class="form-group">
          <label for="quote-validity-days" class="form-label required">
            报价单有效期 (天)
          </label>
          <input
            id="quote-validity-days"
            v-model.number="form.quote_validity_days"
            type="number"
            min="1"
            max="365"
            required
            class="form-input"
            placeholder="30"
          />
          <div v-if="errors.quote_validity_days" class="form-error">
            {{ errors.quote_validity_days }}
          </div>
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
import { ref, reactive, computed, watch } from 'vue'
import type { SystemConfig } from '@/types/settings'
import { CURRENCY_OPTIONS } from '@/types/settings'

// Props
interface Props {
  systemConfig?: SystemConfig
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

// Emits
interface Emits {
  (e: 'update', systemConfig: SystemConfig): void
}

const emit = defineEmits<Emits>()

// Currency options
const currencyOptions = CURRENCY_OPTIONS

// Form data
const form = reactive<SystemConfig>({
  default_currency: 'USD',
  default_tax_rate: 0,
  quote_validity_days: 30
})

// Form errors
const errors = reactive<Partial<Record<keyof SystemConfig, string>>>({})

// Form validation
const isFormValid = computed(() => {
  return form.default_currency && 
         form.quote_validity_days > 0 && 
         Object.keys(errors).length === 0
})

// Initialize form with props data
const initializeForm = () => {
  if (props.systemConfig) {
    Object.assign(form, {
      default_currency: props.systemConfig.default_currency || 'USD',
      default_tax_rate: props.systemConfig.default_tax_rate || 0,
      quote_validity_days: props.systemConfig.quote_validity_days || 30
    })
  }
}

// Validate form fields
const validateField = (field: keyof SystemConfig, value: any) => {
  switch (field) {
    case 'default_currency':
      if (!value) {
        errors[field] = '请选择默认货币'
      } else {
        delete errors[field]
      }
      break

    case 'default_tax_rate':
      if (value < 0 || value > 100) {
        errors[field] = '税率必须在0-100之间'
      } else {
        delete errors[field]
      }
      break

    case 'quote_validity_days':
      if (!value || value < 1 || value > 365) {
        errors[field] = '有效期必须在1-365天之间'
      } else {
        delete errors[field]
      }
      break

    default:
      delete errors[field]
  }
}

// Watch form fields for validation
watch(() => form.default_currency, (value) => validateField('default_currency', value))
watch(() => form.default_tax_rate, (value) => validateField('default_tax_rate', value))
watch(() => form.quote_validity_days, (value) => validateField('quote_validity_days', value))

// Watch props changes
watch(
  () => props.systemConfig,
  () => {
    initializeForm()
  },
  { immediate: true, deep: true }
)

// Handle form submission
const handleSubmit = () => {
  // Validate all fields
  Object.keys(form).forEach(key => {
    validateField(key as keyof SystemConfig, form[key as keyof SystemConfig])
  })

  if (isFormValid.value) {
    emit('update', { ...form })
  }
}

// Handle form reset
const handleReset = () => {
  initializeForm()
  Object.keys(errors).forEach(key => {
    delete errors[key as keyof SystemConfig]
  })
}
</script>

<style scoped>
.system-config-form {
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
  gap: 1.5rem;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-label {
  font-weight: 500;
  color: #374151;
  font-size: 0.875rem;
}

.form-label.required::after {
  content: ' *';
  color: #dc2626;
}

.form-input,
.form-select {
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 1rem;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-error {
  color: #dc2626;
  font-size: 0.875rem;
  margin-top: 0.25rem;
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
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .form-actions {
    flex-direction: column;
  }
}
</style>