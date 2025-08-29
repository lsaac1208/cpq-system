import http from './http'
import type {
  SystemSettings,
  CompanyInfo,
  UpdateSettingsRequest,
  UpdateCompanyInfoRequest,
  SettingsResponse,
  CompanyInfoResponse
} from '@/types/settings'

/**
 * Settings API client
 */
export const settingsApi = {
  /**
   * Get all system settings
   */
  async getSettings(): Promise<SystemSettings> {
    const response = await http.get<SettingsResponse>('/settings')
    return response.data.data
  },

  /**
   * Update system settings
   */
  async updateSettings(settings: UpdateSettingsRequest): Promise<SystemSettings> {
    const response = await http.put<SettingsResponse>('/settings', settings)
    return response.data.data
  },

  /**
   * Get company information only
   */
  async getCompanyInfo(): Promise<CompanyInfo> {
    const response = await http.get<CompanyInfoResponse>('/settings/company')
    return response.data.data
  },

  /**
   * Update company information only
   */
  async updateCompanyInfo(companyInfo: UpdateCompanyInfoRequest): Promise<CompanyInfo> {
    const response = await http.put<CompanyInfoResponse>('/settings/company', companyInfo)
    return response.data.data
  },

  /**
   * Test email settings
   */
  async testEmailSettings(): Promise<{ message: string }> {
    const response = await http.post<{ success: boolean; message: string }>('/settings/test-email')
    return { message: response.data.message }
  },

  /**
   * Reset settings to default values
   */
  async resetSettings(): Promise<SystemSettings> {
    const response = await http.post<SettingsResponse>('/settings/reset')
    return response.data.data
  }
}

/**
 * Settings cache for performance optimization
 */
class SettingsCache {
  private cache: SystemSettings | null = null
  private lastFetch: Date | null = null
  private readonly CACHE_DURATION = 5 * 60 * 1000 // 5 minutes

  async getSettings(forceRefresh = false): Promise<SystemSettings> {
    const now = new Date()
    const shouldRefresh = forceRefresh || 
      !this.cache || 
      !this.lastFetch || 
      (now.getTime() - this.lastFetch.getTime()) > this.CACHE_DURATION

    if (shouldRefresh) {
      this.cache = await settingsApi.getSettings()
      this.lastFetch = now
    }

    return this.cache!
  }

  updateCache(settings: SystemSettings): void {
    this.cache = settings
    this.lastFetch = new Date()
  }

  clearCache(): void {
    this.cache = null
    this.lastFetch = null
  }
}

export const settingsCache = new SettingsCache()

/**
 * Enhanced settings API with caching
 */
export const cachedSettingsApi = {
  /**
   * Get settings with caching
   */
  async getSettings(forceRefresh = false): Promise<SystemSettings> {
    return settingsCache.getSettings(forceRefresh)
  },

  /**
   * Update settings and update cache
   */
  async updateSettings(settings: UpdateSettingsRequest): Promise<SystemSettings> {
    const updatedSettings = await settingsApi.updateSettings(settings)
    settingsCache.updateCache(updatedSettings)
    return updatedSettings
  },

  /**
   * Get company info with caching
   */
  async getCompanyInfo(forceRefresh = false): Promise<CompanyInfo> {
    const settings = await this.getSettings(forceRefresh)
    return settings.company_info
  },

  /**
   * Update company info and update cache
   */
  async updateCompanyInfo(companyInfo: UpdateCompanyInfoRequest): Promise<CompanyInfo> {
    const updatedCompanyInfo = await settingsApi.updateCompanyInfo(companyInfo)
    
    // Update cached settings with new company info
    const currentSettings = await this.getSettings()
    const updatedSettings = {
      ...currentSettings,
      company_info: updatedCompanyInfo
    }
    settingsCache.updateCache(updatedSettings)
    
    return updatedCompanyInfo
  },

  /**
   * Reset settings and clear cache
   */
  async resetSettings(): Promise<SystemSettings> {
    const resetSettings = await settingsApi.resetSettings()
    settingsCache.updateCache(resetSettings)
    return resetSettings
  },

  /**
   * Test email settings
   */
  async testEmailSettings(): Promise<{ message: string }> {
    return settingsApi.testEmailSettings()
  },

  /**
   * Clear cache manually
   */
  clearCache(): void {
    settingsCache.clearCache()
  }
}

// Default export for convenience
export default cachedSettingsApi