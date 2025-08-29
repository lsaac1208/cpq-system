import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { SettingsService } from '../settingsService'
import cachedSettingsApi from '@/api/settings'
import type { SystemSettings } from '@/types/settings'

// Mock the API
vi.mock('@/api/settings', () => ({
  default: {
    getSettings: vi.fn(),
    clearCache: vi.fn()
  }
}))

const mockSettings: SystemSettings = {
  id: 1,
  company_info: {
    name: 'Test Company',
    address: '123 Test St',
    phone: '+1-555-0123',
    email: 'test@company.com',
    website: 'https://testcompany.com',
    tax_number: 'TAX123'
  },
  system_config: {
    default_currency: 'USD',
    default_tax_rate: 8.5,
    quote_validity_days: 30
  },
  pdf_settings: {
    header_color: '#2563eb',
    footer_text: 'Thank you for your business',
    show_logo: true
  },
  email_settings: {
    smtp_enabled: false,
    smtp_host: '',
    smtp_port: 587,
    smtp_username: '',
    smtp_use_tls: true
  },
  business_rules: {
    auto_quote_numbering: true,
    require_customer_approval: false,
    max_discount_percentage: 20
  },
  created_at: '2024-01-01T00:00:00.000Z',
  updated_at: '2024-01-01T00:00:00.000Z'
}

describe('SettingsService', () => {
  let settingsService: SettingsService

  beforeEach(() => {
    settingsService = SettingsService.getInstance()
    // Clear any cached data
    settingsService.clearCache()
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('getInstance', () => {
    it('should return singleton instance', () => {
      const instance1 = SettingsService.getInstance()
      const instance2 = SettingsService.getInstance()
      
      expect(instance1).toBe(instance2)
    })
  })

  describe('getSettings', () => {
    it('should fetch settings from API on first call', async () => {
      const mockGetSettings = vi.mocked(cachedSettingsApi.getSettings)
      mockGetSettings.mockResolvedValue(mockSettings)

      const result = await settingsService.getSettings()

      expect(mockGetSettings).toHaveBeenCalledWith(false)
      expect(result).toEqual(mockSettings)
    })

    it('should return cached settings on subsequent calls', async () => {
      const mockGetSettings = vi.mocked(cachedSettingsApi.getSettings)
      mockGetSettings.mockResolvedValue(mockSettings)

      // First call
      await settingsService.getSettings()
      
      // Second call
      await settingsService.getSettings()

      // API should only be called once
      expect(mockGetSettings).toHaveBeenCalledTimes(1)
    })

    it('should force refresh when requested', async () => {
      const mockGetSettings = vi.mocked(cachedSettingsApi.getSettings)
      mockGetSettings.mockResolvedValue(mockSettings)

      // First call
      await settingsService.getSettings()
      
      // Force refresh
      await settingsService.getSettings(true)

      expect(mockGetSettings).toHaveBeenCalledTimes(2)
      expect(mockGetSettings).toHaveBeenLastCalledWith(true)
    })

    it('should handle API errors gracefully', async () => {
      const mockGetSettings = vi.mocked(cachedSettingsApi.getSettings)
      const error = new Error('API Error')
      mockGetSettings.mockRejectedValue(error)

      await expect(settingsService.getSettings()).rejects.toThrow('API Error')
    })

    it('should return cached settings when API fails but cache exists', async () => {
      const mockGetSettings = vi.mocked(cachedSettingsApi.getSettings)
      
      // First successful call
      mockGetSettings.mockResolvedValueOnce(mockSettings)
      await settingsService.getSettings()
      
      // Second call fails
      mockGetSettings.mockRejectedValueOnce(new Error('API Error'))
      const result = await settingsService.getSettings(true)
      
      // Should return cached settings
      expect(result).toEqual(mockSettings)
    })
  })

  describe('getCompanyInfoForPDF', () => {
    it('should return company info from settings', async () => {
      const mockGetSettings = vi.mocked(cachedSettingsApi.getSettings)
      mockGetSettings.mockResolvedValue(mockSettings)

      const result = await settingsService.getCompanyInfoForPDF()

      expect(result).toEqual(mockSettings.company_info)
    })

    it('should return default company info when API fails', async () => {
      const mockGetSettings = vi.mocked(cachedSettingsApi.getSettings)
      mockGetSettings.mockRejectedValue(new Error('API Error'))

      const result = await settingsService.getCompanyInfoForPDF()

      // Should return default values
      expect(result.name).toBe('您的公司名称')
      expect(result.address).toBe('请在系统设置中配置公司地址')
    })
  })

  describe('getSystemConfig', () => {
    it('should return system config from settings', async () => {
      const mockGetSettings = vi.mocked(cachedSettingsApi.getSettings)
      mockGetSettings.mockResolvedValue(mockSettings)

      const result = await settingsService.getSystemConfig()

      expect(result).toEqual(mockSettings.system_config)
    })
  })

  describe('getPDFSettings', () => {
    it('should return PDF settings from settings', async () => {
      const mockGetSettings = vi.mocked(cachedSettingsApi.getSettings)
      mockGetSettings.mockResolvedValue(mockSettings)

      const result = await settingsService.getPDFSettings()

      expect(result).toEqual(mockSettings.pdf_settings)
    })
  })

  describe('getEmailSettings', () => {
    it('should return email settings from settings', async () => {
      const mockGetSettings = vi.mocked(cachedSettingsApi.getSettings)
      mockGetSettings.mockResolvedValue(mockSettings)

      const result = await settingsService.getEmailSettings()

      expect(result).toEqual(mockSettings.email_settings)
    })
  })

  describe('getBusinessRules', () => {
    it('should return business rules from settings', async () => {
      const mockGetSettings = vi.mocked(cachedSettingsApi.getSettings)
      mockGetSettings.mockResolvedValue(mockSettings)

      const result = await settingsService.getBusinessRules()

      expect(result).toEqual(mockSettings.business_rules)
    })
  })

  describe('clearCache', () => {
    it('should clear internal cache and API cache', () => {
      const mockClearCache = vi.mocked(cachedSettingsApi.clearCache)
      
      settingsService.clearCache()

      expect(mockClearCache).toHaveBeenCalled()
    })
  })

  describe('updateCache', () => {
    it('should update cached settings', async () => {
      const mockGetSettings = vi.mocked(cachedSettingsApi.getSettings)
      
      // Update cache with new settings
      settingsService.updateCache(mockSettings)
      
      // Getting settings should not call API
      const result = await settingsService.getSettings()
      
      expect(mockGetSettings).not.toHaveBeenCalled()
      expect(result).toEqual(mockSettings)
    })
  })

  describe('cache expiration', () => {
    beforeEach(() => {
      // Mock Date.now to control time
      vi.useFakeTimers()
    })

    afterEach(() => {
      vi.useRealTimers()
    })

    it('should refresh cache after expiration', async () => {
      const mockGetSettings = vi.mocked(cachedSettingsApi.getSettings)
      mockGetSettings.mockResolvedValue(mockSettings)

      // First call
      await settingsService.getSettings()
      expect(mockGetSettings).toHaveBeenCalledTimes(1)

      // Advance time by 6 minutes (cache expires after 5 minutes)
      vi.advanceTimersByTime(6 * 60 * 1000)

      // Second call should refresh cache
      await settingsService.getSettings()
      expect(mockGetSettings).toHaveBeenCalledTimes(2)
    })

    it('should not refresh cache before expiration', async () => {
      const mockGetSettings = vi.mocked(cachedSettingsApi.getSettings)
      mockGetSettings.mockResolvedValue(mockSettings)

      // First call
      await settingsService.getSettings()
      expect(mockGetSettings).toHaveBeenCalledTimes(1)

      // Advance time by 4 minutes (cache still valid)
      vi.advanceTimersByTime(4 * 60 * 1000)

      // Second call should use cached data
      await settingsService.getSettings()
      expect(mockGetSettings).toHaveBeenCalledTimes(1)
    })
  })
})