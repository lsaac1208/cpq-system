# -*- coding: utf-8 -*-
"""
学习反馈系统
实现持续学习和优化机制，基于用户反馈和分析结果动态调整优化策略
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
from collections import defaultdict

from src.models.ai_analysis import AIAnalysisRecord
from src.models.prompt_optimization import (
    PromptOptimizationHistory, UserAnalysisPattern, PromptTemplate, PromptABTest
)
from src.services.historical_data_analyzer import HistoricalDataAnalyzer
from src.services.prompt_optimization_engine import PromptOptimizationEngine
from src.models.base import db

logger = logging.getLogger(__name__)

class LearningFeedbackSystem:
    """学习反馈系统"""
    
    def __init__(self):
        self.historical_analyzer = HistoricalDataAnalyzer()
        self.optimization_engine = PromptOptimizationEngine()
        
        # 学习参数配置
        self.learning_config = {
            'min_feedback_samples': 10,  # 最小反馈样本数
            'learning_rate': 0.1,  # 学习率
            'feedback_window_days': 30,  # 反馈窗口期
            'performance_threshold': 0.05,  # 性能改进阈值
            'confidence_threshold': 0.7,  # 置信度阈值
            'auto_optimization_enabled': True,  # 自动优化开关
            'ab_test_duration_days': 14,  # A/B测试持续天数
        }
    
    def process_analysis_feedback(self, user_id: int, analysis_record_id: int, 
                                user_modifications: Dict = None, 
                                user_rating: int = None, comments: str = None) -> Dict[str, Any]:
        """
        处理分析结果的用户反馈
        
        Args:
            user_id: 用户ID
            analysis_record_id: 分析记录ID
            user_modifications: 用户修正数据
            user_rating: 用户评分(1-5)
            comments: 用户评论
            
        Returns:
            反馈处理结果
        """
        try:
            logger.info(f"处理用户{user_id}对分析记录{analysis_record_id}的反馈")
            
            # 获取分析记录
            record = AIAnalysisRecord.query.get(analysis_record_id)
            if not record:
                raise ValueError(f"分析记录不存在: {analysis_record_id}")
            
            # 更新分析记录的用户修正数据
            if user_modifications:
                record.user_modifications = user_modifications
                record.save()
            
            # 分析反馈内容
            feedback_analysis = self._analyze_user_feedback(
                record, user_modifications, user_rating, comments
            )
            
            # 更新用户分析模式
            self._update_user_patterns_from_feedback(user_id, record, feedback_analysis)
            
            # 检查是否需要触发优化
            optimization_needed = self._check_optimization_trigger(user_id, feedback_analysis)
            
            result = {
                'user_id': user_id,
                'analysis_record_id': analysis_record_id,
                'feedback_processed': True,
                'feedback_analysis': feedback_analysis,
                'optimization_triggered': optimization_needed,
                'learning_updates': self._get_learning_updates(user_id, feedback_analysis)
            }
            
            # 如果需要优化，启动自动优化
            if optimization_needed and self.learning_config['auto_optimization_enabled']:
                optimization_result = self._trigger_auto_optimization(user_id, record.document_type)
                result['auto_optimization'] = optimization_result
            
            logger.info(f"用户{user_id}的反馈处理完成")
            return result
            
        except Exception as e:
            logger.error(f"处理用户{user_id}反馈失败: {str(e)}")
            raise
    
    def _analyze_user_feedback(self, record: AIAnalysisRecord, 
                             user_modifications: Dict = None,
                             user_rating: int = None, comments: str = None) -> Dict[str, Any]:
        """分析用户反馈内容"""
        analysis = {
            'has_modifications': bool(user_modifications),
            'modification_count': 0,
            'modified_fields': [],
            'modification_severity': 'none',
            'user_satisfaction': 'neutral',
            'feedback_quality': 'medium'
        }
        
        # 分析用户修正
        if user_modifications:
            basic_modifications = user_modifications.get('basic_info', {})
            analysis['modification_count'] = len(basic_modifications)
            analysis['modified_fields'] = list(basic_modifications.keys())
            
            # 计算修正严重程度
            original_data = record.get_extracted_data().get('basic_info', {})
            severity_score = 0
            
            for field, new_value in basic_modifications.items():
                original_value = original_data.get(field, '')
                if original_value != new_value:
                    # 根据修改类型计算严重程度
                    if not original_value:  # 原来为空
                        severity_score += 1
                    elif not new_value:  # 修改为空
                        severity_score += 2
                    else:  # 内容修改
                        severity_score += 3
            
            if severity_score >= 10:
                analysis['modification_severity'] = 'critical'
            elif severity_score >= 5:
                analysis['modification_severity'] = 'high'
            elif severity_score >= 2:
                analysis['modification_severity'] = 'medium'
            else:
                analysis['modification_severity'] = 'low'
        
        # 分析用户评分
        if user_rating:
            if user_rating >= 4:
                analysis['user_satisfaction'] = 'high'
            elif user_rating >= 3:
                analysis['user_satisfaction'] = 'medium'
            else:
                analysis['user_satisfaction'] = 'low'
        
        # 分析评论内容（简单关键词分析）
        if comments:
            positive_keywords = ['好', '准确', '正确', '满意', 'good', 'accurate', 'correct']
            negative_keywords = ['错误', '不准', '问题', 'wrong', 'incorrect', 'error']
            
            comment_lower = comments.lower()
            positive_count = sum(1 for word in positive_keywords if word in comment_lower)
            negative_count = sum(1 for word in negative_keywords if word in comment_lower)
            
            if positive_count > negative_count:
                analysis['comment_sentiment'] = 'positive'
            elif negative_count > positive_count:
                analysis['comment_sentiment'] = 'negative'
            else:
                analysis['comment_sentiment'] = 'neutral'
            
            analysis['comment_length'] = len(comments)
            analysis['feedback_quality'] = 'high' if len(comments) > 20 else 'medium'
        
        return analysis
    
    def _update_user_patterns_from_feedback(self, user_id: int, record: AIAnalysisRecord,
                                          feedback_analysis: Dict):
        """基于反馈更新用户分析模式"""
        try:
            extracted_data = record.get_extracted_data()
            user_modifications = record.get_user_modifications()
            confidence_scores = record.get_confidence_scores()
            
            # 更新每个字段的模式
            basic_info = extracted_data.get('basic_info', {})
            basic_modifications = user_modifications.get('basic_info', {}) if user_modifications else {}
            
            for field_name, original_value in basic_info.items():
                if field_name and original_value:  # 只处理有值的字段
                    # 查找或创建用户模式记录
                    pattern = UserAnalysisPattern.query.filter_by(
                        user_id=user_id,
                        document_type=record.document_type,
                        field_name=field_name
                    ).first()
                    
                    if not pattern:
                        pattern = UserAnalysisPattern()
                        pattern.user_id = user_id
                        pattern.document_type = record.document_type
                        pattern.field_name = field_name
                        pattern.field_category = self._get_field_category(field_name)
                    
                    # 更新统计数据
                    modification = basic_modifications.get(field_name) if field_name in basic_modifications else None
                    pattern.update_statistics(
                        {field_name: original_value, 'confidence': confidence_scores.get(field_name, 0.0)},
                        {field_name: modification} if modification else None
                    )
                    
                    pattern.save()
            
            logger.info(f"用户{user_id}的分析模式已更新")
            
        except Exception as e:
            logger.error(f"更新用户{user_id}分析模式失败: {str(e)}")
    
    def _get_field_category(self, field_name: str) -> str:
        """获取字段分类"""
        category_mapping = {
            'name': 'basic',
            'model': 'basic',
            'code': 'basic',
            'brand': 'basic',
            'price': 'financial',
            'cost': 'financial',
            'description': 'content',
            'specifications': 'technical',
            'features': 'technical',
            'performance': 'technical'
        }
        
        field_lower = field_name.lower()
        for key, category in category_mapping.items():
            if key in field_lower:
                return category
        
        return 'other'
    
    def _check_optimization_trigger(self, user_id: int, feedback_analysis: Dict) -> bool:
        """检查是否需要触发优化"""
        # 检查修正严重程度
        if feedback_analysis.get('modification_severity') in ['critical', 'high']:
            return True
        
        # 检查用户满意度
        if feedback_analysis.get('user_satisfaction') == 'low':
            return True
        
        # 检查最近的反馈趋势
        recent_feedback_trend = self._analyze_recent_feedback_trend(user_id)
        if recent_feedback_trend.get('declining_performance', False):
            return True
        
        # 检查累积反馈量
        if recent_feedback_trend.get('total_feedback_count', 0) >= self.learning_config['min_feedback_samples']:
            avg_modification_rate = recent_feedback_trend.get('avg_modification_rate', 0)
            if avg_modification_rate > 0.3:  # 修正率超过30%
                return True
        
        return False
    
    def _analyze_recent_feedback_trend(self, user_id: int) -> Dict[str, Any]:
        """分析最近的反馈趋势"""
        cutoff_date = datetime.utcnow() - timedelta(days=self.learning_config['feedback_window_days'])
        
        # 获取最近的分析记录
        recent_records = AIAnalysisRecord.query.filter(
            AIAnalysisRecord.user_id == user_id,
            AIAnalysisRecord.created_at >= cutoff_date
        ).order_by(AIAnalysisRecord.created_at.desc()).all()
        
        if not recent_records:
            return {'total_feedback_count': 0}
        
        # 分析趋势
        total_count = len(recent_records)
        records_with_modifications = [r for r in recent_records if r.get_user_modifications()]
        modification_rate = len(records_with_modifications) / total_count
        
        # 分析置信度趋势
        recent_confidences = []
        older_confidences = []
        mid_point = len(recent_records) // 2
        
        for i, record in enumerate(recent_records):
            confidence = record.get_confidence_scores().get('overall', 0.0)
            if i < mid_point:
                recent_confidences.append(confidence)
            else:
                older_confidences.append(confidence)
        
        avg_recent_confidence = sum(recent_confidences) / len(recent_confidences) if recent_confidences else 0.0
        avg_older_confidence = sum(older_confidences) / len(older_confidences) if older_confidences else 0.0
        
        confidence_declining = avg_recent_confidence < avg_older_confidence - 0.05
        
        # 分析准确率趋势
        recent_accuracy = (mid_point - len([r for r in recent_records[:mid_point] if r.get_user_modifications()])) / mid_point if mid_point > 0 else 1.0
        older_accuracy = (len(recent_records) - mid_point - len([r for r in recent_records[mid_point:] if r.get_user_modifications()])) / (len(recent_records) - mid_point) if len(recent_records) > mid_point else 1.0
        
        accuracy_declining = recent_accuracy < older_accuracy - 0.1
        
        return {
            'total_feedback_count': total_count,
            'avg_modification_rate': modification_rate,
            'avg_recent_confidence': avg_recent_confidence,
            'avg_older_confidence': avg_older_confidence,
            'confidence_declining': confidence_declining,
            'recent_accuracy': recent_accuracy,
            'older_accuracy': older_accuracy,
            'accuracy_declining': accuracy_declining,
            'declining_performance': confidence_declining or accuracy_declining
        }
    
    def _get_learning_updates(self, user_id: int, feedback_analysis: Dict) -> List[str]:
        """获取学习更新信息"""
        updates = []
        
        if feedback_analysis.get('has_modifications'):
            modified_fields = feedback_analysis.get('modified_fields', [])
            updates.append(f"更新了{len(modified_fields)}个字段的错误模式")
        
        if feedback_analysis.get('user_satisfaction') == 'low':
            updates.append("记录用户不满意反馈，将调整优化策略")
        
        if feedback_analysis.get('modification_severity') == 'critical':
            updates.append("检测到严重错误，将加强相关字段的优化")
        
        return updates
    
    def _trigger_auto_optimization(self, user_id: int, document_type: str) -> Dict[str, Any]:
        """触发自动优化"""
        try:
            logger.info(f"为用户{user_id}触发自动优化，文档类型：{document_type}")
            
            # 生成新的优化提示词
            optimization_result = self.optimization_engine.generate_optimized_prompt(
                user_id, document_type
            )
            
            # 检查是否需要创建A/B测试
            current_template = PromptTemplate.get_best_template(document_type, user_id)
            if current_template and current_template.usage_count > 10:
                # 创建A/B测试对比新旧提示词
                ab_test = self._create_optimization_ab_test(
                    user_id, current_template.base_prompt, 
                    optimization_result['optimized_prompt'], document_type
                )
                optimization_result['ab_test'] = ab_test.to_dict()
            
            return optimization_result
            
        except Exception as e:
            logger.error(f"用户{user_id}自动优化失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _create_optimization_ab_test(self, user_id: int, current_prompt: str, 
                                   optimized_prompt: str, document_type: str) -> PromptABTest:
        """为优化创建A/B测试"""
        test_name = f"用户{user_id}_优化测试_{document_type}_{int(datetime.utcnow().timestamp())}"
        
        ab_test = self.optimization_engine.create_ab_test(
            test_name=test_name,
            prompt_a=current_prompt,
            prompt_b=optimized_prompt,
            target_users=[user_id],
            document_types=[document_type] if document_type else None,
            test_ratio=0.5
        )
        
        # 设置测试持续时间
        ab_test.max_duration_days = self.learning_config['ab_test_duration_days']
        ab_test.save()
        
        return ab_test
    
    def evaluate_optimization_performance(self, optimization_id: int) -> Dict[str, Any]:
        """评估优化效果"""
        try:
            optimization = PromptOptimizationHistory.query.get(optimization_id)
            if not optimization:
                raise ValueError(f"优化记录不存在: {optimization_id}")
            
            # 获取优化后的分析记录
            cutoff_date = optimization.created_at
            
            query = AIAnalysisRecord.query.filter(
                AIAnalysisRecord.user_id == optimization.user_id,
                AIAnalysisRecord.created_at >= cutoff_date
            )
            
            if optimization.document_types:
                query = query.filter(AIAnalysisRecord.document_type.in_(optimization.document_types))
            
            post_optimization_records = query.all()
            
            if not post_optimization_records:
                return {
                    'optimization_id': optimization_id,
                    'evaluation_status': 'insufficient_data',
                    'message': '优化后数据不足，无法评估效果'
                }
            
            # 计算优化后的性能指标
            post_optimization_stats = self._calculate_performance_metrics(post_optimization_records)
            
            # 对比优化前的性能
            performance_before = optimization.performance_before or {}
            predicted_after = optimization.performance_after or {}
            
            # 计算实际改进
            actual_improvement = self._calculate_actual_improvement(
                performance_before, post_optimization_stats, predicted_after
            )
            
            # 更新优化记录
            optimization.performance_after = post_optimization_stats
            optimization.improvement_score = actual_improvement.get('overall_improvement', 0.0)
            optimization.save()
            
            evaluation_result = {
                'optimization_id': optimization_id,
                'evaluation_status': 'completed',
                'performance_before': performance_before,
                'performance_after': post_optimization_stats,
                'predicted_improvement': predicted_after,
                'actual_improvement': actual_improvement,
                'optimization_success': actual_improvement.get('overall_improvement', 0.0) > 0.02,  # 2%改进阈值
                'recommendation': self._generate_optimization_recommendation(actual_improvement)
            }
            
            logger.info(f"优化{optimization_id}效果评估完成")
            return evaluation_result
            
        except Exception as e:
            logger.error(f"评估优化{optimization_id}效果失败: {str(e)}")
            raise
    
    def _calculate_performance_metrics(self, records: List[AIAnalysisRecord]) -> Dict[str, float]:
        """计算性能指标"""
        if not records:
            return {}
        
        # 准确率（无用户修正的记录比例）
        records_without_modifications = [r for r in records if not r.get_user_modifications()]
        accuracy = len(records_without_modifications) / len(records)
        
        # 平均置信度
        all_confidences = []
        for record in records:
            confidence = record.get_confidence_scores().get('overall', 0.0)
            if confidence > 0:
                all_confidences.append(confidence)
        
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
        
        # 字段级准确率
        field_accuracy = {}
        field_counts = defaultdict(int)
        field_correct = defaultdict(int)
        
        for record in records:
            basic_info = record.get_extracted_data().get('basic_info', {})
            modifications = record.get_user_modifications()
            basic_modifications = modifications.get('basic_info', {}) if modifications else {}
            
            for field_name, value in basic_info.items():
                if value:  # 只统计有值的字段
                    field_counts[field_name] += 1
                    if field_name not in basic_modifications:
                        field_correct[field_name] += 1
        
        for field_name, total_count in field_counts.items():
            if total_count > 0:
                field_accuracy[field_name] = field_correct[field_name] / total_count
        
        return {
            'overall_accuracy': accuracy,
            'avg_confidence': avg_confidence,
            'total_records': len(records),
            'field_accuracy': field_accuracy,
            'avg_field_accuracy': sum(field_accuracy.values()) / len(field_accuracy) if field_accuracy else 0.0
        }
    
    def _calculate_actual_improvement(self, before_metrics: Dict, after_metrics: Dict,
                                    predicted_metrics: Dict) -> Dict[str, Any]:
        """计算实际改进效果"""
        accuracy_before = before_metrics.get('template_success_rate', 0.8)
        confidence_before = before_metrics.get('template_avg_confidence', 0.7)
        
        accuracy_after = after_metrics.get('overall_accuracy', 0.8)
        confidence_after = after_metrics.get('avg_confidence', 0.7)
        
        accuracy_improvement = accuracy_after - accuracy_before
        confidence_improvement = confidence_after - confidence_before
        
        # 对比预测值
        predicted_accuracy = predicted_metrics.get('predicted_accuracy', accuracy_before)
        predicted_confidence = predicted_metrics.get('predicted_confidence', confidence_before)
        
        accuracy_prediction_accuracy = 1 - abs(accuracy_after - predicted_accuracy)
        confidence_prediction_accuracy = 1 - abs(confidence_after - predicted_confidence)
        
        return {
            'accuracy_improvement': accuracy_improvement,
            'confidence_improvement': confidence_improvement,
            'overall_improvement': (accuracy_improvement + confidence_improvement) / 2,
            'prediction_accuracy': (accuracy_prediction_accuracy + confidence_prediction_accuracy) / 2,
            'exceeded_prediction': (accuracy_after > predicted_accuracy) and (confidence_after > predicted_confidence),
            'improvement_breakdown': {
                'accuracy': {'before': accuracy_before, 'after': accuracy_after, 'change': accuracy_improvement},
                'confidence': {'before': confidence_before, 'after': confidence_after, 'change': confidence_improvement}
            }
        }
    
    def _generate_optimization_recommendation(self, improvement_data: Dict) -> str:
        """生成优化建议"""
        overall_improvement = improvement_data.get('overall_improvement', 0.0)
        
        if overall_improvement > 0.05:  # 5%以上改进
            return "优化效果显著，建议继续使用当前优化策略"
        elif overall_improvement > 0.02:  # 2-5%改进
            return "优化效果良好，建议保持当前设置"
        elif overall_improvement > 0:  # 轻微改进
            return "优化效果一般，可考虑进一步调整优化参数"
        else:  # 无改进或下降
            return "优化效果不佳，建议回滚到之前的设置或尝试其他优化策略"
    
    def run_continuous_learning_cycle(self) -> Dict[str, Any]:
        """运行持续学习循环"""
        try:
            logger.info("开始持续学习循环")
            
            # 获取需要评估的优化记录
            cutoff_date = datetime.utcnow() - timedelta(days=7)  # 7天前的优化记录
            
            optimizations_to_evaluate = PromptOptimizationHistory.query.filter(
                PromptOptimizationHistory.created_at <= cutoff_date,
                PromptOptimizationHistory.improvement_score.is_(None)  # 还未评估的记录
            ).limit(10).all()  # 限制处理数量
            
            evaluation_results = []
            for optimization in optimizations_to_evaluate:
                try:
                    result = self.evaluate_optimization_performance(optimization.id)
                    evaluation_results.append(result)
                except Exception as e:
                    logger.error(f"评估优化{optimization.id}失败: {str(e)}")
                    continue
            
            # 检查需要结束的A/B测试
            completed_tests = self._check_and_complete_ab_tests()
            
            # 更新全局学习配置
            learning_updates = self._update_learning_configuration(evaluation_results)
            
            cycle_result = {
                'timestamp': datetime.utcnow().isoformat(),
                'evaluations_completed': len(evaluation_results),
                'ab_tests_completed': len(completed_tests),
                'learning_updates': learning_updates,
                'successful_optimizations': len([r for r in evaluation_results if r.get('optimization_success', False)]),
                'next_cycle_in_hours': 24  # 24小时后再次运行
            }
            
            logger.info(f"持续学习循环完成，评估{len(evaluation_results)}个优化")
            return cycle_result
            
        except Exception as e:
            logger.error(f"持续学习循环失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _check_and_complete_ab_tests(self) -> List[Dict]:
        """检查并完成A/B测试"""
        completed_tests = []
        
        # 获取应该结束的A/B测试
        active_tests = PromptABTest.query.filter_by(status='running').all()
        
        for test in active_tests:
            # 检查测试是否应该结束（时间或样本量）
            if test._check_test_completion():
                test.save()  # _check_test_completion 会更新状态
                
                if test.status == 'completed':
                    completed_tests.append({
                        'test_id': test.test_id,
                        'winner': test.winner,
                        'significance': test.is_significant,
                        'success_rate_a': test.success_rate_a,
                        'success_rate_b': test.success_rate_b
                    })
                    
                    # 如果B组（优化版本）获胜，更新默认模板
                    if test.winner == 'B' and test.template_b_id:
                        self._promote_winning_template(test.template_b_id)
        
        return completed_tests
    
    def _promote_winning_template(self, template_id: str):
        """提升获胜的模板"""
        template = PromptTemplate.query.filter_by(template_id=template_id).first()
        if template:
            template.priority += 10  # 提高优先级
            template.save()
            logger.info(f"提升获胜模板优先级: {template_id}")
    
    def _update_learning_configuration(self, evaluation_results: List[Dict]) -> List[str]:
        """根据评估结果更新学习配置"""
        updates = []
        
        if not evaluation_results:
            return updates
        
        # 分析成功率
        successful_optimizations = [r for r in evaluation_results if r.get('optimization_success', False)]
        success_rate = len(successful_optimizations) / len(evaluation_results)
        
        # 动态调整学习率
        if success_rate > 0.8:
            # 成功率高，可以提高学习率
            if self.learning_config['learning_rate'] < 0.2:
                self.learning_config['learning_rate'] += 0.02
                updates.append("提高学习率以加速优化")
        elif success_rate < 0.4:
            # 成功率低，降低学习率
            if self.learning_config['learning_rate'] > 0.05:
                self.learning_config['learning_rate'] -= 0.02
                updates.append("降低学习率以增加稳定性")
        
        # 调整性能阈值
        avg_improvement = sum(
            r.get('actual_improvement', {}).get('overall_improvement', 0.0)
            for r in successful_optimizations
        ) / len(successful_optimizations) if successful_optimizations else 0.0
        
        if avg_improvement > 0.1:  # 平均改进超过10%
            self.learning_config['performance_threshold'] = 0.08  # 提高阈值
            updates.append("提高性能改进阈值")
        elif avg_improvement < 0.03:  # 平均改进小于3%
            self.learning_config['performance_threshold'] = 0.03  # 降低阈值
            updates.append("降低性能改进阈值")
        
        return updates
    
    def get_learning_insights(self, user_id: int = None, days: int = 30) -> Dict[str, Any]:
        """获取学习洞察"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # 构建查询
            optimization_query = PromptOptimizationHistory.query.filter(
                PromptOptimizationHistory.created_at >= cutoff_date
            )
            
            if user_id:
                optimization_query = optimization_query.filter_by(user_id=user_id)
            
            optimizations = optimization_query.all()
            
            # 分析优化趋势
            insights = {
                'period': {'days': days, 'start_date': cutoff_date.isoformat()},
                'total_optimizations': len(optimizations),
                'optimization_types': {},
                'success_rate': 0.0,
                'avg_improvement': 0.0,
                'top_improvement_areas': [],
                'common_error_patterns': [],
                'recommendations': []
            }
            
            if not optimizations:
                insights['message'] = '暂无优化数据'
                return insights
            
            # 统计优化类型
            type_counts = defaultdict(int)
            successful_optimizations = []
            total_improvement = 0.0
            
            for opt in optimizations:
                type_counts[opt.optimization_type.value] += 1
                
                if opt.improvement_score and opt.improvement_score > 0.02:
                    successful_optimizations.append(opt)
                    total_improvement += opt.improvement_score
            
            insights['optimization_types'] = dict(type_counts)
            insights['success_rate'] = len(successful_optimizations) / len(optimizations)
            insights['avg_improvement'] = total_improvement / len(successful_optimizations) if successful_optimizations else 0.0
            
            # 分析改进领域
            improvement_areas = defaultdict(int)
            for opt in successful_optimizations:
                for field in opt.target_fields or []:
                    improvement_areas[field] += 1
            
            insights['top_improvement_areas'] = sorted(
                improvement_areas.items(), key=lambda x: x[1], reverse=True
            )[:5]
            
            # 生成建议
            insights['recommendations'] = self._generate_learning_recommendations(insights)
            
            return insights
            
        except Exception as e:
            logger.error(f"获取学习洞察失败: {str(e)}")
            raise
    
    def _generate_learning_recommendations(self, insights: Dict) -> List[str]:
        """生成学习建议"""
        recommendations = []
        
        success_rate = insights.get('success_rate', 0.0)
        avg_improvement = insights.get('avg_improvement', 0.0)
        
        if success_rate < 0.5:
            recommendations.append("优化成功率较低，建议增加历史数据收集时间或调整优化策略")
        elif success_rate > 0.8:
            recommendations.append("优化效果良好，可以考虑更频繁的自动优化")
        
        if avg_improvement < 0.03:
            recommendations.append("平均改进幅度较小，建议分析更细粒度的用户模式")
        
        optimization_types = insights.get('optimization_types', {})
        most_common_type = max(optimization_types, key=optimization_types.get) if optimization_types else None
        
        if most_common_type == 'error_prevention':
            recommendations.append("主要优化方向为错误预防，建议重点关注常见错误模式的识别")
        elif most_common_type == 'personalization':
            recommendations.append("个性化优化较多，说明用户差异明显，建议增强个性化算法")
        
        top_areas = insights.get('top_improvement_areas', [])
        if top_areas:
            top_field = top_areas[0][0]
            recommendations.append(f"'{top_field}'字段改进最多，建议作为重点优化目标")
        
        return recommendations