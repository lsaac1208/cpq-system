<template>
  <div class="template-selector">
    <!-- 搜索和筛选 -->
    <div class="selector-header">
      <el-input
        v-model="searchQuery"
        placeholder="搜索模板..."
        :prefix-icon="Search"
        style="width: 300px"
        clearable
      />
      
      <el-select
        v-model="selectedCategory"
        placeholder="选择分类"
        clearable
        style="width: 200px; margin-left: 15px"
      >
        <el-option
          v-for="category in categories"
          :key="category"
          :label="category"
          :value="category"
        />
      </el-select>
      
      <el-select
        v-model="selectedTag"
        placeholder="选择标签"
        clearable
        style="width: 200px; margin-left: 15px"
      >
        <el-option
          v-for="tag in popularTags"
          :key="tag"
          :label="tag"
          :value="tag"
        />
      </el-select>
    </div>

    <!-- 模板列表 -->
    <div class="template-list" v-loading="loading">
      <div v-if="filteredTemplates.length === 0" class="empty-state">
        <el-empty description="未找到匹配的模板">
          <el-button type="primary" @click="clearFilters">清除筛选条件</el-button>
        </el-empty>
      </div>
      
      <div 
        v-for="template in filteredTemplates" 
        :key="template.id"
        class="template-item"
        @click="selectTemplate(template)"
      >
        <div class="template-header">
          <h4 class="template-name">{{ template.name }}</h4>
          <div class="template-badges">
            <el-tag size="small" type="info">{{ template.category }}</el-tag>
            <el-tag v-if="template.is_public" size="small" type="success">公开</el-tag>
            <el-tag v-else size="small" type="warning">私有</el-tag>
          </div>
        </div>
        
        <p class="template-description">{{ template.description }}</p>
        
        <div class="template-content-preview">
          <code>{{ truncateText(template.template_content, 200) }}</code>
        </div>
        
        <div class="template-tags">
          <el-tag 
            v-for="tag in template.tags.slice(0, 3)" 
            :key="tag"
            size="small"
            effect="plain"
          >
            {{ tag }}
          </el-tag>
          <span v-if="template.tags.length > 3" class="more-tags">
            +{{ template.tags.length - 3 }}
          </span>
        </div>
        
        <div class="template-stats">
          <span class="stat-item">
            <el-icon><View /></el-icon>
            使用 {{ template.usage_count }} 次
          </span>
          <span class="stat-item">
            <el-rate 
              v-model="template.average_rating" 
              disabled
              show-score
              :max="5"
              size="small"
            />
          </span>
          <span class="stat-item">
            成功率 {{ (template.success_rate * 100).toFixed(0) }}%
          </span>
        </div>
        
        <div class="template-meta">
          <span class="created-at">
            创建于 {{ formatDate(template.created_at) }}
          </span>
          <span class="version">v{{ template.version }}</span>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-container" v-if="pagination.total > 0">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.per_page"
        :page-sizes="[10, 20, 50]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 操作按钮 -->
    <div class="selector-actions">
      <el-button @click="$emit('close')">取消</el-button>
      <el-button 
        type="primary" 
        :disabled="!selectedTemplate"
        @click="confirmSelection"
      >
        选择模板
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
// ElMessage removed
import { showMessage } from '@/utils/message'
import { Search, View } from '@element-plus/icons-vue'
import { getPromptTemplates } from '@/api/prompt-optimization'
import type { PromptTemplate, PromptTemplateResponse } from '@/types/prompt-optimization'

// 组件事件
const emit = defineEmits<{
  'template-selected': [template: PromptTemplate]
  'close': []
}>()

// 响应式数据
const loading = ref(false)
const searchQuery = ref('')
const selectedCategory = ref('')
const selectedTag = ref('')
const selectedTemplate = ref<PromptTemplate | null>(null)

const templates = ref<PromptTemplate[]>([])
const categories = ref<string[]>([])
const popularTags = ref<string[]>([])

const pagination = reactive({
  page: 1,
  per_page: 10,
  total: 0,
  pages: 0
})

// 计算属性
const filteredTemplates = computed(() => {
  let filtered = templates.value

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(template => 
      template.name.toLowerCase().includes(query) ||
      template.description.toLowerCase().includes(query) ||
      template.template_content.toLowerCase().includes(query)
    )
  }

  if (selectedCategory.value) {
    filtered = filtered.filter(template => 
      template.category === selectedCategory.value
    )
  }

  if (selectedTag.value) {
    filtered = filtered.filter(template => 
      template.tags.includes(selectedTag.value)
    )
  }

  return filtered
})

// 方法
const loadTemplates = async () => {
  try {
    loading.value = true
    const params = {
      page: pagination.page,
      per_page: pagination.per_page,
      ...(selectedCategory.value && { category: selectedCategory.value }),
      ...(selectedTag.value && { tag: selectedTag.value })
    }

    const response: PromptTemplateResponse = await getPromptTemplates(params)
    
    if (response.success) {
      templates.value = response.templates
      categories.value = response.categories
      popularTags.value = response.popular_tags
      
      Object.assign(pagination, response.pagination)
    } else {
      throw new Error('加载模板失败')
    }
  } catch (error) {
    showMessage.error('加载模板失败')
    console.error('Error loading templates:', error)
  } finally {
    loading.value = false
  }
}

const selectTemplate = (template: PromptTemplate) => {
  selectedTemplate.value = template
}

const confirmSelection = () => {
  if (selectedTemplate.value) {
    emit('template-selected', selectedTemplate.value)
  }
}

const clearFilters = () => {
  searchQuery.value = ''
  selectedCategory.value = ''
  selectedTag.value = ''
  pagination.page = 1
  loadTemplates()
}

const handleSizeChange = (size: number) => {
  pagination.per_page = size
  pagination.page = 1
  loadTemplates()
}

const handleCurrentChange = (page: number) => {
  pagination.page = page
  loadTemplates()
}

const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

// 监听筛选条件变化
watch([selectedCategory, selectedTag], () => {
  pagination.page = 1
  loadTemplates()
})

watch(searchQuery, () => {
  // 搜索使用本地筛选，不需要重新加载
})

onMounted(() => {
  loadTemplates()
})
</script>

<style scoped>
.template-selector {
  min-height: 400px;
}

.selector-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 10px;
}

.template-list {
  max-height: 500px;
  overflow-y: auto;
  margin-bottom: 20px;
}

.template-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;
  cursor: pointer;
  transition: all 0.3s;
  background: #fff;
}

.template-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
}

.template-item.selected {
  border-color: #409eff;
  background-color: #f0f9ff;
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.template-name {
  margin: 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
  flex: 1;
}

.template-badges {
  display: flex;
  gap: 5px;
  flex-shrink: 0;
}

.template-description {
  color: #606266;
  font-size: 14px;
  margin: 0 0 10px 0;
  line-height: 1.4;
}

.template-content-preview {
  background: #f5f7fa;
  border-radius: 4px;
  padding: 10px;
  margin-bottom: 10px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
  color: #606266;
  overflow: hidden;
}

.template-tags {
  margin-bottom: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  align-items: center;
}

.more-tags {
  color: #909399;
  font-size: 12px;
}

.template-stats {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 10px;
  font-size: 12px;
  color: #909399;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 3px;
}

.template-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #c0c4cc;
  border-top: 1px solid #f0f0f0;
  padding-top: 10px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin: 20px 0;
}

.selector-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 15px;
  border-top: 1px solid #e4e7ed;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .selector-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .selector-header > * {
    width: 100% !important;
    margin-left: 0 !important;
  }
  
  .template-header {
    flex-direction: column;
    gap: 10px;
  }
  
  .template-stats {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
  
  .template-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
  
  .selector-actions {
    flex-direction: column;
  }
}
</style>