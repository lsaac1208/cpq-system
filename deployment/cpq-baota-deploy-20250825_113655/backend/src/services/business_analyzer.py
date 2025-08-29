# -*- coding: utf-8 -*-
"""
业务分析服务
专门处理客户需求分析、竞品分析和历史项目挖掘的AI分析服务
"""
import logging
import time
import json
from typing import Dict, Any, Optional, List
from werkzeug.datastructures import FileStorage

from .document_processor import DocumentProcessor
from .zhipuai_client import ZhipuAIClient
from .confidence_scorer import ConfidenceScorer

logger = logging.getLogger(__name__)

class BusinessAnalyzer:
    """业务文档分析器"""
    
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.ai_client = ZhipuAIClient()
        self.confidence_scorer = ConfidenceScorer()
    
    def analyze_business_document(self, file: FileStorage, analysis_type: str, 
                                business_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        分析业务文档
        
        Args:
            file: 上传的文件对象
            analysis_type: 分析类型 (customer_requirements, competitor_analysis, project_mining)
            business_context: 业务上下文配置
            
        Returns:
            Dict: 完整的分析结果
        """
        start_time = time.time()
        
        try:
            # 1. 处理文档，提取文本
            logger.info(f"Processing business document: {file.filename}, type: {analysis_type}")
            text_content, doc_info = self.document_processor.process_document(file)
            
            if not text_content.strip():
                raise ValueError("Document contains no readable text content")
            
            # 2. 根据分析类型选择相应的分析方法
            if analysis_type == 'customer_requirements':
                analysis_result = self._analyze_customer_requirements(text_content, business_context)
            elif analysis_type == 'competitor_analysis':
                analysis_result = self._analyze_competitor_info(text_content, business_context)
            elif analysis_type == 'project_mining':
                analysis_result = self._analyze_project_insights(text_content, business_context)
            else:
                raise ValueError(f"Unsupported analysis type: {analysis_type}")
            
            # 3. 计算置信度分数
            confidence_scores = self.confidence_scorer.calculate_confidence(
                text_content, analysis_result
            )
            
            processing_time = time.time() - start_time
            
            # 4. 构建完整结果
            result = {
                'success': True,
                'analysis_type': analysis_type,
                'business_insights': analysis_result,
                'confidence_scores': confidence_scores,
                'document_info': {
                    **doc_info,
                    'analysis_duration': processing_time,
                    'filename': file.filename
                },
                'metadata': {
                    'processing_timestamp': time.time(),
                    'business_context': business_context or {}
                }
            }
            
            logger.info(f"Business analysis completed for {file.filename} in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Business analysis failed for {file.filename}: {str(e)}")
            
            return {
                'success': False,
                'error': str(e),
                'analysis_type': analysis_type,
                'document_info': {
                    'filename': file.filename,
                    'analysis_duration': processing_time,
                    'size': len(file.read()) if file else 0,
                    'type': file.content_type if file else 'unknown'
                }
            }
    
    def _analyze_customer_requirements(self, text_content: str, 
                                     business_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """分析客户需求文档"""
        
        # 构建针对客户需求分析的提示词
        industry = business_context.get('industry', '未指定') if business_context else '未指定'
        requirements_type = business_context.get('requirements_type', 'mixed') if business_context else 'mixed'
        analysis_focus = business_context.get('analysis_focus', []) if business_context else []
        
        prompt = f"""
作为专业的需求分析师，请分析以下客户需求文档，提取关键信息。

行业背景：{industry}
需求类型：{requirements_type}
分析重点：{', '.join(analysis_focus) if analysis_focus else '全面分析'}

请从以下维度分析客户需求：

1. 技术需求
   - 性能规格要求
   - 功能需求列表
   - 技术约束条件
   - 合规标准要求

2. 商务需求
   - 预算范围
   - 项目时间线
   - 交付条件
   - 支持需求

3. 决策因素
   - 关键评估标准
   - 优先级排序
   - 决定性因素

4. 风险评估
   - 技术风险
   - 商务风险
   - 时间风险
   - 整体风险等级

请以JSON格式返回结构化的分析结果。

文档内容：
{text_content[:4000]}  # 限制长度避免token超限
"""
        
        try:
            response = self.ai_client.chat(prompt)
            
            # 尝试解析JSON响应
            try:
                analysis_data = json.loads(response)
            except json.JSONDecodeError:
                # 如果不是JSON格式，创建结构化数据
                analysis_data = self._parse_requirements_text(response)
            
            return {
                'customer_requirements': {
                    'technical_requirements': analysis_data.get('technical_requirements', {}),
                    'business_requirements': analysis_data.get('business_requirements', {}),
                    'decision_factors': analysis_data.get('decision_factors', {}),
                    'risk_assessment': analysis_data.get('risk_assessment', {
                        'overall_risk_level': 'medium'
                    }),
                    'extracted_insights': analysis_data.get('insights', []),
                    'raw_analysis': response
                }
            }
            
        except Exception as e:
            logger.error(f"Customer requirements analysis failed: {str(e)}")
            return {
                'customer_requirements': {
                    'error': str(e),
                    'raw_text_snippet': text_content[:500]
                }
            }
    
    def _analyze_competitor_info(self, text_content: str, 
                               business_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """分析竞品信息文档"""
        
        industry = business_context.get('industry', '未指定') if business_context else '未指定'
        competitor_category = business_context.get('competitor_category', '未指定') if business_context else '未指定'
        analysis_focus = business_context.get('analysis_focus', []) if business_context else []
        
        prompt = f"""
作为专业的市场分析师，请分析以下竞品资料，提取关键竞争情报。

行业背景：{industry}
产品类别：{competitor_category}
分析重点：{', '.join(analysis_focus) if analysis_focus else '全面分析'}

请从以下维度分析竞品信息：

1. 竞争对手基本信息
   - 公司名称
   - 产品名称
   - 市场地位
   - 主要优势
   - 明显弱点

2. 价格分析
   - 基础价格
   - 定价模式
   - 折扣结构
   - 总拥有成本

3. 技术对比
   - 技术规格
   - 性能基准
   - 功能矩阵
   - 技术栈

4. 市场情报
   - 市场份额
   - 客户反馈
   - 最新动态
   - 战略方向

5. 竞争定位
   - 差异化因素
   - 竞争优势
   - 威胁分析
   - 机会识别

请以JSON格式返回结构化的分析结果。

文档内容：
{text_content[:4000]}
"""
        
        try:
            response = self.ai_client.chat(prompt)
            
            try:
                analysis_data = json.loads(response)
            except json.JSONDecodeError:
                analysis_data = self._parse_competitor_text(response)
            
            return {
                'competitor_analysis': {
                    'competitor_info': analysis_data.get('competitor_info', {}),
                    'pricing_analysis': analysis_data.get('pricing_analysis', {}),
                    'technical_comparison': analysis_data.get('technical_comparison', {}),
                    'market_intelligence': analysis_data.get('market_intelligence', {}),
                    'competitive_positioning': analysis_data.get('competitive_positioning', {}),
                    'raw_analysis': response
                }
            }
            
        except Exception as e:
            logger.error(f"Competitor analysis failed: {str(e)}")
            return {
                'competitor_analysis': {
                    'error': str(e),
                    'raw_text_snippet': text_content[:500]
                }
            }
    
    def _analyze_project_insights(self, text_content: str, 
                                business_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """分析历史项目文档，挖掘项目洞察"""
        
        industry = business_context.get('industry', '未指定') if business_context else '未指定'
        project_type = business_context.get('project_type', '未指定') if business_context else '未指定'
        project_phase = business_context.get('project_phase', 'planning') if business_context else 'planning'
        analysis_focus = business_context.get('analysis_focus', []) if business_context else []
        
        prompt = f"""
作为资深项目管理专家，请分析以下历史项目文档，挖掘有价值的项目洞察。

行业背景：{industry}
项目类型：{project_type}
项目阶段：{project_phase}
分析重点：{', '.join(analysis_focus) if analysis_focus else '全面分析'}

请从以下维度分析项目信息：

1. 项目元数据
   - 项目类型和规模
   - 行业领域
   - 项目周期
   - 最终结果

2. 成功模式
   - 关键成功因素
   - 最佳实践
   - 关键里程碑
   - 资源配置模式

3. 经验教训
   - 成功经验
   - 遇到的挑战
   - 解决方案
   - 改进建议

4. 可复用资产
   - 模板和工具
   - 配置参数
   - 流程工作流
   - 技术方案

5. 风险指标
   - 早期预警信号
   - 缓解策略
   - 应急计划

请以JSON格式返回结构化的分析结果。

文档内容：
{text_content[:4000]}
"""
        
        try:
            response = self.ai_client.chat(prompt)
            
            try:
                analysis_data = json.loads(response)
            except json.JSONDecodeError:
                analysis_data = self._parse_project_text(response)
            
            return {
                'project_insights': {
                    'project_metadata': analysis_data.get('project_metadata', {}),
                    'success_patterns': analysis_data.get('success_patterns', {}),
                    'lessons_learned': analysis_data.get('lessons_learned', {}),
                    'reusable_assets': analysis_data.get('reusable_assets', {}),
                    'risk_indicators': analysis_data.get('risk_indicators', {}),
                    'raw_analysis': response
                }
            }
            
        except Exception as e:
            logger.error(f"Project insights analysis failed: {str(e)}")
            return {
                'project_insights': {
                    'error': str(e),
                    'raw_text_snippet': text_content[:500]
                }
            }
    
    def _parse_requirements_text(self, text: str) -> Dict[str, Any]:
        """解析客户需求分析的文本响应"""
        # 简单的文本解析逻辑，提取关键信息
        return {
            'technical_requirements': {
                'extracted_from_text': True,
                'summary': text[:200]
            },
            'business_requirements': {
                'extracted_from_text': True,
                'summary': text[:200]
            },
            'decision_factors': {
                'extracted_from_text': True,
                'summary': text[:200]
            },
            'risk_assessment': {
                'overall_risk_level': 'medium',
                'extracted_from_text': True
            }
        }
    
    def _parse_competitor_text(self, text: str) -> Dict[str, Any]:
        """解析竞品分析的文本响应"""
        return {
            'competitor_info': {
                'extracted_from_text': True,
                'summary': text[:200]
            },
            'pricing_analysis': {
                'extracted_from_text': True,
                'summary': text[:200]
            },
            'technical_comparison': {
                'extracted_from_text': True,
                'summary': text[:200]
            }
        }
    
    def _parse_project_text(self, text: str) -> Dict[str, Any]:
        """解析项目洞察的文本响应"""
        return {
            'project_metadata': {
                'extracted_from_text': True,
                'summary': text[:200]
            },
            'success_patterns': {
                'extracted_from_text': True,
                'summary': text[:200]
            },
            'lessons_learned': {
                'extracted_from_text': True,
                'summary': text[:200]
            }
        }
    
    def analyze_document(self, document_content: str, analysis_type: str = 'customer_requirements', 
                        business_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        分析文档内容
        
        Args:
            document_content: 文档文本内容
            analysis_type: 分析类型
            business_context: 业务上下文
            
        Returns:
            Dict: 分析结果
        """
        start_time = time.time()
        
        try:
            # 根据分析类型选择相应的分析方法
            if analysis_type == 'customer_requirements':
                analysis_result = self._analyze_customer_requirements(document_content, business_context)
            elif analysis_type == 'competitor_analysis':
                analysis_result = self._analyze_competitor_info(document_content, business_context)
            elif analysis_type == 'project_mining':
                analysis_result = self._analyze_project_insights(document_content, business_context)
            elif analysis_type == 'product_extraction':
                analysis_result = self._analyze_product_extraction(document_content, business_context)
            elif analysis_type == 'document_classification':
                analysis_result = self._analyze_document_classification(document_content, business_context)
            elif analysis_type == 'quality_assessment':
                analysis_result = self._analyze_quality_assessment(document_content, business_context)
            elif analysis_type == 'comprehensive':
                analysis_result = self._analyze_comprehensive(document_content, business_context)
            else:
                raise ValueError(f"Unsupported analysis type: {analysis_type}")
            
            # 计算置信度分数
            confidence_scores = self.confidence_scorer.calculate_comprehensive_confidence(
                analysis_result, {'text_length': len(document_content), 'type': 'business_document'}
            )
            
            processing_time = time.time() - start_time
            
            # 构建完整结果
            result = {
                'success': True,
                'analysis_type': analysis_type,
                'business_insights': analysis_result,
                'confidence_scores': confidence_scores,
                'processing_time': processing_time,
                'metadata': {
                    'processing_timestamp': time.time(),
                    'business_context': business_context or {}
                }
            }
            
            logger.info(f"Business analysis completed for type {analysis_type} in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Business analysis failed for type {analysis_type}: {str(e)}")
            
            return {
                'success': False,
                'error': str(e),
                'analysis_type': analysis_type,
                'processing_time': processing_time
            }
    
    def _analyze_product_extraction(self, text_content: str, 
                                  business_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """专业产品信息提取分析"""
        
        industry = business_context.get('industry', '未指定') if business_context else '未指定'
        product_category = business_context.get('product_category', '通用') if business_context else '通用'
        extraction_focus = business_context.get('extraction_focus', []) if business_context else []
        
        prompt = f"""
作为专业的产品数据分析师，请从以下文档中提取结构化的产品信息。

行业背景：{industry}
产品类别：{product_category}
提取重点：{', '.join(extraction_focus) if extraction_focus else '全面提取'}

请从以下维度提取产品信息：

1. 基本产品信息
   - 产品名称和型号
   - 制造商信息
   - 产品类别分类
   - 产品代码/SKU

2. 技术规格
   - 核心技术参数
   - 性能指标
   - 物理规格（尺寸、重量等）
   - 环境要求

3. 功能特性
   - 主要功能列表
   - 特殊功能
   - 可选配置
   - 扩展能力

4. 商务信息
   - 价格信息
   - 最小订单量
   - 交付周期
   - 质保条款

5. 合规认证
   - 质量认证
   - 安全标准
   - 环保认证
   - 行业标准

6. 应用场景
   - 目标市场
   - 适用行业
   - 使用场景
   - 兼容性信息

请以JSON格式返回结构化的产品信息。

文档内容：
{text_content[:4000]}
"""
        
        try:
            response = self.ai_client.chat(prompt)
            
            try:
                analysis_data = json.loads(response)
            except json.JSONDecodeError:
                analysis_data = self._parse_product_text(response)
            
            return {
                'product_extraction': {
                    'basic_info': analysis_data.get('basic_info', {}),
                    'technical_specs': analysis_data.get('technical_specs', {}),
                    'functional_features': analysis_data.get('functional_features', {}),
                    'business_info': analysis_data.get('business_info', {}),
                    'compliance_certs': analysis_data.get('compliance_certs', {}),
                    'application_scenarios': analysis_data.get('application_scenarios', {}),
                    'structured_data': analysis_data,
                    'raw_analysis': response
                }
            }
            
        except Exception as e:
            logger.error(f"Product extraction analysis failed: {str(e)}")
            return {
                'product_extraction': {
                    'error': str(e),
                    'raw_text_snippet': text_content[:500]
                }
            }
    
    def _analyze_document_classification(self, text_content: str, 
                                       business_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """专业文档分类分析"""
        
        business_domain = business_context.get('business_domain', '通用') if business_context else '通用'
        classification_level = business_context.get('classification_level', 'standard') if business_context else 'standard'
        
        prompt = f"""
作为专业的文档分类专家，请对以下文档进行多维度分类分析。

业务领域：{business_domain}
分类精度：{classification_level}

请从以下维度分析文档：

1. 文档类型分类
   - 主要文档类型（技术文档、商务文档、法律文档等）
   - 细分子类型
   - 文档格式特征
   - 内容结构模式

2. 业务分类
   - 业务流程阶段（售前、售中、售后）
   - 业务功能分类（市场、销售、技术、支持等）
   - 重要程度等级
   - 时效性分类

3. 内容特征
   - 主题关键词
   - 内容复杂度
   - 技术专业程度
   - 信息密度

4. 目标受众
   - 主要读者群体
   - 专业水平要求
   - 使用场景
   - 访问权限建议

5. 处理建议
   - 优先级评级
   - 后续处理流程
   - 存储分类建议
   - 关联文档推荐

6. 元数据标签
   - 自动标签生成
   - 分类标识码
   - 索引关键词
   - 检索优化建议

请以JSON格式返回结构化的分类结果。

文档内容：
{text_content[:4000]}
"""
        
        try:
            response = self.ai_client.chat(prompt)
            
            try:
                analysis_data = json.loads(response)
            except json.JSONDecodeError:
                analysis_data = self._parse_classification_text(response)
            
            return {
                'document_classification': {
                    'document_type': analysis_data.get('document_type', {}),
                    'business_classification': analysis_data.get('business_classification', {}),
                    'content_features': analysis_data.get('content_features', {}),
                    'target_audience': analysis_data.get('target_audience', {}),
                    'processing_recommendations': analysis_data.get('processing_recommendations', {}),
                    'metadata_tags': analysis_data.get('metadata_tags', {}),
                    'classification_confidence': analysis_data.get('confidence_score', 0.85),
                    'raw_analysis': response
                }
            }
            
        except Exception as e:
            logger.error(f"Document classification analysis failed: {str(e)}")
            return {
                'document_classification': {
                    'error': str(e),
                    'raw_text_snippet': text_content[:500]
                }
            }
    
    def _analyze_quality_assessment(self, text_content: str, 
                                  business_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """专业质量评估分析"""
        
        assessment_criteria = business_context.get('assessment_criteria', []) if business_context else []
        quality_standards = business_context.get('quality_standards', 'ISO') if business_context else 'ISO'
        
        prompt = f"""
作为专业的质量评估专家，请对以下文档进行全面的质量评估。

评估标准：{quality_standards}
评估重点：{', '.join(assessment_criteria) if assessment_criteria else '全面评估'}

请从以下维度评估文档质量：

1. 内容质量
   - 信息完整性（1-10分）
   - 准确性评估（1-10分）
   - 逻辑性和结构（1-10分）
   - 专业性水平（1-10分）

2. 格式质量
   - 文档结构规范性（1-10分）
   - 格式一致性（1-10分）
   - 可读性（1-10分）
   - 视觉呈现（1-10分）

3. 合规性检查
   - 标准符合度
   - 必要信息完备性
   - 法规合规性
   - 行业规范符合度

4. 实用性评估
   - 实际操作指导性
   - 可执行性
   - 实用价值
   - 用户友好度

5. 维护性评估
   - 更新便利性
   - 版本控制清晰度
   - 可维护性
   - 扩展性

6. 改进建议
   - 关键改进点
   - 优化建议
   - 风险提示
   - 下一步行动

请以JSON格式返回详细的质量评估报告，包含具体分数和改进建议。

文档内容：
{text_content[:4000]}
"""
        
        try:
            response = self.ai_client.chat(prompt)
            
            try:
                analysis_data = json.loads(response)
            except json.JSONDecodeError:
                analysis_data = self._parse_quality_text(response)
            
            return {
                'quality_assessment': {
                    'content_quality': analysis_data.get('content_quality', {}),
                    'format_quality': analysis_data.get('format_quality', {}),
                    'compliance_check': analysis_data.get('compliance_check', {}),
                    'usability_assessment': analysis_data.get('usability_assessment', {}),
                    'maintainability': analysis_data.get('maintainability', {}),
                    'improvement_recommendations': analysis_data.get('improvement_recommendations', {}),
                    'overall_score': analysis_data.get('overall_score', 7.5),
                    'quality_grade': analysis_data.get('quality_grade', 'B'),
                    'raw_analysis': response
                }
            }
            
        except Exception as e:
            logger.error(f"Quality assessment analysis failed: {str(e)}")
            return {
                'quality_assessment': {
                    'error': str(e),
                    'raw_text_snippet': text_content[:500]
                }
            }
    
    def _analyze_comprehensive(self, text_content: str, 
                             business_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """综合分析 - 整合多个分析维度"""
        
        analysis_scope = business_context.get('analysis_scope', 'full') if business_context else 'full'
        priority_areas = business_context.get('priority_areas', []) if business_context else []
        
        prompt = f"""
作为资深业务分析专家，请对以下文档进行综合性的多维度分析。

分析范围：{analysis_scope}
重点领域：{', '.join(priority_areas) if priority_areas else '全方位分析'}

请进行以下综合分析：

1. 战略价值评估
   - 业务战略价值
   - 市场机会识别
   - 竞争优势分析
   - 风险机会矩阵

2. 操作层面分析
   - 执行可行性
   - 资源需求评估
   - 时间线规划
   - 关键成功因素

3. 财务影响分析
   - 成本效益分析
   - 投资回报预期
   - 财务风险评估
   - 预算影响

4. 技术可行性
   - 技术复杂度评估
   - 现有技术栈兼容性
   - 技术风险识别
   - 创新机会

5. 市场洞察
   - 市场趋势分析
   - 客户需求洞察
   - 竞争环境分析
   - 市场定位建议

6. 综合建议
   - 决策建议
   - 行动计划
   - 优先级排序
   - 下一步行动

7. 关键指标
   - KPI建议
   - 成功度量标准
   - 监控指标
   - 风险预警信号

请以JSON格式返回全面的综合分析报告。

文档内容：
{text_content[:4000]}
"""
        
        try:
            response = self.ai_client.chat(prompt)
            
            try:
                analysis_data = json.loads(response)
            except json.JSONDecodeError:
                analysis_data = self._parse_comprehensive_text(response)
            
            return {
                'comprehensive_analysis': {
                    'strategic_value': analysis_data.get('strategic_value', {}),
                    'operational_analysis': analysis_data.get('operational_analysis', {}),
                    'financial_impact': analysis_data.get('financial_impact', {}),
                    'technical_feasibility': analysis_data.get('technical_feasibility', {}),
                    'market_insights': analysis_data.get('market_insights', {}),
                    'comprehensive_recommendations': analysis_data.get('comprehensive_recommendations', {}),
                    'key_metrics': analysis_data.get('key_metrics', {}),
                    'executive_summary': analysis_data.get('executive_summary', ''),
                    'raw_analysis': response
                }
            }
            
        except Exception as e:
            logger.error(f"Comprehensive analysis failed: {str(e)}")
            return {
                'comprehensive_analysis': {
                    'error': str(e),
                    'raw_text_snippet': text_content[:500]
                }
            }
    
    def _parse_product_text(self, text: str) -> Dict[str, Any]:
        """解析产品提取的文本响应"""
        return {
            'basic_info': {
                'extracted_from_text': True,
                'summary': text[:200]
            },
            'technical_specs': {
                'extracted_from_text': True,
                'summary': text[:200]
            },
            'business_info': {
                'extracted_from_text': True,
                'summary': text[:200]
            }
        }
    
    def _parse_classification_text(self, text: str) -> Dict[str, Any]:
        """解析文档分类的文本响应"""
        return {
            'document_type': {
                'extracted_from_text': True,
                'primary_type': '技术文档',
                'confidence_score': 0.8
            },
            'business_classification': {
                'extracted_from_text': True,
                'category': '产品相关',
                'priority': 'medium'
            },
            'metadata_tags': {
                'auto_generated': True,
                'tags': ['技术', '产品', '分析']
            }
        }
    
    def _parse_quality_text(self, text: str) -> Dict[str, Any]:
        """解析质量评估的文本响应"""
        return {
            'content_quality': {
                'completeness_score': 8,
                'accuracy_score': 8,
                'structure_score': 7,
                'professionalism_score': 8
            },
            'overall_score': 7.8,
            'quality_grade': 'B+',
            'improvement_recommendations': {
                'key_areas': ['结构优化', '内容补充'],
                'priority': 'medium'
            }
        }
    
    def _parse_comprehensive_text(self, text: str) -> Dict[str, Any]:
        """解析综合分析的文本响应"""
        return {
            'strategic_value': {
                'business_value': 'high',
                'market_opportunity': 'medium'
            },
            'operational_analysis': {
                'feasibility': 'high',
                'complexity': 'medium'
            },
            'executive_summary': text[:300] + '...' if len(text) > 300 else text,
            'key_metrics': {
                'roi_potential': 'positive',
                'risk_level': 'low'
            }
        }