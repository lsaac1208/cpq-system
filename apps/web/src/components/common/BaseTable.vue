<template>
  <div class="base-table">
    <!-- Table Header -->
    <div class="table-header" v-if="$slots.header || title">
      <div class="table-title">
        <slot name="header">
          <h3 v-if="title">{{ title }}</h3>
        </slot>
      </div>
      <div class="table-actions" v-if="$slots.actions">
        <slot name="actions" />
      </div>
    </div>

    <!-- Search and Filters -->
    <div class="table-controls" v-if="searchable || $slots.filters">
      <div class="search-container" v-if="searchable">
        <el-input
          v-model="searchQuery"
          placeholder="搜索..."
          :prefix-icon="Search"
          clearable
          @input="handleSearch"
          style="width: 300px"
        />
      </div>
      <div class="filters-container" v-if="$slots.filters">
        <slot name="filters" />
      </div>
    </div>

    <!-- Table -->
    <el-table
      ref="tableRef"
      :data="filteredData"
      :loading="loading"
      :stripe="stripe"
      :border="border"
      :height="height"
      :max-height="maxHeight"
      :row-key="rowKey"
      :default-sort="defaultSort"
      @selection-change="handleSelectionChange"
      @sort-change="handleSortChange"
      @row-click="handleRowClick"
      v-bind="$attrs"
    >
      <!-- Selection Column -->
      <el-table-column
        v-if="selectable"
        type="selection"
        width="55"
        :reserve-selection="true"
      />

      <!-- Index Column -->
      <el-table-column
        v-if="showIndex"
        type="index"
        label="#"
        width="60"
        align="center"
      />

      <!-- Dynamic Columns -->
      <slot />

      <!-- Actions Column -->
      <el-table-column
        v-if="$slots.actions"
        label="操作"
        :width="actionsWidth"
        align="center"
        fixed="right"
      >
        <template #default="scope">
          <slot name="actions" :row="scope.row" :index="scope.$index" />
        </template>
      </el-table-column>
    </el-table>

    <!-- Pagination -->
    <div class="table-pagination" v-if="pagination && pagination.total > 0">
      <el-pagination
        v-model:current-page="pagination.current"
        v-model:page-size="pagination.pageSize"
        :page-sizes="pageSizes"
        :total="pagination.total"
        :background="true"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- Empty State -->
    <div class="empty-state" v-if="!loading && (!data || data.length === 0)">
      <slot name="empty">
        <el-empty description="暂无数据" />
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Search } from '@element-plus/icons-vue'

interface PaginationConfig {
  current: number
  pageSize: number
  total: number
}

interface Props {
  data: any[]
  loading?: boolean
  title?: string
  searchable?: boolean
  selectable?: boolean
  showIndex?: boolean
  stripe?: boolean
  border?: boolean
  height?: string | number
  maxHeight?: string | number
  rowKey?: string
  defaultSort?: { prop: string; order: string }
  pagination?: PaginationConfig
  actionsWidth?: string | number
}

interface Emits {
  (e: 'search', query: string): void
  (e: 'selection-change', selection: any[]): void
  (e: 'sort-change', sort: { column: any; prop: string; order: string }): void
  (e: 'row-click', row: any, column: any, event: Event): void
  (e: 'page-change', page: number): void
  (e: 'page-size-change', size: number): void
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  searchable: false,
  selectable: false,
  showIndex: false,
  stripe: true,
  border: true,
  actionsWidth: 120
})

const emit = defineEmits<Emits>()

const tableRef = ref()
const searchQuery = ref('')
const pageSizes = [10, 20, 50, 100]

// Filtered data based on search
const filteredData = computed(() => {
  if (!props.searchable || !searchQuery.value) {
    return props.data || []
  }
  
  const query = searchQuery.value.toLowerCase()
  return (props.data || []).filter((item: any) => {
    return Object.values(item).some((value: any) =>
      String(value).toLowerCase().includes(query)
    )
  })
})

const handleSearch = (query: string) => {
  emit('search', query)
}

const handleSelectionChange = (selection: any[]) => {
  emit('selection-change', selection)
}

const handleSortChange = (sort: { column: any; prop: string; order: string }) => {
  emit('sort-change', sort)
}

const handleRowClick = (row: any, column: any, event: Event) => {
  emit('row-click', row, column, event)
}

const handleCurrentChange = (page: number) => {
  emit('page-change', page)
}

const handleSizeChange = (size: number) => {
  emit('page-size-change', size)
}

// Public methods
const clearSelection = () => {
  tableRef.value?.clearSelection()
}

const toggleRowSelection = (row: any, selected?: boolean) => {
  tableRef.value?.toggleRowSelection(row, selected)
}

const getSelectionRows = () => {
  return tableRef.value?.getSelectionRows() || []
}

defineExpose({
  clearSelection,
  toggleRowSelection,
  getSelectionRows
})
</script>

<style scoped>
.base-table {
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.table-title h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.table-actions {
  display: flex;
  gap: 8px;
}

.table-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--el-bg-color-page);
}

.search-container {
  flex: 1;
}

.filters-container {
  display: flex;
  gap: 12px;
  align-items: center;
}

.table-pagination {
  display: flex;
  justify-content: flex-end;
  padding: 16px 20px;
  background: var(--el-bg-color-page);
}

.empty-state {
  padding: 40px 20px;
  text-align: center;
  background: white;
}

/* Table responsiveness */
@media (max-width: 768px) {
  .table-controls {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .search-container {
    order: 2;
  }
  
  .filters-container {
    order: 1;
    justify-content: center;
  }
}
</style>