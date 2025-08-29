# -*- coding: utf-8 -*-
"""
历史数据优化Prompt相关数据模型
用于存储和管理AI分析的优化数据和学习记录
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum
from typing import Dict, List, Any, Optional

class OptimizationType(enum.Enum):
    """优化类型"""
    ERROR_PREVENTION = 'error_prevention'    # 错误预防优化
    ACCURACY_IMPROVEMENT = 'accuracy_improvement'  # 准确率提升优化
    PERSONALIZATION = 'personalization'     # 个性化优化
    SUCCESS_PATTERN = 'success_pattern'     # 成功模式优化
    FIELD_FOCUS = 'field_focus'             # 字段关注优化

class PromptOptimizationHistory(BaseModel):
    """Prompt优化历史记录模型"""
    __tablename__ = 'prompt_optimization_history'
    
    id = Column(Integer, primary_key=True)
    
    # 用户信息
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True, comment='用户ID（为空表示全局优化）')
    user = relationship("User", backref="prompt_optimizations")
    
    # 优化信息
    optimization_type = Column(Enum(OptimizationType), nullable=False, comment='优化类型')
    optimization_name = Column(String(200), nullable=False, comment='优化名称')
    description = Column(Text, comment='优化描述')
    
    # 提示词内容
    before_prompt = Column(Text, comment='优化前的提示词')
    after_prompt = Column(Text, nullable=False, comment='优化后的提示词')
    optimization_diff = Column(JSON, comment='优化差异详情')
    
    # 性能指标
    performance_before = Column(JSON, comment='优化前性能指标')
    performance_after = Column(JSON, comment='优化后性能指标')
    improvement_score = Column(Float, comment='改进分数')
    
    # 应用范围
    document_types = Column(JSON, comment='适用文档类型列表')
    target_fields = Column(JSON, comment='目标优化字段')
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment='是否启用')
    usage_count = Column(Integer, default=0, comment='使用次数')
    success_rate = Column(Float, comment='成功率')
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    created_by = Column(Integer, comment='创建者ID')
    
    def __repr__(self):
        return f'<PromptOptimizationHistory {self.id}: {self.optimization_name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'optimization_type': self.optimization_type.value,
            'optimization_name': self.optimization_name,
            'description': self.description,
            'before_prompt': self.before_prompt,
            'after_prompt': self.after_prompt,
            'optimization_diff': self.optimization_diff,
            'performance_before': self.performance_before,
            'performance_after': self.performance_after,
            'improvement_score': self.improvement_score,
            'document_types': self.document_types,
            'target_fields': self.target_fields,
            'is_active': self.is_active,
            'usage_count': self.usage_count,
            'success_rate': self.success_rate,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    def increment_usage(self):
        """增加使用次数"""
        self.usage_count += 1
        self.updated_at = datetime.utcnow()
        return self
    
    def update_success_rate(self, success: bool):
        """更新成功率"""
        if self.success_rate is None:
            self.success_rate = 1.0 if success else 0.0
        else:
            # 使用滑动平均更新成功率
            alpha = 0.1  # 学习率
            new_rate = 1.0 if success else 0.0
            self.success_rate = (1 - alpha) * self.success_rate + alpha * new_rate
        
        self.updated_at = datetime.utcnow()
        return self


class UserAnalysisPattern(BaseModel):
    """用户分析模式记录模型"""
    __tablename__ = 'user_analysis_patterns'
    
    id = Column(Integer, primary_key=True)
    
    # 用户信息
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True, comment='用户ID')
    user = relationship("User", backref="analysis_patterns")
    
    # 模式分类
    document_type = Column(String(50), comment='文档类型')
    field_name = Column(String(100), comment='字段名称')
    field_category = Column(String(50), comment='字段分类')
    
    # 错误模式
    error_patterns = Column(JSON, comment='常见错误模式')
    error_frequency = Column(Integer, default=0, comment='错误频次')
    error_types = Column(JSON, comment='错误类型统计')
    
    # 成功模式
    success_patterns = Column(JSON, comment='成功分析模式')
    success_examples = Column(JSON, comment='成功案例样本')
    
    # 统计指标
    total_analyses = Column(Integer, default=0, comment='总分析次数')
    correct_analyses = Column(Integer, default=0, comment='正确分析次数')
    accuracy_rate = Column(Float, comment='准确率')
    modification_frequency = Column(Float, comment='修正频率')
    
    # 置信度统计
    avg_confidence = Column(Float, comment='平均置信度')
    confidence_distribution = Column(JSON, comment='置信度分布')
    
    # 时间统计
    analysis_duration_avg = Column(Float, comment='平均分析时长')
    last_analysis_at = Column(DateTime, comment='最后分析时间')
    last_updated = Column(DateTime, default=datetime.utcnow, comment='最后更新时间')
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    
    def __repr__(self):
        return f'<UserAnalysisPattern {self.user_id}:{self.field_name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'document_type': self.document_type,
            'field_name': self.field_name,
            'field_category': self.field_category,
            'error_patterns': self.error_patterns,
            'error_frequency': self.error_frequency,
            'error_types': self.error_types,
            'success_patterns': self.success_patterns,
            'success_examples': self.success_examples,
            'total_analyses': self.total_analyses,
            'correct_analyses': self.correct_analyses,
            'accuracy_rate': self.accuracy_rate,
            'modification_frequency': self.modification_frequency,
            'avg_confidence': self.avg_confidence,
            'confidence_distribution': self.confidence_distribution,
            'analysis_duration_avg': self.analysis_duration_avg,
            'last_analysis_at': self.last_analysis_at.isoformat() if self.last_analysis_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def update_statistics(self, analysis_result: dict, user_modification: dict = None):
        """更新统计数据"""
        if self.total_analyses is None:
            self.total_analyses = 0
        if self.correct_analyses is None:
            self.correct_analyses = 0
            
        self.total_analyses += 1
        self.last_analysis_at = datetime.utcnow()
        
        # 更新置信度统计
        confidence = analysis_result.get('confidence', 0.0)
        if self.avg_confidence is None:
            self.avg_confidence = confidence
        else:
            self.avg_confidence = (self.avg_confidence * (self.total_analyses - 1) + confidence) / self.total_analyses
        
        # 更新准确率
        if user_modification is None or not user_modification:
            self.correct_analyses += 1
        else:
            # 记录错误模式
            if self.error_patterns is None:
                self.error_patterns = []
            
            self.error_patterns.append({
                'original_value': analysis_result.get(self.field_name),
                'corrected_value': user_modification.get(self.field_name),
                'timestamp': datetime.utcnow().isoformat(),
                'confidence': confidence
            })
            
            self.error_frequency += 1
        
        # 计算准确率
        self.accuracy_rate = self.correct_analyses / self.total_analyses
        self.modification_frequency = self.error_frequency / self.total_analyses
        
        self.last_updated = datetime.utcnow()
        return self
    
    @classmethod
    def get_user_patterns(cls, user_id: int, document_type: str = None):
        """获取用户分析模式"""
        query = cls.query.filter_by(user_id=user_id)
        
        if document_type:
            query = query.filter_by(document_type=document_type)
        
        return query.order_by(cls.accuracy_rate.asc()).all()


class PromptTemplate(BaseModel):
    """优化提示词模板模型"""
    __tablename__ = 'prompt_templates'
    
    id = Column(Integer, primary_key=True)
    
    # 模板信息
    template_id = Column(String(100), unique=True, nullable=False, index=True, comment='模板ID')
    template_name = Column(String(200), nullable=False, comment='模板名称')
    description = Column(Text, comment='模板描述')
    version = Column(String(20), default='1.0', comment='模板版本')
    
    # 适用范围
    document_types = Column(JSON, comment='适用文档类型')
    target_fields = Column(JSON, comment='目标字段')
    user_groups = Column(JSON, comment='适用用户组')
    
    # 模板内容
    base_prompt = Column(Text, nullable=False, comment='基础提示词')
    optimization_rules = Column(JSON, comment='优化规则')
    dynamic_segments = Column(JSON, comment='动态片段配置')
    
    # 性能指标
    success_rate = Column(Float, comment='成功率')
    avg_confidence = Column(Float, comment='平均置信度')
    usage_count = Column(Integer, default=0, comment='使用次数')
    positive_feedback = Column(Integer, default=0, comment='正面反馈数')
    negative_feedback = Column(Integer, default=0, comment='负面反馈数')
    
    # 优化历史
    optimization_history = Column(JSON, comment='优化历史记录')
    parent_template_id = Column(String(100), comment='父模板ID')
    
    # 状态控制
    is_active = Column(Boolean, default=True, comment='是否启用')
    is_default = Column(Boolean, default=False, comment='是否默认模板')
    priority = Column(Integer, default=0, comment='优先级')
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    created_by = Column(Integer, comment='创建者ID')
    
    def __repr__(self):
        return f'<PromptTemplate {self.template_id}: {self.template_name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'template_id': self.template_id,
            'template_name': self.template_name,
            'description': self.description,
            'version': self.version,
            'document_types': self.document_types,
            'target_fields': self.target_fields,
            'user_groups': self.user_groups,
            'base_prompt': self.base_prompt,
            'optimization_rules': self.optimization_rules,
            'dynamic_segments': self.dynamic_segments,
            'success_rate': self.success_rate,
            'avg_confidence': self.avg_confidence,
            'usage_count': self.usage_count,
            'positive_feedback': self.positive_feedback,
            'negative_feedback': self.negative_feedback,
            'optimization_history': self.optimization_history,
            'parent_template_id': self.parent_template_id,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    def generate_optimized_prompt(self, user_patterns: List[Dict], context: Dict = None) -> str:
        """根据用户模式生成优化的提示词"""
        prompt = self.base_prompt
        
        # 应用优化规则
        if self.optimization_rules:
            for rule in self.optimization_rules:
                if rule.get('type') == 'error_prevention':
                    # 添加错误预防指导
                    error_guidance = self._generate_error_prevention(user_patterns)
                    if error_guidance:
                        prompt += f"\n\n特别注意避免以下常见错误：\n{error_guidance}"
                
                elif rule.get('type') == 'success_pattern':
                    # 添加成功模式指导
                    success_guidance = self._generate_success_guidance(user_patterns)
                    if success_guidance:
                        prompt += f"\n\n参考以下成功分析方法：\n{success_guidance}"
                
                elif rule.get('type') == 'field_focus':
                    # 添加字段重点关注
                    focus_guidance = self._generate_field_focus(user_patterns)
                    if focus_guidance:
                        prompt += f"\n\n重点关注以下字段：\n{focus_guidance}"
        
        # 应用动态片段
        if self.dynamic_segments and context:
            for segment_key, segment_config in self.dynamic_segments.items():
                if segment_key in context:
                    segment_content = self._generate_dynamic_segment(segment_config, context[segment_key])
                    prompt = prompt.replace(f"{{{{ {segment_key} }}}}", segment_content)
        
        return prompt
    
    def _generate_error_prevention(self, user_patterns: List[Dict]) -> str:
        """生成错误预防指导"""
        error_guidance = []
        
        for pattern in user_patterns:
            if pattern.get('error_patterns') and pattern.get('error_frequency', 0) > 2:
                field_name = pattern.get('field_name', '未知字段')
                common_errors = pattern['error_patterns'][:3]  # 取前3个常见错误
                
                error_text = f"- {field_name}字段："
                for error in common_errors:
                    original = error.get('original_value', '')
                    corrected = error.get('corrected_value', '')
                    error_text += f" 避免识别为'{original}'，正确应为'{corrected}'"
                
                error_guidance.append(error_text)
        
        return '\n'.join(error_guidance[:5])  # 最多显示5个错误预防
    
    def _generate_success_guidance(self, user_patterns: List[Dict]) -> str:
        """生成成功模式指导"""
        success_guidance = []
        
        for pattern in user_patterns:
            if pattern.get('success_patterns') and pattern.get('accuracy_rate', 0) > 0.8:
                field_name = pattern.get('field_name', '未知字段')
                success_examples = pattern['success_patterns'][:2]  # 取前2个成功案例
                
                success_text = f"- {field_name}字段的成功识别方法："
                for example in success_examples:
                    method = example.get('method', '')
                    if method:
                        success_text += f" {method}"
                
                success_guidance.append(success_text)
        
        return '\n'.join(success_guidance[:3])  # 最多显示3个成功指导
    
    def _generate_field_focus(self, user_patterns: List[Dict]) -> str:
        """生成字段关注指导"""
        # 根据错误率排序，优先关注错误率高的字段
        high_error_fields = [
            p for p in user_patterns 
            if p.get('accuracy_rate', 1.0) < 0.7
        ]
        
        if not high_error_fields:
            return ""
        
        focus_guidance = []
        for pattern in sorted(high_error_fields, key=lambda x: x.get('accuracy_rate', 1.0))[:5]:
            field_name = pattern.get('field_name', '')
            accuracy = pattern.get('accuracy_rate', 0)
            focus_guidance.append(f"- {field_name}（当前准确率：{accuracy:.1%}，需要特别仔细分析）")
        
        return '\n'.join(focus_guidance)
    
    def _generate_dynamic_segment(self, segment_config: Dict, context_value: Any) -> str:
        """生成动态片段内容"""
        segment_type = segment_config.get('type', 'text')
        
        if segment_type == 'conditional':
            conditions = segment_config.get('conditions', [])
            for condition in conditions:
                if self._evaluate_condition(condition.get('condition'), context_value):
                    return condition.get('content', '')
        
        elif segment_type == 'template':
            template = segment_config.get('template', '')
            return template.format(value=context_value)
        
        return str(context_value)
    
    def _evaluate_condition(self, condition: str, value: Any) -> bool:
        """评估条件表达式"""
        try:
            # 简单的条件评估，可以扩展更复杂的逻辑
            if 'value' in condition:
                return eval(condition.replace('value', str(value)))
            return False
        except:
            return False
    
    def update_performance(self, success: bool, confidence: float = None):
        """更新性能指标"""
        self.usage_count += 1
        
        # 更新成功率
        if self.success_rate is None:
            self.success_rate = 1.0 if success else 0.0
        else:
            alpha = 0.1  # 学习率
            new_rate = 1.0 if success else 0.0
            self.success_rate = (1 - alpha) * self.success_rate + alpha * new_rate
        
        # 更新平均置信度
        if confidence is not None:
            if self.avg_confidence is None:
                self.avg_confidence = confidence
            else:
                alpha = 0.1
                self.avg_confidence = (1 - alpha) * self.avg_confidence + alpha * confidence
        
        self.updated_at = datetime.utcnow()
        return self
    
    def increment_usage(self):
        """增加使用计数"""
        self.usage_count += 1
        self.updated_at = datetime.utcnow()
        return self
    
    @classmethod
    def get_best_template(cls, document_type: str = None, user_id: int = None):
        """获取最佳模板"""
        query = cls.query.filter_by(is_active=True)
        
        if document_type:
            # 筛选适用的文档类型
            query = query.filter(cls.document_types.contains([document_type]))
        
        # 按成功率和使用次数排序
        return query.order_by(
            cls.success_rate.desc().nullslast(),
            cls.usage_count.desc(),
            cls.priority.desc()
        ).first()


class PromptABTest(BaseModel):
    """Prompt A/B测试记录模型"""
    __tablename__ = 'prompt_ab_tests'
    
    id = Column(Integer, primary_key=True)
    
    # 测试信息
    test_id = Column(String(100), unique=True, nullable=False, index=True, comment='测试ID')
    test_name = Column(String(200), nullable=False, comment='测试名称')
    description = Column(Text, comment='测试描述')
    
    # 测试配置
    prompt_a = Column(Text, nullable=False, comment='提示词A')
    prompt_b = Column(Text, nullable=False, comment='提示词B')
    template_a_id = Column(String(100), comment='模板A的ID')
    template_b_id = Column(String(100), comment='模板B的ID')
    
    # 测试范围
    target_users = Column(JSON, comment='目标用户列表')
    document_types = Column(JSON, comment='测试文档类型')
    test_ratio = Column(Float, default=0.5, comment='A/B分流比例')
    
    # 测试结果
    total_tests_a = Column(Integer, default=0, comment='A组测试次数')
    total_tests_b = Column(Integer, default=0, comment='B组测试次数')
    success_rate_a = Column(Float, comment='A组成功率')
    success_rate_b = Column(Float, comment='B组成功率')
    avg_confidence_a = Column(Float, comment='A组平均置信度')
    avg_confidence_b = Column(Float, comment='B组平均置信度')
    
    # 统计显著性
    p_value = Column(Float, comment='统计显著性P值')
    confidence_interval = Column(JSON, comment='置信区间')
    is_significant = Column(Boolean, comment='是否显著差异')
    winner = Column(String(10), comment='获胜方：A或B')
    
    # 测试状态
    status = Column(String(20), default='running', comment='测试状态：running/completed/stopped')
    min_sample_size = Column(Integer, default=50, comment='最小样本量')
    max_duration_days = Column(Integer, default=30, comment='最大测试天数')
    
    # 时间信息
    start_time = Column(DateTime, default=datetime.utcnow, comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    created_by = Column(Integer, comment='创建者ID')
    
    def __repr__(self):
        return f'<PromptABTest {self.test_id}: {self.test_name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'test_id': self.test_id,
            'test_name': self.test_name,
            'description': self.description,
            'prompt_a': self.prompt_a,
            'prompt_b': self.prompt_b,
            'template_a_id': self.template_a_id,
            'template_b_id': self.template_b_id,
            'target_users': self.target_users,
            'document_types': self.document_types,
            'test_ratio': self.test_ratio,
            'total_tests_a': self.total_tests_a,
            'total_tests_b': self.total_tests_b,
            'success_rate_a': self.success_rate_a,
            'success_rate_b': self.success_rate_b,
            'avg_confidence_a': self.avg_confidence_a,
            'avg_confidence_b': self.avg_confidence_b,
            'p_value': self.p_value,
            'confidence_interval': self.confidence_interval,
            'is_significant': self.is_significant,
            'winner': self.winner,
            'status': self.status,
            'min_sample_size': self.min_sample_size,
            'max_duration_days': self.max_duration_days,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by
        }
    
    def assign_group(self, user_id: int) -> str:
        """为用户分配测试组"""
        import hashlib
        
        # 使用用户ID和测试ID的哈希值来确保一致性分配
        hash_input = f"{user_id}_{self.test_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16)
        
        # 根据哈希值和分流比例分配组别
        return 'A' if (hash_value % 100) < (self.test_ratio * 100) else 'B'
    
    def record_test_result(self, group: str, success: bool, confidence: float = None):
        """记录测试结果"""
        if group == 'A':
            self.total_tests_a += 1
            
            # 更新成功率
            if self.success_rate_a is None:
                self.success_rate_a = 1.0 if success else 0.0
            else:
                alpha = 1.0 / self.total_tests_a
                new_rate = 1.0 if success else 0.0
                self.success_rate_a = (1 - alpha) * self.success_rate_a + alpha * new_rate
            
            # 更新置信度
            if confidence is not None:
                if self.avg_confidence_a is None:
                    self.avg_confidence_a = confidence
                else:
                    alpha = 1.0 / self.total_tests_a
                    self.avg_confidence_a = (1 - alpha) * self.avg_confidence_a + alpha * confidence
        
        else:  # group == 'B'
            self.total_tests_b += 1
            
            # 更新成功率
            if self.success_rate_b is None:
                self.success_rate_b = 1.0 if success else 0.0
            else:
                alpha = 1.0 / self.total_tests_b
                new_rate = 1.0 if success else 0.0
                self.success_rate_b = (1 - alpha) * self.success_rate_b + alpha * new_rate
            
            # 更新置信度
            if confidence is not None:
                if self.avg_confidence_b is None:
                    self.avg_confidence_b = confidence
                else:
                    alpha = 1.0 / self.total_tests_b
                    self.avg_confidence_b = (1 - alpha) * self.avg_confidence_b + alpha * confidence
        
        # 检查是否应该结束测试
        self._check_test_completion()
        
        return self
    
    def _check_test_completion(self):
        """检查测试是否应该结束"""
        # 检查样本量
        if (self.total_tests_a + self.total_tests_b) >= self.min_sample_size:
            # 进行显著性检验
            self._calculate_significance()
            
            # 检查是否有显著差异
            if self.is_significant:
                self.status = 'completed'
                self.end_time = datetime.utcnow()
        
        # 检查测试时长
        if self.start_time:
            test_days = (datetime.utcnow() - self.start_time).days
            if test_days >= self.max_duration_days:
                self.status = 'completed'
                self.end_time = datetime.utcnow()
    
    def _calculate_significance(self):
        """计算统计显著性"""
        if (self.total_tests_a < 10 or self.total_tests_b < 10 or 
            self.success_rate_a is None or self.success_rate_b is None):
            return
        
        try:
            import scipy.stats as stats
            
            # 使用卡方检验或比例Z检验
            successes_a = int(self.success_rate_a * self.total_tests_a)
            successes_b = int(self.success_rate_b * self.total_tests_b)
            
            # 比例差异检验
            n1, n2 = self.total_tests_a, self.total_tests_b
            p1, p2 = successes_a / n1, successes_b / n2
            
            # 合并比例
            p_pooled = (successes_a + successes_b) / (n1 + n2)
            se = (p_pooled * (1 - p_pooled) * (1/n1 + 1/n2)) ** 0.5
            
            # Z统计量
            z = (p1 - p2) / se
            self.p_value = 2 * (1 - stats.norm.cdf(abs(z)))
            
            # 判断显著性（α = 0.05）
            self.is_significant = self.p_value < 0.05
            
            # 确定获胜方
            if self.is_significant:
                self.winner = 'A' if self.success_rate_a > self.success_rate_b else 'B'
            
        except ImportError:
            # 如果没有scipy，使用简单的差异判断
            diff = abs((self.success_rate_a or 0) - (self.success_rate_b or 0))
            self.is_significant = diff > 0.05  # 简单阈值
            if self.is_significant:
                self.winner = 'A' if (self.success_rate_a or 0) > (self.success_rate_b or 0) else 'B'
    
    @classmethod
    def get_active_test(cls, user_id: int, document_type: str = None):
        """获取用户的活跃测试"""
        query = cls.query.filter_by(status='running')
        
        # 筛选目标用户
        # 这里简化处理，实际可能需要更复杂的用户匹配逻辑
        if document_type:
            query = query.filter(cls.document_types.contains([document_type]))
        
        return query.first()