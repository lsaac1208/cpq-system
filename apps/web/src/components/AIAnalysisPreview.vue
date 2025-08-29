<template>
  <div class="ai-analysis-preview">
    <!-- 分析概览 -->
    <el-card class="summary-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon><DataAnalysis /></el-icon>
            分析结果概览
          </span>
          <el-tag
            :type="confidenceType"
            size="large"
          >
            总体置信度: {{ (confidenceScores?.overall * 100 || 0).toFixed(0) }}%
          </el-tag>
        </div>
      </template>

      <div class="summary-content">
        <div class="summary-item">
          <span class="label">文档名称:</span>
          <span class="value">{{ documentInfo?.filename || 'N/A' }}</span>
        </div>
        <div class="summary-item">
          <span class="label">分析摘要:</span>
          <span class="value">{{ summary || '无摘要信息' }}</span>
        </div>
        <div class="summary-item">
          <span class="label">分析时长:</span>
          <span class="value">{{ documentInfo?.analysis_duration || 0 }}秒</span>
        </div>
      </div>

      <!-- 置信度分布 -->
      <div class="confidence-breakdown">
        <h4>各模块置信度</h4>
        <div class="confidence-items">
          <div
            v-for="(score, key) in confidenceBreakdown"
            :key="key"
            class="confidence-item"
          >
            <span class="confidence-label">{{ getConfidenceLabel(key) }}</span>
            <el-progress
              :percentage="(score || 0) * 100"
              :color="getConfidenceColor(score || 0)"
              :stroke-width="8"
            />
            <span class="confidence-value">{{ ((score || 0) * 100).toFixed(0) }}%</span>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 产品基础信息 -->
    <el-card class="data-section">
      <template #header>
        <div class="section-header">
          <span class="section-title">
            <el-icon><Box /></el-icon>
            基础信息
          </span>
          <el-tag
            :type="getConfidenceTagType(confidenceScores?.basic_info || 0)"
            size="small"
          >
            {{ (confidenceScores?.basic_info * 100 || 0).toFixed(0) }}%
          </el-tag>
        </div>
      </template>

      <div class="editable-fields">
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="field-item">
              <label class="field-label">产品名称 *</label>
              <el-input
                v-model="editableData.basic_info.name"
                :class="getFieldClass('basic_info', 'name')"
                placeholder="请输入产品名称"
                @change="markFieldAsModified('basic_info.name')"
              />
            </div>
          </el-col>
          
          <el-col :span="12">
            <div class="field-item">
              <label class="field-label">产品代码 *</label>
              <el-input
                v-model="editableData.basic_info.code"
                :class="getFieldClass('basic_info', 'code')"
                placeholder="请输入产品代码"
                @change="markFieldAsModified('basic_info.code')"
              />
            </div>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <div class="field-item">
              <label class="field-label">产品分类 *</label>
              <el-select
                v-model="editableData.basic_info.category"
                :class="getFieldClass('basic_info', 'category')"
                placeholder="选择或输入分类"
                filterable
                allow-create
                style="width: 100%"
                @change="markFieldAsModified('basic_info.category')"
              >
                <el-option
                  v-for="category in predefinedCategories"
                  :key="category"
                  :label="category"
                  :value="category"
                />
              </el-select>
            </div>
          </el-col>
          
          <el-col :span="12">
            <div class="field-item">
              <label class="field-label">基础价格</label>
              <el-input-number
                v-model="editableData.basic_info.base_price"
                :class="getFieldClass('basic_info', 'base_price')"
                :precision="2"
                :min="0"
                style="width: 100%"
                @change="markFieldAsModified('basic_info.base_price')"
              />
            </div>
          </el-col>
        </el-row>

        <div class="field-item">
          <label class="field-label">产品描述</label>
          <el-input
            v-model="editableData.basic_info.description"
            :class="getFieldClass('basic_info', 'description')"
            type="textarea"
            :rows="3"
            placeholder="请输入产品描述"
            @change="markFieldAsModified('basic_info.description')"
          />
        </div>
      </div>
    </el-card>

    <!-- 技术规格 -->
    <el-card v-if="hasSpecifications" class="data-section">
      <template #header>
        <div class="section-header">
          <span class="section-title">
            <el-icon><Setting /></el-icon>
            技术规格
          </span>
          <el-tag
            :type="getConfidenceTagType(confidenceScores?.specifications || 0)"
            size="small"
          >
            {{ (confidenceScores?.specifications * 100 || 0).toFixed(0) }}%
          </el-tag>
        </div>
      </template>

      <div class="specifications-list">
        <div
          v-for="(spec, key) in editableData.specifications"
          :key="key"
          class="spec-item"
        >
          <el-row :gutter="16" align="middle">
            <el-col :span="6">
              <el-input
                :value="key"
                readonly
                size="small"
                class="spec-key"
              />
            </el-col>
            <el-col :span="6">
              <el-input
                v-model="spec.value"
                size="small"
                placeholder="值"
                @change="markFieldAsModified(`specifications.${key}.value`)"
              />
            </el-col>
            <el-col :span="4">
              <el-input
                v-model="spec.unit"
                size="small"
                placeholder="单位"
                @change="markFieldAsModified(`specifications.${key}.unit`)"
              />
            </el-col>
            <el-col :span="6">
              <el-input
                v-model="spec.description"
                size="small"
                placeholder="描述"
                @change="markFieldAsModified(`specifications.${key}.description`)"
              />
            </el-col>
            <el-col :span="2">
              <el-button
                type="danger"
                size="small"
                @click="removeSpecification(key)"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </el-col>
          </el-row>
        </div>
        
        <el-button
          type="primary"
          size="small"
          @click="addSpecification"
        >
          <el-icon><Plus /></el-icon>
          添加规格
        </el-button>
      </div>
    </el-card>

    <!-- 产品特性 -->
    <el-card v-if="hasFeatures" class="data-section">
      <template #header>
        <div class="section-header">
          <span class="section-title">
            <el-icon><Star /></el-icon>
            产品特性
          </span>
          <el-tag
            :type="getConfidenceTagType(confidenceScores?.features || 0)"
            size="small"
          >
            {{ (confidenceScores?.features * 100 || 0).toFixed(0) }}%
          </el-tag>
        </div>
      </template>

      <div class="features-list">
        <div
          v-for="(feature, index) in editableData.features"
          :key="index"
          class="feature-item"
        >
          <el-card size="small">
            <el-row :gutter="16">
              <el-col :span="8">
                <label class="field-label">特性标题</label>
                <el-input
                  v-model="feature.title"
                  placeholder="特性标题"
                  @change="markFieldAsModified(`features.${index}.title`)"
                />
              </el-col>
              <el-col :span="14">
                <label class="field-label">特性描述</label>
                <el-input
                  v-model="feature.description"
                  type="textarea"
                  :rows="2"
                  placeholder="详细描述"
                  @change="markFieldAsModified(`features.${index}.description`)"
                />
              </el-col>
              <el-col :span="2">
                <el-button
                  type="danger"
                  size="small"
                  @click="removeFeature(index)"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-col>
            </el-row>
          </el-card>
        </div>
        
        <el-button
          type="primary"
          size="small"
          @click="addFeature"
        >
          <el-icon><Plus /></el-icon>
          添加特性
        </el-button>
      </div>
    </el-card>

    <!-- 文档预览 -->
    <el-card class="text-preview">
      <template #header>
        <div class="section-header">
          <span class="section-title">
            <el-icon><Document /></el-icon>
            文档内容预览
          </span>
          <el-button
            size="small"
            @click="showFullText = !showFullText"
          >
            {{ showFullText ? '收起' : '展开' }}
          </el-button>
        </div>
      </template>

      <div class="text-content">
        <el-scrollbar :height="showFullText ? '300px' : '100px'">
          <pre class="text-preview-content">{{ textPreview }}</pre>
        </el-scrollbar>
      </div>
    </el-card>

    <!-- 操作按钮 -->
    <div class="action-buttons">
      <el-button
        type="primary"
        size="large"
        :loading="creating"
        @click="confirmCreateProduct"
      >
        <el-icon><Check /></el-icon>
        {{ creating ? '创建中...' : '创建产品并查看详情' }}
      </el-button>
      
      <el-button
        size="large"
        @click="$emit('cancel')"
      >
        取消
      </el-button>
      
      <el-button
        type="info"
        size="large"
        @click="resetToOriginal"
      >
        <el-icon><RefreshRight /></el-icon>
        重置修改
      </el-button>
    </div>

    <!-- 验证提示 -->
    <el-alert
      v-if="validationErrors.length > 0"
      :title="`发现 ${validationErrors.length} 个问题需要处理`"
      type="warning"
      :closable="false"
      class="validation-alert"
    >
      <ul>
        <li v-for="error in validationErrors" :key="error">{{ error }}</li>
      </ul>
    </el-alert>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { showMessage } from '@/utils/message'
import {
  DataAnalysis, Box, Setting, Star, Document, Check, RefreshRight,
  Delete, Plus
} from '@element-plus/icons-vue'
import type { AIAnalysisResult, ExtractedProductData } from '@/types/ai-analysis'
import { createProductFromAnalysis } from '@/api/ai-analysis'

interface Props {
  analysisResult: AIAnalysisResult
  categories?: string[]
}

interface Emits {
  (e: 'product-created', productId: number): void
  (e: 'cancel'): void
  (e: 'field-modified', field: string, value: any): void
}

const props = withDefaults(defineProps<Props>(), {
  categories: () => []
})

const emit = defineEmits<Emits>()

// 路由
const router = useRouter()

// 响应式数据
const creating = ref(false)
const showFullText = ref(false)
const modifiedFields = ref<Set<string>>(new Set())

// 提取数据 - 添加安全访问
const extractedData = computed(() => props.analysisResult?.extracted_data || {})
const confidenceScores = computed(() => props.analysisResult?.confidence_scores || {})
const documentInfo = computed(() => props.analysisResult?.document_info || {})
const summary = computed(() => props.analysisResult?.summary || '')
const textPreview = computed(() => props.analysisResult?.text_preview || '')

// 可编辑数据
const editableData = reactive<ExtractedProductData>({
  basic_info: {
    name: '',
    code: '',
    category: '',
    base_price: 0,
    description: ''
  },
  specifications: {},
  features: [],
  application_scenarios: [],
  accessories: [],
  certificates: [],
  support_info: {
    warranty: { period: '', coverage: '', terms: [] },
    contact_info: {},
    service_promises: []
  }
})

// 预定义分类
const predefinedCategories = [
  '变压器', '开关设备', '保护装置', '测量仪表', 
  '控制设备', '电源设备', '传输设备', '其他'
]

// 计算属性
const confidenceType = computed(() => {
  const overall = confidenceScores.value?.overall || 0
  if (overall >= 0.8) return 'success'
  if (overall >= 0.6) return 'warning'
  return 'danger'
})

const confidenceBreakdown = computed(() => {
  const scores = confidenceScores.value || {}
  const { overall, ...breakdown } = scores
  return breakdown
})

const hasSpecifications = computed(() => {
  return Object.keys(editableData.specifications).length > 0
})

const hasFeatures = computed(() => {
  return editableData.features.length > 0
})

const validationErrors = computed(() => {
  const errors: string[] = []
  
  if (!editableData.basic_info.name?.trim()) {
    errors.push('产品名称不能为空')
  }
  
  if (!editableData.basic_info.code?.trim()) {
    errors.push('产品代码不能为空')
  }
  
  if (!editableData.basic_info.category?.trim()) {
    errors.push('产品分类不能为空')
  }
  
  return errors
})

// 🔧 深度合并函数 - 移到前面避免初始化顺序问题
const deepMergeData = (target: any, source: any): any => {
  // 如果源数据为空或不是对象，返回目标数据
  if (!source || typeof source !== 'object' || Array.isArray(source)) {
    return target
  }
  
  // 创建目标数据的副本
  const result = { ...target }
  
  for (const key in source) {
    if (source.hasOwnProperty(key)) {
      const sourceValue = source[key]
      const targetValue = result[key]
      
      // 如果源值不为空且有效
      if (sourceValue !== null && sourceValue !== undefined) {
        if (Array.isArray(sourceValue)) {
          // 数组直接替换（保留源数据的数组）
          result[key] = [...sourceValue]
        } else if (typeof sourceValue === 'object' && typeof targetValue === 'object' && !Array.isArray(targetValue)) {
          // 对象递归合并
          result[key] = deepMergeData(targetValue || {}, sourceValue)
        } else {
          // 基础类型直接赋值
          result[key] = sourceValue
        }
      }
    }
  }
  
  return result
}

// 🔔 数据完整性验证 - 移到前面避免初始化顺序问题
const validateDataCompleteness = (data: any) => {
  const issues: string[] = []
  const warnings: string[] = []
  
  // 检查基础信息完整性
  if (!data.basic_info?.name?.trim()) {
    issues.push('产品名称缺失')
  }
  if (!data.basic_info?.code?.trim()) {
    issues.push('产品代码缺失')
  }
  if (!data.basic_info?.category?.trim()) {
    warnings.push('产品分类缺失')
  }
  if (!data.basic_info?.description?.trim()) {
    warnings.push('产品描述缺失')
  }
  
  // 检查规格参数
  const specsCount = data.specifications ? Object.keys(data.specifications).length : 0
  if (specsCount === 0) {
    warnings.push('技术规格参数缺失')
  }
  
  // 控制台报告
  if (issues.length > 0) {
    console.error('🚨 数据完整性问题:', issues)
  }
  if (warnings.length > 0) {
    console.warn('⚠️ 数据完整性警告:', warnings)
  }
  
  if (issues.length === 0 && warnings.length === 0) {
    console.log('✅ 数据完整性验证通过')
  }
  
  return { issues, warnings, valid: issues.length === 0 }
}

// 🔧 从分析摘要修复基础信息 - 移到前面避免初始化顺序问题
const repairBasicInfoFromSummary = (mergedData: any, analysisResult: any) => {
  try {
    // 获取分析摘要文本
    const summary = analysisResult.summary || ''
    const extractedData = analysisResult.extracted_data || {}
    
    console.log('🔍 尝试从分析摘要修复基础信息:', { summary, hasExtractedData: !!extractedData })
    
    let repaired = false
    const repairedData: any = {}
    
    // 1. 尝试从摘要文本中提取产品信息
    if (summary) {
      // 匹配模式: "Product: 产品名称 | Model: 型号 | Category: 分类"
      const productMatch = summary.match(/Product:\s*([^|]+?)(?:\s*\||\s*$)/i)
      const modelMatch = summary.match(/Model:\s*([^|]+?)(?:\s*\||\s*$)/i)
      const categoryMatch = summary.match(/Category:\s*([^|]+?)(?:\s*\||\s*$)/i)
      
      if (productMatch && productMatch[1]) {
        repairedData.name = productMatch[1].trim()
        repaired = true
        console.log('📝 从摘要提取产品名称:', repairedData.name)
      }
      
      if (modelMatch && modelMatch[1]) {
        repairedData.code = modelMatch[1].trim()
        repaired = true
        console.log('📝 从摘要提取产品代码:', repairedData.code)
      }
      
      if (categoryMatch && categoryMatch[1]) {
        repairedData.category = categoryMatch[1].trim()
        repaired = true
        console.log('📝 从摘要提取产品分类:', repairedData.category)
      }
    }
    
    // 2. 如果摘要提取失败，尝试智能推断
    if (!repaired && extractedData.specifications && Object.keys(extractedData.specifications).length > 0) {
      console.log('🔧 摘要提取失败，尝试智能推断')
      
      // 根据规格参数推断产品类型
      const specKeys = Object.keys(extractedData.specifications).join(' ').toLowerCase()
      
      if (specKeys.includes('继电') || specKeys.includes('保护') || specKeys.includes('测试')) {
        repairedData.name = repairedData.name || '继电保护测试设备'
        repairedData.category = repairedData.category || '保护装置'
        repaired = true
      } else if (specKeys.includes('变压器')) {
        repairedData.name = repairedData.name || '电力变压器'
        repairedData.category = repairedData.category || '变压器设备'
        repaired = true
      } else {
        repairedData.name = repairedData.name || '电力设备'
        repairedData.category = repairedData.category || '电力设备'
        repaired = true
      }
      
      // 生成产品代码
      if (!repairedData.code) {
        repairedData.code = `AUTO_${Date.now()}`
      }
    }
    
    return { repaired, data: repairedData }
    
  } catch (error) {
    console.error('❌ 基础信息修复失败:', error)
    return { repaired: false, data: {} }
  }
}

// 监听数据变化，初始化编辑数据 - 添加安全检查
watch(
  () => props.analysisResult,
  (newResult) => {
    console.log('🚨 AIAnalysisPreview收到新的analysisResult数据:', newResult)
    
    if (newResult?.extracted_data) {
      console.log('🔍 extracted_data结构:', {
        keys: Object.keys(newResult.extracted_data),
        hasBasicInfo: 'basic_info' in newResult.extracted_data,
        basicInfoType: typeof newResult.extracted_data.basic_info,
        basicInfoKeys: newResult.extracted_data.basic_info ? Object.keys(newResult.extracted_data.basic_info) : 'null'
      })
      
      const basicInfo = newResult.extracted_data.basic_info
      if (basicInfo) {
        console.log('📋 接收到的basic_info详情:', {
          name: `"${basicInfo.name}"`,
          code: `"${basicInfo.code}"`,
          category: `"${basicInfo.category}"`,
          nameEmpty: !basicInfo.name,
          codeEmpty: !basicInfo.code,
          categoryEmpty: !basicInfo.category
        })
      }
      
      try {
        // 🔧 安全地深度合并数据，确保结构完整
        const defaultData = {
          basic_info: {
            name: '',
            code: '',
            category: '',
            base_price: 0,
            description: ''
          },
          specifications: {},
          features: [],
          application_scenarios: [],
          accessories: [],
          certificates: [],
          support_info: {
            warranty: { period: '', coverage: '', terms: [] },
            contact_info: {},
            service_promises: []
          }
        }
        
        // ✅ 使用深度合并避免覆盖嵌套对象
        const mergedData = deepMergeData(defaultData, newResult.extracted_data)
        
        // 🔧 数据完整性修复 - 如果基础信息为空，尝试从分析摘要中提取
        const needsRepair = !mergedData.basic_info.name || !mergedData.basic_info.code || !mergedData.basic_info.category
        console.log('🔧 基础信息完整性检查:', {
          name: `"${mergedData.basic_info.name}"`,
          code: `"${mergedData.basic_info.code}"`,  
          category: `"${mergedData.basic_info.category}"`,
          needsRepair: needsRepair,
          summary: newResult.summary
        })
        
        if (needsRepair) {
          console.log('🔧 检测到基础信息缺失，尝试从分析摘要修复')
          const repairResult = repairBasicInfoFromSummary(mergedData, newResult)
          console.log('🔧 修复结果:', repairResult)
          if (repairResult.repaired) {
            console.log('✅ 基础信息修复成功，应用修复数据:', repairResult.data)
            Object.assign(mergedData.basic_info, repairResult.data)
            console.log('✅ 修复后的basic_info:', mergedData.basic_info)
          } else {
            console.log('❌ 基础信息修复失败')
          }
        } else {
          console.log('✅ 基础信息完整，无需修复')
        }
        
        Object.assign(editableData, mergedData)
        
        console.log('🔧 数据合并完成:', {
          原始字段: Object.keys(newResult.extracted_data),
          合并后字段: Object.keys(mergedData),
          基础信息: mergedData.basic_info,
          原始基础信息: newResult.extracted_data.basic_info,
          合并前基础信息长度: Object.keys(newResult.extracted_data.basic_info || {}).length,
          合并后基础信息长度: Object.keys(mergedData.basic_info || {}).length
        })
        
        // 🔍 检查基础信息字段是否正确传递
        if (mergedData.basic_info) {
          console.log('📝 基础信息字段详情:', {
            name: `"${mergedData.basic_info.name}"` || '空',
            code: `"${mergedData.basic_info.code}"` || '空',
            category: `"${mergedData.basic_info.category}"` || '空',
            description: `"${mergedData.basic_info.description}"` || '空'
          })
        } else {
          console.warn('❌ 合并后的基础信息为空')
        }
        
        // 🔔 最终数据完整性验证和用户提示
        validateDataCompleteness(mergedData)
      } catch (error) {
        console.error('❌ 数据合并异常:', error)
        console.log('🚨 异常发生，尝试直接使用原始数据')
        
        // 发生异常时，尝试直接赋值原始数据
        try {
          const fallbackData = {
            basic_info: {
              name: newResult.extracted_data?.basic_info?.name || '',
              code: newResult.extracted_data?.basic_info?.code || '',
              category: newResult.extracted_data?.basic_info?.category || '',
              description: newResult.extracted_data?.basic_info?.description || '',
              base_price: newResult.extracted_data?.basic_info?.base_price || 0,
              is_active: true,
              is_configurable: false
            },
            specifications: newResult.extracted_data?.specifications || {},
            features: newResult.extracted_data?.features || [],
            application_scenarios: newResult.extracted_data?.application_scenarios || [],
            accessories: newResult.extracted_data?.accessories || [],
            certificates: newResult.extracted_data?.certificates || [],
            support_info: newResult.extracted_data?.support_info || {
              warranty: { period: '', coverage: '', terms: [] },
              contact_info: {},
              service_promises: []
            }
          }
          
          console.log('🔧 应急数据修复，使用fallback数据:', fallbackData.basic_info)
          
          // 如果基础信息还是空的，尝试从摘要修复
          if (!fallbackData.basic_info.name && newResult.summary) {
            console.log('🔧 尝试从摘要修复基础信息')
            const repairResult = repairBasicInfoFromSummary(fallbackData, newResult)
            if (repairResult.repaired) {
              Object.assign(fallbackData.basic_info, repairResult.data)
              console.log('✅ 应急修复成功:', fallbackData.basic_info)
            }
          }
          
          Object.assign(editableData, fallbackData)
          console.log('✅ 应急数据恢复完成')
          
        } catch (fallbackError) {
          console.error('❌ 应急数据恢复也失败了:', fallbackError)
        }
      }
    }
  },
  { immediate: true, deep: true }
)

// 🧹 前端规格参数清理函数
const cleanSpecifications = (specifications: Record<string, any>) => {
  const cleaned: Record<string, any> = {}
  
  // 无效模式列表
  const invalidPatterns = [
    /^h$/i,  // 单个字符"h"
    /^[a-z]$/i,  // 单个字母
    /^\d+$/,  // 单纯数字
    /hyperlink/i,  // 包含HYPERLINK
    /^(EMBED|MERGEFORMAT|CERTIFICATE|PACKING|PAGE|TEST)$/i,  // Word格式标识
    /^(Toc\d+|_Toc|_Ref)/i,  // 文档结构标识
    /^\d+\s+(HYPERLINK|PAGE|EMBED)/i,  // 数字+文档格式
    /^[\s\-_=]+$/  // 只有格式字符
  ]
  
  // 技术关键词（用于保留可能的有效参数）
  const technicalKeywords = [
    '电压', '电流', '功率', '频率', '温度', '湿度', '精度', '范围', '容量',
    'voltage', 'current', 'power', 'frequency', 'temperature',
    'V', 'A', 'W', 'Hz', '℃', '℉', '%', 'Ω'
  ]
  
  for (const [key, value] of Object.entries(specifications)) {
    if (!key || !key.trim()) continue
    
    const specKey = key.trim()
    const specValue = typeof value === 'object' ? value?.value || '' : String(value)
    const combinedText = `${specKey} ${specValue}`.toLowerCase()
    
    // 检查是否匹配无效模式
    let isInvalid = false
    for (const pattern of invalidPatterns) {
      if (pattern.test(specKey) || pattern.test(combinedText)) {
        // 但如果包含技术关键词，仍保留
        const hasTechnicalKeyword = technicalKeywords.some(keyword => 
          combinedText.includes(keyword.toLowerCase())
        )
        if (!hasTechnicalKeyword) {
          isInvalid = true
          console.log(`🧹 前端过滤无效规格: "${specKey}" = "${specValue}"`)
          break
        }
      }
    }
    
    if (!isInvalid) {
      cleaned[specKey] = value
    }
  }
  
  return cleaned
}


// 方法
const getConfidenceLabel = (key: string): string => {
  const labels: Record<string, string> = {
    basic_info: '基础信息',
    specifications: '技术规格',
    features: '产品特性',
    applications: '应用场景',
    certificates: '认证信息'
  }
  return labels[key] || key
}

const getConfidenceColor = (score: number): string => {
  if (score >= 0.8) return '#67C23A'
  if (score >= 0.6) return '#E6A23C'
  return '#F56C6C'
}

const getConfidenceTagType = (score: number): string => {
  if (score >= 0.8) return 'success'
  if (score >= 0.6) return 'warning'
  return 'danger'
}

const getFieldClass = (section: string, field: string): string => {
  const fieldPath = `${section}.${field}`
  const confidence = confidenceScores.value?.[section] || 0
  const isModified = modifiedFields.value.has(fieldPath)
  
  if (isModified) return 'field-modified'
  if (confidence >= 0.8) return 'field-high-confidence'
  if (confidence >= 0.6) return 'field-medium-confidence'
  return 'field-low-confidence'
}

const getFieldValue = (fieldPath: string): any => {
  const parts = fieldPath.split('.')
  let value: any = editableData
  
  for (const part of parts) {
    value = value?.[part]
  }
  
  return value
}

const markFieldAsModified = (fieldPath: string) => {
  modifiedFields.value.add(fieldPath)
  emit('field-modified', fieldPath, getFieldValue(fieldPath))
}

const addSpecification = () => {
  const key = `规格${Object.keys(editableData.specifications).length + 1}`
  editableData.specifications[key] = {
    value: '',
    unit: '',
    description: ''
  }
}

const removeSpecification = (key: string) => {
  delete editableData.specifications[key]
}

const addFeature = () => {
  editableData.features.push({
    title: '',
    description: '',
    icon: '',
    sort_order: editableData.features.length
  })
}

const removeFeature = (index: number) => {
  editableData.features.splice(index, 1)
}

const resetToOriginal = () => {
  if (props.analysisResult?.extracted_data) {
    Object.assign(editableData, props.analysisResult.extracted_data)
    modifiedFields.value.clear()
    showMessage.success('已重置为原始分析结果')
  }
}

const confirmCreateProduct = async () => {
  // 🔧 前置验证：检查必填字段
  if (validationErrors.value.length > 0) {
    showMessage.error('请先解决表单验证问题')
    return
  }

  // 🔧 数据完整性验证
  if (!editableData.basic_info.name?.trim() || 
      !editableData.basic_info.code?.trim() || 
      !editableData.basic_info.category?.trim()) {
    showMessage.error('请确保产品名称、代码和分类都已填写')
    return
  }

  try {
    await ElMessageBox.confirm(
      '确认要基于这些信息创建产品吗？',
      '确认创建',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'info'
      }
    )

    creating.value = true

    // 🔧 创建前最终数据检查和修复
    console.log('🔍 创建产品前最终数据检查')
    const validation = validateDataCompleteness(editableData)
    
    if (!validation.valid) {
      console.log('🔧 检测到数据问题，尝试最终修复')
      const repairResult = repairBasicInfoFromSummary(editableData, props.analysisResult)
      if (repairResult.repaired) {
        Object.assign(editableData.basic_info, repairResult.data)
        console.log('✅ 最终数据修复完成')
        showMessage.success('已自动修复部分缺失的产品信息')
      }
    }

    // 🧹 前端预清理：过滤明显的无效规格参数
    const cleanedSpecs = cleanSpecifications(editableData.specifications)
    if (Object.keys(cleanedSpecs).length !== Object.keys(editableData.specifications).length) {
      const filteredCount = Object.keys(editableData.specifications).length - Object.keys(cleanedSpecs).length
      console.log(`🧹 前端预清理：过滤了 ${filteredCount} 个无效规格参数`)
      editableData.specifications = cleanedSpecs
      showMessage.info(`已自动过滤 ${filteredCount} 个无效的规格参数`)
    }

    // 🔧 确保basic_info的完整性和数据类型正确性，包含安全验证
    const safeBasicInfo = {
      // 🔒 防止XSS：清理HTML标签和恶意脚本
      name: String(editableData.basic_info.name || '').trim().replace(/<[^>]*>/g, '').substring(0, 200),
      code: String(editableData.basic_info.code || '').trim().replace(/[^a-zA-Z0-9\-_]/g, '').substring(0, 50),
      category: String(editableData.basic_info.category || '').trim().replace(/<[^>]*>/g, '').substring(0, 100),
      description: String(editableData.basic_info.description || '').trim().replace(/<script[^>]*>.*?<\/script>/gi, '').substring(0, 2000),
      // 🔒 数值安全：确保价格在合理范围内
      base_price: Math.max(0, Math.min(Number(editableData.basic_info.base_price) || 0, 10000000)),
      is_active: Boolean(editableData.basic_info.is_active !== false), // 默认为true
      is_configurable: Boolean(editableData.basic_info.is_configurable) // 默认为false
    }

    // 🔧 二次验证处理后的数据
    if (!safeBasicInfo.name || !safeBasicInfo.code || !safeBasicInfo.category) {
      throw new Error('处理后的基础信息仍然不完整，请检查数据')
    }

    const userModifications = Object.fromEntries(
      Array.from(modifiedFields.value).map(field => [
        field,
        getFieldValue(field)
      ])
    )

    // 🔧 构建安全的请求数据
    const requestData = {
      analysis_id: props.analysisResult.analysis_id!,
      product_data: {
        ...editableData,
        basic_info: safeBasicInfo
      },
      user_modifications: userModifications
    }

    // 🔒 生产环境安全：避免在日志中暴露敏感数据
    if (process.env.NODE_ENV === 'development') {
      console.log('📤 发送产品创建请求:', {
        analysis_id: requestData.analysis_id,
        basic_info: requestData.product_data.basic_info,
        specifications_count: Object.keys(requestData.product_data.specifications || {}).length,
        user_modifications: Object.keys(userModifications)
      })
    }

    const response = await createProductFromAnalysis(requestData)
    
    // 🔧 处理axios响应结构并提取实际数据
    const result = response?.data || response
    console.log('✅ 处理后的API响应结果:', result)

    if (result && result.success) {
      showMessage.success('产品创建成功，正在跳转到产品详情页...')
      emit('product-created', result.product?.id || result.data?.id)
      
      // 🔄 Force refresh products store to ensure UI updates
      try {
        const productsStore = useProductsStore()
        await productsStore.refreshProducts()
        console.log('✅ Products list refreshed after creation')
      } catch (refreshError) {
        console.warn('⚠️ Failed to refresh products list:', refreshError)
      }
      
      // 延迟跳转，给用户看到成功消息
      setTimeout(() => {
        const productId = result.product?.id || result.data?.id
        if (productId) {
          router.push(`/products/${productId}`)
        }
      }, 1500)
    } else {
      // 🔧 增强错误信息提取
      let errorMessage = '创建失败'
      
      if (result?.error) {
        errorMessage = typeof result.error === 'string' ? result.error : result.error.message || result.error.detail || '创建失败'
      } else if (result?.message) {
        errorMessage = result.message
      } else if (!result) {
        errorMessage = '服务器无响应，请检查网络连接'
      }
      
      throw new Error(errorMessage)
    }

  } catch (error: any) {
    if (error !== 'cancel') {
      // 🔧 增强错误处理和用户友好提示
      let errorMsg = '创建产品失败'
      let showDetails = false
      
      if (error.response?.data?.error) {
        const serverError = error.response.data.error
        
        // 🔍 识别特定错误类型并提供友好提示
        if (serverError.includes('Product code already exists')) {
          errorMsg = '产品代码已存在，正在自动生成新代码'
          showMessage.warning(errorMsg)
          
          // 🔄 自动修改产品代码并重试
          const timestamp = Date.now().toString().slice(-6)
          editableData.basic_info.code = `${editableData.basic_info.code}_${timestamp}`
          markFieldAsModified('basic_info.code')
          
          setTimeout(() => {
            showMessage.info('正在重新尝试创建产品...')
            confirmCreateProduct()
          }, 1000)
          return
          
        } else if (serverError.includes('Unable to generate unique product code')) {
          errorMsg = '无法生成唯一的产品代码，请手动修改产品代码后重试'
          showDetails = true
          
        } else if (serverError.includes('Data validation failed')) {
          errorMsg = '产品数据验证失败，请检查必填字段是否完整'
          showDetails = true
          
        } else if (serverError.includes('analysis_id')) {
          errorMsg = '分析记录异常，请重新分析文档'
          
        } else {
          errorMsg = serverError
          showDetails = true
        }
      } else if (error.message) {
        errorMsg = error.message
      }
      
      // 🎯 显示错误消息
      showMessage.error(errorMsg)
      
      // 🔍 控制台输出详细错误信息以便调试
      console.error('🚨 产品创建失败详情:', {
        error: error,
        response: error.response?.data,
        status: error.response?.status,
        config: error.config,
        requestData: {
          analysis_id: props.analysisResult.analysis_id,
          basic_info: editableData.basic_info
        }
      })
    }
  } finally {
    creating.value = false
  }
}
</script>

<style scoped>
.ai-analysis-preview {
  width: 100%;
}

.summary-card,
.data-section,
.text-preview {
  margin-bottom: 20px;
}

.card-header,
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title,
.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.summary-content {
  padding: 16px 0;
}

.summary-item {
  display: flex;
  margin-bottom: 12px;
  align-items: flex-start;
}

.summary-item .label {
  width: 100px;
  color: #606266;
  font-weight: 500;
  flex-shrink: 0;
}

.summary-item .value {
  color: #303133;
  flex: 1;
}

.confidence-breakdown {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}

.confidence-breakdown h4 {
  margin: 0 0 16px 0;
  font-size: 14px;
  color: #303133;
}

.confidence-items {
  display: grid;
  gap: 12px;
}

.confidence-item {
  display: grid;
  grid-template-columns: 100px 1fr 60px;
  align-items: center;
  gap: 12px;
}

.confidence-label {
  font-size: 12px;
  color: #606266;
}

.confidence-value {
  font-size: 12px;
  color: #303133;
  font-weight: 600;
  text-align: right;
}

.editable-fields {
  padding: 16px 0;
}

.field-item {
  margin-bottom: 20px;
}

.field-label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

/* 字段置信度样式 */
.field-high-confidence :deep(.el-input__wrapper) {
  border-color: #67C23A;
  background-color: rgba(103, 194, 58, 0.05);
}

.field-medium-confidence :deep(.el-input__wrapper) {
  border-color: #E6A23C;
  background-color: rgba(230, 162, 60, 0.05);
}

.field-low-confidence :deep(.el-input__wrapper) {
  border-color: #F56C6C;
  background-color: rgba(245, 108, 108, 0.05);
}

.field-modified :deep(.el-input__wrapper) {
  border-color: #409EFF;
  background-color: rgba(64, 158, 255, 0.05);
  box-shadow: 0 0 0 1px rgba(64, 158, 255, 0.2);
}

.specifications-list,
.features-list {
  padding: 16px 0;
}

.spec-item,
.feature-item {
  margin-bottom: 16px;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.spec-key {
  font-weight: 500;
}

.text-preview-content {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  line-height: 1.5;
  color: #606266;
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin: 32px 0;
  padding-top: 24px;
  border-top: 1px solid #e4e7ed;
}

.validation-alert {
  margin-top: 20px;
}

.validation-alert ul {
  margin: 8px 0;
  padding-left: 20px;
}

.validation-alert li {
  margin-bottom: 4px;
  color: #E6A23C;
}

/* 响应式样式 */
@media (max-width: 768px) {
  .action-buttons {
    flex-direction: column;
  }
  
  .action-buttons .el-button {
    width: 100%;
  }
  
  .confidence-item {
    grid-template-columns: 80px 1fr 50px;
  }
}

/* 动画效果 */
.data-section {
  animation: slideInUp 0.4s ease-out;
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>