<template>
  <div class="system-status">
    <div class="status-header">
      <h3>系统状态</h3>
      <p>批量分析系统的实时运行状态和性能监控</p>
      <div class="refresh-info">
        <el-button :icon="Refresh" @click="refreshStatus" :loading="refreshing">
          刷新状态
        </el-button>
        <span class="last-update">最后更新: {{ lastUpdateTime }}</span>
      </div>
    </div>
    
    <!-- 系统总览 -->
    <div class="system-overview">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="status-card" :class="{ 'status-healthy': systemHealth.overall === 'healthy' }">
            <div class="status-indicator">
              <el-icon :class="getHealthIcon(systemHealth.overall)" :color="getHealthColor(systemHealth.overall)">
                <component :is="getHealthIcon(systemHealth.overall)" />
              </el-icon>
              <div class="status-text">
                <h4>系统状态</h4>
                <p>{{ getHealthText(systemHealth.overall) }}</p>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="metric-card">
            <el-statistic
              title="当前队列"
              :value="systemMetrics.queueLength"
              suffix="个任务"
              :prefix-icon="List"
            />
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="metric-card">
            <el-statistic
              title="并发处理"
              :value="systemMetrics.activeTasks"
              suffix="个任务"
              :prefix-icon="Cpu"
            />
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="metric-card">
            <el-statistic
              title="系统负载"
              :value="systemMetrics.cpuUsage"
              suffix="%"
              :prefix-icon="TrendCharts"
            />
          </el-card>
        </el-col>
      </el-row>
    </div>
    
    <!-- 详细状态 -->
    <div class="detailed-status">
      <el-row :gutter="20">
        <!-- 服务状态 -->
        <el-col :span="12">
          <el-card header="服务状态">
            <div class="service-list">
              <div
                v-for="service in services"
                :key="service.name"
                class="service-item"
              >
                <div class="service-info">
                  <el-icon :color="getServiceStatusColor(service.status)">
                    <component :is="getServiceStatusIcon(service.status)" />
                  </el-icon>
                  <div class="service-details">
                    <h5>{{ service.name }}</h5>
                    <p>{{ service.description }}</p>
                  </div>
                </div>
                <div class="service-metrics">
                  <el-tag :type="getServiceStatusType(service.status)" size="small">
                    {{ getServiceStatusText(service.status) }}
                  </el-tag>
                  <span class="response-time">{{ service.responseTime }}ms</span>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <!-- 资源使用情况 -->
        <el-col :span="12">
          <el-card header="资源使用情况">
            <div class="resource-metrics">
              <div class="resource-item">
                <div class="resource-label">
                  <el-icon><Monitor /></el-icon>
                  <span>CPU 使用率</span>
                </div>
                <div class="resource-progress">
                  <el-progress
                    :percentage="systemMetrics.cpuUsage"
                    :color="getProgressColor(systemMetrics.cpuUsage)"
                    :show-text="false"
                  />
                  <span class="progress-text">{{ systemMetrics.cpuUsage }}%</span>
                </div>
              </div>
              
              <div class="resource-item">
                <div class="resource-label">
                  <el-icon><Monitor /></el-icon>
                  <span>内存使用率</span>
                </div>
                <div class="resource-progress">
                  <el-progress
                    :percentage="systemMetrics.memoryUsage"
                    :color="getProgressColor(systemMetrics.memoryUsage)"
                    :show-text="false"
                  />
                  <span class="progress-text">{{ systemMetrics.memoryUsage }}%</span>
                </div>
              </div>
              
              <div class="resource-item">
                <div class="resource-label">
                  <el-icon><FolderOpened /></el-icon>
                  <span>存储使用率</span>
                </div>
                <div class="resource-progress">
                  <el-progress
                    :percentage="systemMetrics.diskUsage"
                    :color="getProgressColor(systemMetrics.diskUsage)"
                    :show-text="false"
                  />
                  <span class="progress-text">{{ systemMetrics.diskUsage }}%</span>
                </div>
              </div>
              
              <div class="resource-item">
                <div class="resource-label">
                  <el-icon><Connection /></el-icon>
                  <span>网络负载</span>
                </div>
                <div class="resource-progress">
                  <el-progress
                    :percentage="systemMetrics.networkUsage"
                    :color="getProgressColor(systemMetrics.networkUsage)"
                    :show-text="false"
                  />
                  <span class="progress-text">{{ systemMetrics.networkUsage }}%</span>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
    
    <!-- 队列状态 -->
    <div class="queue-status">
      <el-card header="队列状态">
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="queue-metric">
              <h4>等待队列</h4>
              <div class="metric-value">{{ queueStats.pending }}</div>
              <div class="metric-label">个任务</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="queue-metric">
              <h4>处理中</h4>
              <div class="metric-value">{{ queueStats.processing }}</div>
              <div class="metric-label">个任务</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="queue-metric">
              <h4>平均等待时间</h4>
              <div class="metric-value">{{ queueStats.avgWaitTime }}</div>
              <div class="metric-label">分钟</div>
            </div>
          </el-col>
        </el-row>
        
        <div class="queue-visualization" v-if="queueItems.length > 0">
          <h5>队列详情</h5>
          <div class="queue-items">
            <div
              v-for="item in queueItems.slice(0, 10)"
              :key="item.jobId"
              class="queue-item"
              :class="`priority-${item.priority}`"
            >
              <div class="item-info">
                <span class="job-id">#{{ item.jobId }}</span>
                <span class="job-name">{{ item.name }}</span>
              </div>
              <div class="item-meta">
                <el-tag :type="getPriorityType(item.priority)" size="small">
                  {{ getPriorityText(item.priority) }}
                </el-tag>
                <span class="wait-time">等待 {{ item.waitTime }}分钟</span>
              </div>
            </div>
          </div>
          <div v-if="queueItems.length > 10" class="more-items">
            还有 {{ queueItems.length - 10 }} 个任务...
          </div>
        </div>
      </el-card>
    </div>
    
    <!-- 系统日志 -->
    <div class="system-logs">
      <el-card header="系统日志">
        <div class="log-filters">
          <el-select v-model="logLevel" placeholder="日志级别" @change="filterLogs">
            <el-option label="全部" value="" />
            <el-option label="错误" value="error" />
            <el-option label="警告" value="warning" />
            <el-option label="信息" value="info" />
          </el-select>
          <el-button :icon="Refresh" @click="loadLogs">刷新日志</el-button>
        </div>
        
        <div class="log-list">
          <div
            v-for="log in filteredLogs"
            :key="log.id"
            class="log-item"
            :class="`log-${log.level}`"
          >
            <div class="log-time">{{ formatTime(log.timestamp) }}</div>
            <div class="log-level">
              <el-tag :type="getLogLevelType(log.level)" size="small">
                {{ log.level.toUpperCase() }}
              </el-tag>
            </div>
            <div class="log-message">{{ log.message }}</div>
          </div>
        </div>
        
        <div v-if="filteredLogs.length === 0" class="no-logs">
          <el-empty description="暂无日志记录" />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
// ElMessage removed
import { showMessage } from '@/utils/message'
import {
  Refresh,
  TrendCharts,
  Monitor,
  FolderOpened,
  Connection,
  CircleCheck,
  Warning} from '@element-plus/icons-vue'
import { getSystemStatus } from '@/api/batch-analysis'

// 响应式数据
const refreshing = ref(false)
const lastUpdateTime = ref('')
const logLevel = ref('')

// 系统健康状态
const systemHealth = reactive({
  overall: 'healthy' as 'healthy' | 'warning' | 'error'
})

// 系统指标
const systemMetrics = reactive({
  queueLength: 0,
  activeTasks: 0,
  cpuUsage: 0,
  memoryUsage: 0,
  diskUsage: 0,
  networkUsage: 0
})

// 服务状态
const services = ref([
  {
    name: '文档处理服务',
    description: '负责文档解析和预处理',
    status: 'running',
    responseTime: 45
  },
  {
    name: 'AI分析引擎',
    description: '执行智能分析任务',
    status: 'running',
    responseTime: 120
  },
  {
    name: '队列管理器',
    description: '管理任务队列和调度',
    status: 'running',
    responseTime: 15
  },
  {
    name: '结果存储服务',
    description: '存储和管理分析结果',
    status: 'running',
    responseTime: 30
  }
])

// 队列统计
const queueStats = reactive({
  pending: 0,
  processing: 0,
  avgWaitTime: 0
})

// 队列详情
const queueItems = ref([])

// 系统日志
const logs = ref([])
const filteredLogs = ref([])

// 自动刷新定时器
let refreshTimer: number | null = null

// 获取健康状态图标
const getHealthIcon = (health: string) => {
  const iconMap = {
    healthy: 'CircleCheck',
    warning: 'Warning',
    error: 'CircleClose'
  }
  return iconMap[health] || 'CircleCheck'
}

// 获取健康状态颜色
const getHealthColor = (health: string) => {
  const colorMap = {
    healthy: '#67c23a',
    warning: '#e6a23c',
    error: '#f56c6c'
  }
  return colorMap[health] || '#67c23a'
}

// 获取健康状态文本
const getHealthText = (health: string) => {
  const textMap = {
    healthy: '运行正常',
    warning: '存在警告',
    error: '系统异常'
  }
  return textMap[health] || '运行正常'
}

// 获取服务状态图标
const getServiceStatusIcon = (status: string) => {
  const iconMap = {
    running: 'CircleCheck',
    warning: 'Warning',
    error: 'CircleClose',
    stopped: 'CircleClose'
  }
  return iconMap[status] || 'CircleCheck'
}

// 获取服务状态颜色
const getServiceStatusColor = (status: string) => {
  const colorMap = {
    running: '#67c23a',
    warning: '#e6a23c',
    error: '#f56c6c',
    stopped: '#909399'
  }
  return colorMap[status] || '#67c23a'
}

// 获取服务状态类型
const getServiceStatusType = (status: string) => {
  const typeMap = {
    running: 'success',
    warning: 'warning',
    error: 'danger',
    stopped: 'info'
  }
  return typeMap[status] || 'success'
}

// 获取服务状态文本
const getServiceStatusText = (status: string) => {
  const textMap = {
    running: '运行中',
    warning: '警告',
    error: '错误',
    stopped: '已停止'
  }
  return textMap[status] || '运行中'
}

// 获取进度条颜色
const getProgressColor = (percentage: number) => {
  if (percentage < 60) return '#67c23a'
  if (percentage < 80) return '#e6a23c'
  return '#f56c6c'
}

// 获取优先级类型
const getPriorityType = (priority: string) => {
  const typeMap = {
    high: 'danger',
    medium: 'warning',
    low: 'info'
  }
  return typeMap[priority] || 'info'
}

// 获取优先级文本
const getPriorityText = (priority: string) => {
  const textMap = {
    high: '高优先级',
    medium: '中优先级',
    low: '低优先级'
  }
  return textMap[priority] || '低优先级'
}

// 获取日志级别类型
const getLogLevelType = (level: string) => {
  const typeMap = {
    error: 'danger',
    warning: 'warning',
    info: 'info'
  }
  return typeMap[level] || 'info'
}

// 时间格式化
const formatTime = (timestamp: string | number) => {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN')
}

// 刷新系统状态
const refreshStatus = async () => {
  refreshing.value = true
  
  try {
    const response = await getSystemStatus()
    
    console.log('🔍 SystemStatus API 响应:', response)
    
    if (response && response.success && response.status) {
      // 映射后端数据结构到前端期望的结构
      const statusData = response.status
      
      // 更新健康状态
      systemHealth.overall = statusData.status === 'healthy' ? 'healthy' : 
                           statusData.status === 'busy' ? 'warning' : 'error'
      
      // 更新系统指标
      if (statusData.resource_usage) {
        systemMetrics.cpuUsage = statusData.resource_usage.cpu_usage || 0
        systemMetrics.memoryUsage = statusData.resource_usage.memory_usage || 0
        systemMetrics.diskUsage = statusData.resource_usage.disk_usage || 0
        systemMetrics.networkUsage = 0 // 默认值
      }
      
      systemMetrics.queueLength = statusData.queue_length || 0
      systemMetrics.activeTasks = statusData.active_jobs || 0
      
      // 更新队列统计
      queueStats.pending = statusData.queue_length || 0
      queueStats.processing = statusData.active_jobs || 0
      queueStats.avgWaitTime = statusData.performance?.average_file_time || 0
      
      // 模拟服务状态数据
      services.value = [
        {
          name: '批量分析服务',
          description: '文档批量分析处理服务',
          status: statusData.status === 'healthy' ? 'running' : 'warning',
          responseTime: Math.round(Math.random() * 50 + 10)
        },
        {
          name: 'AI分析引擎',
          description: '智能文档分析引擎',
          status: 'running',
          responseTime: Math.round(Math.random() * 100 + 50)
        },
        {
          name: '文件处理器',
          description: '文档上传和预处理服务',
          status: statusData.processing_capacity?.active_workers > 0 ? 'running' : 'stopped',
          responseTime: Math.round(Math.random() * 30 + 20)
        }
      ]
      
      // 模拟队列项目
      queueItems.value = Array.from({ length: Math.min(statusData.queue_length || 0, 5) }, (_, i) => ({
        jobId: 1000 + i,
        name: `批量分析任务 #${1000 + i}`,
        priority: ['high', 'medium', 'low'][Math.floor(Math.random() * 3)] as 'high' | 'medium' | 'low',
        waitTime: Math.round(Math.random() * 300 + 60)
      }))
      
      lastUpdateTime.value = formatTime(Date.now())
      
    } else {
      // 如果API响应失败或格式不正确，显示友好错误信息
      const errorMessage = response?.error || '获取系统状态数据格式错误'
      console.warn('❌ 系统状态获取失败:', errorMessage)
      showMessage.error(errorMessage)
    }
  } catch (error: any) {
    console.error('💥 Refresh status error:', error)
    
    let message = '获取系统状态失败'
    if (error?.response?.status === 404) {
      message = '系统状态API端点不存在'
    } else if (error?.response?.status === 500) {
      message = '服务器内部错误'
    } else if (error?.message) {
      message = error.message
    }
    
    showMessage.error(message)
  } finally {
    refreshing.value = false
  }
}

// 加载系统日志
const loadLogs = async () => {
  try {
    // 模拟日志数据
    const mockLogs = [
      {
        id: 1,
        timestamp: Date.now() - 300000,
        level: 'info',
        message: '批量分析任务 #1001 已完成'
      },
      {
        id: 2,
        timestamp: Date.now() - 600000,
        level: 'warning',
        message: '文档处理服务响应时间较长'
      },
      {
        id: 3,
        timestamp: Date.now() - 900000,
        level: 'error',
        message: '任务 #1000 处理失败：文件格式不支持'
      }
    ]
    
    logs.value = mockLogs
    filterLogs()
    
  } catch (error: any) {
    console.error('Load logs error:', error)
    showMessage.error('加载系统日志失败')
  }
}

// 过滤日志
const filterLogs = () => {
  if (logLevel.value) {
    filteredLogs.value = logs.value.filter(log => log.level === logLevel.value)
  } else {
    filteredLogs.value = [...logs.value]
  }
}

// 开始自动刷新
const startAutoRefresh = () => {
  refreshTimer = window.setInterval(() => {
    refreshStatus()
  }, 30000) // 每30秒刷新一次
}

// 停止自动刷新
const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

onMounted(() => {
  refreshStatus()
  loadLogs()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.system-status {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
}

.status-header h3 {
  margin: 0;
  color: #303133;
  font-size: 20px;
  font-weight: 600;
}

.status-header p {
  margin: 5px 0 0 0;
  color: #909399;
  font-size: 14px;
}

.refresh-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.last-update {
  color: #909399;
  font-size: 12px;
}

.system-overview {
  margin-bottom: 30px;
}

.status-card {
  border: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0.1);
}

.status-card.status-healthy {
  border-left: 4px solid #67c23a;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 15px;
}

.status-text h4 {
  margin: 0 0 5px 0;
  color: #303133;
  font-size: 16px;
}

.status-text p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.metric-card {
  border: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0.1);
  text-align: center;
}

.detailed-status {
  margin-bottom: 30px;
}

.service-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.service-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: #f9f9f9;
  border-radius: 6px;
}

.service-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.service-details h5 {
  margin: 0 0 3px 0;
  color: #303133;
  font-size: 14px;
  font-weight: 500;
}

.service-details p {
  margin: 0;
  color: #909399;
  font-size: 12px;
}

.service-metrics {
  display: flex;
  align-items: center;
  gap: 10px;
}

.response-time {
  color: #606266;
  font-size: 12px;
}

.resource-metrics {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.resource-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.resource-label {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
  font-size: 14px;
  font-weight: 500;
  width: 120px;
}

.resource-progress {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.progress-text {
  color: #606266;
  font-size: 12px;
  font-weight: 500;
  width: 40px;
  text-align: right;
}

.queue-status {
  margin-bottom: 30px;
}

.queue-metric {
  text-align: center;
  padding: 15px;
  background: #f9f9f9;
  border-radius: 6px;
}

.queue-metric h4 {
  margin: 0 0 10px 0;
  color: #606266;
  font-size: 14px;
  font-weight: 500;
}

.metric-value {
  color: #303133;
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 5px;
}

.metric-label {
  color: #909399;
  font-size: 12px;
}

.queue-visualization {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.queue-visualization h5 {
  margin: 0 0 15px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 500;
}

.queue-items {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.queue-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  background: #f5f7fa;
  border-radius: 4px;
  border-left: 3px solid #dcdfe6;
}

.queue-item.priority-high {
  border-left-color: #f56c6c;
}

.queue-item.priority-medium {
  border-left-color: #e6a23c;
}

.queue-item.priority-low {
  border-left-color: #909399;
}

.item-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.job-id {
  color: #409eff;
  font-weight: 500;
  font-size: 12px;
}

.job-name {
  color: #303133;
  font-size: 14px;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.wait-time {
  color: #909399;
  font-size: 12px;
}

.more-items {
  text-align: center;
  color: #909399;
  font-size: 12px;
  margin-top: 10px;
}

.system-logs .log-filters {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.log-list {
  max-height: 400px;
  overflow-y: auto;
}

.log-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 10px;
  border-bottom: 1px solid #f5f7fa;
}

.log-item:last-child {
  border-bottom: none;
}

.log-time {
  color: #909399;
  font-size: 12px;
  width: 130px;
  flex-shrink: 0;
}

.log-level {
  width: 60px;
  flex-shrink: 0;
}

.log-message {
  color: #606266;
  font-size: 14px;
  flex: 1;
}

.no-logs {
  text-align: center;
  padding: 40px;
}

:deep(.el-card__header) {
  background: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
  font-weight: 600;
}

:deep(.el-progress-bar__outer) {
  background-color: #ebeef5;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .status-header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }
  
  .service-item {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  
  .resource-item {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  
  .resource-progress {
    width: 100%;
  }
  
  .queue-item {
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;
  }
  
  .log-filters {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
}
</style>