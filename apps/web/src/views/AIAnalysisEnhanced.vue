<template>
  <div class="ai-analysis-enhanced">
    <div class="page-header">
      <h1>AI智能分析增强版</h1>
      <p class="page-description">基于智谱AI GLM-4模型，提供更智能、更准确的文档分析和数据提取</p>
    </div>

    <div class="analysis-container">
      <!-- 功能导航卡片 -->
      <div class="feature-cards">
        <el-card 
          class="feature-card" 
          :class="{ active: activeFeature === 'single' }"
          @click="activeFeature = 'single'"
        >
          <div class="card-content">
            <el-icon class="card-icon"><Document /></el-icon>
            <h3>单文档智能分析</h3>
            <p>深度分析单个文档，提取结构化数据</p>
          </div>
        </el-card>

        <el-card 
          class="feature-card" 
          :class="{ active: activeFeature === 'batch' }"
          @click="activeFeature = 'batch'"
        >
          <div class="card-content">
            <el-icon class="card-icon"><FolderOpened /></el-icon>
            <h3>批量智能分析</h3>
            <p>高效处理多个文档的批量分析任务</p>
          </div>
        </el-card>

        <el-card 
          class="feature-card" 
          :class="{ active: activeFeature === 'comparison' }"
          @click="activeFeature = 'comparison'"
        >
          <div class="card-content">
            <el-icon class="card-icon"><DocumentCopy /></el-icon>
            <h3>智能文档对比</h3>
            <p>AI驱动的多文档对比和差异分析</p>
          </div>
        </el-card>

        <el-card 
          class="feature-card" 
          :class="{ active: activeFeature === 'optimization' }"
          @click="activeFeature = 'optimization'"
        >
          <div class="card-content">
            <el-icon class="card-icon"><EditPen /></el-icon>
            <h3>Prompt智能优化</h3>
            <p>基于历史数据优化AI提示词效果</p>
          </div>
        </el-card>
      </div>

      <!-- 主要功能区域 -->
      <el-card class="main-feature-area">
        <!-- 单文档分析 -->
        <div v-if="activeFeature === 'single'" class="feature-content">
          <div class="feature-header">
            <h2>单文档智能分析</h2>
            <p>上传文档，AI将自动识别并提取关键信息，支持产品规格、技术参数、价格等数据</p>
          </div>
          
          <!-- 权限检查 -->
          <div v-if="!hasPermission" class="permission-warning">
            <el-alert
              title="权限不足"
              :description="`当前角色 ${userRole} 无权使用AI分析功能。请联系管理员分配 engineer、admin 或 manager 角色。`"
              type="warning"
              show-icon
              :closable="false"
            />
          </div>
          
          <EnhancedSingleAnalysis 
            v-else
            @analysis-success="handleSingleAnalysisSuccess"
            @analysis-error="handleAnalysisError"
          />
        </div>

        <!-- 批量分析 -->
        <div v-if="activeFeature === 'batch'" class="feature-content">
          <div class="feature-header">
            <h2>批量智能分析</h2>
            <p>一次性上传多个文档，系统将自动排队处理，提供实时进度监控</p>
          </div>
          
          <div class="batch-analysis-section">
            <el-alert
              title="批量分析功能"
              type="info"
              description="此功能可在批量分析页面使用，点击下方按钮快速跳转"
              show-icon
              :closable="false"
              style="margin-bottom: 20px"
            />
            
            <div class="quick-actions">
              <el-button 
                type="primary" 
                size="large"
                :disabled="!hasPermission"
                @click="$router.push('/batch-analysis')"
              >
                <template #icon>
                  <el-icon><FolderOpened /></el-icon>
                </template>
                进入批量分析
              </el-button>
              <div v-if="!hasPermission" class="permission-hint">
                <el-text type="warning" size="small">需要 engineer/admin/manager 权限</el-text>
              </div>
            </div>
          </div>
        </div>

        <!-- 文档对比 -->
        <div v-if="activeFeature === 'comparison'" class="feature-content">
          <div class="feature-header">
            <h2>智能文档对比</h2>
            <p>上传多个文档进行AI驱动的智能对比，识别相似性和差异性</p>
          </div>
          
          <div class="comparison-section">
            <el-alert
              title="文档对比功能"
              type="info"
              description="此功能可在文档对比页面使用，点击下方按钮快速跳转"
              show-icon
              :closable="false"
              style="margin-bottom: 20px"
            />
            
            <div class="quick-actions">
              <el-button 
                type="primary" 
                size="large"
                :disabled="!hasPermission"
                @click="$router.push('/document-comparison')"
              >
                <template #icon>
                  <el-icon><DocumentCopy /></el-icon>
                </template>
                进入文档对比
              </el-button>
              <div v-if="!hasPermission" class="permission-hint">
                <el-text type="warning" size="small">需要 engineer/admin/manager 权限</el-text>
              </div>
            </div>
          </div>
        </div>

        <!-- Prompt优化 -->
        <div v-if="activeFeature === 'optimization'" class="feature-content">
          <div class="feature-header">
            <h2>Prompt智能优化</h2>
            <p>基于历史分析数据，智能优化AI提示词，提升分析准确性和用户满意度</p>
          </div>
          
          <div class="optimization-section">
            <el-alert
              title="Prompt优化功能"
              type="info"
              description="此功能可在Prompt优化页面使用，点击下方按钮快速跳转"
              show-icon
              :closable="false"
              style="margin-bottom: 20px"
            />
            
            <div class="quick-actions">
              <el-button 
                type="primary" 
                size="large"
                :disabled="!hasPermission"
                @click="$router.push('/prompt-optimization')"
              >
                <template #icon>
                  <el-icon><EditPen /></el-icon>
                </template>
                进入Prompt优化
              </el-button>
              <div v-if="!hasPermission" class="permission-hint">
                <el-text type="warning" size="small">需要 engineer/admin/manager 权限</el-text>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 快速统计信息 -->
      <div class="stats-overview">
        <el-card class="stats-card">
          <div class="stat-item">
            <div class="stat-number">{{ stats.totalAnalyses }}</div>
            <div class="stat-label">总分析次数</div>
          </div>
        </el-card>
        
        <el-card class="stats-card">
          <div class="stat-item">
            <div class="stat-number">{{ (stats.successRate * 100).toFixed(1) }}%</div>
            <div class="stat-label">成功率</div>
          </div>
        </el-card>
        
        <el-card class="stats-card">
          <div class="stat-item">
            <div class="stat-number">{{ stats.avgConfidence.toFixed(1) }}</div>
            <div class="stat-label">平均置信度</div>
          </div>
        </el-card>
        
        <el-card class="stats-card">
          <div class="stat-item">
            <div class="stat-number">{{ stats.processingJobs }}</div>
            <div class="stat-label">处理中任务</div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 最近分析结果 -->
    <el-card class="recent-results-card">
      <template #header>
        <div class="card-header">
          <h3>最近分析结果</h3>
          <el-button link @click="viewAllResults">查看全部</el-button>
        </div>
      </template>
      
      <RecentAnalysisResults 
        :results="recentResults"
        @result-selected="handleResultSelected"
      />
    </el-card>

    <!-- AI模型信息 -->
    <el-card class="model-info-card">
      <template #header>
        <h3>AI模型信息</h3>
      </template>
      
      <div class="model-info">
        <div class="model-item">
          <div class="model-label">当前模型</div>
          <div class="model-value">智谱AI GLM-4</div>
        </div>
        <div class="model-item">
          <div class="model-label">模型版本</div>
          <div class="model-value">GLM-4-0520</div>
        </div>
        <div class="model-item">
          <div class="model-label">服务状态</div>
          <div class="model-value">
            <el-tag :type="modelStatus === 'online' ? 'success' : 'danger'">
              {{ modelStatus === 'online' ? '在线' : '离线' }}
            </el-tag>
          </div>
        </div>
        <div class="model-item">
          <div class="model-label">响应时间</div>
          <div class="model-value">{{ avgResponseTime }}ms</div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
// ElMessage removed
import { showMessage } from '@/utils/message'
import { Document, FolderOpened, DocumentCopy, EditPen } from '@element-plus/icons-vue'
import EnhancedSingleAnalysis from '@/components/ai/EnhancedSingleAnalysis.vue'
import RecentAnalysisResults from '@/components/ai/RecentAnalysisResults.vue'
import { getAnalysisStatistics } from '@/api/ai-analysis'
import type { AIAnalysisResult } from '@/types/ai-analysis'

const router = useRouter()
const authStore = useAuthStore()

// 当前激活的功能
const activeFeature = ref('single')

// 权限检查
const hasPermission = computed(() => authStore.hasAIAnalysisRole)
const userRole = computed(() => authStore.userRole)
const isAuthenticated = computed(() => authStore.isAuthenticated)

// 统计数据
const stats = reactive({
  totalAnalyses: 0,
  successRate: 0,
  avgConfidence: 0,
  processingJobs: 0
})

// 最近结果
const recentResults = ref<AIAnalysisResult[]>([])

// AI模型状态
const modelStatus = ref<'online' | 'offline'>('online')
const avgResponseTime = ref(850)

const handleSingleAnalysisSuccess = (result: AIAnalysisResult) => {
  showMessage.success('分析完成！')
  
  // 添加到最近结果
  recentResults.value.unshift(result)
  if (recentResults.value.length > 5) {
    recentResults.value = recentResults.value.slice(0, 5)
  }
  
  // 更新统计
  loadStatistics()
}

const handleAnalysisError = (error: string) => {
  showMessage.error(`分析失败: ${error}`)
}

const handleResultSelected = (result: AIAnalysisResult) => {
  // 跳转到结果详情页面或显示详情对话框
  showMessage.info('查看分析结果详情')
}

const viewAllResults = () => {
  // 跳转到分析历史页面
  showMessage.info('查看所有分析结果')
}

const loadStatistics = async () => {
  // 检查权限
  if (!hasPermission.value) {
    console.warn('用户无AI分析权限，跳过统计数据加载')
    return
  }
  
  try {
    const response = await getAnalysisStatistics({ days: 30 })
    
    if (response.success) {
      stats.totalAnalyses = response.statistics.total_analyses
      stats.successRate = response.statistics.success_rate
      stats.avgConfidence = response.statistics.average_confidence
    }
  } catch (error) {
    console.error('Failed to load statistics:', error)
    showMessage.error('加载统计数据失败：请确认您有足够的权限')
  }
}

const checkModelStatus = () => {
  // 模拟检查AI模型状态
  const randomCheck = Math.random()
  modelStatus.value = randomCheck > 0.1 ? 'online' : 'offline'
  
  // 模拟响应时间变化
  avgResponseTime.value = Math.floor(Math.random() * 500) + 600
}

onMounted(async () => {
  // 检查认证状态
  if (!isAuthenticated.value) {
    showMessage.warning('请先登录后再使用AI分析功能')
    router.push('/login')
    return
  }
  
  // 如果用户信息不完整，尝试加载
  if (!authStore.user && authStore.token) {
    try {
      await authStore.loadUserProfile()
    } catch (error) {
      console.error('加载用户信息失败:', error)
      showMessage.error('用户信息加载失败，请重新登录')
      router.push('/login')
      return
    }
  }
  
  // 检查AI分析权限
  if (!hasPermission.value) {
    showMessage.error(`抱歉，${userRole.value} 角色无权访问AI分析功能。仅限 engineer、admin、manager 角色使用。`)
    router.push('/dashboard')
    return
  }
  
  // 权限验证通过，加载数据
  loadStatistics()
  checkModelStatus()
  
  // 定期检查模型状态
  setInterval(checkModelStatus, 30000) // 每30秒检查一次
  
  showMessage.success('AI智能分析系统已就绪，基于智谱AI GLM-4模型提供服务')
})
</script>

<style scoped>
.ai-analysis-enhanced {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 30px;
  text-align: center;
}

.page-header h1 {
  color: #303133;
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 10px;
}

.page-description {
  color: #909399;
  font-size: 16px;
  margin: 0;
  line-height: 1.5;
}

.analysis-container {
  margin-bottom: 30px;
}

.feature-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.feature-card {
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.feature-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.2);
}

.feature-card.active {
  border-color: #409eff;
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.3);
}

.card-content {
  text-align: center;
  padding: 20px;
}

.card-icon {
  font-size: 48px;
  color: #409eff;
  margin-bottom: 15px;
}

.card-content h3 {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 18px;
  font-weight: 600;
}

.card-content p {
  margin: 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.4;
}

.main-feature-area {
  margin-bottom: 30px;
  min-height: 400px;
}

.feature-content {
  padding: 20px;
}

.feature-header {
  text-align: center;
  margin-bottom: 30px;
}

.feature-header h2 {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 24px;
  font-weight: 600;
}

.feature-header p {
  margin: 0;
  color: #606266;
  font-size: 16px;
  line-height: 1.5;
}

.batch-analysis-section,
.comparison-section,
.optimization-section {
  text-align: center;
  padding: 40px 20px;
}

.quick-actions {
  margin-top: 20px;
}

.stats-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stats-card {
  text-align: center;
}

.stat-item {
  padding: 20px;
}

.stat-number {
  font-size: 32px;
  font-weight: 600;
  color: #409eff;
  margin-bottom: 5px;
}

.stat-label {
  color: #606266;
  font-size: 14px;
}

.recent-results-card {
  margin-bottom: 30px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  color: #303133;
  font-size: 18px;
  font-weight: 600;
}

.model-info-card {
  margin-bottom: 30px;
}

.model-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.model-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.model-label {
  font-size: 14px;
  color: #909399;
  font-weight: 500;
}

.model-value {
  font-size: 16px;
  color: #303133;
  font-weight: 600;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .ai-analysis-enhanced {
    padding: 15px;
  }
  
  .page-header h1 {
    font-size: 24px;
  }
  
  .page-description {
    font-size: 14px;
  }
  
  .feature-cards {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  
  .card-content {
    padding: 15px;
  }
  
  .card-icon {
    font-size: 36px;
  }
  
  .card-content h3 {
    font-size: 16px;
  }
  
  .feature-header h2 {
    font-size: 20px;
  }
  
  .feature-header p {
    font-size: 14px;
  }
  
  .stats-overview {
    grid-template-columns: 1fr 1fr;
    gap: 15px;
  }
  
  .stat-number {
    font-size: 24px;
  }
  
  .model-info {
    grid-template-columns: 1fr;
  }
}

/* 权限相关样式 */
.permission-warning {
  margin-bottom: 20px;
}

.permission-hint {
  margin-top: 10px;
  text-align: center;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}
</style>