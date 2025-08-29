# -*- coding: utf-8 -*-
"""
批量分析数据库模型
存储批量处理任务和结果
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum

class BatchStatus(enum.Enum):
    """批量处理状态"""
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

class FileStatus(enum.Enum):
    """文件处理状态"""
    QUEUED = 'queued'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    SKIPPED = 'skipped'

class BatchAnalysisJob(BaseModel):
    """批量分析任务模型"""
    __tablename__ = 'batch_analysis_jobs'
    
    id = Column(Integer, primary_key=True)
    
    # 任务信息
    job_id = Column(String(100), unique=True, nullable=False, index=True, comment='任务ID')
    job_name = Column(String(200), comment='任务名称')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True, comment='用户ID')
    user = relationship("User", backref="batch_analysis_jobs")
    
    # 任务状态
    status = Column(Enum(BatchStatus), default=BatchStatus.PENDING, nullable=False, index=True, comment='处理状态')
    total_files = Column(Integer, default=0, comment='总文件数')
    processed_files = Column(Integer, default=0, comment='已处理文件数')
    successful_files = Column(Integer, default=0, comment='成功文件数')
    failed_files = Column(Integer, default=0, comment='失败文件数')
    
    # 处理设置
    settings = Column(JSON, comment='处理设置')
    
    # 时间信息
    start_time = Column(DateTime, comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')
    estimated_duration = Column(Float, comment='预估处理时间')
    actual_duration = Column(Float, comment='实际处理时间')
    
    # 错误信息
    error_message = Column(Text, comment='错误信息')
    
    # 统计信息
    total_size = Column(Integer, default=0, comment='总文件大小')
    average_confidence = Column(Float, comment='平均置信度')
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __repr__(self):
        return f'<BatchAnalysisJob {self.job_id}: {self.status.value}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'job_id': self.job_id,
            'job_name': self.job_name,
            'user_id': self.user_id,
            'status': self.status.value,
            'total_files': self.total_files,
            'processed_files': self.processed_files,
            'successful_files': self.successful_files,
            'failed_files': self.failed_files,
            'progress_percentage': round((self.processed_files / self.total_files * 100), 2) if self.total_files > 0 else 0,
            'settings': self.settings,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'estimated_duration': self.estimated_duration,
            'actual_duration': self.actual_duration,
            'error_message': self.error_message,
            'total_size': self.total_size,
            'average_confidence': self.average_confidence,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def update_progress(self, processed: int = None, successful: int = None, failed: int = None):
        """更新进度"""
        if processed is not None:
            self.processed_files = processed
        if successful is not None:
            self.successful_files = successful
        if failed is not None:
            self.failed_files = failed
        
        # 更新时间戳
        self.updated_at = datetime.utcnow()
        
        # 如果处理完成，更新结束时间和实际耗时
        if self.processed_files >= self.total_files and self.status == BatchStatus.PROCESSING:
            self.status = BatchStatus.COMPLETED
            self.end_time = datetime.utcnow()
            if self.start_time:
                self.actual_duration = (self.end_time - self.start_time).total_seconds()
        
        return self
    
    def start_processing(self):
        """开始处理"""
        self.status = BatchStatus.PROCESSING
        self.start_time = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        return self
    
    def complete_processing(self, error_message: str = None):
        """完成处理"""
        self.status = BatchStatus.FAILED if error_message else BatchStatus.COMPLETED
        self.end_time = datetime.utcnow()
        self.error_message = error_message
        
        if self.start_time:
            self.actual_duration = (self.end_time - self.start_time).total_seconds()
        
        self.updated_at = datetime.utcnow()
        return self
    
    def cancel_processing(self):
        """取消处理"""
        self.status = BatchStatus.CANCELLED
        self.end_time = datetime.utcnow()
        
        if self.start_time:
            self.actual_duration = (self.end_time - self.start_time).total_seconds()
        
        self.updated_at = datetime.utcnow()
        return self
    
    def get_actual_duration(self):
        """获取实际处理时长"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def progress_percentage(self):
        """获取进度百分比"""
        if self.total_files == 0:
            return 0.0
        return round((self.processed_files / self.total_files * 100), 2)
    
    @classmethod
    def get_user_jobs(cls, user_id: int, limit: int = 20):
        """获取用户的批量任务"""
        return cls.query.filter_by(user_id=user_id)\
                      .order_by(cls.created_at.desc())\
                      .limit(limit).all()
    
    @classmethod
    def get_active_jobs(cls, user_id: int = None):
        """获取活跃任务"""
        query = cls.query.filter(cls.status.in_([BatchStatus.PENDING, BatchStatus.PROCESSING]))
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        return query.all()
    
    @classmethod
    def get_statistics(cls, user_id: int = None, days: int = 30):
        """获取统计信息"""
        from datetime import datetime, timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        query = cls.query.filter(cls.created_at >= start_date)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        jobs = query.all()
        
        total_jobs = len(jobs)
        completed_jobs = len([j for j in jobs if j.status == BatchStatus.COMPLETED])
        total_files = sum(j.total_files for j in jobs)
        successful_files = sum(j.successful_files for j in jobs)
        
        return {
            'total_jobs': total_jobs,
            'completed_jobs': completed_jobs,
            'success_rate': round((completed_jobs / total_jobs * 100), 2) if total_jobs > 0 else 0,
            'total_files': total_files,
            'successful_files': successful_files,
            'file_success_rate': round((successful_files / total_files * 100), 2) if total_files > 0 else 0,
            'average_files_per_job': round(total_files / total_jobs, 2) if total_jobs > 0 else 0
        }

class BatchAnalysisFile(BaseModel):
    """批量分析文件模型"""
    __tablename__ = 'batch_analysis_files'
    
    id = Column(Integer, primary_key=True)
    
    # 关联信息
    job_id = Column(String(100), ForeignKey('batch_analysis_jobs.job_id'), nullable=False, index=True, comment='批量任务ID')
    job = relationship("BatchAnalysisJob", backref="files")
    
    analysis_record_id = Column(Integer, ForeignKey('ai_analysis_records.id'), comment='分析记录ID')
    analysis_record = relationship("AIAnalysisRecord", backref="batch_files")
    
    # 文件信息
    file_id = Column(String(100), nullable=False, comment='文件ID')
    filename = Column(String(255), nullable=False, comment='文件名')
    original_filename = Column(String(255), nullable=False, comment='原始文件名')
    file_size = Column(Integer, comment='文件大小')
    file_type = Column(String(20), comment='文件类型')
    file_hash = Column(String(64), comment='文件哈希')
    
    # 处理状态
    status = Column(Enum(FileStatus), default=FileStatus.QUEUED, nullable=False, index=True, comment='处理状态')
    priority = Column(Integer, default=0, comment='处理优先级')
    
    # 时间信息
    start_time = Column(DateTime, comment='开始处理时间')
    end_time = Column(DateTime, comment='完成时间')
    processing_duration = Column(Float, comment='处理耗时')
    
    # 结果信息
    analysis_result = Column(JSON, comment='分析结果')
    confidence_score = Column(Float, comment='置信度分数')
    error_message = Column(Text, comment='错误信息')
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __repr__(self):
        return f'<BatchAnalysisFile {self.filename}: {self.status.value}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'job_id': self.job_id,
            'analysis_record_id': self.analysis_record_id,
            'file_id': self.file_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'status': self.status.value,
            'priority': self.priority,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'processing_duration': self.processing_duration,
            'confidence_score': self.confidence_score,
            'error_message': self.error_message,
            'has_result': self.analysis_result is not None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def start_processing(self):
        """开始处理"""
        self.status = FileStatus.PROCESSING
        self.start_time = datetime.utcnow()
        return self
    
    def complete_processing(self, analysis_result: dict = None, confidence_score: float = None, 
                          analysis_record_id: int = None, error_message: str = None):
        """完成处理"""
        self.status = FileStatus.FAILED if error_message else FileStatus.COMPLETED
        self.end_time = datetime.utcnow()
        
        if self.start_time:
            self.processing_duration = (self.end_time - self.start_time).total_seconds()
        
        if analysis_result:
            self.analysis_result = analysis_result
        
        if confidence_score is not None:
            self.confidence_score = confidence_score
        
        if analysis_record_id:
            self.analysis_record_id = analysis_record_id
        
        if error_message:
            self.error_message = error_message
        
        self.updated_at = datetime.utcnow()
        return self
    
    def skip_processing(self, reason: str = None):
        """跳过处理"""
        self.status = FileStatus.SKIPPED
        self.error_message = reason
        self.updated_at = datetime.utcnow()
        return self
    
    def get_processing_duration(self):
        """获取处理时长"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return self.processing_duration
    
    def fail_processing(self, error_message: str):
        """处理失败"""
        self.status = FileStatus.FAILED
        self.end_time = datetime.utcnow()
        self.error_message = error_message
        
        if self.start_time:
            self.processing_duration = (self.end_time - self.start_time).total_seconds()
        
        self.updated_at = datetime.utcnow()
        return self
    
    # 修改字段名映射
    @property
    def processing_start_time(self):
        """兼容属性名"""
        return self.start_time
    
    @processing_start_time.setter
    def processing_start_time(self, value):
        """兼容属性名"""
        self.start_time = value
    
    @property 
    def processing_end_time(self):
        """兼容属性名"""
        return self.end_time
    
    @processing_end_time.setter
    def processing_end_time(self, value):
        """兼容属性名"""
        self.end_time = value
    
    @classmethod
    def get_job_files(cls, job_id: str):
        """获取任务的所有文件"""
        return cls.query.filter_by(job_id=job_id)\
                      .order_by(cls.priority.desc(), cls.created_at.asc()).all()
    
    @classmethod
    def get_pending_files(cls, limit: int = 100):
        """获取待处理文件"""
        return cls.query.filter_by(status=FileStatus.QUEUED)\
                      .order_by(cls.priority.desc(), cls.created_at.asc())\
                      .limit(limit).all()

class BatchProcessingSummary(BaseModel):
    """批量处理摘要模型"""
    __tablename__ = 'batch_processing_summaries'
    
    id = Column(Integer, primary_key=True)
    
    # 关联信息
    job_id = Column(String(100), ForeignKey('batch_analysis_jobs.job_id'), nullable=False, unique=True, comment='批量任务ID')
    job = relationship("BatchAnalysisJob", backref="summary", uselist=False)
    
    # 摘要信息
    total_files = Column(Integer, default=0, comment='总文件数')
    successful_files = Column(Integer, default=0, comment='成功文件数')
    failed_files = Column(Integer, default=0, comment='失败文件数')
    skipped_files = Column(Integer, default=0, comment='跳过文件数')
    
    # 性能指标
    total_processing_time = Column(Float, comment='总处理时间')
    average_file_time = Column(Float, comment='平均文件处理时间')
    fastest_file_time = Column(Float, comment='最快处理时间')
    slowest_file_time = Column(Float, comment='最慢处理时间')
    
    # 质量指标
    average_confidence = Column(Float, comment='平均置信度')
    high_confidence_count = Column(Integer, default=0, comment='高置信度文件数')
    low_confidence_count = Column(Integer, default=0, comment='低置信度文件数')
    
    # 文件类型统计
    file_type_stats = Column(JSON, comment='文件类型统计')
    
    # 错误分析
    common_errors = Column(JSON, comment='常见错误统计')
    error_categories = Column(JSON, comment='错误分类统计')
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __repr__(self):
        return f'<BatchProcessingSummary {self.job_id}>'
    
    @property
    def success_rate(self):
        """成功率"""
        if self.total_files == 0:
            return 0.0
        return round((self.successful_files / self.total_files * 100), 2)
    
    @property
    def average_processing_time(self):
        """平均处理时间"""
        return self.average_file_time
    
    @property
    def summary_data(self):
        """摘要数据（兼容属性）"""
        return {
            'file_type_stats': self.file_type_stats,
            'common_errors': self.common_errors,
            'error_categories': self.error_categories
        }
    
    def to_dict(self):
        """转换为字典"""
        success_rate = round((self.successful_files / self.total_files * 100), 2) if self.total_files > 0 else 0
        
        return {
            'job_id': self.job_id,
            'total_files': self.total_files,
            'successful_files': self.successful_files,
            'failed_files': self.failed_files,
            'skipped_files': self.skipped_files,
            'success_rate': success_rate,
            'total_processing_time': self.total_processing_time,
            'average_file_time': self.average_file_time,
            'fastest_file_time': self.fastest_file_time,
            'slowest_file_time': self.slowest_file_time,
            'average_confidence': self.average_confidence,
            'high_confidence_count': self.high_confidence_count,
            'low_confidence_count': self.low_confidence_count,
            'file_type_stats': self.file_type_stats,
            'common_errors': self.common_errors,
            'error_categories': self.error_categories,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def create_from_job(cls, job_id: str):
        """从批量任务创建摘要"""
        files = BatchAnalysisFile.get_job_files(job_id)
        
        if not files:
            return None
        
        summary = cls()
        summary.job_id = job_id
        summary.total_files = len(files)
        
        # 计算状态统计
        summary.successful_files = len([f for f in files if f.status == FileStatus.COMPLETED])
        summary.failed_files = len([f for f in files if f.status == FileStatus.FAILED])
        summary.skipped_files = len([f for f in files if f.status == FileStatus.SKIPPED])
        
        # 计算性能指标
        completed_files = [f for f in files if f.processing_duration is not None]
        if completed_files:
            durations = [f.processing_duration for f in completed_files]
            summary.total_processing_time = sum(durations)
            summary.average_file_time = sum(durations) / len(durations)
            summary.fastest_file_time = min(durations)
            summary.slowest_file_time = max(durations)
        
        # 计算质量指标
        confidence_files = [f for f in files if f.confidence_score is not None]
        if confidence_files:
            confidence_scores = [f.confidence_score for f in confidence_files]
            summary.average_confidence = sum(confidence_scores) / len(confidence_scores)
            summary.high_confidence_count = len([s for s in confidence_scores if s >= 0.8])
            summary.low_confidence_count = len([s for s in confidence_scores if s < 0.5])
        
        # 统计文件类型
        file_type_stats = {}
        for file in files:
            file_type = file.file_type or 'unknown'
            if file_type not in file_type_stats:
                file_type_stats[file_type] = {
                    'total': 0, 'successful': 0, 'failed': 0, 'skipped': 0
                }
            
            file_type_stats[file_type]['total'] += 1
            if file.status == FileStatus.COMPLETED:
                file_type_stats[file_type]['successful'] += 1
            elif file.status == FileStatus.FAILED:
                file_type_stats[file_type]['failed'] += 1
            elif file.status == FileStatus.SKIPPED:
                file_type_stats[file_type]['skipped'] += 1
        
        summary.file_type_stats = file_type_stats
        
        # 统计错误
        failed_files = [f for f in files if f.status == FileStatus.FAILED and f.error_message]
        if failed_files:
            error_messages = [f.error_message for f in failed_files]
            # 简单错误统计（实际实现可以更复杂）
            summary.common_errors = list(set(error_messages))[:10]  # 前10个不重复错误
        
        return summary