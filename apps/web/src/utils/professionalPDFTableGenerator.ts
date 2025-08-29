import { PDFDocument, PDFFont, rgb, PDFPage } from 'pdf-lib'
import fontkit from '@pdf-lib/fontkit'
import { PDFTableLayoutEngine, TableColumn, TableRow, TableCell, TableOptions } from './pdfTableLayoutEngine.js'
import type { Quote, QuotePDFData, CompanyInfo, CustomerInfo } from '@/types'

/**
 * Professional PDF Table Generator
 * 
 * Uses the advanced table layout engine to create perfectly formatted tables with:
 * ✅ Automatic text wrapping
 * ✅ Dynamic column sizing
 * ✅ Professional alignment
 * ✅ Chinese language support
 * ✅ Dynamic row heights
 * ✅ Clean border rendering
 */

export interface QuoteLineItem {
  product_code?: string
  product_name: string
  description?: string
  quantity: number
  unit_price: number
  discount_percentage?: number
  discount_amount?: number
  line_total: number
  specifications?: string
}

export interface QuoteTotals {
  subtotal: number
  discount_amount: number
  tax_amount: number
  total: number
}

export class ProfessionalPDFTableGenerator {
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

  // Font cache
  private static fontCache: Map<string, ArrayBuffer> = new Map()
  private regularFont: PDFFont | null = null
  private boldFont: PDFFont | null = null

  /**
   * Load Chinese font with fallback strategy
   */
  private async loadChineseFont(pdfDoc: PDFDocument): Promise<{ regular: PDFFont, bold: PDFFont }> {
    try {
      pdfDoc.registerFontkit(fontkit)
      
      let fontData = ProfessionalPDFTableGenerator.fontCache.get('NotoSansSC-Regular')
      
      if (!fontData) {
        const fontSources = [
          '/fonts/NotoSansSC-Regular.ttf',
          'https://fonts.gstatic.com/s/notosanssc/v36/k3kCo84MPvpLmixcA63oeAL7Iqp5IZJF9bmaG9_FnYxNbPzS5HE.ttf',
          'https://cdn.jsdelivr.net/npm/@expo-google-fonts/noto-sans-sc@0.2.2/NotoSansSC_400Regular.ttf'
        ]

        for (const source of fontSources) {
          try {
            const response = await fetch(source)
            if (response.ok) {
              fontData = await response.arrayBuffer()
              if (fontData.byteLength > 50000) {
                ProfessionalPDFTableGenerator.fontCache.set('NotoSansSC-Regular', fontData)
                console.log(`✅ 成功加载中文字体: ${source} (${(fontData.byteLength / 1024 / 1024).toFixed(2)}MB)`)
                break
              }
            }
          } catch (error) {
            console.warn(`字体加载失败: ${source}`, error)
          }
        }
      }

      if (fontData) {
        this.regularFont = await pdfDoc.embedFont(fontData)
        this.boldFont = this.regularFont // Use same font for bold (can load separate bold font if needed)
        console.log('✅ 中文字体嵌入成功')
        return { regular: this.regularFont, bold: this.boldFont }
      }

      // Fallback to standard fonts
      this.regularFont = await pdfDoc.embedFont('Helvetica')
      this.boldFont = await pdfDoc.embedFont('Helvetica-Bold')
      console.log('⚠️ 使用降级字体策略')
      return { regular: this.regularFont, bold: this.boldFont }

    } catch (error) {
      console.error('❌ 字体加载失败:', error)
      throw new Error('无法加载字体')
    }
  }

  /**
   * Create professional line items table
   */
  public createLineItemsTable(lineItems: QuoteLineItem[], startX: number, startY: number): {
    columns: TableColumn[]
    rows: TableRow[]
    options: TableOptions
  } {
    const tableWidth = this.pageWidth - (2 * this.margin)
    
    // Define professional table columns with proper sizing
    const columns: TableColumn[] = [
      {
        header: '产品名称',
        percentage: 0.20,
        align: 'left',
        headerAlign: 'center',
        wrap: true,
        minWidth: 80
      },
      {
        header: '产品描述',
        percentage: 0.30,
        align: 'left',
        headerAlign: 'center',
        wrap: true,
        minWidth: 100
      },
      {
        header: '规格',
        percentage: 0.15,
        align: 'left',
        headerAlign: 'center',
        wrap: true,
        minWidth: 60
      },
      {
        header: '数量',
        percentage: 0.10,
        align: 'center',
        headerAlign: 'center',
        wrap: false,
        minWidth: 40
      },
      {
        header: '单价 (¥)',
        percentage: 0.12,
        align: 'right',
        headerAlign: 'center',
        wrap: false,
        minWidth: 50
      },
      {
        header: '折扣',
        percentage: 0.08,
        align: 'center',
        headerAlign: 'center',
        wrap: false,
        minWidth: 35
      },
      {
        header: '小计 (¥)',
        percentage: 0.15,
        align: 'right',
        headerAlign: 'center',
        wrap: false,
        minWidth: 50
      }
    ]

    // Create header row
    const headerRow: TableRow = {
      cells: columns.map(col => ({
        text: col.header,
        align: col.headerAlign || 'center',
        fontWeight: 'bold',
        fontSize: this.fontSize.small,
        color: '0.1,0.1,0.1'
      })),
      isHeader: true,
      backgroundColor: '0.95,0.95,0.95'
    }

    // Create data rows
    const dataRows: TableRow[] = lineItems.map((item, index) => ({
      cells: [
        {
          text: item.product_name || '未命名产品',
          align: 'left',
          wrap: true,
          fontSize: this.fontSize.small,
          color: '0.2,0.2,0.2'
        },
        {
          text: item.description || '暂无描述',
          align: 'left',
          wrap: true,
          fontSize: this.fontSize.small,
          color: '0.3,0.3,0.3'
        },
        {
          text: item.specifications || '-',
          align: 'left',
          wrap: true,
          fontSize: this.fontSize.small,
          color: '0.4,0.4,0.4'
        },
        {
          text: item.quantity.toString(),
          align: 'center',
          wrap: false,
          fontSize: this.fontSize.small,
          color: '0.2,0.2,0.2'
        },
        {
          text: this.formatCurrency(item.unit_price),
          align: 'right',
          wrap: false,
          fontSize: this.fontSize.small,
          color: '0.2,0.2,0.2'
        },
        {
          text: item.discount_percentage ? `${item.discount_percentage}%` : '-',
          align: 'center',
          wrap: false,
          fontSize: this.fontSize.small,
          color: '0.6,0.3,0.3'
        },
        {
          text: this.formatCurrency(item.line_total),
          align: 'right',
          wrap: false,
          fontWeight: 'bold',
          fontSize: this.fontSize.small,
          color: '0.1,0.1,0.1'
        }
      ],
      backgroundColor: index % 2 === 0 ? '1,1,1' : '0.98,0.98,0.98'
    }))

    const rows: TableRow[] = [headerRow, ...dataRows]

    // Table styling options
    const options: TableOptions = {
      x: startX,
      y: startY,
      width: tableWidth,
      borderWidth: 0.8,
      borderColor: '0.6,0.6,0.6',
      headerBackgroundColor: '0.95,0.95,0.95',
      headerTextColor: '0.1,0.1,0.1',
      headerFontSize: this.fontSize.small,
      headerFontWeight: 'bold',
      rowBackgroundColor: '1,1,1',
      alternateRowBackgroundColor: '0.98,0.98,0.98',
      cellPadding: 6,
      fontSize: this.fontSize.small,
      fontColor: '0.2,0.2,0.2',
      lineHeight: 1.3
    }

    return { columns, rows, options }
  }

  /**
   * Create professional summary table
   */
  public createSummaryTable(totals: QuoteTotals, startX: number, startY: number): {
    columns: TableColumn[]
    rows: TableRow[]
    options: TableOptions
  } {
    const tableWidth = 200 // Fixed width for summary
    
    const columns: TableColumn[] = [
      {
        header: '项目',
        width: tableWidth * 0.6,
        align: 'left',
        headerAlign: 'left',
        wrap: false
      },
      {
        header: '金额',
        width: tableWidth * 0.4,
        align: 'right',
        headerAlign: 'right',
        wrap: false
      }
    ]

    const rows: TableRow[] = [
      {
        cells: [
          { text: '小计', align: 'left', fontSize: this.fontSize.normal },
          { text: this.formatCurrency(totals.subtotal), align: 'right', fontSize: this.fontSize.normal }
        ]
      }
    ]

    if (totals.discount_amount > 0) {
      rows.push({
        cells: [
          { text: '折扣', align: 'left', fontSize: this.fontSize.normal, color: '0.8,0.2,0.2' },
          { text: `-${this.formatCurrency(totals.discount_amount)}`, align: 'right', fontSize: this.fontSize.normal, color: '0.8,0.2,0.2' }
        ]
      })
    }

    if (totals.tax_amount > 0) {
      rows.push({
        cells: [
          { text: '税费', align: 'left', fontSize: this.fontSize.normal },
          { text: this.formatCurrency(totals.tax_amount), align: 'right', fontSize: this.fontSize.normal }
        ]
      })
    }

    // Add separator line
    rows.push({
      cells: [
        { text: '', align: 'left' },
        { text: '', align: 'right' }
      ],
      backgroundColor: '0.9,0.9,0.9'
    })

    // Add total
    rows.push({
      cells: [
        { text: '总计', align: 'left', fontWeight: 'bold', fontSize: this.fontSize.heading, color: '0.1,0.1,0.1' },
        { text: this.formatCurrency(totals.total), align: 'right', fontWeight: 'bold', fontSize: this.fontSize.heading, color: '0.8,0.2,0.2' }
      ]
    })

    const options: TableOptions = {
      x: startX,
      y: startY,
      width: tableWidth,
      borderWidth: 0.5,
      borderColor: '0.4,0.4,0.4',
      cellPadding: 4,
      fontSize: this.fontSize.normal,
      fontColor: '0.2,0.2,0.2',
      lineHeight: 1.2
    }

    return { columns, rows, options }
  }

  /**
   * Generate complete quote PDF with professional tables
   */
  public async generateQuotePDF(data: QuotePDFData): Promise<Uint8Array> {
    try {
      console.log('🚀 开始生成专业PDF表格...')
      
      const pdfDoc = await PDFDocument.create()
      const fonts = await this.loadChineseFont(pdfDoc)
      const page = pdfDoc.addPage([this.pageWidth, this.pageHeight])
      
      let currentY = this.pageHeight - this.margin

      // Add company header
      currentY = this.addCompanyHeader(page, fonts, data.company_info, currentY)
      
      // Add quote header
      currentY = this.addQuoteHeader(page, fonts, data.quote, currentY)
      
      // Add customer info
      currentY = this.addCustomerInfo(page, fonts, data.customer_info, currentY)
      
      // Add professional line items table
      currentY = this.addLineItemsTable(page, fonts, data.line_items, currentY)
      
      // Add summary table
      currentY = this.addSummaryTable(page, fonts, data.totals, currentY)
      
      // Add terms and conditions
      if (data.quote.terms_conditions) {
        currentY = this.addTermsAndConditions(page, fonts, data.quote.terms_conditions, currentY)
      }
      
      // Add footer
      this.addFooter(page, fonts, data.company_info)

      const pdfBytes = await pdfDoc.save()
      console.log(`✅ 专业PDF生成成功，大小: ${(pdfBytes.length / 1024).toFixed(1)}KB`)
      return pdfBytes
    } catch (error) {
      console.error('❌ PDF生成失败:', error)
      throw new Error(`PDF生成失败: ${error.message}`)
    }
  }

  /**
   * Add line items table using the layout engine
   */
  private addLineItemsTable(page: PDFPage, fonts: { regular: PDFFont, bold: PDFFont }, lineItems: QuoteLineItem[], startY: number): number {
    const tableEngine = new PDFTableLayoutEngine(fonts.regular, fonts.bold)
    const tableData = this.createLineItemsTable(lineItems, this.margin, startY)
    
    const result = tableEngine.drawTable(page, tableData.columns, tableData.rows, tableData.options)
    
    console.log(`📊 表格渲染完成: ${result.columnWidths.length}列 x ${tableData.rows.length}行, 总高度: ${result.totalHeight.toFixed(1)}pt`)
    
    return startY - result.totalHeight - 20
  }

  /**
   * Add summary table
   */
  private addSummaryTable(page: PDFPage, fonts: { regular: PDFFont, bold: PDFFont }, totals: QuoteTotals, startY: number): number {
    const tableEngine = new PDFTableLayoutEngine(fonts.regular, fonts.bold)
    const tableData = this.createSummaryTable(totals, this.pageWidth - this.margin - 220, startY)
    
    const result = tableEngine.drawTable(page, tableData.columns, tableData.rows, tableData.options)
    
    return startY - result.totalHeight - 20
  }

  /**
   * Format currency with proper localization
   */
  private formatCurrency(amount: number): string {
    return `¥${amount.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  /**
   * Add company header (unchanged from original)
   */
  private addCompanyHeader(page: PDFPage, fonts: { regular: PDFFont, bold: PDFFont }, companyInfo: CompanyInfo, startY: number): number {
    let currentY = startY

    const companyName = companyInfo.name || '电力设备制造有限公司'
    const titleWidth = fonts.bold.widthOfTextAtSize(companyName, this.fontSize.title)
    page.drawText(companyName, {
      x: this.pageWidth / 2 - titleWidth / 2,
      y: currentY,
      size: this.fontSize.title,
      font: fonts.bold,
      color: rgb(0.1, 0.1, 0.1)
    })
    currentY -= 35

    if (companyInfo.address) {
      const addressWidth = fonts.regular.widthOfTextAtSize(companyInfo.address, this.fontSize.normal)
      page.drawText(companyInfo.address, {
        x: this.pageWidth / 2 - addressWidth / 2,
        y: currentY,
        size: this.fontSize.normal,
        font: fonts.regular,
        color: rgb(0.3, 0.3, 0.3)
      })
      currentY -= 25
    }

    const contactInfo = []
    if (companyInfo.phone) contactInfo.push(`电话: ${companyInfo.phone}`)
    if (companyInfo.email) contactInfo.push(`邮箱: ${companyInfo.email}`)
    if (companyInfo.website) contactInfo.push(`网站: ${companyInfo.website}`)
    
    if (contactInfo.length > 0) {
      const contactText = contactInfo.join(' | ')
      const contactWidth = fonts.regular.widthOfTextAtSize(contactText, this.fontSize.small)
      page.drawText(contactText, {
        x: this.pageWidth / 2 - contactWidth / 2,
        y: currentY,
        size: this.fontSize.small,
        font: fonts.regular,
        color: rgb(0.4, 0.4, 0.4)
      })
      currentY -= 20
    }

    page.drawLine({
      start: { x: this.margin, y: currentY },
      end: { x: this.pageWidth - this.margin, y: currentY },
      thickness: 2,
      color: rgb(0.2, 0.2, 0.2)
    })
    currentY -= 30

    return currentY
  }

  /**
   * Add quote header (unchanged from original)
   */
  private addQuoteHeader(page: PDFPage, fonts: { regular: PDFFont, bold: PDFFont }, quote: Quote, startY: number): number {
    let currentY = startY

    page.drawText('产品报价单', {
      x: this.margin,
      y: currentY,
      size: this.fontSize.heading,
      font: fonts.bold,
      color: rgb(0.1, 0.1, 0.1)
    })

    const quoteNoText = `报价单号: ${quote.quote_number}`
    const quoteNoWidth = fonts.regular.widthOfTextAtSize(quoteNoText, this.fontSize.normal)
    page.drawText(quoteNoText, {
      x: this.pageWidth - this.margin - quoteNoWidth,
      y: currentY,
      size: this.fontSize.normal,
      font: fonts.regular,
      color: rgb(0.2, 0.2, 0.2)
    })
    currentY -= 25

    const date = new Date(quote.created_at).toLocaleDateString('zh-CN')
    const dateText = `日期: ${date}`
    const dateWidth = fonts.regular.widthOfTextAtSize(dateText, this.fontSize.normal)
    page.drawText(dateText, {
      x: this.pageWidth - this.margin - dateWidth,
      y: currentY,
      size: this.fontSize.normal,
      font: fonts.regular,
      color: rgb(0.2, 0.2, 0.2)
    })
    currentY -= 20

    if (quote.valid_until) {
      const validUntil = new Date(quote.valid_until).toLocaleDateString('zh-CN')
      const validText = `有效期至: ${validUntil}`
      const validWidth = fonts.regular.widthOfTextAtSize(validText, this.fontSize.normal)
      page.drawText(validText, {
        x: this.pageWidth - this.margin - validWidth,
        y: currentY,
        size: this.fontSize.normal,
        font: fonts.regular,
        color: rgb(0.6, 0.2, 0.2)
      })
      currentY -= 20
    }

    currentY -= 15
    return currentY
  }

  /**
   * Add customer info (unchanged from original)
   */
  private addCustomerInfo(page: PDFPage, fonts: { regular: PDFFont, bold: PDFFont }, customerInfo: CustomerInfo, startY: number): number {
    let currentY = startY

    page.drawText('客户信息', {
      x: this.margin,
      y: currentY,
      size: this.fontSize.subheading,
      font: fonts.bold,
      color: rgb(0.1, 0.1, 0.1)
    })
    currentY -= 25

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
        page.drawText(text, {
          x: this.margin,
          y: currentY,
          size: this.fontSize.normal,
          font: fonts.regular,
          color: rgb(0.2, 0.2, 0.2)
        })
        currentY -= 18
      }
    })

    currentY -= 15
    return currentY
  }

  /**
   * Add terms and conditions with improved text wrapping
   */
  private addTermsAndConditions(page: PDFPage, fonts: { regular: PDFFont, bold: PDFFont }, terms: string, startY: number): number {
    let currentY = startY

    page.drawText('条款和条件', {
      x: this.margin,
      y: currentY,
      size: this.fontSize.subheading,
      font: fonts.bold,
      color: rgb(0.1, 0.1, 0.1)
    })
    currentY -= 25

    // Use the layout engine for better text wrapping
    const maxWidth = this.pageWidth - (2 * this.margin)
    const tableEngine = new PDFTableLayoutEngine(fonts.regular, fonts.bold)
    
    // Create a single-cell table for the terms text
    const columns: TableColumn[] = [{
      header: '',
      width: maxWidth,
      align: 'left',
      wrap: true
    }]

    const rows: TableRow[] = [{
      cells: [{
        text: terms,
        align: 'left',
        wrap: true,
        fontSize: this.fontSize.small,
        color: '0.3,0.3,0.3'
      }]
    }]

    const options: TableOptions = {
      x: this.margin,
      y: currentY,
      width: maxWidth,
      borderWidth: 0,
      cellPadding: 0,
      fontSize: this.fontSize.small
    }

    const result = tableEngine.drawTable(page, columns, rows, options)
    
    return startY - result.totalHeight - 15
  }

  /**
   * Add footer (unchanged from original)
   */
  private addFooter(page: PDFPage, fonts: { regular: PDFFont, bold: PDFFont }, companyInfo: CompanyInfo): void {
    const footerY = this.margin - 10
    const centerX = this.pageWidth / 2

    const footerText = `本报价单由 ${companyInfo.name || '本公司'} 提供`
    const footerWidth = fonts.regular.widthOfTextAtSize(footerText, this.fontSize.small)
    
    page.drawText(footerText, {
      x: centerX - footerWidth / 2,
      y: footerY,
      size: this.fontSize.small,
      font: fonts.regular,
      color: rgb(0.5, 0.5, 0.5)
    })
  }

  /**
   * Test the table generation with sample data
   */
  public async testTableGeneration(): Promise<boolean> {
    try {
      console.log('🧪 测试专业表格生成...')
      
      // Create test data with various content types
      const testData: QuotePDFData = {
        quote: {
          quote_number: 'TEST-2024-001',
          created_at: new Date().toISOString(),
          valid_until: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
          terms_conditions: '这是一段测试用的条款和条件文本，用来验证文本换行功能是否正常工作。包含中文和English混合内容，以及较长的句子来测试自动换行效果。This is a mixed language test to verify the text wrapping functionality works correctly with both Chinese and English text.'
        },
        company_info: {
          name: '测试公司',
          address: '测试地址',
          phone: '123-456-7890',
          email: 'test@example.com'
        },
        customer_info: {
          name: '测试客户',
          company: '客户公司',
          email: 'customer@example.com',
          phone: '098-765-4321',
          address: '客户地址'
        },
        line_items: [
          {
            product_name: '高压变压器',
            description: '这是一款高性能的高压变压器，适用于各种工业应用场景。具有高效率、低噪音、长寿命等特点。This is a high-performance high-voltage transformer suitable for various industrial applications.',
            specifications: '型号: HV-2024, 电压: 10kV, 功率: 1000kVA',
            quantity: 2,
            unit_price: 15000,
            discount_percentage: 5,
            line_total: 28500
          },
          {
            product_name: '配电柜',
            description: '智能配电控制系统，采用先进的微处理器技术，实现精确的电力分配和监控功能。',
            specifications: '型号: PDC-001, 额定电流: 630A',
            quantity: 1,
            unit_price: 8500,
            line_total: 8500
          },
          {
            product_name: '电力电缆',
            description: '高质量铜芯电力电缆，具有良好的导电性能和耐用性。',
            specifications: '规格: YJV-3x95mm², 长度: 100m',
            quantity: 5,
            unit_price: 1200,
            line_total: 6000
          }
        ],
        totals: {
          subtotal: 43000,
          discount_amount: 1500,
          tax_amount: 0,
          total: 41500
        }
      }

      const pdfBytes = await this.generateQuotePDF(testData)
      
      // Test if PDF generation succeeded
      if (pdfBytes && pdfBytes.length > 1000) {
        console.log('✅ 专业表格生成测试通过')
        return true
      }
      
      return false
    } catch (error) {
      console.error('❌ 专业表格生成测试失败:', error)
      return false
    }
  }
}

// Create singleton instance
export const professionalPDFTableGenerator = new ProfessionalPDFTableGenerator()

// Default company info
export const DEFAULT_COMPANY_INFO: CompanyInfo = {
  name: '电力设备制造有限公司',
  address: '中国上海市浦东新区张江高科技园区科苑路001号',
  phone: '+86 21 1234-5678',
  email: 'info@powerequipment.com.cn',
  website: 'www.powerequipment.com.cn',
  tax_number: '91310000123456789X'
}

// Create PDF data utility function
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
    line_items,
    totals
  }
}

console.log('🚀 专业PDF表格生成器已加载 - 支持自动换行、动态列宽、专业对齐')