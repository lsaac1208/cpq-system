# -*- coding: utf-8 -*-
"""
Prompt优化引擎
基于历史数据分析结果，动态生成和优化AI分析的提示词
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import json
import re

from src.models.prompt_optimization import (
    PromptTemplate, PromptOptimizationHistory, OptimizationType,
    PromptABTest, UserAnalysisPattern
)
from src.services.historical_data_analyzer import HistoricalDataAnalyzer
from src.models.base import db

logger = logging.getLogger(__name__)

class PromptOptimizationEngine:
    """Prompt优化引擎"""
    
    def __init__(self):
        self.historical_analyzer = HistoricalDataAnalyzer()
        
        # 基础提示词模板
        self.base_prompt_template = """请分析以下产品规格文档，提取结构化的产品信息。

分析要求：
1. 仔细阅读文档内容，理解产品的基本信息
2. 提取以下关键字段的准确信息：
   - 产品名称（name）
   - 产品型号/编号（model/code）
   - 品牌（brand）
   - 价格（price）
   - 主要规格参数（specifications）
   - 产品描述（description）

3. 确保提取的信息准确、完整，避免遗漏重要细节
4. 对于不确定的信息，请标注置信度较低
5. 使用标准化的格式返回结构化数据

{dynamic_content}

请开始分析："""
        
        # 优化策略配置
        self.optimization_strategies = {
            'error_prevention': {
                'weight': 0.4,
                'enabled': True,
                'description': '基于历史错误模式预防常见错误'
            },
            'success_pattern': {
                'weight': 0.3,
                'enabled': True,
                'description': '复制成功分析的方法和策略'
            },
            'field_focus': {
                'weight': 0.2,
                'enabled': True,
                'description': '重点关注准确率较低的字段'
            },
            'personalization': {
                'weight': 0.1,
                'enabled': True,
                'description': '基于用户特征个性化调整'
            }
        }
        
    def generate_optimized_prompt(self, user_id: int, document_type: str = None, 
                                context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        为用户生成优化的提示词
        
        Args:
            user_id: 用户ID
            document_type: 文档类型
            context: 上下文信息（如文档内容预览）
            
        Returns:
            优化结果字典
        """
        try:
            logger.info(f"为用户{user_id}生成优化提示词，文档类型：{document_type}")
            
            # 分析用户历史模式
            user_analysis = self.historical_analyzer.analyze_user_patterns(user_id, document_type)
            
            # 获取或创建最佳模板
            template = self._get_best_template(document_type, user_id)
            
            # 生成优化的提示词
            if user_analysis.get('total_records', 0) >= 10:  # 有足够历史数据
                optimized_prompt = self._generate_personalized_prompt(
                    template, user_analysis, context
                )
                optimization_type = OptimizationType.PERSONALIZATION
            else:
                # 使用全局优化
                optimized_prompt = self._generate_global_optimized_prompt(
                    template, document_type, context
                )
                optimization_type = OptimizationType.ACCURACY_IMPROVEMENT
            
            # 记录优化历史
            optimization_record = self._record_optimization(
                user_id, template, optimized_prompt, optimization_type, user_analysis
            )
            
            result = {
                'user_id': user_id,
                'document_type': document_type,
                'optimization_id': optimization_record.id,
                'template_id': template.template_id,
                'optimized_prompt': optimized_prompt,
                'optimization_type': optimization_type.value,
                'optimization_features': self._extract_optimization_features(user_analysis),
                'expected_improvements': self._predict_improvements(user_analysis),
                'confidence_score': self._calculate_optimization_confidence(user_analysis)
            }
            
            logger.info(f"用户{user_id}的提示词优化完成，类型：{optimization_type.value}")
            return result
            
        except Exception as e:
            logger.error(f"生成用户{user_id}优化提示词失败: {str(e)}")
            raise
    
    def _get_best_template(self, document_type: str = None, user_id: int = None) -> PromptTemplate:
        """获取最佳提示词模板"""
        # 首先尝试获取现有的最佳模板
        template = PromptTemplate.get_best_template(document_type, user_id)
        
        if not template:
            # 创建默认模板
            template = self._create_default_template(document_type)
        
        return template
    
    def _create_default_template(self, document_type: str = None) -> PromptTemplate:
        """创建默认提示词模板"""
        template_id = f"default_{document_type or 'general'}_{int(datetime.utcnow().timestamp())}"
        
        template = PromptTemplate()
        template.template_id = template_id
        template.template_name = f"默认{document_type or '通用'}模板"
        template.description = f"为{document_type or '通用'}文档类型生成的默认优化模板"
        template.document_types = [document_type] if document_type else ["txt", "pdf", "docx"]
        template.base_prompt = self.base_prompt_template
        template.optimization_rules = [
            {"type": "error_prevention", "enabled": True, "weight": 0.4},
            {"type": "success_pattern", "enabled": True, "weight": 0.3},
            {"type": "field_focus", "enabled": True, "weight": 0.2}
        ]
        template.dynamic_segments = {
            "user_guidance": {
                "type": "conditional",
                "conditions": [
                    {
                        "condition": "len(value) > 0",
                        "content": "基于您的历史分析经验，请特别注意：\n{value}"
                    }
                ]
            }
        }
        template.is_active = True
        template.is_default = True
        template.save()
        
        logger.info(f"创建默认模板：{template_id}")
        return template
    
    def _generate_personalized_prompt(self, template: PromptTemplate, 
                                    user_analysis: Dict, context: Dict = None) -> str:
        """生成个性化提示词"""
        # 提取用户模式数据
        user_patterns = []
        field_patterns = user_analysis.get('field_patterns', {})
        
        for field_name, pattern in field_patterns.items():
            user_patterns.append({
                'field_name': field_name,
                'accuracy_rate': pattern['statistics']['accuracy_rate'],
                'error_patterns': pattern['error_analysis']['common_errors'],
                'error_frequency': pattern['error_analysis']['error_count'],
                'success_patterns': pattern.get('success_cases', [])
            })
        
        # 生成动态内容
        dynamic_content = self._build_dynamic_content(user_analysis, user_patterns)
        
        # 使用模板生成优化提示词
        optimized_prompt = template.generate_optimized_prompt(user_patterns, {
            'user_guidance': dynamic_content,
            'document_type': user_analysis.get('document_type'),
            'user_statistics': user_analysis.get('statistics', {})
        })
        
        return optimized_prompt
    
    def _generate_global_optimized_prompt(self, template: PromptTemplate, 
                                        document_type: str = None, context: Dict = None) -> str:
        """生成全局优化提示词（基于所有用户的错误模式）"""
        # 获取全局错误模式
        global_errors = self.historical_analyzer.get_global_error_patterns(document_type)
        
        # 构建全局优化内容
        if global_errors:
            error_guidance = "基于系统整体分析经验，请特别注意避免以下常见错误：\n"
            
            for i, error_pattern in enumerate(global_errors[:3], 1):
                field_name = error_pattern['field']
                common_errors = error_pattern['common_errors'][:2]  # 取前2个常见错误
                
                error_guidance += f"{i}. {field_name}字段：\n"
                for error in common_errors:
                    error_guidance += f"   - 避免将'{error['original']}'误识别为'{error['corrected']}'\n"
            
            # 替换模板中的动态内容
            base_prompt = template.base_prompt
            optimized_prompt = base_prompt.replace('{dynamic_content}', error_guidance)
        else:
            # 没有全局错误模式，使用基础模板
            optimized_prompt = template.base_prompt.replace('{dynamic_content}', 
                                                          "请仔细分析文档内容，确保提取信息的准确性。")
        
        return optimized_prompt
    
    def _build_dynamic_content(self, user_analysis: Dict, user_patterns: List[Dict]) -> str:
        """构建动态优化内容"""
        content_parts = []
        
        # 错误预防指导
        error_guidance = self._build_error_prevention_guidance(user_patterns)
        if error_guidance:
            content_parts.append(f"**错误预防指导：**\n{error_guidance}")
        
        # 成功经验复制
        success_guidance = self._build_success_guidance(user_analysis)
        if success_guidance:
            content_parts.append(f"**成功经验参考：**\n{success_guidance}")
        
        # 字段重点关注
        focus_guidance = self._build_field_focus_guidance(user_patterns)
        if focus_guidance:
            content_parts.append(f"**重点关注字段：**\n{focus_guidance}")
        
        # 个性化建议
        personal_tips = self._build_personalization_tips(user_analysis)
        if personal_tips:
            content_parts.append(f"**个性化建议：**\n{personal_tips}")
        
        return "\n\n".join(content_parts)
    
    def _build_error_prevention_guidance(self, user_patterns: List[Dict]) -> str:
        """构建错误预防指导"""
        guidance_parts = []
        
        # 按错误频率排序，优先处理最常见的错误
        error_fields = [
            p for p in user_patterns 
            if p.get('error_frequency', 0) > 2
        ]
        
        for pattern in sorted(error_fields, key=lambda x: x.get('error_frequency', 0), reverse=True)[:3]:
            field_name = pattern['field_name']
            error_patterns = pattern.get('error_patterns', [])[:2]  # 取前2个错误
            
            if error_patterns:
                guidance = f"- {field_name}字段：避免"
                error_examples = []
                for error in error_patterns:
                    original = error.get('original', '')
                    corrected = error.get('corrected', '')
                    if original and corrected:
                        error_examples.append(f"将'{original}'误识别为'{corrected}'")
                
                if error_examples:
                    guidance += "、".join(error_examples)
                    guidance_parts.append(guidance)
        
        return "\n".join(guidance_parts)
    
    def _build_success_guidance(self, user_analysis: Dict) -> str:
        """构建成功经验指导"""
        success_features = user_analysis.get('success_features', [])
        guidance_parts = []
        
        # 文档偏好指导
        doc_preferences = [f for f in success_features if f.get('type') == 'document_preference']
        if doc_preferences:
            pref = doc_preferences[0]
            guidance_parts.append(f"- 您在{pref['value']}类型文档上分析效果最佳")
        
        # 字段成功模式
        field_successes = [f for f in success_features if f.get('type') == 'field_success']
        for success in field_successes[:2]:  # 取前2个字段
            field_name = success['feature']
            avg_confidence = success.get('avg_confidence', 0)
            guidance_parts.append(
                f"- {field_name}字段：保持当前分析方法（平均置信度{avg_confidence:.1%}）"
            )
        
        return "\n".join(guidance_parts)
    
    def _build_field_focus_guidance(self, user_patterns: List[Dict]) -> str:
        """构建字段重点关注指导"""
        # 找出准确率较低的字段
        low_accuracy_fields = [
            p for p in user_patterns 
            if p.get('accuracy_rate', 1.0) < 0.7
        ]
        
        if not low_accuracy_fields:
            return ""
        
        guidance_parts = []
        for pattern in sorted(low_accuracy_fields, key=lambda x: x.get('accuracy_rate', 1.0))[:3]:
            field_name = pattern['field_name']
            accuracy = pattern.get('accuracy_rate', 0)
            guidance_parts.append(
                f"- {field_name}：当前准确率{accuracy:.1%}，需要特别仔细分析"
            )
        
        return "\n".join(guidance_parts)
    
    def _build_personalization_tips(self, user_analysis: Dict) -> str:
        """构建个性化建议"""
        statistics = user_analysis.get('statistics', {})
        tips = []
        
        # 基于整体表现的建议
        overall_accuracy = statistics.get('overall_accuracy', 0)
        if overall_accuracy < 0.8:
            tips.append("- 建议放慢分析速度，仔细核对每个字段的提取结果")
        
        avg_confidence = statistics.get('avg_confidence', 0)
        if avg_confidence < 0.7:
            tips.append("- 对于不确定的信息，请明确标注置信度较低")
        
        # 基于文档类型分布的建议
        doc_distribution = statistics.get('document_type_distribution', {})
        if len(doc_distribution) > 1:
            most_common_type = max(doc_distribution, key=doc_distribution.get)
            tips.append(f"- 您最熟悉{most_common_type}类型文档，可参考相似的分析经验")
        
        return "\n".join(tips) if tips else ""
    
    def _record_optimization(self, user_id: int, template: PromptTemplate, 
                           optimized_prompt: str, optimization_type: OptimizationType,
                           user_analysis: Dict) -> PromptOptimizationHistory:
        """记录优化历史"""
        record = PromptOptimizationHistory()
        record.user_id = user_id
        record.optimization_type = optimization_type
        record.optimization_name = f"用户{user_id}_{optimization_type.value}_{int(datetime.utcnow().timestamp())}"
        record.description = f"基于用户历史分析数据的{optimization_type.value}优化"
        record.before_prompt = template.base_prompt
        record.after_prompt = optimized_prompt
        
        # 计算优化差异
        record.optimization_diff = self._calculate_prompt_diff(template.base_prompt, optimized_prompt)
        
        # 记录性能预期
        record.performance_before = {
            'template_success_rate': template.success_rate,
            'template_avg_confidence': template.avg_confidence
        }
        
        # 预测优化后性能
        expected_improvement = self._predict_improvements(user_analysis)
        record.performance_after = expected_improvement
        record.improvement_score = expected_improvement.get('overall_improvement', 0.0)
        
        # 设置应用范围
        record.document_types = user_analysis.get('document_type') and [user_analysis['document_type']] or None
        record.target_fields = list(user_analysis.get('field_patterns', {}).keys())
        
        record.save()
        
        # 更新模板使用计数
        template.increment_usage()
        template.save()
        
        return record
    
    def _calculate_prompt_diff(self, before_prompt: str, after_prompt: str) -> Dict[str, Any]:
        """计算提示词差异"""
        before_lines = before_prompt.split('\n')
        after_lines = after_prompt.split('\n')
        
        # 简单的差异计算
        added_lines = [line for line in after_lines if line not in before_lines]
        removed_lines = [line for line in before_lines if line not in after_lines]
        
        return {
            'added_lines': added_lines[:10],  # 限制返回的行数
            'removed_lines': removed_lines[:10],
            'total_changes': len(added_lines) + len(removed_lines),
            'size_change': len(after_prompt) - len(before_prompt)
        }
    
    def _extract_optimization_features(self, user_analysis: Dict) -> List[str]:
        """提取优化特征"""
        features = []
        
        # 错误预防特征
        error_patterns = user_analysis.get('error_patterns', [])
        if error_patterns:
            critical_errors = [p for p in error_patterns if p.get('severity') == 'critical']
            features.append(f"预防{len(critical_errors)}个严重错误模式")
        
        # 字段焦点特征
        field_patterns = user_analysis.get('field_patterns', {})
        low_accuracy_fields = [
            field for field, pattern in field_patterns.items()
            if pattern['statistics']['accuracy_rate'] < 0.7
        ]
        if low_accuracy_fields:
            features.append(f"重点优化{len(low_accuracy_fields)}个低准确率字段")
        
        # 成功模式特征
        success_features = user_analysis.get('success_features', [])
        if success_features:
            features.append(f"应用{len(success_features)}个成功经验模式")
        
        # 个性化特征
        total_records = user_analysis.get('total_records', 0)
        if total_records >= 20:
            features.append("深度个性化优化")
        elif total_records >= 10:
            features.append("基础个性化优化")
        
        return features
    
    def _predict_improvements(self, user_analysis: Dict) -> Dict[str, Any]:
        """预测优化后的改进效果"""
        statistics = user_analysis.get('statistics', {})
        current_accuracy = statistics.get('overall_accuracy', 0.8)
        current_confidence = statistics.get('avg_confidence', 0.7)
        
        # 基于历史数据预测改进幅度
        field_patterns = user_analysis.get('field_patterns', {})
        error_patterns = user_analysis.get('error_patterns', [])
        
        # 计算潜在改进空间
        accuracy_improvement = 0.0
        confidence_improvement = 0.0
        
        if field_patterns:
            # 基于字段错误率预测准确率改进
            avg_field_accuracy = sum(
                p['statistics']['accuracy_rate'] for p in field_patterns.values()
            ) / len(field_patterns)
            
            accuracy_improvement = min(0.15, (0.9 - avg_field_accuracy) * 0.5)  # 最多改进15%
        
        if error_patterns:
            # 基于错误模式数量预测置信度改进
            critical_errors = len([p for p in error_patterns if p.get('severity') == 'critical'])
            confidence_improvement = min(0.10, critical_errors * 0.03)  # 每个严重错误改进3%
        
        return {
            'predicted_accuracy': min(0.95, current_accuracy + accuracy_improvement),
            'predicted_confidence': min(0.95, current_confidence + confidence_improvement),
            'accuracy_improvement': accuracy_improvement,
            'confidence_improvement': confidence_improvement,
            'overall_improvement': (accuracy_improvement + confidence_improvement) / 2,
            'improvement_areas': self._identify_improvement_areas(user_analysis)
        }
    
    def _identify_improvement_areas(self, user_analysis: Dict) -> List[str]:
        """识别具体改进领域"""
        areas = []
        
        # 准确率改进领域
        field_patterns = user_analysis.get('field_patterns', {})
        low_accuracy_fields = [
            field for field, pattern in field_patterns.items()
            if pattern['statistics']['accuracy_rate'] < 0.7
        ]
        if low_accuracy_fields:
            areas.append(f"字段准确率提升：{', '.join(low_accuracy_fields[:3])}")
        
        # 置信度改进领域
        statistics = user_analysis.get('statistics', {})
        if statistics.get('avg_confidence', 0) < 0.7:
            areas.append("整体置信度提升")
        
        # 错误减少领域
        error_patterns = user_analysis.get('error_patterns', [])
        if error_patterns:
            high_frequency_errors = [
                p['field_name'] for p in error_patterns
                if p.get('error_frequency', 0) > 5
            ]
            if high_frequency_errors:
                areas.append(f"减少常见错误：{', '.join(high_frequency_errors[:2])}")
        
        return areas
    
    def _calculate_optimization_confidence(self, user_analysis: Dict) -> float:
        """计算优化置信度"""
        confidence_factors = []
        
        # 数据量因子
        total_records = user_analysis.get('total_records', 0)
        data_confidence = min(1.0, total_records / 50)  # 50条记录达到满分
        confidence_factors.append(data_confidence * 0.4)
        
        # 模式清晰度因子
        error_patterns = user_analysis.get('error_patterns', [])
        pattern_confidence = min(1.0, len(error_patterns) / 10)  # 10个错误模式达到满分
        confidence_factors.append(pattern_confidence * 0.3)
        
        # 改进空间因子
        statistics = user_analysis.get('statistics', {})
        current_accuracy = statistics.get('overall_accuracy', 0.8)
        improvement_space = 1.0 - current_accuracy  # 准确率越低，改进空间越大
        space_confidence = min(1.0, improvement_space * 2)
        confidence_factors.append(space_confidence * 0.3)
        
        return sum(confidence_factors)
    
    def create_ab_test(self, test_name: str, prompt_a: str, prompt_b: str,
                      target_users: List[int] = None, document_types: List[str] = None,
                      test_ratio: float = 0.5) -> PromptABTest:
        """创建A/B测试"""
        test_id = f"ab_test_{int(datetime.utcnow().timestamp())}"
        
        ab_test = PromptABTest()
        ab_test.test_id = test_id
        ab_test.test_name = test_name
        ab_test.description = f"提示词A/B测试：{test_name}"
        ab_test.prompt_a = prompt_a
        ab_test.prompt_b = prompt_b
        ab_test.target_users = target_users
        ab_test.document_types = document_types
        ab_test.test_ratio = test_ratio
        ab_test.save()
        
        logger.info(f"创建A/B测试：{test_id}")
        return ab_test
    
    def get_prompt_for_user(self, user_id: int, document_type: str = None) -> Tuple[str, Optional[str]]:
        """
        为用户获取提示词（考虑A/B测试）
        
        Returns:
            (prompt, ab_test_group) - 提示词和A/B测试组别
        """
        # 检查是否有活跃的A/B测试
        ab_test = PromptABTest.get_active_test(user_id, document_type)
        
        if ab_test:
            # 分配A/B测试组
            group = ab_test.assign_group(user_id)
            prompt = ab_test.prompt_a if group == 'A' else ab_test.prompt_b
            return prompt, f"{ab_test.test_id}:{group}"
        
        # 没有A/B测试，使用常规优化
        optimization_result = self.generate_optimized_prompt(user_id, document_type)
        return optimization_result['optimized_prompt'], None
    
    def record_prompt_feedback(self, user_id: int, optimization_id: int = None,
                             ab_test_info: str = None, success: bool = True,
                             confidence: float = None, user_modifications: Dict = None):
        """记录提示词反馈"""
        try:
            # 记录A/B测试反馈
            if ab_test_info:
                test_id, group = ab_test_info.split(':')
                ab_test = PromptABTest.query.filter_by(test_id=test_id).first()
                if ab_test:
                    ab_test.record_test_result(group, success, confidence)
                    ab_test.save()
            
            # 记录优化历史反馈
            if optimization_id:
                optimization = PromptOptimizationHistory.query.get(optimization_id)
                if optimization:
                    optimization.update_success_rate(success)
                    optimization.save()
                    
                    # 更新相关模板的性能
                    # 这里可以根据模板ID更新模板性能
            
            logger.info(f"用户{user_id}提示词反馈已记录")
            
        except Exception as e:
            logger.error(f"记录用户{user_id}提示词反馈失败: {str(e)}")
            raise