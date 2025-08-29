<template>
  <div class="customer-requirements-view">
    <div class="analysis-header">
      <h3 class="analysis-title">
        <el-icon><Document /></el-icon>
        客户需求分析结果
      </h3>
    </div>
    
    <el-row :gutter="20">
      <!-- 技术需求 -->
      <el-col :span="12">
        <el-card class="requirement-section" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon class="section-icon"><Monitor /></el-icon>
              <span class="section-title">技术需求</span>
            </div>
          </template>
          
          <div class="requirement-content">
            <!-- 性能规格 -->
            <div v-if="data.technical_requirements.performance_specs" class="requirement-item">
              <h4 class="item-title">性能规格</h4>
              <div class="specs-grid">
                <div 
                  v-for="(value, key) in data.technical_requirements.performance_specs" 
                  :key="key"
                  class="spec-item"
                >
                  <span class="spec-label">{{ formatSpecLabel(key) }}:</span>
                  <span class="spec-value">{{ value }}</span>
                </div>
              </div>
            </div>
            
            <!-- 功能需求 -->
            <div v-if="data.technical_requirements.functional_requirements?.length" class="requirement-item">
              <h4 class="item-title">功能需求</h4>
              <ul class="requirement-list">
                <li v-for="req in data.technical_requirements.functional_requirements" :key="req">
                  <el-icon class="list-icon"><Check /></el-icon>
                  {{ req }}
                </li>
              </ul>
            </div>
            
            <!-- 技术约束 -->
            <div v-if="data.technical_requirements.technical_constraints?.length" class="requirement-item">
              <h4 class="item-title">技术约束</h4>
              <div class="constraints-tags">
                <el-tag 
                  v-for="constraint in data.technical_requirements.technical_constraints" 
                  :key="constraint"
                  type="warning"
                  size="small"
                >
                  {{ constraint }}
                </el-tag>
              </div>
            </div>
            
            <!-- 合规标准 -->
            <div v-if="data.technical_requirements.compliance_standards?.length" class="requirement-item">
              <h4 class="item-title">合规标准</h4>
              <div class="compliance-tags">
                <el-tag 
                  v-for="standard in data.technical_requirements.compliance_standards" 
                  :key="standard"
                  type="success"
                  size="small"
                >
                  {{ standard }}
                </el-tag>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <!-- 商务需求 -->
      <el-col :span="12">
        <el-card class="requirement-section" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon class="section-icon"><Money /></el-icon>
              <span class="section-title">商务需求</span>
            </div>
          </template>
          
          <div class="requirement-content">
            <!-- 预算范围 -->
            <div v-if="data.business_requirements.budget_range" class="requirement-item">
              <h4 class="item-title">预算范围</h4>
              <div class="budget-display">
                <el-tag type="primary" size="large">{{ data.business_requirements.budget_range }}</el-tag>
              </div>
            </div>
            
            <!-- 项目时间线 -->
            <div v-if="data.business_requirements.timeline" class="requirement-item">
              <h4 class="item-title">项目时间线</h4>
              <div class="timeline-display">
                <el-icon><Clock /></el-icon>
                <span>{{ data.business_requirements.timeline }}</span>
              </div>
            </div>
            
            <!-- 交付条件 -->
            <div v-if="data.business_requirements.delivery_terms" class="requirement-item">
              <h4 class="item-title">交付条件</h4>
              <p class="delivery-terms">{{ data.business_requirements.delivery_terms }}</p>
            </div>
            
            <!-- 支持需求 -->
            <div v-if="data.business_requirements.support_needs?.length" class="requirement-item">
              <h4 class="item-title">支持需求</h4>
              <div class="support-tags">
                <el-tag 
                  v-for="need in data.business_requirements.support_needs" 
                  :key="need"
                  type="info"
                  size="small"
                >
                  {{ need }}
                </el-tag>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 决策因素 -->
      <el-col :span="12">
        <el-card class="requirement-section" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon class="section-icon"><TrendCharts /></el-icon>
              <span class="section-title">决策因素</span>
            </div>
          </template>
          
          <div class="requirement-content">
            <!-- 关键标准 -->
            <div v-if="data.decision_factors.key_criteria?.length" class="requirement-item">
              <h4 class="item-title">关键评估标准</h4>
              <ul class="criteria-list">
                <li v-for="criteria in data.decision_factors.key_criteria" :key="criteria">
                  <el-icon class="list-icon"><Star /></el-icon>
                  {{ criteria }}
                </li>
              </ul>
            </div>
            
            <!-- 优先级排序 -->
            <div v-if="data.decision_factors.priority_ranking?.length" class="requirement-item">
              <h4 class="item-title">优先级排序</h4>
              <div class="priority-chart">
                <div 
                  v-for="(item, index) in data.decision_factors.priority_ranking" 
                  :key="item.factor"
                  class="priority-item"
                >
                  <div class="priority-rank">{{ index + 1 }}</div>
                  <div class="priority-factor">{{ item.factor }}</div>
                  <div class="priority-weight">{{ (item.weight * 100).toFixed(0) }}%</div>
                  <div class="priority-bar">
                    <div 
                      class="priority-fill" 
                      :style="{ width: (item.weight * 100) + '%' }"
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <!-- 风险评估 -->
      <el-col :span="12">
        <el-card class="requirement-section" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon class="section-icon"><Warning /></el-icon>
              <span class="section-title">风险评估</span>
            </div>
          </template>
          
          <div class="requirement-content">
            <!-- 整体风险等级 -->
            <div class="requirement-item">
              <h4 class="item-title">整体风险等级</h4>
              <div class="risk-level">
                <el-tag 
                  :type="getRiskLevelType(data.risk_assessment.overall_risk_level)" 
                  size="large"
                >
                  {{ getRiskLevelText(data.risk_assessment.overall_risk_level) }}
                </el-tag>
              </div>
            </div>
            
            <!-- 技术风险 -->
            <div v-if="data.risk_assessment.technical_risks?.length" class="requirement-item">
              <h4 class="item-title">技术风险</h4>
              <ul class="risk-list">
                <li v-for="risk in data.risk_assessment.technical_risks" :key="risk">
                  <el-icon class="risk-icon"><Warning /></el-icon>
                  {{ risk }}
                </li>
              </ul>
            </div>
            
            <!-- 商务风险 -->
            <div v-if="data.risk_assessment.commercial_risks?.length" class="requirement-item">
              <h4 class="item-title">商务风险</h4>
              <ul class="risk-list">
                <li v-for="risk in data.risk_assessment.commercial_risks" :key="risk">
                  <el-icon class="risk-icon"><Warning /></el-icon>
                  {{ risk }}
                </li>
              </ul>
            </div>
            
            <!-- 时间风险 -->
            <div v-if="data.risk_assessment.timeline_risks?.length" class="requirement-item">
              <h4 class="item-title">时间风险</h4>
              <ul class="risk-list">
                <li v-for="risk in data.risk_assessment.timeline_risks" :key="risk">
                  <el-icon class="risk-icon"><Warning /></el-icon>
                  {{ risk }}
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
import { Document, Money, Clock, TrendCharts, Warning, Check, Star } from '@element-plus/icons-vue'
import type { CustomerRequirementsAnalysis } from '@/types/batch-analysis'

interface Props {
  data: CustomerRequirementsAnalysis
}

defineProps<Props>()

const formatSpecLabel = (key: string): string => {
  const labelMap: Record<string, string> = {
    cpu: 'CPU',
    memory: '内存',
    storage: '存储',
    network: '网络',
    performance: '性能',
    scalability: '可扩展性'
  }
  return labelMap[key] || key
}

const getRiskLevelType = (level: string) => {
  switch (level) {
    case 'low': return 'success'
    case 'medium': return 'warning'
    case 'high': return 'danger'
    default: return 'info'
  }
}

const getRiskLevelText = (level: string) => {
  switch (level) {
    case 'low': return '低风险'
    case 'medium': return '中风险'
    case 'high': return '高风险'
    default: return level
  }
}
</script>

<style scoped>
.customer-requirements-view {
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

.requirement-section {
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

.requirement-content {
  padding: 0;
}

.requirement-item {
  margin-bottom: 20px;
}

.requirement-item:last-child {
  margin-bottom: 0;
}

.item-title {
  margin: 0 0 10px 0;
  font-size: 14px;
  font-weight: 600;
  color: #606266;
}

.specs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 10px;
}

.spec-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.spec-label {
  color: #909399;
  font-size: 13px;
}

.spec-value {
  color: #303133;
  font-weight: 500;
}

.requirement-list,
.criteria-list,
.risk-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.requirement-list li,
.criteria-list li,
.risk-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px solid #f0f0f0;
}

.requirement-list li:last-child,
.criteria-list li:last-child,
.risk-list li:last-child {
  border-bottom: none;
}

.list-icon {
  color: #67c23a;
  flex-shrink: 0;
}

.risk-icon {
  color: #e6a23c;
  flex-shrink: 0;
}

.constraints-tags,
.compliance-tags,
.support-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.budget-display {
  text-align: center;
  padding: 20px;
}

.timeline-display {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: #f0f9ff;
  border-radius: 6px;
  color: #409eff;
  font-weight: 500;
}

.delivery-terms {
  margin: 0;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
  color: #606266;
  line-height: 1.6;
}

.priority-chart {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.priority-item {
  display: grid;
  grid-template-columns: 30px 1fr 50px 100px;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
}

.priority-rank {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: #409eff;
  color: white;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
}

.priority-factor {
  color: #303133;
  font-weight: 500;
}

.priority-weight {
  color: #606266;
  font-size: 13px;
  text-align: right;
}

.priority-bar {
  height: 6px;
  background: #e4e7ed;
  border-radius: 3px;
  overflow: hidden;
}

.priority-fill {
  height: 100%;
  background: linear-gradient(to right, #409eff, #67c23a);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.risk-level {
  text-align: center;
  padding: 15px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .specs-grid {
    grid-template-columns: 1fr;
  }
  
  .priority-item {
    grid-template-columns: 30px 1fr;
    gap: 8px;
  }
  
  .priority-weight,
  .priority-bar {
    grid-column: 2;
    margin-top: 5px;
  }
  
  .constraints-tags,
  .compliance-tags,
  .support-tags {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>