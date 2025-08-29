<template>
  <div class="optimization-metrics">
    <div class="metrics-header">
      <h3>优化效果统计</h3>
      <p>Prompt优化的整体效果分析和性能指标</p>
    </div>

    <!-- 总体统计 -->
    <div class="metrics-summary">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-item">
              <el-icon class="metric-icon"><TrendCharts /></el-icon>
              <div class="metric-content">
                <div class="metric-value">{{ metrics.totalOptimizations }}</div>
                <div class="metric-label">总优化次数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-item">
              <el-icon class="metric-icon success"><CircleCheck /></el-icon>
              <div class="metric-content">
                <div class="metric-value">{{ metrics.avgImprovement }}%</div>
                <div class="metric-label">平均改进度</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-item">
              <el-icon class="metric-icon warning"><Clock /></el-icon>
              <div class="metric-content">
                <div class="metric-value">{{ metrics.avgOptimizationTime }}s</div>
                <div class="metric-label">平均优化时长</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-item">
              <el-icon class="metric-icon info"><Star /></el-icon>
              <div class="metric-content">
                <div class="metric-value">{{ metrics.successRate }}%</div>
                <div class="metric-label">优化成功率</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 图表区域 -->
    <div class="charts-section">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-card>
            <template #header>
              <h4>优化类型分布</h4>
            </template>
            <div class="chart-container">
              <div class="chart-placeholder">
                <el-icon><PieChart /></el-icon>
                <p>优化类型饼图</p>
                <div class="chart-data">
                  <div class="data-item">
                    <span class="data-dot" style="background-color: #409EFF;"></span>
                    <span>结构优化: 35%</span>
                  </div>
                  <div class="data-item">
                    <span class="data-dot" style="background-color: #67C23A;"></span>
                    <span>语义增强: 28%</span>
                  </div>
                  <div class="data-item">
                    <span class="data-dot" style="background-color: #E6A23C;"></span>
                    <span>上下文增强: 22%</span>
                  </div>
                  <div class="data-item">
                    <span class="data-dot" style="background-color: #F56C6C;"></span>
                    <span>性能优化: 15%</span>
                  </div>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card>
            <template #header>
              <h4>改进效果分布</h4>
            </template>
            <div class="chart-container">
              <div class="chart-placeholder">
                <el-icon><Histogram /></el-icon>
                <p>改进效果柱状图</p>
                <div class="bar-chart-data">
                  <div class="bar-item">
                    <div class="bar-label">优秀(80-100%)</div>
                    <div class="bar-container">
                      <div class="bar-fill" style="width: 65%; background-color: #67C23A;"></div>
                      <span class="bar-value">65%</span>
                    </div>
                  </div>
                  <div class="bar-item">
                    <div class="bar-label">良好(60-79%)</div>
                    <div class="bar-container">
                      <div class="bar-fill" style="width: 25%; background-color: #409EFF;"></div>
                      <span class="bar-value">25%</span>
                    </div>
                  </div>
                  <div class="bar-item">
                    <div class="bar-label">一般(40-59%)</div>
                    <div class="bar-container">
                      <div class="bar-fill" style="width: 8%; background-color: #E6A23C;"></div>
                      <span class="bar-value">8%</span>
                    </div>
                  </div>
                  <div class="bar-item">
                    <div class="bar-label">较差(<40%)</div>
                    <div class="bar-container">
                      <div class="bar-fill" style="width: 2%; background-color: #F56C6C;"></div>
                      <span class="bar-value">2%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="24">
          <el-card>
            <template #header>
              <h4>优化趋势</h4>
            </template>
            <div class="chart-container">
              <div class="chart-placeholder">
                <el-icon><TrendCharts /></el-icon>
                <p>优化次数和成功率趋势图</p>
                <div class="trend-data">
                  <div class="trend-line">
                    <span>优化次数呈稳定上升趋势，近30天平均每天4.2次优化</span>
                  </div>
                  <div class="trend-line">
                    <span>优化成功率保持在85%以上，整体质量稳定</span>
                  </div>
                  <div class="trend-line">
                    <span>用户满意度评分平均4.3/5.0，持续改善中</span>
                  </div>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 详细统计表格 -->
    <div class="detailed-stats">
      <el-card>
        <template #header>
          <div class="stats-header">
            <h4>分类统计详情</h4>
            <el-button size="small" @click="exportStats">导出数据</el-button>
          </div>
        </template>
        <el-table :data="detailedStats">
          <el-table-column prop="category" label="优化类型" width="150">
            <template #default="scope">
              <el-tag :type="getCategoryColor(scope.row.category)">
                {{ scope.row.category }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="count" label="次数" width="100" />
          <el-table-column prop="avgImprovement" label="平均改进度" width="120">
            <template #default="scope">
              <span class="improvement-score">{{ scope.row.avgImprovement }}%</span>
            </template>
          </el-table-column>
          <el-table-column prop="avgTime" label="平均时长(s)" width="120" />
          <el-table-column prop="successRate" label="成功率" width="100">
            <template #default="scope">
              <el-progress
                :percentage="scope.row.successRate"
                :stroke-width="8"
                :color="getProgressColor(scope.row.successRate)"
              />
            </template>
          </el-table-column>
          <el-table-column prop="userSatisfaction" label="用户满意度" width="120">
            <template #default="scope">
              <el-rate
                v-model="scope.row.userSatisfaction"
                :max="5"
                disabled
                size="small"
                show-score
                text-color="#ff9900"
              />
            </template>
          </el-table-column>
          <el-table-column prop="lastUsed" label="最近使用" width="180" />
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
// ElMessage removed
import { showMessage } from '@/utils/message'
import {
  TrendCharts,
  PieChart,
  Histogram,
  CircleCheck,
  Clock,
  Star
} from '@element-plus/icons-vue'

// 响应式数据
const metrics = ref({
  totalOptimizations: 456,
  avgImprovement: 73.8,
  avgOptimizationTime: 28.5,
  successRate: 87.2
})

const detailedStats = ref([
  {
    category: '结构优化',
    count: 159,
    avgImprovement: 78.5,
    avgTime: 25.2,
    successRate: 89,
    userSatisfaction: 4.2,
    lastUsed: '2024-08-16 16:30:25'
  },
  {
    category: '语义增强',
    count: 128,
    avgImprovement: 82.3,
    avgTime: 32.1,
    successRate: 91,
    userSatisfaction: 4.5,
    lastUsed: '2024-08-16 15:45:12'
  },
  {
    category: '上下文增强',
    count: 100,
    avgImprovement: 67.1,
    avgTime: 28.8,
    successRate: 83,
    userSatisfaction: 4.0,
    lastUsed: '2024-08-16 14:20:08'
  },
  {
    category: '性能优化',
    count: 69,
    avgImprovement: 65.4,
    avgTime: 35.3,
    successRate: 85,
    userSatisfaction: 4.1,
    lastUsed: '2024-08-16 13:15:45'
  }
])

// 方法
const getCategoryColor = (category: string) => {
  const categoryColors: Record<string, string> = {
    '结构优化': 'primary',
    '语义增强': 'success',
    '上下文增强': 'warning',
    '性能优化': 'info'
  }
  return categoryColors[category] || 'info'
}

const getProgressColor = (percentage: number) => {
  if (percentage >= 85) return '#67C23A'
  if (percentage >= 70) return '#409EFF'
  if (percentage >= 50) return '#E6A23C'
  return '#F56C6C'
}

const exportStats = () => {
  showMessage.success('统计数据导出功能开发中...')
}

onMounted(() => {
  // 初始化时可以加载真实数据
})
</script>

<style scoped>
.optimization-metrics {
  padding: 20px;
}

.metrics-header {
  margin-bottom: 24px;
}

.metrics-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.metrics-header p {
  color: #909399;
  margin: 0;
}

.metrics-summary {
  margin-bottom: 24px;
}

.metric-card {
  text-align: center;
  transition: transform 0.2s;
}

.metric-card:hover {
  transform: translateY(-2px);
}

.metric-item {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  gap: 16px;
}

.metric-icon {
  font-size: 32px;
  color: #409EFF;
}

.metric-icon.success {
  color: #67C23A;
}

.metric-icon.warning {
  color: #E6A23C;
}

.metric-icon.info {
  color: #909399;
}

.metric-content {
  text-align: left;
}

.metric-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.metric-label {
  color: #909399;
  font-size: 14px;
}

.charts-section {
  margin-bottom: 24px;
}

.chart-container {
  padding: 20px;
}

.chart-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  color: #C0C4CC;
}

.chart-placeholder .el-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.chart-data {
  margin-top: 20px;
  width: 100%;
}

.data-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  gap: 8px;
}

.data-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.bar-chart-data {
  margin-top: 20px;
  width: 100%;
}

.bar-item {
  margin-bottom: 12px;
}

.bar-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 4px;
}

.bar-container {
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: #F5F7FA;
  border-radius: 4px;
  height: 20px;
  position: relative;
}

.bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.bar-value {
  position: absolute;
  right: 8px;
  font-size: 12px;
  color: #606266;
}

.trend-data {
  margin-top: 20px;
  text-align: left;
}

.trend-line {
  padding: 8px 0;
  color: #606266;
  border-left: 3px solid #409EFF;
  padding-left: 12px;
  margin-bottom: 8px;
}

.detailed-stats {
  margin-top: 24px;
}

.stats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-header h4 {
  margin: 0;
}

.improvement-score {
  color: #67C23A;
  font-weight: 500;
}
</style>