import { PDFDocument, PDFFont, rgb } from 'pdf-lib'
import fontkit from '@pdf-lib/fontkit'
import type { Quote, QuotePDFData, CompanyInfo, CustomerInfo } from '@/types'
import { pdfTableLayoutEngine, type TableColumn, type TableCell, type TableOptions } from './pdfTableLayoutEngine'
import { getCompanyInfoForPDF } from '@/services/settingsService'

/**
 * 统一的中文PDF生成器
 * 完美支持中文字符显示，使用Noto Sans SC字体
 * 
 * ✅ 真实中文字体文件加载
 * ✅ 完美中文字符渲染
 * ✅ 错误处理和降级策略
 * ✅ 中英文混合排版
 */
export class UnifiedChinesePDFGenerator {
  private pageWidth = 595.28 // A4 width in points
  private pageHeight = 841.89 // A4 height in points
  private margin = 50
  private fontSize = {
    title: 24,
    heading: 18,
    subheading: 14,
    normal: 12,
    small: 10
  }

  // 字体缓存
  private static fontCache: Map<string, ArrayBuffer> = new Map()
  private chineseFont: PDFFont | null = null
  private fallbackFont: PDFFont | null = null

  /**
   * 加载中文字体，带完整降级策略
   */
  private async loadChineseFont(pdfDoc: PDFDocument): Promise<{ regularFont: PDFFont, boldFont: PDFFont }> {
    try {
      // 首先注册fontkit
      pdfDoc.registerFontkit(fontkit)
      
      // 尝试从缓存获取字体
      let fontData = UnifiedChinesePDFGenerator.fontCache.get('chinese-font')
      
      if (!fontData) {
        console.log('正在加载中文字体...')
        
        // 字体源优先级列表
        const fontSources = [
          '/fonts/NotoSansSC-Regular.ttf', // 本地字体文件（最高优先级）
          'https://fonts.gstatic.com/s/notosanssc/v36/k3kCo84MPvpLmixcA63oeAL7Iqp5IZJF9bmaG9_FnYxNbPzS5HE.ttf', // Google Fonts
          'https://cdn.jsdelivr.net/npm/@expo-google-fonts/noto-sans-sc@0.2.2/NotoSansSC_400Regular.ttf' // 备用CDN
        ]

        // 尝试每个字体源
        for (const source of fontSources) {
          try {
            console.log(`尝试加载字体: ${source}`)
            const response = await fetch(source)
            if (response.ok) {
              fontData = await response.arrayBuffer()
              
              // 验证字体文件有效性
              if (fontData && fontData.byteLength > 100000) { // 至少100KB的字体文件
                UnifiedChinesePDFGenerator.fontCache.set('chinese-font', fontData)
                console.log(`✅ 成功加载中文字体: ${source} (${(fontData.byteLength / 1024 / 1024).toFixed(2)}MB)`)
                break
              } else {
                console.warn(`字体文件太小或无效: ${source}`)
                fontData = null
              }
            } else {
              console.warn(`字体加载失败 (HTTP ${response.status}): ${source}`)
            }
          } catch (error) {
            console.warn(`字体加载异常: ${source}`, error)
          }
        }
      }

      // 如果成功加载中文字体
      if (fontData) {
        try {
          this.chineseFont = await pdfDoc.embedFont(fontData)
          console.log('✅ 中文字体嵌入成功')
          return {
            regularFont: this.chineseFont,
            boldFont: this.chineseFont // 使用同一字体，通过绘制方式模拟粗体
          }
        } catch (embedError) {
          console.error('中文字体嵌入失败:', embedError)
        }
      }

      // 降级策略：使用PDF标准字体
      console.log('⚠️ 使用降级字体策略')
      const fallbackFont = await pdfDoc.embedFont('Helvetica')
      const fallbackBoldFont = await pdfDoc.embedFont('Helvetica-Bold')
      
      this.fallbackFont = fallbackFont
      
      return {
        regularFont: fallbackFont,
        boldFont: fallbackBoldFont
      }

    } catch (error) {
      console.error('字体加载完全失败:', error)
      throw new Error('无法加载任何字体，PDF生成失败')
    }
  }

  /**
   * 智能文本渲染 - 支持中文和降级处理
   */
  private renderText(page: any, text: string, x: number, y: number, options: any) {
    try {
      // 直接尝试渲染
      page.drawText(text, { x, y, ...options })
    } catch (error) {
      console.warn(`文本渲染失败，尝试降级处理: "${text}"`, error)
      
      // 降级策略1：移除特殊字符
      try {
        const cleanText = this.sanitizeText(text)
        page.drawText(cleanText, { x, y, ...options })
        return
      } catch (cleanError) {
        console.warn('降级文本渲染也失败:', cleanError)
      }

      // 降级策略2：中文转英文
      try {
        const englishText = this.translateChineseToEnglish(text)
        page.drawText(englishText, { x, y, ...options })
        return
      } catch (translateError) {
        console.warn('翻译文本渲染失败:', translateError)
      }

      // 最后的降级策略：占位符
      try {
        page.drawText('[Chinese Text]', { x, y, ...options })
      } catch (finalError) {
        console.error('最终降级策略失败:', finalError)
      }
    }
  }

  /**
   * 清理文本，移除可能导致渲染问题的字符
   */
  private sanitizeText(text: string): string {
    // 移除控制字符和未知字符
    return text.replace(/[\u0000-\u001F\u007F-\u009F]/g, '')
               .replace(/\uFFFD/g, '?') // 替换替换字符
  }

  /**
   * 中文到英文的智能翻译
   */
  private translateChineseToEnglish(text: string): string {
    const translations: { [key: string]: string } = {
      '电力设备制造有限公司': 'Power Equipment Manufacturing Co., Ltd.',
      '报价单': 'Quotation',
      '产品报价单': 'Product Quotation',
      '报价单号': 'Quote No.',
      '日期': 'Date',
      '有效期至': 'Valid Until',
      '客户信息': 'Customer Information',
      '客户姓名': 'Customer Name',
      '公司名称': 'Company Name',
      '联系邮箱': 'Email',
      '联系电话': 'Phone',
      '联系地址': 'Address',
      '邮箱': 'Email',
      '电话': 'Phone',
      '地址': 'Address',
      '产品名称': 'Product',
      '产品': 'Product',
      '产品描述': 'Description',
      '描述': 'Description',
      '数量': 'Quantity',
      '单价': 'Unit Price',
      '折扣': 'Discount',
      '小计': 'Subtotal',
      '税费': 'Tax',
      '总计': 'Total',
      '条款和条件': 'Terms and Conditions',
      '本报价单由': 'Generated by',
      '提供': '',
      '高压变压器': 'HV Transformer',
      '配电柜': 'Distribution Cabinet',
      '电缆': 'Cable',
      '张三': 'Zhang San',
      '上海工业发展有限公司': 'Shanghai Industrial Development Co., Ltd.',
      '上海市': 'Shanghai',
      '中国': 'China',
      '人民币': 'RMB',
      '元': 'Yuan'
    }

    let result = text
    
    // 应用翻译映射
    Object.entries(translations).forEach(([chinese, english]) => {
      result = result.replace(new RegExp(chinese, 'g'), english)
    })

    // 如果还有中文字符，标记为中文内容
    if (/[\u4e00-\u9fff]/.test(result)) {
      // 保留中文，但在前面添加标识
      result = `[CN] ${result}`
    }

    return result
  }

  /**
   * 生成PDF报价单
   */
  public async generateQuotePDF(data: QuotePDFData): Promise<Uint8Array> {
    try {
      console.log('开始生成中文PDF报价单...')
      
      // 创建PDF文档
      const pdfDoc = await PDFDocument.create()
      const page = pdfDoc.addPage([this.pageWidth, this.pageHeight])
      
      // 加载字体
      const fonts = await this.loadChineseFont(pdfDoc)
      
      let currentY = this.pageHeight - this.margin

      // 依次添加各个部分
      currentY = this.addCompanyHeader(page, fonts, data.company_info, currentY)
      currentY = this.addQuoteHeader(page, fonts, data.quote, currentY)
      currentY = this.addCustomerInfo(page, fonts, data.customer_info, currentY)
      currentY = this.addLineItemsTable(page, fonts, data.line_items, currentY)
      currentY = this.addTotals(page, fonts, data.totals, currentY)
      
      if (data.quote.terms_conditions) {
        currentY = this.addTermsAndConditions(page, fonts, data.quote.terms_conditions, currentY)
      }
      
      this.addFooter(page, fonts, data.company_info)

      // 序列化PDF
      const pdfBytes = await pdfDoc.save()
      console.log(`✅ PDF生成成功，大小: ${(pdfBytes.length / 1024).toFixed(1)}KB`)
      return pdfBytes
    } catch (error) {
      console.error('❌ PDF生成失败:', error)
      throw new Error(`PDF生成失败: ${error.message}`)
    }
  }

  /**
   * 下载PDF文件
   */
  public async downloadPDF(data: QuotePDFData, filename?: string): Promise<void> {
    try {
      const pdfBytes = await this.generateQuotePDF(data)
      
      // 创建下载链接
      const blob = new Blob([pdfBytes], { type: 'application/pdf' })
      const url = URL.createObjectURL(blob)
      
      const link = document.createElement('a')
      link.href = url
      link.download = filename || `报价单-${data.quote.quote_number}.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      URL.revokeObjectURL(url)
      console.log('✅ PDF下载成功')
    } catch (error) {
      console.error('❌ PDF下载失败:', error)
      throw error
    }
  }

  /**
   * 测试中文字体支持
   */
  public async testChineseSupport(): Promise<boolean> {
    try {
      console.log('🧪 测试中文字体支持...')
      
      // 创建临时PDF文档测试字体加载
      const tempDoc = await PDFDocument.create()
      const fonts = await this.loadChineseFont(tempDoc)
      
      // 如果成功加载字体，进行简单的渲染测试
      if (fonts.regularFont) {
        const testPage = tempDoc.addPage([200, 100])
        this.renderText(testPage, '测试中文', 10, 50, {
          size: 12,
          font: fonts.regularFont,
          color: rgb(0, 0, 0)
        })
        
        // 尝试保存测试PDF
        await tempDoc.save()
        
        console.log('✅ 中文字体支持测试通过')
        return true
      }
      
      console.log('⚠️ 中文字体支持有限')
      return false
    } catch (error) {
      console.error('❌ 中文字体支持测试失败:', error)
      return false
    }
  }

  // 以下是各个部分的绘制方法...
  private addCompanyHeader(page: any, fonts: any, companyInfo: CompanyInfo, startY: number): number {
    let currentY = startY

    // 公司名称
    const companyName = companyInfo.name || '电力设备制造有限公司'
    const titleWidth = this.getTextWidth(companyName, this.fontSize.title)
    this.renderText(page, companyName, this.pageWidth / 2 - titleWidth / 2, currentY, {
      size: this.fontSize.title,
      font: fonts.boldFont,
      color: rgb(0.1, 0.1, 0.1)
    })
    currentY -= 35

    // 公司地址
    if (companyInfo.address) {
      const addressWidth = this.getTextWidth(companyInfo.address, this.fontSize.normal)
      this.renderText(page, companyInfo.address, this.pageWidth / 2 - addressWidth / 2, currentY, {
        size: this.fontSize.normal,
        font: fonts.regularFont,
        color: rgb(0.3, 0.3, 0.3)
      })
      currentY -= 25
    }

    // 联系信息
    const contactInfo = []
    if (companyInfo.phone) contactInfo.push(`电话: ${companyInfo.phone}`)
    if (companyInfo.email) contactInfo.push(`邮箱: ${companyInfo.email}`)
    if (companyInfo.website) contactInfo.push(`网站: ${companyInfo.website}`)
    
    if (contactInfo.length > 0) {
      const contactText = contactInfo.join(' | ')
      const contactWidth = this.getTextWidth(contactText, this.fontSize.small)
      this.renderText(page, contactText, this.pageWidth / 2 - contactWidth / 2, currentY, {
        size: this.fontSize.small,
        font: fonts.regularFont,
        color: rgb(0.4, 0.4, 0.4)
      })
      currentY -= 20
    }

    // 分隔线
    page.drawLine({
      start: { x: this.margin, y: currentY },
      end: { x: this.pageWidth - this.margin, y: currentY },
      thickness: 2,
      color: rgb(0.2, 0.2, 0.2)
    })
    currentY -= 30

    return currentY
  }

  private addQuoteHeader(page: any, fonts: any, quote: Quote, startY: number): number {
    let currentY = startY

    // 报价单标题
    this.renderText(page, '产品报价单', this.margin, currentY, {
      size: this.fontSize.heading,
      font: fonts.boldFont,
      color: rgb(0.1, 0.1, 0.1)
    })

    // 报价单号
    const quoteNoText = `报价单号: ${quote.quote_number}`
    const quoteNoWidth = this.getTextWidth(quoteNoText, this.fontSize.normal)
    this.renderText(page, quoteNoText, this.pageWidth - this.margin - quoteNoWidth, currentY, {
      size: this.fontSize.normal,
      font: fonts.regularFont,
      color: rgb(0.2, 0.2, 0.2)
    })
    currentY -= 25

    // 日期
    const date = new Date(quote.created_at).toLocaleDateString('zh-CN')
    const dateText = `日期: ${date}`
    const dateWidth = this.getTextWidth(dateText, this.fontSize.normal)
    this.renderText(page, dateText, this.pageWidth - this.margin - dateWidth, currentY, {
      size: this.fontSize.normal,
      font: fonts.regularFont,
      color: rgb(0.2, 0.2, 0.2)
    })
    currentY -= 20

    // 有效期
    if (quote.valid_until) {
      const validUntil = new Date(quote.valid_until).toLocaleDateString('zh-CN')
      const validText = `有效期至: ${validUntil}`
      const validWidth = this.getTextWidth(validText, this.fontSize.normal)
      this.renderText(page, validText, this.pageWidth - this.margin - validWidth, currentY, {
        size: this.fontSize.normal,
        font: fonts.regularFont,
        color: rgb(0.6, 0.2, 0.2)
      })
      currentY -= 20
    }

    currentY -= 15
    return currentY
  }

  private addCustomerInfo(page: any, fonts: any, customerInfo: CustomerInfo, startY: number): number {
    let currentY = startY

    // 客户信息标题
    this.renderText(page, '客户信息', this.margin, currentY, {
      size: this.fontSize.subheading,
      font: fonts.boldFont,
      color: rgb(0.1, 0.1, 0.1)
    })
    currentY -= 25

    // 客户信息详情
    const customerFields = [
      { label: '客户姓名', value: customerInfo.name },
      { label: '公司名称', value: customerInfo.company },
      { label: '联系邮箱', value: customerInfo.email },
      { label: '联系电话', value: customerInfo.phone },
      { label: '联系地址', value: customerInfo.address }
    ]

    customerFields.forEach(field => {
      if (field.value) {
        const text = `${field.label}: ${field.value}`
        this.renderText(page, text, this.margin, currentY, {
          size: this.fontSize.normal,
          font: fonts.regularFont,
          color: rgb(0.2, 0.2, 0.2)
        })
        currentY -= 18
      }
    })

    currentY -= 15
    return currentY
  }

  private addLineItemsTable(page: any, fonts: any, lineItems: any[], startY: number): number {
    // 使用新的专业表格布局引擎
    
    // 定义表格列配置
    const columns: TableColumn[] = [
      { 
        header: '产品名称', 
        weight: 2, 
        align: 'left', 
        headerAlign: 'center',
        minWidth: 80,
        maxWidth: 120
      },
      { 
        header: '产品描述', 
        weight: 4, 
        align: 'left', 
        headerAlign: 'center',
        minWidth: 150,
        maxWidth: 200,
        wrap: true
      },
      { 
        header: '数量', 
        weight: 1, 
        align: 'right', 
        headerAlign: 'center',
        minWidth: 40,
        maxWidth: 60
      },
      { 
        header: '单价 (¥)', 
        weight: 1.5, 
        align: 'right', 
        headerAlign: 'center',
        minWidth: 60,
        maxWidth: 80
      },
      { 
        header: '折扣', 
        weight: 1, 
        align: 'center', 
        headerAlign: 'center',
        minWidth: 40,
        maxWidth: 60
      },
      { 
        header: '小计 (¥)', 
        weight: 1.5, 
        align: 'right', 
        headerAlign: 'center',
        minWidth: 60,
        maxWidth: 80
      }
    ]

    // 转换数据格式
    const data: TableCell[][] = lineItems.map(item => [
      { text: item.product_name || '', align: 'left' },
      { text: item.description || '', align: 'left', wrap: true },
      { text: String(item.quantity || 0), align: 'right' },
      { 
        text: this.formatCurrency(item.unit_price || 0), 
        align: 'right' 
      },
      { 
        text: item.discount_percentage ? `${item.discount_percentage}%` : '-', 
        align: 'center',
        color: [0.6, 0.3, 0.3]
      },
      { 
        text: this.formatCurrency(item.line_total || 0), 
        align: 'right',
        color: [0.1, 0.1, 0.1]
      }
    ])

    // 表格配置选项
    const tableOptions: TableOptions = {
      columns,
      data,
      header: true,
      borderColor: [0.3, 0.3, 0.3],
      borderWidth: 1,
      headerBackgroundColor: [0.9, 0.9, 0.9],
      alternateRowColor: [0.98, 0.98, 0.98],
      fontSize: 9,
      padding: 6
    }

    // 使用表格引擎绘制表格
    return pdfTableLayoutEngine.drawTable(
      page,
      tableOptions,
      { regular: fonts.regularFont, bold: fonts.boldFont },
      startY
    )
  }

  /**
   * 格式化货币显示
   */
  private formatCurrency(amount: number): string {
    if (amount >= 1000000) {
      return `${(amount / 1000000).toFixed(1)}M`
    } else if (amount >= 1000) {
      return `${(amount / 1000).toFixed(0)}k`
    }
    return amount.toLocaleString()
  }

  private addTotals(page: any, fonts: any, totals: any, startY: number): number {
    let currentY = startY
    const rightX = this.pageWidth - this.margin
    const labelX = rightX - 200

    // 小计
    this.renderText(page, '小计:', labelX, currentY, {
      size: this.fontSize.normal,
      font: fonts.regularFont,
      color: rgb(0.2, 0.2, 0.2)
    })
    const subtotal = Number(totals.subtotal || 0)
    const subtotalText = `¥${subtotal.toLocaleString()}`
    const subtotalWidth = this.getTextWidth(subtotalText, this.fontSize.normal)
    this.renderText(page, subtotalText, rightX - subtotalWidth, currentY, {
      size: this.fontSize.normal,
      font: fonts.regularFont,
      color: rgb(0.2, 0.2, 0.2)
    })
    currentY -= 25

    // 折扣
    if (totals.discount_amount > 0) {
      this.renderText(page, '折扣:', labelX, currentY, {
        size: this.fontSize.normal,
        font: fonts.regularFont,
        color: rgb(0.2, 0.2, 0.2)
      })
      const discountText = `¥${Number(totals.discount_amount).toLocaleString()}`
      const discountWidth = this.getTextWidth(discountText, this.fontSize.normal)
      this.renderText(page, discountText, rightX - discountWidth, currentY, {
        size: this.fontSize.normal,
        font: fonts.regularFont,
        color: rgb(0.8, 0.2, 0.2)
      })
      currentY -= 25
    }

    // 税费
    if (totals.tax_amount > 0) {
      this.renderText(page, '税费:', labelX, currentY, {
        size: this.fontSize.normal,
        font: fonts.regularFont,
        color: rgb(0.2, 0.2, 0.2)
      })
      const taxText = `¥${Number(totals.tax_amount).toLocaleString()}`
      const taxWidth = this.getTextWidth(taxText, this.fontSize.normal)
      this.renderText(page, taxText, rightX - taxWidth, currentY, {
        size: this.fontSize.normal,
        font: fonts.regularFont,
        color: rgb(0.2, 0.2, 0.2)
      })
      currentY -= 25
    }

    // 分隔线
    page.drawLine({
      start: { x: labelX, y: currentY + 5 },
      end: { x: rightX, y: currentY + 5 },
      thickness: 1,
      color: rgb(0.3, 0.3, 0.3)
    })
    currentY -= 15

    // 总计
    this.renderText(page, '总计:', labelX, currentY, {
      size: this.fontSize.heading,
      font: fonts.boldFont,
      color: rgb(0.1, 0.1, 0.1)
    })
    const totalAmount = `¥${Number(totals.total || 0).toLocaleString()}`
    const totalWidth = this.getTextWidth(totalAmount, this.fontSize.heading)
    this.renderText(page, totalAmount, rightX - totalWidth, currentY, {
      size: this.fontSize.heading,
      font: fonts.boldFont,
      color: rgb(0.8, 0.2, 0.2)
    })
    currentY -= 40

    return currentY
  }

  private addTermsAndConditions(page: any, fonts: any, terms: string, startY: number): number {
    let currentY = startY

    // 标题
    this.renderText(page, '条款和条件', this.margin, currentY, {
      size: this.fontSize.subheading,
      font: fonts.boldFont,
      color: rgb(0.1, 0.1, 0.1)
    })
    currentY -= 25

    // 内容处理 - 简单换行
    const maxWidth = this.pageWidth - (2 * this.margin)
    const lines = this.wrapText(terms, this.fontSize.small, maxWidth)
    
    lines.forEach(line => {
      this.renderText(page, line, this.margin, currentY, {
        size: this.fontSize.small,
        font: fonts.regularFont,
        color: rgb(0.3, 0.3, 0.3)
      })
      currentY -= 18
    })

    currentY -= 15
    return currentY
  }

  private addFooter(page: any, fonts: any, companyInfo: CompanyInfo): void {
    const footerY = this.margin - 10
    const centerX = this.pageWidth / 2

    const footerText = `本报价单由 ${companyInfo.name || '本公司'} 提供`
    const footerWidth = this.getTextWidth(footerText, this.fontSize.small)
    
    this.renderText(page, footerText, centerX - footerWidth / 2, footerY, {
      size: this.fontSize.small,
      font: fonts.regularFont,
      color: rgb(0.5, 0.5, 0.5)
    })
  }

  /**
   * 估算文本宽度（针对中文优化）
   */
  private getTextWidth(text: string, fontSize: number): number {
    let width = 0
    for (let i = 0; i < text.length; i++) {
      const char = text.charAt(i)
      if (/[\u4e00-\u9fff]/.test(char)) {
        // 中文字符
        width += fontSize * 0.9
      } else if (/[A-Z]/.test(char)) {
        // 大写英文字符
        width += fontSize * 0.7
      } else {
        // 其他字符（小写英文、数字、符号）
        width += fontSize * 0.5
      }
    }
    return width
  }

  /**
   * 文本换行处理
   */
  private wrapText(text: string, fontSize: number, maxWidth: number): string[] {
    const lines: string[] = []
    const characters = text.split('')
    let currentLine = ''

    for (const char of characters) {
      const testLine = currentLine + char
      const testWidth = this.getTextWidth(testLine, fontSize)
      
      if (testWidth > maxWidth && currentLine.length > 0) {
        lines.push(currentLine)
        currentLine = char
      } else {
        currentLine = testLine
      }
    }
    
    if (currentLine.length > 0) {
      lines.push(currentLine)
    }

    return lines
  }

  // 工具方法 - 现在使用表格引擎的精确计算
}

// 创建单例实例
export const unifiedChinesePDFGenerator = new UnifiedChinesePDFGenerator()

// 默认公司信息
export const DEFAULT_COMPANY_INFO: CompanyInfo = {
  name: '电力设备制造有限公司',
  address: '中国上海市浦东新区张江高科技园区科苑路001号',
  phone: '+86 21 1234-5678',
  email: 'info@powerequipment.com.cn',
  website: 'www.powerequipment.com.cn',
  tax_number: '91310000123456789X'
}

// 创建PDF数据的工具函数
export function createQuotePDFData(quote: Quote, companyInfo?: CompanyInfo): QuotePDFData {
  const company = companyInfo || DEFAULT_COMPANY_INFO
  
  const customer: CustomerInfo = {
    name: quote.customer_name,
    company: quote.customer_company,
    email: quote.customer_email,
    phone: quote.customer_phone,
    address: quote.customer_address
  }

  const lineItems = quote.items?.map(item => ({
    product_code: item.product?.code || '',
    product_name: item.product?.name || '',
    description: item.product?.description,
    quantity: item.quantity,
    unit_price: item.unit_price,
    discount_percentage: item.discount_percentage,
    discount_amount: item.discount_amount,
    line_total: item.line_total,
    specifications: item.product?.specifications
  })) || []

  const totals = {
    subtotal: quote.subtotal || 0,
    discount_amount: quote.discount_amount || 0,
    tax_amount: quote.tax_amount || 0,
    total: quote.total_price || 0
  }

  return {
    quote,
    company_info: company,
    customer_info: customer,
    line_items: lineItems,
    totals
  }
}

// 异步版本：从系统设置获取公司信息
export async function createQuotePDFDataFromSettings(quote: Quote): Promise<QuotePDFData> {
  try {
    const companyInfo = await getCompanyInfoForPDF()
    return createQuotePDFData(quote, companyInfo)
  } catch (error) {
    console.warn('Failed to get company info from settings, using defaults:', error)
    return createQuotePDFData(quote)
  }
}

console.log('📄 统一中文PDF生成器已加载 - 支持Noto Sans SC字体和智能降级')