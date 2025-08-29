<template>
  <div class="search-box">
    <div class="search-input-container">
      <el-input
        v-model="searchQuery"
        :placeholder="placeholder"
        :size="size"
        :loading="loading"
        clearable
        @input="handleInput"
        @keyup.enter="handleSearch"
        @focus="handleFocus"
        @blur="handleBlur"
        class="search-input"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
        <template #suffix>
          <el-button
            type="primary"
            :size="size"
            :loading="searching"
            @click="handleSearch"
            class="search-button"
          >
            搜索
          </el-button>
        </template>
      </el-input>
      
      <!-- 搜索建议下拉框 -->
      <div
        v-if="showSuggestions && suggestions.length > 0"
        class="suggestions-dropdown"
        v-click-outside="hideSuggestions"
      >
        <div
          v-for="(suggestion, index) in suggestions"
          :key="`${suggestion.type}-${index}`"
          class="suggestion-item"
          @click="selectSuggestion(suggestion)"
        >
          <div class="suggestion-icon">
            <el-icon v-if="suggestion.type === 'product'">
              <Box />
            </el-icon>
            <el-icon v-else-if="suggestion.type === 'code'">
              <Postcard />
            </el-icon>
            <el-icon v-else>
              <Folder />
            </el-icon>
          </div>
          
          <div class="suggestion-content">
            <div 
              class="suggestion-text"
              v-html="suggestion.highlighted || suggestion.text"
            />
            <div class="suggestion-meta">
              <span v-if="suggestion.category" class="category">
                {{ suggestion.category }}
              </span>
              <span v-if="suggestion.count" class="count">
                {{ suggestion.count }} 个结果
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 热门搜索 -->
    <div v-if="showHotSearches && hotSearches.length > 0" class="hot-searches">
      <div class="hot-searches-label">热门搜索：</div>
      <div class="hot-searches-list">
        <el-tag
          v-for="hotSearch in hotSearches"
          :key="hotSearch.query"
          class="hot-search-tag"
          @click="selectHotSearch(hotSearch.query)"
        >
          {{ hotSearch.query }}
          <span class="search-count">({{ hotSearch.count }})</span>
        </el-tag>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElInput, ElButton, ElIcon, ElTag } from 'element-plus'
import { Search, Box, Postcard, Folder } from '@element-plus/icons-vue'
import { SearchAPI, type SearchSuggestion, type HotSearch } from '@/api/search'
import { debounce } from 'lodash'

// Props
interface Props {
  modelValue?: string
  placeholder?: string
  size?: 'large' | 'default' | 'small'
  showHotSearches?: boolean
  autoFocus?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  placeholder: '搜索产品名称、型号、规格...',
  size: 'default',
  showHotSearches: true,
  autoFocus: false
})

// Emits
interface Emits {
  (e: 'update:modelValue', value: string): void
  (e: 'search', query: string): void
  (e: 'select-suggestion', suggestion: SearchSuggestion): void
}

const emit = defineEmits<Emits>()

// 状态
const searchQuery = ref(props.modelValue)
const suggestions = ref<SearchSuggestion[]>([])
const hotSearches = ref<HotSearch[]>([])
const loading = ref(false)
const searching = ref(false)
const showSuggestions = ref(false)
const inputFocused = ref(false)

// 计算属性
const shouldShowSuggestions = computed(() => 
  showSuggestions.value && inputFocused.value && searchQuery.value.length >= 2
)

// 监听搜索词变化
watch(() => props.modelValue, (newValue) => {
  searchQuery.value = newValue
})

watch(searchQuery, (newValue) => {
  emit('update:modelValue', newValue)
})

// 防抖获取搜索建议
const debouncedGetSuggestions = debounce(async (query: string) => {
  if (!query || query.length < 2) {
    suggestions.value = []
    return
  }
  
  try {
    loading.value = true
    suggestions.value = await SearchAPI.getSearchSuggestions(query, 8)
  } catch (error) {
    console.error('获取搜索建议失败:', error)
    suggestions.value = []
  } finally {
    loading.value = false
  }
}, 300)

// 事件处理
const handleInput = (value: string) => {
  searchQuery.value = value
  debouncedGetSuggestions(value)
  showSuggestions.value = true
}

const handleFocus = () => {
  inputFocused.value = true
  if (searchQuery.value.length >= 2) {
    showSuggestions.value = true
  }
}

const handleBlur = () => {
  // 延迟隐藏建议，以便点击建议项
  setTimeout(() => {
    inputFocused.value = false
    showSuggestions.value = false
  }, 200)
}

const handleSearch = () => {
  if (!searchQuery.value.trim()) return
  
  searching.value = true
  showSuggestions.value = false
  
  try {
    emit('search', searchQuery.value.trim())
  } finally {
    searching.value = false
  }
}

const selectSuggestion = (suggestion: SearchSuggestion) => {
  searchQuery.value = suggestion.text
  showSuggestions.value = false
  emit('select-suggestion', suggestion)
  
  // 自动搜索
  setTimeout(() => {
    handleSearch()
  }, 100)
}

const selectHotSearch = (query: string) => {
  searchQuery.value = query
  handleSearch()
}

const hideSuggestions = () => {
  showSuggestions.value = false
}

// 获取热门搜索
const loadHotSearches = async () => {
  try {
    hotSearches.value = await SearchAPI.getHotSearches(6, 7)
  } catch (error) {
    console.error('获取热门搜索失败:', error)
  }
}

// 生命周期
onMounted(() => {
  if (props.showHotSearches) {
    loadHotSearches()
  }
})

// 点击外部指令
const vClickOutside = {
  mounted(el: HTMLElement, binding: any) {
    el._clickOutsideHandler = (event: Event) => {
      if (!(el === event.target || el.contains(event.target as Node))) {
        binding.value()
      }
    }
    document.addEventListener('click', el._clickOutsideHandler)
  },
  unmounted(el: HTMLElement) {
    document.removeEventListener('click', el._clickOutsideHandler)
  }
}
</script>

<style scoped>
.search-box {
  position: relative;
  width: 100%;
}

.search-input-container {
  position: relative;
}

.search-input {
  width: 100%;
}

.search-input :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.search-input :deep(.el-input__wrapper:hover) {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.search-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.search-button {
  border-radius: 0 6px 6px 0;
  border: none;
  margin-left: -1px;
}

.suggestions-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  max-height: 300px;
  overflow-y: auto;
  margin-top: 4px;
}

.suggestion-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  transition: background-color 0.2s ease;
  border-bottom: 1px solid #f5f7fa;
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-item:hover {
  background-color: #f5f7fa;
}

.suggestion-icon {
  margin-right: 12px;
  color: #909399;
  font-size: 16px;
  flex-shrink: 0;
}

.suggestion-content {
  flex: 1;
  min-width: 0;
}

.suggestion-text {
  font-size: 14px;
  color: #303133;
  margin-bottom: 4px;
  word-break: break-word;
}

.suggestion-text :deep(mark) {
  background-color: #409eff;
  color: white;
  padding: 1px 3px;
  border-radius: 2px;
  font-weight: 500;
}

.suggestion-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #909399;
}

.category {
  background-color: #f0f2f5;
  padding: 2px 6px;
  border-radius: 4px;
}

.count {
  font-weight: 500;
}

.hot-searches {
  margin-top: 16px;
  padding: 12px 0;
}

.hot-searches-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.hot-searches-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.hot-search-tag {
  cursor: pointer;
  transition: all 0.2s ease;
}

.hot-search-tag:hover {
  background-color: #409eff;
  color: white;
}

.search-count {
  font-size: 11px;
  opacity: 0.8;
  margin-left: 4px;
}

@media (max-width: 768px) {
  .search-input :deep(.el-input__inner) {
    font-size: 16px; /* 防止iOS缩放 */
  }
  
  .suggestions-dropdown {
    position: fixed;
    left: 16px;
    right: 16px;
    max-height: 50vh;
  }
  
  .hot-searches-list {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>