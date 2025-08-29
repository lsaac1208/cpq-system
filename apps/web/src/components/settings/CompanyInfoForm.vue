<template>
  <div class="company-info-form">
    <h3 class="form-title">公司信息</h3>
    <p class="form-description">
      配置公司基本信息，这些信息将显示在报价单和其他文档中。
    </p>
    
    <form @submit.prevent="handleSubmit" class="form">
      <div class="form-grid">
        <!-- Company Name -->
        <div class="form-group">
          <label for="company-name" class="form-label required">
            公司名称
          </label>
          <input
            id="company-name"
            v-model="form.name"
            type="text"
            required
            class="form-input"
            placeholder="请输入公司名称"
          />
          <div v-if="errors.name" class="form-error">
            {{ errors.name }}
          </div>
        </div>

        <!-- Company Email -->
        <div class="form-group">
          <label for="company-email" class="form-label">
            公司邮箱
          </label>
          <input
            id="company-email"
            v-model="form.email"
            type="email"
            class="form-input"
            placeholder="请输入公司邮箱"
          />
          <div v-if="errors.email" class="form-error">
            {{ errors.email }}
          </div>
        </div>

        <!-- Company Phone -->
        <div class="form-group">
          <label for="company-phone" class="form-label">
            联系电话
          </label>
          <input
            id="company-phone"
            v-model="form.phone"
            type="tel"
            class="form-input"
            placeholder="请输入联系电话"
          />
          <div v-if="errors.phone" class="form-error">
            {{ errors.phone }}
          </div>
        </div>

        <!-- Company Website -->
        <div class="form-group">
          <label for="company-website" class="form-label">
            公司网站
          </label>
          <input
            id="company-website"
            v-model="form.website"
            type="url"
            class="form-input"
            placeholder="https://www.example.com"
          />
          <div v-if="errors.website" class="form-error">
            {{ errors.website }}
          </div>
        </div>

        <!-- Tax Number -->
        <div class="form-group">
          <label for="tax-number" class="form-label">
            税号
          </label>
          <input
            id="tax-number"
            v-model="form.tax_number"
            type="text"
            class="form-input"
            placeholder="请输入税号"
          />
          <div v-if="errors.tax_number" class="form-error">
            {{ errors.tax_number }}
          </div>
        </div>

        <!-- Logo URL -->
        <div class="form-group">
          <label for="logo-url" class="form-label">
            公司Logo URL
          </label>
          <input
            id="logo-url"
            v-model="form.logo_url"
            type="url"
            class="form-input"
            placeholder="https://www.example.com/logo.png"
          />
          <div v-if="errors.logo_url" class="form-error">
            {{ errors.logo_url }}
          </div>
        </div>
      </div>

      <!-- Company Address -->
      <div class="form-group full-width">
        <label for="company-address" class="form-label">
          公司地址
        </label>
        <textarea
          id="company-address"
          v-model="form.address"
          rows="3"
          class="form-textarea"
          placeholder="请输入完整的公司地址"
        ></textarea>
        <div v-if="errors.address" class="form-error">
          {{ errors.address }}
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
import type { CompanyInfo } from '@/types/settings'

// Props
interface Props {
  companyInfo?: CompanyInfo
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

// Emits
interface Emits {
  (e: 'update', companyInfo: CompanyInfo): void
}

const emit = defineEmits<Emits>()

// Form data
const form = reactive<CompanyInfo>({
  name: '',
  address: '',
  phone: '',
  email: '',
  website: '',
  logo_url: '',
  tax_number: ''
})

// Form errors
const errors = reactive<Partial<Record<keyof CompanyInfo, string>>>({})

// Form validation
const isFormValid = computed(() => {
  return form.name.trim().length > 0 && Object.keys(errors).length === 0
})

// Initialize form with props data
const initializeForm = () => {
  if (props.companyInfo) {
    Object.assign(form, {
      name: props.companyInfo.name || '',
      address: props.companyInfo.address || '',
      phone: props.companyInfo.phone || '',
      email: props.companyInfo.email || '',
      website: props.companyInfo.website || '',
      logo_url: props.companyInfo.logo_url || '',
      tax_number: props.companyInfo.tax_number || ''
    })
  }
}

// Validate form fields
const validateField = (field: keyof CompanyInfo, value: string) => {
  switch (field) {
    case 'name':
      if (!value.trim()) {
        errors[field] = '公司名称不能为空'
      } else if (value.length > 200) {
        errors[field] = '公司名称不能超过200个字符'
      } else {
        delete errors[field]
      }
      break

    case 'email':
      if (value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
        errors[field] = '请输入有效的邮箱地址'
      } else {
        delete errors[field]
      }
      break

    case 'website':
    case 'logo_url':
      if (value && !/^https?:\/\/.+\..+/.test(value)) {
        errors[field] = '请输入有效的URL地址'
      } else {
        delete errors[field]
      }
      break

    case 'phone':
      if (value && value.length > 50) {
        errors[field] = '电话号码不能超过50个字符'
      } else {
        delete errors[field]
      }
      break

    case 'tax_number':
      if (value && value.length > 100) {
        errors[field] = '税号不能超过100个字符'
      } else {
        delete errors[field]
      }
      break

    default:
      delete errors[field]
  }
}

// Watch form fields for validation
watch(() => form.name, (value) => validateField('name', value))
watch(() => form.email, (value) => validateField('email', value))
watch(() => form.website, (value) => validateField('website', value))
watch(() => form.logo_url, (value) => validateField('logo_url', value))
watch(() => form.phone, (value) => validateField('phone', value))
watch(() => form.tax_number, (value) => validateField('tax_number', value))

// Watch props changes
watch(
  () => props.companyInfo,
  () => {
    initializeForm()
  },
  { immediate: true, deep: true }
)

// Handle form submission
const handleSubmit = () => {
  // Validate all fields
  Object.keys(form).forEach(key => {
    validateField(key as keyof CompanyInfo, form[key as keyof CompanyInfo] as string)
  })

  if (isFormValid.value) {
    emit('update', { ...form })
  }
}

// Handle form reset
const handleReset = () => {
  initializeForm()
  Object.keys(errors).forEach(key => {
    delete errors[key as keyof CompanyInfo]
  })
}
</script>

<style scoped>
.company-info-form {
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
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group.full-width {
  grid-column: 1 / -1;
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
.form-textarea {
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 1rem;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-input::placeholder,
.form-textarea::placeholder {
  color: #9ca3af;
}

.form-textarea {
  resize: vertical;
  min-height: 4rem;
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