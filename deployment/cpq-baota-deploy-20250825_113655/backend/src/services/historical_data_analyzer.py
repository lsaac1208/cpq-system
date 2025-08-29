# -*- coding: utf-8 -*-
"""
历史数据分析引擎
分析用户的AI分析历史记录，识别错误模式、成功特征，为prompt优化提供数据支持
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
import json

from src.models.ai_analysis import AIAnalysisRecord
from src.models.prompt_optimization import UserAnalysisPattern
from src.models.base import db

logger = logging.getLogger(__name__)

class HistoricalDataAnalyzer:
    """历史数据分析引擎"""
    
    def __init__(self):
        self.analysis_window_days = 90  # 分析窗口：90天
        self.min_samples_per_field = 5  # 每个字段最少样本数
        self.confidence_threshold = 0.6  # 置信度阈值
        
    def analyze_user_patterns(self, user_id: int, document_type: str = None) -> Dict[str, Any]:
        """
        分析用户的历史分析模式
        
        Args:
            user_id: 用户ID
            document_type: 文档类型（可选）
            
        Returns:
            分析结果字典
        """
        try:
            logger.info(f"开始分析用户{user_id}的历史模式，文档类型：{document_type}")
            
            # 获取历史记录
            cutoff_date = datetime.utcnow() - timedelta(days=self.analysis_window_days)
            
            query = AIAnalysisRecord.query.filter(
                AIAnalysisRecord.user_id == user_id,
                AIAnalysisRecord.created_at >= cutoff_date,
                AIAnalysisRecord.success == True
            )
            
            if document_type:
                query = query.filter(AIAnalysisRecord.document_type == document_type)
            
            records = query.all()
            
            if len(records) < self.min_samples_per_field:
                logger.warning(f"用户{user_id}历史记录不足（{len(records)}条），无法进行有效分析")
                return {
                    'user_id': user_id,
                    'document_type': document_type,
                    'total_records': len(records),
                    'message': '历史记录不足，无法生成个性化优化',
                    'patterns': []
                }
            
            # 按字段分析
            field_patterns = self._analyze_field_patterns(records)
            
            # 识别错误模式
            error_patterns = self._identify_error_patterns(records)
            
            # 提取成功特征
            success_features = self._extract_success_features(records)
            
            # 计算统计指标
            statistics = self._calculate_user_statistics(records)
            
            # 更新或创建用户模式记录
            self._update_user_patterns(user_id, document_type, field_patterns, error_patterns, success_features)
            
            analysis_result = {
                'user_id': user_id,
                'document_type': document_type,
                'analysis_period': {
                    'start_date': cutoff_date.isoformat(),
                    'end_date': datetime.utcnow().isoformat(),
                    'days': self.analysis_window_days
                },
                'total_records': len(records),
                'statistics': statistics,
                'field_patterns': field_patterns,
                'error_patterns': error_patterns,
                'success_features': success_features,
                'optimization_recommendations': self._generate_optimization_recommendations(
                    field_patterns, error_patterns, success_features
                )
            }
            
            logger.info(f"用户{user_id}历史模式分析完成，发现{len(field_patterns)}个字段模式")
            return analysis_result
            
        except Exception as e:
            logger.error(f"分析用户{user_id}历史模式失败: {str(e)}")
            raise
    
    def _analyze_field_patterns(self, records: List[AIAnalysisRecord]) -> Dict[str, Any]:
        """分析字段级别的模式"""
        field_patterns = {}
        
        # 收集所有字段数据
        field_data = defaultdict(lambda: {
            'values': [],
            'confidences': [],
            'modifications': []
        })
        
        for record in records:
            extracted_data = record.get_extracted_data()
            user_modifications = record.get_user_modifications()
            confidence_scores = record.get_confidence_scores()
            
            # 分析基础信息字段
            basic_info = extracted_data.get('basic_info', {})
            for field_name, value in basic_info.items():
                if value:  # 只分析有值的字段
                    field_data[field_name]['values'].append(value)
                    field_data[field_name]['confidences'].append(
                        confidence_scores.get(field_name, confidence_scores.get('overall', 0.0))
                    )
                    
                    # 检查用户是否修正了这个字段
                    modified_basic = user_modifications.get('basic_info', {})
                    if field_name in modified_basic:
                        field_data[field_name]['modifications'].append({
                            'original': value,
                            'corrected': modified_basic[field_name],
                            'confidence': confidence_scores.get(field_name, 0.0)
                        })
        
        # 分析每个字段的模式
        for field_name, data in field_data.items():
            if len(data['values']) >= self.min_samples_per_field:
                field_patterns[field_name] = self._analyze_single_field(field_name, data)
        
        return field_patterns
    
    def _analyze_single_field(self, field_name: str, field_data: Dict) -> Dict[str, Any]:
        """分析单个字段的模式"""
        values = field_data['values']
        confidences = field_data['confidences']
        modifications = field_data['modifications']
        
        # 计算基础统计
        total_count = len(values)
        modification_count = len(modifications)
        accuracy_rate = (total_count - modification_count) / total_count
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # 分析值分布
        value_counts = Counter(values)
        most_common_values = value_counts.most_common(5)
        
        # 分析置信度分布
        confidence_ranges = {
            'low': len([c for c in confidences if c < 0.6]),
            'medium': len([c for c in confidences if 0.6 <= c < 0.8]),
            'high': len([c for c in confidences if c >= 0.8])
        }
        
        # 分析错误模式
        error_analysis = self._analyze_field_errors(modifications)
        
        # 成功案例特征
        success_cases = [
            {'value': v, 'confidence': c} 
            for v, c in zip(values, confidences) 
            if c >= self.confidence_threshold
        ]
        
        pattern = {
            'field_name': field_name,
            'statistics': {
                'total_count': total_count,
                'modification_count': modification_count,
                'accuracy_rate': accuracy_rate,
                'avg_confidence': avg_confidence
            },
            'value_distribution': {
                'unique_values': len(value_counts),
                'most_common': most_common_values,
                'variety_score': len(value_counts) / total_count  # 值的多样性
            },
            'confidence_distribution': confidence_ranges,
            'error_analysis': error_analysis,
            'success_cases': success_cases[:5],  # 取前5个成功案例
            'recommendations': self._generate_field_recommendations(
                field_name, accuracy_rate, avg_confidence, error_analysis
            )
        }
        
        return pattern
    
    def _analyze_field_errors(self, modifications: List[Dict]) -> Dict[str, Any]:
        """分析字段错误模式"""
        if not modifications:
            return {'error_count': 0, 'common_errors': [], 'error_types': {}}
        
        # 分析常见错误
        error_pairs = [(m['original'], m['corrected']) for m in modifications]
        error_counts = Counter(error_pairs)
        common_errors = error_counts.most_common(5)
        
        # 分类错误类型
        error_types = defaultdict(int)
        for mod in modifications:
            original = str(mod['original']).strip()
            corrected = str(mod['corrected']).strip()
            
            if not original:
                error_types['missing_value'] += 1
            elif original.lower() != corrected.lower():
                if len(original) != len(corrected):
                    error_types['format_error'] += 1
                elif original.isdigit() and corrected.isdigit():
                    error_types['numeric_error'] += 1
                else:
                    error_types['content_error'] += 1
            else:
                error_types['case_error'] += 1
        
        return {
            'error_count': len(modifications),
            'common_errors': [
                {
                    'original': original,
                    'corrected': corrected,
                    'frequency': count
                } 
                for (original, corrected), count in common_errors
            ],
            'error_types': dict(error_types),
            'avg_confidence_on_errors': sum(m['confidence'] for m in modifications) / len(modifications)
        }
    
    def _generate_field_recommendations(self, field_name: str, accuracy_rate: float, 
                                      avg_confidence: float, error_analysis: Dict) -> List[str]:
        """为字段生成优化建议"""
        recommendations = []
        
        if accuracy_rate < 0.7:
            recommendations.append(f"重点关注{field_name}字段的准确性（当前准确率：{accuracy_rate:.1%}）")
        
        if avg_confidence < 0.6:
            recommendations.append(f"提高{field_name}字段识别的置信度（当前平均：{avg_confidence:.1%}）")
        
        # 基于错误类型的建议
        error_types = error_analysis.get('error_types', {})
        if error_types.get('missing_value', 0) > 2:
            recommendations.append(f"加强{field_name}字段的缺失值检测和填充")
        
        if error_types.get('format_error', 0) > 2:
            recommendations.append(f"改进{field_name}字段的格式识别和标准化")
        
        if error_types.get('numeric_error', 0) > 2:
            recommendations.append(f"优化{field_name}字段的数值识别准确性")
        
        # 常见错误的具体建议
        common_errors = error_analysis.get('common_errors', [])
        if common_errors:
            top_error = common_errors[0]
            recommendations.append(
                f"避免将{field_name}的'{top_error['original']}'误识别为'{top_error['corrected']}'"
            )
        
        return recommendations[:3]  # 最多返回3个建议
    
    def _identify_error_patterns(self, records: List[AIAnalysisRecord]) -> List[Dict[str, Any]]:
        """识别常见错误模式"""
        error_patterns = []
        
        # 收集所有错误案例
        all_errors = []
        for record in records:
            user_modifications = record.get_user_modifications()
            if user_modifications:
                confidence_scores = record.get_confidence_scores()
                extracted_data = record.get_extracted_data()
                
                # 分析基础信息的错误
                basic_modifications = user_modifications.get('basic_info', {})
                basic_extracted = extracted_data.get('basic_info', {})
                
                for field, corrected_value in basic_modifications.items():
                    original_value = basic_extracted.get(field, '')
                    all_errors.append({
                        'field': field,
                        'original': original_value,
                        'corrected': corrected_value,
                        'confidence': confidence_scores.get(field, 0.0),
                        'document_type': record.document_type,
                        'timestamp': record.created_at
                    })
        
        if not all_errors:
            return error_patterns
        
        # 按字段分组分析
        field_errors = defaultdict(list)
        for error in all_errors:
            field_errors[error['field']].append(error)
        
        # 为每个字段识别错误模式
        for field, errors in field_errors.items():
            if len(errors) >= 3:  # 至少3个错误才考虑为模式
                pattern = self._analyze_error_pattern(field, errors)
                if pattern:
                    error_patterns.append(pattern)
        
        return error_patterns
    
    def _analyze_error_pattern(self, field_name: str, errors: List[Dict]) -> Optional[Dict[str, Any]]:
        """分析特定字段的错误模式"""
        if len(errors) < 3:
            return None
        
        # 计算错误频率和置信度统计
        error_frequency = len(errors)
        avg_confidence_on_error = sum(e['confidence'] for e in errors) / len(errors)
        
        # 分析错误类型分布
        error_pairs = [(e['original'], e['corrected']) for e in errors]
        error_counts = Counter(error_pairs)
        most_common_error = error_counts.most_common(1)[0]
        
        # 时间趋势分析
        recent_errors = [e for e in errors if e['timestamp'] >= datetime.utcnow() - timedelta(days=30)]
        trend = 'increasing' if len(recent_errors) > len(errors) / 3 else 'stable'
        
        pattern = {
            'field_name': field_name,
            'error_frequency': error_frequency,
            'avg_confidence_on_error': avg_confidence_on_error,
            'most_common_error': {
                'original': most_common_error[0][0],
                'corrected': most_common_error[0][1],
                'count': most_common_error[1]
            },
            'error_distribution': dict(error_counts),
            'trend': trend,
            'recent_errors_count': len(recent_errors),
            'severity': self._calculate_error_severity(error_frequency, avg_confidence_on_error)
        }
        
        return pattern
    
    def _calculate_error_severity(self, frequency: int, avg_confidence: float) -> str:
        """计算错误严重程度"""
        # 错误频率权重40%，平均置信度权重60%
        severity_score = (frequency * 0.4) + ((1 - avg_confidence) * 0.6 * 10)
        
        if severity_score >= 7:
            return 'critical'
        elif severity_score >= 4:
            return 'high'
        elif severity_score >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _extract_success_features(self, records: List[AIAnalysisRecord]) -> List[Dict[str, Any]]:
        """提取成功分析的特征"""
        success_features = []
        
        # 找到高质量的分析记录（高置信度且无用户修正）
        high_quality_records = []
        for record in records:
            user_modifications = record.get_user_modifications()
            confidence_scores = record.get_confidence_scores()
            overall_confidence = confidence_scores.get('overall', 0.0)
            
            # 高质量标准：置信度>0.8且无用户修正
            if overall_confidence >= 0.8 and not user_modifications:
                high_quality_records.append(record)
        
        if len(high_quality_records) < 3:
            return success_features
        
        # 分析成功案例的共同特征
        success_patterns = self._analyze_success_patterns(high_quality_records)
        success_features.extend(success_patterns)
        
        return success_features
    
    def _analyze_success_patterns(self, records: List[AIAnalysisRecord]) -> List[Dict[str, Any]]:
        """分析成功案例的模式"""
        patterns = []
        
        # 分析文档特征
        doc_types = Counter(record.document_type for record in records)
        doc_sizes = [record.document_size for record in records if record.document_size]
        text_lengths = [record.text_length for record in records if record.text_length]
        
        if doc_types:
            most_successful_doc_type = doc_types.most_common(1)[0]
            patterns.append({
                'type': 'document_preference',
                'feature': 'document_type',
                'value': most_successful_doc_type[0],
                'success_count': most_successful_doc_type[1],
                'description': f"在{most_successful_doc_type[0]}类型文档上表现最佳"
            })
        
        # 分析内容特征
        if text_lengths:
            avg_length = sum(text_lengths) / len(text_lengths)
            patterns.append({
                'type': 'content_preference',
                'feature': 'optimal_text_length',
                'value': avg_length,
                'description': f"文本长度在{avg_length:.0f}字符左右时识别效果最佳"
            })
        
        # 分析字段成功模式
        field_success_patterns = self._analyze_field_success_patterns(records)
        patterns.extend(field_success_patterns)
        
        return patterns
    
    def _analyze_field_success_patterns(self, records: List[AIAnalysisRecord]) -> List[Dict[str, Any]]:
        """分析字段级别的成功模式"""
        patterns = []
        
        # 收集所有成功字段的特征
        field_successes = defaultdict(list)
        for record in records:
            extracted_data = record.get_extracted_data()
            confidence_scores = record.get_confidence_scores()
            
            basic_info = extracted_data.get('basic_info', {})
            for field, value in basic_info.items():
                if value and confidence_scores.get(field, 0.0) >= 0.8:
                    field_successes[field].append({
                        'value': value,
                        'confidence': confidence_scores.get(field, 0.0),
                        'value_type': type(value).__name__,
                        'value_length': len(str(value))
                    })
        
        # 为每个字段分析成功模式
        for field, successes in field_successes.items():
            if len(successes) >= 3:
                # 分析值的模式
                value_lengths = [s['value_length'] for s in successes]
                avg_length = sum(value_lengths) / len(value_lengths)
                
                avg_confidence = sum(s['confidence'] for s in successes) / len(successes)
                
                patterns.append({
                    'type': 'field_success',
                    'feature': field,
                    'success_count': len(successes),
                    'avg_confidence': avg_confidence,
                    'optimal_length': avg_length,
                    'description': f"{field}字段在长度约{avg_length:.0f}字符时识别最准确"
                })
        
        return patterns
    
    def _calculate_user_statistics(self, records: List[AIAnalysisRecord]) -> Dict[str, Any]:
        """计算用户统计指标"""
        if not records:
            return {}
        
        # 基础统计
        total_records = len(records)
        total_with_modifications = len([r for r in records if r.get_user_modifications()])
        overall_accuracy = (total_records - total_with_modifications) / total_records
        
        # 置信度统计
        all_confidences = []
        for record in records:
            confidence_scores = record.get_confidence_scores()
            overall_confidence = confidence_scores.get('overall', 0.0)
            if overall_confidence > 0:
                all_confidences.append(overall_confidence)
        
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
        
        # 时间统计
        analysis_durations = [r.analysis_duration for r in records if r.analysis_duration]
        avg_duration = sum(analysis_durations) / len(analysis_durations) if analysis_durations else 0.0
        
        # 文档类型分布
        doc_type_distribution = Counter(r.document_type for r in records)
        
        return {
            'total_records': total_records,
            'overall_accuracy': overall_accuracy,
            'modification_rate': total_with_modifications / total_records,
            'avg_confidence': avg_confidence,
            'avg_analysis_duration': avg_duration,
            'document_type_distribution': dict(doc_type_distribution),
            'confidence_distribution': {
                'high': len([c for c in all_confidences if c >= 0.8]),
                'medium': len([c for c in all_confidences if 0.6 <= c < 0.8]),
                'low': len([c for c in all_confidences if c < 0.6])
            }
        }
    
    def _update_user_patterns(self, user_id: int, document_type: str, 
                            field_patterns: Dict, error_patterns: List, success_features: List):
        """更新用户分析模式记录"""
        try:
            for field_name, pattern in field_patterns.items():
                # 查找或创建用户模式记录
                user_pattern = UserAnalysisPattern.query.filter_by(
                    user_id=user_id,
                    document_type=document_type,
                    field_name=field_name
                ).first()
                
                if not user_pattern:
                    user_pattern = UserAnalysisPattern()
                    user_pattern.user_id = user_id
                    user_pattern.document_type = document_type
                    user_pattern.field_name = field_name
                
                # 更新统计数据
                stats = pattern['statistics']
                user_pattern.total_analyses = stats['total_count']
                user_pattern.correct_analyses = stats['total_count'] - stats['modification_count']
                user_pattern.accuracy_rate = stats['accuracy_rate']
                user_pattern.modification_frequency = stats['modification_count'] / stats['total_count']
                user_pattern.avg_confidence = stats['avg_confidence']
                
                # 更新错误模式
                error_analysis = pattern['error_analysis']
                user_pattern.error_frequency = error_analysis['error_count']
                user_pattern.error_patterns = error_analysis.get('common_errors', [])
                user_pattern.error_types = error_analysis.get('error_types', {})
                
                # 更新成功模式
                user_pattern.success_examples = pattern['success_cases']
                user_pattern.success_patterns = [
                    f for f in success_features 
                    if f.get('feature') == field_name
                ]
                
                user_pattern.last_updated = datetime.utcnow()
                user_pattern.save()
            
            logger.info(f"用户{user_id}的{len(field_patterns)}个字段模式已更新")
            
        except Exception as e:
            logger.error(f"更新用户{user_id}模式记录失败: {str(e)}")
            raise
    
    def _generate_optimization_recommendations(self, field_patterns: Dict, 
                                             error_patterns: List, success_features: List) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        # 基于字段模式的建议
        low_accuracy_fields = [
            field for field, pattern in field_patterns.items()
            if pattern['statistics']['accuracy_rate'] < 0.7
        ]
        
        if low_accuracy_fields:
            recommendations.append(
                f"需要特别关注这些准确率较低的字段：{', '.join(low_accuracy_fields[:3])}"
            )
        
        # 基于错误模式的建议
        critical_errors = [
            pattern for pattern in error_patterns
            if pattern.get('severity') == 'critical'
        ]
        
        if critical_errors:
            recommendations.append(
                f"发现{len(critical_errors)}个严重错误模式，建议优先优化"
            )
        
        # 基于成功特征的建议
        doc_preferences = [
            f for f in success_features
            if f.get('type') == 'document_preference'
        ]
        
        if doc_preferences:
            best_doc_type = doc_preferences[0]['value']
            recommendations.append(
                f"在{best_doc_type}类型文档上表现最佳，可作为优化参考"
            )
        
        # 通用建议
        if not recommendations:
            recommendations.append("当前分析表现良好，建议保持现有设置")
        
        return recommendations[:5]  # 最多返回5个建议
    
    def get_global_error_patterns(self, document_type: str = None, days: int = 30) -> List[Dict[str, Any]]:
        """获取全局错误模式（所有用户）"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            query = AIAnalysisRecord.query.filter(
                AIAnalysisRecord.created_at >= cutoff_date,
                AIAnalysisRecord.success == True
            )
            
            if document_type:
                query = query.filter(AIAnalysisRecord.document_type == document_type)
            
            records = query.all()
            
            # 收集所有用户的错误模式
            all_errors = []
            for record in records:
                user_modifications = record.get_user_modifications()
                if user_modifications:
                    basic_modifications = user_modifications.get('basic_info', {})
                    basic_extracted = record.get_extracted_data().get('basic_info', {})
                    
                    for field, corrected_value in basic_modifications.items():
                        all_errors.append({
                            'field': field,
                            'original': basic_extracted.get(field, ''),
                            'corrected': corrected_value,
                            'user_id': record.user_id
                        })
            
            # 统计全局错误模式
            field_errors = defaultdict(list)
            for error in all_errors:
                field_errors[error['field']].append((error['original'], error['corrected']))
            
            global_patterns = []
            for field, errors in field_errors.items():
                error_counts = Counter(errors)
                if len(error_counts) >= 3:  # 至少3个用户遇到相同错误
                    most_common = error_counts.most_common(5)
                    global_patterns.append({
                        'field': field,
                        'total_errors': len(errors),
                        'unique_users': len(set(e.get('user_id') for e in all_errors if e['field'] == field)),
                        'common_errors': [
                            {
                                'original': original,
                                'corrected': corrected,
                                'frequency': count
                            }
                            for (original, corrected), count in most_common
                        ]
                    })
            
            return sorted(global_patterns, key=lambda x: x['total_errors'], reverse=True)
            
        except Exception as e:
            logger.error(f"获取全局错误模式失败: {str(e)}")
            return []