<template>
  <div class="comparison-metrics">
    <div class="metrics-header">
      <h3>对比统计</h3>
      <p>文档对比分析的统计数据和趋势</p>
    </div>

    <!-- 总体统计 -->
    <div class="metrics-summary">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-item">
              <div class="metric-value">{{ metrics.totalComparisons }}</div>
              <div class="metric-label">总对比次数</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-item">
              <div class="metric-value">{{ metrics.avgSimilarity }}%</div>
              <div class="metric-label">平均相似度</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-item">
              <div class="metric-value">{{ metrics.avgProcessingTime }}s</div>
              <div class="metric-label">平均处理时间</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-item">
              <div class="metric-value">{{ metrics.successRate }}%</div>
              <div class="metric-label">成功率</div>
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
              <h4>相似度分布</h4>
            </template>
            <div class="chart-placeholder">
              <el-icon><TrendCharts /></el-icon>
              <p>相似度分布图表</p>
            </div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card>
            <template #header>
              <h4>对比类型分布</h4>
            </template>
            <div class="chart-placeholder">
              <el-icon><PieChart /></el-icon>
              <p>对比类型饼图</p>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="24">
          <el-card>
            <template #header>
              <h4>对比趋势</h4>
            </template>
            <div class="chart-placeholder">
              <el-icon><TrendCharts /></el-icon>
              <p>对比次数趋势图</p>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 详细统计表格 -->
    <div class="detailed-stats">
      <el-card>
        <template #header>
          <h4>详细统计</h4>
        </template>
        <el-table :data="detailedStats">
          <el-table-column prop="category" label="分类" width="150" />
          <el-table-column prop="count" label="次数" width="100" />
          <el-table-column prop="avgSimilarity" label="平均相似度" width="120" />
          <el-table-column prop="avgTime" label="平均时长(s)" width="120" />
          <el-table-column prop="successRate" label="成功率" width="100" />
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { TrendCharts, PieChart } from '@element-plus/icons-vue'

// 响应式数据
const metrics = ref({
  totalComparisons: 256,
  avgSimilarity: 73.2,
  avgProcessingTime: 18.5,
  successRate: 96.1
})

const detailedStats = ref([
  {
    category: '产品规格对比',
    count: 89,
    avgSimilarity: 78.5,
    avgTime: 15.2,
    successRate: 97.8
  },
  {
    category: '技术文档对比',
    count: 67,
    avgSimilarity: 71.3,
    avgTime: 22.1,
    successRate: 95.5
  },
  {
    category: '标准文件对比',
    count: 45,
    avgSimilarity: 84.2,
    avgTime: 12.8,
    successRate: 98.9
  },
  {
    category: '其他对比',
    count: 55,
    avgSimilarity: 65.1,
    avgTime: 25.3,
    successRate: 92.7
  }
])

onMounted(() => {
  // 初始化图表等
})
</script>

<style scoped>
.comparison-metrics {
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
}

.metric-item {
  padding: 20px;
}

.metric-value {
  font-size: 24px;
  font-weight: 600;
  color: #409EFF;
  margin-bottom: 8px;
}

.metric-label {
  color: #909399;
  font-size: 14px;
}

.charts-section {
  margin-bottom: 24px;
}

.chart-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #C0C4CC;
}

.chart-placeholder .el-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.detailed-stats {
  margin-top: 24px;
}
</style>