<template>
  <div class="comparison-history">
    <div class="history-header">
      <h3>对比历史</h3>
      <p>查看和管理历史文档对比记录</p>
    </div>

    <div class="filters">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-input
            v-model="searchQuery"
            placeholder="搜索对比记录..."
            clearable
            @change="handleSearch"
          />
        </el-col>
        <el-col :span="4">
          <el-select v-model="statusFilter" placeholder="状态" clearable>
            <el-option label="全部" value="" />
            <el-option label="已完成" value="completed" />
            <el-option label="进行中" value="processing" />
            <el-option label="失败" value="failed" />
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
      <el-table-column prop="name" label="对比名称" min-width="200" />
      <el-table-column prop="documentCount" label="文档数量" width="100" />
      <el-table-column prop="similarity" label="相似度" width="100">
        <template #default="scope">
          <span>{{ scope.row.similarity }}%</span>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="scope">
          <el-tag :type="getStatusType(scope.row.status)">
            {{ scope.row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="createdAt" label="创建时间" width="180" />
      <el-table-column label="操作" width="200">
        <template #default="scope">
          <el-button size="small" @click="viewComparison(scope.row)">
            查看
          </el-button>
          <el-button size="small" type="primary" @click="downloadReport(scope.row)">
            下载
          </el-button>
          <el-button size="small" type="danger" @click="deleteComparison(scope.row)">
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessageBox } from 'element-plus'
import { showMessage } from '@/utils/message'

const emit = defineEmits(['view-comparison'])

// 响应式数据
const loading = ref(false)
const searchQuery = ref('')
const statusFilter = ref('')
const dateRange = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 模拟历史数据
const historyData = ref([
  {
    id: 1,
    name: 'A703与A704产品对比',
    documentCount: 2,
    similarity: 78,
    status: 'completed',
    createdAt: '2024-08-16 14:30:25',
    documents: ['A703说明书.pdf', 'A704说明书.pdf']
  },
  {
    id: 2,
    name: '继电保护设备规格对比',
    documentCount: 3,
    similarity: 65,
    status: 'completed',
    createdAt: '2024-08-15 09:15:12',
    documents: ['设备A.pdf', '设备B.pdf', '设备C.pdf']
  },
  {
    id: 3,
    name: '技术标准文档对比',
    documentCount: 2,
    similarity: 92,
    status: 'processing',
    createdAt: '2024-08-16 16:20:08',
    documents: ['标准V1.pdf', '标准V2.pdf']
  }
])

// 计算属性
const filteredHistory = computed(() => {
  let filtered = historyData.value

  if (searchQuery.value) {
    filtered = filtered.filter(item =>
      item.name.toLowerCase().includes(searchQuery.value.toLowerCase())
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
const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    completed: 'success',
    processing: 'warning',
    failed: 'danger'
  }
  return statusMap[status] || 'info'
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

const viewComparison = (record: any) => {
  emit('view-comparison', record)
}

const downloadReport = (record: any) => {
  showMessage.success(`正在下载对比报告: ${record.name}`)
}

const deleteComparison = async (record: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除对比记录"${record.name}"吗？`,
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
.comparison-history {
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

.pagination {
  margin-top: 20px;
  text-align: center;
}
</style>