<template>
  <div class="competitor-analysis-view">
    <div class="analysis-header">
      <h3 class="analysis-title">
        <el-icon><TrendCharts /></el-icon>
        竞品分析结果
      </h3>
    </div>
    
    <el-row :gutter="20">
      <!-- 竞争对手基本信息 -->
      <el-col :span="12">
        <el-card class="info-section" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon class="section-icon"><OfficeBuilding /></el-icon>
              <span class="section-title">竞争对手信息</span>
            </div>
          </template>
          
          <div class="info-content">
            <div v-if="data.competitor_info.company_name" class="info-item">
              <span class="info-label">公司名称:</span>
              <span class="info-value company-name">{{ data.competitor_info.company_name }}</span>
            </div>
            
            <div v-if="data.competitor_info.product_name" class="info-item">
              <span class="info-label">产品名称:</span>
              <span class="info-value product-name">{{ data.competitor_info.product_name }}</span>
            </div>
            
            <div v-if="data.competitor_info.market_position" class="info-item">
              <span class="info-label">市场地位:</span>
              <el-tag :type="getPositionType(data.competitor_info.market_position)" size="small">
                {{ data.competitor_info.market_position }}
              </el-tag>
            </div>
            
            <div v-if="data.competitor_info.key_strengths?.length" class="info-item">
              <span class="info-label">主要优势:</span>
              <ul class="strengths-list">
                <li v-for="strength in data.competitor_info.key_strengths" :key="strength">
                  <el-icon class="strength-icon"><CircleCheckFilled /></el-icon>
                  {{ strength }}
                </li>
              </ul>
            </div>
            
            <div v-if="data.competitor_info.weaknesses?.length" class="info-item">
              <span class="info-label">主要弱点:</span>
              <ul class="weaknesses-list">
                <li v-for="weakness in data.competitor_info.weaknesses" :key="weakness">
                  <el-icon class="weakness-icon"><CircleCloseFilled /></el-icon>
                  {{ weakness }}
                </li>
              </ul>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <!-- 价格分析 -->
      <el-col :span="12">
        <el-card class="pricing-section" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon class="section-icon"><Money /></el-icon>
              <span class="section-title">价格分析</span>
            </div>
          </template>
          
          <div class="pricing-content">
            <div v-if="data.pricing_analysis.base_price" class="pricing-item">
              <div class="price-display">
                <span class="price-label">基础价格</span>
                <span class="price-value">{{ formatPrice(data.pricing_analysis.base_price) }}</span>
              </div>
            </div>
            
            <div v-if="data.pricing_analysis.total_cost_of_ownership" class="pricing-item">
              <div class="price-display">
                <span class="price-label">总拥有成本</span>
                <span class="price-value tco">{{ formatPrice(data.pricing_analysis.total_cost_of_ownership) }}</span>
              </div>
            </div>
            
            <div v-if="data.pricing_analysis.pricing_model" class="pricing-item">
              <span class="info-label">定价模式:</span>
              <el-tag type="info" size="small">{{ data.pricing_analysis.pricing_model }}</el-tag>
            </div>
            
            <div v-if="data.pricing_analysis.discount_structure" class="pricing-item">
              <span class="info-label">折扣结构:</span>
              <span class="info-value">{{ data.pricing_analysis.discount_structure }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 技术对比 -->
      <el-col :span="24">
        <el-card class="technical-section" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon class="section-icon"><Monitor /></el-icon>
              <span class="section-title">技术对比</span>
            </div>
          </template>
          
          <div class="technical-content">
            <el-row :gutter="20">
              <!-- 技术规格 -->
              <el-col :span="8" v-if="data.technical_comparison.specifications">
                <h4 class="sub-title">技术规格</h4>
                <div class="specs-list">
                  <div 
                    v-for="(value, key) in data.technical_comparison.specifications" 
                    :key="key"
                    class="spec-item"
                  >
                    <span class="spec-name">{{ key }}:</span>
                    <span class="spec-value">{{ value }}</span>
                  </div>
                </div>
              </el-col>
              
              <!-- 性能基准 -->
              <el-col :span="8" v-if="data.technical_comparison.performance_benchmarks">
                <h4 class="sub-title">性能基准</h4>
                <div class="benchmarks-list">
                  <div 
                    v-for="(value, key) in data.technical_comparison.performance_benchmarks" 
                    :key="key"
                    class="benchmark-item"
                  >
                    <span class="benchmark-name">{{ key }}:</span>
                    <span class="benchmark-value">{{ value }}{{ getBenchmarkUnit(key) }}</span>
                  </div>
                </div>
              </el-col>
              
              <!-- 功能矩阵 -->
              <el-col :span="8" v-if="data.technical_comparison.feature_matrix">
                <h4 class="sub-title">功能矩阵</h4>
                <div class="features-list">
                  <div 
                    v-for="(value, key) in data.technical_comparison.feature_matrix" 
                    :key="key"
                    class="feature-item"
                  >
                    <span class="feature-name">{{ key }}:</span>
                    <el-icon 
                      v-if="typeof value === 'boolean'"
                      :class="value ? 'feature-yes' : 'feature-no'"
                    >
                      <component :is="value ? 'CircleCheckFilled' : 'CircleCloseFilled'" />
                    </el-icon>
                    <span v-else class="feature-value">{{ value }}</span>
                  </div>
                </div>
              </el-col>
            </el-row>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 市场情报 -->
      <el-col :span="12" v-if="hasMarketIntelligence">
        <el-card class="market-section" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon class="section-icon"><DataAnalysis /></el-icon>
              <span class="section-title">市场情报</span>
            </div>
          </template>
          
          <div class="market-content">
            <div v-if="data.market_intelligence?.market_share" class="market-item">
              <span class="info-label">市场份额:</span>
              <div class="market-share">
                <el-progress 
                  :percentage="data.market_intelligence.market_share" 
                  :color="getMarketShareColor(data.market_intelligence.market_share)"
                />
              </div>
            </div>
            
            <div v-if="data.market_intelligence?.customer_feedback?.length" class="market-item">
              <span class="info-label">客户反馈:</span>
              <ul class="feedback-list">
                <li v-for="feedback in data.market_intelligence.customer_feedback" :key="feedback">
                  <el-icon class="feedback-icon"><ChatLineSquare /></el-icon>
                  {{ feedback }}
                </li>
              </ul>
            </div>
            
            <div v-if="data.market_intelligence?.strategic_direction" class="market-item">
              <span class="info-label">战略方向:</span>
              <p class="strategic-direction">{{ data.market_intelligence.strategic_direction }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <!-- 竞争定位 -->
      <el-col :span="12">
        <el-card class="positioning-section" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon class="section-icon"><Position /></el-icon>
              <span class="section-title">竞争定位</span>
            </div>
          </template>
          
          <div class="positioning-content">
            <div v-if="data.competitive_positioning.differentiators?.length" class="positioning-item">
              <h4 class="item-title">差异化因素</h4>
              <div class="differentiators-tags">
                <el-tag 
                  v-for="diff in data.competitive_positioning.differentiators" 
                  :key="diff"
                  type="primary"
                  size="small"
                >
                  {{ diff }}
                </el-tag>
              </div>
            </div>
            
            <div v-if="data.competitive_positioning.advantages?.length" class="positioning-item">
              <h4 class="item-title">竞争优势</h4>
              <ul class="advantages-list">
                <li v-for="advantage in data.competitive_positioning.advantages" :key="advantage">
                  <el-icon class="advantage-icon"><TrophyBase /></el-icon>
                  {{ advantage }}
                </li>
              </ul>
            </div>
            
            <div v-if="data.competitive_positioning.threats?.length" class="positioning-item">
              <h4 class="item-title">威胁分析</h4>
              <ul class="threats-list">
                <li v-for="threat in data.competitive_positioning.threats" :key="threat">
                  <el-icon class="threat-icon"><Warning /></el-icon>
                  {{ threat }}
                </li>
              </ul>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { 
  TrendCharts, OfficeBuilding, Money, DataAnalysis, Position,
  CircleCheckFilled, CircleCloseFilled, ChatLineSquare, TrophyBase, Warning
} from '@element-plus/icons-vue'
import type { CompetitorAnalysis } from '@/types/batch-analysis'

interface Props {
  data: CompetitorAnalysis
}

const props = defineProps<Props>()

const hasMarketIntelligence = computed(() => {
  const mi = props.data.market_intelligence
  return mi && (mi.market_share || mi.customer_feedback?.length || mi.strategic_direction)
})

const getPositionType = (position: string) => {
  if (position.includes('领导') || position.includes('第一')) return 'success'
  if (position.includes('挑战') || position.includes('竞争')) return 'warning'
  return 'info'
}

const formatPrice = (price: number): string => {
  if (price >= 10000) {
    return (price / 10000).toFixed(1) + '万元'
  }
  return price.toFixed(0) + '元'
}

const getBenchmarkUnit = (key: string): string => {
  const unitMap: Record<string, string> = {
    '响应时间': 'ms',
    '并发用户': '人',
    '吞吐量': 'TPS',
    '可用性': '%'
  }
  return unitMap[key] || ''
}

const getMarketShareColor = (percentage: number) => {
  if (percentage >= 30) return '#67c23a'
  if (percentage >= 15) return '#e6a23c'
  return '#f56c6c'
}
</script>

<style scoped>
.competitor-analysis-view {
  width: 100%;
}

.analysis-header {
  margin-bottom: 20px;
}

.analysis-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.info-section,
.pricing-section,
.technical-section,
.market-section,
.positioning-section {
  border: 1px solid #e4e7ed;
  margin-bottom: 15px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-icon {
  color: #409eff;
}

.section-title {
  font-weight: 600;
  color: #303133;
}

.info-content,
.pricing-content,
.technical-content,
.market-content,
.positioning-content {
  padding: 0;
}

.info-item,
.pricing-item,
.market-item,
.positioning-item {
  margin-bottom: 15px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-item:last-child,
.pricing-item:last-child,
.market-item:last-child,
.positioning-item:last-child {
  margin-bottom: 0;
}

.info-label {
  color: #606266;
  font-size: 13px;
  font-weight: 500;
}

.info-value {
  color: #303133;
}

.company-name,
.product-name {
  font-weight: 600;
  color: #409eff;
}

.strengths-list,
.weaknesses-list,
.feedback-list,
.advantages-list,
.threats-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.strengths-list li,
.weaknesses-list li,
.feedback-list li,
.advantages-list li,
.threats-list li {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 4px 0;
  line-height: 1.5;
}

.strength-icon,
.advantage-icon {
  color: #67c23a;
  margin-top: 2px;
  flex-shrink: 0;
}

.weakness-icon,
.threat-icon {
  color: #f56c6c;
  margin-top: 2px;
  flex-shrink: 0;
}

.feedback-icon {
  color: #409eff;
  margin-top: 2px;
  flex-shrink: 0;
}

.price-display {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f0f9ff;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.price-label {
  color: #606266;
  font-size: 13px;
}

.price-value {
  font-size: 18px;
  font-weight: 600;
  color: #409eff;
}

.price-value.tco {
  color: #e6a23c;
}

.sub-title {
  margin: 0 0 15px 0;
  font-size: 14px;
  font-weight: 600;
  color: #606266;
  border-bottom: 1px solid #e4e7ed;
  padding-bottom: 8px;
}

.specs-list,
.benchmarks-list,
.features-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.spec-item,
.benchmark-item,
.feature-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 8px;
  background: #f8f9fa;
  border-radius: 4px;
  font-size: 13px;
}

.spec-name,
.benchmark-name,
.feature-name {
  color: #606266;
  flex: 1;
}

.spec-value,
.benchmark-value,
.feature-value {
  color: #303133;
  font-weight: 500;
}

.feature-yes {
  color: #67c23a;
}

.feature-no {
  color: #f56c6c;
}

.market-share {
  margin-top: 5px;
}

.strategic-direction {
  margin: 0;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 6px;
  color: #606266;
  line-height: 1.5;
  font-size: 13px;
}

.item-title {
  margin: 0 0 10px 0;
  font-size: 13px;
  font-weight: 600;
  color: #606266;
}

.differentiators-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .price-display {
    flex-direction: column;
    gap: 8px;
    text-align: center;
  }
  
  .spec-item,
  .benchmark-item,
  .feature-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .differentiators-tags {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>