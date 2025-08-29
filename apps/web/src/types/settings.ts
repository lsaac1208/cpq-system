import type { BaseEntity } from './common'

// Company Information Types
export interface CompanyInfo {
  name: string
  address?: string
  phone?: string
  email?: string
  website?: string
  logo_url?: string
  tax_number?: string
}

// System Configuration Types
export interface SystemConfig {
  default_currency: string
  default_tax_rate: number
  quote_validity_days: number
}

// PDF Settings Types
export interface PDFSettings {
  header_color: string
  footer_text?: string
  show_logo: boolean
}

// Email Settings Types
export interface EmailSettings {
  smtp_enabled: boolean
  smtp_host?: string
  smtp_port?: number
  smtp_username?: string
  smtp_password?: string
  smtp_use_tls: boolean
}

// Business Rules Types
export interface BusinessRules {
  auto_quote_numbering: boolean
  require_customer_approval: boolean
  max_discount_percentage: number
}

// Main Settings Interface
export interface SystemSettings extends BaseEntity {
  company_info: CompanyInfo
  system_config: SystemConfig
  pdf_settings: PDFSettings
  email_settings: EmailSettings
  business_rules: BusinessRules
}

// Request/Response Types
export interface UpdateSettingsRequest {
  company_info?: Partial<CompanyInfo>
  system_config?: Partial<SystemConfig>
  pdf_settings?: Partial<PDFSettings>
  email_settings?: Partial<EmailSettings>
  business_rules?: Partial<BusinessRules>
}

export interface UpdateCompanyInfoRequest {
  name: string
  address?: string
  phone?: string
  email?: string
  website?: string
  logo_url?: string
  tax_number?: string
}

export interface SettingsResponse {
  success: boolean
  data: SystemSettings
  message?: string
}

export interface CompanyInfoResponse {
  success: boolean
  data: CompanyInfo
  message?: string
}

// Form Types for UI Components
export interface CompanyInfoForm {
  name: string
  address: string
  phone: string
  email: string
  website: string
  logo_url: string
  tax_number: string
}

export interface SystemConfigForm {
  default_currency: string
  default_tax_rate: number
  quote_validity_days: number
}

export interface PDFSettingsForm {
  header_color: string
  footer_text: string
  show_logo: boolean
}

export interface EmailSettingsForm {
  smtp_enabled: boolean
  smtp_host: string
  smtp_port: number
  smtp_username: string
  smtp_password: string
  smtp_use_tls: boolean
}

export interface BusinessRulesForm {
  auto_quote_numbering: boolean
  require_customer_approval: boolean
  max_discount_percentage: number
}

// Validation Types
export interface SettingsValidationError {
  field: string
  message: string
}

export interface SettingsValidationErrors {
  company_info?: Record<string, string>
  system_config?: Record<string, string>
  pdf_settings?: Record<string, string>
  email_settings?: Record<string, string>
  business_rules?: Record<string, string>
}

// Settings Tab Types
export type SettingsTab = 
  | 'company'
  | 'system'
  | 'pdf'
  | 'email'
  | 'business'

// Settings Actions
export interface SettingsAction {
  type: string
  payload?: any
}

// Settings State for Store
export interface SettingsState {
  settings: SystemSettings | null
  loading: boolean
  error: string | null
  saving: boolean
  lastUpdated: Date | null
}

// Currency Options
export interface CurrencyOption {
  code: string
  name: string
  symbol: string
}

// Common Currency List
export const CURRENCY_OPTIONS: CurrencyOption[] = [
  { code: 'USD', name: 'US Dollar', symbol: '$' },
  { code: 'EUR', name: 'Euro', symbol: '€' },
  { code: 'GBP', name: 'British Pound', symbol: '£' },
  { code: 'JPY', name: 'Japanese Yen', symbol: '¥' },
  { code: 'CNY', name: 'Chinese Yuan', symbol: '¥' },
  { code: 'CAD', name: 'Canadian Dollar', symbol: 'C$' },
  { code: 'AUD', name: 'Australian Dollar', symbol: 'A$' },
]

// Default Values
export const DEFAULT_SETTINGS: Partial<SystemSettings> = {
  company_info: {
    name: 'Your Company Name',
    address: '',
    phone: '',
    email: '',
    website: '',
    logo_url: '',
    tax_number: ''
  },
  system_config: {
    default_currency: 'USD',
    default_tax_rate: 0,
    quote_validity_days: 30
  },
  pdf_settings: {
    header_color: '#2563eb',
    footer_text: '',
    show_logo: true
  },
  email_settings: {
    smtp_enabled: false,
    smtp_host: '',
    smtp_port: 587,
    smtp_username: '',
    smtp_password: '',
    smtp_use_tls: true
  },
  business_rules: {
    auto_quote_numbering: true,
    require_customer_approval: false,
    max_discount_percentage: 20
  }
}