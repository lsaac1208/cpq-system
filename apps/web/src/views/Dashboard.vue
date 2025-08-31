<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1>仪表盘</h1>
      <p>欢迎使用CPQ系统</p>
    </div>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon products">
              <el-icon><Box /></el-icon>
            </div>
            <div class="stat-info">
              <h3>{{ stats.products }}</h3>
              <p>活跃产品</p>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon quotes">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-info">
              <h3>{{ stats.quotes }}</h3>
              <p>总报价数</p>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon pending">
              <el-icon><Clock /></el-icon>
            </div>
            <div class="stat-info">
              <h3>{{ stats.pendingQuotes }}</h3>
              <p>待处理报价</p>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon revenue">
              <el-icon><Money /></el-icon>
            </div>
            <div class="stat-info">
              <h3>${{ stats.revenue.toLocaleString() }}</h3>
              <p>总收入</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="content-row">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最近报价</span>
              <router-link to="/quotes">
                <el-button type="primary" size="small">查看全部</el-button>
              </router-link>
            </div>
          </template>
          
          <el-table :data="recentQuotes" style="width: 100%" v-loading="loading">
            <el-table-column prop="quote_number" label="报价单号" width="120" />
            <el-table-column prop="customer_name" label="客户" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="final_price" label="金额" width="100">
              <template #default="{ row }">
                ${{ row.final_price?.toLocaleString() }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最近AI分析</span>
              <router-link to="/ai-analysis-enhanced">
                <el-button type="primary" size="small">查看全部</el-button>
              </router-link>
            </div>
          </template>
          
          <el-table :data="recentAnalysis" style="width: 100%" v-loading="loading">
            <el-table-column prop="document_name" label="文档名称" width="150">
              <template #default="{ row }">
                <el-tooltip :content="row.document_name" placement="top">
                  <span>{{ truncateText(row.document_name, 20) }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column label="分析结果" width="100">
              <template #default="{ row }">
                <span v-if="row.success && row.extracted_data?.basic_info?.name && !row.extracted_data.basic_info.name.includes('失败')">
                  {{ truncateText(row.extracted_data.basic_info.name, 15) }}
                </span>
                <el-tag v-else type="warning" size="small">解析异常</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="置信度" width="80">
              <template #default="{ row }">
                <el-tag 
                  :type="getConfidenceType(row.overall_confidence || 0)" 
                  size="small"
                >
                  {{ ((row.overall_confidence || 0) * 100).toFixed(0) }}%
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.success ? 'success' : 'danger'" size="small">
                  {{ row.success ? '成功' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="content-row">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>快捷操作</span>
            </div>
          </template>
          
          <div class="quick-actions">
            <router-link to="/quotes/create">
              <el-button type="primary" size="large" class="action-button">
                <el-icon><Plus /></el-icon>
                创建新报价
              </el-button>
            </router-link>

            <router-link to="/products">
              <el-button type="success" size="large" class="action-button">
                <el-icon><Box /></el-icon>
                管理产品
              </el-button>
            </router-link>

            <router-link to="/ai-analysis-enhanced">
              <el-button type="info" size="large" class="action-button">
                <el-icon><MagicStick /></el-icon>
                AI智能分析
              </el-button>
            </router-link>

            <router-link to="/quotes">
              <el-button type="warning" size="large" class="action-button">
                <el-icon><Document /></el-icon>
                查看所有报价
              </el-button>
            </router-link>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { quotesApi, multiQuotesApi } from '@/api/quotes'
import { productsApi } from '@/api/products'
import { getAnalysisHistory } from '@/api/ai-analysis'
import { Box, Document, Clock, Money, Plus, MagicStick } from '@element-plus/icons-vue'
import type { Quote } from '@/types/quote'
import type { AIAnalysisRecord } from '@/types/ai-analysis'

const loading = ref(false)
const recentQuotes = ref<Quote[]>([])
const recentAnalysis = ref<AIAnalysisRecord[]>([])

const stats = ref({
  products: 0,
  quotes: 0,
  pendingQuotes: 0,
  revenue: 0
})

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    draft: 'info',
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    expired: 'info'
  }
  return types[status] || 'info'
}

const getConfidenceType = (confidence: number): string => {
  if (confidence >= 0.8) return 'success'
  if (confidence >= 0.6) return 'warning'
  return 'danger'
}

const truncateText = (text: string, maxLength: number): string => {
  if (!text) return ''
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

const loadDashboardData = async () => {
  loading.value = true
  try {
    console.log('🚀 儀表板開始加載數據...')
    
    // 直接調用分別的API並手動合併
    console.log('📞 直接調用分別的API...')
    const [singleResult, multiResult] = await Promise.allSettled([
      quotesApi.getQuotes({ page: 1, per_page: 5 }),
      multiQuotesApi.getMultiQuotes({ page: 1, per_page: 5 })
    ])
    
    console.log('📊 分別API調用結果:')
    console.log('- 單產品結果:', singleResult)
    console.log('- 多產品結果:', multiResult)
    
    let allQuotes: Quote[] = []
    let totalQuotes = 0
    
    // 處理單產品結果
    if (singleResult.status === 'fulfilled' && singleResult.value?.data?.quotes) {
      console.log('✅ 單產品API成功，數量:', singleResult.value.data.quotes.length)
      allQuotes.push(...singleResult.value.data.quotes)
      totalQuotes += singleResult.value.data.pagination?.total || 0
    } else {
      console.error('❌ 單產品API失敗:', singleResult)
    }
    
    // 處理多產品結果
    if (multiResult.status === 'fulfilled' && multiResult.value?.data?.quotes) {
      console.log('✅ 多產品API成功，數量:', multiResult.value.data.quotes.length)
      allQuotes.push(...multiResult.value.data.quotes)
      totalQuotes += multiResult.value.data.pagination?.total || 0
    } else {
      console.error('❌ 多產品API失敗:', multiResult)
    }
    
    console.log('📋 合併後報價數量:', allQuotes.length)
    console.log('📋 總報價數:', totalQuotes)
    
    recentQuotes.value = allQuotes.slice(0, 5)
    console.log('📋 儀表板設置recentQuotes:', recentQuotes.value.length)

    // Load products count
    const productsResponse = await productsApi.getProducts({ page: 1, per_page: 1 })
    
    // Load recent AI analysis
    try {
      const analysisResponse = await getAnalysisHistory({ page: 1, per_page: 5 })
      recentAnalysis.value = analysisResponse?.records || []
    } catch (error) {
      console.warn('Failed to load AI analysis history:', error)
      recentAnalysis.value = []
    }
    
    // Calculate stats with merged data
    stats.value = {
      products: productsResponse?.pagination?.total || 0,
      quotes: totalQuotes,
      pendingQuotes: allQuotes.filter(q => q.status === 'pending').length,
      revenue: allQuotes
        .filter(q => q.status === 'approved')
        .reduce((sum, q) => sum + (q.final_price || q.total_price || 0), 0)
    }
    
    console.log('📊 最終統計數據:', stats.value)
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
    // Set default values on error
    stats.value = {
      products: 0,
      quotes: 0,
      pendingQuotes: 0,
      revenue: 0
    }
    recentQuotes.value = []
    recentAnalysis.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDashboardData()
})
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
}

.dashboard-header {
  margin-bottom: 30px;
}

.dashboard-header h1 {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 32px;
  font-weight: 600;
}

.dashboard-header p {
  margin: 0;
  color: #606266;
  font-size: 16px;
}

.stats-row {
  margin-bottom: 30px;
}

.stat-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.stat-icon.products {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.quotes {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.pending {
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
  color: #e6a23c;
}

.stat-icon.revenue {
  background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
  color: #67c23a;
}

.stat-info h3 {
  margin: 0 0 5px 0;
  color: #303133;
  font-size: 24px;
  font-weight: 600;
}

.stat-info p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.content-row .el-card {
  height: 400px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 15px;
  padding: 20px 0;
}

.action-button {
  width: 100%;
  height: 60px;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}
</style>