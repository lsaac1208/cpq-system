<template>
  <div class="comparison-progress">
    <div class="progress-header">
      <h3>对比进度</h3>
      <p>实时监控文档对比分析的进度</p>
    </div>

    <!-- 当前任务 -->
    <div v-if="currentTask" class="current-task">
      <el-card>
        <template #header>
          <div class="task-header">
            <span>当前对比任务</span>
            <el-tag :type="getStatusType(currentTask.status)">
              {{ currentTask.status }}
            </el-tag>
          </div>
        </template>
        
        <div class="task-info">
          <div class="task-name">{{ currentTask.name }}</div>
          <div class="task-documents">
            <span>对比文档：</span>
            <el-tag 
              v-for="doc in currentTask.documents" 
              :key="doc"
              size="small"
              style="margin-right: 8px;"
            >
              {{ doc }}
            </el-tag>
          </div>
        </div>

        <div class="progress-section">
          <div class="progress-info">
            <span>整体进度：{{ currentTask.progress }}%</span>
            <span>预计剩余时间：{{ currentTask.estimatedTime }}s</span>
          </div>
          <el-progress
            :percentage="currentTask.progress"
            :status="currentTask.progress === 100 ? 'success' : 'primary'"
            :stroke-width="12"
          />
        </div>

        <div class="steps-progress">
          <el-steps :active="currentTask.currentStep" align-center>
            <el-step 
              v-for="step in currentTask.steps" 
              :key="step.id"
              :title="step.title"
              :description="step.description"
              :status="step.status"
            />
          </el-steps>
        </div>

        <div class="task-actions">
          <el-button 
            v-if="currentTask.status === 'processing'"
            type="danger" 
            @click="cancelTask"
          >
            取消任务
          </el-button>
          <el-button 
            v-if="currentTask.status === 'completed'"
            type="primary" 
            @click="viewResults"
          >
            查看结果
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 无任务状态 -->
    <div v-else class="no-task">
      <el-empty description="当前没有正在进行的对比任务">
        <el-button type="primary" @click="startNewComparison">
          开始新对比
        </el-button>
      </el-empty>
    </div>

    <!-- 任务队列 -->
    <div v-if="taskQueue.length > 0" class="task-queue">
      <el-card>
        <template #header>
          <h4>等待队列</h4>
        </template>
        <div 
          v-for="task in taskQueue" 
          :key="task.id"
          class="queue-item"
        >
          <div class="queue-info">
            <span class="queue-name">{{ task.name }}</span>
            <span class="queue-time">预计开始时间：{{ task.estimatedStartTime }}</span>
          </div>
          <el-button size="small" text @click="removeFromQueue(task.id)">
            移除
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 实时日志 -->
    <div class="task-logs">
      <el-card>
        <template #header>
          <div class="logs-header">
            <h4>实时日志</h4>
            <el-button size="small" @click="clearLogs">清空日志</el-button>
          </div>
        </template>
        <div class="logs-container">
          <div 
            v-for="(log, index) in logs" 
            :key="index"
            class="log-item"
            :class="log.level"
          >
            <span class="log-time">{{ log.time }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessageBox } from 'element-plus'
import { showMessage } from '@/utils/message'

const emit = defineEmits(['view-results', 'start-comparison'])

// 响应式数据
const currentTask = ref({
  id: 1,
  name: 'A703与A704产品对比',
  documents: ['A703说明书.pdf', 'A704说明书.pdf'],
  status: 'processing',
  progress: 65,
  estimatedTime: 45,
  currentStep: 2,
  steps: [
    { id: 1, title: '文档解析', description: '解析上传的文档内容', status: 'finish' },
    { id: 2, title: '内容分析', description: '分析文档结构和内容', status: 'process' },
    { id: 3, title: '对比计算', description: '计算文档间的相似度', status: 'wait' },
    { id: 4, title: '生成报告', description: '生成详细对比报告', status: 'wait' }
  ]
})

const taskQueue = ref([
  {
    id: 2,
    name: '技术标准对比',
    estimatedStartTime: '14:35:20'
  },
  {
    id: 3,
    name: '产品规格对比',
    estimatedStartTime: '14:42:15'
  }
])

const logs = ref([
  { time: '14:28:15', level: 'info', message: '开始解析文档 A703说明书.pdf' },
  { time: '14:28:18', level: 'success', message: '文档解析完成，提取到 156 个段落' },
  { time: '14:28:22', level: 'info', message: '开始解析文档 A704说明书.pdf' },
  { time: '14:28:25', level: 'success', message: '文档解析完成，提取到 142 个段落' },
  { time: '14:28:28', level: 'info', message: '开始内容分析和特征提取' },
  { time: '14:29:05', level: 'warning', message: '检测到部分内容格式不规范，自动修正中...' },
  { time: '14:29:15', level: 'info', message: '正在计算语义相似度...' }
])

let progressTimer: NodeJS.Timeout | null = null

// 方法
const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    processing: 'warning',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info'
  }
  return statusMap[status] || 'info'
}

const cancelTask = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要取消当前对比任务吗？',
      '确认取消',
      {
        confirmButtonText: '取消任务',
        cancelButtonText: '继续任务',
        type: 'warning'
      }
    )
    
    if (currentTask.value) {
      currentTask.value.status = 'cancelled'
      addLog('warning', '用户取消了对比任务')
      showMessage.warning('任务已取消')
    }
  } catch {
    // 用户选择继续任务
  }
}

const viewResults = () => {
  emit('view-results', currentTask.value)
}

const startNewComparison = () => {
  emit('start-comparison')
}

const removeFromQueue = (taskId: number) => {
  const index = taskQueue.value.findIndex(task => task.id === taskId)
  if (index > -1) {
    taskQueue.value.splice(index, 1)
    showMessage.success('已从队列中移除')
  }
}

const clearLogs = () => {
  logs.value = []
}

const addLog = (level: string, message: string) => {
  const now = new Date()
  const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`
  logs.value.push({ time, level, message })
  
  // 保持日志数量在合理范围内
  if (logs.value.length > 50) {
    logs.value.shift()
  }
}

const simulateProgress = () => {
  if (currentTask.value && currentTask.value.status === 'processing') {
    if (currentTask.value.progress < 100) {
      currentTask.value.progress += Math.random() * 3
      currentTask.value.estimatedTime = Math.max(0, currentTask.value.estimatedTime - 2)
      
      // 模拟步骤进展
      if (currentTask.value.progress > 25 && currentTask.value.currentStep < 1) {
        currentTask.value.currentStep = 1
        currentTask.value.steps[1].status = 'process'
        addLog('info', '开始内容分析阶段')
      }
      if (currentTask.value.progress > 50 && currentTask.value.currentStep < 2) {
        currentTask.value.currentStep = 2
        currentTask.value.steps[1].status = 'finish'
        currentTask.value.steps[2].status = 'process'
        addLog('info', '开始对比计算阶段')
      }
      if (currentTask.value.progress > 80 && currentTask.value.currentStep < 3) {
        currentTask.value.currentStep = 3
        currentTask.value.steps[2].status = 'finish'
        currentTask.value.steps[3].status = 'process'
        addLog('info', '开始生成报告阶段')
      }
    } else {
      currentTask.value.progress = 100
      currentTask.value.status = 'completed'
      currentTask.value.estimatedTime = 0
      currentTask.value.currentStep = 4
      currentTask.value.steps[3].status = 'finish'
      addLog('success', '对比任务完成！相似度: 78.5%')
    }
  }
}

onMounted(() => {
  // 模拟进度更新
  progressTimer = setInterval(simulateProgress, 2000)
})

onUnmounted(() => {
  if (progressTimer) {
    clearInterval(progressTimer)
  }
})
</script>

<style scoped>
.comparison-progress {
  padding: 20px;
}

.progress-header {
  margin-bottom: 24px;
}

.progress-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.progress-header p {
  color: #909399;
  margin: 0;
}

.current-task {
  margin-bottom: 24px;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-info {
  margin-bottom: 20px;
}

.task-name {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
}

.task-documents {
  color: #606266;
}

.progress-section {
  margin-bottom: 20px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
}

.steps-progress {
  margin: 24px 0;
}

.task-actions {
  text-align: center;
}

.no-task {
  margin-bottom: 24px;
}

.task-queue {
  margin-bottom: 24px;
}

.queue-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #EBEEF5;
}

.queue-item:last-child {
  border-bottom: none;
}

.queue-info {
  display: flex;
  flex-direction: column;
}

.queue-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.queue-time {
  font-size: 12px;
  color: #909399;
}

.task-logs {
  margin-bottom: 24px;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logs-header h4 {
  margin: 0;
}

.logs-container {
  max-height: 300px;
  overflow-y: auto;
  background-color: #F5F7FA;
  padding: 12px;
  border-radius: 4px;
}

.log-item {
  padding: 4px 0;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.4;
}

.log-time {
  color: #909399;
  margin-right: 8px;
}

.log-item.info .log-message {
  color: #409EFF;
}

.log-item.success .log-message {
  color: #67C23A;
}

.log-item.warning .log-message {
  color: #E6A23C;
}

.log-item.error .log-message {
  color: #F56C6C;
}
</style>