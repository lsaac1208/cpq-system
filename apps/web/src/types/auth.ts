// Authentication related types

export interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  full_name: string
  role: UserRole
  is_active: boolean
  created_at: string
  updated_at: string
}

export type UserRole = 'engineer' | 'sales' | 'manager' | 'admin'

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  first_name: string
  last_name: string
  role?: UserRole
}

// 后端API响应的data部分结构 (在axios response.data中)
export interface LoginResponseData {
  success: boolean
  message: string
  timestamp: string
  data: {
    user: User
    tokens: {
      access_token: string
      refresh_token: string
    }
  }
}

export interface RegisterResponseData {
  success: boolean
  message: string
  timestamp: string
  data: {
    user: User
    tokens: {
      access_token: string
      refresh_token: string
    }
  }
}

// 向后兼容的别名
export type LoginResponse = LoginResponseData
export type RegisterResponse = RegisterResponseData

export interface RefreshTokenResponse {
  access_token: string
}

export interface CurrentUserResponse {
  user: User
}

// Alias for compatibility
export type AuthResponse = LoginResponse