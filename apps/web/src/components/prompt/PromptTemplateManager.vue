<template>
  <div class="prompt-template-manager">
    <div class="manager-header">
      <h3>Prompt模板管理</h3>
      <p>管理和编辑AI分析的Prompt模板，提升分析效果</p>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        新建模板
      </el-button>
    </div>

    <!-- 模板列表 -->
    <div class="templates-list">
      <el-row :gutter="20">
        <el-col 
          v-for="template in templates" 
          :key="template.id"
          :span="8"
        >
          <el-card class="template-card" shadow="hover">
            <template #header>
              <div class="template-header">
                <span class="template-name">{{ template.name }}</span>
                <el-dropdown @command="handleCommand">
                  <el-button text size="small">
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item :command="`edit-${template.id}`">
                        编辑
                      </el-dropdown-item>
                      <el-dropdown-item :command="`copy-${template.id}`">
                        复制
                      </el-dropdown-item>
                      <el-dropdown-item :command="`delete-${template.id}`" divided>
                        删除
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </template>
            
            <div class="template-content">
              <div class="template-meta">
                <el-tag :type="getTypeColor(template.type)" size="small">
                  {{ template.type }}
                </el-tag>
                <span class="template-usage">使用次数: {{ template.usageCount }}</span>
              </div>
              
              <div class="template-description">
                {{ template.description }}
              </div>
              
              <div class="template-preview">
                <el-input
                  v-model="template.content"
                  type="textarea"
                  :rows="3"
                  readonly
                  resize="none"
                />
              </div>
              
              <div class="template-stats">
                <div class="stat-item">
                  <span class="stat-label">成功率:</span>
                  <span class="stat-value">{{ template.successRate }}%</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">平均时长:</span>
                  <span class="stat-value">{{ template.avgTime }}s</span>
                </div>
              </div>
              
              <div class="template-actions">
                <el-button size="small" @click="useTemplate(template)">
                  使用模板
                </el-button>
                <el-button size="small" type="primary" @click="editTemplate(template)">
                  编辑
                </el-button>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingTemplate ? '编辑模板' : '新建模板'"
      width="60%"
      @close="resetForm"
    >
      <el-form
        ref="templateFormRef"
        :model="templateForm"
        :rules="templateRules"
        label-width="100px"
      >
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="templateForm.name" placeholder="请输入模板名称" />
        </el-form-item>
        
        <el-form-item label="模板类型" prop="type">
          <el-select v-model="templateForm.type" placeholder="请选择模板类型">
            <el-option label="产品信息提取" value="product_extraction" />
            <el-option label="技术规格分析" value="specification_analysis" />
            <el-option label="文档分类" value="document_classification" />
            <el-option label="质量评估" value="quality_assessment" />
            <el-option label="综合分析" value="comprehensive_analysis" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="模板描述" prop="description">
          <el-input 
            v-model="templateForm.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入模板描述"
          />
        </el-form-item>
        
        <el-form-item label="Prompt内容" prop="content">
          <el-input 
            v-model="templateForm.content" 
            type="textarea" 
            :rows="8"
            placeholder="请输入Prompt内容，支持变量：{document}, {context}, {requirements}"
          />
        </el-form-item>
        
        <el-form-item label="预期输出">
          <el-input 
            v-model="templateForm.expectedOutput" 
            type="textarea" 
            :rows="4"
            placeholder="描述预期的输出格式和内容"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="saveTemplate" :loading="saving">
            {{ editingTemplate ? '更新' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessageBox } from 'element-plus'
import { showMessage } from '@/utils/message'
import { Plus, MoreFilled } from '@element-plus/icons-vue'

const emit = defineEmits(['template-saved', 'template-used'])

// 响应式数据
const showCreateDialog = ref(false)
const editingTemplate = ref<any>(null)
const saving = ref(false)
const templateFormRef = ref()

// 模板表单
const templateForm = reactive({
  name: '',
  type: '',
  description: '',
  content: '',
  expectedOutput: ''
})

// 表单验证规则
const templateRules = {
  name: [
    { required: true, message: '请输入模板名称', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择模板类型', trigger: 'change' }
  ],
  description: [
    { required: true, message: '请输入模板描述', trigger: 'blur' }
  ],
  content: [
    { required: true, message: '请输入Prompt内容', trigger: 'blur' },
    { min: 50, message: 'Prompt内容至少50个字符', trigger: 'blur' }
  ]
}

// 模拟模板数据
const templates = ref([
  {
    id: 1,
    name: '产品规格提取模板',
    type: '产品信息提取',
    description: '专门用于提取产品技术规格和基本信息的模板',
    content: '请分析以下产品文档，提取产品的基本信息、技术规格、产品特性等关键信息。\n\n文档内容：{document}\n\n请按照以下JSON格式返回结果：\n{\n  "basic_info": {\n    "name": "产品名称",\n    "code": "产品代码",\n    "category": "产品类别"\n  },\n  "specifications": {},\n  "features": []\n}',
    expectedOutput: 'JSON格式的产品信息',
    usageCount: 156,
    successRate: 94,
    avgTime: 45.2
  },
  {
    id: 2,
    name: '文档质量评估模板',
    type: '质量评估',
    description: '评估文档的完整性、准确性和可用性',
    content: '请对以下文档进行质量评估，从完整性、准确性、可读性等维度进行分析。\n\n文档内容：{document}\n\n评估要求：{requirements}\n\n请提供详细的评估报告和改进建议。',
    expectedOutput: '质量评估报告和改进建议',
    usageCount: 89,
    successRate: 87,
    avgTime: 62.1
  },
  {
    id: 3,
    name: '技术文档分类模板',
    type: '文档分类',
    description: '自动识别和分类技术文档类型',
    content: '请分析以下文档并确定其类型和类别。\n\n文档内容：{document}\n\n上下文信息：{context}\n\n请判断文档类型并提供分类依据。',
    expectedOutput: '文档分类结果和分类依据',
    usageCount: 234,
    successRate: 91,
    avgTime: 28.5
  }
])

// 方法
const getTypeColor = (type: string) => {
  const typeColors: Record<string, string> = {
    '产品信息提取': 'primary',
    '质量评估': 'success',
    '文档分类': 'warning',
    '技术规格分析': 'info',
    '综合分析': 'danger'
  }
  return typeColors[type] || 'info'
}

const handleCommand = (command: string) => {
  const [action, id] = command.split('-')
  const template = templates.value.find(t => t.id === parseInt(id))
  
  if (!template) return
  
  switch (action) {
    case 'edit':
      editTemplate(template)
      break
    case 'copy':
      copyTemplate(template)
      break
    case 'delete':
      deleteTemplate(template)
      break
  }
}

const useTemplate = (template: any) => {
  emit('template-used', template)
  showMessage.success(`已应用模板：${template.name}`)
}

const editTemplate = (template: any) => {
  editingTemplate.value = template
  Object.assign(templateForm, template)
  showCreateDialog.value = true
}

const copyTemplate = (template: any) => {
  const newTemplate = {
    ...template,
    id: Date.now(),
    name: `${template.name} - 副本`,
    usageCount: 0
  }
  templates.value.push(newTemplate)
  showMessage.success('模板复制成功')
}

const deleteTemplate = async (template: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模板"${template.name}"吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const index = templates.value.findIndex(t => t.id === template.id)
    if (index > -1) {
      templates.value.splice(index, 1)
      showMessage.success('模板删除成功')
    }
  } catch {
    // 用户取消删除
  }
}

const saveTemplate = async () => {
  if (!templateFormRef.value) return
  
  try {
    await templateFormRef.value.validate()
    saving.value = true
    
    // 模拟保存延迟
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    if (editingTemplate.value) {
      // 更新现有模板
      Object.assign(editingTemplate.value, templateForm)
      showMessage.success('模板更新成功')
    } else {
      // 创建新模板
      const newTemplate = {
        ...templateForm,
        id: Date.now(),
        usageCount: 0,
        successRate: 0,
        avgTime: 0
      }
      templates.value.push(newTemplate)
      showMessage.success('模板创建成功')
    }
    
    emit('template-saved')
    showCreateDialog.value = false
    resetForm()
  } catch (error) {
    console.error('保存模板失败:', error)
  } finally {
    saving.value = false
  }
}

const resetForm = () => {
  editingTemplate.value = null
  Object.assign(templateForm, {
    name: '',
    type: '',
    description: '',
    content: '',
    expectedOutput: ''
  })
  if (templateFormRef.value) {
    templateFormRef.value.clearValidate()
  }
}

onMounted(() => {
  // 组件挂载时的初始化
})
</script>

<style scoped>
.prompt-template-manager {
  padding: 20px;
}

.manager-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.manager-header div {
  flex: 1;
}

.manager-header h3 {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.manager-header p {
  color: #909399;
  margin: 0;
}

.templates-list {
  margin-bottom: 24px;
}

.template-card {
  margin-bottom: 20px;
  height: 100%;
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.template-name {
  font-weight: 500;
  color: #303133;
}

.template-content {
  padding: 16px 0;
}

.template-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.template-usage {
  font-size: 12px;
  color: #909399;
}

.template-description {
  color: #606266;
  margin-bottom: 12px;
  line-height: 1.6;
}

.template-preview {
  margin-bottom: 12px;
}

.template-stats {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
  padding: 8px 12px;
  background-color: #F5F7FA;
  border-radius: 4px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.template-actions {
  display: flex;
  gap: 8px;
}

.dialog-footer {
  display: flex;
  gap: 12px;
}
</style>