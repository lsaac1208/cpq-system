<template>
  <div class="prompt-optimizer">
    <el-card class="optimizer-card">
      <template #header>
        <div class="card-header">
          <h3>智能Prompt优化</h3>
          <p>输入当前Prompt和历史数据，获得AI驱动的优化建议</p>
        </div>
      </template>

      <el-form 
        ref="formRef" 
        :model="formData" 
        :rules="formRules" 
        label-width="120px"
        class="optimizer-form"
      >
        <!-- 当前Prompt -->
        <el-form-item label="当前Prompt" prop="current_prompt" required>
          <el-input
            v-model="formData.current_prompt"
            type="textarea"
            :rows="6"
            placeholder="请输入需要优化的Prompt..."
            show-word-limit
            maxlength="2000"
          />
          <div class="form-tip">
            提示：详细描述当前使用的Prompt，包括指令、参数和期望的输出格式
          </div>
        </el-form-item>

        <!-- 历史成功案例 -->
        <el-form-item label="成功案例">
          <div class="historical-data-section">
            <div class="section-header">
              <span>历史成功案例</span>
              <el-button 
                type="primary" 
                size="small" 
                @click="addSuccessCase"
                :icon="Plus"
              >
                添加案例
              </el-button>
            </div>
            
            <div v-if="formData.historical_data.success_cases.length === 0" class="empty-state">
              <el-empty description="暂无成功案例，点击上方按钮添加">
                <el-button type="primary" @click="addSuccessCase">添加成功案例</el-button>
              </el-empty>
            </div>
            
            <div 
              v-for="(case_item, index) in formData.historical_data.success_cases" 
              :key="`success-${index}`"
              class="case-item success-case"
            >
              <div class="case-header">
                <span class="case-title">成功案例 #{{ index + 1 }}</span>
                <el-button 
                  type="danger" 
                  size="small" 
                  text 
                  @click="removeSuccessCase(index)"
                  :icon="Delete"
                />
              </div>
              
              <el-input
                v-model="case_item.prompt"
                type="textarea"
                :rows="3"
                placeholder="输入成功的Prompt..."
                class="case-input"
              />
              
              <div class="case-meta">
                <el-rate 
                  v-model="case_item.result_quality" 
                  :max="5" 
                  show-score
                  text-color="#ff9900"
                  score-template="质量: {value}"
                />
                
                <el-input
                  v-model="case_item.user_feedback"
                  placeholder="用户反馈..."
                  size="small"
                  style="width: 200px; margin-left: 15px"
                />
              </div>
            </div>
          </div>
        </el-form-item>

        <!-- 历史失败案例 -->
        <el-form-item label="失败案例">
          <div class="historical-data-section">
            <div class="section-header">
              <span>历史失败案例</span>
              <el-button 
                type="warning" 
                size="small" 
                @click="addFailureCase"
                :icon="Plus"
              >
                添加案例
              </el-button>
            </div>
            
            <div v-if="formData.historical_data.failure_cases.length === 0" class="empty-state">
              <el-empty description="暂无失败案例，点击上方按钮添加">
                <el-button type="warning" @click="addFailureCase">添加失败案例</el-button>
              </el-empty>
            </div>
            
            <div 
              v-for="(case_item, index) in formData.historical_data.failure_cases" 
              :key="`failure-${index}`"
              class="case-item failure-case"
            >
              <div class="case-header">
                <span class="case-title">失败案例 #{{ index + 1 }}</span>
                <el-button 
                  type="danger" 
                  size="small" 
                  text 
                  @click="removeFailureCase(index)"
                  :icon="Delete"
                />
              </div>
              
              <el-input
                v-model="case_item.prompt"
                type="textarea"
                :rows="3"
                placeholder="输入失败的Prompt..."
                class="case-input"
              />
              
              <div class="case-meta">
                <el-tag 
                  v-for="(issue, issueIndex) in case_item.issues" 
                  :key="issueIndex"
                  type="danger" 
                  size="small"
                  closable
                  @close="removeIssue(index, issueIndex)"
                  style="margin-right: 5px"
                >
                  {{ issue }}
                </el-tag>
                
                <el-input
                  v-model="newIssue[index]"
                  placeholder="添加问题..."
                  size="small"
                  style="width: 120px; margin-right: 10px"
                  @keyup.enter="addIssue(index)"
                />
                
                <el-button 
                  size="small" 
                  type="primary" 
                  text
                  @click="addIssue(index)"
                >
                  添加问题
                </el-button>
              </div>
              
              <el-input
                v-model="case_item.user_feedback"
                placeholder="用户反馈..."
                size="small"
                style="margin-top: 10px"
              />
            </div>
          </div>
        </el-form-item>

        <!-- 优化目标 -->
        <el-form-item label="优化目标" prop="optimization_goals" required>
          <el-checkbox-group v-model="formData.optimization_goals" class="goal-checkboxes">
            <el-checkbox label="accuracy">提升准确性</el-checkbox>
            <el-checkbox label="clarity">增强清晰度</el-checkbox>
            <el-checkbox label="efficiency">提高效率</el-checkbox>
            <el-checkbox label="user_satisfaction">用户满意度</el-checkbox>
            <el-checkbox label="consistency">保持一致性</el-checkbox>
            <el-checkbox label="robustness">增强鲁棒性</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <!-- 目标领域 -->
        <el-form-item label="目标领域">
          <el-select 
            v-model="formData.target_domain" 
            placeholder="选择应用领域" 
            clearable
            style="width: 200px"
          >
            <el-option label="产品分析" value="product_analysis" />
            <el-option label="文档解析" value="document_parsing" />
            <el-option label="数据提取" value="data_extraction" />
            <el-option label="质量评估" value="quality_assessment" />
            <el-option label="内容生成" value="content_generation" />
            <el-option label="通用分析" value="general_analysis" />
          </el-select>
        </el-form-item>

        <!-- 权重配置 -->
        <el-form-item label="权重配置">
          <div class="weight-config">
            <div class="weight-item">
              <span>准确性</span>
              <el-slider 
                v-model="formData.priority_weights.accuracy" 
                :min="0" 
                :max="1" 
                :step="0.1"
                show-stops
                show-input
                :input-size="'small'"
                style="width: 300px"
              />
            </div>
            <div class="weight-item">
              <span>清晰度</span>
              <el-slider 
                v-model="formData.priority_weights.clarity" 
                :min="0" 
                :max="1" 
                :step="0.1"
                show-stops
                show-input
                :input-size="'small'"
                style="width: 300px"
              />
            </div>
            <div class="weight-item">
              <span>效率</span>
              <el-slider 
                v-model="formData.priority_weights.efficiency" 
                :min="0" 
                :max="1" 
                :step="0.1"
                show-stops
                show-input
                :input-size="'small'"
                style="width: 300px"
              />
            </div>
            <div class="weight-item">
              <span>用户满意度</span>
              <el-slider 
                v-model="formData.priority_weights.user_satisfaction" 
                :min="0" 
                :max="1" 
                :step="0.1"
                show-stops
                show-input
                :input-size="'small'"
                style="width: 300px"
              />
            </div>
          </div>
        </el-form-item>

        <!-- 操作按钮 -->
        <el-form-item>
          <div class="action-buttons">
            <el-button 
              type="primary" 
              size="large"
              :loading="loading"
              @click="startOptimization"
              :disabled="!canSubmit"
            >
              <template #icon>
                <el-icon><MagicStick /></el-icon>
              </template>
              开始优化
            </el-button>
            
            <el-button 
              size="large" 
              @click="resetForm"
            >
              重置表单
            </el-button>
            
            <el-button 
              type="success" 
              size="large"
              @click="loadTemplate"
            >
              <template #icon>
                <el-icon><Document /></el-icon>
              </template>
              加载模板
            </el-button>
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 快速示例 -->
    <el-card class="example-card">
      <template #header>
        <h3>快速示例</h3>
      </template>
      
      <div class="examples">
        <div 
          v-for="example in examples" 
          :key="example.title"
          class="example-item"
          @click="loadExample(example)"
        >
          <h4>{{ example.title }}</h4>
          <p>{{ example.description }}</p>
          <el-tag size="small" type="info">{{ example.domain }}</el-tag>
        </div>
      </div>
    </el-card>

    <!-- 模板选择对话框 -->
    <el-dialog
      v-model="showTemplateDialog"
      title="选择Prompt模板"
      width="70%"
    >
      <TemplateSelector
        @template-selected="handleTemplateSelected"
        @close="showTemplateDialog = false"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { showMessage } from '@/utils/message'
import { Plus, Delete, MagicStick, Document } from '@element-plus/icons-vue'
import { getOptimizationSuggestions } from '@/api/prompt-optimization'
import TemplateSelector from './TemplateSelector.vue'
import type { 
  PromptOptimizationRequest, 
  PromptOptimizationResponse,
  PromptTemplate 
} from '@/types/prompt-optimization'

// 组件事件
const emit = defineEmits<{
  'optimization-success': [result: PromptOptimizationResponse]
  'optimization-error': [error: string]
}>()

// 响应式数据
const formRef = ref<FormInstance>()
const loading = ref(false)
const showTemplateDialog = ref(false)

// 表单数据
const formData = reactive<PromptOptimizationRequest>({
  current_prompt: '',
  historical_data: {
    success_cases: [],
    failure_cases: []
  },
  optimization_goals: [],
  target_domain: '',
  priority_weights: {
    accuracy: 0.3,
    clarity: 0.3,
    efficiency: 0.2,
    user_satisfaction: 0.2
  }
})

// 新问题输入
const newIssue = ref<Record<number, string>>({})

// 表单验证规则
const formRules: FormRules = {
  current_prompt: [
    { required: true, message: '请输入当前Prompt', trigger: 'blur' },
    { min: 10, message: 'Prompt至少需要10个字符', trigger: 'blur' }
  ],
  optimization_goals: [
    { required: true, message: '请选择至少一个优化目标', trigger: 'change' }
  ]
}

// 计算属性
const canSubmit = computed(() => {
  return formData.current_prompt.trim().length >= 10 && 
         formData.optimization_goals.length > 0
})

// 快速示例数据
const examples = [
  {
    title: '产品文档分析',
    description: '用于分析产品规格文档的Prompt优化示例',
    domain: 'product_analysis',
    data: {
      current_prompt: '请分析以下产品文档，提取产品名称、规格参数、价格信息和主要特性',
      optimization_goals: ['accuracy', 'consistency'],
      target_domain: 'product_analysis'
    }
  },
  {
    title: '数据提取优化',
    description: '提升结构化数据提取准确性的示例',
    domain: 'data_extraction',
    data: {
      current_prompt: '从文档中提取结构化数据，包括表格、列表和关键信息',
      optimization_goals: ['accuracy', 'efficiency'],
      target_domain: 'data_extraction'
    }
  },
  {
    title: '质量评估增强',
    description: '改进内容质量评估的Prompt示例',
    domain: 'quality_assessment',
    data: {
      current_prompt: '评估文档质量，包括完整性、准确性和一致性',
      optimization_goals: ['clarity', 'user_satisfaction'],
      target_domain: 'quality_assessment'
    }
  }
]

// 方法
const addSuccessCase = () => {
  formData.historical_data.success_cases.push({
    prompt: '',
    result_quality: 5,
    user_feedback: '',
    metadata: {}
  })
}

const removeSuccessCase = (index: number) => {
  formData.historical_data.success_cases.splice(index, 1)
}

const addFailureCase = () => {
  const index = formData.historical_data.failure_cases.length
  formData.historical_data.failure_cases.push({
    prompt: '',
    issues: [],
    user_feedback: '',
    metadata: {}
  })
  newIssue.value[index] = ''
}

const removeFailureCase = (index: number) => {
  formData.historical_data.failure_cases.splice(index, 1)
  delete newIssue.value[index]
}

const addIssue = (caseIndex: number) => {
  const issue = newIssue.value[caseIndex]?.trim()
  if (issue) {
    formData.historical_data.failure_cases[caseIndex].issues.push(issue)
    newIssue.value[caseIndex] = ''
  }
}

const removeIssue = (caseIndex: number, issueIndex: number) => {
  formData.historical_data.failure_cases[caseIndex].issues.splice(issueIndex, 1)
}

const startOptimization = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    loading.value = true
    const result = await getOptimizationSuggestions(formData)
    
    if (result.success) {
      emit('optimization-success', result)
      showMessage.success('Prompt优化完成！')
    } else {
      throw new Error(result.error || '优化失败')
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : '优化过程中发生错误'
    emit('optimization-error', message)
    showMessage.error(message)
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  if (!formRef.value) return
  
  ElMessageBox.confirm('确定要重置表单吗？所有输入的数据将丢失。', '确认重置', {
    type: 'warning'
  }).then(() => {
    formRef.value?.resetFields()
    formData.historical_data.success_cases = []
    formData.historical_data.failure_cases = []
    formData.optimization_goals = []
    formData.target_domain = ''
    newIssue.value = {}
    showMessage.success('表单已重置')
  }).catch(() => {
    // 用户取消
  })
}

const loadTemplate = () => {
  showTemplateDialog.value = true
}

const loadExample = (example: any) => {
  ElMessageBox.confirm('确定要加载此示例吗？当前表单数据将被替换。', '确认加载示例', {
    type: 'info'
  }).then(() => {
    Object.assign(formData, {
      ...formData,
      ...example.data
    })
    showMessage.success(`已加载示例：${example.title}`)
  }).catch(() => {
    // 用户取消
  })
}

const handleTemplateSelected = (template: PromptTemplate) => {
  formData.current_prompt = template.template_content
  if (template.category) {
    formData.target_domain = template.category
  }
  showTemplateDialog.value = false
  showMessage.success(`已加载模板：${template.name}`)
}

onMounted(() => {
  // 初始化新问题输入对象
  newIssue.value = {}
})
</script>

<style scoped>
.prompt-optimizer {
  space-y: 20px;
}

.optimizer-card {
  margin-bottom: 20px;
}

.card-header h3 {
  margin: 0 0 5px 0;
  color: #303133;
  font-size: 18px;
  font-weight: 600;
}

.card-header p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.optimizer-form {
  margin-top: 20px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.historical-data-section {
  width: 100%;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 15px;
  background-color: #fafafa;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  font-weight: 500;
  color: #303133;
}

.case-item {
  background: #fff;
  border-radius: 6px;
  padding: 15px;
  margin-bottom: 10px;
  border: 1px solid #e4e7ed;
}

.success-case {
  border-left: 4px solid #67c23a;
}

.failure-case {
  border-left: 4px solid #f56c6c;
}

.case-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.case-title {
  font-weight: 500;
  color: #303133;
}

.case-input {
  margin-bottom: 10px;
}

.case-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.goal-checkboxes {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 10px;
}

.weight-config {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
}

.weight-item {
  display: flex;
  align-items: center;
  gap: 15px;
}

.weight-item span {
  min-width: 80px;
  font-weight: 500;
}

.action-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 20px;
}

.example-card {
  margin-top: 20px;
}

.examples {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 15px;
}

.example-item {
  padding: 15px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
}

.example-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
}

.example-item h4 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 16px;
}

.example-item p {
  margin: 0 0 10px 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.4;
}

.empty-state {
  text-align: center;
  padding: 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .optimizer-form {
    :deep(.el-form-item__label) {
      width: auto !important;
      text-align: left;
      margin-bottom: 5px;
    }
    
    :deep(.el-form-item__content) {
      margin-left: 0 !important;
    }
  }
  
  .goal-checkboxes {
    grid-template-columns: 1fr;
  }
  
  .weight-config {
    grid-template-columns: 1fr;
  }
  
  .weight-item {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  
  .action-buttons {
    flex-direction: column;
    align-items: stretch;
  }
  
  .examples {
    grid-template-columns: 1fr;
  }
  
  .case-meta {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>