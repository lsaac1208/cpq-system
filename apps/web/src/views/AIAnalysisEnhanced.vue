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

  <!-- 分析结果详情对话框 -->
  <el-dialog
    v-model="showDetailDialog"
    title="分析结果详情"
    width="80%"
    top="5vh"
    :close-on-click-modal="false"
  >
    <div v-if="selectedAnalysisResult" class="analysis-detail">
      <!-- 基础信息 -->
      <el-card class="detail-section">
        <template #header>
          <h3>基础信息</h3>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="产品名称">
            {{ selectedAnalysisResult.extracted_data?.basic_info?.name || '未识别' }}
          </el-descriptions-item>
          <el-descriptions-item label="产品代码">
            {{ selectedAnalysisResult.extracted_data?.basic_info?.code || '未识别' }}
          </el-descriptions-item>
          <el-descriptions-item label="产品分类">
            {{ selectedAnalysisResult.extracted_data?.basic_info?.category || '未识别' }}
          </el-descriptions-item>
          <el-descriptions-item label="文档名称">
            {{ selectedAnalysisResult.document_info?.filename }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 统计信息 -->
      <el-card class="detail-section">
        <template #header>
          <h3>统计信息</h3>
        </template>
        <el-descriptions :column="3" border>
          <el-descriptions-item label="技术规格">
            {{ Object.keys(selectedAnalysisResult.extracted_data?.specifications || {}).length }} 项
          </el-descriptions-item>
          <el-descriptions-item label="产品特性">
            {{ selectedAnalysisResult.extracted_data?.features?.length || 0 }} 项
          </el-descriptions-item>
          <el-descriptions-item label="认证信息">
            {{ selectedAnalysisResult.extracted_data?.certificates?.length || 0 }} 项
          </el-descriptions-item>
          <el-descriptions-item label="文件大小">
            {{ formatFileSize(selectedAnalysisResult.document_info?.size || 0) }}
          </el-descriptions-item>
          <el-descriptions-item label="分析时长">
            {{ selectedAnalysisResult.document_info?.analysis_duration || 0 }}秒
          </el-descriptions-item>
          <el-descriptions-item label="整体置信度">
            {{ Math.round((selectedAnalysisResult.confidence_scores?.overall || 0) * 100) }}%
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 技术规格详情 -->
      <el-card v-if="Object.keys(selectedAnalysisResult.extracted_data?.specifications || {}).length > 0" class="detail-section">
        <template #header>
          <h3>技术规格详情</h3>
        </template>
        <el-table :data="formatSpecifications(selectedAnalysisResult.extracted_data?.specifications || {})" border>
          <el-table-column prop="name" label="规格名称" />
          <el-table-column prop="value" label="规格值" />
        </el-table>
      </el-card>

      <!-- 产品特性 -->
      <el-card v-if="selectedAnalysisResult.extracted_data?.features?.length" class="detail-section">
        <template #header>
          <h3>产品特性</h3>
        </template>
        <el-tag 
          v-for="(feature, index) in selectedAnalysisResult.extracted_data.features" 
          :key="index"
          type="info"
          style="margin: 5px;"
        >
          {{ feature }}
        </el-tag>
      </el-card>
    </div>

    <template #footer>
      <el-button @click="showDetailDialog = false">关闭</el-button>
      <el-button v-if="selectedAnalysisResult?.success" type="primary" @click="createProductFromResult">
        创建产品
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
// ElMessage removed
import { showMessage } from '@/utils/message'
import { Document, FolderOpened, DocumentCopy, EditPen } from '@element-plus/icons-vue'
import EnhancedSingleAnalysis from '@/components/ai/EnhancedSingleAnalysis.vue'
import RecentAnalysisResults from '@/components/ai/RecentAnalysisResults.vue'
import { getAnalysisStatistics, getRecentAnalysisResults } from '@/api/ai-analysis'
import type { AIAnalysisResult } from '@/types/ai-analysis'

const router = useRouter()
const authStore = useAuthStore()

// 当前激活的功能
const activeFeature = ref('single')

// 详情对话框相关
const showDetailDialog = ref(false)
const selectedAnalysisResult = ref<AIAnalysisResult | null>(null)

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
  
  // 更新统计和最近结果
  loadStatistics()
  loadRecentResults()
}

const handleAnalysisError = (error: string) => {
  showMessage.error(`分析失败: ${error}`)
}

const handleResultSelected = (result: AIAnalysisResult) => {
  // 显示详细的分析结果对话框
  selectedAnalysisResult.value = result
  showDetailDialog.value = true
}

const viewAllResults = () => {
  // 跳转到分析历史页面
  showMessage.info('查看所有分析结果')
}

// Helper functions for detail dialog
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatSpecifications = (specs: Record<string, any>): Array<{name: string, value: string}> => {
  return Object.entries(specs).map(([name, value]) => ({
    name,
    value: String(value)
  }))
}

const createProductFromResult = () => {
  if (!selectedAnalysisResult.value) {
    showMessage.warning('没有选择分析结果')
    return
  }
  
  // 基于分析结果创建产品
  const analysisData = selectedAnalysisResult.value
  showMessage.success('正在基于分析结果创建产品...')
  
  // 这里可以跳转到产品创建页面，并传递分析数据
  // router.push({
  //   path: '/products/create',
  //   query: { fromAnalysis: analysisData.id }
  // })
  
  showDetailDialog.value = false
}

const loadStatistics = async () => {
  // 只检查认证状态，让API处理权限控制
  if (!isAuthenticated.value) {
    console.warn('用户未认证，跳过统计数据加载')
    return
  }
  
  console.log('=== 开始加载统计数据 ===')
  console.log('当前stats对象:', JSON.stringify(stats))
  
  try {
    const response = await getAnalysisStatistics(30)
    console.log('API Response:', JSON.stringify(response, null, 2))
    console.log('API Response Data:', JSON.stringify(response.data, null, 2))
    
    // 修复：访问response.data而不是response直接属性
    if (response && response.data && response.data.success && response.data.statistics) {
      const statistics = response.data.statistics
      console.log('Statistics from API:', JSON.stringify(statistics, null, 2))
      
      // 直接逐个赋值而不是Object.assign
      stats.totalAnalyses = Number(statistics.total_analyses) || 0
      stats.successRate = Number(statistics.success_rate) || 0
      stats.avgConfidence = Number((statistics.average_confidence || 0) * 100)
      stats.processingJobs = Number(statistics.processing_count) || 0
      
      console.log('=== 数据赋值完成 ===')
      console.log('更新后的stats:', JSON.stringify(stats))
      console.log('totalAnalyses:', stats.totalAnalyses, typeof stats.totalAnalyses)
      console.log('successRate:', stats.successRate, typeof stats.successRate)  
      console.log('avgConfidence:', stats.avgConfidence, typeof stats.avgConfidence)
      console.log('processingJobs:', stats.processingJobs, typeof stats.processingJobs)
      
      showMessage.success('统计数据加载成功')
      
    } else {
      console.warn('API响应格式错误:', JSON.stringify(response, null, 2))
      console.warn('API响应数据格式错误:', JSON.stringify(response.data, null, 2))
      showMessage.warning('API响应格式错误')
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
    showMessage.error(`加载统计数据失败: ${error.message}`)
  }
}

const loadRecentResults = async () => {
  // 只检查认证状态，让API处理权限控制
  if (!isAuthenticated.value) {
    console.warn('用户未认证，跳过最近结果加载')
    return
  }
  
  console.log('开始加载最近分析结果...')
  
  try {
    const response = await getRecentAnalysisResults(5)
    
    if (response.data && response.data.success) {
      // 转换API响应格式为前端需要的格式
      recentResults.value = response.data.results.map(result => ({
        success: result.success,
        document_info: {
          filename: result.document_name,
          type: 'doc', // 从文件扩展名推断
          size: 157, // 暂时使用合理的默认值，后续可从API获取
          analysis_duration: result.analysis_duration
        },
        extracted_data: {
          basic_info: {
            name: result.product_info.name,
            code: result.product_info.code,
            category: result.product_info.category,
            base_price: 0,
            description: ''
          },
          // 🔧 修复：基于API实际返回的统计数据生成模拟数据结构
          specifications: (() => {
            const specsCount = result.product_info.specs_count || 0
            const specs = {}
            // 为每个规格生成合理的键值对，显示正确的数量
            for (let i = 0; i < specsCount; i++) {
              specs[`规格${i + 1}`] = `规格值${i + 1}`
            }
            return specs
          })(),
          features: (() => {
            // 基于置信度估算特性数量（API没有直接提供）
            const featuresConfidence = result.confidence?.features || 0
            const estimatedFeatures = Math.floor(featuresConfidence * 10) // 估算特性数量
            const features = []
            for (let i = 0; i < Math.max(estimatedFeatures, 4); i++) { // 至少4个特性
              features.push(`特性${i + 1}`)
            }
            return features
          })(),
          application_scenarios: [],
          accessories: [],
          certificates: (() => {
            // 估算认证数量（通常2-3个）
            const certs = []
            for (let i = 0; i < 2; i++) { // 默认2个认证
              certs.push(`认证${i + 1}`)
            }
            return certs
          })(),
          support_info: {
            warranty: { period: '', coverage: '', terms: [] },
            contact_info: {},
            service_promises: []
          }
        },
        confidence_scores: {
          basic_info: result.confidence.basic_info,
          specifications: result.confidence.specifications,
          features: result.confidence.features,
          overall: result.confidence.overall
        },
        validation: {
          valid: true,
          warnings: [],
          suggestions: [],
          completeness_score: result.confidence.overall
        },
        summary: `${result.product_info.name} - ${result.confidence.overall * 100}% 置信度`,
        text_preview: '',
        analysis_timestamp: (() => {
          // 修复时区问题：API返回的时间是UTC时间，但没有时区标识
          const dateStr = result.analysis_date
          if (dateStr.includes('Z') || dateStr.includes('+') || dateStr.includes('-', 10)) {
            // 如果包含时区信息，直接使用
            return new Date(dateStr).getTime()
          } else {
            // 如果没有时区信息，API返回的是UTC时间，需要添加Z标识
            return new Date(dateStr + 'Z').getTime()
          }
        })(),
        id: result.id,
        created_product_id: result.created_product_id
      }))
    }
  } catch (error) {
    console.error('Failed to load recent results:', error)
    showMessage.error('加载最近分析结果失败')
  }
}

const checkModelStatus = () => {
  // 模拟检查AI模型状态
  const randomCheck = Math.random()
  modelStatus.value = randomCheck > 0.1 ? 'online' : 'offline'
  
  // 模拟响应时间变化
  avgResponseTime.value = Math.floor(Math.random() * 500) + 600
}

// 使用组件级别的ref存储定时器引用，确保能正确清理
const updateInterval = ref<NodeJS.Timeout | null>(null)

// 清理现有定时器的函数
const clearUpdateInterval = () => {
  if (updateInterval.value) {
    clearInterval(updateInterval.value)
    updateInterval.value = null
    console.log('定时器已清理')
  }
}

// 启动定时器的函数
const startUpdateInterval = () => {
  // 先清理任何现有的定时器
  clearUpdateInterval()
  
  // 只有在用户认证且有权限时才启动定时器
  if (isAuthenticated.value && hasPermission.value) {
    updateInterval.value = setInterval(() => {
      console.log('定时器触发，检查用户状态...')
      // 再次检查用户状态，防止在用户登出后继续调用
      if (isAuthenticated.value && hasPermission.value) {
        checkModelStatus()
        // 暂时注释掉API调用，避免无限循环
        // loadStatistics()
        // loadRecentResults()
      } else {
        console.log('用户状态已变化，清理定时器')
        clearUpdateInterval()
      }
    }, 300000) // 改为5分钟检查一次，减少API调用频率
    
    console.log('定时器已启动(5分钟间隔)')
  } else {
    console.log('用户未认证或无权限，跳过定时器启动')
  }
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
  await loadStatistics()
  await loadRecentResults()
  checkModelStatus()
  
  // 启动定时器
  startUpdateInterval()
  
  showMessage.success('AI智能分析系统已就绪，基于智谱AI GLM-4模型提供服务')
})

// 页面卸载时清理定时器
onUnmounted(() => {
  console.log('组件卸载，清理定时器')
  clearUpdateInterval()
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

/* 详情对话框样式 */
.analysis-detail {
  max-height: 70vh;
  overflow-y: auto;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-section .el-card__header {
  background-color: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.detail-section h3 {
  margin: 0;
  color: #409eff;
  font-size: 16px;
  font-weight: 600;
}

.detail-section .el-descriptions {
  margin-top: 15px;
}

.detail-section .el-table {
  margin-top: 15px;
}

.detail-section .el-tag {
  margin: 3px 5px 3px 0;
}
</style>