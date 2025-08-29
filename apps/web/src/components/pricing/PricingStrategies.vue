<template>
  <div class="pricing-strategies">
    <!-- 整体策略 -->
    <div class="overall-strategy-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>推荐定价策略</span>
            <el-tag 
              :type="getStrategyType(strategies.overall_strategy.strategy)"
              size="large"
            >
              {{ getStrategyName(strategies.overall_strategy.strategy) }}
            </el-tag>
          </div>
        </template>
        
        <div class="strategy-content">
          <div class="strategy-description">
            <p>{{ strategies.overall_strategy.description }}</p>
          </div>
          
          <div class="success-probability">
            <h4>成功概率评估</h4>
            <el-progress 
              :percentage="strategies.overall_strategy.success_probability * 100"
              :color="getSuccessColor(strategies.overall_strategy.success_probability)"
              :stroke-width="20"
            >
              <template #default="{ percentage }">
                <span class="probability-text">{{ percentage.toFixed(1) }}%</span>
              </template>
            </el-progress>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 策略详情 -->
    <div class="strategy-details">
      <el-row :gutter="24">
        <!-- 打包销售机会 -->
        <el-col :span="12">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>打包销售机会</span>
                <el-tag 
                  :type="strategies.bundle_opportunities.length > 0 ? 'success' : 'info'"
                  size="small"
                >
                  {{ strategies.bundle_opportunities.length }} 个机会
                </el-tag>
              </div>
            </template>
            
            <div class="bundle-section">
              <div v-if="strategies.bundle_opportunities.length === 0" class="empty-state">
                <el-empty description="暂无打包销售机会" :image-size="80" />
              </div>
              
              <div v-else class="bundle-list">
                <div 
                  v-for="(bundle, index) in strategies.bundle_opportunities" 
                  :key="index"
                  class="bundle-item"
                >
                  <div class="bundle-header">
                    <h4>{{ bundle.category }} 解决方案</h4>
                    <el-tag type="success" size="small">
                      {{ bundle.estimated_discount }} 折扣
                    </el-tag>
                  </div>
                  
                  <div class="bundle-products">
                    <h5>包含产品:</h5>
                    <ul>
                      <li v-for="product in bundle.products" :key="product">
                        {{ product }}
                      </li>
                    </ul>
                  </div>
                  
                  <div class="bundle-value">
                    <p class="value-proposition">
                      <el-icon><Star /></el-icon>
                      {{ bundle.value_proposition }}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- 折扣建议 -->
        <el-col :span="12">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>折扣策略建议</span>
                <el-tag type="warning" size="small">灵活定价</el-tag>
              </div>
            </template>
            
            <div class="discount-section">
              <!-- 批量折扣 -->
              <div class="discount-type">
                <h4>
                  <el-icon><TrendCharts /></el-icon>
                  批量折扣
                </h4>
                <div class="discount-details">
                  <div class="discount-rule">
                    <span class="rule-label">数量阈值:</span>
                    <span class="rule-value">{{ strategies.discount_recommendations.volume_discount.threshold }} 件</span>
                  </div>
                  <div class="discount-rule">
                    <span class="rule-label">折扣范围:</span>
                    <span class="rule-value">{{ strategies.discount_recommendations.volume_discount.discount_range }}</span>
                  </div>
                </div>
              </div>

              <!-- 早鸟折扣 -->
              <div class="discount-type">
                <h4>
                  <el-icon><Clock /></el-icon>
                  早鸟折扣
                </h4>
                <div class="discount-details">
                  <div class="discount-rule">
                    <span class="rule-label">有效期:</span>
                    <span class="rule-value">{{ strategies.discount_recommendations.early_bird_discount.duration }}</span>
                  </div>
                  <div class="discount-rule">
                    <span class="rule-label">折扣幅度:</span>
                    <span class="rule-value">{{ strategies.discount_recommendations.early_bird_discount.discount }}</span>
                  </div>
                </div>
              </div>

              <!-- 折扣条件 -->
              <div class="discount-conditions">
                <h4>重要条件</h4>
                <ul>
                  <li v-for="condition in strategies.discount_recommendations.conditions" :key="condition">
                    {{ condition }}
                  </li>
                </ul>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 时机考虑 -->
    <div class="timing-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>时机策略分析</span>
            <el-tag 
              :type="getTimingType(strategies.timing_considerations.market_window)"
              size="small"
            >
              {{ getTimingText(strategies.timing_considerations.market_window) }}窗口期
            </el-tag>
          </div>
        </template>
        
        <div class="timing-content">
          <el-row :gutter="24">
            <el-col :span="6">
              <div class="timing-card">
                <div class="timing-icon optimal">
                  <el-icon><Timer /></el-icon>
                </div>
                <h4>最佳时机</h4>
                <p>{{ strategies.timing_considerations.optimal_timing }}</p>
              </div>
            </el-col>
            
            <el-col :span="6">
              <div class="timing-card">
                <div class="timing-icon window">
                  <el-icon><Calendar /></el-icon>
                </div>
                <h4>市场窗口</h4>
                <p>{{ getTimingText(strategies.timing_considerations.market_window) }}机会期</p>
              </div>
            </el-col>
            
            <el-col :span="6">
              <div class="timing-card">
                <div class="timing-icon seasonal">
                  <el-icon><Sunny /></el-icon>
                </div>
                <h4>季节因素</h4>
                <p>{{ strategies.timing_considerations.seasonal_factors }}</p>
              </div>
            </el-col>
            
            <el-col :span="6">
              <div class="timing-card">
                <div class="timing-icon urgency">
                  <el-icon><Warning /></el-icon>
                </div>
                <h4>紧急信号</h4>
                <p>{{ strategies.timing_considerations.urgency_indicators.length || 0 }} 个信号</p>
              </div>
            </el-col>
          </el-row>

          <!-- 紧急性指标 -->
          <div v-if="strategies.timing_considerations.urgency_indicators.length > 0" class="urgency-indicators">
            <h4>紧急性指标</h4>
            <div class="indicator-list">
              <el-tag 
                v-for="indicator in strategies.timing_considerations.urgency_indicators" 
                :key="indicator"
                type="warning"
                class="indicator-tag"
              >
                {{ indicator }}
              </el-tag>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 策略实施建议 -->
    <div class="implementation-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>实施建议</span>
            <el-tag type="primary" size="small">行动指南</el-tag>
          </div>
        </template>
        
        <div class="implementation-content">
          <div class="implementation-steps">
            <div class="step-item">
              <div class="step-number">1</div>
              <div class="step-content">
                <h4>策略选择</h4>
                <p>基于市场分析结果，采用 <strong>{{ getStrategyName(strategies.overall_strategy.strategy) }}</strong> 策略</p>
              </div>
            </div>

            <div class="step-item">
              <div class="step-number">2</div>
              <div class="step-content">
                <h4>价格设定</h4>
                <p>根据产品推荐中的建议价格进行定价，考虑市场竞争和客户价格敏感度</p>
              </div>
            </div>

            <div class="step-item">
              <div class="step-number">3</div>
              <div class="step-content">
                <h4>折扣应用</h4>
                <p>合理运用批量折扣和早鸟折扣，避免过度价格竞争</p>
              </div>
            </div>

            <div class="step-item">
              <div class="step-number">4</div>
              <div class="step-content">
                <h4>时机把握</h4>
                <p>在{{ getTimingText(strategies.timing_considerations.market_window) }}市场窗口期内实施策略</p>
              </div>
            </div>
          </div>

          <div class="key-success-factors">
            <h4>成功关键因素</h4>
            <div class="success-factors">
              <el-tag 
                v-for="factor in getKeySuccessFactors(strategies.overall_strategy.strategy)" 
                :key="factor"
                type="success"
                class="factor-tag"
              >
                {{ factor }}
              </el-tag>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps } from 'vue'
import { 
  Star, TrendCharts, Clock, Timer, Calendar, Sunny, Warning 
} from '@element-plus/icons-vue'
import type { PricingStrategies } from '@/api/pricing-decision'

// 定义属性
defineProps<{
  strategies: PricingStrategies
}>()

// 获取策略类型样式
const getStrategyType = (strategy: string): string => {
  switch (strategy) {
    case 'value_based_pricing': return 'primary'
    case 'aggressive_pricing': return 'danger'
    case 'premium_pricing': return 'success'
    case 'market_penetration': return 'warning'
    default: return 'info'
  }
}

// 获取策略名称
const getStrategyName = (strategy: string): string => {
  switch (strategy) {
    case 'value_based_pricing': return '价值定价'
    case 'aggressive_pricing': return '积极定价'
    case 'premium_pricing': return '溢价定价'
    case 'market_penetration': return '市场渗透'
    default: return '标准定价'
  }
}

// 获取成功概率颜色
const getSuccessColor = (probability: number): string => {
  if (probability >= 0.8) return '#67c23a'
  if (probability >= 0.6) return '#e6a23c'
  return '#f56c6c'
}

// 获取时机类型和文本
const getTimingType = (window: string): string => {
  switch (window) {
    case 'excellent': return 'success'
    case 'good': return 'primary'
    case 'challenging': return 'warning'
    default: return 'info'
  }
}

const getTimingText = (window: string): string => {
  switch (window) {
    case 'excellent': return '绝佳'
    case 'good': return '良好'
    case 'challenging': return '挑战'
    default: return '一般'
  }
}

// 获取关键成功因素
const getKeySuccessFactors = (strategy: string): string[] => {
  switch (strategy) {
    case 'value_based_pricing':
      return ['产品价值展示', '客户需求匹配', '服务质量', 'ROI论证']
    case 'aggressive_pricing':
      return ['成本控制', '运营效率', '规模优势', '快速响应']
    case 'premium_pricing':
      return ['品牌建设', '产品差异化', '技术创新', '客户体验']
    case 'market_penetration':
      return ['市场份额', '客户获取', '渠道建设', '竞争分析']
    default:
      return ['产品质量', '客户服务', '价格竞争力', '市场定位']
  }
}
</script>

<style scoped>
.pricing-strategies {
  padding: 16px 0;
}

.overall-strategy-section {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.strategy-content {
  padding: 16px 0;
}

.strategy-description {
  margin-bottom: 24px;
}

.strategy-description p {
  font-size: 16px;
  color: #606266;
  line-height: 1.6;
  margin: 0;
}

.success-probability h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #303133;
}

.probability-text {
  font-size: 14px;
  font-weight: 600;
}

.strategy-details {
  margin-bottom: 24px;
}

.bundle-section,
.discount-section {
  padding: 16px 0;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
}

.bundle-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.bundle-item {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #67c23a;
}

.bundle-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.bundle-header h4 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.bundle-products {
  margin-bottom: 12px;
}

.bundle-products h5 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #606266;
}

.bundle-products ul {
  margin: 0;
  padding-left: 20px;
}

.bundle-products li {
  margin-bottom: 4px;
  color: #606266;
  font-size: 13px;
}

.bundle-value {
  margin-top: 12px;
}

.value-proposition {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #67c23a;
  font-weight: 500;
}

.discount-type {
  margin-bottom: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.discount-type h4 {
  margin: 0 0 12px 0;
  font-size: 15px;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.discount-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.discount-rule {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.rule-label {
  color: #909399;
  font-size: 13px;
}

.rule-value {
  color: #303133;
  font-weight: 500;
  font-size: 13px;
}

.discount-conditions {
  margin-top: 20px;
}

.discount-conditions h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #606266;
}

.discount-conditions ul {
  margin: 0;
  padding-left: 20px;
}

.discount-conditions li {
  margin-bottom: 6px;
  color: #606266;
  font-size: 13px;
  line-height: 1.4;
}

.timing-section {
  margin-bottom: 24px;
}

.timing-content {
  padding: 16px 0;
}

.timing-card {
  text-align: center;
  padding: 20px 16px;
  background: #f8f9fa;
  border-radius: 8px;
  height: 120px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.timing-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 12px auto;
  font-size: 18px;
  color: white;
}

.timing-icon.optimal {
  background: #67c23a;
}

.timing-icon.window {
  background: #409eff;
}

.timing-icon.seasonal {
  background: #e6a23c;
}

.timing-icon.urgency {
  background: #f56c6c;
}

.timing-card h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #303133;
}

.timing-card p {
  margin: 0;
  font-size: 12px;
  color: #606266;
  line-height: 1.4;
}

.urgency-indicators {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #ebeef5;
}

.urgency-indicators h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #303133;
}

.indicator-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.indicator-tag {
  margin: 0;
}

.implementation-section {
  margin-bottom: 24px;
}

.implementation-content {
  padding: 16px 0;
}

.implementation-steps {
  margin-bottom: 32px;
}

.step-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 24px;
}

.step-number {
  width: 32px;
  height: 32px;
  background: #409eff;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  margin-right: 16px;
  flex-shrink: 0;
}

.step-content {
  flex: 1;
}

.step-content h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: #303133;
}

.step-content p {
  margin: 0;
  color: #606266;
  line-height: 1.5;
}

.key-success-factors h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #303133;
}

.success-factors {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.factor-tag {
  margin: 0;
}

@media (max-width: 768px) {
  .strategy-details .el-col {
    margin-bottom: 16px;
  }

  .timing-content .el-col {
    margin-bottom: 16px;
  }

  .timing-card {
    height: auto;
    padding: 16px;
  }

  .step-item {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .step-number {
    margin-right: 0;
    margin-bottom: 12px;
  }
}
</style>