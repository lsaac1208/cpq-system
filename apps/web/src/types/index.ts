// Re-export shared types
export * from '@/types/common'
export * from '@/types/auth'
export * from '@/types/product'
export * from '@/types/quote'
export * from '@/types/settings'
export * from '@/types/ai-analysis'
export * from '@/types/prompt-optimization'
export * from '@/types/document-comparison'
export * from '@/types/batch-analysis'

// Additional exports for backward compatibility
export type { 
  QuotePDFData,
  CompanyInfo,
  CustomerInfo,
  QuotePDFLineItem,
  QuoteTotals,
  QuoteSearchParams
} from '@/types/quote'

// Settings types for easy access
export type {
  SystemSettings,
  CompanyInfo as SettingsCompanyInfo,
  UpdateSettingsRequest,
  SettingsResponse,
  SettingsTab
} from '@/types/settings'