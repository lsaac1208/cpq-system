// Common types used across the application

export interface BaseEntity {
  id: number
  created_at: string
  updated_at: string
}

export interface PaginationParams {
  page?: number
  per_page?: number
}

export interface PaginationResponse {
  page: number
  per_page: number
  total: number
  pages: number
}

export interface ApiResponse<T = any> {
  data?: T
  message?: string
  error?: string
  details?: any
}

export interface FilterParams {
  category?: string
  is_active?: boolean
  search?: string
}

// Form validation types
export interface FormRule {
  required?: boolean
  message?: string
  trigger?: 'blur' | 'change' | 'submit'
  min?: number
  max?: number
  pattern?: RegExp
  validator?: (rule: any, value: any, callback: Function) => void
}

export interface FormRules {
  [key: string]: FormRule | FormRule[]
}

// HTTP request types
export interface RequestConfig {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  headers?: Record<string, string>
  params?: Record<string, any>
  data?: any
  timeout?: number
}

// Component props types
export interface BaseComponentProps {
  id?: string
  class?: string | string[] | Record<string, boolean>
  style?: string | Record<string, any>
}

// Table column types
export interface TableColumn {
  prop?: string
  label: string
  width?: string | number
  minWidth?: string | number
  align?: 'left' | 'center' | 'right'
  sortable?: boolean | 'custom'
  fixed?: boolean | 'left' | 'right'
  type?: 'selection' | 'index' | 'expand'
  formatter?: (row: any, column: any, cellValue: any, index: number) => any
}

// Upload file types
export interface UploadFile {
  name: string
  size: number
  type: string
  url?: string
  status?: 'ready' | 'uploading' | 'success' | 'fail'
  progress?: number
}

// Error types
export interface ErrorDetail {
  field?: string
  message: string
  code?: string
}

export interface ValidationError {
  message: string
  errors: ErrorDetail[]
}

// Loading states
export type LoadingState = 'idle' | 'loading' | 'success' | 'error'

// Generic utility types
export type Optional<T, K extends keyof T> = Pick<Partial<T>, K> & Omit<T, K>
export type RequiredKeys<T> = {
  [K in keyof T]-?: {} extends Pick<T, K> ? never : K
}[keyof T]