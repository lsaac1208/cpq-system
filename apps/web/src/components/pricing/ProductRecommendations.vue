<template>
  <div class="product-recommendations">
    <div v-if="recommendations.length === 0" class="empty-state">
      <el-empty description="暂无产品推荐">
        <el-button type="primary" @click="$emit('refresh')">
          刷新数据
        </el-button>
      </el-empty>
    </div>

    <div v-else class="recommendations-list">
      <div 
        v-for="(rec, index) in recommendations" 
        :key="rec.product.id"
        class="recommendation-card"
      >
        <el-card shadow="hover">
          <div class="recommendation-header">
            <div class="product-info">
              <h3 class="product-name">{{ rec.product.name }}</h3>
              <p class="product-code">型号: {{ rec.product.code }}</p>
              <p class="product-category">类别: {{ rec.product.category }}</p>
            </div>
            <div class="match-score">
              <el-progress 
                type="circle" 
                :percentage="Math.round(rec.match_score * 100)"
                :color="getScoreColor(rec.match_score)"
                :width="80"
              >
                <template #default="{ percentage }">
                  <span class="score-text">{{ percentage }}%</span>
                </template>
              </el-progress>
              <p class="score-label">匹配度</p>
            </div>
          </div>

          <div class="recommendation-content">
            <!-- 产品描述 -->
            <div class="product-description">
              <p>{{ rec.product.description }}</p>
            </div>

            <!-- 匹配原因 -->
            <div class="match-reasons">
              <h4>匹配原因</h4>
              <ul>
                <li v-for="reason in rec.match_reasons" :key="reason">
                  {{ reason }}
                </li>
              </ul>
            </div>

            <!-- 价格信息 -->
            <div class="pricing-info">
              <h4>价格建议</h4>
              <div class="price-comparison">
                <div class="price-item">
                  <span class="price-label">基础价格:</span>
                  <span class="price-value">¥{{ formatPrice(rec.recommended_price.base_price) }}</span>
                </div>
                <div class="price-item">
                  <span class="price-label">建议价格:</span>
                  <span class="price-value recommended">¥{{ formatPrice(rec.recommended_price.recommended_price) }}</span>
                </div>
                <div class="price-item">
                  <span class="price-label">调整幅度:</span>
                  <span 
                    class="price-change"
                    :class="rec.recommended_price.price_change_percentage >= 0 ? 'positive' : 'negative'"
                  >
                    {{ rec.recommended_price.price_change_percentage > 0 ? '+' : '' }}{{ rec.recommended_price.price_change_percentage }}%
                  </span>
                </div>
              </div>
              
              <!-- 价格调整原因 -->
              <div class="adjustment-reasons">
                <h5>调整原因:</h5>
                <ul>
                  <li v-for="reason in rec.recommended_price.adjustment_reasons" :key="reason">
                    {{ reason }}
                  </li>
                </ul>
              </div>
            </div>

            <!-- 配置建议 -->
            <div v-if="Object.keys(rec.config_recommendations).length > 0" class="config-recommendations">
              <h4>配置建议</h4>
              <div class="config-items">
                <div 
                  v-for="(value, key) in rec.config_recommendations" 
                  :key="key"
                  class="config-item"
                >
                  <span class="config-key">{{ key }}:</span>
                  <span class="config-value">{{ value }}</span>
                </div>
              </div>
            </div>

            <!-- 定价策略 -->
            <div class="pricing-strategy">
              <h4>推荐策略</h4>
              <div v-if="rec.pricing_strategy.primary_strategy" class="primary-strategy">
                <div class="strategy-card">
                  <div class="strategy-header">
                    <span class="strategy-name">{{ rec.pricing_strategy.primary_strategy.name }}</span>
                    <el-tag 
                      :type="getStrategyRiskType(rec.pricing_strategy.primary_strategy.risk_level)"
                      size="small"
                    >
                      {{ rec.pricing_strategy.primary_strategy.risk_level }} 风险
                    </el-tag>
                  </div>
                  <p class="strategy-description">{{ rec.pricing_strategy.primary_strategy.description }}</p>
                </div>
              </div>

              <!-- 其他策略选项 -->
              <div v-if="rec.pricing_strategy.recommended_strategies.length > 1" class="alternative-strategies">
                <h5>备选策略:</h5>
                <div class="strategy-list">
                  <div 
                    v-for="strategy in rec.pricing_strategy.recommended_strategies.slice(1)" 
                    :key="strategy.name"
                    class="strategy-item"
                  >
                    <span class="strategy-name">{{ strategy.name }}</span>
                    <span class="strategy-description">{{ strategy.description }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="recommendation-actions">
            <el-button 
              type="primary"
              @click="createQuote(rec)"
              icon="Plus"
            >
              创建报价
            </el-button>
            <el-button 
              @click="viewProductDetails(rec.product)"
              icon="View"
            >
              查看详情
            </el-button>
            <el-button 
              @click="compareProduct(rec)"
              icon="TrendCharts"
            >
              对比分析
            </el-button>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, View, TrendCharts } from '@element-plus/icons-vue'
import type { ProductRecommendation } from '@/api/pricing-decision'

// 定义属性
defineProps<{
  recommendations: ProductRecommendation[]
}>()

// 定义事件
const emit = defineEmits<{
  'create-quote': [recommendation: ProductRecommendation]
  'view-product': [product: any]
  'compare-product': [recommendation: ProductRecommendation]
  'refresh': []
}>()

// 创建报价
const createQuote = (recommendation: ProductRecommendation) => {
  emit('create-quote', recommendation)
}

// 查看产品详情
const viewProductDetails = (product: any) => {
  emit('view-product', product)
  // 可以跳转到产品详情页
  // router.push(`/products/${product.id}`)
}

// 对比产品
const compareProduct = (recommendation: ProductRecommendation) => {
  emit('compare-product', recommendation)
  ElMessage.info('产品对比功能正在开发中')
}

// 格式化价格
const formatPrice = (price: number): string => {
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(price)
}

// 获取评分颜色
const getScoreColor = (score: number): string => {
  if (score >= 0.8) return '#67c23a'
  if (score >= 0.6) return '#e6a23c'
  return '#f56c6c'
}

// 获取策略风险类型
const getStrategyRiskType = (riskLevel: string): string => {
  switch (riskLevel) {
    case 'low': return 'success'
    case 'medium': return 'warning'
    case 'high': return 'danger'
    default: return 'info'
  }
}
</script>

<style scoped>
.product-recommendations {
  padding: 16px 0;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.recommendations-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.recommendation-card {
  width: 100%;
}

.recommendation-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.product-info {
  flex: 1;
}

.product-name {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.product-code,
.product-category {
  margin: 4px 0;
  color: #909399;
  font-size: 14px;
}

.match-score {
  text-align: center;
}

.score-text {
  font-size: 14px;
  font-weight: 600;
}

.score-label {
  margin: 8px 0 0 0;
  font-size: 12px;
  color: #909399;
}

.recommendation-content {
  margin-bottom: 24px;
}

.product-description {
  margin-bottom: 20px;
}

.product-description p {
  color: #606266;
  line-height: 1.6;
  margin: 0;
}

.match-reasons,
.pricing-info,
.config-recommendations,
.pricing-strategy {
  margin-bottom: 20px;
}

.match-reasons h4,
.pricing-info h4,
.config-recommendations h4,
.pricing-strategy h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.match-reasons ul {
  margin: 0;
  padding-left: 20px;
}

.match-reasons li {
  margin-bottom: 4px;
  color: #606266;
  line-height: 1.5;
}

.price-comparison {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.price-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.price-label {
  color: #909399;
  font-size: 14px;
}

.price-value {
  font-weight: 600;
  font-size: 16px;
  color: #303133;
}

.price-value.recommended {
  color: #409eff;
  font-size: 18px;
}

.price-change {
  font-weight: 600;
  font-size: 14px;
}

.price-change.positive {
  color: #67c23a;
}

.price-change.negative {
  color: #f56c6c;
}

.adjustment-reasons {
  margin-top: 12px;
}

.adjustment-reasons h5 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #606266;
}

.adjustment-reasons ul {
  margin: 0;
  padding-left: 20px;
}

.adjustment-reasons li {
  margin-bottom: 4px;
  color: #606266;
  font-size: 13px;
  line-height: 1.4;
}

.config-items {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 12px;
}

.config-item {
  display: flex;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 4px;
}

.config-key {
  color: #909399;
  font-size: 13px;
  margin-right: 8px;
}

.config-value {
  color: #303133;
  font-size: 13px;
  font-weight: 500;
}

.primary-strategy {
  margin-bottom: 16px;
}

.strategy-card {
  padding: 16px;
  background: #f0f9ff;
  border: 1px solid #e1f5fe;
  border-radius: 8px;
}

.strategy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.strategy-name {
  font-weight: 600;
  color: #303133;
}

.strategy-description {
  margin: 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

.alternative-strategies h5 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #606266;
}

.strategy-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.strategy-item {
  display: flex;
  flex-direction: column;
  padding: 8px 12px;
  background: #fafafa;
  border-radius: 4px;
}

.strategy-item .strategy-name {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.strategy-item .strategy-description {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
}

.recommendation-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

@media (max-width: 768px) {
  .recommendation-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .match-score {
    margin-top: 16px;
  }

  .price-comparison {
    grid-template-columns: 1fr;
  }

  .config-items {
    grid-template-columns: 1fr;
  }

  .recommendation-actions {
    flex-direction: column;
  }
}
</style>