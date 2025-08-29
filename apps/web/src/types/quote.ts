import type { BaseEntity, PaginationResponse } from './common'
import type { Product, ProductConfiguration } from './product'
import type { User } from './auth'

// Quote related types
export interface Quote extends BaseEntity {
  quote_number: string
  customer_name: string
  customer_email: string
  customer_company?: string
  customer_phone?: string
  customer_address?: string
  
  // Multi-product support
  items?: QuoteItem[]
  
  // Legacy single product support (for backward compatibility)
  product_id?: number
  product?: Product
  configuration?: ProductConfiguration
  base_price?: number
  
  // Quote totals
  subtotal: number
  discount_amount?: number
  discount_percentage?: number
  tax_amount?: number
  total_price: number
  
  status: QuoteStatus
  valid_until: string
  notes?: string
  terms_conditions?: string
  
  // Metadata
  created_by: number
  created_by_user?: User
  version: number
  expires_at?: string
}

// Quote item for multi-product quotes
export interface QuoteItem extends BaseEntity {
  quote_id: number
  product_id: number
  product?: Product
  quantity: number
  unit_price: number
  line_total: number
  discount_percentage?: number
  discount_amount?: number
  configuration?: ProductConfiguration
  notes?: string
  sort_order: number
}

export type QuoteStatus = 'draft' | 'pending' | 'approved' | 'rejected' | 'expired'

export interface CreateQuoteRequest {
  customer_name: string
  customer_email: string
  customer_company?: string
  customer_phone?: string
  customer_address?: string
  
  // Multi-product support
  items: CreateQuoteItemRequest[]
  
  // Legacy single product support (for backward compatibility)
  product_id?: number
  configuration?: ProductConfiguration
  
  discount_percentage?: number
  tax_percentage?: number
  notes?: string
  terms_conditions?: string
  valid_until?: string
}

export interface CreateQuoteItemRequest {
  product_id: number
  quantity: number
  unit_price?: number // Optional, will use product base price if not provided
  discount_percentage?: number
  configuration?: ProductConfiguration
  notes?: string
}

export interface UpdateQuoteRequest {
  customer_name?: string
  customer_email?: string
  customer_company?: string
  customer_phone?: string
  customer_address?: string
  
  items?: UpdateQuoteItemRequest[]
  
  // Legacy support
  configuration?: ProductConfiguration
  
  discount_percentage?: number
  tax_percentage?: number
  status?: QuoteStatus
  notes?: string
  terms_conditions?: string
  valid_until?: string
}

export interface UpdateQuoteItemRequest {
  id?: number // Existing item ID for updates
  product_id: number
  quantity: number
  unit_price: number
  discount_percentage?: number
  configuration?: ProductConfiguration
  notes?: string
  sort_order?: number
}

export interface UpdateQuoteStatusRequest {
  status: QuoteStatus
}

export interface QuoteListResponse {
  quotes: Quote[]
  pagination: PaginationResponse
}

export interface QuoteResponse {
  quote: Quote
  message?: string
}

export interface QuoteFilterParams {
  status?: QuoteStatus
  customer_name?: string
  product_id?: number
  created_by?: number
  date_from?: string
  date_to?: string
  page?: number
  per_page?: number
}

export interface QuoteCalculation {
  base_price: number
  configuration_adjustments: number
  subtotal: number
  discount_amount: number
  total_price: number
  breakdown: QuoteLineItem[]
}

export interface QuoteLineItem {
  name: string
  description?: string
  quantity: number
  unit_price: number
  total_price: number
}

// PDF Export related types
export interface QuotePDFData {
  quote: Quote
  company_info: CompanyInfo
  customer_info: CustomerInfo
  line_items: QuotePDFLineItem[]
  totals: QuoteTotals
}

export interface CompanyInfo {
  name: string
  logo_url?: string
  address: string
  phone?: string
  email?: string
  website?: string
  tax_number?: string
}

export interface CustomerInfo {
  name: string
  company?: string
  email: string
  phone?: string
  address?: string
}

export interface QuotePDFLineItem {
  product_code: string
  product_name: string
  description?: string
  quantity: number
  unit_price: number
  discount_percentage?: number
  discount_amount?: number
  line_total: number
  specifications?: Record<string, any>
}

export interface QuoteTotals {
  subtotal: number
  discount_amount: number
  tax_amount: number
  total: number
  discount_percentage?: number
  tax_percentage?: number
}

// Quote search and filter types
export interface QuoteSearchParams {
  search?: string
  customer_name?: string
  quote_number?: string
  status?: QuoteStatus | string  // Allow empty string for "all statuses"
  date_from?: string
  date_to?: string
  min_amount?: number | null
  max_amount?: number | null
  created_by?: number | null
  page?: number
  per_page?: number
  sort_by?: 'created_at' | 'total_price' | 'customer_name' | 'quote_number'
  sort_order?: 'asc' | 'desc'
}