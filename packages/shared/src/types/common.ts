// Common types shared between frontend and backend

export interface BaseEntity {
  id: number
  created_at: string
  updated_at: string
}

export interface PaginationParams {
  page?: number
  per_page?: number
}

export interface PaginationInfo {
  page: number
  per_page: number
  total: number
  pages: number
}

export interface ApiResponse<T> {
  data?: T
  message?: string
  error?: string
  details?: any
}

export interface ListResponse<T> {
  items: T[]
  pagination: PaginationInfo
}

// Status types
export type Status = 'active' | 'inactive' | 'pending' | 'archived'

// Role types
export type UserRole = 'admin' | 'manager' | 'user'

// Quote status types
export type QuoteStatus = 'draft' | 'pending' | 'approved' | 'rejected' | 'expired'