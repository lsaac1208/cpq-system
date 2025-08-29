<template>
  <div class="settings-page">
    <!-- Page Header -->
    <div class="settings-header">
      <h1 class="settings-title">系统设置</h1>
      <p class="settings-subtitle">管理系统配置和公司信息</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>加载设置中...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <div class="error-message">
        <h3>加载失败</h3>
        <p>{{ error }}</p>
        <button @click="loadSettings" class="retry-button">重试</button>
      </div>
    </div>

    <!-- Settings Content -->
    <div v-else class="settings-content">
      <!-- Tab Navigation -->
      <div class="settings-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          @click="activeTab = tab.key"
          :class="['tab-button', { 'active': activeTab === tab.key }]"
        >
          <component :is="tab.icon" class="tab-icon" />
          {{ tab.label }}
        </button>
      </div>

      <!-- Tab Content -->
      <div class="tab-content">
        <!-- Company Information Tab -->
        <div v-if="activeTab === 'company'" class="tab-panel">
          <CompanyInfoForm
            :company-info="settings?.company_info"
            :loading="saving"
            @update="updateCompanyInfo"
          />
        </div>

        <!-- System Configuration Tab -->
        <div v-if="activeTab === 'system'" class="tab-panel">
          <SystemConfigForm
            :system-config="settings?.system_config"
            :loading="saving"
            @update="updateSystemConfig"
          />
        </div>

        <!-- PDF Settings Tab -->
        <div v-if="activeTab === 'pdf'" class="tab-panel">
          <PDFSettingsForm
            :pdf-settings="settings?.pdf_settings"
            :loading="saving"
            @update="updatePDFSettings"
          />
        </div>

        <!-- Email Settings Tab -->
        <div v-if="activeTab === 'email'" class="tab-panel">
          <EmailSettingsForm
            :email-settings="settings?.email_settings"
            :loading="saving"
            @update="updateEmailSettings"
            @test="testEmailSettings"
          />
        </div>

        <!-- Business Rules Tab -->
        <div v-if="activeTab === 'business'" class="tab-panel">
          <BusinessRulesForm
            :business-rules="settings?.business_rules"
            :loading="saving"
            @update="updateBusinessRules"
          />
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="settings-actions">
        <button
          @click="resetSettings"
          :disabled="saving"
          class="reset-button"
        >
          重置为默认值
        </button>
        
        <div class="action-buttons">
          <button
            @click="loadSettings(true)"
            :disabled="saving"
            class="refresh-button"
          >
            刷新
          </button>
        </div>
      </div>
    </div>

    <!-- Success/Error Messages -->
    <div v-if="message" :class="['message', messageType]">
      {{ message }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import cachedSettingsApi from '@/api/settings'
import type { 
  SystemSettings, 
  SettingsTab, 
  UpdateSettingsRequest,
  CompanyInfo,
  SystemConfig,
  PDFSettings,
  EmailSettings,
  BusinessRules
} from '@/types/settings'
import CompanyInfoForm from '@/components/settings/CompanyInfoForm.vue'
import SystemConfigForm from '@/components/settings/SystemConfigForm.vue'
import PDFSettingsForm from '@/components/settings/PDFSettingsForm.vue'
import EmailSettingsForm from '@/components/settings/EmailSettingsForm.vue'
import BusinessRulesForm from '@/components/settings/BusinessRulesForm.vue'

// Icons (you can replace with your preferred icon library)
import { 
  BuildingOfficeIcon,
  CogIcon,
  DocumentIcon,
  EnvelopeIcon,
  ShieldCheckIcon
} from '@heroicons/vue/24/outline'

// Reactive state
const settings = ref<SystemSettings | null>(null)
const loading = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)
const message = ref<string>('')
const messageType = ref<'success' | 'error'>('success')
const activeTab = ref<SettingsTab>('company')

// Tab configuration
const tabs = [
  { key: 'company' as SettingsTab, label: '公司信息', icon: BuildingOfficeIcon },
  { key: 'system' as SettingsTab, label: '系统配置', icon: CogIcon },
  { key: 'pdf' as SettingsTab, label: 'PDF设置', icon: DocumentIcon },
  { key: 'email' as SettingsTab, label: '邮件设置', icon: EnvelopeIcon },
  { key: 'business' as SettingsTab, label: '业务规则', icon: ShieldCheckIcon }
]

// Load settings
const loadSettings = async (forceRefresh = false) => {
  loading.value = true
  error.value = null
  
  try {
    settings.value = await cachedSettingsApi.getSettings(forceRefresh)
  } catch (err: any) {
    error.value = err.message || '加载设置失败'
    console.error('Failed to load settings:', err)
  } finally {
    loading.value = false
  }
}

// Update methods for each section
const updateCompanyInfo = async (companyInfo: CompanyInfo) => {
  await updateSettings({ company_info: companyInfo })
}

const updateSystemConfig = async (systemConfig: SystemConfig) => {
  await updateSettings({ system_config: systemConfig })
}

const updatePDFSettings = async (pdfSettings: PDFSettings) => {
  await updateSettings({ pdf_settings: pdfSettings })
}

const updateEmailSettings = async (emailSettings: EmailSettings) => {
  await updateSettings({ email_settings: emailSettings })
}

const updateBusinessRules = async (businessRules: BusinessRules) => {
  await updateSettings({ business_rules: businessRules })
}

// Generic update settings method
const updateSettings = async (updates: UpdateSettingsRequest) => {
  saving.value = true
  
  try {
    settings.value = await cachedSettingsApi.updateSettings(updates)
    showMessage('设置更新成功', 'success')
  } catch (err: any) {
    showMessage(err.message || '更新设置失败', 'error')
    console.error('Failed to update settings:', err)
  } finally {
    saving.value = false
  }
}

// Test email settings
const testEmailSettings = async () => {
  saving.value = true
  
  try {
    const result = await cachedSettingsApi.testEmailSettings()
    showMessage(result.message || '邮件测试成功', 'success')
  } catch (err: any) {
    showMessage(err.message || '邮件测试失败', 'error')
    console.error('Failed to test email settings:', err)
  } finally {
    saving.value = false
  }
}

// Reset settings
const resetSettings = async () => {
  if (!confirm('确定要重置为默认设置吗？此操作不可恢复。')) {
    return
  }
  
  saving.value = true
  
  try {
    settings.value = await cachedSettingsApi.resetSettings()
    showMessage('设置已重置为默认值', 'success')
  } catch (err: any) {
    showMessage(err.message || '重置设置失败', 'error')
    console.error('Failed to reset settings:', err)
  } finally {
    saving.value = false
  }
}

// Show message
const showMessage = (text: string, type: 'success' | 'error') => {
  message.value = text
  messageType.value = type
  
  // Auto hide after 5 seconds
  setTimeout(() => {
    message.value = ''
  }, 5000)
}

// Initialize
onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.settings-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.settings-header {
  margin-bottom: 2rem;
}

.settings-title {
  font-size: 2rem;
  font-weight: bold;
  color: #1f2937;
  margin: 0 0 0.5rem 0;
}

.settings-subtitle {
  color: #6b7280;
  margin: 0;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem;
}

.loading-spinner {
  width: 3rem;
  height: 3rem;
  border: 3px solid #e5e7eb;
  border-top: 3px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-container {
  display: flex;
  justify-content: center;
  padding: 4rem;
}

.error-message {
  text-align: center;
  padding: 2rem;
  border: 1px solid #fca5a5;
  border-radius: 0.5rem;
  background-color: #fef2f2;
}

.error-message h3 {
  color: #dc2626;
  margin: 0 0 1rem 0;
}

.error-message p {
  color: #991b1b;
  margin: 0 0 1rem 0;
}

.retry-button {
  background-color: #dc2626;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.25rem;
  cursor: pointer;
}

.retry-button:hover {
  background-color: #b91c1c;
}

.settings-content {
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.settings-tabs {
  display: flex;
  border-bottom: 1px solid #e5e7eb;
  background-color: #f9fafb;
}

.tab-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem 1.5rem;
  border: none;
  background: none;
  color: #6b7280;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.tab-button:hover {
  color: #374151;
  background-color: #f3f4f6;
}

.tab-button.active {
  color: #3b82f6;
  background-color: white;
  border-bottom: 2px solid #3b82f6;
}

.tab-icon {
  width: 1.25rem;
  height: 1.25rem;
}

.tab-content {
  padding: 2rem;
}

.tab-panel {
  min-height: 400px;
}

.settings-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  border-top: 1px solid #e5e7eb;
  background-color: #f9fafb;
}

.reset-button {
  background-color: #dc2626;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 0.375rem;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.reset-button:hover:not(:disabled) {
  background-color: #b91c1c;
}

.reset-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-buttons {
  display: flex;
  gap: 1rem;
}

.refresh-button {
  background-color: #6b7280;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 0.375rem;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.refresh-button:hover:not(:disabled) {
  background-color: #4b5563;
}

.refresh-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.message {
  position: fixed;
  top: 2rem;
  right: 2rem;
  padding: 1rem 1.5rem;
  border-radius: 0.375rem;
  font-weight: 500;
  z-index: 1000;
  animation: slideIn 0.3s ease-out;
}

.message.success {
  background-color: #d1fae5;
  color: #065f46;
  border: 1px solid #a7f3d0;
}

.message.error {
  background-color: #fef2f2;
  color: #991b1b;
  border: 1px solid #fca5a5;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
</style>