<template>
  <div class="market-analysis">
    <!-- 市场概览 -->
    <div class="market-overview">
      <el-row :gutter="24">
        <el-col :span="8">
          <el-card class="metric-card">
            <div class="metric-content">
              <div class="metric-icon trend">
                <el-icon><TrendCharts /></el-icon>
              </div>
              <div class="metric-info">
                <h3>市场趋势</h3>
                <p class="metric-value" :class="getTrendClass(marketContext.market_trend)">
                  {{ getTrendText(marketContext.market_trend) }}
                </p>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="8">
          <el-card class="metric-card">
            <div class="metric-content">
              <div class="metric-icon competition">
                <el-icon><Trophy /></el-icon>
              </div>
              <div class="metric-info">
                <h3>竞争强度</h3>
                <p class="metric-value" :class="getIntensityClass(marketContext.competition_intensity.level)">
                  {{ getIntensityText(marketContext.competition_intensity.level) }}
                </p>
                <p class="metric-detail">{{ marketContext.competition_intensity.competitor_count }} 个竞争对手</p>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="8">
          <el-card class="metric-card">
            <div class="metric-content">
              <div class="metric-icon demand">
                <el-icon><Opportunity /></el-icon>
              </div>
              <div class="metric-info">
                <h3>需求热度</h3>
                <p class="metric-value" :class="getHeatClass(marketContext.demand_heat.level)">
                  {{ getHeatText(marketContext.demand_heat.level) }}
                </p>
                <p class="metric-detail">{{ marketContext.demand_heat.total_demands }} 个需求点</p>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 详细分析 -->
    <div class="detailed-analysis">
      <el-row :gutter="24">
        <!-- 竞争分析 -->
        <el-col :span="12">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>竞争环境分析</span>
                <el-tag :type="getIntensityType(marketContext.competition_intensity.level)">
                  {{ getIntensityText(marketContext.competition_intensity.level) }}竞争
                </el-tag>
              </div>
            </template>
            
            <div class="competition-analysis">
              <!-- 竞争强度图表 -->
              <div class="competition-chart">
                <div class="chart-header">
                  <h4>竞争强度评分</h4>
                  <span class="score">{{ (marketContext.competition_intensity.score * 100).toFixed(0) }}分</span>
                </div>
                <el-progress 
                  :percentage="marketContext.competition_intensity.score * 100"
                  :color="getProgressColor(marketContext.competition_intensity.score)"
                  :stroke-width="20"
                />
              </div>

              <!-- 竞争对手特征 -->
              <div class="competitor-features">
                <h4>竞争对手特征</h4>
                <div class="feature-list">
                  <div class="feature-item">
                    <span class="feature-label">大型企业:</span>
                    <span class="feature-value">{{ marketContext.competition_intensity.analysis.large_enterprises }}</span>
                  </div>
                  <div class="feature-item">
                    <span class="feature-label">价格激进:</span>
                    <span class="feature-value">{{ marketContext.competition_intensity.analysis.pricing_aggressive }}</span>
                  </div>
                  <div class="feature-item">
                    <span class="feature-label">技术先进:</span>
                    <span class="feature-value">{{ marketContext.competition_intensity.analysis.technology_advanced }}</span>
                  </div>
                </div>
              </div>

              <!-- 竞争建议 -->
              <div class="competition-recommendations">
                <h4>竞争策略建议</h4>
                <ul>
                  <li v-if="marketContext.competition_intensity.level === 'high'">
                    采用差异化策略，避免正面价格竞争
                  </li>
                  <li v-if="marketContext.competition_intensity.level === 'high'">
                    强化产品优势和服务质量
                  </li>
                  <li v-if="marketContext.competition_intensity.level === 'medium'">
                    平衡价格竞争力与产品价值
                  </li>
                  <li v-if="marketContext.competition_intensity.level === 'low'">
                    可以采用溢价策略，建立市场领导地位
                  </li>
                </ul>
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- 市场机会分析 -->
        <el-col :span="12">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>市场机会分析</span>
                <el-tag :type="getOpportunityType(marketContext.market_opportunities.level)">
                  {{ getOpportunityText(marketContext.market_opportunities.level) }}机会
                </el-tag>
              </div>
            </template>
            
            <div class="opportunity-analysis">
              <!-- 机会评分 -->
              <div class="opportunity-chart">
                <div class="chart-header">
                  <h4>机会评分</h4>
                  <span class="score">{{ (marketContext.market_opportunities.score * 100).toFixed(0) }}分</span>
                </div>
                <el-progress 
                  :percentage="marketContext.market_opportunities.score * 100"
                  :color="getProgressColor(marketContext.market_opportunities.score)"
                  :stroke-width="20"
                />
              </div>

              <!-- 机会统计 -->
              <div class="opportunity-stats">
                <h4>机会统计</h4>
                <div class="stats-grid">
                  <div class="stat-item">
                    <span class="stat-number">{{ marketContext.market_opportunities.total_opportunities }}</span>
                    <span class="stat-label">总机会数</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-number">{{ marketContext.market_opportunities.high_value_opportunities }}</span>
                    <span class="stat-label">高价值机会</span>
                  </div>
                </div>
              </div>

              <!-- 主要机会 -->
              <div v-if="marketContext.market_opportunities.opportunities.length > 0" class="top-opportunities">
                <h4>主要机会</h4>
                <div class="opportunity-list">
                  <div 
                    v-for="(opp, index) in marketContext.market_opportunities.opportunities.slice(0, 3)" 
                    :key="index"
                    class="opportunity-item"
                  >
                    <div class="opportunity-content">
                      <span class="opportunity-title">机会 {{ index + 1 }}</span>
                      <p class="opportunity-description">{{ formatOpportunity(opp) }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 价格敏感度分析 -->
    <div class="price-sensitivity-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>价格敏感度分析</span>
            <el-tag :type="getSensitivityType(marketContext.price_sensitivity.level)">
              {{ getSensitivityText(marketContext.price_sensitivity.level) }}敏感
            </el-tag>
          </div>
        </template>
        
        <div class="sensitivity-analysis">
          <el-row :gutter="24">
            <el-col :span="8">
              <div class="sensitivity-chart">
                <h4>敏感度评分</h4>
                <el-progress 
                  type="circle"
                  :percentage="marketContext.price_sensitivity.score * 100"
                  :color="getProgressColor(1 - marketContext.price_sensitivity.score)"
                  :width="120"
                >
                  <template #default="{ percentage }">
                    <span class="score-text">{{ percentage.toFixed(0) }}%</span>
                  </template>
                </el-progress>
              </div>
            </el-col>
            
            <el-col :span="8">
              <div class="sensitivity-factors">
                <h4>影响因素</h4>
                <div class="factor-list">
                  <div class="factor-item">
                    <span class="factor-label">预算提及:</span>
                    <span class="factor-value">{{ marketContext.price_sensitivity.budget_mentions }} 次</span>
                  </div>
                  <div class="factor-item">
                    <span class="factor-label">成本关注:</span>
                    <span class="factor-value">{{ marketContext.price_sensitivity.cost_concerns }} 次</span>
                  </div>
                </div>
              </div>
            </el-col>
            
            <el-col :span="8">
              <div class="sensitivity-recommendations">
                <h4>定价建议</h4>
                <ul>
                  <li v-if="marketContext.price_sensitivity.level === 'high'">
                    采用成本导向定价，控制价格水平
                  </li>
                  <li v-if="marketContext.price_sensitivity.level === 'high'">
                    提供多档次产品组合
                  </li>
                  <li v-if="marketContext.price_sensitivity.level === 'medium'">
                    平衡价格与价值，强调性价比
                  </li>
                  <li v-if="marketContext.price_sensitivity.level === 'low'">
                    可以采用价值定价策略
                  </li>
                </ul>
              </div>
            </el-col>
          </el-row>
        </div>
      </el-card>
    </div>

    <!-- 需求热度分析 -->
    <div class="demand-analysis-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>需求热度分析</span>
            <el-tag :type="getHeatType(marketContext.demand_heat.level)">
              {{ getHeatText(marketContext.demand_heat.level) }}需求
            </el-tag>
          </div>
        </template>
        
        <div class="demand-analysis">
          <el-row :gutter="24">
            <el-col :span="12">
              <div class="demand-overview">
                <h4>需求概况</h4>
                <div class="demand-stats">
                  <div class="demand-stat">
                    <span class="stat-number">{{ marketContext.demand_heat.total_demands }}</span>
                    <span class="stat-label">总需求数</span>
                  </div>
                  <div class="demand-stat">
                    <span class="stat-number">{{ Object.keys(marketContext.demand_heat.product_categories).length }}</span>
                    <span class="stat-label">产品类别</span>
                  </div>
                </div>
                
                <div class="demand-score">
                  <h5>需求热度评分</h5>
                  <el-progress 
                    :percentage="marketContext.demand_heat.score * 100"
                    :color="getProgressColor(marketContext.demand_heat.score)"
                    :stroke-width="16"
                  />
                </div>
              </div>
            </el-col>
            
            <el-col :span="12">
              <div class="trending-products">
                <h4>热门产品类别</h4>
                <div v-if="marketContext.demand_heat.trending_products.length > 0" class="trending-list">
                  <div 
                    v-for="([category, count], index) in marketContext.demand_heat.trending_products" 
                    :key="category"
                    class="trending-item"
                  >
                    <div class="trending-rank">{{ index + 1 }}</div>
                    <div class="trending-info">
                      <span class="trending-category">{{ category }}</span>
                      <span class="trending-count">{{ count }} 个需求</span>
                    </div>
                    <div class="trending-bar">
                      <el-progress 
                        :percentage="(count / Math.max(...marketContext.demand_heat.trending_products.map(([,c]) => c))) * 100"
                        :show-text="false"
                        :stroke-width="8"
                      />
                    </div>
                  </div>
                </div>
                <div v-else class="no-trending">
                  <p>暂无热门产品类别数据</p>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps } from 'vue'
import { TrendCharts, Trophy, Opportunity } from '@element-plus/icons-vue'
import type { MarketContext } from '@/api/pricing-decision'

// 定义属性
defineProps<{
  marketContext: MarketContext
}>()

// 格式化机会信息
const formatOpportunity = (opportunity: any): string => {
  if (typeof opportunity === 'string') return opportunity
  if (typeof opportunity === 'object') {
    return opportunity.description || opportunity.title || JSON.stringify(opportunity)
  }
  return String(opportunity)
}

// 获取趋势相关样式和文本
const getTrendClass = (trend: string): string => {
  switch (trend) {
    case 'growing': return 'trend-growing'
    case 'stable': return 'trend-stable'
    case 'declining': return 'trend-declining'
    default: return 'trend-unknown'
  }
}

const getTrendText = (trend: string): string => {
  switch (trend) {
    case 'growing': return '增长中'
    case 'stable': return '稳定'
    case 'declining': return '下降'
    default: return '未知'
  }
}

// 获取竞争强度相关样式和文本
const getIntensityClass = (level: string): string => {
  switch (level) {
    case 'low': return 'intensity-low'
    case 'medium': return 'intensity-medium'
    case 'high': return 'intensity-high'
    default: return 'intensity-unknown'
  }
}

const getIntensityText = (level: string): string => {
  switch (level) {
    case 'low': return '低'
    case 'medium': return '中等'
    case 'high': return '激烈'
    default: return '未知'
  }
}

const getIntensityType = (level: string): string => {
  switch (level) {
    case 'low': return 'success'
    case 'medium': return 'warning'
    case 'high': return 'danger'
    default: return 'info'
  }
}

// 获取需求热度相关样式和文本
const getHeatClass = (level: string): string => {
  switch (level) {
    case 'low': return 'heat-low'
    case 'medium': return 'heat-medium'
    case 'high': return 'heat-high'
    default: return 'heat-unknown'
  }
}

const getHeatText = (level: string): string => {
  switch (level) {
    case 'low': return '较低'
    case 'medium': return '中等'
    case 'high': return '旺盛'
    default: return '未知'
  }
}

const getHeatType = (level: string): string => {
  switch (level) {
    case 'low': return 'info'
    case 'medium': return 'warning'
    case 'high': return 'success'
    default: return 'info'
  }
}

// 获取机会相关样式和文本
const getOpportunityText = (level: string): string => {
  switch (level) {
    case 'low': return '较少'
    case 'medium': return '中等'
    case 'high': return '丰富'
    default: return '未知'
  }
}

const getOpportunityType = (level: string): string => {
  switch (level) {
    case 'low': return 'info'
    case 'medium': return 'warning'
    case 'high': return 'success'
    default: return 'info'
  }
}

// 获取价格敏感度相关样式和文本
const getSensitivityText = (level: string): string => {
  switch (level) {
    case 'low': return '不'
    case 'medium': return '中等'
    case 'high': return '高度'
    default: return '未知'
  }
}

const getSensitivityType = (level: string): string => {
  switch (level) {
    case 'low': return 'success'
    case 'medium': return 'warning'
    case 'high': return 'danger'
    default: return 'info'
  }
}

// 获取进度条颜色
const getProgressColor = (score: number): string => {
  if (score >= 0.8) return '#67c23a'
  if (score >= 0.6) return '#e6a23c'
  if (score >= 0.4) return '#f56c6c'
  return '#909399'
}
</script>

<style scoped>
.market-analysis {
  padding: 16px 0;
}

.market-overview {
  margin-bottom: 24px;
}

.metric-card {
  height: 120px;
}

.metric-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.metric-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  font-size: 24px;
  color: white;
}

.metric-icon.trend {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.metric-icon.competition {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.metric-icon.demand {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.metric-info h3 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #909399;
  font-weight: 500;
}

.metric-value {
  margin: 0 0 4px 0;
  font-size: 20px;
  font-weight: 600;
}

.metric-detail {
  margin: 0;
  font-size: 12px;
  color: #909399;
}

/* 趋势颜色 */
.trend-growing { color: #67c23a; }
.trend-stable { color: #409eff; }
.trend-declining { color: #f56c6c; }

/* 竞争强度颜色 */
.intensity-low { color: #67c23a; }
.intensity-medium { color: #e6a23c; }
.intensity-high { color: #f56c6c; }

/* 需求热度颜色 */
.heat-low { color: #909399; }
.heat-medium { color: #e6a23c; }
.heat-high { color: #67c23a; }

.detailed-analysis {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.competition-analysis,
.opportunity-analysis {
  padding: 16px 0;
}

.competition-chart,
.opportunity-chart {
  margin-bottom: 24px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.chart-header h4 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.score {
  font-size: 18px;
  font-weight: 600;
  color: #409eff;
}

.competitor-features,
.opportunity-stats {
  margin-bottom: 24px;
}

.competitor-features h4,
.opportunity-stats h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #606266;
}

.feature-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.feature-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 4px;
}

.feature-label {
  color: #909399;
  font-size: 13px;
}

.feature-value {
  color: #303133;
  font-weight: 500;
  font-size: 13px;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.stat-number {
  display: block;
  font-size: 24px;
  font-weight: 600;
  color: #409eff;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

.competition-recommendations,
.top-opportunities {
  margin-top: 16px;
}

.competition-recommendations h4,
.top-opportunities h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #606266;
}

.competition-recommendations ul {
  margin: 0;
  padding-left: 20px;
}

.competition-recommendations li {
  margin-bottom: 8px;
  color: #606266;
  font-size: 13px;
  line-height: 1.5;
}

.opportunity-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.opportunity-item {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.opportunity-title {
  font-size: 13px;
  font-weight: 500;
  color: #409eff;
}

.opportunity-description {
  margin: 4px 0 0 0;
  font-size: 12px;
  color: #606266;
  line-height: 1.4;
}

.price-sensitivity-section,
.demand-analysis-section {
  margin-bottom: 24px;
}

.sensitivity-analysis,
.demand-analysis {
  padding: 16px 0;
}

.sensitivity-chart {
  text-align: center;
}

.sensitivity-chart h4 {
  margin: 0 0 16px 0;
  font-size: 14px;
  color: #606266;
}

.score-text {
  font-size: 16px;
  font-weight: 600;
}

.sensitivity-factors h4,
.sensitivity-recommendations h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #606266;
}

.factor-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.factor-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 4px;
}

.factor-label {
  color: #909399;
  font-size: 13px;
}

.factor-value {
  color: #303133;
  font-weight: 500;
  font-size: 13px;
}

.sensitivity-recommendations ul {
  margin: 0;
  padding-left: 20px;
}

.sensitivity-recommendations li {
  margin-bottom: 8px;
  color: #606266;
  font-size: 13px;
  line-height: 1.5;
}

.demand-overview h4,
.trending-products h4 {
  margin: 0 0 16px 0;
  font-size: 14px;
  color: #606266;
}

.demand-stats {
  display: flex;
  gap: 24px;
  margin-bottom: 20px;
}

.demand-stat {
  text-align: center;
}

.demand-score h5 {
  margin: 0 0 12px 0;
  font-size: 13px;
  color: #909399;
}

.trending-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.trending-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.trending-rank {
  width: 24px;
  height: 24px;
  background: #409eff;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.trending-info {
  flex: 1;
  min-width: 0;
}

.trending-category {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 2px;
}

.trending-count {
  font-size: 11px;
  color: #909399;
}

.trending-bar {
  width: 100px;
  flex-shrink: 0;
}

.no-trending {
  text-align: center;
  padding: 40px 20px;
  color: #909399;
}

@media (max-width: 768px) {
  .detailed-analysis .el-col,
  .sensitivity-analysis .el-col,
  .demand-analysis .el-col {
    margin-bottom: 16px;
  }

  .demand-stats {
    flex-direction: column;
    gap: 16px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>