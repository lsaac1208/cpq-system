# -*- coding: utf-8 -*-
"""
置信度评分系统
基于多维度指标计算AI分析结果的置信度分数
"""
import re
import logging
from typing import Dict, Any, List, Tuple
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ConfidenceScorer:
    """置信度评分器"""
    
    def __init__(self):
        # 字段重要性权重
        self.field_weights = {
            'basic_info': {
                'name': 0.3,
                'code': 0.25,
                'category': 0.2,
                'base_price': 0.15,
                'description': 0.1
            },
            'specifications': 0.25,
            'features': 0.15,
            'application_scenarios': 0.1,
            'certificates': 0.1,
            'support_info': 0.05
        }
        
        # 数据质量评估规则
        self.quality_rules = {
            'completeness': {
                'required_fields': ['name', 'code', 'category'],
                'important_fields': ['base_price', 'description', 'specifications'],
                'optional_fields': ['features', 'application_scenarios', 'certificates']
            },
            'format_validation': {
                'code_pattern': r'^[A-Z0-9\-_]+$',
                'price_pattern': r'^\d+(\.\d{1,2})?$',
                'email_pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                'phone_pattern': r'^[\d\-\+\(\)\s]+$'
            },
            'content_quality': {
                'min_description_length': 10,
                'min_feature_count': 1,
                'min_spec_count': 3
            }
        }
        
        # 历史表现数据缓存
        self._historical_accuracy = None
        self._last_cache_update = None
        self._cache_duration = timedelta(hours=1)
    
    def calculate_comprehensive_confidence(self, extracted_data: Dict[str, Any], 
                                         document_info: Dict[str, Any],
                                         historical_context: Dict[str, Any] = None) -> Dict[str, float]:
        """
        计算综合置信度分数
        
        Args:
            extracted_data: 提取的产品数据
            document_info: 文档信息
            historical_context: 历史上下文数据
            
        Returns:
            Dict: 各维度置信度分数
        """
        try:
            # 1. 内容完整性评分
            completeness_score = self._calculate_completeness_score(extracted_data)
            
            # 2. 数据质量评分
            quality_score = self._calculate_quality_score(extracted_data)
            
            # 3. 格式一致性评分
            format_score = self._calculate_format_score(extracted_data)
            
            # 4. 文档源质量评分
            source_score = self._calculate_source_quality_score(document_info)
            
            # 5. 历史表现评分
            historical_score = self._calculate_historical_score(historical_context)
            
            # 6. 字段级置信度
            field_confidences = self._calculate_field_confidences(extracted_data)
            
            # 综合计算总体置信度
            overall_score = (
                completeness_score * 0.25 +
                quality_score * 0.25 +
                format_score * 0.2 +
                source_score * 0.15 +
                historical_score * 0.15
            )
            
            confidence_scores = {
                'overall': min(1.0, max(0.0, overall_score)),
                'completeness': completeness_score,
                'quality': quality_score,
                'format': format_score,
                'source': source_score,
                'historical': historical_score,
                **field_confidences
            }
            
            # 添加置信度等级
            confidence_scores['level'] = self._get_confidence_level(overall_score)
            confidence_scores['recommendations'] = self._generate_recommendations(confidence_scores)
            
            logger.info(f"Confidence calculated: overall={overall_score:.3f}, level={confidence_scores['level']}")
            return confidence_scores
            
        except Exception as e:
            logger.error(f"Confidence calculation failed: {str(e)}")
            return self._get_default_confidence_scores()
    
    def _calculate_completeness_score(self, extracted_data: Dict[str, Any]) -> float:
        """计算完整性分数"""
        total_score = 0.0
        max_score = 0.0
        
        basic_info = extracted_data.get('basic_info', {})
        
        # 检查必需字段
        for field in self.quality_rules['completeness']['required_fields']:
            max_score += 0.4
            if basic_info.get(field) and str(basic_info[field]).strip():
                total_score += 0.4
        
        # 检查重要字段
        for field in self.quality_rules['completeness']['important_fields']:
            max_score += 0.2
            if field == 'specifications':
                if extracted_data.get('specifications') and len(extracted_data['specifications']) > 0:
                    total_score += 0.2
            elif basic_info.get(field) and str(basic_info[field]).strip():
                total_score += 0.2
        
        # 检查可选字段
        for field in self.quality_rules['completeness']['optional_fields']:
            max_score += 0.1
            field_data = extracted_data.get(field)
            if field_data:
                if isinstance(field_data, list) and len(field_data) > 0:
                    total_score += 0.1
                elif isinstance(field_data, dict) and len(field_data) > 0:
                    total_score += 0.1
        
        return total_score / max_score if max_score > 0 else 0.0
    
    def _calculate_quality_score(self, extracted_data: Dict[str, Any]) -> float:
        """计算数据质量分数"""
        quality_indicators = []
        
        basic_info = extracted_data.get('basic_info', {})
        
        # 描述质量
        description = basic_info.get('description', '')
        if len(description) >= self.quality_rules['content_quality']['min_description_length']:
            quality_indicators.append(0.8)
        else:
            quality_indicators.append(0.3)
        
        # 规格数量和质量
        specifications = extracted_data.get('specifications', {})
        spec_count = len(specifications)
        if spec_count >= self.quality_rules['content_quality']['min_spec_count']:
            # 检查规格的详细程度
            detailed_specs = sum(1 for spec in specifications.values() 
                               if isinstance(spec, dict) and spec.get('value') and spec.get('unit'))
            spec_quality = min(1.0, detailed_specs / spec_count)
            quality_indicators.append(spec_quality)
        else:
            quality_indicators.append(0.2)
        
        # 特性质量
        features = extracted_data.get('features', [])
        if len(features) >= self.quality_rules['content_quality']['min_feature_count']:
            # 检查特性的详细程度
            detailed_features = sum(1 for feature in features 
                                  if isinstance(feature, dict) and 
                                  feature.get('title') and feature.get('description'))
            feature_quality = min(1.0, detailed_features / len(features)) if features else 0
            quality_indicators.append(feature_quality)
        else:
            quality_indicators.append(0.4)
        
        # 数值合理性检查
        base_price = basic_info.get('base_price', 0)
        if isinstance(base_price, (int, float)) and base_price > 0:
            # 价格在合理范围内
            if 1 <= base_price <= 1000000:  # 1元到100万元
                quality_indicators.append(0.9)
            else:
                quality_indicators.append(0.5)
        else:
            quality_indicators.append(0.2)
        
        return np.mean(quality_indicators) if quality_indicators else 0.0
    
    def _calculate_format_score(self, extracted_data: Dict[str, Any]) -> float:
        """计算格式一致性分数"""
        format_scores = []
        
        basic_info = extracted_data.get('basic_info', {})
        validation_rules = self.quality_rules['format_validation']
        
        # 产品代码格式
        code = basic_info.get('code', '')
        if code:
            if re.match(validation_rules['code_pattern'], code):
                format_scores.append(1.0)
            else:
                format_scores.append(0.6)  # 有内容但格式不标准
        else:
            format_scores.append(0.0)
        
        # 价格格式
        base_price = basic_info.get('base_price')
        if base_price is not None:
            try:
                price_float = float(base_price)
                if price_float >= 0:
                    format_scores.append(1.0)
                else:
                    format_scores.append(0.3)
            except (ValueError, TypeError):
                format_scores.append(0.0)
        else:
            format_scores.append(0.0)
        
        # 联系信息格式
        support_info = extracted_data.get('support_info', {})
        contact_info = support_info.get('contact_info', {})
        
        # 邮箱格式
        emails = [contact_info.get('sales_email'), contact_info.get('support_email')]
        email_scores = []
        for email in emails:
            if email:
                if re.match(validation_rules['email_pattern'], email):
                    email_scores.append(1.0)
                else:
                    email_scores.append(0.3)
        
        if email_scores:
            format_scores.append(np.mean(email_scores))
        
        # 电话格式
        phones = [contact_info.get('sales_phone'), contact_info.get('support_phone')]
        phone_scores = []
        for phone in phones:
            if phone:
                if re.match(validation_rules['phone_pattern'], phone):
                    phone_scores.append(1.0)
                else:
                    phone_scores.append(0.5)
        
        if phone_scores:
            format_scores.append(np.mean(phone_scores))
        
        return np.mean(format_scores) if format_scores else 0.5
    
    def _calculate_source_quality_score(self, document_info: Dict[str, Any]) -> float:
        """计算文档源质量分数"""
        quality_factors = []
        
        # 文档类型质量
        doc_type = document_info.get('type', '').lower()
        type_scores = {
            'pdf': 0.9,  # PDF通常结构化程度高
            'docx': 0.8,  # Word文档结构化中等
            'txt': 0.6,   # 纯文本结构化程度低
            'png': 0.4,   # 图片需要OCR，准确度较低
            'jpg': 0.4,
            'jpeg': 0.4
        }
        quality_factors.append(type_scores.get(doc_type, 0.5))
        
        # 文档大小合理性
        doc_size = document_info.get('size', 0)
        if 1000 <= doc_size <= 10000000:  # 1KB到10MB
            quality_factors.append(0.8)
        elif doc_size < 1000:
            quality_factors.append(0.3)  # 太小可能信息不足
        else:
            quality_factors.append(0.6)  # 太大可能有很多无关信息
        
        # 文本长度和单词数
        text_length = document_info.get('text_length', 0)
        word_count = document_info.get('word_count', 0)
        
        if text_length > 100 and word_count > 20:
            quality_factors.append(0.8)
        elif text_length > 50:
            quality_factors.append(0.6)
        else:
            quality_factors.append(0.3)
        
        # 文档是否被截断
        if document_info.get('truncated', False):
            quality_factors.append(0.4)
        else:
            quality_factors.append(0.8)
        
        return np.mean(quality_factors)
    
    def _calculate_historical_score(self, historical_context: Dict[str, Any] = None) -> float:
        """计算基于历史表现的分数"""
        if not historical_context:
            return 0.7  # 默认中等分数
        
        # 历史准确率
        historical_accuracy = historical_context.get('accuracy', 0.7)
        
        # 相似文档的历史表现
        similar_docs_accuracy = historical_context.get('similar_docs_accuracy', 0.7)
        
        # 用户修正率（越低越好）
        modification_rate = historical_context.get('modification_rate', 0.3)
        modification_score = max(0.0, 1.0 - modification_rate)
        
        # 综合历史分数
        historical_score = (
            historical_accuracy * 0.4 +
            similar_docs_accuracy * 0.4 +
            modification_score * 0.2
        )
        
        return historical_score
    
    def _calculate_field_confidences(self, extracted_data: Dict[str, Any]) -> Dict[str, float]:
        """计算字段级置信度"""
        field_confidences = {}
        
        # 基础信息字段
        basic_info = extracted_data.get('basic_info', {})
        for field, weight in self.field_weights['basic_info'].items():
            confidence = self._calculate_single_field_confidence(basic_info.get(field), field)
            field_confidences[f'basic_info_{field}'] = confidence
        
        # 计算基础信息整体置信度
        basic_info_scores = [score for key, score in field_confidences.items() 
                            if key.startswith('basic_info_')]
        field_confidences['basic_info'] = np.mean(basic_info_scores) if basic_info_scores else 0.0
        
        # 规格信息
        specifications = extracted_data.get('specifications', {})
        if specifications:
            spec_scores = []
            for spec_name, spec_data in specifications.items():
                spec_confidence = self._calculate_specification_confidence(spec_data)
                spec_scores.append(spec_confidence)
            field_confidences['specifications'] = np.mean(spec_scores)
        else:
            field_confidences['specifications'] = 0.0
        
        # 产品特性
        features = extracted_data.get('features', [])
        if features:
            feature_scores = []
            for feature in features:
                feature_confidence = self._calculate_feature_confidence(feature)
                feature_scores.append(feature_confidence)
            field_confidences['features'] = np.mean(feature_scores)
        else:
            field_confidences['features'] = 0.0
        
        return field_confidences
    
    def _calculate_single_field_confidence(self, field_value: Any, field_name: str) -> float:
        """计算单个字段的置信度"""
        if not field_value or (isinstance(field_value, str) and not field_value.strip()):
            return 0.0
        
        confidence = 0.5  # 基础分数
        
        if field_name == 'name':
            # 产品名称评估
            name_str = str(field_value)
            if len(name_str) > 3:
                confidence += 0.2
            if len(name_str) > 10:
                confidence += 0.2
            if any(char.isdigit() for char in name_str):  # 包含型号数字
                confidence += 0.1
                
        elif field_name == 'code':
            # 产品代码评估
            code_str = str(field_value)
            if re.match(r'^[A-Z0-9\-_]+$', code_str):
                confidence += 0.3
            if 3 <= len(code_str) <= 20:
                confidence += 0.2
                
        elif field_name == 'category':
            # 分类评估
            category_str = str(field_value)
            if len(category_str) > 2:
                confidence += 0.3
            # 检查是否为常见分类
            common_categories = ['变压器', '开关设备', '保护装置', '测量仪表', '控制设备']
            if any(cat in category_str for cat in common_categories):
                confidence += 0.2
                
        elif field_name == 'base_price':
            # 价格评估
            try:
                price = float(field_value)
                if 1 <= price <= 1000000:
                    confidence += 0.3
                if price % 1 == 0 or len(str(price).split('.')[-1]) <= 2:  # 整数或最多2位小数
                    confidence += 0.2
            except (ValueError, TypeError):
                confidence = 0.1
                
        elif field_name == 'description':
            # 描述评估
            desc_str = str(field_value)
            if len(desc_str) > 10:
                confidence += 0.2
            if len(desc_str) > 50:
                confidence += 0.1
            if len(desc_str) > 100:
                confidence += 0.1
        
        return min(1.0, confidence)
    
    def _calculate_specification_confidence(self, spec_data: Dict[str, Any]) -> float:
        """计算规格的置信度"""
        if not isinstance(spec_data, dict):
            return 0.3
        
        confidence = 0.4  # 基础分数
        
        # 有值
        if spec_data.get('value'):
            confidence += 0.3
        
        # 有单位
        if spec_data.get('unit'):
            confidence += 0.2
        
        # 有描述
        if spec_data.get('description'):
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _calculate_feature_confidence(self, feature_data: Dict[str, Any]) -> float:
        """计算特性的置信度"""
        if not isinstance(feature_data, dict):
            return 0.2
        
        confidence = 0.3  # 基础分数
        
        # 有标题
        if feature_data.get('title'):
            confidence += 0.3
        
        # 有描述
        if feature_data.get('description'):
            description = feature_data['description']
            if len(str(description)) > 10:
                confidence += 0.3
            if len(str(description)) > 30:
                confidence += 0.1
        
        return min(1.0, confidence)
    
    def _get_confidence_level(self, overall_score: float) -> str:
        """获取置信度等级"""
        if overall_score >= 0.8:
            return 'high'
        elif overall_score >= 0.6:
            return 'medium'
        elif overall_score >= 0.4:
            return 'low'
        else:
            return 'very_low'
    
    def _generate_recommendations(self, confidence_scores: Dict[str, float]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if confidence_scores['overall'] < 0.6:
            recommendations.append("总体置信度较低，建议仔细检查所有提取的信息")
        
        if confidence_scores['completeness'] < 0.7:
            recommendations.append("信息完整性不足，建议补充缺失的关键字段")
        
        if confidence_scores['quality'] < 0.6:
            recommendations.append("数据质量有待改善，建议核实规格参数和特性描述")
        
        if confidence_scores['format'] < 0.7:
            recommendations.append("格式规范性需要改进，检查代码、价格、联系方式等格式")
        
        if confidence_scores.get('basic_info', 0) < 0.7:
            recommendations.append("基础产品信息需要完善，重点检查名称、代码、分类")
        
        if confidence_scores.get('specifications', 0) < 0.6:
            recommendations.append("技术规格信息不够详细，建议补充参数值和单位")
        
        return recommendations
    
    def _get_default_confidence_scores(self) -> Dict[str, float]:
        """获取默认置信度分数"""
        return {
            'overall': 0.5,
            'completeness': 0.5,
            'quality': 0.5,
            'format': 0.5,
            'source': 0.5,
            'historical': 0.5,
            'basic_info': 0.5,
            'specifications': 0.5,
            'features': 0.5,
            'level': 'medium',
            'recommendations': ["无法计算置信度，建议人工检查所有信息"]
        }
    
    def update_historical_performance(self, analysis_id: int, user_modifications: Dict[str, Any],
                                    final_accuracy: float):
        """更新历史表现数据"""
        try:
            # 这里可以实现学习逻辑，基于用户修正更新模型
            logger.info(f"Updated historical performance for analysis {analysis_id}: accuracy={final_accuracy}")
        except Exception as e:
            logger.error(f"Failed to update historical performance: {str(e)}")