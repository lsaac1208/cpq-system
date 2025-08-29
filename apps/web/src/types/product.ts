import type { BaseEntity, PaginationResponse, FilterParams } from './common'

// Product Image related types
export interface ProductImage extends BaseEntity {
  product_id: number
  filename: string
  original_filename?: string
  image_url: string
  thumbnail_url?: string
  title?: string
  description?: string
  alt_text?: string
  file_size?: number
  width?: number
  height?: number
  format?: string
  sort_order: number
  is_primary: boolean
  is_active: boolean
  image_type: 'product' | 'detail' | 'usage' | 'comparison'
}

export interface GalleryStats {
  total_images: number
  total_size: number
  by_type: Record<string, number>
  has_primary: boolean
  primary_image_id?: number
}

export interface ImageUploadResult {
  filename: string
  success: boolean
  error?: string
  image?: ProductImage
}

// Extended product content types
export interface ProductFeature {
  id?: string
  icon?: string
  title: string
  description: string
  sort_order?: number
}

export interface ProductAccessory {
  id?: string
  name: string
  description: string
  type: 'standard' | 'optional'
  sort_order?: number
}

export interface ProductCertificate {
  id?: string
  name: string
  description: string
  certificate_number?: string
  type: string // e.g., 'quality', 'safety', 'compliance'
  sort_order?: number
}

export interface ProductWarranty {
  period: string // e.g., "3年"
  coverage: string
  terms: string[]
}

export interface ProductSupport {
  warranty: ProductWarranty
  contact_info: {
    sales_phone?: string
    sales_email?: string
    support_phone?: string
    support_email?: string
    service_wechat?: string
  }
  service_promises: string[]
}

export interface ApplicationScenario {
  id?: string
  name: string
  icon?: string
  sort_order?: number
}

// Product related types
export interface Product extends BaseEntity {
  name: string
  code: string
  description?: string
  category: string
  base_price: number
  image_url?: string
  configuration_schema?: Record<string, any>
  specifications?: Record<string, any>
  is_active: boolean
  is_configurable: boolean
  // 图片集相关字段
  gallery_images?: ProductImage[]
  primary_image?: ProductImage
  total_images?: number
  // Extended content fields
  detailed_description?: string
  application_scenarios?: ApplicationScenario[]
  features?: ProductFeature[]
  accessories?: ProductAccessory[]
  certificates?: ProductCertificate[]
  support_info?: ProductSupport
}

export interface CreateProductRequest {
  name: string
  code: string
  description?: string
  category: string
  base_price: number
  image_url?: string
  configuration_schema?: Record<string, any>
  specifications?: Record<string, any>
  is_active?: boolean
  is_configurable?: boolean
  // Extended content fields
  detailed_description?: string
  application_scenarios?: ApplicationScenario[]
  features?: ProductFeature[]
  accessories?: ProductAccessory[]
  certificates?: ProductCertificate[]
  support_info?: ProductSupport
}

export interface UpdateProductRequest {
  name?: string
  code?: string
  description?: string
  category?: string
  base_price?: number
  image_url?: string
  configuration_schema?: Record<string, any>
  specifications?: Record<string, any>
  is_active?: boolean
  is_configurable?: boolean
  // Extended content fields
  detailed_description?: string
  application_scenarios?: ApplicationScenario[]
  features?: ProductFeature[]
  accessories?: ProductAccessory[]
  certificates?: ProductCertificate[]
  support_info?: ProductSupport
}

export interface ProductListResponse {
  products: Product[]
  pagination: PaginationResponse
}

export interface ProductResponse {
  product: Product
  message?: string
}

export interface ProductFilterParams extends FilterParams {
  category?: string
  is_active?: boolean
  is_configurable?: boolean
  min_price?: number
  max_price?: number
}

export interface ProductFormData {
  name: string
  code: string
  description: string
  category: string
  base_price: number
  image_url: string
  specifications: Record<string, any>
  configuration_schema: Record<string, any>
  is_active: boolean
  is_configurable: boolean
  // Extended content fields
  detailed_description: string
  application_scenarios: ApplicationScenario[]
  features: ProductFeature[]
  accessories: ProductAccessory[]
  certificates: ProductCertificate[]
  support_info: ProductSupport
}

// Technical specifications structure
export interface TechnicalSpecification {
  name: string
  value: string | number | boolean
  unit?: string
  description?: string
}

// Configuration schema structure for dynamic product configuration
export interface ConfigurationField {
  name: string
  type: 'text' | 'number' | 'boolean' | 'select' | 'multiselect'
  label: string
  description?: string
  required: boolean
  default?: any
  options?: ConfigurationOption[]
  validation?: {
    min?: number
    max?: number
    pattern?: string
    message?: string
  }
}

export interface ConfigurationOption {
  value: string | number
  label: string
  price_modifier?: number
}

export interface ProductConfiguration {
  [fieldName: string]: any
}