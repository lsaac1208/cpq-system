/**
 * 高性能图片压缩工具
 * 使用Canvas API + Web Worker实现快速图片压缩
 */

// 压缩配置接口
export interface CompressionOptions {
  maxWidth?: number
  maxHeight?: number
  quality?: number
  maxSizeMB?: number
  format?: 'jpeg' | 'webp' | 'png'
  enableWebWorker?: boolean
}

// 压缩结果接口
export interface CompressionResult {
  file: File
  originalSize: number
  compressedSize: number
  compressionRatio: number
  width: number
  height: number
  format: string
}

// 进度回调接口
export type ProgressCallback = (progress: number, stage: string) => void

class FastImageCompressor {
  private static instance: FastImageCompressor
  private worker?: Worker

  static getInstance(): FastImageCompressor {
    if (!FastImageCompressor.instance) {
      FastImageCompressor.instance = new FastImageCompressor()
    }
    return FastImageCompressor.instance
  }

  /**
   * 快速图片压缩 - 主要方法
   */
  async compressImage(
    file: File,
    options: CompressionOptions = {},
    onProgress?: ProgressCallback
  ): Promise<CompressionResult> {
    const defaultOptions: Required<CompressionOptions> = {
      maxWidth: 1920,
      maxHeight: 1920,
      quality: 0.85,
      maxSizeMB: 2,
      format: 'jpeg',
      enableWebWorker: true,
      ...options
    }

    onProgress?.(0, '开始处理图片')

    // 验证文件
    if (!this.isValidImageFile(file)) {
      throw new Error('不支持的文件格式')
    }

    onProgress?.(10, '读取图片数据')

    // 创建图片元素
    const img = await this.loadImage(file)
    
    onProgress?.(25, '计算压缩参数')

    // 计算目标尺寸
    const { targetWidth, targetHeight } = this.calculateTargetSize(
      img.width,
      img.height,
      defaultOptions.maxWidth,
      defaultOptions.maxHeight
    )

    onProgress?.(40, '开始压缩图片')

    // 执行压缩
    const compressedBlob = await this.compressWithCanvas(
      img,
      targetWidth,
      targetHeight,
      defaultOptions.quality,
      defaultOptions.format,
      (progress) => onProgress?.(40 + progress * 0.5, '压缩中')
    )

    onProgress?.(90, '优化文件大小')

    // 如果文件仍然太大，进行二次压缩
    let finalBlob = compressedBlob
    if (compressedBlob.size > defaultOptions.maxSizeMB * 1024 * 1024) {
      finalBlob = await this.secondaryCompression(
        img,
        targetWidth,
        targetHeight,
        defaultOptions,
        (progress) => onProgress?.(90 + progress * 0.1, '深度压缩')
      )
    }

    onProgress?.(100, '压缩完成')

    // 创建压缩后的文件
    const compressedFile = new File(
      [finalBlob],
      this.generateCompressedFileName(file.name, defaultOptions.format),
      { type: finalBlob.type }
    )

    return {
      file: compressedFile,
      originalSize: file.size,
      compressedSize: finalBlob.size,
      compressionRatio: ((file.size - finalBlob.size) / file.size) * 100,
      width: targetWidth,
      height: targetHeight,
      format: defaultOptions.format
    }
  }

  /**
   * 验证图片文件
   */
  private isValidImageFile(file: File): boolean {
    const validTypes = [
      'image/jpeg',
      'image/jpg', 
      'image/png',
      'image/webp',
      'image/gif'
    ]
    return validTypes.includes(file.type)
  }

  /**
   * 加载图片
   */
  private loadImage(file: File): Promise<HTMLImageElement> {
    return new Promise((resolve, reject) => {
      const img = new Image()
      img.onload = () => resolve(img)
      img.onerror = () => reject(new Error('图片加载失败'))
      img.src = URL.createObjectURL(file)
    })
  }

  /**
   * 计算目标尺寸
   */
  private calculateTargetSize(
    originalWidth: number,
    originalHeight: number,
    maxWidth: number,
    maxHeight: number
  ): { targetWidth: number; targetHeight: number } {
    let targetWidth = originalWidth
    let targetHeight = originalHeight

    // 计算缩放比例
    const widthRatio = maxWidth / originalWidth
    const heightRatio = maxHeight / originalHeight
    const ratio = Math.min(widthRatio, heightRatio, 1) // 不放大

    targetWidth = Math.round(originalWidth * ratio)
    targetHeight = Math.round(originalHeight * ratio)

    return { targetWidth, targetHeight }
  }

  /**
   * 使用Canvas进行高效压缩
   */
  private compressWithCanvas(
    img: HTMLImageElement,
    targetWidth: number,
    targetHeight: number,
    quality: number,
    format: string,
    onProgress?: (progress: number) => void
  ): Promise<Blob> {
    return new Promise((resolve, reject) => {
      try {
        // 创建离屏Canvas以提高性能
        const canvas = document.createElement('canvas')
        const ctx = canvas.getContext('2d')
        
        if (!ctx) {
          throw new Error('无法创建Canvas上下文')
        }

        canvas.width = targetWidth
        canvas.height = targetHeight

        onProgress?.(0.2)

        // 使用高质量图片缩放算法
        ctx.imageSmoothingEnabled = true
        ctx.imageSmoothingQuality = 'high'

        onProgress?.(0.5)

        // 绘制图片
        ctx.drawImage(img, 0, 0, targetWidth, targetHeight)

        onProgress?.(0.8)

        // 转换为Blob
        canvas.toBlob(
          (blob) => {
            if (blob) {
              resolve(blob)
            } else {
              reject(new Error('图片压缩失败'))
            }
          },
          this.getMimeType(format),
          quality
        )

        onProgress?.(1)

      } catch (error) {
        reject(error)
      }
    })
  }

  /**
   * 二次压缩 - 当文件仍然过大时
   */
  private async secondaryCompression(
    img: HTMLImageElement,
    width: number,
    height: number,
    options: Required<CompressionOptions>,
    onProgress?: (progress: number) => void
  ): Promise<Blob> {
    // 更激进的压缩设置
    const aggressiveWidth = Math.round(width * 0.8)
    const aggressiveHeight = Math.round(height * 0.8)
    const aggressiveQuality = Math.max(0.6, options.quality * 0.8)

    return this.compressWithCanvas(
      img,
      aggressiveWidth,
      aggressiveHeight,
      aggressiveQuality,
      'jpeg', // 强制使用JPEG获得最佳压缩
      onProgress
    )
  }

  /**
   * 获取MIME类型
   */
  private getMimeType(format: string): string {
    switch (format) {
      case 'jpeg':
        return 'image/jpeg'
      case 'webp':
        return 'image/webp'
      case 'png':
        return 'image/png'
      default:
        return 'image/jpeg'
    }
  }

  /**
   * 生成压缩后的文件名
   */
  private generateCompressedFileName(originalName: string, format: string): string {
    const nameWithoutExt = originalName.replace(/\.[^/.]+$/, '')
    const ext = format === 'jpeg' ? 'jpg' : format
    return `${nameWithoutExt}_compressed.${ext}`
  }
}

// 导出单例实例
export const fastCompressor = FastImageCompressor.getInstance()

/**
 * 便捷的压缩函数
 */
export async function compressImageFast(
  file: File,
  options?: CompressionOptions,
  onProgress?: ProgressCallback
): Promise<CompressionResult> {
  return fastCompressor.compressImage(file, options, onProgress)
}

/**
 * 批量压缩图片
 */
export async function compressImagesBatch(
  files: File[],
  options?: CompressionOptions,
  onProgress?: (fileIndex: number, fileProgress: number, fileName: string) => void
): Promise<CompressionResult[]> {
  const results: CompressionResult[] = []

  for (let i = 0; i < files.length; i++) {
    const file = files[i]
    const result = await compressImageFast(
      file,
      options,
      (progress, stage) => {
        onProgress?.(i, progress, file.name)
      }
    )
    results.push(result)
  }

  return results
}

/**
 * 预设压缩配置
 */
export const CompressionPresets = {
  // 高质量 - 适合产品展示图
  highQuality: {
    maxWidth: 2048,
    maxHeight: 2048,
    quality: 0.9,
    maxSizeMB: 3,
    format: 'jpeg' as const
  },
  
  // 标准质量 - 平衡质量和大小
  standard: {
    maxWidth: 1920,
    maxHeight: 1920,
    quality: 0.85,
    maxSizeMB: 2,
    format: 'jpeg' as const
  },
  
  // 快速压缩 - 优先速度
  fast: {
    maxWidth: 1280,
    maxHeight: 1280,
    quality: 0.8,
    maxSizeMB: 1,
    format: 'jpeg' as const
  },
  
  // 缩略图
  thumbnail: {
    maxWidth: 400,
    maxHeight: 400,
    quality: 0.8,
    maxSizeMB: 0.2,
    format: 'jpeg' as const
  }
}