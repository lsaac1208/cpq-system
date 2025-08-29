# -*- coding: utf-8 -*-
"""
AI分析记录数据模型
记录AI分析过程和结果，用于追踪和优化
"""
import json
from datetime import datetime
from .base import db, BaseModel
from sqlalchemy.dialects.sqlite import JSON

class AIAnalysisRecord(BaseModel):
    """AI分析记录模型"""
    
    __tablename__ = 'ai_analysis_records'
    
    # 基础信息
    document_name = db.Column(db.String(255), nullable=False, comment='文档名称')
    document_type = db.Column(db.String(50), nullable=False, comment='文档类型')
    document_size = db.Column(db.Integer, comment='文档大小(字节)')
    
    # 分析内容
    original_text = db.Column(db.Text, comment='原始文本内容')
    text_length = db.Column(db.Integer, comment='文本长度')
    word_count = db.Column(db.Integer, comment='单词数量')
    
    # AI分析结果
    extracted_data = db.Column(JSON, comment='提取的产品数据')
    confidence_scores = db.Column(JSON, comment='置信度分数')
    analysis_summary = db.Column(db.Text, comment='分析摘要')
    
    # 用户修正记录
    user_modifications = db.Column(JSON, comment='用户修改记录')
    final_data = db.Column(JSON, comment='最终确认的数据')
    
    # 关联信息
    created_product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True, comment='创建的产品ID')
    user_id = db.Column(db.Integer, nullable=True, comment='操作用户ID')
    
    # 性能指标
    analysis_duration = db.Column(db.Integer, comment='分析耗时(秒)')
    api_tokens_used = db.Column(db.Integer, comment='API消耗token数')
    api_cost = db.Column(db.Numeric(10, 4), comment='API调用成本')
    
    # 状态标记
    status = db.Column(db.String(20), default='completed', comment='分析状态')
    success = db.Column(db.Boolean, default=True, comment='分析是否成功')
    error_message = db.Column(db.Text, comment='错误信息')
    
    # 关系
    created_product = db.relationship('Product', backref='ai_analysis_records', lazy=True)
    
    def get_extracted_data(self):
        """获取提取的数据为dict"""
        if self.extracted_data:
            return self.extracted_data if isinstance(self.extracted_data, dict) else json.loads(self.extracted_data)
        return {}
    
    def set_extracted_data(self, data_dict):
        """设置提取的数据从dict"""
        self.extracted_data = data_dict
    
    def get_confidence_scores(self):
        """获取置信度分数为dict"""
        if self.confidence_scores:
            return self.confidence_scores if isinstance(self.confidence_scores, dict) else json.loads(self.confidence_scores)
        return {}
    
    def set_confidence_scores(self, scores_dict):
        """设置置信度分数从dict"""
        self.confidence_scores = scores_dict
    
    def get_user_modifications(self):
        """获取用户修改记录为dict"""
        if self.user_modifications:
            return self.user_modifications if isinstance(self.user_modifications, dict) else json.loads(self.user_modifications)
        return {}
    
    def set_user_modifications(self, modifications_dict):
        """设置用户修改记录从dict"""
        self.user_modifications = modifications_dict
    
    def get_final_data(self):
        """获取最终数据为dict"""
        if self.final_data:
            return self.final_data if isinstance(self.final_data, dict) else json.loads(self.final_data)
        return {}
    
    def set_final_data(self, data_dict):
        """设置最终数据从dict"""
        self.final_data = data_dict
    
    def calculate_modification_rate(self):
        """计算用户修改率"""
        modifications = self.get_user_modifications()
        if not modifications:
            return 0.0
        
        total_fields = len(self.get_extracted_data().get('basic_info', {}))
        if total_fields == 0:
            return 0.0
        
        modified_fields = len(modifications.get('basic_info', {}))
        return modified_fields / total_fields
    
    def get_overall_confidence(self):
        """获取总体置信度"""
        scores = self.get_confidence_scores()
        return scores.get('overall', 0.0)
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        
        # 添加计算字段
        data['extracted_data'] = self.get_extracted_data()
        data['confidence_scores'] = self.get_confidence_scores()
        data['user_modifications'] = self.get_user_modifications()
        data['final_data'] = self.get_final_data()
        data['modification_rate'] = self.calculate_modification_rate()
        data['overall_confidence'] = self.get_overall_confidence()
        
        # 添加关联产品信息
        if self.created_product:
            data['created_product'] = {
                'id': self.created_product.id,
                'name': self.created_product.name,
                'code': self.created_product.code
            }
        
        return data
    
    @classmethod
    def create_from_analysis(cls, analysis_result: dict, user_id: int = None):
        """从分析结果创建记录"""
        doc_info = analysis_result.get('document_info', {})
        extracted_data = analysis_result.get('extracted_data', {})
        confidence_scores = analysis_result.get('confidence_scores', {})
        
        record = cls(
            document_name=doc_info.get('filename', 'unknown'),
            document_type=doc_info.get('type', 'unknown'),
            document_size=doc_info.get('size', 0),
            text_length=doc_info.get('text_length', 0),
            word_count=doc_info.get('word_count', 0),
            analysis_duration=doc_info.get('analysis_duration', 0),
            user_id=user_id,
            success=analysis_result.get('success', False),
            error_message=analysis_result.get('error'),
            status='completed' if analysis_result.get('success') else 'failed'
        )
        
        if analysis_result.get('success'):
            record.set_extracted_data(extracted_data)
            record.set_confidence_scores(confidence_scores)
            
            # 生成分析摘要
            basic_info = extracted_data.get('basic_info', {})
            summary_parts = []
            if basic_info.get('name'):
                summary_parts.append(f"Product: {basic_info['name']}")
            if basic_info.get('code'):
                summary_parts.append(f"Model: {basic_info['code']}")
            if confidence_scores.get('overall'):
                summary_parts.append(f"Confidence: {confidence_scores['overall']:.1%}")
            
            record.analysis_summary = " | ".join(summary_parts) if summary_parts else "Analysis completed"
        
        return record
    
    @classmethod
    def get_user_analysis_history(cls, user_id: int, limit: int = 10):
        """获取用户分析历史"""
        return cls.query.filter_by(user_id=user_id)\
                      .order_by(cls.created_at.desc())\
                      .limit(limit).all()
    
    @classmethod
    def get_success_rate(cls, days: int = 30):
        """获取指定天数内的成功率"""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        total = cls.query.filter(cls.created_at >= cutoff_date).count()
        if total == 0:
            return 1.0
        
        successful = cls.query.filter(
            cls.created_at >= cutoff_date,
            cls.success == True
        ).count()
        
        return successful / total
    
    @classmethod
    def get_average_confidence(cls, days: int = 30):
        """获取平均置信度"""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        records = cls.query.filter(
            cls.created_at >= cutoff_date,
            cls.success == True
        ).all()
        
        if not records:
            return 0.0
        
        confidences = [record.get_overall_confidence() for record in records]
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    def __repr__(self):
        return f'<AIAnalysisRecord {self.id}: {self.document_name} ({self.status})>'


class AIAnalysisSettings(BaseModel):
    """AI分析设置模型"""
    
    __tablename__ = 'ai_analysis_settings'
    
    # 设置键值
    setting_key = db.Column(db.String(100), unique=True, nullable=False, comment='设置键')
    setting_value = db.Column(JSON, nullable=False, comment='设置值')
    description = db.Column(db.Text, comment='设置描述')
    category = db.Column(db.String(50), default='general', comment='设置分类')
    
    # 管理信息
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    updated_by = db.Column(db.Integer, comment='更新用户ID')
    
    @classmethod
    def get_setting(cls, key: str, default=None):
        """获取设置值"""
        setting = cls.query.filter_by(setting_key=key, is_active=True).first()
        if setting:
            return setting.setting_value
        return default
    
    @classmethod
    def set_setting(cls, key: str, value, description: str = None, user_id: int = None):
        """设置配置值"""
        setting = cls.query.filter_by(setting_key=key).first()
        if setting:
            setting.setting_value = value
            setting.updated_by = user_id
            if description:
                setting.description = description
        else:
            setting = cls(
                setting_key=key,
                setting_value=value,
                description=description,
                updated_by=user_id
            )
            db.session.add(setting)
        
        setting.save()
        return setting
    
    def __repr__(self):
        return f'<AIAnalysisSettings {self.setting_key}>'