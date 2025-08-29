<template>
  <div class="create-product">
    <!-- 页面头部 -->
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ name: 'Products' }">产品管理</el-breadcrumb-item>
        <el-breadcrumb-item>创建产品</el-breadcrumb-item>
      </el-breadcrumb>
      
      <div class="header-content">
        <h1 class="page-title">
          <el-icon><Plus /></el-icon>
          创建产品
        </h1>
        <p class="page-description">
          手动录入产品详细信息，支持完整的产品信息管理
        </p>
      </div>
    </div>

    <!-- 创建模式选择 -->
    <el-card class="mode-selection-card">
      <template #header>
        <span class="card-title">
          <el-icon><Operation /></el-icon>
          创建模式选择
        </span>
      </template>

      <div class="mode-options">
        <div class="mode-option active">
          <div class="mode-icon">
            <el-icon><Edit /></el-icon>
          </div>
          <div class="mode-info">
            <h3>手动创建</h3>
            <p>逐步填写产品信息，适合精确控制产品详情</p>
          </div>
          <div class="mode-status">
            <el-tag type="primary">当前模式</el-tag>
          </div>
        </div>
        
        <div class="mode-option" @click="switchToAIMode">
          <div class="mode-icon">
            <el-icon><MagicStick /></el-icon>
          </div>
          <div class="mode-info">
            <h3>AI智能创建</h3>
            <p>上传文档，AI自动提取产品信息，快速高效</p>
          </div>
          <div class="mode-status">
            <el-button type="success" size="small">
              <el-icon><Switch /></el-icon>
              切换模式
            </el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 产品表单 -->
    <ProductForm
      ref="productFormRef"
      :categories="categories"
      :loading="loading"
      @submit="handleSubmit"
      @cancel="handleCancel"
    />

    <!-- 快速操作面板 -->
    <el-card class="quick-actions">
      <template #header>
        <span class="card-title">
          <el-icon><Operation /></el-icon>
          快速操作
        </span>
      </template>

      <el-space wrap>
        <el-button @click="handleCancel">
          <el-icon><Back /></el-icon>
          返回列表
        </el-button>
        
        <el-button
          type="success"
          @click="switchToAIMode"
        >
          <el-icon><MagicStick /></el-icon>
          AI智能创建
        </el-button>
        
        <el-button
          type="warning"
          @click="resetForm"
        >
          <el-icon><RefreshRight /></el-icon>
          重置表单
        </el-button>
      </el-space>
    </el-card>

    <!-- 帮助信息 -->
    <el-card class="help-card">
      <template #header>
        <span class="card-title">
          <el-icon><QuestionFilled /></el-icon>
          填写指南
        </span>
      </template>

      <el-collapse v-model="activeHelp">
        <el-collapse-item title="基本信息填写" name="basic">
          <div class="help-content">
            <p><strong>产品名称:</strong> 简洁明了的产品名称，便于识别和搜索</p>
            <p><strong>产品代码:</strong> 唯一的产品标识符，建议使用字母数字组合</p>
            <p><strong>分类:</strong> 产品所属类别，可选择现有分类或创建新分类</p>
            <p><strong>基础价格:</strong> 产品的标准价格，支持小数</p>
          </div>
        </el-collapse-item>
        
        <el-collapse-item title="技术规格说明" name="specifications">
          <div class="help-content">
            <ul>
              <li>技术规格用于描述产品的具体参数</li>
              <li>每个规格包含名称、值、单位和描述</li>
              <li>建议按重要性和类型分组填写</li>
              <li>单位字段可选，但建议填写以提高专业性</li>
            </ul>
          </div>
        </el-collapse-item>
        
        <el-collapse-item title="配置架构设置" name="configuration">
          <div class="help-content">
            <p>当产品支持配置时，需要定义配置架构：</p>
            <ul>
              <li><strong>文本类型:</strong> 适用于名称、描述等文本输入</li>
              <li><strong>数字类型:</strong> 适用于尺寸、重量等数值输入</li>
              <li><strong>布尔类型:</strong> 适用于是/否选择</li>
              <li><strong>选择类型:</strong> 单选，需要预设选项</li>
              <li><strong>多选类型:</strong> 多选，需要预设选项</li>
            </ul>
          </div>
        </el-collapse-item>
        
        <el-collapse-item title="图片上传建议" name="images">
          <div class="help-content">
            <div class="image-tips">
              <h4>单图模式:</h4>
              <ul>
                <li>适合只有一张主图的产品</li>
                <li>支持快速上传和压缩优化</li>
                <li>建议图片尺寸不小于 800x600</li>
              </ul>
              
              <h4>图集模式:</h4>
              <ul>
                <li>适合多角度、多规格的产品展示</li>
                <li>支持批量上传和图集管理</li>
                <li>可设置主图和排序</li>
              </ul>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { showMessage } from '@/utils/message'
import {
  Plus, Operation, Edit, MagicStick, Switch, Back, RefreshRight,
  QuestionFilled
} from '@element-plus/icons-vue'

import ProductForm from '@/components/ProductForm.vue'
import { productsApi } from '@/api/products'
import type { ProductFormData } from '@/types/product'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const categories = ref<string[]>([])
const activeHelp = ref(['basic'])

// 组件引用
const productFormRef = ref()

// 生命周期
onMounted(async () => {
  await loadCategories()
})

// 方法
const loadCategories = async () => {
  try {
    const response = await productsApi.getCategories()
    categories.value = response.categories || []
  } catch (error) {
    console.error('Failed to load categories:', error)
    showMessage.error('加载产品分类失败')
  }
}

const handleSubmit = async (formData: ProductFormData, pendingImageFile?: File) => {
  loading.value = true
  
  try {
    const response = await productsApi.createProduct(formData)
    
    if (response && response.product && response.product.id) {
      showMessage.success('产品创建成功！')
      
      // 如果有待上传的图片，通知表单组件处理
      if (pendingImageFile && productFormRef.value?.uploadImageAfterCreate) {
        await productFormRef.value.uploadImageAfterCreate(response.product.id.toString())
      }
      
      // 延迟跳转，让用户看到成功消息
      setTimeout(() => {
        router.push({
          name: 'ProductDetail',
          params: { id: response.product.id }
        })
      }, 1500)
    } else {
      showMessage.error('产品创建失败：服务器响应异常')
    }
  } catch (error: any) {
    console.error('Create product error:', error)
    
    let errorMessage = '产品创建失败'
    if (error.response?.data?.error) {
      errorMessage = error.response.data.error
    } else if (error.message) {
      errorMessage = error.message
    }
    
    showMessage.error(errorMessage)
  } finally {
    loading.value = false
  }
}

const handleCancel = () => {
  ElMessageBox.confirm(
    '确定要离开吗？未保存的数据将会丢失。',
    '确认离开',
    {
      confirmButtonText: '确定离开',
      cancelButtonText: '继续编辑',
      type: 'warning'
    }
  ).then(() => {
    router.push({ name: 'Products' })
  }).catch(() => {
    // 用户选择继续编辑
  })
}

const switchToAIMode = () => {
  ElMessageBox.confirm(
    '切换到AI智能创建模式？当前填写的数据将会丢失。',
    '切换创建模式',
    {
      confirmButtonText: '切换到AI模式',
      cancelButtonText: '继续手动创建',
      type: 'info'
    }
  ).then(() => {
    router.push({ name: 'CreateProductAI' })
  }).catch(() => {
    // 用户选择继续手动创建
  })
}

const resetForm = () => {
  ElMessageBox.confirm(
    '确定要重置表单吗？所有填写的数据将会清空。',
    '重置表单',
    {
      confirmButtonText: '确定重置',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    if (productFormRef.value) {
      // 重置表单的逻辑由ProductForm组件处理
      location.reload() // 简单的重置方式
    }
    showMessage.success('表单已重置')
  }).catch(() => {
    // 用户取消重置
  })
}

// 页面标题
document.title = '创建产品 - CPQ系统'
</script>

<style scoped>
.create-product {
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
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
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

.mode-selection-card {
  margin-bottom: 32px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.mode-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
}

.mode-option {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
}

.mode-option:hover {
  border-color: #3b82f6;
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(59, 130, 246, 0.15);
}

.mode-option.active {
  border-color: #6366f1;
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
}

.mode-icon {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  font-size: 24px;
}

.mode-info {
  flex: 1;
}

.mode-info h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.mode-info p {
  margin: 0;
  font-size: 14px;
  color: #6b7280;
  line-height: 1.5;
}

.mode-status {
  flex-shrink: 0;
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

.help-content h4 {
  margin: 16px 0 8px 0;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.image-tips {
  background: #f8fafc;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.image-tips h4 {
  color: #1f2937;
  margin-top: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .create-product {
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
  
  .mode-options {
    grid-template-columns: 1fr;
  }
  
  .mode-option {
    flex-direction: column;
    text-align: center;
  }
  
  .mode-info {
    text-align: center;
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
    background: linear-gradient(135deg, #4c1d95 0%, #581c87 100%);
  }
  
  .mode-option {
    background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
    border-color: #374151;
  }
  
  .mode-option.active {
    background: linear-gradient(135deg, #312e81 0%, #3730a3 100%);
    border-color: #6366f1;
  }
  
  .mode-info h3 {
    color: #f9fafb;
  }
  
  .mode-info p {
    color: #d1d5db;
  }
}
</style>