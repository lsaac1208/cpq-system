<template>
  <div class="create-product-ai">
    <!-- 页面头部 -->
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ name: 'products' }">产品管理</el-breadcrumb-item>
        <el-breadcrumb-item>AI智能创建</el-breadcrumb-item>
      </el-breadcrumb>
      
      <div class="header-content">
        <h1 class="page-title">
          <el-icon><MagicStick /></el-icon>
          AI智能产品创建
        </h1>
        <p class="page-description">
          上传产品相关文档，AI将自动分析并提取产品信息，大幅提升产品录入效率
        </p>
      </div>
    </div>

    <!-- 创建步骤指示器 -->
    <el-card class="steps-card">
      <el-steps :active="currentStep" align-center>
        <el-step title="上传文档" icon="Upload">
          <template #description>
            上传产品相关文档
          </template>
        </el-step>
        <el-step title="AI分析" icon="MagicStick">
          <template #description>
            AI智能提取产品信息
          </template>
        </el-step>
        <el-step title="结果预览" icon="View">
          <template #description>
            预览并确认分析结果
          </template>
        </el-step>
        <el-step title="创建产品" icon="Check">
          <template #description>
            确认创建产品
          </template>
        </el-step>
      </el-steps>
    </el-card>

    <!-- 步骤1: 文档上传 -->
    <div v-show="currentStep === 0" class="step-content">
      <AIDocumentUpload
        ref="documentUploadRef"
        @analysis-start="handleAnalysisStart"
        @analysis-success="handleAnalysisSuccess"
        @analysis-error="handleAnalysisError"
        @analysis-complete="handleAnalysisComplete"
      />
    </div>

    <!-- 步骤2: 分析预览 -->
    <div v-show="currentStep >= 1 && analysisResult" class="step-content">
      <AIAnalysisPreview
        ref="analysisPreviewRef"
        :analysis-result="analysisResult"
        :categories="productCategories"
        @product-created="handleProductCreated"
        @cancel="handleCancel"
        @field-modified="handleFieldModified"
      />
    </div>

    <!-- 成功创建提示 -->
    <el-result
      v-if="currentStep === 3 && createdProduct"
      icon="success"
      title="产品创建成功！"
      :sub-title="'产品 ' + (createdProduct?.name || '') + ' 已成功创建'"
      class="success-result"
    >
      <template #extra>
        <el-space>
          <el-button
            type="primary"
            @click="viewCreatedProduct"
          >
            查看产品详情
          </el-button>
          <el-button @click="createAnother">
            继续创建
          </el-button>
          <el-button @click="goBack">
            返回产品列表
          </el-button>
        </el-space>
      </template>
    </el-result>

    <!-- 快速操作面板 -->
    <el-card v-if="currentStep < 3" class="quick-actions">
      <template #header>
        <span class="card-title">
          <el-icon><Operation /></el-icon>
          快速操作
        </span>
      </template>

      <el-space wrap>
        <el-button
          v-if="currentStep > 0"
          type="info"
          @click="goToPreviousStep"
        >
          <el-icon><ArrowLeft /></el-icon>
          上一步
        </el-button>
        
        <el-button
          type="warning"
          @click="resetWorkflow"
        >
          <el-icon><RefreshRight /></el-icon>
          重新开始
        </el-button>
        
        <el-button @click="goBack">
          <el-icon><Back /></el-icon>
          返回列表
        </el-button>
        
        <el-button
          type="success"
          @click="goToTraditionalCreate"
        >
          <el-icon><Edit /></el-icon>
          传统创建
        </el-button>
      </el-space>
    </el-card>

    <!-- 帮助信息 -->
    <el-card class="help-card">
      <template #header>
        <span class="card-title">
          <el-icon><QuestionFilled /></el-icon>
          使用帮助
        </span>
      </template>

      <el-collapse v-model="activeHelp">
        <el-collapse-item title="支持的文档格式" name="formats">
          <div class="help-content">
            <p><strong>文本文档:</strong> TXT, PDF, Word文档 (DOC/DOCX)</p>
            <p><strong>图片文档:</strong> PNG, JPG, JPEG (通过OCR识别)</p>
            <p><strong>建议:</strong> 文档内容越详细，AI提取的信息越准确</p>
          </div>
        </el-collapse-item>
        
        <el-collapse-item title="最佳实践" name="best-practices">
          <div class="help-content">
            <ul>
              <li>使用包含完整产品规格的正式文档</li>
              <li>确保文档中包含产品名称、型号等关键信息</li>
              <li>技术参数表格式的文档效果更好</li>
              <li>分析后请仔细检查并修正AI提取的信息</li>
            </ul>
          </div>
        </el-collapse-item>
        
        <el-collapse-item title="置信度说明" name="confidence">
          <div class="help-content">
            <p><strong>高置信度 (80%+):</strong> <el-tag type="success" size="small">绿色</el-tag> 信息准确，可直接使用</p>
            <p><strong>中等置信度 (60-79%):</strong> <el-tag type="warning" size="small">黄色</el-tag> 建议人工核实</p>
            <p><strong>低置信度 (<60%):</strong> <el-tag type="danger" size="small">红色</el-tag> 需要人工修正</p>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { showMessage } from '@/utils/message'
import {
  MagicStick, Upload, View, Check, Operation, ArrowLeft, RefreshRight,
  Back, Edit, QuestionFilled
} from '@element-plus/icons-vue'

import AIDocumentUpload from '@/components/AIDocumentUpload.vue'
import AIAnalysisPreview from '@/components/AIAnalysisPreview.vue'
import type { AIAnalysisResult } from '@/types/ai-analysis'
import { productsApi } from '@/api/products'

const router = useRouter()

// 响应式数据
const currentStep = ref(0)
const analysisResult = ref<AIAnalysisResult | null>(null)
const createdProduct = ref<any>(null)
const productCategories = ref<string[]>([])
const activeHelp = ref([])

// 组件引用
const documentUploadRef = ref()
const analysisPreviewRef = ref()

// 生命周期
onMounted(async () => {
  await loadProductCategories()
})

// 计算属性
const stepTitles = computed(() => [
  '上传文档',
  'AI分析',
  '结果预览',
  '创建产品'
])

// 方法
const loadProductCategories = async () => {
  try {
    const response = await productsApi.getCategories()
    productCategories.value = response.categories || []
  } catch (error) {
    console.error('Failed to load categories:', error)
  }
}

const handleAnalysisStart = () => {
  currentStep.value = 1
  analysisResult.value = null
  showMessage.info('开始分析文档...')
}

const handleAnalysisSuccess = (result: AIAnalysisResult) => {
  analysisResult.value = result
  currentStep.value = 2
  
  showMessage.success('文档分析完成！请检查提取的信息')
  
  // 滚动到分析结果
  nextTick(() => {
    document.querySelector('.step-content')?.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    })
  })
}

const handleAnalysisError = (error: string) => {
  showMessage.error(`分析失败: ${error}`)
  currentStep.value = 0
}

const handleAnalysisComplete = () => {
  // 分析完成的处理逻辑
}

const handleProductCreated = (productId: number) => {
  // 获取创建的产品信息
  if (analysisResult.value) {
    createdProduct.value = {
      id: productId,
      name: analysisResult.value.extracted_data.basic_info.name,
      code: analysisResult.value.extracted_data.basic_info.code
    }
  }
  
  currentStep.value = 3
  // 注意：AI分析预览组件会自动跳转到产品详情页，所以这个成功消息可能不会显示
  showMessage.success('产品创建成功！正在跳转到产品详情页...')
}

const handleCancel = () => {
  ElMessageBox.confirm(
    '确定要取消当前操作吗？未保存的数据将会丢失。',
    '确认取消',
    {
      confirmButtonText: '确定',
      cancelButtonText: '继续编辑',
      type: 'warning'
    }
  ).then(() => {
    goBack()
  }).catch(() => {
    // 用户选择继续编辑
  })
}

const handleFieldModified = (field: string, value: any) => {
  console.log('Field modified:', field, value)
  // 可以在这里记录用户的修改行为
}

const goToPreviousStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const resetWorkflow = () => {
  ElMessageBox.confirm(
    '确定要重新开始吗？当前进度将会丢失。',
    '重新开始',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    currentStep.value = 0
    analysisResult.value = null
    createdProduct.value = null
    
    // 重置上传组件
    if (documentUploadRef.value) {
      documentUploadRef.value.clearFile()
    }
    
    showMessage.success('已重置，请重新上传文档')
  }).catch(() => {
    // 用户取消
  })
}

const goBack = () => {
  router.push({ name: 'Products' })
}

const goToTraditionalCreate = () => {
  router.push({ name: 'CreateProduct' })
}

const viewCreatedProduct = () => {
  if (createdProduct.value) {
    router.push({
      name: 'ProductDetail',
      params: { id: createdProduct.value.id }
    })
  }
}

const createAnother = () => {
  resetWorkflow()
}

// 页面标题
document.title = 'AI智能产品创建 - CPQ系统'
</script>

<style scoped>
.create-product-ai {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-header :deep(.el-breadcrumb) {
  margin-bottom: 16px;
}

.header-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 32px;
  border-radius: 12px;
  color: white;
  text-align: center;
}

.page-title {
  margin: 0 0 12px 0;
  font-size: 28px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.page-description {
  margin: 0;
  font-size: 16px;
  opacity: 0.9;
  line-height: 1.5;
}

.steps-card {
  margin-bottom: 32px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.steps-card :deep(.el-card__body) {
  padding: 32px;
}

.step-content {
  margin-bottom: 32px;
  animation: fadeInUp 0.5s ease-out;
}

.success-result {
  margin: 32px 0;
  padding: 32px;
  border-radius: 12px;
  background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
}

.quick-actions {
  margin-bottom: 24px;
  border-radius: 12px;
}

.quick-actions :deep(.el-space) {
  width: 100%;
  justify-content: center;
}

.help-card {
  border-radius: 12px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.help-content {
  line-height: 1.6;
  color: #606266;
}

.help-content p {
  margin: 8px 0;
}

.help-content ul {
  margin: 8px 0;
  padding-left: 20px;
}

.help-content li {
  margin: 4px 0;
}

/* 动画效果 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .create-product-ai {
    padding: 16px;
  }
  
  .header-content {
    padding: 24px 16px;
  }
  
  .page-title {
    font-size: 24px;
    flex-direction: column;
    gap: 8px;
  }
  
  .page-description {
    font-size: 14px;
  }
  
  .steps-card :deep(.el-card__body) {
    padding: 20px;
  }
  
  .quick-actions :deep(.el-space) {
    flex-direction: column;
  }
  
  .quick-actions :deep(.el-space .el-button) {
    width: 100%;
  }
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
  .header-content {
    background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
  }
  
  .success-result {
    background: linear-gradient(135deg, #2a4d4a 0%, #4a2d42 100%);
  }
}
</style>