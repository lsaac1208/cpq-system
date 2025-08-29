<template>
  <div class="global-loading-manager">
    <!-- 全局加载遮罩 -->
    <el-dialog
      v-model="showGlobalLoading"
      :show-close="false"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      width="400px"
      align-center
      class="loading-dialog"
    >
      <div class="loading-content">
        <div class="loading-animation">
          <el-icon class="rotating" size="48">
            <Loading />
          </el-icon>
        </div>
        
        <div class="loading-text">
          <h3>{{ currentTask.title }}</h3>
          <p>{{ currentTask.description }}</p>
        </div>
        
        <div v-if="currentTask.showProgress" class="loading-progress">
          <el-progress 
            :percentage="currentTask.progress" 
            :status="currentTask.status"
            :stroke-width="8"
          />
          <div class="progress-details">
            <span class="progress-text">{{ currentTask.progressText }}</span>
            <span v-if="currentTask.estimatedTime > 0" class="estimated-time">
              预计剩余: {{ formatTime(currentTask.estimatedTime) }}
            </span>
          </div>
        </div>
        
        <div v-if="currentTask.allowCancel" class="loading-actions">
          <el-button 
            type="warning" 
            size="small"
            @click="cancelTask"
          >
            取消操作
          </el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 页面级加载遮罩 -->
    <el-loading
      v-if="showPageLoading"
      :text="pageLoadingText"
      background="rgba(0, 0, 0.8)"
      element-loading-background="rgba(0, 0, 0.8)"
      element-loading-text="加载中..."
      element-loading-spinner="el-icon-loading"
      element-loading-svg-view-box="-10, -10, 50, 50"
    />

    <!-- 操作反馈条 -->
    <transition name="slide-down">
      <div v-if="showFeedbackBar" class="feedback-bar" :class="feedbackType">
        <div class="feedback-content">
          <el-icon class="feedback-icon">
            <SuccessFilled v-if="feedbackType === 'success'" />
            <WarningFilled v-if="feedbackType === 'warning'" />
            <CircleCloseFilled v-if="feedbackType === 'error'" />
            <InfoFilled v-if="feedbackType === 'info'" />
          </el-icon>
          
          <div class="feedback-text">
            <span class="feedback-title">{{ feedbackTitle }}</span>
            <span v-if="feedbackMessage" class="feedback-message">{{ feedbackMessage }}</span>
          </div>
          
          <div class="feedback-actions">
            <el-button 
              v-if="feedbackAction"
              type="primary" 
              size="small"
              @click="executeFeedbackAction"
            >
              {{ feedbackAction.text }}
            </el-button>
            
            <el-button 
              link 
              size="small"
              @click="hideFeedbackBar"
            >
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </transition>

    <!-- 任务队列指示器 -->
    <transition name="slide-up">
      <div v-if="showTaskQueue && taskQueue.length > 0" class="task-queue-indicator">
        <div class="queue-header">
          <span class="queue-title">
            <el-icon><Menu /></el-icon>
            任务队列 ({{ taskQueue.length }})
          </span>
          <el-button 
            link 
            size="small"
            @click="toggleQueueDetails"
          >
            {{ showQueueDetails ? '收起' : '展开' }}
          </el-button>
        </div>
        
        <div v-if="showQueueDetails" class="queue-details">
          <div 
            v-for="(task, index) in taskQueue" 
            :key="task.id"
            class="queue-task"
            :class="{ active: index === 0 }"
          >
            <div class="task-info">
              <span class="task-title">{{ task.title }}</span>
              <span class="task-status">
                <el-tag 
                  :type="getTaskStatusType(task.status)" 
                  size="small"
                >
                  {{ getTaskStatusText(task.status) }}
                </el-tag>
              </span>
            </div>
            
            <div v-if="task.showProgress" class="task-progress">
              <el-progress 
                :percentage="task.progress" 
                :stroke-width="4"
                :show-text="false"
              />
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
// ElMessage removed
import { showMessage } from '@/utils/message'
import { 
  Loading, 
  SuccessFilled, 
  WarningFilled, 
  CircleCloseFilled, 
  InfoFilled, 
  Close} from '@element-plus/icons-vue'

// 任务状态类型
export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

// 反馈类型
export type FeedbackType = 'success' | 'warning' | 'error' | 'info'

// 任务接口
export interface LoadingTask {
  id: string
  title: string
  description: string
  status: TaskStatus
  progress: number
  progressText: string
  estimatedTime: number
  showProgress: boolean
  allowCancel: boolean
  onCancel?: () => void
}

// 反馈操作接口
export interface FeedbackAction {
  text: string
  handler: () => void
}

// 响应式数据
const showGlobalLoading = ref(false)
const showPageLoading = ref(false)
const pageLoadingText = ref('加载中...')

const showFeedbackBar = ref(false)
const feedbackType = ref<FeedbackType>('info')
const feedbackTitle = ref('')
const feedbackMessage = ref('')
const feedbackAction = ref<FeedbackAction | null>(null)

const showTaskQueue = ref(false)
const showQueueDetails = ref(false)
const taskQueue = ref<LoadingTask[]>([])

const currentTask = reactive<LoadingTask>({
  id: '',
  title: '处理中...',
  description: '正在执行操作，请稍候',
  status: 'pending',
  progress: 0,
  progressText: '',
  estimatedTime: 0,
  showProgress: false,
  allowCancel: false
})

// 自动隐藏定时器
let feedbackTimer: number | null = null
let taskUpdateTimer: number | null = null

// 计算属性
const hasActiveTasks = computed(() => {
  return taskQueue.value.some(task => 
    task.status === 'running' || task.status === 'pending'
  )
})

// 方法
const startGlobalLoading = (task: Partial<LoadingTask> = {}) => {
  Object.assign(currentTask, {
    id: Date.now().toString(),
    title: '处理中...',
    description: '正在执行操作，请稍候',
    status: 'running',
    progress: 0,
    progressText: '',
    estimatedTime: 0,
    showProgress: false,
    allowCancel: false,
    ...task
  })
  
  showGlobalLoading.value = true
}

const updateGlobalLoading = (updates: Partial<LoadingTask>) => {
  Object.assign(currentTask, updates)
}

const stopGlobalLoading = () => {
  showGlobalLoading.value = false
  Object.assign(currentTask, {
    status: 'completed',
    progress: 100
  })
}

const startPageLoading = (text = '加载中...') => {
  pageLoadingText.value = text
  showPageLoading.value = true
}

const stopPageLoading = () => {
  showPageLoading.value = false
}

const showFeedback = (
  type: FeedbackType,
  title: string,
  message = '',
  action?: FeedbackAction,
  duration = 5000
) => {
  feedbackType.value = type
  feedbackTitle.value = title
  feedbackMessage.value = message
  feedbackAction.value = action || null
  showFeedbackBar.value = true
  
  // 清除之前的定时器
  if (feedbackTimer) {
    clearTimeout(feedbackTimer)
  }
  
  // 设置自动隐藏
  if (duration > 0) {
    feedbackTimer = window.setTimeout(() => {
      hideFeedbackBar()
    }, duration)
  }
}

const hideFeedbackBar = () => {
  showFeedbackBar.value = false
  feedbackAction.value = null
  
  if (feedbackTimer) {
    clearTimeout(feedbackTimer)
    feedbackTimer = null
  }
}

const executeFeedbackAction = () => {
  if (feedbackAction.value) {
    feedbackAction.value.handler()
    hideFeedbackBar()
  }
}

const addTask = (task: Partial<LoadingTask>): string => {
  const newTask: LoadingTask = {
    id: Date.now().toString(),
    title: '新任务',
    description: '',
    status: 'pending',
    progress: 0,
    progressText: '',
    estimatedTime: 0,
    showProgress: false,
    allowCancel: false,
    ...task
  }
  
  taskQueue.value.push(newTask)
  showTaskQueue.value = true
  
  // 如果是第一个任务，开始处理
  if (taskQueue.value.length === 1) {
    processNextTask()
  }
  
  return newTask.id
}

const updateTask = (taskId: string, updates: Partial<LoadingTask>) => {
  const task = taskQueue.value.find(t => t.id === taskId)
  if (task) {
    Object.assign(task, updates)
    
    // 如果是当前任务，也更新全局状态
    if (taskQueue.value[0]?.id === taskId) {
      updateGlobalLoading(updates)
    }
  }
}

const removeTask = (taskId: string) => {
  const index = taskQueue.value.findIndex(t => t.id === taskId)
  if (index !== -1) {
    taskQueue.value.splice(index, 1)
    
    // 如果移除的是当前任务，处理下一个
    if (index === 0 && taskQueue.value.length > 0) {
      processNextTask()
    } else if (taskQueue.value.length === 0) {
      showTaskQueue.value = false
      stopGlobalLoading()
    }
  }
}

const processNextTask = () => {
  const nextTask = taskQueue.value[0]
  if (nextTask) {
    startGlobalLoading(nextTask)
    nextTask.status = 'running'
  }
}

const cancelTask = () => {
  if (currentTask.onCancel) {
    currentTask.onCancel()
  }
  
  currentTask.status = 'cancelled'
  
  // 移除当前任务
  if (taskQueue.value[0]) {
    removeTask(taskQueue.value[0].id)
  }
  
  showMessage.warning('操作已取消')
}

const toggleQueueDetails = () => {
  showQueueDetails.value = !showQueueDetails.value
}

const getTaskStatusType = (status: TaskStatus): string => {
  const typeMap: Record<TaskStatus, string> = {
    pending: 'info',
    running: 'primary',
    completed: 'success',
    failed: 'danger',
    cancelled: 'warning'
  }
  return typeMap[status]
}

const getTaskStatusText = (status: TaskStatus): string => {
  const textMap: Record<TaskStatus, string> = {
    pending: '等待中',
    running: '执行中',
    completed: '已完成',
    failed: '已失败',
    cancelled: '已取消'
  }
  return textMap[status]
}

const formatTime = (seconds: number): string => {
  if (seconds < 60) return `${seconds}秒`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}分${remainingSeconds}秒`
}

// 便捷方法
const showSuccess = (title: string, message = '', action?: FeedbackAction) => {
  showFeedback('success', title, message, action)
}

const showWarning = (title: string, message = '', action?: FeedbackAction) => {
  showFeedback('warning', title, message, action)
}

const showError = (title: string, message = '', action?: FeedbackAction) => {
  showFeedback('error', title, message, action, 8000) // 错误消息显示更长时间
}

const showInfo = (title: string, message = '', action?: FeedbackAction) => {
  showFeedback('info', title, message, action)
}

// 暴露方法给父组件使用
defineExpose({
  startGlobalLoading,
  updateGlobalLoading,
  stopGlobalLoading,
  startPageLoading,
  stopPageLoading,
  showFeedback,
  showSuccess,
  showWarning,
  showError,
  showInfo,
  hideFeedbackBar,
  addTask,
  updateTask,
  removeTask
})

onMounted(() => {
  // 开始定期更新任务状态
  taskUpdateTimer = window.setInterval(() => {
    // 这里可以添加定期更新逻辑
  }, 1000)
})

onUnmounted(() => {
  if (feedbackTimer) {
    clearTimeout(feedbackTimer)
  }
  if (taskUpdateTimer) {
    clearInterval(taskUpdateTimer)
  }
})
</script>

<style scoped>
.global-loading-manager {
  position: relative;
  z-index: 9999;
}

/* 加载对话框样式 */
.loading-dialog :deep(.el-dialog) {
  border-radius: 12px;
  overflow: hidden;
}

.loading-dialog :deep(.el-dialog__header) {
  display: none;
}

.loading-dialog :deep(.el-dialog__body) {
  padding: 30px 20px;
}

.loading-content {
  text-align: center;
}

.loading-animation {
  margin-bottom: 20px;
}

.rotating {
  animation: rotate 2s linear infinite;
  color: #409eff;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.loading-text h3 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 18px;
  font-weight: 600;
}

.loading-text p {
  margin: 0 0 20px 0;
  color: #606266;
  font-size: 14px;
}

.loading-progress {
  margin-bottom: 20px;
}

.progress-details {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

.loading-actions {
  margin-top: 15px;
}

/* 反馈条样式 */
.feedback-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 3000;
  padding: 12px 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0.1);
}

.feedback-bar.success {
  background-color: #f0f9ff;
  border-bottom: 3px solid #67c23a;
}

.feedback-bar.warning {
  background-color: #fdf6ec;
  border-bottom: 3px solid #e6a23c;
}

.feedback-bar.error {
  background-color: #fef0f0;
  border-bottom: 3px solid #f56c6c;
}

.feedback-bar.info {
  background-color: #f4f4f5;
  border-bottom: 3px solid #909399;
}

.feedback-content {
  display: flex;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
}

.feedback-icon {
  font-size: 20px;
  margin-right: 12px;
}

.feedback-bar.success .feedback-icon {
  color: #67c23a;
}

.feedback-bar.warning .feedback-icon {
  color: #e6a23c;
}

.feedback-bar.error .feedback-icon {
  color: #f56c6c;
}

.feedback-bar.info .feedback-icon {
  color: #909399;
}

.feedback-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.feedback-title {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

.feedback-message {
  color: #606266;
  font-size: 13px;
}

.feedback-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 任务队列指示器样式 */
.task-queue-indicator {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 320px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0.15);
  z-index: 2000;
  overflow: hidden;
}

.queue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

.queue-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
  color: #303133;
  font-size: 14px;
}

.queue-details {
  max-height: 300px;
  overflow-y: auto;
}

.queue-task {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.queue-task:last-child {
  border-bottom: none;
}

.queue-task.active {
  background: #f0f9ff;
  border-left: 3px solid #409eff;
}

.task-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.task-title {
  font-size: 13px;
  color: #303133;
  font-weight: 500;
}

.task-progress {
  margin-top: 8px;
}

/* 动画效果 */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from {
  transform: translateY(-100%);
  opacity: 0;
}

.slide-down-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from {
  transform: translateY(100%);
  opacity: 0;
}

.slide-up-leave-to {
  transform: translateY(100%);
  opacity: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .loading-dialog {
    width: 90% !important;
  }
  
  .task-queue-indicator {
    bottom: 10px;
    right: 10px;
    left: 10px;
    width: auto;
  }
  
  .feedback-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .feedback-actions {
    align-self: stretch;
    justify-content: flex-end;
  }
}
</style>