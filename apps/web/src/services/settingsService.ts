import cachedSettingsApi from '@/api/settings'
import type { CompanyInfo, SystemSettings } from '@/types/settings'

/**
 * Settings service for managing system settings and providing them to other services
 */
export class SettingsService {
  private static instance: SettingsService
  private settings: SystemSettings | null = null
  private lastFetch: Date | null = null
  private readonly CACHE_DURATION = 5 * 60 * 1000 // 5 minutes

  static getInstance(): SettingsService {
    if (!SettingsService.instance) {
      SettingsService.instance = new SettingsService()
    }
    return SettingsService.instance
  }

  /**
   * Get current system settings with caching
   */
  async getSettings(forceRefresh = false): Promise<SystemSettings> {
    const now = new Date()
    const shouldRefresh = forceRefresh || 
      !this.settings || 
      !this.lastFetch || 
      (now.getTime() - this.lastFetch.getTime()) > this.CACHE_DURATION

    if (shouldRefresh) {
      try {
        this.settings = await cachedSettingsApi.getSettings(forceRefresh)
        this.lastFetch = now
      } catch (error) {
        console.error('Failed to fetch settings:', error)
        // Return cached settings if available, otherwise throw
        if (!this.settings) {
          throw error
        }
      }
    }

    return this.settings!
  }

  /**
   * Get company information for PDF generation
   */
  async getCompanyInfoForPDF(): Promise<CompanyInfo> {
    try {
      const settings = await this.getSettings()
      return settings.company_info
    } catch (error) {
      console.error('Failed to get company info for PDF, using defaults:', error)
      // Return default company info if settings are not available
      return this.getDefaultCompanyInfo()
    }
  }

  /**
   * Get system configuration
   */
  async getSystemConfig() {
    const settings = await this.getSettings()
    return settings.system_config
  }

  /**
   * Get PDF settings
   */
  async getPDFSettings() {
    const settings = await this.getSettings()
    return settings.pdf_settings
  }

  /**
   * Get email settings
   */
  async getEmailSettings() {
    const settings = await this.getSettings()
    return settings.email_settings
  }

  /**
   * Get business rules
   */
  async getBusinessRules() {
    const settings = await this.getSettings()
    return settings.business_rules
  }

  /**
   * Clear cached settings
   */
  clearCache(): void {
    this.settings = null
    this.lastFetch = null
    cachedSettingsApi.clearCache()
  }

  /**
   * Update cached settings
   */
  updateCache(settings: SystemSettings): void {
    this.settings = settings
    this.lastFetch = new Date()
  }

  /**
   * Get default company info when settings are not available
   */
  private getDefaultCompanyInfo(): CompanyInfo {
    return {
      name: '您的公司名称',
      address: '请在系统设置中配置公司地址',
      phone: '+86 xxx-xxxx-xxxx',
      email: 'info@yourcompany.com',
      website: 'www.yourcompany.com',
      tax_number: '请配置税号'
    }
  }
}

// Export singleton instance
export const settingsService = SettingsService.getInstance()

// Export convenience functions
export const getCompanyInfoForPDF = () => settingsService.getCompanyInfoForPDF()
export const getSystemConfig = () => settingsService.getSystemConfig()
export const getPDFSettings = () => settingsService.getPDFSettings()
export const getEmailSettings = () => settingsService.getEmailSettings()
export const getBusinessRules = () => settingsService.getBusinessRules()
export const clearSettingsCache = () => settingsService.clearCache()

export default settingsService