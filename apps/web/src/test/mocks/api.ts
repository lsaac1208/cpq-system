/**
 * Mock API responses for testing
 */

import { vi } from 'vitest'
import type { User, LoginResponse, RegisterResponse } from '@/types/auth'
import type { Product } from '@/types/product'
import type { Quote } from '@/types/quote'

// Mock user data
export const mockUser: User = {
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  first_name: 'Test',
  last_name: 'User',
  role: 'user',
  full_name: 'Test User',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z'
}

export const mockAdminUser: User = {
  id: 2,
  username: 'admin',
  email: 'admin@example.com',
  first_name: 'Admin',
  last_name: 'User',
  role: 'admin',
  full_name: 'Admin User',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z'
}

// Mock product data
export const mockProduct: Product = {
  id: 1,
  name: 'Test Product',
  code: 'TEST-001',
  description: 'A test product for unit testing',
  category: 'Testing',
  base_price: 999.99,
  configuration_schema: {
    cpu: {
      type: 'select',
      options: ['Intel i5', 'Intel i7', 'AMD Ryzen 5'],
      default: 'Intel i5',
      price_modifier: [0, 200, 150]
    },
    memory: {
      type: 'select',
      options: ['8GB', '16GB', '32GB'],
      default: '8GB',
      price_modifier: [0, 300, 800]
    }
  },
  specifications: {
    weight: '2.5kg',
    dimensions: '35x25x2cm',
    warranty: '2 years'
  },
  is_active: true,
  is_configurable: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z'
}

export const mockProducts: Product[] = [
  mockProduct,
  {
    id: 2,
    name: 'Another Product',
    code: 'TEST-002',
    description: 'Another test product',
    category: 'Testing',
    base_price: 1299.99,
    configuration_schema: {},
    specifications: {},
    is_active: true,
    is_configurable: false,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  }
]

// Mock quote data
export const mockQuote: Quote = {
  id: 1,
  quote_number: 'Q-20240101120000-0001',
  customer_name: 'John Doe',
  customer_email: 'john.doe@example.com',
  customer_company: 'Acme Corp',
  product_id: 1,
  configuration: {
    cpu: 'Intel i7',
    memory: '16GB'
  },
  quantity: 2,
  unit_price: 1499.99,
  total_price: 2999.98,
  discount_percentage: 10.00,
  discount_amount: 299.998,
  final_price: 2699.98,
  status: 'draft',
  valid_until: '2024-02-01T00:00:00Z',
  created_by: 1,
  approved_by: null,
  notes: 'Test quote for integration testing',
  terms_conditions: 'Standard terms and conditions apply',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z'
}

// Mock API responses
export const mockLoginResponse: LoginResponse = {
  user: mockUser,
  tokens: {
    access_token: 'mock-access-token',
    refresh_token: 'mock-refresh-token'
  }
}

export const mockRegisterResponse: RegisterResponse = {
  user: mockUser,
  tokens: {
    access_token: 'mock-access-token',
    refresh_token: 'mock-refresh-token'
  }
}

// Mock API functions
export const mockAuthApi = {
  login: vi.fn().mockResolvedValue(mockLoginResponse),
  register: vi.fn().mockResolvedValue(mockRegisterResponse),
  getCurrentUser: vi.fn().mockResolvedValue({ user: mockUser }),
  refresh: vi.fn().mockResolvedValue({ access_token: 'new-mock-token' }),
  logout: vi.fn().mockResolvedValue({ message: 'Logged out successfully' })
}

export const mockProductsApi = {
  getProducts: vi.fn().mockResolvedValue({
    products: mockProducts,
    pagination: {
      page: 1,
      per_page: 20,
      total: mockProducts.length,
      pages: 1
    }
  }),
  getProduct: vi.fn().mockResolvedValue({ product: mockProduct }),
  createProduct: vi.fn().mockResolvedValue({ product: mockProduct }),
  updateProduct: vi.fn().mockResolvedValue({ product: mockProduct }),
  deleteProduct: vi.fn().mockResolvedValue({ message: 'Product deleted successfully' }),
  getCategories: vi.fn().mockResolvedValue({ categories: ['Testing', 'Hardware', 'Software'] })
}

export const mockQuotesApi = {
  getQuotes: vi.fn().mockResolvedValue({
    quotes: [mockQuote],
    pagination: {
      page: 1,
      per_page: 20,
      total: 1,
      pages: 1
    }
  }),
  getQuote: vi.fn().mockResolvedValue({ quote: mockQuote }),
  createQuote: vi.fn().mockResolvedValue({ quote: mockQuote }),
  updateQuote: vi.fn().mockResolvedValue({ quote: mockQuote }),
  deleteQuote: vi.fn().mockResolvedValue({ message: 'Quote deleted successfully' })
}

// Mock localStorage
export const mockLocalStorage = {
  getItem: vi.fn((key: string) => {
    const items = {
      'cpq_access_token': 'mock-access-token',
      'cpq_refresh_token': 'mock-refresh-token'
    }
    return items[key as keyof typeof items] || null
  }),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}

// Mock router
export const mockRouter = {
  push: vi.fn(),
  replace: vi.fn(),
  go: vi.fn(),
  back: vi.fn(),
  forward: vi.fn(),
  currentRoute: {
    value: {
      path: '/',
      query: {},
      params: {},
      name: 'home'
    }
  }
}

// Mock i18n
export const mockI18n = {
  t: vi.fn((key: string) => key),
  locale: { value: 'en' },
  availableLocales: ['en', 'zh'],
  setLocale: vi.fn()
}