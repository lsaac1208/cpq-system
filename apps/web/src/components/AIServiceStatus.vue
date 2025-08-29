<template>
  <div class="ai-service-status">
    <!-- 主状态栏 -->
    <div class="status-bar" :class="`status-${serviceStatusColor}`">
      <div class="status-content">
        <div class="status-icon">
          <el-icon class="status-indicator" :class="{ 'pulse': isAnalyzing }">
            <Connection v-if="serviceStatusColor === 'success'" />
            <Loading v-else-if="serviceStatusColor === 'info'" />
            <Warning v-else-if="serviceStatusColor === 'warning'" />
            <Close v-else />
          </el-icon>
        </div>
        
        <div class="status-text">
          <span class="status-label">AI分析服务</span>
          <span class="status-value">{{ serviceStatusText }}</span>
        </div>
        
        <div v-if="isServiceAvailable" class="status-metrics">
          <el-tooltip content="队列使用率" placement="top">
            <div class="metric">
              <el-icon><Menu /></el-icon>
              <span>{{ queueUtilization }}%</span>
            </div>
          </el-tooltip>
          
          <el-tooltip content="处理器使用率" placement="top">
            <div class="metric">
              <el-icon><Monitor /></el-icon>
              <span>{{ processingUtilization }}%</span>
            </div>
          </el-tooltip>
          
          <el-tooltip v-if="networkLatency < 9999" :content="`网络延迟: ${networkLatency}ms`" placement="top">
            <div class="metric" :class="{ 'metric-warning': networkLatency > 500 }">
              <el-icon><Connection /></el-icon>
              <span>{{ networkLatency }}ms</span>
            </div>
          </el-tooltip>
        </div>
        
        <div class="status-actions">
          <el-button
            v-if="!isNetworkOnline"
            type="warning"
            size="small"
            icon="Refresh"
            @click="checkConnection"
            :loading="checkingConnection"
          >
            重连
          </el-button>
          
          <el-popover
            placement="bottom-end"
            title="服务详情"
            width="320"
            trigger="click"
          >
            <template #reference>
              <el-button
                type="primary"
                size="small"
                icon="InfoFilled"
                circle
                :disabled="!isServiceAvailable"
              />
            </template>
            
            <!-- 详细状态面板 -->
            <div class="status-details">
              <div class="detail-section">
                <h4>服务状态</h4>
                <div class="detail-grid">
                  <div class="detail-item">
                    <span class="detail-label">状态:</span>
                    <el-tag :type="serviceStatusColor" size="small">
                      {{ serviceStatusText }}
                    </el-tag>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">队列长度:</span>
                    <span>{{ serviceStatus.queue_size }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">处理中:</span>
                    <span>{{ serviceStatus.processing_count }}/{{ serviceStatus.max_concurrent }}</span>
                  </div>
                  <div v-if="serviceStatus.estimated_wait_time" class="detail-item">
                    <span class="detail-label">预计等待:</span>
                    <span>{{ formatTime(serviceStatus.estimated_wait_time) }}</span>
                  </div>
                </div>
              </div>
              
              <div v-if="serviceStatus.recommendations?.length" class="detail-section">
                <h4>建议</h4>
                <ul class="recommendation-list">
                  <li v-for="rec in serviceStatus.recommendations" :key="rec">
                    {{ rec }}
                  </li>
                </ul>
              </div>
              
              <div class="detail-section">
                <h4>网络状态</h4>
                <div class="detail-grid">
                  <div class="detail-item">
                    <span class="detail-label">连接:</span>
                    <el-tag :type="isNetworkOnline ? 'success' : 'danger'" size="small">
                      {{ isNetworkOnline ? '正常' : '断开' }}
                    </el-tag>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">延迟:</span>
                    <span>{{ networkLatency < 9999 ? `${networkLatency}ms` : '无法测量' }}</span>
                  </div>
                </div>
              </div>
              
              <div class="detail-actions">
                <el-button size="small" @click="manualRefresh" :loading="refreshing">
                  <el-icon><Refresh /></el-icon>
                  刷新状态
                </el-button>
              </div>
            </div>
          </el-popover>
        </div>
      </div>
    </div>
    
    <!-- 分析进度条 (当正在分析时显示) -->
    <div v-if="isAnalyzing" class="analysis-progress-bar">
      <div class="progress-header">
        <span class="progress-title">正在分析文档...</span>
        <span class="progress-time">
          {{ remainingTime > 0 ? `剩余约 ${formatTime(remainingTime)}` : '即将完成' }}
        </span>
      </div>
      
      <el-progress
        :percentage="progressPercentage"
        :show-text="false"
        :stroke-width="6"
        color="#409EFF"
        class="progress-bar"
      />
      
      <div class="progress-footer">
        <span class="confidence-indicator">
          <el-icon><TrendCharts /></el-icon>
          预估准确度: {{ analysisStatus.confidence }}%
        </span>
      </div>
    </div>
    
    <!-- 离线提示 -->
    <div v-if="!isNetworkOnline" class="offline-banner">
      <el-icon><Close /></el-icon>
      <span>网络连接已断开，请检查网络设置</span>
      <el-button type="text" @click="checkConnection">重试连接</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { 
  Connection, Loading, Warning, Close, Menu, 
  Monitor, InfoFilled, Refresh, TrendCharts 
} from '@element-plus/icons-vue'
import { useAIAnalysisStatus } from '@/composables/useAIAnalysisStatus'
import { showMessage } from '@/utils/message'

const {
  serviceStatus,
  analysisStatus,
  networkStatus,
  isServiceHealthy,
  isServiceAvailable,
  queueUtilization,
  processingUtilization,
  serviceStatusText,
  serviceStatusColor,
  checkServiceStatus,
  formatTime
} = useAIAnalysisStatus()

// 本地状态
const refreshing = ref(false)
const checkingConnection = ref(false)

// 计算属性
const isAnalyzing = computed(() => analysisStatus.value.isAnalyzing)
const remainingTime = computed(() => analysisStatus.value.remainingTime)
const networkLatency = computed(() => networkStatus.value.latency)
const isNetworkOnline = computed(() => networkStatus.value.isOnline)

const progressPercentage = computed(() => {
  if (!isAnalyzing.value) return 0
  
  const { estimatedTime, actualStartTime } = analysisStatus.value
  if (!actualStartTime) return 0
  
  const elapsed = (Date.now() - actualStartTime) / 1000
  const progress = Math.min(95, (elapsed / estimatedTime) * 100)
  
  return Math.round(progress)
})

// 方法
const manualRefresh = async () => {
  refreshing.value = true
  try {
    await checkServiceStatus()
    showMessage.success('状态已更新')
  } catch (error) {
    showMessage.error('刷新失败')
  } finally {
    refreshing.value = false
  }
}

const checkConnection = async () => {
  checkingConnection.value = true
  try {
    // 简单的网络连接测试
    await fetch('/api/v1/system/health', { 
      method: 'HEAD',
      cache: 'no-cache'
    })
    showMessage.success('网络连接正常')
  } catch (error) {
    showMessage.error('网络连接失败')
  } finally {
    checkingConnection.value = false
  }
}
</script>

<style scoped>
.ai-service-status {
  width: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
}

.status-bar {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid transparent;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
}

.status-bar.status-success {
  border-color: #10b981;
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.1);
}

.status-bar.status-warning {
  border-color: #f59e0b;
  background: linear-gradient(135deg, #fefce8 0%, #fef3c7 100%);
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.1);
}

.status-bar.status-danger {
  border-color: #ef4444;
  background: linear-gradient(135deg, #fef2f2 0%, #fecaca 100%);
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.1);
}

.status-bar.status-info {
  border-color: #3b82f6;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
}

.status-content {
  display: flex;
  align-items: center;
  width: 100%;
  gap: 12px;
}

.status-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-indicator {
  font-size: 20px;
  transition: all 0.3s ease;
}

.status-indicator.pulse {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.1);
  }
}

.status-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.status-label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

.status-value {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.status-metrics {
  display: flex;
  gap: 16px;
  margin-left: auto;
  margin-right: 12px;
}

.metric {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #6b7280;
  padding: 4px 8px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 6px;
  transition: all 0.3s ease;
}

.metric.metric-warning {
  color: #d97706;
  background: rgba(251, 191, 36, 0.1);
}

.metric:hover {
  background: rgba(255, 255, 255, 0.8);
  transform: translateY(-1px);
}

.status-actions {
  display: flex;
  gap: 8px;
}

.analysis-progress-bar {
  margin-top: 16px;
  padding: 16px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-radius: 8px;
  border: 1px solid #0ea5e9;
  animation: slideInDown 0.3s ease-out;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.progress-title {
  font-size: 14px;
  font-weight: 600;
  color: #0c4a6e;
}

.progress-time {
  font-size: 12px;
  color: #0369a1;
  font-weight: 500;
}

.progress-bar {
  margin: 8px 0;
}

.progress-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

.confidence-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #0369a1;
  background: rgba(255, 255, 255, 0.6);
  padding: 2px 8px;
  border-radius: 4px;
}

.offline-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  margin-top: 16px;
  background: linear-gradient(135deg, #fef3c7 0%, #fed7aa 100%);
  border: 1px solid #f59e0b;
  border-radius: 8px;
  color: #92400e;
  font-size: 14px;
  animation: slideInDown 0.3s ease-out;
}

.status-details {
  max-height: 400px;
  overflow-y: auto;
}

.detail-section {
  margin-bottom: 16px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-section h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px;
  background: #f9fafb;
  border-radius: 4px;
  font-size: 13px;
}

.detail-label {
  color: #6b7280;
  font-weight: 500;
}

.recommendation-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.recommendation-list li {
  padding: 8px 12px;
  margin: 4px 0;
  background: #f0f9ff;
  border-left: 3px solid #0ea5e9;
  border-radius: 0 4px 4px 0;
  font-size: 13px;
  color: #0c4a6e;
  line-height: 1.4;
}

.detail-actions {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: center;
}

/* 响应式样式 */
@media (max-width: 768px) {
  .status-content {
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .status-metrics {
    order: 1;
    width: 100%;
    margin: 8px 0 0 0;
    justify-content: center;
  }
  
  .status-actions {
    order: 2;
  }
  
  .progress-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .detail-grid {
    grid-template-columns: 1fr;
  }
}

/* 动画效果 */
@keyframes slideInDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.status-bar {
  animation: fadeInUp 0.5s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>