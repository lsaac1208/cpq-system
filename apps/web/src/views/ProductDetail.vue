<template>
  <div class="product-detail">
    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="loading-content">
        <el-skeleton :rows="12" animated />
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <div class="error-content">
        <el-icon size="64" color="#f56c6c"><WarningFilled /></el-icon>
        <h2>产品未找到</h2>
        <p>{{ error }}</p>
        <div class="error-actions">
          <el-button @click="$router.go(-1)">返回上一页</el-button>
          <el-button type="primary" @click="$router.push('/products')">浏览产品</el-button>
        </div>
      </div>
    </div>

    <!-- Product Content -->
    <div v-else-if="product" class="product-container">
      <!-- Breadcrumb Navigation -->
      <div class="breadcrumb-section">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/' }">
            <el-icon><House /></el-icon>
            首页
          </el-breadcrumb-item>
          <el-breadcrumb-item :to="{ path: authStore.isAdmin ? '/products' : '/search' }">
            {{ authStore.isAdmin ? '产品管理' : '产品中心' }}
          </el-breadcrumb-item>
          <el-breadcrumb-item v-if="product.category">{{ product.category }}</el-breadcrumb-item>
          <el-breadcrumb-item>{{ editMode ? '编辑产品' : product.name }}</el-breadcrumb-item>
        </el-breadcrumb>
        
        <!-- Admin Controls -->
        <div v-if="authStore.canEditProducts" class="admin-controls">
          <el-button v-if="!editMode" type="primary" @click="enterEditMode">
            <el-icon><Edit /></el-icon>
            编辑产品
          </el-button>
          <div v-else class="edit-controls">
            <el-button @click="cancelEdit">取消编辑</el-button>
            <el-button type="primary" @click="saveProduct" :loading="saving">
              <el-icon><Check /></el-icon>
              保存修改
            </el-button>
          </div>
        </div>
      </div>

      <!-- Main Product Section -->
      <div class="product-main">
        <!-- Product Gallery -->
        <div class="product-gallery">
          <!-- 统一的图片集组件，支持查看和编辑模式 -->
          <ProductGallery
            v-if="product?.id"
            :product-id="product.id"
            :edit-mode="editMode && authStore.canEditProducts"
            :can-edit="authStore.canEditProducts"
            height="400px"
            @refresh="loadProduct"
            @image-change="handleImageChange"
            @images-update="handleImagesUpdate"
          />
        </div>

        <!-- Product Information -->
        <div class="product-info">
          <!-- Product Status Tags -->
          <div class="product-status">
            <el-tag 
              :type="(editMode ? formData.is_active : product.is_active) ? 'success' : 'danger'" 
              size="large"
              effect="light"
            >
              {{ (editMode ? formData.is_active : product.is_active) ? '有效产品' : '已停产' }}
            </el-tag>
            <el-tag 
              v-if="editMode ? formData.is_configurable : product.is_configurable" 
              type="primary" 
              size="large"
              effect="light"
            >
              <el-icon><Setting /></el-icon>
              可定制配置
            </el-tag>
            <el-tag 
              v-if="isCreatedFromAI" 
              type="warning" 
              size="large"
              effect="light"
            >
              <el-icon><Lightning /></el-icon>
              AI智能创建
            </el-tag>
            
            <!-- Edit Mode Status Controls -->
            <div v-if="editMode && authStore.canEditProducts" class="status-controls">
              <el-switch
                v-model="formData.is_active"
                active-text="启用"
                inactive-text="禁用"
                inline-prompt
              />
              <el-switch
                v-model="formData.is_configurable"
                active-text="可配置"
                inactive-text="固定"
                inline-prompt
              />
            </div>
          </div>

          <!-- Product Title and Code -->
          <div class="product-header-info">
            <h1 v-if="!editMode" class="product-title">{{ product.name }}</h1>
            <el-input
              v-else
              v-model="formData.name"
              class="product-title-edit"
              size="large"
              placeholder="请输入产品名称"
            />
            
            <p v-if="!editMode" class="product-code">产品编码: {{ product.code }}</p>
            <div v-else class="product-code-edit">
              <span>产品编码: </span>
              <el-input
                v-model="formData.code"
                style="width: 200px"
                placeholder="请输入产品编码"
              />
            </div>
          </div>

          <!-- Basic Information Card -->
          <div class="basic-info-card">
            <div class="info-item">
              <div class="info-label">
                <el-icon><Folder /></el-icon>
                产品分类
              </div>
              <div v-if="!editMode" class="info-value">{{ product.category || '未分类' }}</div>
              <el-input
                v-else
                v-model="formData.category"
                class="info-value-edit"
                placeholder="请输入产品分类"
              />
            </div>
            
            <div class="info-item">
              <div class="info-label">
                <el-icon><Money /></el-icon>
                基础价格
              </div>
              <div v-if="!editMode" class="info-value price">
                ¥{{ formatPrice(product.base_price) }}
                <span v-if="product.is_configurable" class="price-note">起</span>
              </div>
              <el-input-number
                v-else
                v-model="formData.base_price"
                :min="0"
                :precision="2"
                class="info-value-edit"
              />
            </div>
            
            <div class="info-item">
              <div class="info-label">
                <el-icon><Document /></el-icon>
                产品描述
              </div>
              <div v-if="!editMode" class="info-value">
                {{ product.description || '暂无描述' }}
              </div>
              <el-input
                v-else
                v-model="formData.description"
                type="textarea"
                :rows="3"
                class="info-value-edit"
                placeholder="请输入产品描述"
              />
            </div>
            
            <div class="info-item">
              <div class="info-label">
                <el-icon><Calendar /></el-icon>
                发布时间
              </div>
              <div class="info-value">{{ formatDate(product.created_at) }}</div>
            </div>
          </div>

          <!-- Key Specifications Preview -->
          <div v-if="keySpecifications.length > 0" class="key-specs-preview">
            <h3>核心规格</h3>
            <div class="key-specs-grid">
              <div
                v-for="spec in keySpecifications"
                :key="spec.key"
                class="key-spec-item"
              >
                <div class="spec-label">{{ spec.label }}</div>
                <div class="spec-value">{{ spec.value }}</div>
              </div>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="product-actions">
            <el-button
              v-if="!authStore.isAdmin"
              type="primary"
              size="large"
              :loading="addingToQuote"
              @click="handleAddToQuote"
            >
              <el-icon><Plus /></el-icon>
              加入询价单
            </el-button>
            
            <el-button
              v-if="!authStore.isAdmin"
              size="large"
              @click="handleContactSupplier"
            >
              <el-icon><Phone /></el-icon>
              联系供应商
            </el-button>
            
            <el-button
              v-if="!authStore.isAdmin"
              size="large"
              @click="handleShare"
            >
              <el-icon><Share /></el-icon>
              分享产品
            </el-button>
          </div>
        </div>
      </div>

      <!-- Anchor Navigation Long Page -->
      <div class="product-long-page-container">
        <!-- Anchor Navigation -->
        <div class="anchor-navigation" ref="anchorNav">
          <div class="nav-container">
            <div class="nav-list">
              <a 
                v-for="section in sections" 
                :key="section.id"
                :href="`#${section.id}`"
                :class="['nav-item', { active: activeSection === section.id }]"
                @click="scrollToSection(section.id, $event)"
              >
                <el-icon><component :is="section.icon" /></el-icon>
                <span>{{ section.label }}</span>
              </a>
            </div>
          </div>
        </div>

        <!-- Long Page Content -->
        <div class="long-page-content" ref="longPageContent">
          <!-- 产品简介 Section -->
          <section id="overview" class="content-section overview-section">
            <div class="section-header">
              <h2>
                <el-icon><Document /></el-icon>
                产品简介
              </h2>
            </div>
            <div class="section-content overview-content">
              <!-- AI分析来源提示 -->
              <div v-if="isCreatedFromAI" class="ai-source-notice">
                <div class="ai-notice-content">
                  <el-icon class="ai-icon"><Lightning /></el-icon>
                  <div class="ai-text">
                    <h4>AI智能分析生成</h4>
                    <p>此产品信息由AI智能分析文档生成，包含自动提取的技术规格、产品特性和应用场景。</p>
                  </div>
                </div>
              </div>
              
              <div class="content-section">
                <h3>产品介绍</h3>
                <div class="product-description">
                  <p v-if="!editMode">
                    {{ product.detailed_description || product.description || '请在编辑模式中添加产品详细介绍' }}
                  </p>
                  <el-input
                    v-else
                    v-model="formData.detailed_description"
                    type="textarea"
                    :rows="8"
                    placeholder="请输入产品详细介绍"
                    class="description-editor"
                  />
                </div>
                
                <div v-if="product?.application_scenarios && Array.isArray(product.application_scenarios) && product.application_scenarios.length > 0" class="application-scenarios">
                  <h4><el-icon><Setting /></el-icon>应用场景</h4>
                  <ul class="scenario-list">
                    <li v-for="scenario in product.application_scenarios" :key="scenario.id">
                      <el-icon v-if="scenario.icon"><component :is="scenario.icon" /></el-icon>
                      <el-icon v-else><Star /></el-icon>
                      {{ scenario.name }}
                    </li>
                  </ul>
                </div>
                <div v-else-if="!editMode" class="application-scenarios">
                  <h4><el-icon><Setting /></el-icon>应用场景</h4>
                  <p class="no-data">暂未设置应用场景信息</p>
                </div>
              </div>
            </div>
          </section>

          <!-- 产品特点 Section -->
          <section id="features" class="content-section features-section">
            <div class="section-header">
              <h2>
                <el-icon><Star /></el-icon>
                产品特点
              </h2>
            </div>
            <div class="section-content features-content">
              <div class="content-section">
                <h3>产品优势特点</h3>
                <div v-if="product?.features && Array.isArray(product.features) && product.features.length > 0" class="features-grid">
                  <div
                    v-for="feature in product.features"
                    :key="feature.id"
                    class="feature-card"
                  >
                    <div class="feature-icon">
                      <el-icon v-if="feature.icon" color="#2563eb">
                        <component :is="feature.icon" />
                      </el-icon>
                      <el-icon v-else color="#2563eb"><Star /></el-icon>
                    </div>
                    <div class="feature-info">
                      <h4>{{ feature.title }}</h4>
                      <p>{{ feature.description }}</p>
                    </div>
                  </div>
                </div>
                <div v-else class="no-features-message">
                  <el-empty description="暂未设置产品特点信息">
                    <template #image>
                      <el-icon size="60" color="#d1d5db"><Star /></el-icon>
                    </template>
                  </el-empty>
                </div>
              </div>
            </div>
          </section>

          <!-- 技术参数 Section -->
          <section id="specifications" class="content-section specifications-section">
            <div class="section-header">
              <h2>
                <el-icon><Grid /></el-icon>
                技术参数
              </h2>
            </div>
            <div class="section-content specifications-content">
              <div class="content-section">
                <div class="spec-header">
                  <h3><el-icon><Grid /></el-icon>技术参数</h3>
                  <div v-if="editMode && authStore.canEditProducts" class="spec-controls">
                    <el-button type="primary" size="small" @click="addSpecification">
                      <el-icon><Plus /></el-icon>
                      添加规格
                    </el-button>
                  </div>
                </div>
                
                <div v-if="!editMode" class="specifications-table">
                  <el-table :data="formattedSpecifications" stripe class="spec-table">
                    <el-table-column prop="label" label="参数名称" width="200" />
                    <el-table-column prop="displayValue" label="数值" width="150" />
                    <el-table-column prop="unit" label="单位" width="100" />
                    <el-table-column prop="description" label="说明" />
                  </el-table>
                </div>
                
                <div v-else class="specifications-editor">
                  <div
                    v-for="(spec, key) in formData.specifications"
                    :key="key"
                    class="spec-edit-item"
                  >
                    <el-row :gutter="16">
                      <el-col :span="6">
                        <el-input v-model="spec.label" placeholder="规格名称" />
                      </el-col>
                      <el-col :span="6">
                        <el-input v-model="spec.value" placeholder="数值" />
                      </el-col>
                      <el-col :span="4">
                        <el-input v-model="spec.unit" placeholder="单位" />
                      </el-col>
                      <el-col :span="6">
                        <el-input v-model="spec.description" placeholder="说明" />
                      </el-col>
                      <el-col :span="2">
                        <el-button
                          type="danger"
                          icon="Delete"
                          @click="removeSpecification(key)"
                        />
                      </el-col>
                    </el-row>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <!-- 附件配件 Section -->
          <section id="accessories" class="content-section accessories-section">
            <div class="section-header">
              <h2>
                <el-icon><Box /></el-icon>
                附件配件
              </h2>
            </div>
            <div class="section-content accessories-content">
              <div class="content-section">
                <!-- Standard Accessories -->
                <div v-if="standardAccessories && standardAccessories.length > 0">
                  <h3><el-icon><Box /></el-icon>标准配置</h3>
                  <div class="accessories-grid">
                    <div
                      v-for="accessory in standardAccessories"
                      :key="accessory.id"
                      class="accessory-item"
                    >
                      <div class="accessory-icon">
                        <el-icon v-if="accessory.icon">
                          <component :is="accessory.icon" />
                        </el-icon>
                        <el-icon v-else><Box /></el-icon>
                      </div>
                      <div class="accessory-info">
                        <h4>{{ accessory.name }}</h4>
                        <p>{{ accessory.description }}</p>
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- Optional Accessories -->
                <div v-if="optionalAccessories && optionalAccessories.length > 0" class="optional-accessories">
                  <h4><el-icon><Plus /></el-icon>可选配件</h4>
                  <ul class="optional-list">
                    <li v-for="accessory in optionalAccessories" :key="accessory.id">
                      {{ accessory.name }} - {{ accessory.description }}
                    </li>
                  </ul>
                </div>
                
                <!-- No accessories message -->
                <div v-if="!product?.accessories || !Array.isArray(product.accessories) || product.accessories.length === 0" class="no-accessories">
                  <el-empty description="暂未设置配件信息">
                    <template #image>
                      <el-icon size="60" color="#d1d5db"><Box /></el-icon>
                    </template>
                  </el-empty>
                </div>
              </div>
            </div>
          </section>

          <!-- 检定证书 Section -->
          <section id="certificates" class="content-section certificates-section">
            <div class="section-header">
              <h2>
                <el-icon><Medal /></el-icon>
                检定证书
              </h2>
            </div>
            <div class="section-content certificates-content">
              <div class="content-section">
                <h3><el-icon><Medal /></el-icon>质量认证</h3>
                <div v-if="product?.certificates && Array.isArray(product.certificates) && product.certificates.length > 0" class="certificates-grid">
                  <div
                    v-for="certificate in product.certificates"
                    :key="certificate.id"
                    class="certificate-card"
                  >
                    <div class="cert-icon">
                      <el-icon><Medal /></el-icon>
                    </div>
                    <div class="cert-info">
                      <h4>{{ certificate.name }}</h4>
                      <p>{{ certificate.description }}</p>
                      <p v-if="certificate.certificate_number" class="cert-number">
                        证书编号: {{ certificate.certificate_number }}
                      </p>
                    </div>
                  </div>
                </div>
                <div v-else class="no-certificates">
                  <el-empty description="暂未设置证书信息">
                    <template #image>
                      <el-icon size="60" color="#d1d5db"><Medal /></el-icon>
                    </template>
                  </el-empty>
                </div>
              </div>
            </div>
          </section>

          <!-- 售后保障 Section -->
          <section id="support" class="content-section support-section">
            <div class="section-header">
              <h2>
                <el-icon><Service /></el-icon>
                售后保障
              </h2>
            </div>
            <div class="section-content support-content">
              <div class="content-section">
                <h3><el-icon><Service /></el-icon>服务承诺</h3>
                
                <!-- Warranty Information -->
                <div v-if="product.support_info?.warranty" class="warranty-info">
                  <div class="warranty-card">
                    <div class="warranty-icon">
                      <el-icon color="#059669"><Lock /></el-icon>
                    </div>
                    <div class="warranty-details">
                      <h4>质量保证</h4>
                      <p v-if="product?.support_info?.warranty?.period">
                        质保期：{{ product.support_info.warranty.period }}
                      </p>
                      <p v-if="product?.support_info?.warranty?.coverage">
                        {{ product.support_info.warranty.coverage }}
                      </p>
                      <div v-if="product?.support_info?.warranty?.terms?.length > 0">
                        <p v-for="(term, index) in product.support_info.warranty.terms" :key="index">
                          {{ term }}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- Contact Information -->
                <div v-if="hasContactInfo" class="contact-support">
                  <h4><el-icon><Phone /></el-icon>联系我们</h4>
                  <div class="contact-grid">
                    <div v-if="product.support_info?.contact_info?.sales_phone" class="contact-item">
                      <el-icon><Phone /></el-icon>
                      <div class="contact-details">
                        <div class="contact-label">销售热线</div>
                        <div class="contact-value">{{ product.support_info.contact_info.sales_phone }}</div>
                      </div>
                    </div>
                    
                    <div v-if="product.support_info?.contact_info?.sales_email" class="contact-item">
                      <el-icon><Message /></el-icon>
                      <div class="contact-details">
                        <div class="contact-label">邮箱咨询</div>
                        <div class="contact-value">{{ product.support_info.contact_info.sales_email }}</div>
                      </div>
                    </div>
                    
                    <div v-if="product.support_info?.contact_info?.service_wechat" class="contact-item">
                      <el-icon><ChatDotRound /></el-icon>
                      <div class="contact-details">
                        <div class="contact-label">在线客服</div>
                        <div class="contact-value">微信: {{ product.support_info.contact_info.service_wechat }}</div>
                      </div>
                    </div>
                    
                    <div v-if="product.support_info?.contact_info?.support_email" class="contact-item">
                      <el-icon><Service /></el-icon>
                      <div class="contact-details">
                        <div class="contact-label">技术支持</div>
                        <div class="contact-value">{{ product.support_info.contact_info.support_email }}</div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- Service Promises -->
                <div v-if="product?.support_info?.service_promises && Array.isArray(product.support_info.service_promises) && product.support_info.service_promises.length > 0" class="service-promise">
                  <h4><el-icon><Star /></el-icon>服务承诺</h4>
                  <ul class="promise-list">
                    <li v-for="(promise, index) in product.support_info.service_promises" :key="index">
                      ✓ {{ promise }}
                    </li>
                  </ul>
                </div>
                
                <!-- No support info message -->
                <div v-if="!hasSupportInfo" class="no-support">
                  <el-empty description="暂未设置售后保障信息">
                    <template #image>
                      <el-icon size="60" color="#d1d5db"><Service /></el-icon>
                    </template>
                  </el-empty>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>

    <!-- Back to Top Button -->
    <button 
      v-show="showBackToTop"
      :class="['back-to-top', { visible: showBackToTop }]"
      @click="scrollToTop"
      aria-label="回到顶部"
    >
      <el-icon><Top /></el-icon>
    </button>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { showMessage } from '@/utils/message'
import { 
  House, Edit, Check, Picture, Setting, Folder, Money, 
  Document, Calendar, Plus, Phone, Share, Grid, Tools, 
  Service, ChatDotRound, Message, WarningFilled,
  Lightning, School, Monitor, View, CircleCheck, Box,
  Medal, Star, Lock, Top
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import http from '@/api/http'
import ProductGallery from '@/components/ProductGallery.vue'

// 路由和store
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// 状态
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const product = ref<any>(null)
const editMode = ref(false)
const addingToQuote = ref(false)
const selectedImageIndex = ref(0)
const activeSection = ref('overview')
const anchorNav = ref<HTMLElement>()
const longPageContent = ref<HTMLElement>()

// 定义导航区域
const sections = ref([
  { id: 'overview', label: '产品简介', icon: 'Document' },
  { id: 'features', label: '产品特点', icon: 'Star' },
  { id: 'specifications', label: '技术参数', icon: 'Grid' },
  { id: 'accessories', label: '附件配件', icon: 'Box' },
  { id: 'certificates', label: '检定证书', icon: 'Medal' },
  { id: 'support', label: '售后保障', icon: 'Service' }
])

// 表单数据
const formData = reactive({
  name: '',
  code: '',
  category: '',
  description: '',
  base_price: 0,
  image_url: '',
  is_active: true,
  is_configurable: false,
  configuration_schema: {} as Record<string, any>,
  specifications: {} as Record<string, any>,
  // Extended fields - 仅用于显示，不发送到后端
  detailed_description: '',
  application_scenarios: [] as any[],
  features: [] as any[],
  accessories: [] as any[],
  certificates: [] as any[],
  support_info: {
    warranty: { period: '', coverage: '', terms: [] },
    contact_info: {},
    service_promises: []
  }
})

// 默认产品图片
const defaultProductImage = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE1MCIgdmlld0JveD0iMCAwIDIwMCAxNTAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMTUwIiBmaWxsPSIjRjVGN0ZBIi8+CjxwYXRoIGQ9Ik03NyA2N0g4M1Y3M0g3N1Y2N1pNODMgNjFINzdWNjdIODNWNjFaTTc3IDczSDgzVjc5SDc3VjczWk04OSA2N0g5NVY3M0g4OVY2N1pNOTUgNjFIOTlWNjdIOTVWNjFaTTEwMSA2N0gxMDdWNzNIMTAxVjY3Wk0xMDcgNjFIMTEzVjY3SDEwN1Y2MVpNMTEzIDY3SDExOVY3M0gxMTNWNjdaTTExOSA2MUgxMjVWNjdIMTE5VjYxWiIgZmlsbD0iI0MwQzRDQyIvPgo8dGV4dCB4PSIxMDAiIHk9IjkwIiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM5MDkzOTkiIHRleHQtYW5jaG9yPSJtaWRkbGUiPueUn+WTgeWbvueJhzwvdGV4dD4KPC9zdmc+'

// 计算属性
const productImageSrc = computed(() => {
  if (!product.value) return defaultProductImage
  
  try {
    const imageUrl = product.value.image_url || 
                     product.value.image || 
                     product.value.photo_url ||
                     null
    
    if (imageUrl && typeof imageUrl === 'string' && imageUrl.trim()) {
      if (imageUrl.startsWith('/')) return imageUrl
      if (imageUrl.startsWith('http')) return imageUrl
      return `/images/products/${imageUrl}`
    }
  } catch (error) {
    console.warn('Error processing product image URL:', error)
  }
  
  return defaultProductImage
})

const hasValidImage = computed(() => {
  if (!product.value) return false
  
  try {
    const imageUrl = product.value.image_url || product.value.image || product.value.photo_url
    return imageUrl && typeof imageUrl === 'string' && imageUrl.trim().length > 0
  } catch (error) {
    console.warn('Error checking image validity:', error)
    return false
  }
})

// 图片集事件处理 - 添加安全性检查
const handleImageChange = (imageUrl: string) => {
  console.log('Main image changed:', imageUrl)
  if (product.value && imageUrl && typeof imageUrl === 'string') {
    product.value.image_url = imageUrl
    // 同步更新表单数据
    formData.image_url = imageUrl
  }
}

const handleImagesUpdate = (images: any[]) => {
  console.log('Images updated:', images)
  
  if (!Array.isArray(images) || !product.value) {
    return
  }
  
  try {
    // 更新主图信息
    const primaryImage = images.find(img => img && img.is_primary && img.image_url)
    if (primaryImage) {
      product.value.image_url = primaryImage.image_url
      formData.image_url = primaryImage.image_url
    }
  } catch (error) {
    console.warn('Error updating images:', error)
  }
}

const productImages = computed(() => {
  const images = []
  if (hasValidImage.value) {
    images.push(productImageSrc.value)
  } else {
    images.push(defaultProductImage)
  }
  return images
})

const keySpecifications = computed(() => {
  if (!product.value?.specifications || typeof product.value.specifications !== 'object') {
    return []
  }
  
  try {
    return Object.entries(product.value.specifications)
      .slice(0, 4)
      .map(([key, value]) => {
        const spec = formatSpecification(key, value)
        return {
          key,
          label: spec.label,
          value: spec.displayValue + (spec.unit ? spec.unit : '')
        }
      })
  } catch (error) {
    console.warn('Error processing key specifications:', error)
    return []
  }
})

const formattedSpecifications = computed(() => {
  if (!product.value?.specifications || typeof product.value.specifications !== 'object') {
    return []
  }
  
  try {
    return Object.entries(product.value.specifications).map(([key, value]) => {
      return formatSpecification(key, value)
    })
  } catch (error) {
    console.warn('Error processing specifications:', error)
    return []
  }
})

// 方法
const formatSpecification = (key: string, value: any) => {
  const labelMap: Record<string, string> = {
    power: '功率',
    voltage: '电压',
    current: '电流',
    speed: '转速',
    efficiency: '效率',
    weight: '重量',
    dimensions: '尺寸',
    protection: '防护等级',
    mounting: '安装方式',
    cooling: '冷却方式',
    '电压': '电压',
    '电流': '电流',
    '额定功率': '额定功率'
  }
  
  const label = labelMap[key] || key
  let displayValue: string
  let unit: string | undefined
  let description: string | undefined
  
  if (value === null || value === undefined) {
    displayValue = '-'
  } else if (typeof value === 'object') {
    if (Array.isArray(value)) {
      displayValue = value.join(', ')
    } else if (value.value !== undefined) {
      displayValue = String(value.value)
      unit = value.unit
      description = value.description
    } else if (value.min !== undefined && value.max !== undefined) {
      displayValue = `${value.min}-${value.max}`
      unit = value.unit
      description = value.description
    } else {
      displayValue = '多参数配置'
    }
  } else if (typeof value === 'boolean') {
    displayValue = value ? '是' : '否'
  } else {
    displayValue = String(value)
  }
  
  return {
    label,
    value,
    displayValue,
    unit: unit || '',
    description: description || ''
  }
}

const formatPrice = (price: string | number): string => {
  const numPrice = typeof price === 'string' ? parseFloat(price) : price
  return numPrice.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const getConfigOptions = (config: any): string => {
  if (config.options && Array.isArray(config.options)) {
    return config.options.slice(0, 3).join(', ') + (config.options.length > 3 ? '...' : '')
  }
  return '可配置'
}

const loadProduct = async () => {
  const productId = route.params.id
  if (!productId) return

  console.log('📦 开始加载产品信息', { productId })
  loading.value = true
  error.value = ''

  try {
    const response = await http.get(`/products/${productId}`)
    console.log('📦 ProductDetail API response:', response)
    
    // 处理API响应结构 - 兼容不同的响应格式
    const productData = response.data?.product || response.product || response.data
    product.value = productData
    
    console.log('✅ 产品信息加载成功', {
      productId: product.value?.id,
      productName: product.value?.name,
      hasProductGallery: !!document.querySelector('ProductGallery')
    })
    
    // 初始化表单数据，添加安全性检查
    Object.assign(formData, {
      name: product.value?.name || '',
      code: product.value?.code || '',
      category: product.value?.category || '',
      description: product.value?.description || '',
      base_price: product.value?.base_price ? parseFloat(product.value.base_price) : 0,
      image_url: product.value?.image_url || '',
      is_active: Boolean(product.value?.is_active),
      is_configurable: Boolean(product.value?.is_configurable),
      configuration_schema: (product.value?.configuration_schema && typeof product.value.configuration_schema === 'object') 
        ? { ...product.value.configuration_schema } : {},
      specifications: (product.value?.specifications && typeof product.value.specifications === 'object') 
        ? { ...product.value.specifications } : {},
      // Extended fields with safe defaults
      detailed_description: product.value?.detailed_description || '',
      application_scenarios: Array.isArray(product.value?.application_scenarios) 
        ? [...product.value.application_scenarios] : [],
      features: Array.isArray(product.value?.features) 
        ? [...product.value.features] : [],
      accessories: Array.isArray(product.value?.accessories) 
        ? [...product.value.accessories] : [],
      certificates: Array.isArray(product.value?.certificates) 
        ? [...product.value.certificates] : [],
      support_info: product.value?.support_info || {
        warranty: { period: '', coverage: '', terms: [] },
        contact_info: {},
        service_promises: []
      }
    })
  } catch (err: any) {
    error.value = err.response?.data?.message || '加载产品信息失败'
  } finally {
    loading.value = false
  }
}

const enterEditMode = () => {
  editMode.value = true
}

const cancelEdit = () => {
  editMode.value = false
  // 重置表单数据
  Object.assign(formData, {
    name: product.value.name,
    code: product.value.code,
    category: product.value.category || '',
    description: product.value.description || '',
    base_price: parseFloat(product.value.base_price),
    image_url: product.value.image_url || '',
    is_active: product.value.is_active,
    is_configurable: product.value.is_configurable,
    configuration_schema: { ...product.value.configuration_schema } || {},
    specifications: { ...product.value.specifications } || {}
  })

// Computed properties for dynamic content - 修复数据访问错误
const standardAccessories = computed(() => {
  if (!product.value?.accessories || !Array.isArray(product.value.accessories)) {
    return []
  }
  return product.value.accessories.filter(acc => acc && acc.type === 'standard') || []
})

const optionalAccessories = computed(() => {
  if (!product.value?.accessories || !Array.isArray(product.value.accessories)) {
    return []
  }
  return product.value.accessories.filter(acc => acc && acc.type === 'optional') || []
})

const hasContactInfo = computed(() => {
  if (!product.value?.support_info?.contact_info) {
    return false
  }
  const contact = product.value.support_info.contact_info
  return !!(contact?.sales_phone || contact?.sales_email || contact?.support_phone || 
           contact?.support_email || contact?.service_wechat)
})

const hasSupportInfo = computed(() => {
  if (!product.value?.support_info) {
    return false
  }
  const support = product.value.support_info
  const hasWarrantyInfo = support?.warranty?.period || support?.warranty?.coverage || 
                         (support?.warranty?.terms && Array.isArray(support.warranty.terms) && support.warranty.terms.length > 0)
  const hasServicePromises = support?.service_promises && Array.isArray(support.service_promises) && support.service_promises.length > 0
  return !!(hasWarrantyInfo || hasContactInfo.value || hasServicePromises)
})

// 检测产品是否来自AI分析创建
const isCreatedFromAI = computed(() => {
  // 如果产品有详细的特性、规格和描述结构，且近期创建，则可能来自AI
  if (!product.value) return false
  
  const hasDetailedFeatures = product.value.features && Array.isArray(product.value.features) && product.value.features.length > 0
  const hasDetailedSpecs = product.value.specifications && typeof product.value.specifications === 'object' && Object.keys(product.value.specifications).length > 3
  const hasApplicationScenarios = product.value.application_scenarios && Array.isArray(product.value.application_scenarios) && product.value.application_scenarios.length > 0
  const hasDetailedDescription = product.value.detailed_description && product.value.detailed_description.length > 50
  
  // 检查是否在最近一天内创建且具有AI特征
  const createdRecently = product.value.created_at && (Date.now() - new Date(product.value.created_at).getTime()) < 24 * 60 * 60 * 1000
  
  // 如果有多个AI特征且是最近创建的，则判定为AI创建
  const aiFeatureCount = [hasDetailedFeatures, hasDetailedSpecs, hasApplicationScenarios, hasDetailedDescription].filter(Boolean).length
  
  return createdRecently && aiFeatureCount >= 2
})
}

const saveProduct = async () => {
  console.log('💾 开始保存产品信息')
  saving.value = true

  try {
    const productId = route.params.id
    
    // 只发送后端期望的字段
    const updateData = {
      name: formData.name,
      code: formData.code,
      description: formData.description,
      category: formData.category,
      base_price: formData.base_price,
      image_url: formData.image_url,
      configuration_schema: formData.configuration_schema || {},
      specifications: formData.specifications || {},
      is_active: formData.is_active,
      is_configurable: formData.is_configurable
    }
    
    console.log('📤 发送更新数据:', updateData)
    
    const response = await http.put(`/products/${productId}`, updateData)
    console.log('✅ 产品更新成功:', response.data)
    
    // 更新product数据
    Object.assign(product.value, updateData)
    
    showMessage.success('产品信息已保存')
    editMode.value = false
  } catch (err: any) {
    console.error('❌ 产品保存失败:', err)
    console.error('📊 错误详情:', {
      status: err.response?.status,
      data: err.response?.data,
      message: err.message
    })
    
    const errorMessage = err.response?.data?.error || 
                        err.response?.data?.message || 
                        '保存失败'
    showMessage.error(errorMessage)
  } finally {
    saving.value = false
  }
}

const addSpecification = () => {
  const key = `spec_${Date.now()}`
  formData.specifications[key] = {
    label: '',
    value: '',
    unit: '',
    description: ''
  }
}

const removeSpecification = (key: string) => {
  delete formData.specifications[key]
}

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.src = defaultProductImage
}

const handleAddToQuote = async () => {
  if (!product.value || addingToQuote.value) return
  
  addingToQuote.value = true
  
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    showMessage.success(`产品 "${product.value?.name || '未知产品'}" 已添加到询价单`)
  } catch (error) {
    showMessage.error('加入询价单失败，请稍后重试')
  } finally {
    addingToQuote.value = false
  }
}

const handleContactSupplier = () => {
  ElMessageBox.alert(
    '请拨打销售热线 400-123-4567 或发送邮件至 sales@company.com',
    '联系供应商',
    {
      confirmButtonText: '确定',
      type: 'info'
    }
  )
}

const handleShare = async () => {
  if (!product.value) return
  
  const shareUrl = window.location.href
  const shareText = `${product.value.name} - ${product.value.description || '优质产品'}`
  
  if (navigator.share) {
    try {
      await navigator.share({
        title: product.value.name,
        text: shareText,
        url: shareUrl
      })
    } catch (error) {
      // 用户取消了分享
    }
  } else {
    try {
      await navigator.clipboard.writeText(shareUrl)
      showMessage.success('产品链接已复制到剪贴板')
    } catch (error) {
      showMessage.error('分享失败')
    }
  }
}

// 锥点导航功能
const scrollToSection = (sectionId: string, event?: Event) => {
  if (event) {
    event.preventDefault()
  }
  
  const targetElement = document.getElementById(sectionId)
  if (targetElement) {
    const navHeight = anchorNav.value?.offsetHeight || 0
    const targetPosition = targetElement.offsetTop - navHeight - 20
    
    window.scrollTo({
      top: targetPosition,
      behavior: 'smooth'
    })
    
    activeSection.value = sectionId
    // 更新 URL 哈希
    window.history.replaceState(null, '', `#${sectionId}`)
  }
}

// 监听滚动事件来更新活跃区域
const handleScroll = () => {
  const navHeight = anchorNav.value?.offsetHeight || 0
  const scrollTop = window.pageYOffset || document.documentElement.scrollTop
  
  for (let i = sections.value.length - 1; i >= 0; i--) {
    const section = sections.value[i]
    const element = document.getElementById(section.id)
    
    if (element && element.offsetTop - navHeight - 50 <= scrollTop) {
      activeSection.value = section.id
      break
    }
  }
}

// 初始化页面滚动位置
const initializeScrollPosition = async () => {
  await nextTick()
  
  const hash = window.location.hash.substring(1)
  if (hash && sections.value.some(s => s.id === hash)) {
    setTimeout(() => {
      scrollToSection(hash)
    }, 100)
  }
}

// 回到顶部功能
const showBackToTop = ref(false)

const scrollToTop = () => {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  })
}

const handleScrollForBackToTop = () => {
  showBackToTop.value = window.pageYOffset > 300
}

// 结合滚动事件处理
const combinedScrollHandler = () => {
  handleScroll()
  handleScrollForBackToTop()
}

// 初始化
onMounted(async () => {
  await loadProduct()
  await initializeScrollPosition()
  
  // 添加滚动监听
  window.addEventListener('scroll', combinedScrollHandler, { passive: true })
})

onUnmounted(() => {
  // 清理滚动监听
  window.removeEventListener('scroll', combinedScrollHandler)
})
</script>

<style scoped>
/* Base Styles */
.product-detail {
  min-height: 100vh;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
}

/* Loading & Error States */
.loading-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
}

.loading-content {
  background: white;
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.error-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 80px 20px;
}

.error-content {
  text-align: center;
  background: white;
  border-radius: 16px;
  padding: 60px 40px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.error-content h2 {
  font-size: 24px;
  color: #1e293b;
  margin: 20px 0 12px 0;
  font-weight: 600;
}

.error-content p {
  color: #64748b;
  margin-bottom: 32px;
  font-size: 16px;
}

.error-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
}

/* Product Container */
.product-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px 20px;
}

/* Breadcrumb Section */
.breadcrumb-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding: 20px 0;
  border-bottom: 1px solid #e2e8f0;
}

.admin-controls {
  display: flex;
  gap: 12px;
}

.edit-controls {
  display: flex;
  gap: 12px;
}

/* Product Main */
.product-main {
  display: grid;
  grid-template-columns: 460px 1fr;
  gap: 48px;
  background: white;
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  margin-bottom: 32px;
}

/* Product Gallery */
.product-gallery {
  display: flex;
  flex-direction: column;
  gap: 16px;
}


.main-image-container {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.main-image {
  height: 340px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.main-image img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  transition: transform 0.3s ease;
}

.main-image:hover img {
  transform: scale(1.02);
}

.image-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #94a3b8;
  font-size: 14px;
}

/* Image Thumbnails */
.image-thumbnails {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.thumbnail {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  overflow: hidden;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
}

.thumbnail:hover,
.thumbnail.active {
  border-color: #2563eb;
}

.thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Product Info */
.product-info {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* Product Status */
.product-status {
  display: flex;
  gap: 12px;
  align-items: center;
}

.status-controls {
  display: flex;
  gap: 16px;
  margin-left: auto;
}

/* Product Header */
.product-header-info {
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 20px;
}

.product-title {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 8px 0;
  line-height: 1.3;
}

.product-title-edit {
  margin-bottom: 12px;
}

.product-title-edit :deep(.el-input__wrapper) {
  font-size: 28px;
  font-weight: 700;
}

.product-code {
  font-size: 16px;
  color: #64748b;
  margin: 0;
  font-family: 'Courier New', monospace;
}

.product-code-edit {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  color: #64748b;
  font-family: 'Courier New', monospace;
}

/* Basic Info Card */
.basic-info-card {
  background: #f8fafc;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e2e8f0;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #e2e8f0;
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #374151;
  font-size: 14px;
}

.info-label .el-icon {
  color: #2563eb;
  font-size: 16px;
}

.info-value {
  font-size: 16px;
  color: #1e293b;
  text-align: right;
  max-width: 60%;
}

.info-value.price {
  font-size: 20px;
  font-weight: 700;
  color: #dc2626;
}

.price-note {
  font-size: 14px;
  color: #64748b;
  font-weight: 400;
  margin-left: 4px;
}

.info-value-edit {
  max-width: 60%;
}

/* Key Specifications */
.key-specs-preview h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 16px 0;
}

.key-specs-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.key-spec-item {
  background: #f1f5f9;
  padding: 16px;
  border-radius: 8px;
  border-left: 4px solid #2563eb;
}

.spec-label {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.spec-value {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

/* Product Actions */
.product-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.product-actions .el-button {
  flex: 1;
  min-width: 140px;
}

/* Long Page Container */
.product-long-page-container {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  margin-bottom: 32px;
  overflow: hidden;
}

/* Anchor Navigation */
.anchor-navigation {
  position: sticky;
  top: 0;
  z-index: 100;
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.nav-container {
  max-width: 100%;
  padding: 0 32px;
}

.nav-list {
  display: flex;
  align-items: center;
  overflow-x: auto;
  gap: 0;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.nav-list::-webkit-scrollbar {
  display: none;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 24px;
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  font-size: 16px;
  font-weight: 500;
  white-space: nowrap;
  transition: all 0.3s ease;
  position: relative;
  border-radius: 0;
}

.nav-item:hover {
  color: white;
  background: rgba(255, 255, 255, 0.1);
}

.nav-item.active {
  color: white;
  background: rgba(255, 255, 255, 0.15);
  font-weight: 600;
}

.nav-item.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #fbbf24 0%, #f59e0b 100%);
}

.nav-item .el-icon {
  font-size: 18px;
}

/* Long Page Content */
.long-page-content {
  padding: 0;
}

/* Smooth scrolling for the whole page */
html {
  scroll-behavior: smooth;
}

/* Visual feedback for section transitions */
.content-section {
  transition: background-color 0.3s ease;
}

.content-section:target {
  background-color: rgba(37, 99, 235, 0.02);
}

/* Scroll indicator */
.anchor-navigation::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  height: 2px;
  background: rgba(255, 255, 255, 0.3);
  width: 100%;
}

/* Back to top button */
.back-to-top {
  position: fixed;
  bottom: 32px;
  right: 32px;
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  border: none;
  border-radius: 50%;
  color: white;
  font-size: 20px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
  transition: all 0.3s ease;
  z-index: 1000;
  opacity: 0;
  visibility: hidden;
  transform: translateY(10px);
}

.back-to-top.visible {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.back-to-top:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(37, 99, 235, 0.4);
}

/* Content Sections */
.content-section {
  padding: 40px 32px;
  border-bottom: 1px solid #e2e8f0;
  scroll-margin-top: 100px;
}

.content-section:last-child {
  border-bottom: none;
}

.section-header {
  margin-bottom: 32px;
  padding-bottom: 16px;
  border-bottom: 2px solid #e2e8f0;
}

.section-header h2 {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-header h2 .el-icon {
  font-size: 32px;
  color: #2563eb;
}

.section-content {
  max-width: 100%;
}

.section-content h3 {
  font-size: 22px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 24px 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-content h4 {
  font-size: 18px;
  font-weight: 600;
  color: #374151;
  margin: 24px 0 16px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Product Description */
.product-description {
  margin-bottom: 32px;
}

.product-description p {
  font-size: 16px;
  line-height: 1.7;
  color: #374151;
  margin: 0;
  text-align: justify;
}

.description-editor {
  margin-top: 16px;
}

/* Application Scenarios */
.application-scenarios {
  background: #f8fafc;
  border-radius: 12px;
  padding: 24px;
  border-left: 4px solid #2563eb;
}

.scenario-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.scenario-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #374151;
  padding: 8px 0;
}

.scenario-list li .el-icon {
  color: #2563eb;
  font-size: 16px;
}

/* Features Grid */
.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-top: 24px;
}

.feature-card {
  background: #f8fafc;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
  display: flex;
  gap: 16px;
}

.feature-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  border-color: #2563eb;
}

.feature-icon {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  background: white;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.15);
}

.feature-icon .el-icon {
  font-size: 24px;
}

.feature-info h4 {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 8px 0;
}

.feature-info p {
  font-size: 14px;
  color: #64748b;
  line-height: 1.5;
  margin: 0;
}

/* Specifications Content */
.spec-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.spec-table {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
}

/* Accessories Grid */
.accessories-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.accessory-item {
  background: #f8fafc;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e2e8f0;
  display: flex;
  gap: 16px;
  transition: all 0.3s ease;
}

.accessory-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.accessory-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  background: white;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.accessory-icon .el-icon {
  font-size: 20px;
  color: #2563eb;
}

.accessory-info h4 {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 4px 0;
}

.accessory-info p {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.optional-accessories {
  background: #f1f5f9;
  border-radius: 12px;
  padding: 20px;
}

.optional-list {
  list-style: none;
  padding: 0;
  margin: 8px 0 0 0;
}

.optional-list li {
  padding: 6px 0;
  color: #374151;
  font-size: 14px;
  position: relative;
  padding-left: 20px;
}

.optional-list li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: #2563eb;
  font-weight: bold;
}

/* Certificates Grid */
.certificates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.certificate-card {
  background: #f8fafc;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e2e8f0;
  display: flex;
  gap: 16px;
  transition: all 0.3s ease;
}

.certificate-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
}

.cert-icon {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  background: white;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.cert-icon .el-icon {
  font-size: 24px;
  color: #059669;
}

.cert-info h4 {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 8px 0;
}

.cert-info p {
  font-size: 14px;
  color: #64748b;
  margin: 0 0 4px 0;
}

.cert-number {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #2563eb !important;
  font-weight: 500;
}

.compliance-info {
  background: #f1f5f9;
  border-radius: 12px;
  padding: 20px;
}

.standards-list {
  list-style: none;
  padding: 0;
  margin: 8px 0 0 0;
}

.standards-list li {
  padding: 6px 0;
  color: #374151;
  font-size: 14px;
  position: relative;
  padding-left: 20px;
}

.standards-list li::before {
  content: '✓';
  position: absolute;
  left: 0;
  color: #059669;
  font-weight: bold;
}

/* Warranty Info */
.warranty-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.warranty-card {
  background: #f8fafc;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e2e8f0;
  display: flex;
  gap: 16px;
  transition: all 0.3s ease;
}

.warranty-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
}

.warranty-icon {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  background: white;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(5, 150, 105, 0.15);
}

.warranty-icon .el-icon {
  font-size: 24px;
}

.warranty-details h4 {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 8px 0;
}

.warranty-details p {
  font-size: 14px;
  color: #64748b;
  margin: 0 0 4px 0;
  line-height: 1.5;
}

/* Contact Grid */
.contact-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

/* Service Promise */
.service-promise {
  background: #f1f5f9;
  border-radius: 12px;
  padding: 20px;
}

.promise-list {
  list-style: none;
  padding: 0;
  margin: 8px 0 0 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 8px;
}

.promise-list li {
  padding: 6px 0;
  color: #374151;
  font-size: 14px;
}

/* Specifications Editor */
.specifications-editor {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.spec-edit-item {
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

/* Contact Item Styles */
.contact-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  transition: all 0.2s;
}

.contact-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.contact-item .el-icon {
  font-size: 24px;
  color: #059669;
}

.contact-details {
  flex: 1;
}

.contact-label {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.contact-value {
  font-size: 16px;
  color: #374151;
  font-weight: 600;
}

/* Responsive Design */
@media (max-width: 1024px) {
  .product-main {
    grid-template-columns: 1fr;
    gap: 32px;
    padding: 32px;
  }
  
  .main-image {
    height: 300px;
    max-width: 400px;
    margin: 0 auto;
  }
  
  .key-specs-grid {
    grid-template-columns: 1fr;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
  }
  
  .accessories-grid {
    grid-template-columns: 1fr;
  }
  
  .certificates-grid {
    grid-template-columns: 1fr;
  }
  
  .warranty-info {
    grid-template-columns: 1fr;
  }
  
  .nav-container {
    padding: 0 16px;
  }
  
  .nav-item {
    padding: 16px 16px;
    font-size: 14px;
  }
  
  .section-header h2 {
    font-size: 24px;
  }
  
  .content-section {
    padding: 32px 24px;
  }
}

@media (max-width: 768px) {
  .product-container {
    padding: 16px;
  }
  
  .breadcrumb-section {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .product-main {
    padding: 24px;
  }
  
  .product-title {
    font-size: 24px;
  }
  
  .contact-grid {
    grid-template-columns: 1fr;
  }
  
  .product-actions {
    flex-direction: column;
  }
  
  .product-actions .el-button {
    flex: none;
  }
  
  .nav-item {
    padding: 12px 12px;
    font-size: 13px;
  }
  
  .nav-item span {
    display: none;
  }
  
  .nav-item .el-icon {
    font-size: 20px;
  }
  
  .content-section {
    padding: 24px 16px;
  }
  
  .section-header h2 {
    font-size: 20px;
  }
  
  .section-content h3 {
    font-size: 18px;
  }
  
  .section-content h4 {
    font-size: 16px;
  }
  
  .scenario-list {
    grid-template-columns: 1fr;
  }
  
  .promise-list {
    grid-template-columns: 1fr;
  }
  
  .back-to-top {
    bottom: 20px;
    right: 20px;
    width: 44px;
    height: 44px;
    font-size: 18px;
  }
}

/* AI Source Notice */
.ai-source-notice {
  background: linear-gradient(135deg, #fef3c7 0%, #fed7aa 100%);
  border: 1px solid #f59e0b;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 32px;
  position: relative;
  overflow: hidden;
}

.ai-source-notice::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #f59e0b 0%, #d97706 100%);
}

.ai-notice-content {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.ai-icon {
  flex-shrink: 0;
  font-size: 24px;
  color: #d97706;
  margin-top: 2px;
}

.ai-text h4 {
  font-size: 16px;
  font-weight: 600;
  color: #92400e;
  margin: 0 0 8px 0;
}

.ai-text p {
  font-size: 14px;
  color: #a16207;
  margin: 0;
  line-height: 1.5;
}

/* Additional styling for new sections */
.no-data {
  color: #9ca3af;
  font-style: italic;
  text-align: center;
  padding: 20px 0;
}

.no-features-message,
.no-accessories,
.no-certificates,
.no-support {
  text-align: center;
  padding: 40px 20px;
}
</style>