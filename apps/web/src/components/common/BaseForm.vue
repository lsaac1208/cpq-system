<template>
  <div class="base-form">
    <el-form
      ref="formRef"
      :model="modelValue"
      :rules="rules"
      :label-width="labelWidth"
      :label-position="labelPosition"
      :size="size"
      :disabled="disabled"
      :validate-on-rule-change="validateOnRuleChange"
      @submit.prevent="handleSubmit"
      v-bind="$attrs"
    >
      <slot />
      
      <!-- Form Actions -->
      <div class="form-actions" v-if="showActions">
        <slot name="actions">
          <BaseButton
            v-if="showCancelButton"
            type="default"
            @click="handleCancel"
            :disabled="loading"
          >
            {{ cancelText }}
          </BaseButton>
          
          <BaseButton
            v-if="showResetButton"
            type="warning"
            @click="handleReset"
            :disabled="loading"
          >
            {{ resetText }}
          </BaseButton>
          
          <BaseButton
            type="primary"
            @click="handleSubmit"
            :loading="loading"
          >
            {{ submitText }}
          </BaseButton>
        </slot>
      </div>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import BaseButton from './BaseButton.vue'

interface Props {
  modelValue: Record<string, any>
  rules?: Record<string, any>
  labelWidth?: string | number
  labelPosition?: 'left' | 'right' | 'top'
  size?: 'large' | 'default' | 'small'
  disabled?: boolean
  loading?: boolean
  validateOnRuleChange?: boolean
  showActions?: boolean
  showCancelButton?: boolean
  showResetButton?: boolean
  submitText?: string
  cancelText?: string
  resetText?: string
}

interface Emits {
  (e: 'update:modelValue', value: Record<string, any>): void
  (e: 'submit', formData: Record<string, any>): void
  (e: 'cancel'): void
  (e: 'reset'): void
  (e: 'validate', isValid: boolean, invalidFields?: Record<string, any>): void
}

const props = withDefaults(defineProps<Props>(), {
  labelWidth: '120px',
  labelPosition: 'right',
  size: 'default',
  disabled: false,
  loading: false,
  validateOnRuleChange: true,
  showActions: true,
  showCancelButton: true,
  showResetButton: false,
  submitText: '提交',
  cancelText: '取消',
  resetText: '重置'
})

const emit = defineEmits<Emits>()

const formRef = ref()

const handleSubmit = async () => {
  try {
    const isValid = await validate()
    if (isValid) {
      emit('submit', props.modelValue)
    }
  } catch (error) {
    console.error('Form validation failed:', error)
  }
}

const handleCancel = () => {
  emit('cancel')
}

const handleReset = () => {
  resetFields()
  emit('reset')
}

// Public methods
const validate = (): Promise<boolean> => {
  return new Promise((resolve) => {
    formRef.value?.validate((valid: boolean, invalidFields?: Record<string, any>) => {
      emit('validate', valid, invalidFields)
      if (!valid && invalidFields) {
        // Show validation error message
        const firstError = Object.values(invalidFields)[0]
        if (Array.isArray(firstError) && firstError.length > 0) {
          ElMessage.error(firstError[0].message)
        }
      }
      resolve(valid)
    })
  })
}

const validateField = (prop: string): Promise<boolean> => {
  return new Promise((resolve) => {
    formRef.value?.validateField(prop, (errorMessage: string) => {
      resolve(!errorMessage)
    })
  })
}

const resetFields = () => {
  formRef.value?.resetFields()
}

const clearValidation = (props?: string | string[]) => {
  formRef.value?.clearValidate(props)
}

// Scroll to first error field
const scrollToField = (prop: string) => {
  nextTick(() => {
    const field = formRef.value?.$el.querySelector(`[data-prop="${prop}"]`)
    if (field) {
      field.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  })
}

defineExpose({
  validate,
  validateField,
  resetFields,
  clearValidation,
  scrollToField
})
</script>

<style scoped>
.base-form {
  width: 100%;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--el-border-color-lighter);
}

/* Responsive form actions */
@media (max-width: 768px) {
  .form-actions {
    flex-direction: column-reverse;
  }
  
  .form-actions :deep(.el-button) {
    width: 100%;
  }
}

/* Form field spacing */
.base-form :deep(.el-form-item) {
  margin-bottom: 22px;
}

.base-form :deep(.el-form-item:last-child) {
  margin-bottom: 0;
}

/* Improved form field focus */
.base-form :deep(.el-input__wrapper) {
  transition: all 0.3s ease;
}

.base-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--el-input-hover-border-color) inset;
}

.base-form :deep(.el-textarea__inner) {
  transition: all 0.3s ease;
}

.base-form :deep(.el-textarea__inner:hover) {
  border-color: var(--el-input-hover-border-color);
}
</style>