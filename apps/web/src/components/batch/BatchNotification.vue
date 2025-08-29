<template>
  <div class="batch-notification">
    <!-- 通知容器 -->
    <div class="notification-container">
      <transition-group name="notification" tag="div" class="notification-list">
        <div
          v-for="notification in visibleNotifications"
          :key="notification.id"
          class="notification-item"
          :class="[`notification-${notification.type}`]"
          @click="handleNotificationClick(notification)"
        >
          <div class="notification-icon">
            <el-icon :size="20">
              <component :is="getNotificationIcon(notification.type)" />
            </el-icon>
          </div>
          
          <div class="notification-content">
            <div class="notification-title">{{ notification.title }}</div>
            <div class="notification-message">{{ notification.message }}</div>
            <div class="notification-time">{{ formatRelativeTime(notification.timestamp) }}</div>
          </div>
          
          <div class="notification-actions">
            <el-button
              text
              :icon="Close"
              @click.stop="dismissNotification(notification.id)"
              class="dismiss-button"
            />
          </div>
        </div>
      </transition-group>
    </div>
    
    <!-- 通知中心按钮 -->
    <div class="notification-center">
      <el-badge :value="unreadCount" :hidden="unreadCount === 0">
        <el-button
          type="primary"
          :icon="Bell"
          circle
          @click="toggleNotificationCenter"
          class="notification-button"
        />
      </el-badge>
    </div>
    
    <!-- 通知中心抽屉 -->
    <el-drawer
      v-model="showNotificationCenter"
      title="通知中心"
      direction="rtl"
      size="400px"
    >
      <div class="notification-center-content">
        <!-- 通知筛选 -->
        <div class="notification-filters">
          <el-radio-group v-model="filterType" @change="filterNotifications">
            <el-radio-button value="all">全部</el-radio-button>
            <el-radio-button value="unread">未读</el-radio-button>
            <el-radio-button value="success">成功</el-radio-button>
            <el-radio-button value="error">错误</el-radio-button>
          </el-radio-group>
          
          <div class="notification-actions-bar">
            <el-button text @click="markAllAsRead">
              全部标记为已读
            </el-button>
            <el-button text @click="clearAllNotifications">
              清空通知
            </el-button>
          </div>
        </div>
        
        <!-- 通知列表 -->
        <div class="notification-history">
          <div
            v-for="notification in filteredNotifications"
            :key="notification.id"
            class="history-notification-item"
            :class="{ 'unread': !notification.read }"
            @click="markAsRead(notification.id)"
          >
            <div class="history-notification-header">
              <div class="notification-meta">
                <el-icon :color="getNotificationColor(notification.type)">
                  <component :is="getNotificationIcon(notification.type)" />
                </el-icon>
                <span class="notification-type">{{ getNotificationTypeText(notification.type) }}</span>
                <span class="notification-timestamp">{{ formatTime(notification.timestamp) }}</span>
              </div>
              <el-button
                text
                :icon="Close"
                @click.stop="removeNotification(notification.id)"
                size="small"
              />
            </div>
            
            <div class="history-notification-content">
              <h4>{{ notification.title }}</h4>
              <p>{{ notification.message }}</p>
            </div>
            
            <div v-if="notification.actions" class="notification-action-buttons">
              <el-button
                v-for="action in notification.actions"
                :key="action.label"
                :type="action.type || 'text'"
                size="small"
                @click.stop="handleAction(action, notification)"
              >
                {{ action.label }}
              </el-button>
            </div>
          </div>
          
          <div v-if="filteredNotifications.length === 0" class="no-notifications">
            <el-empty description="暂无通知" />
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
// ElMessage removed
import {
  Bell,
  Close,
  CircleCheck,
  Warning,
  InfoFilled
} from '@element-plus/icons-vue'

interface NotificationAction {
  label: string
  type?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'text'
  action: string
  params?: any
}

interface Notification {
  id: string
  type: 'success' | 'warning' | 'error' | 'info'
  title: string
  message: string
  timestamp: number
  read?: boolean
  persistent?: boolean
  autoClose?: boolean
  duration?: number
  actions?: NotificationAction[]
}

interface Props {
  notifications: Notification[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  notificationDismissed: [notificationId: string]
  notificationAction: [action: string, params: any, notification: Notification]
}>()

// 响应式数据
const showNotificationCenter = ref(false)
const filterType = ref('all')
const maxVisibleNotifications = ref(3)

// 所有通知的本地副本
const allNotifications = ref<Notification[]>([])

// 可见的浮动通知
const visibleNotifications = computed(() => {
  return allNotifications.value
    .filter(n => !n.read && (n.persistent || !n.autoClose))
    .slice(0, maxVisibleNotifications.value)
})

// 未读通知数量
const unreadCount = computed(() => {
  return allNotifications.value.filter(n => !n.read).length
})

// 过滤后的通知列表
const filteredNotifications = computed(() => {
  let notifications = [...allNotifications.value].reverse() // 最新的在前面
  
  switch (filterType.value) {
    case 'unread':
      notifications = notifications.filter(n => !n.read)
      break
    case 'success':
      notifications = notifications.filter(n => n.type === 'success')
      break
    case 'error':
      notifications = notifications.filter(n => n.type === 'error')
      break
    case 'warning':
      notifications = notifications.filter(n => n.type === 'warning')
      break
    case 'info':
      notifications = notifications.filter(n => n.type === 'info')
      break
  }
  
  return notifications
})

// 获取通知图标
const getNotificationIcon = (type: string) => {
  const iconMap = {
    success: 'CircleCheck',
    warning: 'Warning',
    error: 'CircleClose',
    info: 'InfoFilled'
  }
  return iconMap[type] || 'InfoFilled'
}

// 获取通知颜色
const getNotificationColor = (type: string) => {
  const colorMap = {
    success: '#67c23a',
    warning: '#e6a23c',
    error: '#f56c6c',
    info: '#409eff'
  }
  return colorMap[type] || '#409eff'
}

// 获取通知类型文本
const getNotificationTypeText = (type: string) => {
  const textMap = {
    success: '成功',
    warning: '警告',
    error: '错误',
    info: '信息'
  }
  return textMap[type] || '信息'
}

// 相对时间格式化
const formatRelativeTime = (timestamp: number) => {
  const now = Date.now()
  const diff = now - timestamp
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return `${Math.floor(diff / 86400000)}天前`
}

// 绝对时间格式化
const formatTime = (timestamp: number) => {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN')
}

// 切换通知中心
const toggleNotificationCenter = () => {
  showNotificationCenter.value = !showNotificationCenter.value
}

// 处理通知点击
const handleNotificationClick = (notification: Notification) => {
  markAsRead(notification.id)
  
  // 如果有默认操作，执行它
  if (notification.actions && notification.actions.length > 0) {
    const defaultAction = notification.actions[0]
    handleAction(defaultAction, notification)
  }
}

// 关闭通知
const dismissNotification = (notificationId: string) => {
  const index = allNotifications.value.findIndex(n => n.id === notificationId)
  if (index >= 0) {
    allNotifications.value.splice(index, 1)
  }
  emit('notificationDismissed', notificationId)
}

// 移除通知
const removeNotification = (notificationId: string) => {
  dismissNotification(notificationId)
}

// 标记为已读
const markAsRead = (notificationId: string) => {
  const notification = allNotifications.value.find(n => n.id === notificationId)
  if (notification) {
    notification.read = true
  }
}

// 标记全部为已读
const markAllAsRead = () => {
  allNotifications.value.forEach(n => {
    n.read = true
  })
}

// 清空所有通知
const clearAllNotifications = () => {
  allNotifications.value = []
  emit('notificationDismissed', 'all')
}

// 过滤通知
const filterNotifications = () => {
  // 过滤逻辑在计算属性中处理
}

// 处理通知动作
const handleAction = (action: NotificationAction, notification: Notification) => {
  emit('notificationAction', action.action, action.params, notification)
}

// 自动关闭通知
const setupAutoClose = (notification: Notification) => {
  if (notification.autoClose !== false) {
    const duration = notification.duration || 5000
    setTimeout(() => {
      if (!notification.read) {
        dismissNotification(notification.id)
      }
    }, duration)
  }
}

// 监听props变化
watch(() => props.notifications, (newNotifications) => {
  // 添加新通知
  newNotifications.forEach(notification => {
    const exists = allNotifications.value.find(n => n.id === notification.id)
    if (!exists) {
      allNotifications.value.push({ ...notification })
      setupAutoClose(notification)
    }
  })
  
  // 移除不存在的通知
  allNotifications.value = allNotifications.value.filter(existing => 
    newNotifications.some(n => n.id === existing.id)
  )
}, { immediate: true, deep: true })

// 键盘快捷键
const handleKeyboard = (event: KeyboardEvent) => {
  // Esc 关闭通知中心
  if (event.key === 'Escape' && showNotificationCenter.value) {
    showNotificationCenter.value = false
  }
  
  // Ctrl/Cmd + Shift + N 打开通知中心
  if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'N') {
    toggleNotificationCenter()
    event.preventDefault()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeyboard)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyboard)
})
</script>

<style scoped>
.batch-notification {
  position: relative;
}

.notification-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 3000;
  max-width: 400px;
  pointer-events: none;
}

.notification-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0.15);
  border-left: 4px solid;
  cursor: pointer;
  pointer-events: auto;
  transition: all 0.3s ease;
  max-width: 380px;
}

.notification-item:hover {
  transform: translateX(-5px);
  box-shadow: 0 6px 16px rgba(0, 0, 0.2);
}

.notification-success {
  border-left-color: #67c23a;
}

.notification-warning {
  border-left-color: #e6a23c;
}

.notification-error {
  border-left-color: #f56c6c;
}

.notification-info {
  border-left-color: #409eff;
}

.notification-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  color: #303133;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 4px;
  line-height: 1.4;
}

.notification-message {
  color: #606266;
  font-size: 13px;
  line-height: 1.4;
  margin-bottom: 6px;
  word-wrap: break-word;
}

.notification-time {
  color: #909399;
  font-size: 12px;
}

.notification-actions {
  flex-shrink: 0;
}

.dismiss-button {
  color: #c0c4cc;
  padding: 0;
  margin: 0;
  width: 20px;
  height: 20px;
}

.dismiss-button:hover {
  color: #f56c6c;
}

.notification-center {
  position: fixed;
  bottom: 30px;
  right: 30px;
  z-index: 2000;
}

.notification-button {
  width: 50px;
  height: 50px;
  box-shadow: 0 4px 12px rgba(0, 0, 0.15);
}

.notification-center-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.notification-filters {
  padding: 20px;
  border-bottom: 1px solid #ebeef5;
}

.notification-actions-bar {
  display: flex;
  justify-content: space-between;
  margin-top: 15px;
}

.notification-history {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

.history-notification-item {
  padding: 20px;
  border-bottom: 1px solid #f5f7fa;
  cursor: pointer;
  transition: background-color 0.2s;
}

.history-notification-item:hover {
  background-color: #f9f9f9;
}

.history-notification-item.unread {
  background-color: #f0f9ff;
  border-left: 3px solid #409eff;
}

.history-notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.notification-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.notification-type {
  color: #909399;
  font-size: 12px;
  font-weight: 500;
}

.notification-timestamp {
  color: #c0c4cc;
  font-size: 12px;
}

.history-notification-content h4 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.4;
}

.history-notification-content p {
  margin: 0 0 12px 0;
  color: #606266;
  font-size: 13px;
  line-height: 1.5;
  word-wrap: break-word;
}

.notification-action-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.no-notifications {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
}

/* 过渡动画 */
.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.notification-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

.notification-move {
  transition: transform 0.3s ease;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .notification-container {
    top: 10px;
    right: 10px;
    left: 10px;
    max-width: none;
  }
  
  .notification-item {
    max-width: none;
  }
  
  .notification-center {
    bottom: 20px;
    right: 20px;
  }
  
  .notification-button {
    width: 45px;
    height: 45px;
  }
}
</style>