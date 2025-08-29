# -*- coding: utf-8 -*-
"""
文档对比分析数据库模型
存储多文档对比分析的结果和配置
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum
from typing import Dict, List, Any, Optional

class ComparisonStatus(enum.Enum):
    """对比分析状态"""
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

class ComparisonType(enum.Enum):
    """对比类型"""
    PRODUCT_SPECS = 'product_specs'      # 产品规格对比
    PRICE_ANALYSIS = 'price_analysis'    # 价格分析对比
    FEATURE_MATRIX = 'feature_matrix'    # 功能特性矩阵
    COMPETITIVE_ANALYSIS = 'competitive_analysis'  # 竞品分析
    CUSTOM = 'custom'                     # 自定义对比

class DocumentComparison(BaseModel):
    """文档对比分析模型"""
    __tablename__ = 'document_comparisons'
    
    id = Column(Integer, primary_key=True)
    
    # 对比信息
    comparison_id = Column(String(100), unique=True, nullable=False, index=True, comment='对比分析ID')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True, comment='用户ID')
    user = relationship("User", backref="document_comparisons")
    
    # 对比配置
    name = Column(String(200), nullable=False, comment='对比分析名称')
    description = Column(Text, comment='对比描述')
    comparison_type = Column(Enum(ComparisonType), nullable=False, comment='对比类型')
    status = Column(Enum(ComparisonStatus), default=ComparisonStatus.PENDING, nullable=False, index=True, comment='处理状态')
    
    # 文档信息
    document_count = Column(Integer, default=0, comment='参与对比的文档数量')
    primary_document_id = Column(Integer, ForeignKey('ai_analysis_records.id'), comment='主对比文档ID')
    primary_document = relationship("AIAnalysisRecord", foreign_keys=[primary_document_id])
    
    # 对比设置
    comparison_settings = Column(JSON, comment='对比设置和配置')
    
    # 时间信息
    start_time = Column(DateTime, comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')
    processing_duration = Column(Float, comment='处理耗时')
    
    # 结果统计
    total_differences = Column(Integer, default=0, comment='总差异数')
    significant_differences = Column(Integer, default=0, comment='重要差异数')
    similarities_count = Column(Integer, default=0, comment='相似项数量')
    confidence_score = Column(Float, comment='对比结果置信度')
    
    # 错误信息
    error_message = Column(Text, comment='错误信息')
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __repr__(self):
        return f'<DocumentComparison {self.comparison_id}: {self.status.value}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'comparison_id': self.comparison_id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'comparison_type': self.comparison_type.value,
            'status': self.status.value,
            'document_count': self.document_count,
            'primary_document_id': self.primary_document_id,
            'comparison_settings': self.comparison_settings,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'processing_duration': self.processing_duration,
            'total_differences': self.total_differences,
            'significant_differences': self.significant_differences,
            'similarities_count': self.similarities_count,
            'confidence_score': self.confidence_score,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def start_processing(self):
        """开始处理"""
        self.status = ComparisonStatus.PROCESSING
        self.start_time = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        return self
    
    def complete_processing(self, results: Dict[str, Any] = None, error_message: str = None):
        """完成处理"""
        self.status = ComparisonStatus.FAILED if error_message else ComparisonStatus.COMPLETED
        self.end_time = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        if self.start_time:
            self.processing_duration = (self.end_time - self.start_time).total_seconds()
        
        if error_message:
            self.error_message = error_message
        
        if results:
            self.total_differences = results.get('total_differences', 0)
            self.significant_differences = results.get('significant_differences', 0)
            self.similarities_count = results.get('similarities_count', 0)
            self.confidence_score = results.get('confidence_score', 0.0)
        
        return self
    
    def cancel_processing(self, reason: str = None):
        """取消处理"""
        self.status = ComparisonStatus.CANCELLED
        self.end_time = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        if self.start_time:
            self.processing_duration = (self.end_time - self.start_time).total_seconds()
        
        if reason:
            self.error_message = reason
        
        return self
    
    @classmethod
    def get_user_comparisons(cls, user_id: int, limit: int = 50):
        """获取用户的对比分析"""
        return cls.query.filter_by(user_id=user_id)\
                      .order_by(cls.created_at.desc())\
                      .limit(limit).all()
    
    @classmethod
    def get_active_comparisons(cls):
        """获取活跃的对比分析"""
        return cls.query.filter(cls.status.in_([
            ComparisonStatus.PENDING,
            ComparisonStatus.PROCESSING
        ])).all()


class ComparisonDocument(BaseModel):
    """对比文档关联模型"""
    __tablename__ = 'comparison_documents'
    
    id = Column(Integer, primary_key=True)
    
    # 关联信息
    comparison_id = Column(String(100), ForeignKey('document_comparisons.comparison_id'), nullable=False, index=True, comment='对比分析ID')
    comparison = relationship("DocumentComparison", backref="documents")
    
    analysis_record_id = Column(Integer, ForeignKey('ai_analysis_records.id'), nullable=False, comment='分析记录ID')
    analysis_record = relationship("AIAnalysisRecord", backref="comparison_documents")
    
    # 文档角色
    document_role = Column(String(50), default='secondary', comment='文档角色: primary/secondary/reference')
    document_label = Column(String(100), comment='文档标签/别名')
    display_order = Column(Integer, default=0, comment='显示顺序')
    
    # 对比权重
    comparison_weight = Column(Float, default=1.0, comment='对比权重')
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    
    def __repr__(self):
        return f'<ComparisonDocument {self.comparison_id}:{self.analysis_record_id}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'comparison_id': self.comparison_id,
            'analysis_record_id': self.analysis_record_id,
            'document_role': self.document_role,
            'document_label': self.document_label,
            'display_order': self.display_order,
            'comparison_weight': self.comparison_weight,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ComparisonResult(BaseModel):
    """对比结果模型"""
    __tablename__ = 'comparison_results'
    
    id = Column(Integer, primary_key=True)
    
    # 关联信息
    comparison_id = Column(String(100), ForeignKey('document_comparisons.comparison_id'), nullable=False, index=True, comment='对比分析ID')
    comparison = relationship("DocumentComparison", backref="results")
    
    # 结果分类
    result_type = Column(String(50), nullable=False, comment='结果类型: difference/similarity/summary/insight')
    category = Column(String(100), comment='结果分类')
    subcategory = Column(String(100), comment='结果子分类')
    
    # 结果内容
    title = Column(String(500), comment='结果标题')
    description = Column(Text, comment='结果描述')
    details = Column(JSON, comment='详细结果数据')
    
    # 重要性评分
    importance_score = Column(Float, default=0.0, comment='重要性评分')
    confidence_score = Column(Float, default=0.0, comment='置信度评分')
    
    # 涉及文档
    involved_documents = Column(JSON, comment='涉及的文档ID列表')
    
    # 位置信息
    source_locations = Column(JSON, comment='源位置信息')
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    
    def __repr__(self):
        return f'<ComparisonResult {self.comparison_id}:{self.result_type}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'comparison_id': self.comparison_id,
            'result_type': self.result_type,
            'category': self.category,
            'subcategory': self.subcategory,
            'title': self.title,
            'description': self.description,
            'details': self.details,
            'importance_score': self.importance_score,
            'confidence_score': self.confidence_score,
            'involved_documents': self.involved_documents,
            'source_locations': self.source_locations,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def get_comparison_results(cls, comparison_id: str, result_type: str = None):
        """获取对比结果"""
        query = cls.query.filter_by(comparison_id=comparison_id)
        
        if result_type:
            query = query.filter_by(result_type=result_type)
        
        return query.order_by(cls.importance_score.desc(), cls.created_at.desc()).all()
    
    @classmethod
    def get_significant_differences(cls, comparison_id: str, min_importance: float = 0.7):
        """获取重要差异"""
        return cls.query.filter(
            cls.comparison_id == comparison_id,
            cls.result_type == 'difference',
            cls.importance_score >= min_importance
        ).order_by(cls.importance_score.desc()).all()


class ComparisonTemplate(BaseModel):
    """对比模板模型"""
    __tablename__ = 'comparison_templates'
    
    id = Column(Integer, primary_key=True)
    
    # 模板信息
    template_id = Column(String(100), unique=True, nullable=False, index=True, comment='模板ID')
    name = Column(String(200), nullable=False, comment='模板名称')
    description = Column(Text, comment='模板描述')
    comparison_type = Column(Enum(ComparisonType), nullable=False, comment='对比类型')
    
    # 模板配置
    template_config = Column(JSON, nullable=False, comment='模板配置')
    comparison_fields = Column(JSON, comment='对比字段配置')
    output_format = Column(JSON, comment='输出格式配置')
    
    # 使用统计
    usage_count = Column(Integer, default=0, comment='使用次数')
    
    # 权限控制
    is_public = Column(Boolean, default=True, comment='是否公开')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建者ID')
    creator = relationship("User")
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __repr__(self):
        return f'<ComparisonTemplate {self.template_id}: {self.name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'comparison_type': self.comparison_type.value,
            'template_config': self.template_config,
            'comparison_fields': self.comparison_fields,
            'output_format': self.output_format,
            'usage_count': self.usage_count,
            'is_public': self.is_public,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def increment_usage(self):
        """增加使用次数"""
        self.usage_count += 1
        self.updated_at = datetime.utcnow()
        return self
    
    @classmethod
    def get_public_templates(cls, comparison_type: ComparisonType = None):
        """获取公开模板"""
        query = cls.query.filter_by(is_public=True)
        
        if comparison_type:
            query = query.filter_by(comparison_type=comparison_type)
        
        return query.order_by(cls.usage_count.desc(), cls.created_at.desc()).all()
    
    @classmethod
    def get_user_templates(cls, user_id: int):
        """获取用户模板"""
        return cls.query.filter_by(created_by=user_id)\
                      .order_by(cls.updated_at.desc()).all()