<template>
  <div class="risk-opportunity-analysis">
    <!-- 总览 -->
    <div class="overview-section">
      <el-row :gutter="24">
        <el-col :span="12">
          <el-card class="overview-card opportunities">
            <div class="overview-content">
              <div class="overview-icon">
                <el-icon><Opportunity /></el-icon>
              </div>
              <div class="overview-info">
                <h3>市场机会</h3>
                <p class="overview-count">{{ analysis.opportunities.length }} 个</p>
                <p class="overview-desc">发现的潜在机会</p>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="12">
          <el-card class="overview-card risks">
            <div class="overview-content">
              <div class="overview-icon">
                <el-icon><Warning /></el-icon>
              </div>
              <div class="overview-info">
                <h3>潜在风险</h3>
                <p class="overview-count">{{ analysis.risks.length }} 个</p>
                <p class="overview-desc">需要关注的风险点</p>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 详细分析 -->
    <div class="detailed-analysis">
      <el-row :gutter="24">
        <!-- 机会分析 -->
        <el-col :span="12">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>机会分析</span>
                <el-tag 
                  :type="analysis.opportunities.length > 2 ? 'success' : analysis.opportunities.length > 0 ? 'warning' : 'info'"
                  size="small"
                >
                  {{ getOpportunityLevel(analysis.opportunities.length) }}
                </el-tag>
              </div>
            </template>
            
            <div class="opportunities-section">
              <div v-if="analysis.opportunities.length === 0" class="empty-state">
                <el-empty description="暂无明显机会" :image-size="80">
                  <p class="empty-tip">建议加强市场调研，寻找潜在机会</p>
                </el-empty>
              </div>
              
              <div v-else class="opportunities-list">
                <div 
                  v-for="(opportunity, index) in analysis.opportunities" 
                  :key="index"
                  class="opportunity-item"
                >
                  <div class="opportunity-header">
                    <div class="opportunity-icon">
                      <el-icon><Star /></el-icon>
                    </div>
                    <div class="opportunity-title">
                      <h4>{{ opportunity.type }}</h4>
                      <el-tag 
                        :type="getImpactType(opportunity.impact)"
                        size="small"
                      >
                        {{ getImpactText(opportunity.impact) }}影响
                      </el-tag>
                    </div>
                  </div>
                  
                  <div class="opportunity-content">
                    <p>{{ opportunity.description }}</p>
                  </div>
                  
                  <div class="opportunity-actions">
                    <el-button 
                      type="primary" 
                      size="small"
                      @click="handleOpportunity(opportunity)"
                    >
                      制定行动计划
                    </el-button>
                  </div>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- 风险分析 -->
        <el-col :span="12">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>风险分析</span>
                <el-tag 
                  :type="analysis.risks.length > 2 ? 'danger' : analysis.risks.length > 0 ? 'warning' : 'success'"
                  size="small"
                >
                  {{ getRiskLevel(analysis.risks.length) }}
                </el-tag>
              </div>
            </template>
            
            <div class="risks-section">
              <div v-if="analysis.risks.length === 0" class="empty-state">
                <el-empty description="风险较低" :image-size="80">
                  <p class="empty-tip">当前市场环境相对安全</p>
                </el-empty>
              </div>
              
              <div v-else class="risks-list">
                <div 
                  v-for="(risk, index) in analysis.risks" 
                  :key="index"
                  class="risk-item"
                  :class="getRiskSeverityClass(risk.probability, risk.impact)"
                >
                  <div class="risk-header">
                    <div class="risk-icon">
                      <el-icon><WarningFilled /></el-icon>
                    </div>
                    <div class="risk-title">
                      <h4>{{ risk.type }}</h4>
                      <div class="risk-tags">
                        <el-tag 
                          :type="getProbabilityType(risk.probability)"
                          size="small"
                        >
                          {{ getProbabilityText(risk.probability) }}概率
                        </el-tag>
                        <el-tag 
                          :type="getImpactType(risk.impact)"
                          size="small"
                        >
                          {{ getImpactText(risk.impact) }}影响
                        </el-tag>
                      </div>
                    </div>
                  </div>
                  
                  <div class="risk-content">
                    <p>{{ risk.description }}</p>
                  </div>
                  
                  <div class="risk-actions">
                    <el-button 
                      type="danger" 
                      size="small"
                      @click="handleRisk(risk)"
                    >
                      制定应对措施
                    </el-button>
                  </div>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 缓解策略 -->
    <div class="mitigation-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>风险缓解策略</span>
            <el-tag type="primary" size="small">
              {{ analysis.mitigation_strategies.length }} 项策略
            </el-tag>
          </div>
        </template>
        
        <div class="mitigation-content">
          <div v-if="analysis.mitigation_strategies.length === 0" class="empty-state">
            <el-empty description="暂无特定缓解策略" :image-size="80" />
          </div>
          
          <div v-else class="strategies-grid">
            <div 
              v-for="(strategy, index) in analysis.mitigation_strategies" 
              :key="index"
              class="strategy-card"
            >
              <div class="strategy-number">{{ index + 1 }}</div>
              <div class="strategy-content">
                <p>{{ strategy }}</p>
              </div>
              <div class="strategy-priority">
                <el-tag 
                  :type="getStrategyPriority(index)"
                  size="small"
                >
                  {{ getStrategyPriorityText(index) }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 行动建议 -->
    <div class="action-recommendations">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>行动建议</span>
            <el-tag type="success" size="small">立即执行</el-tag>
          </div>
        </template>
        
        <div class="recommendations-content">
          <div class="recommendation-categories">
            <!-- 短期行动 -->
            <div class="category-section">
              <h4>
                <el-icon><Clock /></el-icon>
                短期行动 (1-3个月)
              </h4>
              <ul class="action-list">
                <li v-if="analysis.opportunities.length > 0">
                  抓住 {{ analysis.opportunities[0]?.type || '主要' }} 机会，快速行动
                </li>
                <li v-if="analysis.risks.length > 0">
                  优先应对 {{ analysis.risks[0]?.type || '主要' }} 风险
                </li>
                <li>建立市场监控机制，跟踪竞争动态</li>
              </ul>
            </div>

            <!-- 中期规划 -->
            <div class="category-section">
              <h4>
                <el-icon><Calendar /></el-icon>
                中期规划 (3-12个月)
              </h4>
              <ul class="action-list">
                <li>建立完善的风险管理体系</li>
                <li>开发差异化产品和服务</li>
                <li>加强客户关系管理，提升客户忠诚度</li>
              </ul>
            </div>

            <!-- 长期战略 -->
            <div class="category-section">
              <h4>
                <el-icon><TrendCharts /></el-icon>
                长期战略 (1年以上)
              </h4>
              <ul class="action-list">
                <li>建立行业领导地位</li>
                <li>构建可持续竞争优势</li>
                <li>探索新兴市场和技术机会</li>
              </ul>
            </div>
          </div>

          <!-- 关键成功因素 -->
          <div class="success-factors">
            <h4>关键成功因素</h4>
            <div class="factors-tags">
              <el-tag 
                v-for="factor in getKeySuccessFactors()" 
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Opportunity, Warning, Star, WarningFilled, Clock, Calendar, TrendCharts 
} from '@element-plus/icons-vue'
import type { RiskOpportunityAnalysis } from '@/api/pricing-decision'

// 定义属性
defineProps<{
  analysis: RiskOpportunityAnalysis
}>()

// 处理机会
const handleOpportunity = async (opportunity: any) => {
  try {
    const action = await ElMessageBox.prompt(
      `为 "${opportunity.type}" 机会制定行动计划:`,
      '行动计划',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPlaceholder: '请输入具体的行动计划...'
      }
    )
    
    if (action.value) {
      ElMessage.success('行动计划已记录')
      // 这里可以调用API保存行动计划
    }
  } catch (error) {
    // 用户取消
  }
}

// 处理风险
const handleRisk = async (risk: any) => {
  try {
    const mitigation = await ElMessageBox.prompt(
      `为 "${risk.type}" 风险制定应对措施:`,
      '应对措施',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPlaceholder: '请输入具体的应对措施...'
      }
    )
    
    if (mitigation.value) {
      ElMessage.success('应对措施已记录')
      // 这里可以调用API保存应对措施
    }
  } catch (error) {
    // 用户取消
  }
}

// 获取机会等级
const getOpportunityLevel = (count: number): string => {
  if (count > 2) return '机会丰富'
  if (count > 0) return '有机会'
  return '机会较少'
}

// 获取风险等级
const getRiskLevel = (count: number): string => {
  if (count > 2) return '高风险'
  if (count > 0) return '中等风险'
  return '低风险'
}

// 获取影响类型和文本
const getImpactType = (impact: string): string => {
  switch (impact) {
    case 'high': return 'danger'
    case 'medium': return 'warning'
    case 'low': return 'info'
    default: return 'info'
  }
}

const getImpactText = (impact: string): string => {
  switch (impact) {
    case 'high': return '高'
    case 'medium': return '中等'
    case 'low': return '低'
    default: return '未知'
  }
}

// 获取概率类型和文本
const getProbabilityType = (probability: string): string => {
  switch (probability) {
    case 'high': return 'danger'
    case 'medium': return 'warning'
    case 'low': return 'success'
    default: return 'info'
  }
}

const getProbabilityText = (probability: string): string => {
  switch (probability) {
    case 'high': return '高'
    case 'medium': return '中等'
    case 'low': return '低'
    default: return '未知'
  }
}

// 获取风险严重程度样式
const getRiskSeverityClass = (probability: string, impact: string): string => {
  if (probability === 'high' && impact === 'high') return 'risk-critical'
  if (probability === 'high' || impact === 'high') return 'risk-high'
  if (probability === 'medium' || impact === 'medium') return 'risk-medium'
  return 'risk-low'
}

// 获取策略优先级
const getStrategyPriority = (index: number): string => {
  if (index === 0) return 'danger'
  if (index === 1) return 'warning'
  return 'info'
}

const getStrategyPriorityText = (index: number): string => {
  if (index === 0) return '高优先级'
  if (index === 1) return '中优先级'
  return '低优先级'
}

// 获取关键成功因素
const getKeySuccessFactors = (): string[] => {
  return [
    '市场洞察',
    '快速响应',
    '风险控制',
    '创新能力',
    '客户关系',
    '团队执行力'
  ]
}
</script>

<style scoped>
.risk-opportunity-analysis {
  padding: 16px 0;
}

.overview-section {
  margin-bottom: 24px;
}

.overview-card {
  height: 120px;
}

.overview-card.opportunities {
  border-left: 4px solid #67c23a;
}

.overview-card.risks {
  border-left: 4px solid #f56c6c;
}

.overview-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.overview-icon {
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

.opportunities .overview-icon {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
}

.risks .overview-icon {
  background: linear-gradient(135deg, #f56c6c 0%, #f78989 100%);
}

.overview-info h3 {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: #303133;
  font-weight: 600;
}

.overview-count {
  margin: 0 0 4px 0;
  font-size: 24px;
  font-weight: 600;
  color: #409eff;
}

.overview-desc {
  margin: 0;
  font-size: 12px;
  color: #909399;
}

.detailed-analysis {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.opportunities-section,
.risks-section {
  padding: 16px 0;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
}

.empty-tip {
  margin-top: 12px;
  color: #909399;
  font-size: 13px;
}

.opportunities-list,
.risks-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.opportunity-item,
.risk-item {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #67c23a;
}

.risk-item {
  border-left-color: #f56c6c;
}

.risk-item.risk-critical {
  background: #fef0f0;
  border-left-color: #f56c6c;
}

.risk-item.risk-high {
  background: #fdf6ec;
  border-left-color: #e6a23c;
}

.risk-item.risk-medium {
  background: #f4f9ff;
  border-left-color: #409eff;
}

.opportunity-header,
.risk-header {
  display: flex;
  align-items: flex-start;
  margin-bottom: 12px;
}

.opportunity-icon,
.risk-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  flex-shrink: 0;
  font-size: 16px;
  color: white;
}

.opportunity-icon {
  background: #67c23a;
}

.risk-icon {
  background: #f56c6c;
}

.opportunity-title,
.risk-title {
  flex: 1;
}

.opportunity-title h4,
.risk-title h4 {
  margin: 0 0 8px 0;
  font-size: 15px;
  color: #303133;
}

.risk-tags {
  display: flex;
  gap: 8px;
}

.opportunity-content,
.risk-content {
  margin-bottom: 12px;
}

.opportunity-content p,
.risk-content p {
  margin: 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

.opportunity-actions,
.risk-actions {
  text-align: right;
}

.mitigation-section {
  margin-bottom: 24px;
}

.mitigation-content {
  padding: 16px 0;
}

.strategies-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.strategy-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.strategy-number {
  width: 28px;
  height: 28px;
  background: #409eff;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}

.strategy-content {
  flex: 1;
}

.strategy-content p {
  margin: 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

.strategy-priority {
  flex-shrink: 0;
}

.action-recommendations {
  margin-bottom: 24px;
}

.recommendations-content {
  padding: 16px 0;
}

.recommendation-categories {
  margin-bottom: 32px;
}

.category-section {
  margin-bottom: 24px;
}

.category-section h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-list {
  margin: 0;
  padding-left: 20px;
}

.action-list li {
  margin-bottom: 8px;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

.success-factors {
  padding-top: 24px;
  border-top: 1px solid #ebeef5;
}

.success-factors h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #303133;
}

.factors-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.factor-tag {
  margin: 0;
}

@media (max-width: 768px) {
  .detailed-analysis .el-col {
    margin-bottom: 16px;
  }

  .strategies-grid {
    grid-template-columns: 1fr;
  }

  .strategy-card {
    flex-direction: column;
    text-align: center;
  }

  .strategy-number {
    margin-bottom: 8px;
  }
}
</style>