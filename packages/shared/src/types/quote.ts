import type { BaseEntity, QuoteStatus, ListResponse } from './common'
import type { Product } from './product'
import type { User } from './auth'

export interface QuoteConfiguration {
  [key: string]: string | string[] | number | boolean
}

export interface Quote extends BaseEntity {
  quote_number: string
  customer_name: string
  customer_email: string
  customer_company?: string
  
  // Product and configuration
  product_id: number
  product?: Product
  configuration: QuoteConfiguration
  quantity: number
  
  // Pricing
  unit_price: number
  total_price: number
  discount_percentage: number
  discount_amount: number
  final_price: number
  
  // Status and validity
  status: QuoteStatus
  valid_until?: string
  
  // User relationships
  created_by?: number
  approved_by?: number
  creator?: User
  approver?: User
  
  // Additional information
  notes?: string
  terms_conditions?: string
}

export interface CreateQuoteRequest {
  customer_name: string
  customer_email: string
  customer_company?: string
  product_id: number
  configuration?: QuoteConfiguration
  quantity?: number
  discount_percentage?: number
  notes?: string
}

export interface UpdateQuoteRequest extends Partial<CreateQuoteRequest> {}

export interface UpdateQuoteStatusRequest {
  status: QuoteStatus
}

export interface QuoteListResponse extends ListResponse<Quote> {
  quotes: Quote[]
}