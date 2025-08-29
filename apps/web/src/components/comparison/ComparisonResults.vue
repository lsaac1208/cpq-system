<template>
  <div class="comparison-results">
    <div class="results-header">
      <h3>对比分析结果</h3>
      <p>详细的文档对比分析结果和差异报告</p>
    </div>

    <!-- 总体统计 -->
    <div class="summary-section">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ results.similarity || 0 }}%</div>
              <div class="stat-label">相似度</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ results.differences || 0 }}</div>
              <div class="stat-label">差异点</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ results.commonItems || 0 }}</div>
              <div class="stat-label">共同点</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ results.confidence || 0 }}%</div>
              <div class="stat-label">置信度</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 差异详情 -->
    <div class="differences-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <h4>差异详情</h4>
            <el-button-group>
              <el-button 
                :type="viewMode === 'table' ? 'primary' : ''"
                @click="viewMode = 'table'"
                size="small"
              >
                表格视图
              </el-button>
              <el-button 
                :type="viewMode === 'list' ? 'primary' : ''"
                @click="viewMode = 'list'"
                size="small"
              >
                列表视图
              </el-button>
            </el-button-group>
          </div>
        </template>

        <!-- 表格视图 -->
        <div v-if="viewMode === 'table'">
          <el-table :data="results.differenceDetails" v-loading="loading">
            <el-table-column prop="category" label="类别" width="120" />
            <el-table-column prop="field" label="字段" width="150" />
            <el-table-column prop="document1" label="文档1" min-width="200" />
            <el-table-column prop="document2" label="文档2" min-width="200" />
            <el-table-column prop="type" label="差异类型" width="100">
              <template #default="scope">
                <el-tag :type="getDifferenceType(scope.row.type)">
                  {{ scope.row.type }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 列表视图 -->
        <div v-else class="differences-list">
          <div 
            v-for="(diff, index) in results.differenceDetails" 
            :key="index"
            class="difference-item"
          >
            <div class="diff-header">
              <span class="diff-category">{{ diff.category }}</span>
              <el-tag :type="getDifferenceType(diff.type)" size="small">
                {{ diff.type }}
              </el-tag>
            </div>
            <div class="diff-content">
              <div class="diff-field">
                <strong>字段：</strong>{{ diff.field }}
              </div>
              <div class="diff-comparison">
                <div class="diff-item">
                  <span class="diff-label">文档1：</span>
                  <span class="diff-value">{{ diff.document1 }}</span>
                </div>
                <div class="diff-item">
                  <span class="diff-label">文档2：</span>
                  <span class="diff-value">{{ diff.document2 }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 相似内容 -->
    <div class="similarities-section">
      <el-card>
        <template #header>
          <h4>相似内容</h4>
        </template>
        <div class="similarities-list">
          <div 
            v-for="(item, index) in results.similarities" 
            :key="index"
            class="similarity-item"
          >
            <div class="similarity-header">
              <span class="similarity-category">{{ item.category }}</span>
              <span class="similarity-score">{{ item.score }}%</span>
            </div>
            <div class="similarity-content">
              {{ item.content }}
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 操作按钮 -->
    <div class="actions-section">
      <el-button type="primary" @click="downloadReport">
        <el-icon><Download /></el-icon>
        下载报告
      </el-button>
      <el-button @click="shareResults">
        <el-icon><Share /></el-icon>
        分享结果
      </el-button>
      <el-button @click="newComparison">
        <el-icon><Refresh /></el-icon>
        新建对比
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
// ElMessage removed
import { showMessage } from '@/utils/message'
import { Download, Share, Refresh } from '@element-plus/icons-vue'

interface Props {
  results?: any
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  results: () => ({
    similarity: 78,
    differences: 12,
    commonItems: 45,
    confidence: 85,
    differenceDetails: [
      {
        category: '技术规格',
        field: '额定电压',
        document1: '220V',
        document2: '380V',
        type: '数值不同'
      },
      {
        category: '产品特性',
        field: '工作温度',
        document1: '-10~50℃',
        document2: '0~60℃',
        type: '范围不同'
      },
      {
        category: '基本信息',
        field: '型号',
        document1: 'A703',
        document2: 'A704',
        type: '内容不同'
      }
    ],
    similarities: [
      {
        category: '产品类别',
        content: '三相继电保护测试仪',
        score: 95
      },
      {
        category: '制造商',
        content: '电力设备制造有限公司',
        score: 100
      },
      {
        category: '应用场景',
        content: '电力系统继电保护测试',
        score: 88
      }
    ]
  }),
  loading: false
})

const emit = defineEmits(['new-comparison'])

// 响应式数据
const viewMode = ref('table')

// 计算属性
const getDifferenceType = (type: string) => {
  const typeMap: Record<string, string> = {
    '数值不同': 'warning',
    '范围不同': 'info',
    '内容不同': 'danger',
    '格式不同': 'success'
  }
  return typeMap[type] || 'info'
}

// 方法
const downloadReport = () => {
  showMessage.success('报告下载中...')
}

const shareResults = () => {
  showMessage.success('分享链接已复制到剪贴板')
}

const newComparison = () => {
  emit('new-comparison')
}
</script>

<style scoped>
.comparison-results {
  padding: 20px;
}

.results-header {
  margin-bottom: 24px;
}

.results-header h3 {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.results-header p {
  color: #909399;
  margin: 0;
}

.summary-section {
  margin-bottom: 24px;
}

.stat-card {
  text-align: center;
}

.stat-item {
  padding: 20px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #409EFF;
  margin-bottom: 8px;
}

.stat-label {
  color: #909399;
  font-size: 14px;
}

.differences-section,
.similarities-section {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.differences-list {
  max-height: 400px;
  overflow-y: auto;
}

.difference-item {
  border: 1px solid #EBEEF5;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 12px;
}

.diff-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.diff-category {
  font-weight: 500;
  color: #303133;
}

.diff-content {
  color: #606266;
}

.diff-field {
  margin-bottom: 8px;
}

.diff-comparison {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.diff-item {
  padding: 8px 12px;
  background-color: #F5F7FA;
  border-radius: 4px;
}

.diff-label {
  font-weight: 500;
  color: #909399;
}

.diff-value {
  color: #303133;
}

.similarities-list {
  max-height: 300px;
  overflow-y: auto;
}

.similarity-item {
  border: 1px solid #E4E7ED;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 12px;
  background-color: #F0F9FF;
}

.similarity-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.similarity-category {
  font-weight: 500;
  color: #303133;
}

.similarity-score {
  color: #67C23A;
  font-weight: 600;
}

.similarity-content {
  color: #606266;
}

.actions-section {
  display: flex;
  gap: 12px;
  justify-content: center;
  padding: 20px;
}
</style>