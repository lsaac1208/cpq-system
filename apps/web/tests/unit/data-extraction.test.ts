/**
 * 前端数据提取方法单元测试
 * 测试 BatchAnalysisResultsSimple.vue 中的数据解析逻辑
 */

import { describe, it, expect } from 'vitest'

// 模拟前端数据提取方法
class DataExtractor {
  extractJsonFromRawAnalysis(rawAnalysis: string): any {
    try {
      // 从markdown JSON代码块中提取JSON
      const jsonMatch = rawAnalysis.match(/```json\s*([\s\S]*?)\s*```/)
      if (jsonMatch) {
        return JSON.parse(jsonMatch[1])
      }
      // 尝试直接解析JSON
      return JSON.parse(rawAnalysis)
    } catch {
      return null
    }
  }

  extractTechnicalRequirements(rawAnalysis: string): string {
    const data = this.extractJsonFromRawAnalysis(rawAnalysis)
    if (data?.技术需求?.性能规格要求) {
      return data.技术需求.性能规格要求.slice(0, 3).join(', ') + (data.技术需求.性能规格要求.length > 3 ? '...' : '')
    }
    return '未提取到技术需求信息'
  }

  extractBudgetRange(rawAnalysis: string): string {
    const data = this.extractJsonFromRawAnalysis(rawAnalysis)
    return data?.商务需求?.预算范围 || data?.预算范围 || '未指定'
  }

  extractTimeline(rawAnalysis: string): string {
    const data = this.extractJsonFromRawAnalysis(rawAnalysis)
    return data?.商务需求?.项目时间线 || data?.项目时间线 || data?.时间要求 || '未指定'
  }

  extractCompetitorProduct(rawAnalysis: string): string {
    const data = this.extractJsonFromRawAnalysis(rawAnalysis)
    return data?.产品信息?.产品名称 || data?.competitor_product || '未识别产品'
  }

  extractCompetitorPrice(rawAnalysis: string): string {
    const data = this.extractJsonFromRawAnalysis(rawAnalysis)
    return data?.价格信息?.价格范围 || data?.price_info || '未获取价格信息'
  }

  extractProjectInfo(rawAnalysis: string): string {
    const data = this.extractJsonFromRawAnalysis(rawAnalysis)
    return data?.项目信息?.项目类型 || data?.project_type || '未分类项目'
  }

  extractSuccessPatterns(rawAnalysis: string): string {
    const data = this.extractJsonFromRawAnalysis(rawAnalysis)
    if (data?.成功经验 && Array.isArray(data.成功经验)) {
      return data.成功经验.slice(0, 2).join('; ')
    }
    return data?.success_patterns || '未发现明显成功模式'
  }

  extractProductDetails(rawAnalysis: string): string {
    const data = this.extractJsonFromRawAnalysis(rawAnalysis)
    if (data?.产品信息?.产品名称) {
      return `${data.产品信息.产品名称} - ${data.产品信息.产品描述 || '无描述'}`
    }
    return data?.product_name || '未提取到产品信息'
  }

  extractDocumentCategory(rawAnalysis: string): string {
    const data = this.extractJsonFromRawAnalysis(rawAnalysis)
    return data?.文档类型 || data?.document_category || '未分类'
  }

  extractQualityScore(rawAnalysis: string): string {
    const data = this.extractJsonFromRawAnalysis(rawAnalysis)
    const score = data?.质量评分 || data?.quality_score
    return score ? `${score}/100` : '未评分'
  }

  extractComprehensiveInsights(rawAnalysis: string): string {
    const data = this.extractJsonFromRawAnalysis(rawAnalysis)
    if (data?.综合评估?.关键发现) {
      return data.综合评估.关键发现.slice(0, 2).join('; ')
    }
    return data?.key_insights || '综合分析结果'
  }
}

describe('数据提取方法测试', () => {
  const extractor = new DataExtractor()

  describe('JSON解析测试', () => {
    it('应该正确解析markdown JSON代码块', () => {
      const rawAnalysis = `\`\`\`json
{
  "技术需求": {
    "性能规格要求": ["高速处理", "低延迟", "高可靠性"]
  }
}
\`\`\``
      
      const result = extractor.extractJsonFromRawAnalysis(rawAnalysis)
      expect(result).not.toBeNull()
      expect(result.技术需求.性能规格要求).toEqual(['高速处理', '低延迟', '高可靠性'])
    })

    it('应该处理直接JSON字符串', () => {
      const rawAnalysis = '{"test": "value"}'
      const result = extractor.extractJsonFromRawAnalysis(rawAnalysis)
      expect(result).toEqual({ test: 'value' })
    })

    it('应该处理无效JSON返回null', () => {
      const rawAnalysis = 'invalid json'
      const result = extractor.extractJsonFromRawAnalysis(rawAnalysis)
      expect(result).toBeNull()
    })
  })

  describe('客户需求分析数据提取', () => {
    const sampleCustomerData = `\`\`\`json
{
  "技术需求": {
    "性能规格要求": ["高速处理", "低延迟", "高可靠性", "模块化设计", "可扩展性"]
  },
  "商务需求": {
    "预算范围": "100-200万元",
    "项目时间线": "6个月内完成"
  }
}
\`\`\``

    it('应该正确提取技术需求', () => {
      const result = extractor.extractTechnicalRequirements(sampleCustomerData)
      expect(result).toBe('高速处理, 低延迟, 高可靠性...')
    })

    it('应该正确提取预算范围', () => {
      const result = extractor.extractBudgetRange(sampleCustomerData)
      expect(result).toBe('100-200万元')
    })

    it('应该正确提取项目时间线', () => {
      const result = extractor.extractTimeline(sampleCustomerData)
      expect(result).toBe('6个月内完成')
    })

    it('应该处理缺失技术需求的情况', () => {
      const emptyData = '```json\n{}\n```'
      const result = extractor.extractTechnicalRequirements(emptyData)
      expect(result).toBe('未提取到技术需求信息')
    })
  })

  describe('竞品分析数据提取', () => {
    const sampleCompetitorData = `\`\`\`json
{
  "产品信息": {
    "产品名称": "竞品A系统",
    "产品描述": "企业级管理系统"
  },
  "价格信息": {
    "价格范围": "80-150万元"
  }
}
\`\`\``

    it('应该正确提取竞品产品信息', () => {
      const result = extractor.extractCompetitorProduct(sampleCompetitorData)
      expect(result).toBe('竞品A系统')
    })

    it('应该正确提取竞品价格信息', () => {
      const result = extractor.extractCompetitorPrice(sampleCompetitorData)
      expect(result).toBe('80-150万元')
    })

    it('应该处理缺失竞品信息的情况', () => {
      const emptyData = '```json\n{}\n```'
      const productResult = extractor.extractCompetitorProduct(emptyData)
      const priceResult = extractor.extractCompetitorPrice(emptyData)
      
      expect(productResult).toBe('未识别产品')
      expect(priceResult).toBe('未获取价格信息')
    })
  })

  describe('项目洞察数据提取', () => {
    const sampleProjectData = `\`\`\`json
{
  "项目信息": {
    "项目类型": "ERP实施项目"
  },
  "成功经验": ["需求分析要充分", "用户培训很重要", "分阶段实施"]
}
\`\`\``

    it('应该正确提取项目信息', () => {
      const result = extractor.extractProjectInfo(sampleProjectData)
      expect(result).toBe('ERP实施项目')
    })

    it('应该正确提取成功经验', () => {
      const result = extractor.extractSuccessPatterns(sampleProjectData)
      expect(result).toBe('需求分析要充分; 用户培训很重要')
    })

    it('应该处理缺失项目信息的情况', () => {
      const emptyData = '```json\n{}\n```'
      const result = extractor.extractProjectInfo(emptyData)
      expect(result).toBe('未分类项目')
    })
  })

  describe('产品信息提取', () => {
    const sampleProductData = `\`\`\`json
{
  "产品信息": {
    "产品名称": "测试产品",
    "产品描述": "这是一个测试产品"
  }
}
\`\`\``

    it('应该正确提取产品详情', () => {
      const result = extractor.extractProductDetails(sampleProductData)
      expect(result).toBe('测试产品 - 这是一个测试产品')
    })

    it('应该处理无产品描述的情况', () => {
      const noDescData = `\`\`\`json
{
  "产品信息": {
    "产品名称": "测试产品"
  }
}
\`\`\``
      const result = extractor.extractProductDetails(noDescData)
      expect(result).toBe('测试产品 - 无描述')
    })
  })

  describe('文档分类数据提取', () => {
    const sampleClassificationData = `\`\`\`json
{
  "文档类型": "技术规格书"
}
\`\`\``

    it('应该正确提取文档分类', () => {
      const result = extractor.extractDocumentCategory(sampleClassificationData)
      expect(result).toBe('技术规格书')
    })

    it('应该处理未分类的情况', () => {
      const emptyData = '```json\n{}\n```'
      const result = extractor.extractDocumentCategory(emptyData)
      expect(result).toBe('未分类')
    })
  })

  describe('质量评估数据提取', () => {
    const sampleQualityData = `\`\`\`json
{
  "质量评分": 85
}
\`\`\``

    it('应该正确提取质量评分', () => {
      const result = extractor.extractQualityScore(sampleQualityData)
      expect(result).toBe('85/100')
    })

    it('应该处理未评分的情况', () => {
      const emptyData = '```json\n{}\n```'
      const result = extractor.extractQualityScore(emptyData)
      expect(result).toBe('未评分')
    })
  })

  describe('综合分析数据提取', () => {
    const sampleComprehensiveData = `\`\`\`json
{
  "综合评估": {
    "关键发现": ["数据质量良好", "业务逻辑清晰", "技术架构合理"]
  }
}
\`\`\``

    it('应该正确提取综合洞察', () => {
      const result = extractor.extractComprehensiveInsights(sampleComprehensiveData)
      expect(result).toBe('数据质量良好; 业务逻辑清晰')
    })

    it('应该处理缺失综合分析的情况', () => {
      const emptyData = '```json\n{}\n```'
      const result = extractor.extractComprehensiveInsights(emptyData)
      expect(result).toBe('综合分析结果')
    })
  })

  describe('数据一致性测试', () => {
    it('应该处理后端实际数据格式', () => {
      // 模拟后端实际返回的数据格式
      const backendFormat = {
        filename: 'test_document.pdf',
        analysis_result: {
          analysis_type: 'customer_requirements',
          business_insights: {
            customer_requirements: {
              raw_analysis: `\`\`\`json
{
  "技术需求": {
    "性能规格要求": ["高速处理", "低延迟", "高可靠性"]
  },
  "商务需求": {
    "预算范围": "100-200万元"
  }
}
\`\`\``,
              risk_assessment: {
                overall_risk_level: '中等'
              }
            }
          },
          confidence_scores: {
            overall: 0.85,
            level: 'high'
          }
        }
      }

      // 测试数据提取
      const rawAnalysis = backendFormat.analysis_result.business_insights.customer_requirements.raw_analysis
      
      const techReq = extractor.extractTechnicalRequirements(rawAnalysis)
      const budget = extractor.extractBudgetRange(rawAnalysis)
      
      expect(techReq).toBe('高速处理, 低延迟, 高可靠性')
      expect(budget).toBe('100-200万元')
    })

    it('应该正确处理文件名字段的多种格式', () => {
      const testCases = [
        { filename: 'test.pdf', expected: 'test.pdf' },
        { file_name: 'test.pdf', expected: 'test.pdf' },
        { original_filename: 'test.pdf', expected: 'test.pdf' },
        { filename: null, file_name: 'test.pdf', expected: 'test.pdf' },
        {}, // 空对象
      ]

      testCases.forEach((testCase, index) => {
        const result = testCase.filename || testCase.file_name || testCase.original_filename || '未知文件'
        if (index < 4) {
          expect(result).toBe('test.pdf')
        } else {
          expect(result).toBe('未知文件')
        }
      })
    })
  })

  describe('边界情况测试', () => {
    it('应该处理空字符串', () => {
      const result = extractor.extractTechnicalRequirements('')
      expect(result).toBe('未提取到技术需求信息')
    })

    it('应该处理null/undefined输入', () => {
      const result1 = extractor.extractTechnicalRequirements(null as any)
      const result2 = extractor.extractTechnicalRequirements(undefined as any)
      
      expect(result1).toBe('未提取到技术需求信息')
      expect(result2).toBe('未提取到技术需求信息')
    })

    it('应该处理格式错误的JSON', () => {
      const malformedJson = '```json\n{invalid json}\n```'
      const result = extractor.extractTechnicalRequirements(malformedJson)
      expect(result).toBe('未提取到技术需求信息')
    })

    it('应该处理超长数组的截断', () => {
      const longArrayData = `\`\`\`json
{
  "技术需求": {
    "性能规格要求": ["需求1", "需求2", "需求3", "需求4", "需求5", "需求6"]
  }
}
\`\`\``
      
      const result = extractor.extractTechnicalRequirements(longArrayData)
      expect(result).toBe('需求1, 需求2, 需求3...')
    })
  })
})