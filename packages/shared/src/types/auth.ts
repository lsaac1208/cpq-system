import type { BaseEntity, UserRole } from './common'

export interface User extends BaseEntity {
  username: string
  email: string
  first_name: string
  last_name: string
  full_name: string
  role: UserRole
  is_active: boolean
}

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
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
}

export interface AuthResponse {
  message: string
  user: User
  tokens: AuthTokens
}

export interface RefreshTokenResponse {
  access_token: string
}