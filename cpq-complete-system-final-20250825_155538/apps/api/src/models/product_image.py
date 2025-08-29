#!/usr/bin/env python3
"""
Product Image model for CPQ system
Supports multiple images per product with ordering and metadata
"""

from .base import db, BaseModel
from sqlalchemy import Index


class ProductImage(BaseModel):
    """Product Image model for image gallery functionality."""
    
    __tablename__ = 'product_images'
    
    # 关联产品ID
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    
    # 图片信息
    filename = db.Column(db.String(255), nullable=False)  # 文件名
    original_filename = db.Column(db.String(255), nullable=True)  # 原始文件名
    image_url = db.Column(db.String(255), nullable=False)  # 图片URL
    thumbnail_url = db.Column(db.String(255), nullable=True)  # 缩略图URL
    
    # 图片元数据
    title = db.Column(db.String(200), nullable=True)  # 图片标题
    description = db.Column(db.Text, nullable=True)  # 图片描述
    alt_text = db.Column(db.String(200), nullable=True)  # 图片alt文本
    
    # 图片属性
    file_size = db.Column(db.Integer, nullable=True)  # 文件大小（字节）
    width = db.Column(db.Integer, nullable=True)  # 图片宽度
    height = db.Column(db.Integer, nullable=True)  # 图片高度
    format = db.Column(db.String(10), nullable=True)  # 图片格式（jpg, png, webp等）
    
    # 排序和状态
    sort_order = db.Column(db.Integer, default=0, nullable=False)  # 排序顺序
    is_primary = db.Column(db.Boolean, default=False, nullable=False)  # 是否为主图
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # 是否有效
    
    # 图片类型分类
    image_type = db.Column(db.String(50), default='product', nullable=False)  # 图片类型：product, detail, usage等
    
    # 关系定义
    product = db.relationship('Product', backref=db.backref('images', 
                             lazy='dynamic', 
                             order_by='ProductImage.sort_order',
                             cascade='all, delete-orphan'))
    
    # 索引优化
    __table_args__ = (
        Index('idx_product_images_product_id', 'product_id'),
        Index('idx_product_images_sort', 'product_id', 'sort_order'),
        Index('idx_product_images_primary', 'product_id', 'is_primary'),
        Index('idx_product_images_active', 'product_id', 'is_active'),
    )
    
    def to_dict(self):
        """Convert product image to dictionary."""
        data = super().to_dict()
        data.update({
            'product_id': self.product_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'image_url': self.image_url,
            'thumbnail_url': self.thumbnail_url,
            'title': self.title,
            'description': self.description,
            'alt_text': self.alt_text,
            'file_size': self.file_size,
            'width': self.width,
            'height': self.height,
            'format': self.format,
            'sort_order': self.sort_order,
            'is_primary': self.is_primary,
            'is_active': self.is_active,
            'image_type': self.image_type
        })
        return data
    
    @classmethod
    def get_product_images(cls, product_id, active_only=True):
        """获取产品的所有图片，按排序顺序"""
        query = cls.query.filter_by(product_id=product_id)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.order_by(cls.sort_order).all()
    
    @classmethod
    def get_primary_image(cls, product_id):
        """获取产品主图"""
        return cls.query.filter_by(
            product_id=product_id, 
            is_primary=True, 
            is_active=True
        ).first()
    
    @classmethod
    def set_primary_image(cls, product_id, image_id):
        """设置主图（同时取消其他主图状态）"""
        # 先取消所有主图状态
        cls.query.filter_by(product_id=product_id).update({'is_primary': False})
        
        # 设置新主图
        image = cls.query.filter_by(id=image_id, product_id=product_id).first()
        if image:
            image.is_primary = True
            db.session.commit()
            return image
        return None
    
    @classmethod
    def reorder_images(cls, product_id, image_orders):
        """重新排序图片
        Args:
            product_id: 产品ID
            image_orders: 格式为 [{'id': image_id, 'sort_order': order}, ...]
        """
        for item in image_orders:
            cls.query.filter_by(
                id=item['id'], 
                product_id=product_id
            ).update({'sort_order': item['sort_order']})
        
        db.session.commit()
    
    @classmethod
    def get_next_sort_order(cls, product_id):
        """获取下一个排序号"""
        max_order = db.session.query(
            db.func.max(cls.sort_order)
        ).filter_by(product_id=product_id).scalar()
        
        return (max_order or 0) + 10  # 间隔10，方便插入
    
    def __repr__(self):
        return f'<ProductImage {self.id}: {self.filename} for Product {self.product_id}>'


class ProductImageProcessingLog(BaseModel):
    """产品图片处理日志，用于追踪图片处理历史"""
    
    __tablename__ = 'product_image_processing_logs'
    
    # 关联图片
    image_id = db.Column(db.Integer, db.ForeignKey('product_images.id', ondelete='CASCADE'), nullable=False)
    
    # 处理信息
    operation = db.Column(db.String(50), nullable=False)  # upload, resize, compress, delete等
    original_size = db.Column(db.Integer, nullable=True)  # 原始大小
    processed_size = db.Column(db.Integer, nullable=True)  # 处理后大小
    compression_ratio = db.Column(db.Float, nullable=True)  # 压缩比例
    processing_time = db.Column(db.Integer, nullable=True)  # 处理时间(ms)
    
    # 处理参数
    parameters = db.Column(db.Text, nullable=True)  # JSON格式的处理参数
    
    # 结果状态
    status = db.Column(db.String(20), default='success', nullable=False)  # success, failed, warning
    error_message = db.Column(db.Text, nullable=True)  # 错误信息
    
    # 关系定义
    image = db.relationship('ProductImage', backref=db.backref('processing_logs', lazy='dynamic'))
    
    def to_dict(self):
        """Convert log to dictionary."""
        data = super().to_dict()
        data.update({
            'image_id': self.image_id,
            'operation': self.operation,
            'original_size': self.original_size,
            'processed_size': self.processed_size,
            'compression_ratio': self.compression_ratio,
            'processing_time': self.processing_time,
            'parameters': self.parameters,
            'status': self.status,
            'error_message': self.error_message
        })
        return data
    
    def save(self):
        """重写save方法，确保image_id有效"""
        if not self.image_id:
            raise ValueError("ProductImageProcessingLog requires a valid image_id")
        
        # 验证image_id对应的ProductImage是否存在
        if not ProductImage.query.get(self.image_id):
            raise ValueError(f"ProductImage with id {self.image_id} does not exist")
            
        return super().save()
    
    def __repr__(self):
        return f'<ProcessingLog {self.id}: {self.operation} for Image {self.image_id}>'