<template>
  <div class="optimization-history">
    <div class="history-header">
      <h3>优化历史</h3>
      <p>查看历史Prompt优化记录和效果对比</p>
    </div>

    <div class="filters">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-input
            v-model="searchQuery"
            placeholder="搜索优化记录..."
            clearable
            @change="handleSearch"
          />
        </el-col>
        <el-col :span="4">
          <el-select v-model="statusFilter" placeholder="状态" clearable>
            <el-option label="全部" value="" />
            <el-option label="优化成功" value="success" />
            <el-option label="优化中" value="processing" />
            <el-option label="优化失败" value="failed" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            @change="handleDateChange"
          />
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="refreshHistory">刷新</el-button>
        </el-col>
      </el-row>
    </div>

    <el-table :data="filteredHistory" v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="original_prompt" label="原始Prompt" min-width="300">
        <template #default="scope">
          <div class="prompt-preview">
            {{ truncateText(scope.row.original_prompt, 100) }}
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="optimization_type" label="优化类型" width="120">
        <template #default="scope">
          <el-tag :type="getTypeColor(scope.row.optimization_type)" size="small">
            {{ scope.row.optimization_type }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="improvement_score" label="改进评分" width="100">
        <template #default="scope">
          <div class="score-display">
            <el-progress
              type="circle"
              :percentage="scope.row.improvement_score"
              :width="40"
              :stroke-width="6"
              :color="getScoreColor(scope.row.improvement_score)"
            />
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="scope">
          <el-tag :type="getStatusType(scope.row.status)">
            {{ getStatusText(scope.row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="200">
        <template #default="scope">
          <el-button size="small" @click="viewRecord(scope.row)">
            查看详情
          </el-button>
          <el-button size="small" type="primary" @click="applyOptimization(scope.row)">
            应用优化
          </el-button>
          <el-button size="small" type="danger" @click="deleteRecord(scope.row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      title="优化记录详情"
      width="80%"
      @close="currentRecord = null"
    >
      <div v-if="currentRecord" class="record-detail">
        <el-tabs>
          <el-tab-pane label="基本信息" name="basic">
            <div class="info-section">
              <div class="info-item">
                <label>优化ID:</label>
                <span>{{ currentRecord.id }}</span>
              </div>
              <div class="info-item">
                <label>优化类型:</label>
                <el-tag :type="getTypeColor(currentRecord.optimization_type)">
                  {{ currentRecord.optimization_type }}
                </el-tag>
              </div>
              <div class="info-item">
                <label>改进评分:</label>
                <span class="score">{{ currentRecord.improvement_score }}%</span>
              </div>
              <div class="info-item">
                <label>创建时间:</label>
                <span>{{ currentRecord.created_at }}</span>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="原始Prompt" name="original">
            <el-input
              v-model="currentRecord.original_prompt"
              type="textarea"
              :rows="10"
              readonly
            />
          </el-tab-pane>

          <el-tab-pane label="优化后Prompt" name="optimized">
            <el-input
              v-model="currentRecord.optimized_prompt"
              type="textarea"
              :rows="10"
              readonly
            />
          </el-tab-pane>

          <el-tab-pane label="优化建议" name="suggestions">
            <div class="suggestions-list">
              <div 
                v-for="(suggestion, index) in currentRecord.suggestions_applied" 
                :key="index"
                class="suggestion-item"
              >
                <div class="suggestion-type">
                  <el-tag size="small">{{ suggestion.type }}</el-tag>
                </div>
                <div class="suggestion-content">
                  <h4>{{ suggestion.title }}</h4>
                  <p>{{ suggestion.description }}</p>
                  <div class="suggestion-impact">
                    <span>预期影响: {{ suggestion.expected_impact }}%</span>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessageBox } from 'element-plus'
import { showMessage } from '@/utils/message'

const emit = defineEmits(['record-selected'])

// 响应式数据
const loading = ref(false)
const searchQuery = ref('')
const statusFilter = ref('')
const dateRange = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const showDetailDialog = ref(false)
const currentRecord = ref<any>(null)

// 模拟历史数据
const historyData = ref([
  {
    id: 1,
    original_prompt: '请分析以下产品文档，提取产品的基本信息、技术规格、产品特性等关键信息。',
    optimized_prompt: '请仔细分析以下产品文档，系统性地提取并整理产品的基本信息（名称、型号、代码）、详细技术规格（性能参数、技术指标）、以及产品特性（功能亮点、应用场景）等关键信息。请确保信息的准确性和完整性。',
    optimization_type: '结构优化',
    improvement_score: 85,
    status: 'success',
    created_at: '2024-08-16 14:30:25',
    suggestions_applied: [
      {
        type: '清晰度',
        title: '增强指令明确性',
        description: '在原始prompt基础上增加了"系统性地"、"详细"等修饰词，使指令更加明确',
        expected_impact: 25
      },
      {
        type: '完整性',
        title: '补充质量要求',
        description: '添加了"确保信息的准确性和完整性"的质量要求',
        expected_impact: 20
      }
    ]
  },
  {
    id: 2,
    original_prompt: '对文档进行质量评估',
    optimized_prompt: '请对以下文档进行全面的质量评估，从内容完整性、信息准确性、结构清晰度、语言规范性四个维度进行系统分析，并提供具体的评分依据和改进建议。',
    optimization_type: '语义增强',
    improvement_score: 92,
    status: 'success',
    created_at: '2024-08-15 09:15:12',
    suggestions_applied: [
      {
        type: '具体化',
        title: '明确评估维度',
        description: '将模糊的"质量评估"具体化为四个明确的评估维度',
        expected_impact: 40
      },
      {
        type: '输出规范',
        title: '规范输出要求',
        description: '要求提供评分依据和改进建议，使输出更加有价值',
        expected_impact: 30
      }
    ]
  },
  {
    id: 3,
    original_prompt: '分析文档类型',
    optimized_prompt: '请分析以下文档内容，基于文档的结构特征、内容主题、专业术语使用情况等因素，准确识别文档类型（如：产品说明书、技术规范、用户手册、测试报告等），并说明判断依据。',
    optimization_type: '上下文增强',
    improvement_score: 78,
    status: 'processing',
    created_at: '2024-08-16 16:20:08',
    suggestions_applied: [
      {
        type: '方法论',
        title: '增加分析方法',
        description: '提供了具体的分析维度：结构特征、内容主题、专业术语',
        expected_impact: 35
      }
    ]
  }
])

// 计算属性
const filteredHistory = computed(() => {
  let filtered = historyData.value

  if (searchQuery.value) {
    filtered = filtered.filter(item =>
      item.original_prompt.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      item.optimized_prompt.toLowerCase().includes(searchQuery.value.toLowerCase())
    )
  }

  if (statusFilter.value) {
    filtered = filtered.filter(item => item.status === statusFilter.value)
  }

  total.value = filtered.length
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filtered.slice(start, end)
})

// 方法
const truncateText = (text: string, maxLength: number) => {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

const getTypeColor = (type: string) => {
  const typeColors: Record<string, string> = {
    '结构优化': 'primary',
    '语义增强': 'success',
    '上下文增强': 'warning',
    '性能优化': 'info'
  }
  return typeColors[type] || 'info'
}

const getScoreColor = (score: number) => {
  if (score >= 80) return '#67C23A'
  if (score >= 60) return '#E6A23C'
  return '#F56C6C'
}

const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    success: 'success',
    processing: 'warning',
    failed: 'danger'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    success: '优化成功',
    processing: '优化中',
    failed: '优化失败'
  }
  return statusMap[status] || status
}

const handleSearch = () => {
  currentPage.value = 1
}

const handleDateChange = () => {
  currentPage.value = 1
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
}

const refreshHistory = async () => {
  loading.value = true
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    showMessage.success('历史记录已刷新')
  } catch (error) {
    showMessage.error('刷新失败')
  } finally {
    loading.value = false
  }
}

const viewRecord = (record: any) => {
  currentRecord.value = record
  showDetailDialog.value = true
  emit('record-selected', record)
}

const applyOptimization = (record: any) => {
  showMessage.success(`已应用优化记录 #${record.id} 的Prompt`)
}

const deleteRecord = async (record: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除优化记录 #${record.id} 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const index = historyData.value.findIndex(item => item.id === record.id)
    if (index > -1) {
      historyData.value.splice(index, 1)
      showMessage.success('删除成功')
    }
  } catch {
    // 用户取消删除
  }
}

onMounted(() => {
  refreshHistory()
})
</script>

<style scoped>
.optimization-history {
  padding: 20px;
}

.history-header {
  margin-bottom: 24px;
}

.history-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.history-header p {
  color: #909399;
  margin: 0;
}

.filters {
  margin-bottom: 20px;
}

.prompt-preview {
  line-height: 1.6;
  color: #606266;
}

.score-display {
  display: flex;
  justify-content: center;
}

.pagination {
  margin-top: 20px;
  text-align: center;
}

.record-detail {
  padding: 20px 0;
}

.info-section {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.info-item label {
  font-weight: 500;
  color: #606266;
  min-width: 80px;
}

.score {
  font-weight: 600;
  color: #409EFF;
}

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.suggestion-item {
  display: flex;
  gap: 12px;
  padding: 16px;
  background-color: #F5F7FA;
  border-radius: 8px;
}

.suggestion-type {
  flex-shrink: 0;
}

.suggestion-content {
  flex: 1;
}

.suggestion-content h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.suggestion-content p {
  margin: 0 0 8px 0;
  color: #606266;
  line-height: 1.6;
}

.suggestion-impact {
  font-size: 12px;
  color: #909399;
}
</style>