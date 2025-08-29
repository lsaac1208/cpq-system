import type { BaseEntity, ListResponse } from './common'

// Configuration schema types
export interface ConfigurationOption {
  type: 'select' | 'multiselect' | 'text' | 'number' | 'boolean'
  label: string
  options?: string[]
  required?: boolean
  price_modifier?: Record<string, number>
  validation?: {
    min?: number
    max?: number
    pattern?: string
  }
}

export interface ConfigurationSchema {
  [key: string]: ConfigurationOption
}

export interface ProductSpecifications {
  [key: string]: string | number | boolean
}

export interface Product extends BaseEntity {
  name: string
  code: string
  description?: string
  category: string
  base_price: number
  configuration_schema: ConfigurationSchema
  specifications: ProductSpecifications
  is_active: boolean
  is_configurable: boolean
}

export interface CreateProductRequest {
  name: string
  code: string
  description?: string
  category: string
  base_price: number
  configuration_schema?: ConfigurationSchema
  specifications?: ProductSpecifications
  is_active?: boolean
  is_configurable?: boolean
}

export interface UpdateProductRequest extends Partial<CreateProductRequest> {}

export interface ProductListResponse extends ListResponse<Product> {
  products: Product[]
}