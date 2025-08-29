<template>
  <el-card
    :body-style="bodyStyle"
    :shadow="shadow"
    :class="[
      'base-card',
      {
        'base-card--hoverable': hoverable,
        'base-card--clickable': clickable
      }
    ]"
    @click="handleClick"
  >
    <template #header v-if="$slots.header || title">
      <div class="card-header">
        <slot name="header">
          <h3 class="card-title">{{ title }}</h3>
        </slot>
        <div class="card-actions" v-if="$slots.actions">
          <slot name="actions" />
        </div>
      </div>
    </template>

    <div class="card-content">
      <slot />
    </div>

    <template #footer v-if="$slots.footer">
      <div class="card-footer">
        <slot name="footer" />
      </div>
    </template>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  title?: string
  shadow?: 'always' | 'hover' | 'never'
  hoverable?: boolean
  clickable?: boolean
  bodyStyle?: Record<string, string>
  loading?: boolean
}

interface Emits {
  (e: 'click', event: MouseEvent): void
}

const props = withDefaults(defineProps<Props>(), {
  shadow: 'hover',
  hoverable: false,
  clickable: false,
  loading: false
})

const emit = defineEmits<Emits>()

const handleClick = (event: MouseEvent) => {
  if (props.clickable) {
    emit('click', event)
  }
}
</script>

<style scoped>
.base-card {
  margin-bottom: 16px;
  transition: all 0.3s ease;
}

.base-card--hoverable:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.base-card--clickable {
  cursor: pointer;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.card-actions {
  display: flex;
  gap: 8px;
}

.card-content {
  min-height: 0; /* For flex layouts */
}

.card-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-lighter);
}

/* Loading state */
.base-card :deep(.el-loading-mask) {
  border-radius: var(--el-card-border-radius);
}
</style>