# -*- coding: utf-8 -*-
"""
学习模式数据库模型
存储用户修正模式和学习数据
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import BaseModel

class LearningPattern(BaseModel):
    """学习模式模型"""
    __tablename__ = 'learning_patterns'
    
    id = Column(Integer, primary_key=True)
    
    # 模式基本信息
    field_path = Column(String(200), nullable=False, index=True, comment='字段路径')
    field_category = Column(String(50), nullable=False, index=True, comment='字段分类')
    pattern_type = Column(String(50), nullable=False, index=True, comment='模式类型')
    
    # 修正信息
    original_value_type = Column(String(50), comment='原始值类型')
    original_value = Column(Text, comment='原始值')
    corrected_value_type = Column(String(50), comment='修正值类型') 
    corrected_value = Column(Text, comment='修正值')
    value_difference = Column(Float, default=0.0, comment='值差异度')
    
    # 文档上下文
    document_type = Column(String(20), index=True, comment='文档类型')
    document_category = Column(String(100), comment='产品分类')
    document_size_range = Column(String(20), comment='文档大小范围')
    
    # 用户信息
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True, comment='用户ID')
    user = relationship("User", backref="learning_patterns")
    
    # 统计信息
    frequency = Column(Integer, default=1, comment='出现频率')
    success_rate = Column(Float, default=1.0, comment='成功率')
    confidence_improvement = Column(Float, default=0.0, comment='置信度改进')
    last_seen = Column(DateTime, default=datetime.utcnow, comment='最后出现时间')
    
    # 学习权重
    learning_weight = Column(Float, default=1.0, comment='学习权重')
    is_validated = Column(Boolean, default=False, comment='是否已验证')
    validation_count = Column(Integer, default=0, comment='验证次数')
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __repr__(self):
        return f'<LearningPattern {self.field_path}: {self.pattern_type}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'field_path': self.field_path,
            'field_category': self.field_category,
            'pattern_type': self.pattern_type,
            'original_value': self.original_value,
            'corrected_value': self.corrected_value,
            'value_difference': self.value_difference,
            'document_type': self.document_type,
            'document_category': self.document_category,
            'user_id': self.user_id,
            'frequency': self.frequency,
            'success_rate': self.success_rate,
            'confidence_improvement': self.confidence_improvement,
            'learning_weight': self.learning_weight,
            'is_validated': self.is_validated,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def create_from_modification(cls, field_path: str, original_value: any, 
                               corrected_value: any, user_id: int,
                               document_info: dict = None):
        """从修正信息创建学习模式"""
        pattern = cls()
        pattern.field_path = field_path
        pattern.field_category = cls._categorize_field(field_path)
        pattern.pattern_type = cls._classify_pattern_type(original_value, corrected_value)
        
        # 存储值和类型
        pattern.original_value = str(original_value) if original_value is not None else None
        pattern.original_value_type = type(original_value).__name__ if original_value is not None else 'NoneType'
        pattern.corrected_value = str(corrected_value) if corrected_value is not None else None
        pattern.corrected_value_type = type(corrected_value).__name__ if corrected_value is not None else 'NoneType'
        
        # 计算值差异
        pattern.value_difference = cls._calculate_value_difference(original_value, corrected_value)
        
        # 设置用户和文档信息
        pattern.user_id = user_id
        if document_info:
            pattern.document_type = document_info.get('type', 'unknown')
            pattern.document_category = document_info.get('category', 'unknown')
            pattern.document_size_range = cls._categorize_document_size(document_info.get('size', 0))
        
        return pattern
    
    @classmethod
    def find_similar_patterns(cls, field_path: str, pattern_type: str, 
                            user_id: int = None, document_type: str = None):
        """查找相似的学习模式"""
        query = cls.query.filter(
            cls.field_path == field_path,
            cls.pattern_type == pattern_type
        )
        
        if user_id:
            query = query.filter(cls.user_id == user_id)
        
        if document_type:
            query = query.filter(cls.document_type == document_type)
        
        return query.all()
    
    @classmethod
    def get_user_patterns(cls, user_id: int, field_category: str = None, 
                         days: int = 90, min_frequency: int = 2):
        """获取用户的学习模式"""
        from datetime import datetime, timedelta
        
        query = cls.query.filter(
            cls.user_id == user_id,
            cls.frequency >= min_frequency,
            cls.last_seen >= datetime.utcnow() - timedelta(days=days)
        )
        
        if field_category:
            query = query.filter(cls.field_category == field_category)
        
        return query.order_by(cls.frequency.desc(), cls.learning_weight.desc()).all()
    
    @classmethod
    def get_global_patterns(cls, field_path: str = None, document_type: str = None,
                           min_frequency: int = 5, min_success_rate: float = 0.8):
        """获取全局学习模式"""
        query = cls.query.filter(
            cls.frequency >= min_frequency,
            cls.success_rate >= min_success_rate,
            cls.is_validated == True
        )
        
        if field_path:
            query = query.filter(cls.field_path == field_path)
        
        if document_type:
            query = query.filter(cls.document_type == document_type)
        
        return query.order_by(cls.frequency.desc()).all()
    
    def update_frequency(self):
        """更新使用频率"""
        self.frequency += 1
        self.last_seen = datetime.utcnow()
        
        # 动态调整学习权重
        if self.frequency > 10:
            self.learning_weight = min(2.0, self.learning_weight * 1.1)
        
        return self
    
    def update_success_rate(self, is_successful: bool):
        """更新成功率"""
        total_attempts = self.validation_count + 1
        current_successes = self.success_rate * self.validation_count
        
        if is_successful:
            current_successes += 1
        
        self.success_rate = current_successes / total_attempts
        self.validation_count = total_attempts
        
        # 如果成功率足够高，标记为已验证
        if self.validation_count >= 3 and self.success_rate >= 0.8:
            self.is_validated = True
        
        return self
    
    @staticmethod
    def _categorize_field(field_path: str) -> str:
        """字段分类"""
        field_categories = {
            'basic_info': ['name', 'code', 'category', 'base_price', 'description'],
            'technical': ['specifications', 'features', 'performance'],
            'contact': ['email', 'phone', 'address', 'contact'],
            'certification': ['certificate', 'standard', 'compliance'],
            'commercial': ['price', 'warranty', 'delivery', 'payment']
        }
        
        for category, keywords in field_categories.items():
            if any(keyword in field_path.lower() for keyword in keywords):
                return category
        
        return 'other'
    
    @staticmethod
    def _classify_pattern_type(original_value: any, corrected_value: any) -> str:
        """分类模式类型"""
        if original_value is None and corrected_value is not None:
            return 'value_addition'
        elif original_value is not None and corrected_value is None:
            return 'value_removal'
        elif type(original_value) != type(corrected_value):
            return 'type_conversion'
        elif isinstance(original_value, str) and isinstance(corrected_value, str):
            if len(original_value) != len(corrected_value):
                return 'format_correction'
            else:
                return 'content_refinement'
        elif isinstance(original_value, (int, float)) and isinstance(corrected_value, (int, float)):
            return 'numeric_adjustment'
        else:
            return 'value_replacement'
    
    @staticmethod
    def _calculate_value_difference(original: any, corrected: any) -> float:
        """计算值差异"""
        if original is None or corrected is None:
            return 1.0
        
        if isinstance(original, (int, float)) and isinstance(corrected, (int, float)):
            if original == 0:
                return 1.0 if corrected != 0 else 0.0
            return abs(corrected - original) / abs(original)
        
        elif isinstance(original, str) and isinstance(corrected, str):
            if len(original) == 0:
                return 1.0 if len(corrected) > 0 else 0.0
            elif len(corrected) == 0:
                return 1.0
            
            # 简单的字符串差异计算
            common_chars = set(original) & set(corrected)
            total_chars = set(original) | set(corrected)
            
            if len(total_chars) == 0:
                return 0.0
            
            return 1.0 - (len(common_chars) / len(total_chars))
        
        else:
            return 1.0 if original != corrected else 0.0
    
    @staticmethod
    def _categorize_document_size(size: int) -> str:
        """文档大小分类"""
        if size < 1024:  # < 1KB
            return 'tiny'
        elif size < 10 * 1024:  # < 10KB
            return 'small'
        elif size < 100 * 1024:  # < 100KB
            return 'medium'
        elif size < 1024 * 1024:  # < 1MB
            return 'large'
        else:
            return 'extra_large'

class LearningFeedback(BaseModel):
    """学习反馈模型"""
    __tablename__ = 'learning_feedback'
    
    id = Column(Integer, primary_key=True)
    
    # 关联信息
    analysis_record_id = Column(Integer, ForeignKey('ai_analysis_records.id'), nullable=False, comment='分析记录ID')
    analysis_record = relationship("AIAnalysisRecord", backref="learning_feedback")
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    user = relationship("User", backref="learning_feedback")
    
    # 反馈内容
    field_path = Column(String(200), nullable=False, comment='字段路径')
    original_confidence = Column(Float, comment='原始置信度')
    user_rating = Column(Integer, comment='用户评分 1-5')
    is_accurate = Column(Boolean, comment='是否准确')
    
    # 改进建议
    improvement_suggestion = Column(Text, comment='改进建议')
    feedback_type = Column(String(50), comment='反馈类型')
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    
    def __repr__(self):
        return f'<LearningFeedback {self.field_path}: {self.user_rating}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'analysis_record_id': self.analysis_record_id,
            'user_id': self.user_id,
            'field_path': self.field_path,
            'original_confidence': self.original_confidence,
            'user_rating': self.user_rating,
            'is_accurate': self.is_accurate,
            'improvement_suggestion': self.improvement_suggestion,
            'feedback_type': self.feedback_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }