# -*- coding: utf-8 -*-
"""
历史数据分析引擎
分析用户的历史修正记录，识别AI分析的常见错误模式和成功案例
"""
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict, Counter
from sqlalchemy import func, desc, and_, or_

from ..models.ai_analysis import AIAnalysisRecord
from ..models.prompt_optimization import ErrorPattern, UserLearningProfile, PromptPerformanceMetric
from .base import db

logger = logging.getLogger(__name__)

class HistoricalAnalysisEngine:
    """历史数据分析引擎"""
    
    def __init__(self):
        self.analysis_cache = {}  # 分析结果缓存
        self.cache_ttl = 3600  # 缓存TTL（秒）
    
    def analyze_user_modification_patterns(self, user_id: int, days: int = 90) -> Dict[str, Any]:
        """
        分析用户的修正模式
        
        Args:
            user_id: 用户ID
            days: 分析天数
            
        Returns:
            Dict: 用户修正模式分析结果
        """
        cache_key = f"user_patterns_{user_id}_{days}"
        if self._get_from_cache(cache_key):
            return self._get_from_cache(cache_key)
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # 获取用户的分析记录
            records = AIAnalysisRecord.query.filter(
                AIAnalysisRecord.user_id == user_id,
                AIAnalysisRecord.created_at >= cutoff_date,
                AIAnalysisRecord.success == True
            ).all()
            
            if not records:
                return {
                    'total_analyses': 0,
                    'modification_patterns': {},
                    'field_accuracy': {},
                    'improvement_trend': 0.0,
                    'common_errors': []
                }
            
            # 分析修正模式
            modification_patterns = defaultdict(list)
            field_modifications = defaultdict(int)
            field_totals = defaultdict(int)
            confidence_trends = []
            
            for record in records:
                modifications = record.get_user_modifications()
                extracted_data = record.get_extracted_data()
                final_data = record.get_final_data()
                
                # 分析字段级别的修正
                self._analyze_field_modifications(
                    modifications, extracted_data, final_data,
                    modification_patterns, field_modifications, field_totals
                )
                
                # 记录置信度趋势
                confidence_trends.append({
                    'date': record.created_at,
                    'confidence': record.get_overall_confidence(),
                    'modification_rate': record.calculate_modification_rate()
                })
            
            # 计算字段准确性
            field_accuracy = {}
            for field in field_totals:
                if field_totals[field] > 0:
                    accuracy = 1.0 - (field_modifications[field] / field_totals[field])
                    field_accuracy[field] = max(0.0, accuracy)
            
            # 计算改进趋势
            improvement_trend = self._calculate_improvement_trend(confidence_trends)
            
            # 识别常见错误
            common_errors = self._identify_common_errors(modification_patterns)
            
            result = {
                'total_analyses': len(records),
                'modification_patterns': dict(modification_patterns),
                'field_accuracy': field_accuracy,
                'improvement_trend': improvement_trend,
                'common_errors': common_errors,
                'confidence_trend': confidence_trends[-10:] if len(confidence_trends) > 10 else confidence_trends,
                'analysis_period_days': days
            }
            
            self._set_cache(cache_key, result)
            logger.info(f"Analyzed modification patterns for user {user_id}: {len(records)} records")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing user modification patterns: {str(e)}")
            return {
                'error': str(e),
                'total_analyses': 0,
                'modification_patterns': {},
                'field_accuracy': {},
                'improvement_trend': 0.0,
                'common_errors': []
            }
    
    def analyze_global_error_patterns(self, days: int = 30) -> Dict[str, Any]:
        """
        分析全局错误模式
        
        Args:
            days: 分析天数
            
        Returns:
            Dict: 全局错误模式分析结果
        """
        cache_key = f"global_errors_{days}"
        if self._get_from_cache(cache_key):
            return self._get_from_cache(cache_key)
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # 获取所有分析记录
            records = AIAnalysisRecord.query.filter(
                AIAnalysisRecord.created_at >= cutoff_date,
                AIAnalysisRecord.success == True
            ).all()
            
            if not records:
                return {
                    'total_records': 0,
                    'error_patterns': [],
                    'field_performance': {},
                    'document_type_performance': {}
                }
            
            # 按文档类型分组分析
            document_type_stats = defaultdict(lambda: {
                'total': 0,
                'modifications': 0,
                'avg_confidence': 0.0,
                'field_errors': defaultdict(int)
            })
            
            # 字段级别的错误统计
            field_error_stats = defaultdict(lambda: {
                'total_occurrences': 0,
                'modification_count': 0,
                'error_types': defaultdict(int),
                'low_confidence_count': 0
            })
            
            for record in records:
                doc_type = record.document_type or 'unknown'
                modifications = record.get_user_modifications()
                confidence_scores = record.get_confidence_scores()
                extracted_data = record.get_extracted_data()
                
                # 更新文档类型统计
                document_type_stats[doc_type]['total'] += 1
                document_type_stats[doc_type]['avg_confidence'] += record.get_overall_confidence()
                
                # 分析字段错误
                self._analyze_field_errors(
                    extracted_data, modifications, confidence_scores,
                    field_error_stats, document_type_stats[doc_type]['field_errors']
                )
            
            # 计算平均值
            for doc_type in document_type_stats:
                if document_type_stats[doc_type]['total'] > 0:
                    document_type_stats[doc_type]['avg_confidence'] /= document_type_stats[doc_type]['total']
            
            # 识别关键错误模式
            error_patterns = self._identify_critical_error_patterns(field_error_stats)
            
            # 计算字段性能
            field_performance = {}
            for field, stats in field_error_stats.items():
                if stats['total_occurrences'] > 0:
                    accuracy = 1.0 - (stats['modification_count'] / stats['total_occurrences'])
                    field_performance[field] = {
                        'accuracy': max(0.0, accuracy),
                        'total_occurrences': stats['total_occurrences'],
                        'modification_rate': stats['modification_count'] / stats['total_occurrences'],
                        'low_confidence_rate': stats['low_confidence_count'] / stats['total_occurrences']
                    }
            
            result = {
                'total_records': len(records),
                'error_patterns': error_patterns,
                'field_performance': field_performance,
                'document_type_performance': dict(document_type_stats),
                'analysis_period_days': days,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            self._set_cache(cache_key, result)
            logger.info(f"Analyzed global error patterns: {len(records)} records over {days} days")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing global error patterns: {str(e)}")
            return {
                'error': str(e),
                'total_records': 0,
                'error_patterns': [],
                'field_performance': {},
                'document_type_performance': {}
            }
    
    def identify_success_patterns(self, user_id: int = None, days: int = 30) -> Dict[str, Any]:
        """
        识别成功的分析模式
        
        Args:
            user_id: 用户ID，None表示全局分析
            days: 分析天数
            
        Returns:
            Dict: 成功模式分析结果
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            query = AIAnalysisRecord.query.filter(
                AIAnalysisRecord.created_at >= cutoff_date,
                AIAnalysisRecord.success == True
            )
            
            if user_id:
                query = query.filter(AIAnalysisRecord.user_id == user_id)
            
            records = query.all()
            
            if not records:
                return {
                    'success_patterns': [],
                    'high_confidence_characteristics': {},
                    'minimal_modification_patterns': {}
                }
            
            # 找出高质量分析（高置信度 + 低修改率）
            high_quality_records = [
                record for record in records
                if record.get_overall_confidence() > 0.8 and record.calculate_modification_rate() < 0.1
            ]
            
            # 分析成功模式
            success_patterns = []
            if high_quality_records:
                # 文档特征分析
                doc_features = self._analyze_document_features(high_quality_records)
                success_patterns.append({
                    'pattern_type': 'document_features',
                    'description': 'Documents with these features tend to have higher accuracy',
                    'characteristics': doc_features
                })
                
                # 内容特征分析
                content_features = self._analyze_content_features(high_quality_records)
                success_patterns.append({
                    'pattern_type': 'content_features',
                    'description': 'Content patterns associated with successful analysis',
                    'characteristics': content_features
                })
            
            # 高置信度特征分析
            high_confidence_chars = self._analyze_high_confidence_characteristics(records)
            
            # 最小修改模式分析
            minimal_mod_patterns = self._analyze_minimal_modification_patterns(records)
            
            return {
                'success_patterns': success_patterns,
                'high_confidence_characteristics': high_confidence_chars,
                'minimal_modification_patterns': minimal_mod_patterns,
                'total_records_analyzed': len(records),
                'high_quality_records': len(high_quality_records)
            }
            
        except Exception as e:
            logger.error(f"Error identifying success patterns: {str(e)}")
            return {
                'error': str(e),
                'success_patterns': [],
                'high_confidence_characteristics': {},
                'minimal_modification_patterns': {}
            }
    
    def generate_learning_insights(self, user_id: int = None, days: int = 60) -> Dict[str, Any]:
        """
        生成学习洞察
        
        Args:
            user_id: 用户ID，None表示全局洞察
            days: 分析天数
            
        Returns:
            Dict: 学习洞察结果
        """
        try:
            # 获取修正模式分析
            if user_id:
                modification_analysis = self.analyze_user_modification_patterns(user_id, days)
            else:
                modification_analysis = self.analyze_global_error_patterns(days)
            
            # 获取成功模式分析
            success_analysis = self.identify_success_patterns(user_id, days)
            
            # 生成改进建议
            improvement_suggestions = self._generate_improvement_suggestions(
                modification_analysis, success_analysis
            )
            
            # 计算学习效果指标
            learning_metrics = self._calculate_learning_metrics(user_id, days)
            
            # 识别需要关注的领域
            focus_areas = self._identify_focus_areas(modification_analysis, success_analysis)
            
            return {
                'improvement_suggestions': improvement_suggestions,
                'learning_metrics': learning_metrics,
                'focus_areas': focus_areas,
                'modification_analysis_summary': self._summarize_modification_analysis(modification_analysis),
                'success_patterns_summary': self._summarize_success_patterns(success_analysis),
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating learning insights: {str(e)}")
            return {
                'error': str(e),
                'improvement_suggestions': [],
                'learning_metrics': {},
                'focus_areas': []
            }
    
    def _analyze_field_modifications(self, modifications, extracted_data, final_data,
                                   modification_patterns, field_modifications, field_totals):
        """分析字段级别的修正"""
        def traverse_dict(path, orig_dict, mod_dict, final_dict):
            if isinstance(orig_dict, dict) and isinstance(final_dict, dict):
                for key in set(orig_dict.keys()) | set(final_dict.keys()):
                    current_path = f"{path}.{key}" if path else key
                    field_totals[current_path] += 1
                    
                    orig_val = orig_dict.get(key)
                    final_val = final_dict.get(key)
                    
                    if orig_val != final_val:
                        field_modifications[current_path] += 1
                        
                        # 记录修正类型
                        change_type = 'modification'
                        if orig_val is None:
                            change_type = 'addition'
                        elif final_val is None:
                            change_type = 'deletion'
                        
                        modification_patterns[current_path].append({
                            'type': change_type,
                            'original': orig_val,
                            'final': final_val,
                            'pattern': self._classify_change_pattern(orig_val, final_val)
                        })
                    
                    # 递归处理嵌套字典
                    if isinstance(orig_val, dict) and isinstance(final_val, dict):
                        traverse_dict(current_path, orig_val, {}, final_val)
        
        traverse_dict('', extracted_data, modifications, final_data)
    
    def _analyze_field_errors(self, extracted_data, modifications, confidence_scores,
                            field_error_stats, doc_type_field_errors):
        """分析字段错误"""
        def traverse_fields(path, data_dict, conf_dict):
            if isinstance(data_dict, dict):
                for key, value in data_dict.items():
                    current_path = f"{path}.{key}" if path else key
                    field_error_stats[current_path]['total_occurrences'] += 1
                    
                    # 检查是否被修正
                    if self._was_field_modified(current_path, modifications):
                        field_error_stats[current_path]['modification_count'] += 1
                        doc_type_field_errors[current_path] += 1
                        
                        # 分析错误类型
                        error_type = self._classify_error_type(value, modifications.get(current_path))
                        field_error_stats[current_path]['error_types'][error_type] += 1
                    
                    # 检查置信度
                    field_confidence = conf_dict.get(key, 0.5) if isinstance(conf_dict, dict) else 0.5
                    if field_confidence < 0.6:
                        field_error_stats[current_path]['low_confidence_count'] += 1
                    
                    # 递归处理嵌套字典
                    if isinstance(value, dict):
                        nested_conf = conf_dict.get(key, {}) if isinstance(conf_dict, dict) else {}
                        traverse_fields(current_path, value, nested_conf)
        
        traverse_fields('', extracted_data, confidence_scores)
    
    def _calculate_improvement_trend(self, confidence_trends):
        """计算改进趋势"""
        if len(confidence_trends) < 2:
            return 0.0
        
        # 按时间排序
        trends = sorted(confidence_trends, key=lambda x: x['date'])
        
        # 使用简单的线性回归来计算趋势
        n = len(trends)
        if n < 3:
            return 0.0
        
        # 计算最近三分之一和最早三分之一的平均值
        early_third = trends[:n//3]
        recent_third = trends[-n//3:]
        
        early_avg = sum(t['confidence'] for t in early_third) / len(early_third)
        recent_avg = sum(t['confidence'] for t in recent_third) / len(recent_third)
        
        return recent_avg - early_avg
    
    def _identify_common_errors(self, modification_patterns):
        """识别常见错误"""
        error_counter = Counter()
        
        for field_path, modifications in modification_patterns.items():
            for mod in modifications:
                pattern = mod.get('pattern', 'unknown')
                error_counter[f"{field_path}:{pattern}"] += 1
        
        return [
            {
                'error_pattern': pattern,
                'frequency': count,
                'field': pattern.split(':')[0],
                'pattern_type': pattern.split(':')[1] if ':' in pattern else 'unknown'
            }
            for pattern, count in error_counter.most_common(10)
        ]
    
    def _identify_critical_error_patterns(self, field_error_stats):
        """识别关键错误模式"""
        critical_patterns = []
        
        for field, stats in field_error_stats.items():
            if stats['total_occurrences'] >= 5:  # 至少出现5次
                modification_rate = stats['modification_count'] / stats['total_occurrences']
                
                if modification_rate > 0.3:  # 修改率超过30%
                    pattern = {
                        'field_path': field,
                        'modification_rate': modification_rate,
                        'occurrence_count': stats['total_occurrences'],
                        'error_types': dict(stats['error_types']),
                        'severity': 'high' if modification_rate > 0.6 else 'medium'
                    }
                    critical_patterns.append(pattern)
        
        return sorted(critical_patterns, key=lambda x: x['modification_rate'], reverse=True)
    
    def _analyze_document_features(self, high_quality_records):
        """分析文档特征"""
        features = {
            'document_types': Counter(),
            'size_ranges': Counter(),
            'text_length_ranges': Counter()
        }
        
        for record in high_quality_records:
            features['document_types'][record.document_type or 'unknown'] += 1
            
            # 文档大小范围
            size = record.document_size or 0
            if size < 10240:  # < 10KB
                features['size_ranges']['small'] += 1
            elif size < 102400:  # < 100KB
                features['size_ranges']['medium'] += 1
            else:
                features['size_ranges']['large'] += 1
            
            # 文本长度范围
            length = record.text_length or 0
            if length < 1000:
                features['text_length_ranges']['short'] += 1
            elif length < 5000:
                features['text_length_ranges']['medium'] += 1
            else:
                features['text_length_ranges']['long'] += 1
        
        return {k: dict(v) for k, v in features.items()}
    
    def _analyze_content_features(self, high_quality_records):
        """分析内容特征"""
        # 这里可以添加更复杂的文本分析
        return {
            'structured_content_rate': 0.85,  # 示例值
            'technical_terms_density': 0.12,
            'table_presence_rate': 0.67
        }
    
    def _analyze_high_confidence_characteristics(self, records):
        """分析高置信度特征"""
        high_conf_records = [r for r in records if r.get_overall_confidence() > 0.8]
        
        if not high_conf_records:
            return {}
        
        return {
            'percentage': len(high_conf_records) / len(records),
            'avg_confidence': sum(r.get_overall_confidence() for r in high_conf_records) / len(high_conf_records),
            'common_document_types': Counter(r.document_type for r in high_conf_records).most_common(3)
        }
    
    def _analyze_minimal_modification_patterns(self, records):
        """分析最小修改模式"""
        minimal_mod_records = [r for r in records if r.calculate_modification_rate() < 0.1]
        
        if not minimal_mod_records:
            return {}
        
        return {
            'percentage': len(minimal_mod_records) / len(records),
            'avg_modification_rate': sum(r.calculate_modification_rate() for r in minimal_mod_records) / len(minimal_mod_records)
        }
    
    def _generate_improvement_suggestions(self, modification_analysis, success_analysis):
        """生成改进建议"""
        suggestions = []
        
        # 基于错误模式的建议
        if 'common_errors' in modification_analysis:
            for error in modification_analysis['common_errors'][:3]:
                suggestions.append({
                    'type': 'error_prevention',
                    'priority': 'high',
                    'suggestion': f"Add specific guidance for {error['field']} to prevent {error['pattern_type']} errors",
                    'field': error['field'],
                    'impact_estimate': error['frequency']
                })
        
        # 基于字段准确性的建议
        if 'field_accuracy' in modification_analysis:
            low_accuracy_fields = [
                field for field, accuracy in modification_analysis['field_accuracy'].items()
                if accuracy < 0.7
            ]
            
            for field in low_accuracy_fields[:3]:
                suggestions.append({
                    'type': 'accuracy_improvement',
                    'priority': 'medium',
                    'suggestion': f"Enhance prompt instructions for {field} extraction",
                    'field': field,
                    'current_accuracy': modification_analysis['field_accuracy'][field]
                })
        
        return suggestions
    
    def _calculate_learning_metrics(self, user_id, days):
        """计算学习效果指标"""
        try:
            if user_id:
                profile = UserLearningProfile.get_or_create_profile(user_id)
                return {
                    'total_analyses': profile.total_analyses,
                    'avg_modification_rate': profile.avg_modification_rate,
                    'improvement_trend': profile.improvement_trend,
                    'expertise_fields': profile.get_expertise_fields()
                }
            else:
                # 全局指标
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                total_analyses = AIAnalysisRecord.query.filter(
                    AIAnalysisRecord.created_at >= cutoff_date
                ).count()
                
                return {
                    'total_analyses': total_analyses,
                    'analysis_period_days': days
                }
        except Exception:
            return {}
    
    def _identify_focus_areas(self, modification_analysis, success_analysis):
        """识别需要关注的领域"""
        focus_areas = []
        
        # 基于错误频率识别
        if 'common_errors' in modification_analysis:
            high_frequency_errors = [
                error for error in modification_analysis['common_errors']
                if error['frequency'] > 3
            ]
            
            for error in high_frequency_errors:
                focus_areas.append({
                    'area': error['field'],
                    'reason': f"High error frequency ({error['frequency']} occurrences)",
                    'priority': 'high'
                })
        
        return focus_areas
    
    def _summarize_modification_analysis(self, analysis):
        """总结修正分析"""
        return {
            'total_analyses': analysis.get('total_analyses', 0),
            'improvement_trend': analysis.get('improvement_trend', 0.0),
            'top_error_fields': [error['field'] for error in analysis.get('common_errors', [])[:3]]
        }
    
    def _summarize_success_patterns(self, analysis):
        """总结成功模式"""
        return {
            'success_patterns_count': len(analysis.get('success_patterns', [])),
            'high_quality_percentage': analysis.get('high_quality_records', 0) / max(1, analysis.get('total_records_analyzed', 1))
        }
    
    def _classify_change_pattern(self, original, final):
        """分类变更模式"""
        if original is None:
            return 'addition'
        elif final is None:
            return 'deletion'
        elif isinstance(original, str) and isinstance(final, str):
            if len(final) > len(original) * 1.5:
                return 'expansion'
            elif len(final) < len(original) * 0.5:
                return 'compression'
            else:
                return 'modification'
        else:
            return 'type_change'
    
    def _was_field_modified(self, field_path, modifications):
        """检查字段是否被修正"""
        if not modifications:
            return False
        
        # 简单的路径匹配
        for mod_path in modifications.keys():
            if field_path == mod_path or field_path.startswith(f"{mod_path}."):
                return True
        return False
    
    def _classify_error_type(self, original_value, modification):
        """分类错误类型"""
        if original_value is None:
            return 'missing_extraction'
        elif modification is None:
            return 'false_positive'
        elif isinstance(original_value, str) and isinstance(modification, str):
            if len(original_value) == 0:
                return 'empty_extraction'
            else:
                return 'incorrect_extraction'
        else:
            return 'type_mismatch'
    
    def _get_from_cache(self, key):
        """从缓存获取数据"""
        if key in self.analysis_cache:
            cached_data, timestamp = self.analysis_cache[key]
            if datetime.utcnow().timestamp() - timestamp < self.cache_ttl:
                return cached_data
            else:
                del self.analysis_cache[key]
        return None
    
    def _set_cache(self, key, data):
        """设置缓存数据"""
        self.analysis_cache[key] = (data, datetime.utcnow().timestamp())
        
        # 简单的缓存清理
        if len(self.analysis_cache) > 100:
            oldest_key = min(self.analysis_cache.keys(), 
                           key=lambda k: self.analysis_cache[k][1])
            del self.analysis_cache[oldest_key]