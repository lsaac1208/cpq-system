<template>
  <div class="layout">
    <el-container>
      <!-- Header -->
      <el-header class="header">
        <div class="header-left">
          <h1 class="title">CPQ系统</h1>
        </div>
        <div class="header-right">
          <span class="user-info">{{ authStore.user?.full_name }}</span>
          <el-dropdown @command="handleCommand">
            <el-button link class="user-dropdown">
              <el-icon><User /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人资料</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-container>
        <!-- Sidebar -->
        <el-aside class="sidebar" width="200px">
          <el-menu
            :default-active="currentRoute"
            class="sidebar-menu"
            router
            background-color="#f5f5f5"
            text-color="#333"
            active-text-color="#409eff"
          >
            <el-menu-item index="/">
              <el-icon><Odometer /></el-icon>
              <span>仪表盘</span>
            </el-menu-item>
            <el-menu-item index="/products">
              <el-icon><Box /></el-icon>
              <span>产品管理</span>
            </el-menu-item>
            <el-menu-item index="/search">
              <el-icon><Search /></el-icon>
              <span>产品搜索</span>
            </el-menu-item>
            <el-menu-item index="/quotes">
              <el-icon><Document /></el-icon>
              <span>报价管理</span>
            </el-menu-item>
            
            <!-- AI功能菜单组 -->
            <el-sub-menu index="ai-features">
              <template #title>
                <el-icon><MagicStick /></el-icon>
                <span>AI智能功能</span>
              </template>
              <el-menu-item index="/ai-analysis-enhanced">
                <el-icon><Monitor /></el-icon>
                <span>智能分析增强</span>
              </el-menu-item>
              <el-menu-item index="/prompt-optimization">
                <el-icon><EditPen /></el-icon>
                <span>Prompt优化</span>
              </el-menu-item>
              <el-menu-item index="/document-comparison">
                <el-icon><DocumentCopy /></el-icon>
                <span>文档对比</span>
              </el-menu-item>
              <el-menu-item index="/batch-analysis">
                <el-icon><FolderOpened /></el-icon>
                <span>批量分析</span>
              </el-menu-item>
              <el-menu-item index="/pricing-decision">
                <el-icon><TrendCharts /></el-icon>
                <span>报价决策支持</span>
              </el-menu-item>
            </el-sub-menu>
            
            <el-menu-item v-if="authStore.isAdmin" index="/settings">
              <el-icon><Setting /></el-icon>
              <span>系统设置</span>
            </el-menu-item>
          </el-menu>
        </el-aside>

        <!-- Main Content -->
        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
// ElMessage removed
import { showMessage } from '@/utils/message'
import { 
  User, 
  Odometer, 
  Box, 
  Document, 
  Setting, 
  Search, 
  MagicStick,
  EditPen, 
  DocumentCopy, 
  FolderOpened,
  TrendCharts,
  Monitor
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const currentRoute = computed(() => route.path)

// 确保用户信息已加载
onMounted(async () => {
  // 如果有token但用户信息未加载，尝试加载
  if (authStore.isAuthenticated && !authStore.user) {
    try {
      await authStore.loadUserProfile()
      console.log('✅ Layout: 用户信息加载成功', authStore.user?.username, '角色:', authStore.userRole)
    } catch (error) {
      console.warn('❌ Layout: 用户信息加载失败', error)
    }
  }
})

// 监听路由变化，确保管理员状态正确
watch([() => authStore.user, () => route.path], ([user, path]) => {
  if (user) {
    console.log('🔄 Layout: 用户状态更新', {
      username: user.username,
      role: user.role,
      isAdmin: authStore.isAdmin,
      currentPath: path
    })
  }
}, { immediate: true })

const handleCommand = (command: string) => {
  switch (command) {
    case 'profile':
      showMessage.info('个人资料功能即将推出')
      break
    case 'logout':
      authStore.logout()
      router.push('/login')
      showMessage.success('退出登录成功')
      break
  }
}
</script>

<style scoped>
.layout {
  height: 100vh;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 20px;
}

.header-left .title {
  margin: 0;
  color: #409eff;
  font-size: 24px;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-info {
  color: #606266;
  font-size: 14px;
}

.user-dropdown {
  color: #606266;
}

.sidebar {
  background-color: #f5f5f5;
  border-right: 1px solid #e4e7ed;
}

.sidebar-menu {
  border: none;
  height: 100%;
}

.main-content {
  background-color: #f9f9f9;
  padding: 20px;
}
</style>