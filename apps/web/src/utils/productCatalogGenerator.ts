import { PDFDocument, PDFFont, rgb } from 'pdf-lib'
import fontkit from '@pdf-lib/fontkit'
import { PDFTableLayoutEngine, type TableColumn, type TableCell } from './pdfTableLayoutEngine'
import type { Product } from '@/types/product'
import { DEFAULT_COMPANY_INFO } from './unifiedChinesePDFGenerator'

/**
 * 产品目录PDF生成器
 * 使用PDF表格布局引擎生成专业的产品目录
 */
export class ProductCatalogGenerator {
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
  private regularFont: PDFFont | null = null
  private boldFont: PDFFont | null = null

  /**
   * 加载中文字体
   */
  private async loadChineseFont(pdfDoc: PDFDocument): Promise<{ regular: PDFFont, bold: PDFFont }> {
    try {
      // 先尝试从缓存获取
      let fontData = ProductCatalogGenerator.fontCache.get('NotoSansSC-Regular')
      
      if (!fontData) {
        // 尝试多个字体源
        const fontSources = [
          '/fonts/NotoSansSC-Regular.ttf', // 本地字体文件
          'https://fonts.gstatic.com/s/notosanssc/v36/k3kCo84MPvpLmixcA63oeAL7Iqp5IZJF9bmaG9_FnYxNbPzS5HE.ttf', // Google Fonts CDN
        ]

        for (const source of fontSources) {
          try {
            console.log(`尝试加载中文字体: ${source}`)
            const response = await fetch(source)
            if (response.ok) {
              fontData = await response.arrayBuffer()
              // 验证字体文件大小
              if (fontData.byteLength > 50000) { // 至少50KB，确保是有效的字体文件
                ProductCatalogGenerator.fontCache.set('NotoSansSC-Regular', fontData)
                console.log(`✅ 成功加载中文字体: ${source} (${(fontData.byteLength / 1024 / 1024).toFixed(2)}MB)`)
                break
              } else {
                console.warn(`字体文件太小，可能无效: ${source} (${fontData.byteLength} bytes)`)
                fontData = null
              }
            }
          } catch (error) {
            console.warn(`加载字体失败: ${source}`, error)
            fontData = null
          }
        }

        if (!fontData) {
          throw new Error('无法加载任何中文字体文件')
        }
      }

      // 嵌入字体到PDF文档
      this.regularFont = await pdfDoc.embedFont(fontData)
      
      // 使用同一字体作为粗体（实际项目中可以加载单独的Bold字体文件）
      this.boldFont = this.regularFont

      console.log('✅ 中文字体加载成功')
      return {
        regular: this.regularFont,
        bold: this.boldFont
      }
    } catch (error) {
      console.error('❌ 中文字体加载失败:', error)
      throw new Error('中文字体加载失败，PDF生成将无法正确显示中文')
    }
  }

  /**
   * 生成产品目录PDF
   */
  public async generateProductCatalogPDF(products: Product[]): Promise<Uint8Array> {
    try {
      console.log('开始生成产品目录PDF...')
      
      // 创建PDF文档
      const pdfDoc = await PDFDocument.create()
      pdfDoc.registerFontkit(fontkit)
      
      // 加载中文字体
      const fonts = await this.loadChineseFont(pdfDoc)
      
      // 创建表格布局引擎实例
      const tableEngine = new PDFTableLayoutEngine()
      
      let currentPage = pdfDoc.addPage([this.pageWidth, this.pageHeight])
      let currentY = this.pageHeight - this.margin

      // 添加公司头部信息
      currentY = await this.addCompanyHeader(currentPage, fonts, currentY)
      
      // 添加目录标题
      currentY = await this.addCatalogHeader(currentPage, fonts, products.length, currentY)
      
      // 添加产品分类统计
      currentY = await this.addCategorySummary(currentPage, fonts, products, currentY)
      
      // 添加产品表格
      currentY = await this.addProductTable(currentPage, fonts, products, tableEngine, currentY)
      
      // 序列化PDF
      const pdfBytes = await pdfDoc.save()
      console.log('✅ 产品目录PDF生成成功')
      return pdfBytes
    } catch (error) {
      console.error('❌ 生成产品目录PDF失败:', error)
      throw new Error(`产品目录PDF生成失败: ${error.message}`)
    }
  }

  /**
   * 添加公司头部信息
   */
  private async addCompanyHeader(page: any, fonts: { regular: PDFFont, bold: PDFFont }, startY: number): Promise<number> {
    let currentY = startY

    // 公司名称
    const companyName = DEFAULT_COMPANY_INFO.name || '电力设备制造有限公司'
    const titleWidth = this.getTextWidth(companyName, this.fontSize.title)
    page.drawText(companyName, {
      x: this.pageWidth / 2 - titleWidth / 2,
      y: currentY,
      size: this.fontSize.title,
      font: fonts.bold,
      color: rgb(0.1, 0.1, 0.1)
    })
    currentY -= 35

    // 公司地址
    if (DEFAULT_COMPANY_INFO.address) {
      const addressWidth = this.getTextWidth(DEFAULT_COMPANY_INFO.address, this.fontSize.normal)
      page.drawText(DEFAULT_COMPANY_INFO.address, {
        x: this.pageWidth / 2 - addressWidth / 2,
        y: currentY,
        size: this.fontSize.normal,
        font: fonts.regular,
        color: rgb(0.3, 0.3, 0.3)
      })
      currentY -= 25
    }

    // 联系信息
    const contactInfo = []
    if (DEFAULT_COMPANY_INFO.phone) contactInfo.push(`电话: ${DEFAULT_COMPANY_INFO.phone}`)
    if (DEFAULT_COMPANY_INFO.email) contactInfo.push(`邮箱: ${DEFAULT_COMPANY_INFO.email}`)
    if (DEFAULT_COMPANY_INFO.website) contactInfo.push(`网站: ${DEFAULT_COMPANY_INFO.website}`)
    
    if (contactInfo.length > 0) {
      const contactText = contactInfo.join(' | ')
      const contactWidth = this.getTextWidth(contactText, this.fontSize.small)
      page.drawText(contactText, {
        x: this.pageWidth / 2 - contactWidth / 2,
        y: currentY,
        size: this.fontSize.small,
        font: fonts.regular,
        color: rgb(0.4, 0.4, 0.4)
      })
      currentY -= 20
    }

    // 装饰性分隔线
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
   * 添加目录标题
   */
  private async addCatalogHeader(page: any, fonts: { regular: PDFFont, bold: PDFFont }, productCount: number, startY: number): Promise<number> {
    let currentY = startY

    // 目录标题
    page.drawText('产品目录', {
      x: this.margin,
      y: currentY,
      size: this.fontSize.heading,
      font: fonts.bold,
      color: rgb(0.1, 0.1, 0.1)
    })

    // 产品数量和生成日期
    const dateText = `生成日期: ${new Date().toLocaleDateString('zh-CN')} | 产品总数: ${productCount}`
    const dateWidth = this.getTextWidth(dateText, this.fontSize.normal)
    page.drawText(dateText, {
      x: this.pageWidth - this.margin - dateWidth,
      y: currentY,
      size: this.fontSize.normal,
      font: fonts.regular,
      color: rgb(0.2, 0.2, 0.2)
    })

    currentY -= 40
    return currentY
  }

  /**
   * 添加分类统计
   */
  private async addCategorySummary(page: any, fonts: { regular: PDFFont, bold: PDFFont }, products: Product[], startY: number): Promise<number> {
    let currentY = startY

    // 统计各分类产品数量
    const categoryStats = new Map<string, number>()
    products.forEach(product => {
      const category = product.category || '未分类'
      categoryStats.set(category, (categoryStats.get(category) || 0) + 1)
    })

    // 分类标题
    page.drawText('分类统计', {
      x: this.margin,
      y: currentY,
      size: this.fontSize.subheading,
      font: fonts.bold,
      color: rgb(0.1, 0.1, 0.1)
    })
    currentY -= 25

    // 分类统计信息
    const statsText = Array.from(categoryStats.entries())
      .map(([category, count]) => `${category}: ${count}个产品`)
      .join(' | ')
    
    const statsWidth = this.getTextWidth(statsText, this.fontSize.normal)
    page.drawText(statsText, {
      x: this.pageWidth / 2 - statsWidth / 2,
      y: currentY,
      size: this.fontSize.normal,
      font: fonts.regular,
      color: rgb(0.3, 0.3, 0.3)
    })

    currentY -= 40
    return currentY
  }

  /**
   * 添加产品表格
   */
  private async addProductTable(page: any, fonts: { regular: PDFFont, bold: PDFFont }, products: Product[], tableEngine: PDFTableLayoutEngine, startY: number): Promise<number> {
    // 表格列配置
    const columns: TableColumn[] = [
      { header: '产品代码', width: 80, align: 'center' },
      { header: '产品名称', width: 120, align: 'left' },
      { header: '分类', width: 80, align: 'center' },
      { header: '基础价格', width: 80, align: 'right' },
      { header: '产品类型', width: 70, align: 'center' },
      { header: '状态', width: 60, align: 'center' },
      { header: '描述', width: 120, align: 'left' }
    ]

    // 转换产品数据为表格数据
    const tableData: TableCell[][] = products.map(product => [
      { text: product.code || '', align: 'center' },
      { text: product.name || '', align: 'left' },
      { text: product.category || '', align: 'center' },
      { text: `$${product.base_price?.toLocaleString() || '0'}`, align: 'right' },
      { text: product.is_configurable ? '可配置' : '标准', align: 'center' },
      { text: product.is_active ? '活跃' : '非活跃', align: 'center' },
      { text: product.description || '', align: 'left' }
    ])

    // 表格选项
    const tableOptions = {
      columns,
      data: tableData,
      header: true,
      borderColor: [0.3, 0.3, 0.3],
      borderWidth: 1,
      headerBackgroundColor: [0.9, 0.9, 0.9],
      alternateRowColor: [0.98, 0.98, 0.98],
      fontSize: 9,
      padding: 6
    }

    // 使用表格布局引擎绘制表格
    const endY = tableEngine.drawTable(page, tableOptions, fonts, startY)

    return endY
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
   * 下载产品目录PDF
   */
  public async downloadProductCatalogPDF(products: Product[], filename?: string): Promise<void> {
    try {
      const pdfBytes = await this.generateProductCatalogPDF(products)
      
      // 创建Blob并下载
      const blob = new Blob([pdfBytes], { type: 'application/pdf' })
      const url = URL.createObjectURL(blob)
      
      const link = document.createElement('a')
      link.href = url
      link.download = filename || `产品目录-${new Date().toLocaleDateString('zh-CN')}.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      URL.revokeObjectURL(url)
      console.log('✅ 产品目录PDF下载成功')
    } catch (error) {
      console.error('❌ 下载产品目录PDF失败:', error)
      throw error
    }
  }
}

// 创建单例实例
export const productCatalogGenerator = new ProductCatalogGenerator()

/**
 * 快速生成产品目录PDF
 */
export async function generateProductCatalogPDF(products: Product[]): Promise<void> {
  await productCatalogGenerator.downloadProductCatalogPDF(products)
}

console.log('📄 产品目录PDF生成器已加载 - 使用PDF表格布局引擎')