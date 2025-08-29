<template>
  <div class="email-settings-form">
    <h3 class="form-title">邮件设置</h3>
    <p class="form-description">
      配置SMTP邮件服务器，用于发送报价单和系统通知。
    </p>
    
    <form @submit.prevent="handleSubmit" class="form">
      <!-- Enable SMTP -->
      <div class="form-group full-width">
        <div class="checkbox-wrapper">
          <input
            id="smtp-enabled"
            v-model="form.smtp_enabled"
            type="checkbox"
            class="form-checkbox"
          />
          <label for="smtp-enabled" class="checkbox-label">
            启用邮件功能
          </label>
        </div>
      </div>

      <div v-if="form.smtp_enabled" class="smtp-config">
        <div class="form-grid">
          <!-- SMTP Host -->
          <div class="form-group">
            <label for="smtp-host" class="form-label required">
              SMTP服务器
            </label>
            <input
              id="smtp-host"
              v-model="form.smtp_host"
              type="text"
              required
              class="form-input"
              placeholder="smtp.gmail.com"
            />
            <div v-if="errors.smtp_host" class="form-error">
              {{ errors.smtp_host }}
            </div>
          </div>

          <!-- SMTP Port -->
          <div class="form-group">
            <label for="smtp-port" class="form-label required">
              端口
            </label>
            <input
              id="smtp-port"
              v-model.number="form.smtp_port"
              type="number"
              min="1"
              max="65535"
              required
              class="form-input"
              placeholder="587"
            />
            <div v-if="errors.smtp_port" class="form-error">
              {{ errors.smtp_port }}
            </div>
          </div>

          <!-- SMTP Username -->
          <div class="form-group">
            <label for="smtp-username" class="form-label">
              用户名
            </label>
            <input
              id="smtp-username"
              v-model="form.smtp_username"
              type="text"
              class="form-input"
              placeholder="your-email@gmail.com"
            />
            <div v-if="errors.smtp_username" class="form-error">
              {{ errors.smtp_username }}
            </div>
          </div>

          <!-- SMTP Password -->
          <div class="form-group">
            <label for="smtp-password" class="form-label">
              密码
            </label>
            <input
              id="smtp-password"
              v-model="form.smtp_password"
              type="password"
              class="form-input"
              placeholder="应用专用密码"
            />
            <div v-if="errors.smtp_password" class="form-error">
              {{ errors.smtp_password }}
            </div>
          </div>
        </div>

        <!-- Use TLS -->
        <div class="form-group">
          <div class="checkbox-wrapper">
            <input
              id="smtp-use-tls"
              v-model="form.smtp_use_tls"
              type="checkbox"
              class="form-checkbox"
            />
            <label for="smtp-use-tls" class="checkbox-label">
              使用TLS加密连接
            </label>
          </div>
        </div>
      </div>

      <!-- Form Actions -->
      <div class="form-actions">
        <button
          v-if="form.smtp_enabled"
          type="button"
          @click="handleTest"
          :disabled="loading || !canTest"
          class="test-button"
        >
          <span v-if="testing" class="loading-spinner"></span>
          {{ testing ? '测试中...' : '测试连接' }}
        </button>
        
        <div class="action-group">
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
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import type { EmailSettings } from '@/types/settings'

// Props
interface Props {
  emailSettings?: EmailSettings
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

// Emits
interface Emits {
  (e: 'update', emailSettings: EmailSettings): void
  (e: 'test'): void
}

const emit = defineEmits<Emits>()

// Form data
const form = reactive<EmailSettings>({
  smtp_enabled: false,
  smtp_host: '',
  smtp_port: 587,
  smtp_username: '',
  smtp_password: '',
  smtp_use_tls: true
})

// Form errors
const errors = reactive<Partial<Record<keyof EmailSettings, string>>>({})

// Testing state
const testing = ref(false)

// Form validation
const isFormValid = computed(() => {
  if (!form.smtp_enabled) return true
  return form.smtp_host && form.smtp_port && Object.keys(errors).length === 0
})

const canTest = computed(() => {
  return form.smtp_enabled && form.smtp_host && form.smtp_port
})

// Initialize form with props data
const initializeForm = () => {
  if (props.emailSettings) {
    Object.assign(form, {
      smtp_enabled: props.emailSettings.smtp_enabled ?? false,
      smtp_host: props.emailSettings.smtp_host || '',
      smtp_port: props.emailSettings.smtp_port || 587,
      smtp_username: props.emailSettings.smtp_username || '',
      smtp_password: props.emailSettings.smtp_password || '',
      smtp_use_tls: props.emailSettings.smtp_use_tls ?? true
    })
  }
}

// Validate form fields
const validateField = (field: keyof EmailSettings, value: any) => {
  if (!form.smtp_enabled) {
    delete errors[field]
    return
  }

  switch (field) {
    case 'smtp_host':
      if (!value) {
        errors[field] = '请输入SMTP服务器地址'
      } else {
        delete errors[field]
      }
      break

    case 'smtp_port':
      if (!value || value < 1 || value > 65535) {
        errors[field] = '端口必须在1-65535之间'
      } else {
        delete errors[field]
      }
      break

    default:
      delete errors[field]
  }
}

// Watch form fields for validation
watch(() => form.smtp_enabled, () => {
  if (!form.smtp_enabled) {
    Object.keys(errors).forEach(key => {
      delete errors[key as keyof EmailSettings]
    })
  }
})

watch(() => form.smtp_host, (value) => validateField('smtp_host', value))
watch(() => form.smtp_port, (value) => validateField('smtp_port', value))

// Watch props changes
watch(
  () => props.emailSettings,
  () => {
    initializeForm()
  },
  { immediate: true, deep: true }
)

// Handle form submission
const handleSubmit = () => {
  if (form.smtp_enabled) {
    // Validate required fields when SMTP is enabled
    validateField('smtp_host', form.smtp_host)
    validateField('smtp_port', form.smtp_port)
  }

  if (isFormValid.value) {
    emit('update', { ...form })
  }
}

// Handle test connection
const handleTest = async () => {
  testing.value = true
  try {
    emit('test')
  } finally {
    // Reset testing state after parent handles the test
    setTimeout(() => {
      testing.value = false
    }, 1000)
  }
}

// Handle form reset
const handleReset = () => {
  initializeForm()
  Object.keys(errors).forEach(key => {
    delete errors[key as keyof EmailSettings]
  })
}
</script>

<style scoped>
.email-settings-form {
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

.form-group.full-width {
  grid-column: 1 / -1;
}

.smtp-config {
  padding: 1.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  background-color: #f9fafb;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
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
  font-weight: 500;
}

.form-error {
  color: #dc2626;
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
  flex-wrap: wrap;
  gap: 1rem;
}

.action-group {
  display: flex;
  gap: 1rem;
}

.test-button,
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

.test-button {
  background-color: #10b981;
  color: white;
}

.test-button:hover:not(:disabled) {
  background-color: #059669;
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

.test-button:disabled,
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
    align-items: stretch;
  }
  
  .action-group {
    justify-content: space-between;
  }
}
</style>