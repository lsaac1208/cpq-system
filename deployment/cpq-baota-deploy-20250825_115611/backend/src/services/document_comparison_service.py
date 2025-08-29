# -*- coding: utf-8 -*-
"""
文档对比分析服务
提供多文档智能对比分析功能
"""
import os
import json
import time
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from .ai_analyzer import AIAnalyzer
from .openai_client import OpenAIClient
from src.models.ai_analysis import AIAnalysisRecord
from src.models.document_comparison import (
    DocumentComparison, ComparisonDocument, ComparisonResult, 
    ComparisonTemplate, ComparisonStatus, ComparisonType
)

logger = logging.getLogger(__name__)

@dataclass
class ComparisonConfig:
    """对比配置"""
    comparison_type: str = 'product_specs'
    focus_areas: List[str] = None
    include_similarities: bool = True
    include_differences: bool = True
    min_confidence_threshold: float = 0.6
    importance_threshold: float = 0.5
    max_results_per_category: int = 50
    enable_insights: bool = True
    custom_fields: List[str] = None

@dataclass
class DocumentInfo:
    """文档信息"""
    analysis_record_id: int
    label: str
    role: str = 'secondary'  # primary/secondary/reference
    weight: float = 1.0

class DocumentComparisonService:
    """文档对比分析服务"""
    
    def __init__(self):
        self.openai_client = OpenAIClient()
        self.ai_analyzer = AIAnalyzer()
        
        # 对比配置
        self.max_documents = 10  # 最多对比10个文档
        self.max_processing_time = 1800  # 30分钟超时
        
        # 内置对比模板
        self.built_in_templates = {
            'product_specs': {
                'name': '产品规格对比',
                'focus_areas': ['价格', '规格', '功能', '性能', '尺寸', '重量', '材质', '颜色', '品牌'],
                'comparison_prompt': self._get_product_specs_prompt(),
                'output_categories': ['价格差异', '规格对比', '功能比较', '性能分析', '物理属性']
            },
            'price_analysis': {
                'name': '价格分析对比',
                'focus_areas': ['价格', '性价比', '成本', '优惠', '折扣', '套餐'],
                'comparison_prompt': self._get_price_analysis_prompt(),
                'output_categories': ['价格对比', '性价比分析', '优惠政策', '成本效益']
            },
            'feature_matrix': {
                'name': '功能特性矩阵',
                'focus_areas': ['功能', '特性', '能力', '支持', '兼容性', '限制'],
                'comparison_prompt': self._get_feature_matrix_prompt(),
                'output_categories': ['核心功能', '扩展特性', '技术支持', '兼容性分析']
            }
        }
    
    def create_comparison(self, user_id: int, documents: List[DocumentInfo], 
                         config: ComparisonConfig, name: str = None, 
                         description: str = None) -> str:
        """
        创建文档对比分析
        
        Args:
            user_id: 用户ID
            documents: 文档列表
            config: 对比配置
            name: 对比名称
            description: 对比描述
            
        Returns:
            comparison_id: 对比分析ID
        """
        try:
            # 验证输入
            if not documents or len(documents) < 2:
                raise ValueError("至少需要2个文档进行对比")
            
            if len(documents) > self.max_documents:
                raise ValueError(f"最多支持{self.max_documents}个文档对比")
            
            # 验证文档存在
            for doc in documents:
                record = AIAnalysisRecord.query.get(doc.analysis_record_id)
                if not record:
                    raise ValueError(f"文档记录不存在: {doc.analysis_record_id}")
            
            # 生成对比ID
            comparison_id = f"cmp_{int(time.time())}_{str(uuid.uuid4())[:8]}"
            
            # 创建对比记录
            comparison = DocumentComparison()
            comparison.comparison_id = comparison_id
            comparison.user_id = user_id
            comparison.name = name or f"文档对比分析 {datetime.now().strftime('%Y%m%d_%H%M%S')}"
            comparison.description = description
            # 查找匹配的枚举值
            comparison_type = None
            for ct in ComparisonType:
                if ct.value == config.comparison_type:
                    comparison_type = ct
                    break
            
            comparison.comparison_type = comparison_type or ComparisonType.PRODUCT_SPECS
            comparison.document_count = len(documents)
            comparison.comparison_settings = {
                'focus_areas': config.focus_areas or [],
                'include_similarities': config.include_similarities,
                'include_differences': config.include_differences,
                'min_confidence_threshold': config.min_confidence_threshold,
                'importance_threshold': config.importance_threshold,
                'max_results_per_category': config.max_results_per_category,
                'enable_insights': config.enable_insights,
                'custom_fields': config.custom_fields or []
            }
            
            # 设置主文档
            primary_doc = next((d for d in documents if d.role == 'primary'), documents[0])
            comparison.primary_document_id = primary_doc.analysis_record_id
            
            comparison.save()
            
            # 创建文档关联记录
            for i, doc in enumerate(documents):
                comp_doc = ComparisonDocument()
                comp_doc.comparison_id = comparison_id
                comp_doc.analysis_record_id = doc.analysis_record_id
                comp_doc.document_role = doc.role
                comp_doc.document_label = doc.label
                comp_doc.display_order = i
                comp_doc.comparison_weight = doc.weight
                comp_doc.save()
            
            logger.info(f"Document comparison created: {comparison_id} with {len(documents)} documents")
            return comparison_id
            
        except Exception as e:
            logger.error(f"Error creating document comparison: {str(e)}")
            raise
    
    def start_comparison(self, comparison_id: str) -> bool:
        """
        启动对比分析
        
        Args:
            comparison_id: 对比分析ID
            
        Returns:
            bool: 是否启动成功
        """
        try:
            comparison = DocumentComparison.query.filter_by(comparison_id=comparison_id).first()
            if not comparison:
                raise ValueError(f"对比分析不存在: {comparison_id}")
            
            if comparison.status != ComparisonStatus.PENDING:
                raise ValueError(f"对比分析状态错误: {comparison.status.value}")
            
            # 启动异步处理
            comparison.start_processing()
            comparison.save()
            
            # 在后台线程中处理
            executor = ThreadPoolExecutor(max_workers=1)
            executor.submit(self._process_comparison, comparison_id)
            
            logger.info(f"Document comparison started: {comparison_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting comparison {comparison_id}: {str(e)}")
            return False
    
    def _process_comparison(self, comparison_id: str):
        """处理对比分析（后台任务）"""
        try:
            comparison = DocumentComparison.query.filter_by(comparison_id=comparison_id).first()
            if not comparison:
                return
            
            # 获取参与对比的文档
            comp_docs = ComparisonDocument.query.filter_by(comparison_id=comparison_id)\
                                              .order_by(ComparisonDocument.display_order).all()
            
            documents_data = []
            for comp_doc in comp_docs:
                record = AIAnalysisRecord.query.get(comp_doc.analysis_record_id)
                if record:
                    # 兼容性处理 - AIAnalysisRecord的字段名可能不同
                    content = getattr(record, 'original_text', None) or getattr(record, 'original_content', '')
                    analysis = getattr(record, 'extracted_data', None) or getattr(record, 'analysis_result', {})
                    confidence = 0
                    
                    if hasattr(record, 'confidence_scores') and record.confidence_scores:
                        confidence = record.confidence_scores.get('overall', 0)
                    elif hasattr(record, 'confidence_score'):
                        confidence = record.confidence_score or 0
                    
                    # 只有当有内容时才添加
                    if content and analysis:
                        documents_data.append({
                            'id': comp_doc.analysis_record_id,
                            'label': comp_doc.document_label,
                            'role': comp_doc.document_role,
                            'weight': comp_doc.comparison_weight,
                            'content': content,
                            'analysis': analysis,
                            'confidence': confidence
                        })
            
            if len(documents_data) < 2:
                raise ValueError("有效文档不足，无法进行对比")
            
            # 获取对比模板和配置
            template = self.built_in_templates.get(
                comparison.comparison_type.value, 
                self.built_in_templates['product_specs']
            )
            
            settings = comparison.comparison_settings or {}
            
            # 执行对比分析
            comparison_results = self._perform_comparison_analysis(
                documents_data, template, settings
            )
            
            # 保存结果
            self._save_comparison_results(comparison_id, comparison_results)
            
            # 更新对比状态
            comparison.complete_processing(comparison_results.get('summary', {}))
            comparison.save()
            
            logger.info(f"Document comparison completed: {comparison_id}")
            
        except Exception as e:
            logger.error(f"Error processing comparison {comparison_id}: {str(e)}")
            
            # 更新失败状态
            try:
                comparison = DocumentComparison.query.filter_by(comparison_id=comparison_id).first()
                if comparison:
                    comparison.complete_processing(error_message=str(e))
                    comparison.save()
            except:
                pass
    
    def _perform_comparison_analysis(self, documents_data: List[Dict], 
                                   template: Dict, settings: Dict) -> Dict[str, Any]:
        """执行对比分析"""
        try:
            # 构建对比提示词
            comparison_prompt = self._build_comparison_prompt(
                documents_data, template, settings
            )
            
            # 调用AI进行对比分析
            response = self.openai_client.chat_completion([
                {
                    "role": "system", 
                    "content": "你是一个专业的产品分析师，擅长进行多文档对比分析，能够准确识别产品规格的差异和相似性。"
                },
                {
                    "role": "user",
                    "content": comparison_prompt
                }
            ])
            
            if not response:
                raise ValueError("AI分析服务无响应")
            
            # 解析分析结果
            analysis_result = self._parse_comparison_result(response)
            
            # 计算置信度和重要性分数
            analysis_result = self._calculate_scores(analysis_result, documents_data)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error performing comparison analysis: {str(e)}")
            raise
    
    def _build_comparison_prompt(self, documents_data: List[Dict], 
                               template: Dict, settings: Dict) -> str:
        """构建对比分析提示词"""
        focus_areas = settings.get('focus_areas', template.get('focus_areas', []))
        include_similarities = settings.get('include_similarities', True)
        include_differences = settings.get('include_differences', True)
        
        prompt = f"""请对以下{len(documents_data)}个文档进行{template['name']}对比分析：

**对比重点领域：**
{', '.join(focus_areas) if focus_areas else '全面对比'}

**文档内容：**
"""
        
        # 添加文档内容
        for i, doc in enumerate(documents_data, 1):
            prompt += f"\n**文档{i} ({doc['label']})：**\n"
            prompt += f"原始内容：\n{doc['content'][:2000]}...\n"
            if doc['analysis']:
                prompt += f"已有分析结果：\n{json.dumps(doc['analysis'], ensure_ascii=False, indent=2)[:1000]}...\n"
        
        prompt += f"""

**分析要求：**
1. 请使用JSON格式返回分析结果
2. 结果结构如下：
{{
    "summary": {{
        "total_differences": 数字,
        "significant_differences": 数字,
        "similarities_count": 数字,
        "confidence_score": 0.0-1.0
    }},
    "differences": [
        {{
            "category": "分类",
            "subcategory": "子分类", 
            "title": "差异标题",
            "description": "差异描述",
            "importance_score": 0.0-1.0,
            "confidence_score": 0.0-1.0,
            "involved_documents": [文档ID列表],
            "details": {{
                "field": "字段名",
                "values": {{"doc1_label": "值1", "doc2_label": "值2"}},
                "analysis": "分析说明"
            }}
        }}
    ],
    "similarities": [
        {{
            "category": "分类",
            "title": "相似点标题", 
            "description": "相似点描述",
            "confidence_score": 0.0-1.0,
            "involved_documents": [文档ID列表],
            "common_value": "共同值"
        }}
    ],
    "insights": [
        {{
            "type": "insight类型",
            "title": "洞察标题",
            "description": "洞察描述", 
            "actionable": true/false,
            "priority": "high/medium/low"
        }}
    ]
}}

3. 重点关注：{', '.join(focus_areas) if focus_areas else '产品的核心属性和规格'}
4. 差异分析：{'包含' if include_differences else '不包含'}
5. 相似性分析：{'包含' if include_similarities else '不包含'}
6. 确保分析结果准确、客观、有价值
7. 重要性评分要合理，0.8以上为高重要性
8. 置信度要基于信息明确程度判断

请开始分析："""
        
        return prompt
    
    def _parse_comparison_result(self, ai_response: str) -> Dict[str, Any]:
        """解析AI对比结果"""
        try:
            # 尝试解析JSON
            if '```json' in ai_response:
                json_start = ai_response.find('```json') + 7
                json_end = ai_response.find('```', json_start)
                json_content = ai_response[json_start:json_end].strip()
            else:
                json_content = ai_response.strip()
            
            result = json.loads(json_content)
            
            # 验证结果结构
            if not isinstance(result, dict):
                raise ValueError("结果不是有效的字典格式")
            
            # 确保必要字段存在
            if 'summary' not in result:
                result['summary'] = {}
            
            if 'differences' not in result:
                result['differences'] = []
            
            if 'similarities' not in result:
                result['similarities'] = []
            
            if 'insights' not in result:
                result['insights'] = []
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            logger.debug(f"AI Response: {ai_response[:500]}...")
            
            # 返回基础结构
            return {
                'summary': {
                    'total_differences': 0,
                    'significant_differences': 0,
                    'similarities_count': 0,
                    'confidence_score': 0.0
                },
                'differences': [],
                'similarities': [],
                'insights': [],
                'parse_error': str(e)
            }
    
    def _calculate_scores(self, analysis_result: Dict, documents_data: List[Dict]) -> Dict[str, Any]:
        """计算置信度和重要性分数"""
        try:
            # 基于文档数据质量调整分数
            avg_doc_confidence = sum(doc.get('confidence', 0) for doc in documents_data) / len(documents_data)
            
            # 调整总体置信度
            summary = analysis_result.get('summary', {})
            if 'confidence_score' in summary:
                # 结合文档置信度和分析置信度
                summary['confidence_score'] = (summary['confidence_score'] + avg_doc_confidence) / 2
            
            # 调整个别结果的置信度
            for diff in analysis_result.get('differences', []):
                if 'confidence_score' in diff:
                    diff['confidence_score'] = min(diff['confidence_score'], avg_doc_confidence + 0.2)
            
            for sim in analysis_result.get('similarities', []):
                if 'confidence_score' in sim:
                    sim['confidence_score'] = min(sim['confidence_score'], avg_doc_confidence + 0.1)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error calculating scores: {str(e)}")
            return analysis_result
    
    def _save_comparison_results(self, comparison_id: str, results: Dict[str, Any]):
        """保存对比结果"""
        try:
            # 保存差异结果
            for diff in results.get('differences', []):
                result = ComparisonResult()
                result.comparison_id = comparison_id
                result.result_type = 'difference'
                result.category = diff.get('category', '')
                result.subcategory = diff.get('subcategory', '')
                result.title = diff.get('title', '')
                result.description = diff.get('description', '')
                result.details = diff.get('details', {})
                result.importance_score = diff.get('importance_score', 0.0)
                result.confidence_score = diff.get('confidence_score', 0.0)
                result.involved_documents = diff.get('involved_documents', [])
                result.save()
            
            # 保存相似性结果
            for sim in results.get('similarities', []):
                result = ComparisonResult()
                result.comparison_id = comparison_id
                result.result_type = 'similarity'
                result.category = sim.get('category', '')
                result.title = sim.get('title', '')
                result.description = sim.get('description', '')
                result.details = {'common_value': sim.get('common_value', '')}
                result.confidence_score = sim.get('confidence_score', 0.0)
                result.involved_documents = sim.get('involved_documents', [])
                result.save()
            
            # 保存洞察结果
            for insight in results.get('insights', []):
                result = ComparisonResult()
                result.comparison_id = comparison_id
                result.result_type = 'insight'
                result.category = insight.get('type', '')
                result.title = insight.get('title', '')
                result.description = insight.get('description', '')
                result.details = {
                    'actionable': insight.get('actionable', False),
                    'priority': insight.get('priority', 'medium')
                }
                result.importance_score = {'high': 0.9, 'medium': 0.6, 'low': 0.3}.get(
                    insight.get('priority', 'medium'), 0.6)
                result.save()
            
            logger.info(f"Saved comparison results for {comparison_id}")
            
        except Exception as e:
            logger.error(f"Error saving comparison results: {str(e)}")
            raise
    
    def get_comparison_results(self, comparison_id: str) -> Dict[str, Any]:
        """获取对比分析结果"""
        try:
            comparison = DocumentComparison.query.filter_by(comparison_id=comparison_id).first()
            if not comparison:
                raise ValueError(f"对比分析不存在: {comparison_id}")
            
            # 获取文档信息
            comp_docs = ComparisonDocument.query.filter_by(comparison_id=comparison_id)\
                                              .order_by(ComparisonDocument.display_order).all()
            
            documents = []
            for comp_doc in comp_docs:
                record = AIAnalysisRecord.query.get(comp_doc.analysis_record_id)
                if record:
                    documents.append({
                        **comp_doc.to_dict(),
                        'filename': record.filename,
                        'file_type': record.file_type,
                        'upload_time': record.created_at.isoformat() if record.created_at else None
                    })
            
            # 获取结果
            differences = ComparisonResult.get_comparison_results(comparison_id, 'difference')
            similarities = ComparisonResult.get_comparison_results(comparison_id, 'similarity')
            insights = ComparisonResult.get_comparison_results(comparison_id, 'insight')
            
            return {
                'comparison': comparison.to_dict(),
                'documents': documents,
                'results': {
                    'differences': [r.to_dict() for r in differences],
                    'similarities': [r.to_dict() for r in similarities],
                    'insights': [r.to_dict() for r in insights]
                },
                'summary': {
                    'total_differences': len(differences),
                    'significant_differences': len([d for d in differences if d.importance_score >= 0.7]),
                    'similarities_count': len(similarities),
                    'insights_count': len(insights)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting comparison results {comparison_id}: {str(e)}")
            raise
    
    def cancel_comparison(self, comparison_id: str, reason: str = None) -> bool:
        """取消对比分析"""
        try:
            comparison = DocumentComparison.query.filter_by(comparison_id=comparison_id).first()
            if not comparison:
                return False
            
            if comparison.status not in [ComparisonStatus.PENDING, ComparisonStatus.PROCESSING]:
                return False
            
            comparison.cancel_processing(reason)
            comparison.save()
            
            logger.info(f"Comparison cancelled: {comparison_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling comparison {comparison_id}: {str(e)}")
            return False
    
    # 内置提示词模板
    def _get_product_specs_prompt(self):
        return "专注于产品规格、价格、功能、性能等核心属性的对比分析"
    
    def _get_price_analysis_prompt(self):
        return "专注于价格、性价比、优惠政策等价格相关的对比分析"
    
    def _get_feature_matrix_prompt(self):
        return "专注于功能特性、能力支持、兼容性等功能相关的对比分析"