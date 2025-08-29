from .base import db, BaseModel
import json
from sqlalchemy import Index
from decimal import Decimal

class Product(BaseModel):
    """Product model for CPQ system."""
    
    __tablename__ = 'products'
    
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100), nullable=False)
    base_price = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Configuration options stored as JSON
    configuration_schema = db.Column(db.Text)  # JSON schema for configuration options
    
    # Product specifications
    specifications = db.Column(db.Text)  # JSON for technical specifications
    
    # Extended AI analysis fields
    detailed_description = db.Column(db.Text)  # 详细产品描述
    features = db.Column(db.Text)  # JSON for product features
    application_scenarios = db.Column(db.Text)  # JSON for application scenarios
    accessories = db.Column(db.Text)  # JSON for accessories
    certificates = db.Column(db.Text)  # JSON for certificates
    support_info = db.Column(db.Text)  # JSON for support information
    
    # Product image (保持向后兼容，同时支持新的图片集功能)
    image_url = db.Column(db.String(255), nullable=True)
    
    # Status and availability
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_configurable = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    quotes = db.relationship('Quote', backref='product', lazy=True)
    # 图片集关系将在 ProductImage 模型中定义，避免循环导入
    
    # Database indexes for performance
    __table_args__ = (
        Index('idx_product_code', 'code'),
        Index('idx_product_category', 'category'),
        Index('idx_product_active', 'is_active'),
        Index('idx_product_configurable', 'is_configurable'),
    )
    
    def validate(self):
        """Validate product data."""
        errors = []
        
        if not self.name or len(self.name.strip()) == 0:
            errors.append("Product name is required")
            
        if not self.code or len(self.code.strip()) == 0:
            errors.append("Product code is required")
            
        if not self.category or len(self.category.strip()) == 0:
            errors.append("Product category is required")
            
        if self.base_price is None or self.base_price < 0:
            errors.append("Base price must be a non-negative number")
            
        return errors
    
    def get_configuration_schema(self):
        """Get configuration schema as dict."""
        if self.configuration_schema:
            return json.loads(self.configuration_schema)
        return {}
    
    def set_configuration_schema(self, schema_dict):
        """Set configuration schema from dict."""
        self.configuration_schema = json.dumps(schema_dict)
    
    def get_specifications(self):
        """Get specifications as dict."""
        if self.specifications:
            return json.loads(self.specifications)
        return {}
    
    def set_specifications(self, specs_dict):
        """Set specifications from dict."""
        self.specifications = json.dumps(specs_dict)
    
    def get_features(self):
        """Get features as list."""
        if self.features:
            return json.loads(self.features)
        return []
    
    def set_features(self, features_list):
        """Set features from list."""
        self.features = json.dumps(features_list)
    
    def get_application_scenarios(self):
        """Get application scenarios as list."""
        if self.application_scenarios:
            return json.loads(self.application_scenarios)
        return []
    
    def set_application_scenarios(self, scenarios_list):
        """Set application scenarios from list."""
        self.application_scenarios = json.dumps(scenarios_list)
    
    def get_accessories(self):
        """Get accessories as list."""
        if self.accessories:
            return json.loads(self.accessories)
        return []
    
    def set_accessories(self, accessories_list):
        """Set accessories from list."""
        self.accessories = json.dumps(accessories_list)
    
    def get_certificates(self):
        """Get certificates as list."""
        if self.certificates:
            return json.loads(self.certificates)
        return []
    
    def set_certificates(self, certificates_list):
        """Set certificates from list."""
        self.certificates = json.dumps(certificates_list)
    
    def get_support_info(self):
        """Get support info as dict."""
        if self.support_info:
            return json.loads(self.support_info)
        return {}
    
    def set_support_info(self, support_dict):
        """Set support info from dict."""
        self.support_info = json.dumps(support_dict)
    
    def to_dict(self):
        """Convert product to dictionary."""
        data = super().to_dict()
        data['configuration_schema'] = self.get_configuration_schema()
        data['specifications'] = self.get_specifications()
        
        # 添加AI分析扩展字段
        data['features'] = self.get_features()
        data['application_scenarios'] = self.get_application_scenarios()
        data['accessories'] = self.get_accessories()
        data['certificates'] = self.get_certificates()
        data['support_info'] = self.get_support_info()
        
        # 添加图片集信息
        data['gallery_images'] = self.get_gallery_images()
        data['primary_image'] = self.get_primary_image_info()
        data['total_images'] = self.get_total_images_count()
        
        return data
    
    def get_gallery_images(self):
        """获取产品图片集信息"""
        try:
            from .product_image import ProductImage
            images = ProductImage.get_product_images(self.id, active_only=True)
            return [img.to_dict() for img in images]
        except ImportError:
            # 如果ProductImage模型不可用，返回空列表
            return []
    
    def get_primary_image_info(self):
        """获取主图信息，优先使用图片集中的主图"""
        try:
            from .product_image import ProductImage
            primary_image = ProductImage.get_primary_image(self.id)
            if primary_image:
                return primary_image.to_dict()
        except ImportError:
            pass
        
        # 向后兼容：如果没有图片集或主图，使用原有的image_url
        if self.image_url:
            return {
                'image_url': self.image_url,
                'is_legacy': True  # 标识这是旧版图片
            }
        
        return None
    
    def get_total_images_count(self):
        """获取产品图片总数"""
        try:
            from .product_image import ProductImage
            count = ProductImage.query.filter_by(
                product_id=self.id, 
                is_active=True
            ).count()
            return count
        except ImportError:
            # 向后兼容
            return 1 if self.image_url else 0
    
    def migrate_legacy_image(self):
        """将旧版image_url迁移到新的图片集系统"""
        if not self.image_url:
            return None
            
        try:
            from .product_image import ProductImage
            
            # 检查是否已经迁移过
            existing = ProductImage.query.filter_by(
                product_id=self.id,
                image_url=self.image_url
            ).first()
            
            if existing:
                return existing
            
            # 创建新的图片记录
            new_image = ProductImage(
                product_id=self.id,
                filename=self.image_url.split('/')[-1] if '/' in self.image_url else self.image_url,
                image_url=self.image_url,
                is_primary=True,
                sort_order=0,
                image_type='product',
                title=f'{self.name} - 产品图片'
            )
            
            new_image.save()
            return new_image
            
        except ImportError:
            return None
    
    def __repr__(self):
        return f'<Product {self.code}: {self.name}>'