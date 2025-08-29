# -*- coding: utf-8 -*-
"""
用户修正学习引擎
基于用户修正行为来改进AI分析准确性
"""
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ModificationPattern:
    """修正模式数据结构"""
    field_path: str
    original_value: Any
    corrected_value: Any
    frequency: int
    confidence_improvement: float
    document_type: str
    user_id: int
    created_at: datetime

class LearningEngine:
    """用户修正学习引擎"""
    
    def __init__(self):
        # 学习参数
        self.learning_config = {
            'min_pattern_frequency': 3,  # 最小模式频率
            'confidence_threshold': 0.7,  # 置信度阈值
            'learning_window_days': 90,  # 学习窗口天数
            'max_patterns_per_field': 10,  # 每个字段最大模式数
            'decay_factor': 0.95  # 时间衰减因子
        }
        
        # 字段类型分类
        self.field_categories = {
            'text_fields': ['name', 'description', 'category'],
            'numeric_fields': ['base_price', 'numeric_value'],
            'code_fields': ['code'],
            'technical_fields': ['specifications', 'features'],
            'contact_fields': ['sales_email', 'support_email', 'sales_phone', 'support_phone']
        }
        
        # 修正模式缓存
        self._pattern_cache = None
        self._cache_expiry = None
        self._cache_duration = timedelta(hours=1)
    
    def learn_from_modifications(self, analysis_record_id: int, 
                                original_data: Dict[str, Any], 
                                final_data: Dict[str, Any],
                                user_modifications: Dict[str, Any]) -> Dict[str, Any]:
        """
        从用户修正中学习
        
        Args:
            analysis_record_id: 分析记录ID
            original_data: 原始AI提取数据
            final_data: 最终确认数据
            user_modifications: 用户修正记录
            
        Returns:
            Dict: 学习结果和模式识别
        """
        try:
            # 识别修正模式
            modification_patterns = self._identify_modification_patterns(
                original_data, final_data, user_modifications
            )
            
            # 分析修正原因
            modification_reasons = self._analyze_modification_reasons(
                modification_patterns, original_data
            )
            
            # 更新学习模式库
            learned_patterns = self._update_pattern_library(
                modification_patterns, analysis_record_id
            )
            
            # 生成改进建议
            improvement_suggestions = self._generate_improvement_suggestions(
                modification_patterns, modification_reasons
            )
            
            learning_result = {
                'patterns_identified': len(modification_patterns),
                'learned_patterns': learned_patterns,
                'modification_reasons': modification_reasons,
                'improvement_suggestions': improvement_suggestions,
                'learning_confidence': self._calculate_learning_confidence(modification_patterns)
            }
            
            logger.info(f"Learning completed for record {analysis_record_id}: "
                       f"{len(modification_patterns)} patterns identified")
            
            return learning_result
            
        except Exception as e:
            logger.error(f"Learning from modifications failed: {str(e)}")
            return {
                'patterns_identified': 0,
                'learned_patterns': [],
                'modification_reasons': {},
                'improvement_suggestions': [],
                'learning_confidence': 0.0,
                'error': str(e)
            }
    
    def get_personalized_hints(self, user_id: int, document_type: str, 
                              extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取个性化提示和预测修正
        
        Args:
            user_id: 用户ID
            document_type: 文档类型
            extracted_data: 提取的数据
            
        Returns:
            Dict: 个性化提示和建议
        """
        try:
            # 获取用户历史修正模式
            user_patterns = self._get_user_patterns(user_id, document_type)
            
            # 预测可能的修正
            predicted_modifications = self._predict_modifications(
                extracted_data, user_patterns
            )
            
            # 生成个性化提示
            personalized_hints = self._generate_personalized_hints(
                user_patterns, predicted_modifications
            )
            
            # 计算字段置信度调整
            confidence_adjustments = self._calculate_confidence_adjustments(
                extracted_data, user_patterns
            )
            
            return {
                'predicted_modifications': predicted_modifications,
                'personalized_hints': personalized_hints,
                'confidence_adjustments': confidence_adjustments,
                'pattern_count': len(user_patterns),
                'recommendations': self._generate_user_recommendations(user_patterns)
            }
            
        except Exception as e:
            logger.error(f"Failed to get personalized hints: {str(e)}")
            return {
                'predicted_modifications': {},
                'personalized_hints': [],
                'confidence_adjustments': {},
                'pattern_count': 0,
                'recommendations': []
            }
    
    def optimize_extraction_prompt(self, document_type: str, 
                                  category: str = None) -> Dict[str, Any]:
        """
        基于学习模式优化提取prompt
        
        Args:
            document_type: 文档类型
            category: 产品分类
            
        Returns:
            Dict: 优化的prompt配置
        """
        try:
            # 获取相关修正模式
            relevant_patterns = self._get_relevant_patterns(document_type, category)
            
            # 分析常见错误
            common_errors = self._analyze_common_errors(relevant_patterns)
            
            # 生成优化指导
            optimization_rules = self._generate_optimization_rules(common_errors)
            
            # 构建优化的prompt片段
            prompt_enhancements = self._build_prompt_enhancements(
                optimization_rules, relevant_patterns
            )
            
            return {
                'prompt_enhancements': prompt_enhancements,
                'common_errors': common_errors,
                'optimization_rules': optimization_rules,
                'pattern_confidence': self._calculate_pattern_confidence(relevant_patterns),
                'applicability_score': self._calculate_applicability_score(
                    relevant_patterns, document_type, category
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to optimize extraction prompt: {str(e)}")
            return {
                'prompt_enhancements': {},
                'common_errors': [],
                'optimization_rules': [],
                'pattern_confidence': 0.0,
                'applicability_score': 0.0
            }
    
    def _identify_modification_patterns(self, original_data: Dict[str, Any],
                                      final_data: Dict[str, Any],
                                      user_modifications: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别修正模式"""
        patterns = []
        
        # 遍历所有修正
        for field_path, modification_info in user_modifications.items():
            original_value = self._get_nested_value(original_data, field_path)
            final_value = self._get_nested_value(final_data, field_path)
            
            pattern = {
                'field_path': field_path,
                'field_category': self._categorize_field(field_path),
                'original_value': original_value,
                'final_value': final_value,
                'modification_type': self._classify_modification_type(original_value, final_value),
                'value_difference': self._calculate_value_difference(original_value, final_value),
                'timestamp': datetime.now()
            }
            
            patterns.append(pattern)
        
        return patterns
    
    def _analyze_modification_reasons(self, patterns: List[Dict[str, Any]], 
                                    original_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """分析修正原因"""
        reasons = defaultdict(list)
        
        for pattern in patterns:
            field_path = pattern['field_path']
            original_value = pattern['original_value']
            final_value = pattern['final_value']
            
            # 分析可能的修正原因
            if not original_value or (isinstance(original_value, str) and not original_value.strip()):
                reasons[field_path].append('missing_value')
            
            elif pattern['modification_type'] == 'format_correction':
                reasons[field_path].append('format_error')
            
            elif pattern['modification_type'] == 'value_refinement':
                reasons[field_path].append('accuracy_improvement')
            
            elif pattern['modification_type'] == 'category_change':
                reasons[field_path].append('classification_error')
            
            elif isinstance(original_value, (int, float)) and isinstance(final_value, (int, float)):
                if abs(final_value - original_value) / max(abs(original_value), 1) > 0.1:
                    reasons[field_path].append('significant_value_error')
        
        return dict(reasons)
    
    def _update_pattern_library(self, patterns: List[Dict[str, Any]], 
                               record_id: int) -> List[Dict[str, Any]]:
        """更新模式库"""
        from ..models.ai_analysis import AIAnalysisRecord
        
        learned_patterns = []
        
        try:
            # 获取分析记录以获取更多上下文
            record = AIAnalysisRecord.query.get(record_id)
            if not record:
                return learned_patterns
            
            for pattern in patterns:
                # 检查是否已存在相似模式
                similar_patterns = self._find_similar_patterns(pattern)
                
                if similar_patterns:
                    # 更新现有模式频率
                    self._update_pattern_frequency(similar_patterns[0], pattern)
                else:
                    # 创建新的学习模式
                    new_pattern = self._create_learning_pattern(pattern, record)
                    learned_patterns.append(new_pattern)
            
            # 清理过期模式
            self._cleanup_expired_patterns()
            
        except Exception as e:
            logger.error(f"Failed to update pattern library: {str(e)}")
        
        return learned_patterns
    
    def _generate_improvement_suggestions(self, patterns: List[Dict[str, Any]],
                                        reasons: Dict[str, List[str]]) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        # 分析修正频率
        field_frequencies = Counter(p['field_path'] for p in patterns)
        modification_types = Counter(p['modification_type'] for p in patterns)
        
        # 基于频率生成建议
        for field, freq in field_frequencies.most_common(3):
            if freq > 1:
                field_reasons = reasons.get(field, [])
                if 'format_error' in field_reasons:
                    suggestions.append(f"字段 {field} 格式识别需要改进")
                elif 'accuracy_improvement' in field_reasons:
                    suggestions.append(f"字段 {field} 准确性需要提升")
                elif 'missing_value' in field_reasons:
                    suggestions.append(f"字段 {field} 值提取存在遗漏")
        
        # 基于修正类型生成建议
        for mod_type, freq in modification_types.most_common(2):
            if freq > 1:
                if mod_type == 'format_correction':
                    suggestions.append("需要加强格式规范化处理")
                elif mod_type == 'value_refinement':
                    suggestions.append("需要提高数值提取精度")
                elif mod_type == 'category_change':
                    suggestions.append("需要改进分类识别算法")
        
        return suggestions
    
    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """获取嵌套字段值"""
        keys = field_path.split('.')
        value = data
        
        try:
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    return None
            return value
        except:
            return None
    
    def _categorize_field(self, field_path: str) -> str:
        """字段分类"""
        for category, fields in self.field_categories.items():
            if any(field in field_path for field in fields):
                return category
        return 'other'
    
    def _classify_modification_type(self, original_value: Any, final_value: Any) -> str:
        """分类修正类型"""
        if not original_value and final_value:
            return 'value_addition'
        elif original_value and not final_value:
            return 'value_removal'
        elif isinstance(original_value, str) and isinstance(final_value, str):
            if len(original_value) != len(final_value):
                return 'format_correction'
            else:
                return 'value_refinement'
        elif type(original_value) != type(final_value):
            return 'type_conversion'
        elif isinstance(original_value, (int, float)) and isinstance(final_value, (int, float)):
            return 'numeric_adjustment'
        else:
            return 'value_replacement'
    
    def _calculate_value_difference(self, original: Any, final: Any) -> float:
        """计算值差异"""
        if isinstance(original, (int, float)) and isinstance(final, (int, float)):
            if original == 0:
                return float('inf') if final != 0 else 0.0
            return abs(final - original) / abs(original)
        
        elif isinstance(original, str) and isinstance(final, str):
            # 使用Levenshtein距离的简化版本
            if len(original) == 0:
                return len(final)
            elif len(final) == 0:
                return len(original)
            else:
                # 简单的字符差异比例
                diff = sum(c1 != c2 for c1, c2 in zip(original, final))
                diff += abs(len(original) - len(final))
                return diff / max(len(original), len(final))
        
        else:
            return 1.0 if original != final else 0.0
    
    def _calculate_learning_confidence(self, patterns: List[Dict[str, Any]]) -> float:
        """计算学习置信度"""
        if not patterns:
            return 0.0
        
        confidence_factors = []
        
        # 基于模式数量
        pattern_count_score = min(1.0, len(patterns) / 5.0)
        confidence_factors.append(pattern_count_score)
        
        # 基于修正类型多样性
        modification_types = set(p['modification_type'] for p in patterns)
        diversity_score = len(modification_types) / 6.0  # 最多6种类型
        confidence_factors.append(diversity_score)
        
        # 基于值差异分析
        differences = [p['value_difference'] for p in patterns if p['value_difference'] < float('inf')]
        if differences:
            avg_difference = np.mean(differences)
            difference_score = 1.0 - min(1.0, avg_difference)  # 差异越小，置信度越高
            confidence_factors.append(difference_score)
        
        return np.mean(confidence_factors)
    
    def _get_user_patterns(self, user_id: int, document_type: str) -> List[Dict[str, Any]]:
        """获取用户历史修正模式"""
        # 这里应该从数据库查询用户的历史修正模式
        # 暂时返回示例数据
        return []
    
    def _predict_modifications(self, extracted_data: Dict[str, Any],
                             user_patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """预测可能的修正"""
        predictions = {}
        
        for pattern in user_patterns:
            field_path = pattern['field_path']
            current_value = self._get_nested_value(extracted_data, field_path)
            
            # 基于历史模式预测修正
            if pattern['frequency'] >= self.learning_config['min_pattern_frequency']:
                prediction_confidence = min(1.0, pattern['frequency'] / 10.0)
                
                predictions[field_path] = {
                    'predicted_value': pattern.get('typical_correction'),
                    'confidence': prediction_confidence,
                    'reason': f"基于{pattern['frequency']}次类似修正"
                }
        
        return predictions
    
    def _generate_personalized_hints(self, user_patterns: List[Dict[str, Any]],
                                   predicted_modifications: Dict[str, Any]) -> List[str]:
        """生成个性化提示"""
        hints = []
        
        # 基于用户常见修正生成提示
        field_frequencies = Counter(p['field_path'] for p in user_patterns)
        
        for field, freq in field_frequencies.most_common(3):
            if freq >= 2:
                hints.append(f"根据您的历史习惯，请特别注意检查 {field} 字段")
        
        # 基于预测修正生成提示
        for field, prediction in predicted_modifications.items():
            if prediction['confidence'] > 0.7:
                hints.append(f"建议将 {field} 修正为: {prediction['predicted_value']}")
        
        return hints
    
    def _calculate_confidence_adjustments(self, extracted_data: Dict[str, Any],
                                        user_patterns: List[Dict[str, Any]]) -> Dict[str, float]:
        """计算置信度调整"""
        adjustments = {}
        
        for pattern in user_patterns:
            field_path = pattern['field_path']
            
            # 基于历史修正频率调整置信度
            if pattern['frequency'] >= self.learning_config['min_pattern_frequency']:
                # 经常被修正的字段降低置信度
                adjustment = -0.1 * min(5, pattern['frequency']) / 5
                adjustments[field_path] = adjustment
        
        return adjustments
    
    def _generate_user_recommendations(self, user_patterns: List[Dict[str, Any]]) -> List[str]:
        """生成用户建议"""
        recommendations = []
        
        if not user_patterns:
            recommendations.append("建议多使用AI分析功能，系统将学习您的偏好")
            return recommendations
        
        # 分析用户修正习惯
        frequent_fields = Counter(p['field_path'] for p in user_patterns)
        
        for field, freq in frequent_fields.most_common(2):
            if freq >= 3:
                recommendations.append(f"您经常修正 {field} 字段，建议在上传时确保相关信息清晰")
        
        return recommendations

    def get_learning_statistics(self, days: int = 30) -> Dict[str, Any]:
        """获取学习统计信息"""
        try:
            from ..models.ai_analysis import AIAnalysisRecord
            from datetime import datetime, timedelta
            
            # 获取指定时间范围内的分析记录
            start_date = datetime.utcnow() - timedelta(days=days)
            records = AIAnalysisRecord.query.filter(
                AIAnalysisRecord.created_at >= start_date,
                AIAnalysisRecord.user_modifications.isnot(None)
            ).all()
            
            if not records:
                return {
                    'total_modifications': 0,
                    'avg_modification_rate': 0.0,
                    'most_modified_fields': [],
                    'learning_improvement': 0.0,
                    'pattern_count': 0
                }
            
            # 统计修正信息
            total_modifications = 0
            modification_rates = []
            field_modifications = Counter()
            
            for record in records:
                mod_count = len(record.get_user_modifications())
                total_modifications += mod_count
                
                mod_rate = record.calculate_modification_rate()
                modification_rates.append(mod_rate)
                
                # 统计字段修正频率
                for field_path in record.get_user_modifications().keys():
                    field_modifications[field_path] += 1
            
            avg_modification_rate = np.mean(modification_rates) if modification_rates else 0.0
            
            # 计算学习改进效果
            recent_records = records[-10:] if len(records) >= 10 else records
            old_records = records[:-10] if len(records) >= 20 else []
            
            learning_improvement = 0.0
            if old_records and recent_records:
                old_avg_rate = np.mean([r.calculate_modification_rate() for r in old_records])
                recent_avg_rate = np.mean([r.calculate_modification_rate() for r in recent_records])
                learning_improvement = max(0.0, old_avg_rate - recent_avg_rate)
            
            return {
                'total_modifications': total_modifications,
                'avg_modification_rate': avg_modification_rate,
                'most_modified_fields': field_modifications.most_common(5),
                'learning_improvement': learning_improvement,
                'pattern_count': len(field_modifications),
                'records_analyzed': len(records)
            }
            
        except Exception as e:
            logger.error(f"Failed to get learning statistics: {str(e)}")
            return {
                'total_modifications': 0,
                'avg_modification_rate': 0.0,
                'most_modified_fields': [],
                'learning_improvement': 0.0,
                'pattern_count': 0,
                'error': str(e)
            }