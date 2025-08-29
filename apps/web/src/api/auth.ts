import http from './http'
import type { 
  LoginRequest, 
  RegisterRequest, 
  LoginResponse,
  RegisterResponse,
  User 
} from '@/types/auth'
import type { AxiosResponse } from 'axios'

export const authApi = {
  // Login - 返回完整的Axios响应对象
  login(data: LoginRequest): Promise<AxiosResponse<LoginResponse>> {
    return http.post('/auth/login', data)
  },

  // Register - 返回完整的Axios响应对象
  register(data: RegisterRequest): Promise<AxiosResponse<RegisterResponse>> {
    return http.post('/auth/register', data)
  },

  // Refresh token - 返回完整的Axios响应对象
  refresh(): Promise<AxiosResponse<{ access_token: string }>> {
    return http.post('/auth/refresh')
  },

  // Get current user - 返回完整的Axios响应对象
  getCurrentUser(): Promise<AxiosResponse<{ user: User }>> {
    return http.get('/auth/me')
  }
}