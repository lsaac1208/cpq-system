<template>
  <div class="product-form">
    <el-form
      ref="productFormRef"
      :model="form"
      :rules="rules"
      label-width="140px"
      @submit.prevent="handleSubmit"
    >
      <!-- Basic Information -->
      <el-card class="form-section">
        <template #header>
          <span class="section-title">基本信息</span>
        </template>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="产品名称" prop="name">
              <el-input
                v-model="form.name"
                placeholder="请输入产品名称"
                maxlength="200"
                show-word-limit
              />
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="产品代码" prop="code">
              <el-input
                v-model="form.code"
                placeholder="请输入唯一产品代码"
                maxlength="50"
                show-word-limit
                :disabled="isEditing"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="分类" prop="category">
              <el-select
                v-model="form.category"
                placeholder="选择或输入分类"
                filterable
                allow-create
                default-first-option
                style="width: 100%"
              >
                <el-option
                  v-for="category in categories"
                  :key="category"
                  :label="category"
                  :value="category"
                />
              </el-select>
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="基础价格" prop="base_price">
              <el-input-number
                v-model="form.base_price"
                :precision="2"
                :min="0"
                :max="999999.99"
                style="width: 100%"
                controls-position="right"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="产品描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入产品描述"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="状态">
              <el-switch
                v-model="form.is_active"
                active-text="活跃"
                inactive-text="非活跃"
              />
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="可配置">
              <el-switch
                v-model="form.is_configurable"
                active-text="是"
                inactive-text="否"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>

      <!-- Product Image -->
      <el-card class="form-section">
        <template #header>
          <span class="section-title">产品图片</span>
        </template>
        
        <!-- Image Upload Mode Selection -->
        <div class="image-upload-mode">
          <el-radio-group v-model="imageUploadMode" class="mode-selector">
            <el-radio-button value="single">单图上传</el-radio-button>
            <el-radio-button value="gallery">图集管理</el-radio-button>
          </el-radio-group>
        </div>

        <!-- Single Image Upload Mode -->
        <div v-if="imageUploadMode === 'single'">
          <FastImageUpload
            ref="fastImageUploadRef"
            :product-id="editingProductId"
            :initial-image-url="form.image_url"
            :disabled="loading"
            compression-preset="standard"
            @upload-success="handleImageUploadSuccess"
            @upload-error="handleImageUploadError"
            @delete-success="handleImageDeleteSuccess"
            @delete-error="handleImageDeleteError"
          />
        </div>

        <!-- Gallery Management Mode -->
        <div v-else>
          <ProductGallery
            ref="productGalleryRef"
            :product-id="editingProductId"
            :edit-mode="true"
            :can-edit="true"
            auto-load
            @refresh="handleGalleryRefresh"
            @image-change="handleGalleryImageChange"
            @images-update="handleGalleryImagesUpdate"
          />
        </div>
      </el-card>

      <!-- Technical Specifications -->
      <el-card class="form-section">
        <template #header>
          <div class="section-header">
            <span class="section-title">技术规格</span>
            <el-button
              type="primary"
              size="small"
              @click="addSpecification"
            >
              <el-icon><Plus /></el-icon>
              添加规格
            </el-button>
          </div>
        </template>
        
        <div v-if="specificationsArray.length === 0" class="empty-state">
          <el-empty description="尚未添加规格" />
        </div>
        
        <div
          v-for="(spec, index) in specificationsArray"
          :key="spec.id"
          class="specification-item"
        >
          <el-row :gutter="16" align="middle">
            <el-col :span="6">
              <el-input
                v-model="spec.name"
                placeholder="规格名称"
                size="small"
              />
            </el-col>
            <el-col :span="6">
              <el-input
                v-model="spec.value"
                placeholder="值"
                size="small"
              />
            </el-col>
            <el-col :span="4">
              <el-input
                v-model="spec.unit"
                placeholder="单位（可选）"
                size="small"
              />
            </el-col>
            <el-col :span="6">
              <el-input
                v-model="spec.description"
                placeholder="描述（可选）"
                size="small"
              />
            </el-col>
            <el-col :span="2">
              <el-button
                type="danger"
                size="small"
                @click="removeSpecification(index)"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </el-col>
          </el-row>
        </div>
      </el-card>

      <!-- Configuration Schema -->
      <el-card v-if="form.is_configurable" class="form-section">
        <template #header>
          <div class="section-header">
            <span class="section-title">配置架构</span>
            <el-button
              type="primary"
              size="small"
              @click="addConfigField"
            >
              <el-icon><Plus /></el-icon>
              添加字段
            </el-button>
          </div>
        </template>
        
        <div v-if="configFieldsArray.length === 0" class="empty-state">
          <el-empty description="尚未添加配置字段" />
        </div>
        
        <div
          v-for="(field, index) in configFieldsArray"
          :key="field.id"
          class="config-field-item"
        >
          <el-card size="small">
            <el-row :gutter="16">
              <el-col :span="8">
                <el-form-item label="字段名称" size="small">
                  <el-input v-model="field.name" placeholder="字段名称" />
                </el-form-item>
                
                <el-form-item label="标签" size="small">
                  <el-input v-model="field.label" placeholder="显示标签" />
                </el-form-item>
                
                <el-form-item label="类型" size="small">
                  <el-select v-model="field.type" style="width: 100%">
                    <el-option label="文本" value="text" />
                    <el-option label="数字" value="number" />
                    <el-option label="布尔" value="boolean" />
                    <el-option label="选择" value="select" />
                    <el-option label="多选" value="multiselect" />
                  </el-select>
                </el-form-item>
              </el-col>
              
              <el-col :span="8">
                <el-form-item label="描述" size="small">
                  <el-input
                    v-model="field.description"
                    type="textarea"
                    :rows="2"
                    placeholder="字段描述"
                  />
                </el-form-item>
                
                <el-form-item label="默认值" size="small">
                  <el-input v-model="field.default" placeholder="默认值" />
                </el-form-item>
                
                <el-form-item size="small">
                  <el-checkbox v-model="field.required">必填</el-checkbox>
                </el-form-item>
              </el-col>
              
              <el-col :span="6">
                <div v-if="['select', 'multiselect'].includes(field.type)">
                  <el-form-item label="选项" size="small">
                    <div
                      v-for="(option, optIndex) in field.options"
                      :key="optIndex"
                      class="option-item"
                    >
                      <el-row :gutter="8" align="middle">
                        <el-col :span="10">
                          <el-input
                            v-model="option.label"
                            placeholder="标签"
                            size="small"
                          />
                        </el-col>
                        <el-col :span="10">
                          <el-input
                            v-model="option.value"
                            placeholder="值"
                            size="small"
                          />
                        </el-col>
                        <el-col :span="4">
                          <el-button
                            type="danger"
                            size="small"
                            @click="removeOption(index, optIndex)"
                          >
                            <el-icon><Delete /></el-icon>
                          </el-button>
                        </el-col>
                      </el-row>
                    </div>
                    <el-button
                      link
                      size="small"
                      @click="addOption(index)"
                    >
                      添加选项
                    </el-button>
                  </el-form-item>
                </div>
                
                <div v-if="field.type === 'number'">
                  <el-form-item label="最小值" size="small">
                    <el-input-number
                      v-model="field.validation.min"
                      size="small"
                      style="width: 100%"
                    />
                  </el-form-item>
                  <el-form-item label="最大值" size="small">
                    <el-input-number
                      v-model="field.validation.max"
                      size="small"
                      style="width: 100%"
                    />
                  </el-form-item>
                </div>
              </el-col>
              
              <el-col :span="2">
                <el-button
                  type="danger"
                  size="small"
                  @click="removeConfigField(index)"
                >
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </el-col>
            </el-row>
          </el-card>
        </div>
      </el-card>

      <!-- Product Overview and Details -->
      <el-card class="form-section">
        <template #header>
          <span class="section-title">产品详情</span>
        </template>
        
        <el-form-item label="详细介绍">
          <el-input
            v-model="form.detailed_description"
            type="textarea"
            :rows="6"
            placeholder="请输入产品详细介绍，支持应用场景、工作原理等详细描述"
            maxlength="2000"
            show-word-limit
          />
        </el-form-item>
        
        <!-- Application Scenarios -->
        <div class="subsection">
          <div class="subsection-header">
            <span class="subsection-title">应用场景</span>
            <el-button
              type="primary"
              size="small"
              @click="addApplicationScenario"
            >
              <el-icon><Plus /></el-icon>
              添加场景
            </el-button>
          </div>
          
          <div v-if="form.application_scenarios.length === 0" class="empty-state">
            <el-empty description="尚未添加应用场景" />
          </div>
          
          <div
            v-for="(scenario, index) in form.application_scenarios"
            :key="scenario.id"
            class="list-item"
          >
            <el-row :gutter="16" align="middle">
              <el-col :span="6">
                <el-input
                  v-model="scenario.name"
                  placeholder="场景名称"
                  size="small"
                />
              </el-col>
              <el-col :span="6">
                <el-input
                  v-model="scenario.icon"
                  placeholder="图标类名（可选）"
                  size="small"
                />
              </el-col>
              <el-col :span="10">
                <span class="item-info">排序: {{ index + 1 }}</span>
              </el-col>
              <el-col :span="2">
                <el-button
                  type="danger"
                  size="small"
                  @click="removeApplicationScenario(index)"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-col>
            </el-row>
          </div>
        </div>
      </el-card>

      <!-- Product Features -->
      <el-card class="form-section">
        <template #header>
          <div class="section-header">
            <span class="section-title">产品特点</span>
            <el-button
              type="primary"
              size="small"
              @click="addFeature"
            >
              <el-icon><Plus /></el-icon>
              添加特点
            </el-button>
          </div>
        </template>
        
        <div v-if="form.features.length === 0" class="empty-state">
          <el-empty description="尚未添加产品特点" />
        </div>
        
        <div
          v-for="(feature, index) in form.features"
          :key="feature.id"
          class="feature-item"
        >
          <el-card size="small" class="feature-card">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="特点标题" size="small">
                  <el-input v-model="feature.title" placeholder="特点标题" />
                </el-form-item>
                
                <el-form-item label="图标类名" size="small">
                  <el-input v-model="feature.icon" placeholder="图标类名（可选）" />
                </el-form-item>
              </el-col>
              
              <el-col :span="10">
                <el-form-item label="特点描述" size="small">
                  <el-input
                    v-model="feature.description"
                    type="textarea"
                    :rows="3"
                    placeholder="详细描述该产品特点"
                  />
                </el-form-item>
              </el-col>
              
              <el-col :span="2">
                <el-button
                  type="danger"
                  size="small"
                  @click="removeFeature(index)"
                >
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </el-col>
            </el-row>
          </el-card>
        </div>
      </el-card>

      <!-- Accessories -->
      <el-card class="form-section">
        <template #header>
          <div class="section-header">
            <span class="section-title">附件配件</span>
            <div class="section-actions">
              <el-button
                type="primary"
                size="small"
                @click="addAccessory('standard')"
              >
                <el-icon><Plus /></el-icon>
                标准配置
              </el-button>
              <el-button
                type="success"
                size="small"
                @click="addAccessory('optional')"
              >
                <el-icon><Plus /></el-icon>
                可选配件
              </el-button>
            </div>
          </div>
        </template>
        
        <div v-if="form.accessories.length === 0" class="empty-state">
          <el-empty description="尚未添加附件配件" />
        </div>
        
        <!-- Standard Accessories -->
        <div v-if="form.accessories.some(acc => acc.type === 'standard')" class="accessory-section">
          <h4 class="accessory-section-title">标准配置</h4>
          <div
            v-for="(accessory, index) in form.accessories.filter(acc => acc.type === 'standard')"
            :key="accessory.id"
            class="accessory-item"
          >
            <el-row :gutter="16" align="middle">
              <el-col :span="6">
                <el-input
                  v-model="accessory.name"
                  placeholder="配件名称"
                  size="small"
                />
              </el-col>
              <el-col :span="14">
                <el-input
                  v-model="accessory.description"
                  placeholder="配件描述"
                  size="small"
                />
              </el-col>
              <el-col :span="2">
                <el-tag type="primary" size="small">标准</el-tag>
              </el-col>
              <el-col :span="2">
                <el-button
                  type="danger"
                  size="small"
                  @click="removeAccessory(form.accessories.findIndex(acc => acc.id === accessory.id))"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-col>
            </el-row>
          </div>
        </div>
        
        <!-- Optional Accessories -->
        <div v-if="form.accessories.some(acc => acc.type === 'optional')" class="accessory-section">
          <h4 class="accessory-section-title">可选配件</h4>
          <div
            v-for="(accessory, index) in form.accessories.filter(acc => acc.type === 'optional')"
            :key="accessory.id"
            class="accessory-item"
          >
            <el-row :gutter="16" align="middle">
              <el-col :span="6">
                <el-input
                  v-model="accessory.name"
                  placeholder="配件名称"
                  size="small"
                />
              </el-col>
              <el-col :span="14">
                <el-input
                  v-model="accessory.description"
                  placeholder="配件描述"
                  size="small"
                />
              </el-col>
              <el-col :span="2">
                <el-tag type="success" size="small">可选</el-tag>
              </el-col>
              <el-col :span="2">
                <el-button
                  type="danger"
                  size="small"
                  @click="removeAccessory(form.accessories.findIndex(acc => acc.id === accessory.id))"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-col>
            </el-row>
          </div>
        </div>
      </el-card>

      <!-- Certificates -->
      <el-card class="form-section">
        <template #header>
          <div class="section-header">
            <span class="section-title">检定证书</span>
            <el-button
              type="primary"
              size="small"
              @click="addCertificate"
            >
              <el-icon><Plus /></el-icon>
              添加证书
            </el-button>
          </div>
        </template>
        
        <div v-if="form.certificates.length === 0" class="empty-state">
          <el-empty description="尚未添加证书信息" />
        </div>
        
        <div
          v-for="(certificate, index) in form.certificates"
          :key="certificate.id"
          class="certificate-item"
        >
          <el-card size="small">
            <el-row :gutter="16">
              <el-col :span="8">
                <el-form-item label="证书名称" size="small">
                  <el-input v-model="certificate.name" placeholder="证书名称" />
                </el-form-item>
                
                <el-form-item label="证书类型" size="small">
                  <el-select v-model="certificate.type" placeholder="选择类型" style="width: 100%">
                    <el-option label="质量认证" value="quality" />
                    <el-option label="安全认证" value="safety" />
                    <el-option label="合规认证" value="compliance" />
                    <el-option label="计量检定" value="metrology" />
                    <el-option label="其他" value="other" />
                  </el-select>
                </el-form-item>
              </el-col>
              
              <el-col :span="8">
                <el-form-item label="证书编号" size="small">
                  <el-input v-model="certificate.certificate_number" placeholder="证书编号" />
                </el-form-item>
                
                <el-form-item label="证书描述" size="small">
                  <el-input
                    v-model="certificate.description"
                    type="textarea"
                    :rows="2"
                    placeholder="证书描述"
                  />
                </el-form-item>
              </el-col>
              
              <el-col :span="6">
                <div class="certificate-actions">
                  <el-button
                    type="danger"
                    size="small"
                    @click="removeCertificate(index)"
                  >
                    <el-icon><Delete /></el-icon>
                    删除证书
                  </el-button>
                </div>
              </el-col>
            </el-row>
          </el-card>
        </div>
      </el-card>

      <!-- Support Information -->
      <el-card class="form-section">
        <template #header>
          <span class="section-title">售后保障</span>
        </template>
        
        <!-- Warranty Information -->
        <div class="subsection">
          <h4 class="subsection-title">质保信息</h4>
          
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="质保期限">
                <el-input
                  v-model="form.support_info.warranty.period"
                  placeholder="例：3年"
                />
              </el-form-item>
            </el-col>
            <el-col :span="16">
              <el-form-item label="质保内容">
                <el-input
                  v-model="form.support_info.warranty.coverage"
                  placeholder="例：产品质保期3年，终身维护服务"
                />
              </el-form-item>
            </el-col>
          </el-row>
          
          <!-- Warranty Terms -->
          <div class="warranty-terms">
            <div class="terms-header">
              <span class="terms-title">质保条款</span>
              <el-button link size="small" @click="addWarrantyTerm">
                <el-icon><Plus /></el-icon>
                添加条款
              </el-button>
            </div>
            
            <div
              v-for="(term, index) in form.support_info.warranty.terms"
              :key="index"
              class="term-item"
            >
              <el-row :gutter="8" align="middle">
                <el-col :span="22">
                  <el-input
                    v-model="form.support_info.warranty.terms[index]"
                    placeholder="质保条款内容"
                    size="small"
                  />
                </el-col>
                <el-col :span="2">
                  <el-button
                    type="danger"
                    size="small"
                    @click="removeWarrantyTerm(index)"
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </el-col>
              </el-row>
            </div>
          </div>
        </div>
        
        <!-- Contact Information -->
        <div class="subsection">
          <h4 class="subsection-title">联系方式</h4>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="销售热线">
                <el-input
                  v-model="form.support_info.contact_info.sales_phone"
                  placeholder="销售热线电话"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="销售邮箱">
                <el-input
                  v-model="form.support_info.contact_info.sales_email"
                  placeholder="sales@company.com"
                />
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="技术支持">
                <el-input
                  v-model="form.support_info.contact_info.support_phone"
                  placeholder="技术支持电话"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="技术邮箱">
                <el-input
                  v-model="form.support_info.contact_info.support_email"
                  placeholder="tech@company.com"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="服务微信">
                <el-input
                  v-model="form.support_info.contact_info.service_wechat"
                  placeholder="服务微信号"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </div>
        
        <!-- Service Promises -->
        <div class="subsection">
          <div class="subsection-header">
            <span class="subsection-title">服务承诺</span>
            <el-button link size="small" @click="addServicePromise">
              <el-icon><Plus /></el-icon>
              添加承诺
            </el-button>
          </div>
          
          <div
            v-for="(promise, index) in form.support_info.service_promises"
            :key="index"
            class="promise-item"
          >
            <el-row :gutter="8" align="middle">
              <el-col :span="22">
                <el-input
                  v-model="form.support_info.service_promises[index]"
                  placeholder="服务承诺内容"
                  size="small"
                />
              </el-col>
              <el-col :span="2">
                <el-button
                  type="danger"
                  size="small"
                  @click="removeServicePromise(index)"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-col>
            </el-row>
          </div>
        </div>
      </el-card>

      <!-- Form Actions -->
      <div class="form-actions">
        <el-button @click="$emit('cancel')">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="loading">
          {{ isEditing ? '更新产品' : '创建产品' }}
        </el-button>
      </div>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { type FormInstance, type FormRules } from 'element-plus'
import { showMessage } from '@/utils/message'
import { Plus, Delete } from '@element-plus/icons-vue'
import type { 
  Product, 
  ProductFormData, 
  ProductFeature, 
  ProductAccessory, 
  ProductCertificate, 
  ApplicationScenario, 
  ProductSupport 
} from '@/types/product'
import FastImageUpload from './FastImageUpload.vue'
import ProductGallery from './ProductGallery.vue'

interface Props {
  product?: Product | null
  categories?: string[]
  loading?: boolean
}

interface Emits {
  (e: 'submit', data: ProductFormData, pendingImage?: File): void
  (e: 'cancel'): void
}

const props = withDefaults(defineProps<Props>(), {
  product: null,
  categories: () => [],
  loading: false
})

const emit = defineEmits<Emits>()

const productFormRef = ref<FormInstance>()
const fastImageUploadRef = ref<any>(null)
const productGalleryRef = ref<any>(null)
const imageUploadMode = ref<'single' | 'gallery'>('single')
const pendingImageFile = ref<File | null>(null)

const isEditing = computed(() => !!props.product)

// Form data
const form = reactive<ProductFormData>({
  name: '',
  code: '',
  description: '',
  category: '',
  base_price: 0,
  image_url: '',
  specifications: {},
  configuration_schema: {},
  is_active: true,
  is_configurable: false,
  // Extended content fields
  detailed_description: '',
  application_scenarios: [],
  features: [],
  accessories: [],
  certificates: [],
  support_info: {
    warranty: {
      period: '',
      coverage: '',
      terms: []
    },
    contact_info: {
      sales_phone: '',
      sales_email: '',
      support_phone: '',
      support_email: '',
      service_wechat: ''
    },
    service_promises: []
  }
})

// 编辑产品ID（用于图片上传）
const editingProductId = ref<number | null>(null)

// Specifications array for easier manipulation
const specificationsArray = ref<Array<{
  id: string
  name: string
  value: string
  unit?: string
  description?: string
}>>([])

// Configuration fields array
const configFieldsArray = ref<Array<{
  id: string
  name: string
  type: string
  label: string
  description?: string
  required: boolean
  default?: any
  options?: Array<{ label: string; value: string }>
  validation?: { min?: number; max?: number; pattern?: string }
}>>([])

// Function definitions first
const resetForm = () => {
  Object.assign(form, {
    name: '',
    code: '',
    description: '',
    category: '',
    base_price: 0,
    image_url: '',
    specifications: {},
    configuration_schema: {},
    is_active: true,
    is_configurable: false,
    // Extended content fields
    detailed_description: '',
    application_scenarios: [],
    features: [],
    accessories: [],
    certificates: [],
    support_info: {
      warranty: {
        period: '',
        coverage: '',
        terms: []
      },
      contact_info: {
        sales_phone: '',
        sales_email: '',
        support_phone: '',
        support_email: '',
        service_wechat: ''
      },
      service_promises: []
    }
  })
  specificationsArray.value = []
  configFieldsArray.value = []
  editingProductId.value = null
}

const populateForm = (product: Product) => {
  Object.assign(form, {
    name: product.name,
    code: product.code,
    description: product.description || '',
    category: product.category,
    base_price: product.base_price,
    image_url: (product as any).image_url || '',
    specifications: product.specifications || {},
    configuration_schema: product.configuration_schema || {},
    is_active: product.is_active,
    is_configurable: product.is_configurable,
    // Extended content fields
    detailed_description: product.detailed_description || '',
    application_scenarios: product.application_scenarios || [],
    features: product.features || [],
    accessories: product.accessories || [],
    certificates: product.certificates || [],
    support_info: product.support_info || {
      warranty: {
        period: '',
        coverage: '',
        terms: []
      },
      contact_info: {},
      service_promises: []
    }
  })
  
  // 设置编辑产品ID
  editingProductId.value = (product as any).id || null
  
  // Convert specifications object to array
  specificationsArray.value = Object.entries(form.specifications).map(([key, spec]: [string, any]) => ({
    id: Math.random().toString(36).substr(2, 9),
    name: key,
    value: spec.value || spec,
    unit: spec.unit || '',
    description: spec.description || ''
  }))
  
  // Convert configuration schema to array
  configFieldsArray.value = Object.entries(form.configuration_schema).map(([key, field]: [string, any]) => ({
    id: Math.random().toString(36).substr(2, 9),
    name: key,
    type: field.type || 'text',
    label: field.label || key,
    description: field.description || '',
    required: field.required || false,
    default: field.default,
    options: field.options || [],
    validation: field.validation || {}
  }))
}

// Form validation rules
const rules: FormRules = {
  name: [
    { required: true, message: '请输入产品名称', trigger: 'blur' },
    { min: 1, max: 200, message: '长度应为1到200个字符', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入产品代码', trigger: 'blur' },
    { min: 1, max: 50, message: '长度应为1到50个字符', trigger: 'blur' }
  ],
  category: [
    { required: true, message: '请选择或输入分类', trigger: 'blur' }
  ],
  base_price: [
    { required: true, message: '请输入基础价格', trigger: 'blur' },
    { type: 'number', min: 0, message: '价格不能为负数', trigger: 'blur' }
  ],
  detailed_description: [
    { max: 2000, message: '详细介绍不能超过2000个字符', trigger: 'blur' }
  ]
}

// Additional validation functions
const validateFeatures = () => {
  const errors: string[] = []
  
  form.features.forEach((feature, index) => {
    if (!feature.title.trim()) {
      errors.push(`第${index + 1}个产品特点的标题不能为空`)
    }
    if (!feature.description.trim()) {
      errors.push(`第${index + 1}个产品特点的描述不能为空`)
    }
  })
  
  return errors
}

const validateAccessories = () => {
  const errors: string[] = []
  
  form.accessories.forEach((accessory, index) => {
    if (!accessory.name.trim()) {
      errors.push(`第${index + 1}个配件的名称不能为空`)
    }
    if (!accessory.description.trim()) {
      errors.push(`第${index + 1}个配件的描述不能为空`)
    }
  })
  
  return errors
}

const validateCertificates = () => {
  const errors: string[] = []
  
  form.certificates.forEach((certificate, index) => {
    if (!certificate.name.trim()) {
      errors.push(`第${index + 1}个证书的名称不能为空`)
    }
    if (!certificate.description.trim()) {
      errors.push(`第${index + 1}个证书的描述不能为空`)
    }
  })
  
  return errors
}

const validateSupportInfo = () => {
  const errors: string[] = []
  
  // Validate warranty terms
  form.support_info.warranty.terms.forEach((term, index) => {
    if (!term.trim()) {
      errors.push(`第${index + 1}个质保条款不能为空`)
    }
  })
  
  // Validate service promises
  form.support_info.service_promises.forEach((promise, index) => {
    if (!promise.trim()) {
      errors.push(`第${index + 1}个服务承诺不能为空`)
    }
  })
  
  // Validate email format
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (form.support_info.contact_info.sales_email && !emailPattern.test(form.support_info.contact_info.sales_email)) {
    errors.push('销售邮箱格式不正确')
  }
  if (form.support_info.contact_info.support_email && !emailPattern.test(form.support_info.contact_info.support_email)) {
    errors.push('技术支持邮箱格式不正确')
  }
  
  return errors
}

const performExtendedValidation = () => {
  const errors: string[] = []
  
  // Collect all validation errors
  errors.push(...validateFeatures())
  errors.push(...validateAccessories())
  errors.push(...validateCertificates())
  errors.push(...validateSupportInfo())
  
  return errors
}

// Watch for product changes (editing mode)
watch(() => props.product, async (newProduct) => {
  if (newProduct) {
    populateForm(newProduct)
    
    // Auto-detect image upload mode based on existing data
    if ((newProduct as any).id && isEditing.value) {
      // Check if product has multiple images to suggest gallery mode
      try {
        // We'll check if there are multiple images and suggest gallery mode
        // For now, default to single mode but user can switch
        imageUploadMode.value = 'single'
      } catch (error) {
        console.error('Error detecting image mode:', error)
        imageUploadMode.value = 'single'
      }
    }
  } else {
    resetForm()
    imageUploadMode.value = 'single' // Default for new products
  }
}, { immediate: true })

// Specifications management
const addSpecification = () => {
  specificationsArray.value.push({
    id: Math.random().toString(36).substr(2, 9),
    name: '',
    value: '',
    unit: '',
    description: ''
  })
}

const removeSpecification = (index: number) => {
  specificationsArray.value.splice(index, 1)
}

// Configuration fields management
const addConfigField = () => {
  configFieldsArray.value.push({
    id: Math.random().toString(36).substr(2, 9),
    name: '',
    type: 'text',
    label: '',
    description: '',
    required: false,
    default: '',
    options: [],
    validation: {}
  })
}

const removeConfigField = (index: number) => {
  configFieldsArray.value.splice(index, 1)
}

const addOption = (fieldIndex: number) => {
  if (!configFieldsArray.value[fieldIndex].options) {
    configFieldsArray.value[fieldIndex].options = []
  }
  configFieldsArray.value[fieldIndex].options!.push({
    label: '',
    value: ''
  })
}

const removeOption = (fieldIndex: number, optionIndex: number) => {
  configFieldsArray.value[fieldIndex].options!.splice(optionIndex, 1)
}

// Application scenarios management
const addApplicationScenario = () => {
  form.application_scenarios.push({
    id: Math.random().toString(36).substr(2, 9),
    name: '',
    icon: '',
    sort_order: form.application_scenarios.length
  })
}

const removeApplicationScenario = (index: number) => {
  form.application_scenarios.splice(index, 1)
}

// Features management
const addFeature = () => {
  form.features.push({
    id: Math.random().toString(36).substr(2, 9),
    icon: '',
    title: '',
    description: '',
    sort_order: form.features.length
  })
}

const removeFeature = (index: number) => {
  form.features.splice(index, 1)
}

// Accessories management
const addAccessory = (type: 'standard' | 'optional' = 'standard') => {
  form.accessories.push({
    id: Math.random().toString(36).substr(2, 9),
    name: '',
    description: '',
    type,
    sort_order: form.accessories.length
  })
}

const removeAccessory = (index: number) => {
  form.accessories.splice(index, 1)
}

// Certificates management
const addCertificate = () => {
  form.certificates.push({
    id: Math.random().toString(36).substr(2, 9),
    name: '',
    description: '',
    certificate_number: '',
    type: 'quality',
    sort_order: form.certificates.length
  })
}

const removeCertificate = (index: number) => {
  form.certificates.splice(index, 1)
}

// Support info management
const addWarrantyTerm = () => {
  form.support_info.warranty.terms.push('')
}

const removeWarrantyTerm = (index: number) => {
  form.support_info.warranty.terms.splice(index, 1)
}

const addServicePromise = () => {
  form.support_info.service_promises.push('')
}

const removeServicePromise = (index: number) => {
  form.support_info.service_promises.splice(index, 1)
}

// Convert arrays back to objects before submitting
const prepareFormData = (): ProductFormData => {
  // Convert specifications array to object
  const specifications: Record<string, any> = {}
  specificationsArray.value.forEach(spec => {
    if (spec.name) {
      specifications[spec.name] = {
        value: spec.value,
        unit: spec.unit,
        description: spec.description
      }
    }
  })
  
  // Convert config fields array to object
  const configuration_schema: Record<string, any> = {}
  configFieldsArray.value.forEach(field => {
    if (field.name) {
      configuration_schema[field.name] = {
        type: field.type,
        label: field.label,
        description: field.description,
        required: field.required,
        default: field.default,
        options: field.options,
        validation: field.validation
      }
    }
  })
  
  return {
    ...form,
    specifications,
    configuration_schema
  }
}

const handleSubmit = async () => {
  if (!productFormRef.value) return
  
  try {
    // First validate the basic form fields
    await productFormRef.value.validate()
    
    // Then perform extended validation for new fields
    const extendedErrors = performExtendedValidation()
    if (extendedErrors.length > 0) {
      showMessage.error({
        message: `表单验证失败：\n${extendedErrors.join('\n')}`,
        duration: 6000,
        showClose: true
      })
      return
    }
    
    const formData = prepareFormData()
    
    // 如果是创建模式且有待上传的图片，先提交产品信息
    if (!isEditing.value && pendingImageFile.value) {
      emit('submit', formData, pendingImageFile.value)
    } else {
      emit('submit', formData)
    }
  } catch (error) {
    showMessage.error('请修复表单错误')
  }
}

// 产品创建成功后上传图片
const uploadImageAfterCreate = async (productId: string) => {
  try {
    // 设置编辑产品ID，让上传组件知道可以上传了
    editingProductId.value = parseInt(productId)
    
    if (imageUploadMode.value === 'single' && fastImageUploadRef.value) {
      // 单图模式：如果有待上传的文件，现在上传
      if (pendingImageFile.value) {
        // FastImageUpload 会自动处理有productId的情况
        showMessage.info('正在上传产品图片...')
        // 组件会自动处理上传逻辑
      }
    } else if (imageUploadMode.value === 'gallery' && productGalleryRef.value) {
      // 图集模式：重新加载图集以显示上传功能
      await productGalleryRef.value.loadGallery()
      showMessage.success('产品创建成功，现在可以上传图集')
    }
    
    showMessage.success('产品创建成功')
  } catch (error) {
    showMessage.warning('产品创建成功，但图片处理可能有问题')
    console.error('Upload after create error:', error)
  }
}

// 暴露给父组件
defineExpose({
  uploadImageAfterCreate
})

// 图片上传事件处理
const handleImageUploadSuccess = (imageUrl: string, imageInfo: any) => {
  form.image_url = imageUrl
  showMessage.success('产品图片上传成功')
}

const handleImageUploadError = (error: string) => {
  showMessage.error(`图片上传失败: ${error}`)
}

const handleImageDeleteSuccess = () => {
  form.image_url = ''
  showMessage.success('产品图片删除成功')
}

const handleImageDeleteError = (error: string) => {
  showMessage.error(`图片删除失败: ${error}`)
}

// Gallery事件处理
const handleGalleryRefresh = () => {
  showMessage.success('图集已刷新')
}

const handleGalleryImageChange = (imageUrl: string) => {
  // 当图集中的主图发生变化时，更新表单的image_url
  if (imageUrl && imageUrl !== form.image_url) {
    form.image_url = imageUrl
    showMessage.info('主图已更新')
  }
}

const handleGalleryImagesUpdate = (images: any[]) => {
  // 当图集更新时，如果有主图，设置为表单的image_url
  const primaryImage = images.find(img => img.is_primary)
  if (primaryImage && primaryImage.image_url !== form.image_url) {
    form.image_url = primaryImage.image_url
  }
}
</script>

<style scoped>
.product-form {
  max-width: 1000px;
}

.form-section {
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title {
  font-weight: 600;
  font-size: 16px;
}

.specification-item {
  margin-bottom: 12px;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background-color: #fafafa;
}

.config-field-item {
  margin-bottom: 16px;
}

.option-item {
  margin-bottom: 8px;
}

.empty-state {
  text-align: center;
  padding: 40px 0;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e4e7ed;
}

/* Image Upload Mode Selector */
.image-upload-mode {
  margin-bottom: 16px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.mode-selector {
  width: 100%;
  display: flex;
  justify-content: center;
}

.mode-selector .el-radio-button {
  flex: 1;
}

.mode-selector .el-radio-button__inner {
  width: 100%;
  padding: 12px 20px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.mode-selector .el-radio-button--small .el-radio-button__inner {
  padding: 8px 15px;
}

/* Gallery mode specific styling */
.image-upload-mode + div {
  transition: all 0.3s ease;
}

/* Enhanced visual feedback */
.mode-selector .el-radio-button__inner:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* New Section Styles */
.subsection {
  margin-bottom: 24px;
  padding: 16px;
  background: #fafbfc;
  border-radius: 8px;
  border: 1px solid #e5e8eb;
}

.subsection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.subsection-title {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.accessory-section-title {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin: 0 0 12px 0;
}

.list-item {
  margin-bottom: 12px;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background-color: #fafafa;
}

.item-info {
  font-size: 12px;
  color: #6b7280;
}

.feature-item {
  margin-bottom: 16px;
}

.feature-card {
  border: 1px solid #e5e8eb;
}

.accessory-section {
  margin-bottom: 20px;
}

.accessory-item {
  margin-bottom: 12px;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background-color: #fafafa;
}

.certificate-item {
  margin-bottom: 16px;
}

.certificate-actions {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.section-actions {
  display: flex;
  gap: 8px;
}

.warranty-terms {
  margin-top: 20px;
}

.terms-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.terms-title {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.term-item {
  margin-bottom: 8px;
}

.promise-item {
  margin-bottom: 8px;
}
</style>