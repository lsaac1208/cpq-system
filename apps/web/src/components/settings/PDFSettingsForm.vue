<template>
  <div class="pdf-settings-form">
    <h3 class="form-title">PDF设置</h3>
    <p class="form-description">
      配置PDF文档的样式和显示选项。
    </p>
    
    <form @submit.prevent="handleSubmit" class="form">
      <div class="form-grid">
        <!-- Header Color -->
        <div class="form-group">
          <label for="header-color" class="form-label required">
            标题颜色
          </label>
          <div class="color-input-wrapper">
            <input
              id="header-color"
              v-model="form.header_color"
              type="color"
              required
              class="form-color-input"
            />
            <input
              v-model="form.header_color"
              type="text"
              class="form-input color-text-input"
              placeholder="#2563eb"
            />
          </div>
          <div v-if="errors.header_color" class="form-error">
            {{ errors.header_color }}
          </div>
        </div>

        <!-- Show Logo -->
        <div class="form-group">
          <label class="form-label">
            显示Logo
          </label>
          <div class="checkbox-wrapper">
            <input
              id="show-logo"
              v-model="form.show_logo"
              type="checkbox"
              class="form-checkbox"
            />
            <label for="show-logo" class="checkbox-label">
              在PDF中显示公司Logo
            </label>
          </div>
        </div>
      </div>

      <!-- Footer Text -->
      <div class="form-group full-width">
        <label for="footer-text" class="form-label">
          页脚文本
        </label>
        <textarea
          id="footer-text"
          v-model="form.footer_text"
          rows="3"
          class="form-textarea"
          placeholder="请输入页脚文本（可选）"
        ></textarea>
        <div v-if="errors.footer_text" class="form-error">
          {{ errors.footer_text }}
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
import type { PDFSettings } from '@/types/settings'

// Props
interface Props {
  pdfSettings?: PDFSettings
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

// Emits
interface Emits {
  (e: 'update', pdfSettings: PDFSettings): void
}

const emit = defineEmits<Emits>()

// Form data
const form = reactive<PDFSettings>({
  header_color: '#2563eb',
  footer_text: '',
  show_logo: true
})

// Form errors
const errors = reactive<Partial<Record<keyof PDFSettings, string>>>({})

// Form validation
const isFormValid = computed(() => {
  return form.header_color && Object.keys(errors).length === 0
})

// Initialize form with props data
const initializeForm = () => {
  if (props.pdfSettings) {
    Object.assign(form, {
      header_color: props.pdfSettings.header_color || '#2563eb',
      footer_text: props.pdfSettings.footer_text || '',
      show_logo: props.pdfSettings.show_logo ?? true
    })
  }
}

// Validate form fields
const validateField = (field: keyof PDFSettings, value: any) => {
  switch (field) {
    case 'header_color':
      if (!value) {
        errors[field] = '请选择标题颜色'
      } else if (!/^#[0-9A-Fa-f]{6}$/.test(value)) {
        errors[field] = '请输入有效的颜色代码'
      } else {
        delete errors[field]
      }
      break

    default:
      delete errors[field]
  }
}

// Watch form fields for validation
watch(() => form.header_color, (value) => validateField('header_color', value))

// Watch props changes
watch(
  () => props.pdfSettings,
  () => {
    initializeForm()
  },
  { immediate: true, deep: true }
)

// Handle form submission
const handleSubmit = () => {
  // Validate all fields
  validateField('header_color', form.header_color)

  if (isFormValid.value) {
    emit('update', { ...form })
  }
}

// Handle form reset
const handleReset = () => {
  initializeForm()
  Object.keys(errors).forEach(key => {
    delete errors[key as keyof PDFSettings]
  })
}
</script>

<style scoped>
.pdf-settings-form {
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

.color-input-wrapper {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.form-color-input {
  width: 3rem;
  height: 3rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  cursor: pointer;
}

.color-text-input {
  flex: 1;
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

.checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.form-checkbox {
  width: 1.25rem;
  height: 1.25rem;
  accent-color: #3b82f6;
}

.checkbox-label {
  font-size: 0.875rem;
  color: #374151;
  cursor: pointer;
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
</style>