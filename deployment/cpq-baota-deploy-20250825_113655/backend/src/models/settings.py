from sqlalchemy import Column, String, Text, Boolean
from .base import BaseModel, db


class SystemSettings(BaseModel):
    """System settings model for managing application-wide configurations."""
    
    __tablename__ = 'system_settings'
    
    # Company Information
    company_name = Column(String(200), nullable=False, default='Your Company Name')
    company_address = Column(Text, nullable=True)
    company_phone = Column(String(50), nullable=True)
    company_email = Column(String(100), nullable=True)
    company_website = Column(String(200), nullable=True)
    company_logo_url = Column(String(500), nullable=True)
    company_tax_number = Column(String(100), nullable=True)
    
    # System Configuration
    default_currency = Column(String(10), nullable=False, default='USD')
    default_tax_rate = Column(String(10), nullable=False, default='0.00')  # Stored as string to preserve precision
    quote_validity_days = Column(String(10), nullable=False, default='30')
    
    # PDF Settings
    pdf_header_color = Column(String(20), nullable=False, default='#2563eb')
    pdf_footer_text = Column(Text, nullable=True)
    pdf_show_logo = Column(Boolean, nullable=False, default=True)
    
    # Email Settings
    smtp_enabled = Column(Boolean, nullable=False, default=False)
    smtp_host = Column(String(255), nullable=True)
    smtp_port = Column(String(10), nullable=True)
    smtp_username = Column(String(255), nullable=True)
    smtp_password = Column(String(255), nullable=True)  # Should be encrypted in production
    smtp_use_tls = Column(Boolean, nullable=False, default=True)
    
    # Business Rules
    auto_quote_numbering = Column(Boolean, nullable=False, default=True)
    require_customer_approval = Column(Boolean, nullable=False, default=False)
    max_discount_percentage = Column(String(10), nullable=False, default='20.00')
    
    def __repr__(self):
        return f'<SystemSettings {self.company_name}>'
    
    def to_dict(self):
        """Convert model to dictionary with grouped structure."""
        return {
            'id': self.id,
            'company_info': {
                'name': self.company_name,
                'address': self.company_address,
                'phone': self.company_phone,
                'email': self.company_email,
                'website': self.company_website,
                'logo_url': self.company_logo_url,
                'tax_number': self.company_tax_number
            },
            'system_config': {
                'default_currency': self.default_currency,
                'default_tax_rate': float(self.default_tax_rate),
                'quote_validity_days': int(self.quote_validity_days)
            },
            'pdf_settings': {
                'header_color': self.pdf_header_color,
                'footer_text': self.pdf_footer_text,
                'show_logo': self.pdf_show_logo
            },
            'email_settings': {
                'smtp_enabled': self.smtp_enabled,
                'smtp_host': self.smtp_host,
                'smtp_port': int(self.smtp_port) if self.smtp_port else None,
                'smtp_username': self.smtp_username,
                'smtp_use_tls': self.smtp_use_tls
            },
            'business_rules': {
                'auto_quote_numbering': self.auto_quote_numbering,
                'require_customer_approval': self.require_customer_approval,
                'max_discount_percentage': float(self.max_discount_percentage)
            },
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def get_settings(cls):
        """Get current system settings (singleton pattern)."""
        settings = cls.query.first()
        if not settings:
            # Create default settings if none exist
            settings = cls()
            settings.save()
        return settings
    
    @classmethod
    def update_settings(cls, **kwargs):
        """Update system settings."""
        settings = cls.get_settings()
        
        # Update company info
        if 'company_info' in kwargs and kwargs['company_info'] is not None:
            company_info = kwargs['company_info']
            if 'name' in company_info:
                settings.company_name = company_info['name']
            if 'address' in company_info:
                settings.company_address = company_info['address']
            if 'phone' in company_info:
                settings.company_phone = company_info['phone']
            if 'email' in company_info:
                settings.company_email = company_info['email']
            if 'website' in company_info:
                settings.company_website = company_info['website']
            if 'logo_url' in company_info:
                settings.company_logo_url = company_info['logo_url']
            if 'tax_number' in company_info:
                settings.company_tax_number = company_info['tax_number']
        
        # Update system config
        if 'system_config' in kwargs and kwargs['system_config'] is not None:
            system_config = kwargs['system_config']
            if 'default_currency' in system_config:
                settings.default_currency = system_config['default_currency']
            if 'default_tax_rate' in system_config:
                settings.default_tax_rate = str(system_config['default_tax_rate'])
            if 'quote_validity_days' in system_config:
                settings.quote_validity_days = str(system_config['quote_validity_days'])
        
        # Update PDF settings
        if 'pdf_settings' in kwargs and kwargs['pdf_settings'] is not None:
            pdf_settings = kwargs['pdf_settings']
            if 'header_color' in pdf_settings:
                settings.pdf_header_color = pdf_settings['header_color']
            if 'footer_text' in pdf_settings:
                settings.pdf_footer_text = pdf_settings['footer_text']
            if 'show_logo' in pdf_settings:
                settings.pdf_show_logo = pdf_settings['show_logo']
        
        # Update email settings
        if 'email_settings' in kwargs and kwargs['email_settings'] is not None:
            email_settings = kwargs['email_settings']
            if 'smtp_enabled' in email_settings:
                settings.smtp_enabled = email_settings['smtp_enabled']
            if 'smtp_host' in email_settings:
                settings.smtp_host = email_settings['smtp_host']
            if 'smtp_port' in email_settings:
                settings.smtp_port = str(email_settings['smtp_port'])
            if 'smtp_username' in email_settings:
                settings.smtp_username = email_settings['smtp_username']
            if 'smtp_password' in email_settings:
                settings.smtp_password = email_settings['smtp_password']
            if 'smtp_use_tls' in email_settings:
                settings.smtp_use_tls = email_settings['smtp_use_tls']
        
        # Update business rules
        if 'business_rules' in kwargs and kwargs['business_rules'] is not None:
            business_rules = kwargs['business_rules']
            if 'auto_quote_numbering' in business_rules:
                settings.auto_quote_numbering = business_rules['auto_quote_numbering']
            if 'require_customer_approval' in business_rules:
                settings.require_customer_approval = business_rules['require_customer_approval']
            if 'max_discount_percentage' in business_rules:
                settings.max_discount_percentage = str(business_rules['max_discount_percentage'])
        
        settings.save()
        return settings