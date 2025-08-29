import { PDFDocument, PDFFont, rgb } from 'pdf-lib'

/**
 * 表格配置接口
 */
export interface TableColumn {
  header: string
  width?: number // 固定宽度
  minWidth?: number // 最小宽度
  maxWidth?: number // 最大宽度
  weight?: number // 权重，用于动态宽度分配
  align?: 'left' | 'center' | 'right' // 对齐方式
  headerAlign?: 'left' | 'center' | 'right' // 表头对齐方式
  wrap?: boolean // 是否允许换行
  fontSize?: number // 字体大小
}

export interface TableCell {
  text: string
  colspan?: number
  rowspan?: number
  align?: 'left' | 'center' | 'right'
  fontSize?: number
  color?: [number, number, number]
  backgroundColor?: [number, number, number]
}

export interface TableOptions {
  columns: TableColumn[]
  data: TableCell[][]
  header?: boolean
  borderColor?: [number, number, number]
  borderWidth?: number
  headerBackgroundColor?: [number, number, number]
  alternateRowColor?: [number, number, number]
  fontSize?: number
  padding?: number
}

/**
 * 专业PDF表格布局引擎
 * 
 * 解决关键问题：
 * ✅ 精确的文本宽度和高度计算
 * ✅ 自动文本换行（支持中文）
 * ✅ 动态列宽和行高
 * ✅ 专业的表格边框渲染
 * ✅ 多种对齐方式
 * 
 * 基于pdf-lib最佳实践和深入研究
 */
export class PDFTableLayoutEngine {
  private pageWidth = 595.28 // A4 width in points
  private margin = 50
  private padding = 8

  /**
   * 精确计算文本宽度
   */
  calculateTextWidth(text: string, font: PDFFont, fontSize: number): number {
    // 使用font.widthOfTextAtSize进行精确计算
    return font.widthOfTextAtSize(text, fontSize)
  }

  /**
   * 智能文本换行 - 支持中英文混合
   */
  wrapText(text: string, font: PDFFont, fontSize: number, maxWidth: number): string[] {
    const lines: string[] = []
    let currentLine = ''
    
    // 处理中文文本换行
    for (let i = 0; i < text.length; i++) {
      const char = text[i]
      const testLine = currentLine + char
      const testWidth = this.calculateTextWidth(testLine, font, fontSize)
      
      if (testWidth > maxWidth && currentLine.length > 0) {
        lines.push(currentLine.trim())
        currentLine = char
      } else {
        currentLine = testLine
      }
    }
    
    if (currentLine.length > 0) {
      lines.push(currentLine.trim())
    }
    
    return lines.length > 0 ? lines : ['']
  }

  /**
   * 计算单元格所需高度
   */
  calculateCellHeight(
    cell: TableCell, 
    font: PDFFont, 
    cellWidth: number, 
    fontSize: number,
    lineHeight: number = 1.2
  ): number {
    const effectiveFontSize = cell.fontSize || fontSize
    const availableWidth = cellWidth - (2 * this.padding)
    
    if (cell.text.trim() === '') {
      return fontSize + (2 * this.padding)
    }
    
    const lines = this.wrapText(cell.text, font, effectiveFontSize, availableWidth)
    const lineCount = Math.max(1, lines.length)
    const textHeight = effectiveFontSize * lineCount * lineHeight
    
    return textHeight + (2 * this.padding)
  }

  /**
   * 动态计算列宽
   */
  calculateColumnWidths(columns: TableColumn[], data: TableCell[][], font: PDFFont, fontSize: number, tableWidth: number): number[] {
    const totalWeight = columns.reduce((sum, col) => sum + (col.weight || 1), 0)
    const minWidths = columns.map(col => col.minWidth || 50)
    const maxWidths = columns.map(col => col.maxWidth || 200)
    
    // 第一轮：计算每列的最大内容宽度
    const contentWidths = columns.map((col, colIndex) => {
      let maxContentWidth = 0
      
      // 检查表头
      const headerWidth = this.calculateTextWidth(col.header, font, fontSize)
      maxContentWidth = Math.max(maxContentWidth, headerWidth)
      
      // 检查数据行
      data.forEach(row => {
        if (row[colIndex]) {
          const cell = row[colIndex]
          const cellWidth = this.calculateTextWidth(cell.text, font, cell.fontSize || fontSize)
          maxContentWidth = Math.max(maxContentWidth, cellWidth)
        }
      })
      
      return maxContentWidth + (2 * this.padding)
    })
    
    // 第二轮：应用约束和分配剩余空间
    let remainingWidth = tableWidth
    let flexibleColumns = columns.map((col, index) => ({
      index,
      weight: col.weight || 1,
      minWidth: Math.max(minWidths[index], contentWidths[index]),
      maxWidth: maxWidths[index]
    }))
    
    // 分配最小宽度
    let usedWidth = 0
    const finalWidths = new Array(columns.length).fill(0)
    
    flexibleColumns.forEach(col => {
      const width = Math.min(col.minWidth, remainingWidth)
      finalWidths[col.index] = width
      remainingWidth -= width
    })
    
    // 如果还有剩余宽度，按权重分配
    if (remainingWidth > 0) {
      const totalFlexibleWeight = flexibleColumns.reduce((sum, col) => {
        return sum + (col.maxWidth > finalWidths[col.index] ? col.weight : 0)
      }, 0)
      
      if (totalFlexibleWeight > 0) {
        flexibleColumns.forEach(col => {
          if (col.maxWidth > finalWidths[col.index]) {
            const additionalWidth = Math.min(
              remainingWidth * (col.weight / totalFlexibleWeight),
              col.maxWidth - finalWidths[col.index]
            )
            finalWidths[col.index] += additionalWidth
            remainingWidth -= additionalWidth
          }
        })
      }
    }
    
    return finalWidths
  }

  /**
   * 绘制表格
   */
  drawTable(
    page: any,
    options: TableOptions,
    fonts: { regular: PDFFont, bold: PDFFont },
    startY: number
  ): number {
    const {
      columns,
      data,
      header = true,
      borderColor = [0.3, 0.3, 0.3],
      borderWidth = 1,
      headerBackgroundColor = [0.9, 0.9, 0.9],
      alternateRowColor = [0.98, 0.98, 0.98],
      fontSize = 10,
      padding = 8
    } = options

    this.padding = padding
    const tableWidth = this.pageWidth - (2 * this.margin)
    
    // 计算列宽
    const columnWidths = this.calculateColumnWidths(columns, data, fonts.regular, fontSize, tableWidth)
    
    // 计算行高
    const rowHeights = data.map(row => {
      let maxHeight = 0
      row.forEach((cell, colIndex) => {
        const cellHeight = this.calculateCellHeight(cell, fonts.regular, columnWidths[colIndex], fontSize)
        maxHeight = Math.max(maxHeight, cellHeight)
      })
      return maxHeight
    })
    
    // 计算表格总高度
    const headerHeight = header ? this.calculateCellHeight(
      { text: columns[0].header }, 
      fonts.bold, 
      columnWidths[0], 
      fontSize
    ) : 0
    
    const totalHeight = headerHeight + rowHeights.reduce((sum, height) => sum + height, 0)
    
    // 重新设计表格绘制顺序，避免边框覆盖文本
    let currentY = startY
    
    // 第一步：绘制表格背景（最底层）
    this.drawTableBackground(page, this.margin, currentY - totalHeight, tableWidth, totalHeight)
    
    // 第二步：绘制表头背景
    if (header) {
      this.drawTableHeaderBackground(page, columns, columnWidths, headerHeight, headerBackgroundColor, currentY)
      currentY -= headerHeight
    }
    
    // 第三步：绘制数据行背景
    rowHeights.forEach((rowHeight, rowIndex) => {
      const backgroundColor = rowIndex % 2 === 1 ? alternateRowColor : [1, 1, 1]
      this.drawTableRowBackground(page, columnWidths, rowHeight, backgroundColor, currentY)
      currentY -= rowHeight
    })
    
    // 第四步：绘制表格边框（中间层）
    this.drawCompleteTableBorder(page, this.margin, startY - totalHeight, tableWidth, totalHeight, borderColor, borderWidth)
    
    // 第五步：绘制列分隔线和行分隔线（中间层）
    this.drawColumnSeparators(page, this.margin, startY - totalHeight, startY, columnWidths, borderColor, borderWidth)
    this.drawRowSeparators(page, this.margin, startY - totalHeight, columnWidths, rowHeights, headerHeight, borderColor, borderWidth)
    
    // 第六步：绘制表头文本（最上层）
    if (header) {
      currentY = startY - headerHeight
      this.drawTableHeaderText(page, columns, columnWidths, headerHeight, fonts.bold, currentY)
    }
    
    // 第七步：绘制数据行文本（最上层）
    currentY = startY - headerHeight
    rowHeights.forEach((rowHeight, rowIndex) => {
      this.drawTableRowText(page, data[rowIndex], columnWidths, rowHeight, fonts.regular, currentY)
      currentY -= rowHeight
    })
    
    return startY - totalHeight
  }

  /**
   * 绘制表格背景
   */
  private drawTableBackground(page: any, x: number, y: number, width: number, height: number): void {
    page.drawRectangle({
      x,
      y,
      width,
      height,
      color: rgb(1, 1, 1)
    })
  }

  /**
   * 绘制表头背景
   */
  private drawTableHeaderBackground(
    page: any,
    columns: TableColumn[],
    columnWidths: number[],
    height: number,
    backgroundColor: [number, number, number],
    startY: number
  ): void {
    page.drawRectangle({
      x: this.margin,
      y: startY - height,
      width: columnWidths.reduce((sum, width) => sum + width, 0),
      height,
      color: rgb(backgroundColor[0], backgroundColor[1], backgroundColor[2])
    })
  }

  /**
   * 绘制表头文本
   */
  private drawTableHeaderText(
    page: any,
    columns: TableColumn[],
    columnWidths: number[],
    height: number,
    font: PDFFont,
    startY: number
  ): void {
    let x = this.margin
    columns.forEach((column, index) => {
      const align = column.headerAlign || column.align || 'center'
      this.drawTextInCell(
        page,
        column.header,
        x,
        startY - height,
        columnWidths[index],
        height,
        font,
        10,
        align,
        'middle',
        rgb(0.1, 0.1, 0.1)
      )
      x += columnWidths[index]
    })
  }

  /**
   * 绘制数据行背景
   */
  private drawTableRowBackground(
    page: any,
    columnWidths: number[],
    height: number,
    backgroundColor: [number, number, number],
    startY: number
  ): void {
    page.drawRectangle({
      x: this.margin,
      y: startY - height,
      width: columnWidths.reduce((sum, width) => sum + width, 0),
      height,
      color: rgb(backgroundColor[0], backgroundColor[1], backgroundColor[2])
    })
  }

  /**
   * 绘制数据行文本
   */
  private drawTableRowText(
    page: any,
    cells: TableCell[],
    columnWidths: number[],
    height: number,
    font: PDFFont,
    startY: number
  ): void {
    let x = this.margin
    cells.forEach((cell, index) => {
      if (index < columnWidths.length) {
        this.drawTextInCell(
          page,
          cell.text,
          x,
          startY - height,
          columnWidths[index],
          height,
          font,
          cell.fontSize || 10,
          cell.align || 'left',
          'top',
          rgb(cell.color?.[0] || 0.2, cell.color?.[1] || 0.2, cell.color?.[2] || 0.2)
        )
        x += columnWidths[index]
      }
    })
  }

  /**
   * 在单元格内绘制文本（优化版）
   */
  private drawTextInCell(
    page: any,
    text: string,
    cellX: number,
    cellY: number,
    cellWidth: number,
    cellHeight: number,
    font: PDFFont,
    fontSize: number,
    hAlign: 'left' | 'center' | 'right',
    vAlign: 'top' | 'middle' | 'bottom',
    color: any
  ): void {
    const availableWidth = cellWidth - (2 * this.padding)
    const lines = this.wrapText(text, font, fontSize, availableWidth)
    const lineHeight = fontSize * 1.2
    const totalTextHeight = lines.length * lineHeight
    
    // 计算垂直位置 - 更精确的垂直居中
    let y = cellY + this.padding
    if (vAlign === 'middle') {
      y = cellY + (cellHeight - totalTextHeight) / 2
    } else if (vAlign === 'bottom') {
      y = cellY + cellHeight - totalTextHeight - this.padding
    }
    
    // 绘制每一行文本
    lines.forEach((line, lineIndex) => {
      const lineWidth = this.calculateTextWidth(line, font, fontSize)
      let x = cellX + this.padding
      
      if (hAlign === 'center') {
        x = cellX + (cellWidth - lineWidth) / 2
      } else if (hAlign === 'right') {
        x = cellX + cellWidth - lineWidth - this.padding
      }
      
      // 改进的文本基线位置计算
      const textY = y + (lineIndex * lineHeight) + (fontSize * 0.85) // 更精确的基线位置
      
      page.drawText(line, {
        x,
        y: textY,
        size: fontSize,
        font,
        color
      })
    })
  }

  /**
   * 绘制完整的表格边框（优化版）
   */
  private drawCompleteTableBorder(page: any, x: number, y: number, width: number, height: number, borderColor: [number, number, number], borderWidth: number): void {
    page.drawRectangle({
      x,
      y,
      width,
      height,
      borderColor: rgb(borderColor[0], borderColor[1], borderColor[2]),
      borderWidth: Math.max(0.5, borderWidth) // 确保边框线宽一致
    })
  }

  /**
   * 绘制列分隔线（优化版）
   */
  private drawColumnSeparators(page: any, startX: number, startY: number, endY: number, columnWidths: number[], borderColor: [number, number, number], borderWidth: number): void {
    let x = startX
    const tableWidth = columnWidths.reduce((sum, w) => sum + w, 0)
    
    for (let i = 0; i < columnWidths.length - 1; i++) {
      x += columnWidths[i]
      // 确保垂直线从表格顶部到底部，但只在内部分隔
      if (x < startX + tableWidth) {
        this.drawVerticalLine(page, x, startY, endY, borderColor, Math.max(0.5, borderWidth))
      }
    }
  }

  /**
   * 绘制行分隔线（优化版）
   */
  private drawRowSeparators(page: any, startX: number, startY: number, columnWidths: number[], rowHeights: number[], headerHeight: number, borderColor: [number, number, number], borderWidth: number): void {
    const tableWidth = columnWidths.reduce((sum, w) => sum + w, 0)
    let currentY = startY - headerHeight
    
    // 绘制表头和数据行之间的分隔线
    if (headerHeight > 0) {
      this.drawHorizontalLine(page, startX, startX + tableWidth, currentY, borderColor, Math.max(0.5, borderWidth))
    }
    
    // 绘制数据行之间的分隔线
    for (let i = 0; i < rowHeights.length - 1; i++) {
      currentY -= rowHeights[i]
      this.drawHorizontalLine(page, startX, startX + tableWidth, currentY, borderColor, Math.max(0.5, borderWidth))
    }
  }

  /**
   * 绘制表格边框（保留原方法以备后用）
   */
  private drawTableBorder(page: any, x: number, y: number, width: number, height: number, borderColor: [number, number, number], borderWidth: number): void {
    page.drawRectangle({
      x,
      y,
      width,
      height,
      borderColor: rgb(borderColor[0], borderColor[1], borderColor[2]),
      borderWidth
    })
  }

  /**
   * 绘制垂直线（增强线条渲染）
   */
  private drawVerticalLine(page: any, x: number, y1: number, y2: number, borderColor: [number, number, number], borderWidth: number): void {
    // 确保y1 <= y2，避免线条绘制错误
    const topY = Math.min(y1, y2)
    const bottomY = Math.max(y1, y2)
    
    page.drawLine({
      start: { x, y: topY },
      end: { x, y: bottomY },
      thickness: Math.max(0.5, borderWidth),
      color: rgb(borderColor[0], borderColor[1], borderColor[2])
    })
  }

  /**
   * 绘制水平线（增强线条渲染）
   */
  private drawHorizontalLine(page: any, x1: number, x2: number, y: number, borderColor: [number, number, number], borderWidth: number): void {
    // 确保x1 <= x2，避免线条绘制错误
    const leftX = Math.min(x1, x2)
    const rightX = Math.max(x1, x2)
    
    page.drawLine({
      start: { x: leftX, y },
      end: { x: rightX, y },
      thickness: Math.max(0.5, borderWidth),
      color: rgb(borderColor[0], borderColor[1], borderColor[2])
    })
  }
}

// 创建单例实例
export const pdfTableLayoutEngine = new PDFTableLayoutEngine()