<template>
  <el-button
    :type="buttonType"
    :size="size"
    :loading="loading"
    :disabled="disabled"
    :icon="icon"
    :plain="plain"
    :round="round"
    :circle="circle"
    @click="handleClick"
    :class="customClass"
  >
    <slot />
  </el-button>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  type?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'text'
  size?: 'large' | 'default' | 'small'
  loading?: boolean
  disabled?: boolean
  icon?: string
  plain?: boolean
  round?: boolean
  circle?: boolean
  variant?: 'solid' | 'outline' | 'ghost'
  customClass?: string
}

interface Emits {
  (e: 'click', event: MouseEvent): void
}

const props = withDefaults(defineProps<Props>(), {
  type: 'default',
  size: 'default',
  loading: false,
  disabled: false,
  plain: false,
  round: false,
  circle: false,
  variant: 'solid'
})

const emit = defineEmits<Emits>()

const buttonType = computed(() => {
  if (props.variant === 'outline') {
    return props.type === 'default' ? 'primary' : props.type
  }
  return props.type
})

const handleClick = (event: MouseEvent) => {
  if (!props.loading && !props.disabled) {
    emit('click', event)
  }
}
</script>

<style scoped>
.el-button--outline {
  border: 1px solid var(--el-button-border-color);
  background: transparent;
}

.el-button--ghost {
  background: transparent;
  border: none;
}

.el-button--ghost:hover {
  background: var(--el-fill-color-light);
}
</style>