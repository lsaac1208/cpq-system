<template>
  <div class="project-insights-view">
    <div class="analysis-header">
      <h3 class="analysis-title">
        <el-icon><FolderOpened /></el-icon>
        历史项目洞察
      </h3>
    </div>
    
    <el-row :gutter="20">
      <!-- 项目元数据 -->
      <el-col :span="12">
        <el-card class="metadata-section" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon class="section-icon"><DataBoard /></el-icon>
              <span class="section-title">项目概况</span>
            </div>
          </template>
          
          <div class="metadata-content">
            <div v-if="data.project_metadata.project_type" class="metadata-item">
              <span class="metadata-label">项目类型:</span>
              <el-tag type="primary" size="small">{{ data.project_metadata.project_type }}</el-tag>
            </div>
            
            <div v-if="data.project_metadata.industry_sector" class="metadata-item">
              <span class="metadata-label">行业领域:</span>
              <el-tag type="info" size="small">{{ data.project_metadata.industry_sector }}</el-tag>
            </div>
            
            <div v-if="data.project_metadata.project_scale" class="metadata-item">
              <span class="metadata-label">项目规模:</span>
              <el-tag :type="getScaleType(data.project_metadata.project_scale)" size="small">
                {{ data.project_metadata.project_scale }}
              </el-tag>
            </div>
            
            <div v-if="data.project_metadata.duration" class="metadata-item">
              <span class="metadata-label">项目周期:</span>
              <div class="duration-display">
                <el-icon><Clock /></el-icon>
                <span>{{ data.project_metadata.duration }}</span>
              </div>
            </div>
            
            <div v-if="data.project_metadata.outcome" class="metadata-item">
              <span class="metadata-label">项目结果:</span>
              <el-tag :type="getOutcomeType(data.project_metadata.outcome)" size="small">
                {{ getOutcomeText(data.project_metadata.outcome) }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <!-- 成功模式 -->
      <el-col :span="12">
        <el-card class="success-section" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon class="section-icon"><Trophy /></el-icon>
              <span class="section-title">成功模式</span>
            </div>
          </template>
          
          <div class="success-content">
            <div v-if="data.success_patterns.key_success_factors?.length" class="success-item">
              <h4 class="item-title">关键成功因素</h4>
              <ul class="factors-list">
                <li v-for="factor in data.success_patterns.key_success_factors" :key="factor">
                  <el-icon class="success-icon"><Medal /></el-icon>
                  {{ factor }}
                </li>
              </ul>
            </div>
            
            <div v-if="data.success_patterns.best_practices?.length" class="success-item">
              <h4 class="item-title">最佳实践</h4>
              <div class="practices-tags">
                <el-tag 
                  v-for="practice in data.success_patterns.best_practices" 
                  :key="practice"
                  type="success"
                  size="small"
                >
                  {{ practice }}
                </el-tag>
              </div>
            </div>
            
            <div v-if="data.success_patterns.critical_milestones?.length" class="success-item">
              <h4 class="item-title">关键里程碑</h4>
              <div class="milestones-timeline">
                <div 
                  v-for="(milestone, index) in data.success_patterns.critical_milestones" 
                  :key="milestone"
                  class="milestone-item"
                >
                  <div class="milestone-number">{{ index + 1 }}</div>
                  <div class="milestone-text">{{ milestone }}</div>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 资源配置 -->
    <el-row :gutter="20" style="margin-top: 20px;" v-if="data.success_patterns.resource_allocation">
      <el-col :span="24">
        <el-card class="resource-section" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon class="section-icon"><PieChart /></el-icon>
              <span class="section-title">资源配置模式</span>
            </div>
          </template>
          
          <div class="resource-content">
            <div class="resource-chart">
              <div 
                v-for="(value, key) in data.success_patterns.resource_allocation" 
                :key="key"
                class="resource-item"
              >
                <div class="resource-label">{{ key }}</div>
                <div class="resource-bar">
                  <div 
                    class="resource-fill" 
                    :style="{ 
                      width: (value * 100) + '%',
                      backgroundColor: getResourceColor(key)
                    }"
                  ></div>
                </div>
                <div class="resource-percentage">{{ (value * 100).toFixed(0) }}%</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 经验教训 -->
      <el-col :span="12">
        <el-card class="lessons-section" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon class="section-icon"><Reading /></el-icon>
              <span class="section-title">经验教训</span>
            </div>
          </template>
          
          <div class="lessons-content">
            <div v-if="data.lessons_learned.what_worked_well?.length" class="lessons-item">
              <h4 class="item-title positive">✓ 成功经验</h4>
              <ul class="success-lessons">
                <li v-for="lesson in data.lessons_learned.what_worked_well" :key="lesson">
                  <el-icon class="lesson-icon success"><CircleCheckFilled /></el-icon>
                  {{ lesson }}
                </li>
              </ul>
            </div>
            
            <div v-if="data.lessons_learned.challenges_faced?.length" class="lessons-item">
              <h4 class="item-title warning">⚠ 遇到的挑战</h4>
              <ul class="challenge-lessons">
                <li v-for="challenge in data.lessons_learned.challenges_faced" :key="challenge">
                  <el-icon class="lesson-icon warning"><WarningFilled /></el-icon>
                  {{ challenge }}
                </li>
              </ul>
            </div>
            
            <div v-if="data.lessons_learned.solutions_applied?.length" class="lessons-item">
              <h4 class="item-title info">💡 解决方案</h4>
              <ul class="solution-lessons">
                <li v-for="solution in data.lessons_learned.solutions_applied" :key="solution">
                  <el-icon class="lesson-icon info"><Lightbulb /></el-icon>
                  {{ solution }}
                </li>
              </ul>
            </div>
            
            <div v-if="data.lessons_learned.recommendations?.length" class="lessons-item">
              <h4 class="item-title primary">📋 改进建议</h4>
              <ul class="recommendation-lessons">
                <li v-for="rec in data.lessons_learned.recommendations" :key="rec">
                  <el-icon class="lesson-icon primary"><Flag /></el-icon>
                  {{ rec }}
                </li>
              </ul>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <!-- 可复用资产 -->
      <el-col :span="12">
        <el-card class="assets-section" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon class="section-icon"><Files /></el-icon>
              <span class="section-title">可复用资产</span>
            </div>
          </template>
          
          <div class="assets-content">
            <div v-if="data.reusable_assets.templates?.length" class="assets-item">
              <h4 class="item-title">模板文档</h4>
              <div class="templates-grid">
                <div 
                  v-for="template in data.reusable_assets.templates" 
                  :key="template"
                  class="template-card"
                >
                  <el-icon class="template-icon"><Document /></el-icon>
                  <span class="template-name">{{ template }}</span>
                </div>
              </div>
            </div>
            
            <div v-if="data.reusable_assets.process_workflows?.length" class="assets-item">
              <h4 class="item-title">流程工作流</h4>
              <div class="workflows-list">
                <div 
                  v-for="workflow in data.reusable_assets.process_workflows" 
                  :key="workflow"
                  class="workflow-item"
                >
                  <el-icon class="workflow-icon"><Operation /></el-icon>
                  <span>{{ workflow }}</span>
                </div>
              </div>
            </div>
            
            <div v-if="data.reusable_assets.configurations && Object.keys(data.reusable_assets.configurations).length" class="assets-item">
              <h4 class="item-title">配置参数</h4>
              <div class="configs-list">
                <div 
                  v-for="(value, key) in data.reusable_assets.configurations" 
                  :key="key"
                  class="config-item"
                >
                  <span class="config-key">{{ key }}:</span>
                  <span class="config-value">{{ typeof value === 'object' ? '配置对象' : value }}</span>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 风险指标 -->
    <el-row :gutter="20" style="margin-top: 20px;" v-if="hasRiskIndicators">
      <el-col :span="24">
        <el-card class="risk-section" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon class="section-icon"><Warning /></el-icon>
              <span class="section-title">风险指标与应对</span>
            </div>
          </template>
          
          <div class="risk-content">
            <el-row :gutter="20">
              <el-col :span="8" v-if="data.risk_indicators?.early_warning_signs?.length">
                <h4 class="risk-subtitle">早期预警信号</h4>
                <ul class="warning-list">
                  <li v-for="warning in data.risk_indicators.early_warning_signs" :key="warning">
                    <el-icon class="warning-icon"><Bell /></el-icon>
                    {{ warning }}
                  </li>
                </ul>
              </el-col>
              
              <el-col :span="8" v-if="data.risk_indicators?.mitigation_strategies?.length">
                <h4 class="risk-subtitle">缓解策略</h4>
                <ul class="mitigation-list">
                  <li v-for="strategy in data.risk_indicators.mitigation_strategies" :key="strategy">
                    <el-icon class="mitigation-icon"><Shield /></el-icon>
                    {{ strategy }}
                  </li>
                </ul>
              </el-col>
              
              <el-col :span="8" v-if="data.risk_indicators?.contingency_plans?.length">
                <h4 class="risk-subtitle">应急计划</h4>
                <ul class="contingency-list">
                  <li v-for="plan in data.risk_indicators.contingency_plans" :key="plan">
                    <el-icon class="contingency-icon"><FirstAidKit /></el-icon>
                    {{ plan }}
                  </li>
                </ul>
              </el-col>
            </el-row>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { 
  FolderOpened, DataBoard, Trophy, Medal, PieChart, Reading, Files, Warning,
  Clock, Document, Operation, CircleCheckFilled, WarningFilled, Lightbulb,
  Flag, Bell, Shield, FirstAidKit
} from '@element-plus/icons-vue'
import type { ProjectInsights } from '@/types/batch-analysis'

interface Props {
  data: ProjectInsights
}

const props = defineProps<Props>()

const hasRiskIndicators = computed(() => {
  const ri = props.data.risk_indicators
  return ri && (
    ri.early_warning_signs?.length || 
    ri.mitigation_strategies?.length || 
    ri.contingency_plans?.length
  )
})

const getScaleType = (scale: string) => {
  if (scale.includes('大型') || scale.includes('large')) return 'danger'
  if (scale.includes('中型') || scale.includes('medium')) return 'warning'
  return 'success'
}

const getOutcomeType = (outcome: string) => {
  switch (outcome) {
    case 'successful': return 'success'
    case 'partially_successful': return 'warning'
    case 'failed': return 'danger'
    case 'cancelled': return 'info'
    default: return 'info'
  }
}

const getOutcomeText = (outcome: string) => {
  switch (outcome) {
    case 'successful': return '成功'
    case 'partially_successful': return '部分成功'
    case 'failed': return '失败'
    case 'cancelled': return '取消'
    default: return outcome
  }
}

const getResourceColor = (key: string) => {
  const colorMap: Record<string, string> = {
    '开发': '#409eff',
    '测试': '#67c23a',
    '实施': '#e6a23c',
    '培训': '#f56c6c',
    '管理': '#909399'
  }
  return colorMap[key] || '#409eff'
}
</script>

<style scoped>
.project-insights-view {
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

.metadata-section,
.success-section,
.resource-section,
.lessons-section,
.assets-section,
.risk-section {
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

.metadata-content,
.success-content,
.resource-content,
.lessons-content,
.assets-content,
.risk-content {
  padding: 0;
}

.metadata-item,
.success-item,
.lessons-item,
.assets-item {
  margin-bottom: 15px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.metadata-item:last-child,
.success-item:last-child,
.lessons-item:last-child,
.assets-item:last-child {
  margin-bottom: 0;
}

.metadata-label {
  color: #606266;
  font-size: 13px;
  font-weight: 500;
}

.duration-display {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #409eff;
  font-weight: 500;
}

.item-title {
  margin: 0 0 10px 0;
  font-size: 14px;
  font-weight: 600;
  color: #606266;
}

.item-title.positive {
  color: #67c23a;
}

.item-title.warning {
  color: #e6a23c;
}

.item-title.info {
  color: #409eff;
}

.item-title.primary {
  color: #606266;
}

.factors-list,
.success-lessons,
.challenge-lessons,
.solution-lessons,
.recommendation-lessons,
.warning-list,
.mitigation-list,
.contingency-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.factors-list li,
.success-lessons li,
.challenge-lessons li,
.solution-lessons li,
.recommendation-lessons li,
.warning-list li,
.mitigation-list li,
.contingency-list li {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 6px 0;
  line-height: 1.5;
}

.success-icon {
  color: #67c23a;
  margin-top: 2px;
  flex-shrink: 0;
}

.lesson-icon.success {
  color: #67c23a;
}

.lesson-icon.warning {
  color: #e6a23c;
}

.lesson-icon.info {
  color: #409eff;
}

.lesson-icon.primary {
  color: #606266;
}

.warning-icon {
  color: #e6a23c;
  margin-top: 2px;
  flex-shrink: 0;
}

.mitigation-icon {
  color: #67c23a;
  margin-top: 2px;
  flex-shrink: 0;
}

.contingency-icon {
  color: #f56c6c;
  margin-top: 2px;
  flex-shrink: 0;
}

.practices-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.milestones-timeline {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.milestone-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.milestone-number {
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
  flex-shrink: 0;
}

.milestone-text {
  color: #303133;
  font-size: 14px;
}

.resource-chart {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.resource-item {
  display: grid;
  grid-template-columns: 80px 1fr 50px;
  align-items: center;
  gap: 15px;
}

.resource-label {
  color: #606266;
  font-size: 13px;
  font-weight: 500;
}

.resource-bar {
  height: 20px;
  background: #e4e7ed;
  border-radius: 10px;
  overflow: hidden;
}

.resource-fill {
  height: 100%;
  border-radius: 10px;
  transition: width 0.3s ease;
}

.resource-percentage {
  color: #606266;
  font-size: 12px;
  text-align: right;
}

.templates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 10px;
}

.template-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f0f9ff;
  border: 1px solid #d0e7ff;
  border-radius: 6px;
  color: #409eff;
  font-size: 13px;
}

.template-icon {
  flex-shrink: 0;
}

.template-name {
  flex: 1;
  word-break: break-word;
}

.workflows-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.workflow-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: #f5f7fa;
  border-radius: 4px;
  color: #606266;
  font-size: 13px;
}

.workflow-icon {
  color: #909399;
  flex-shrink: 0;
}

.configs-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.config-item {
  display: flex;
  justify-content: space-between;
  padding: 6px 8px;
  background: #f8f9fa;
  border-radius: 4px;
  font-size: 12px;
}

.config-key {
  color: #606266;
  font-weight: 500;
}

.config-value {
  color: #303133;
}

.risk-subtitle {
  margin: 0 0 15px 0;
  font-size: 14px;
  font-weight: 600;
  color: #606266;
  border-bottom: 1px solid #e4e7ed;
  padding-bottom: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .resource-item {
    grid-template-columns: 1fr;
    gap: 8px;
    text-align: left;
  }
  
  .resource-percentage {
    text-align: left;
  }
  
  .templates-grid {
    grid-template-columns: 1fr;
  }
  
  .milestone-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .practices-tags {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>