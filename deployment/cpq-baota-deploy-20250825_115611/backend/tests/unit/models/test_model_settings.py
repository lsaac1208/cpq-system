"""
Tests for Settings model
"""

import pytest
from src.models.settings import SystemSettings
from src.models.base import db


class TestSystemSettings:
    """Test SystemSettings model"""
    
    def test_create_default_settings(self, app_context):
        """Test creating settings with default values"""
        settings = SystemSettings()
        settings.save()
        
        assert settings.id is not None
        assert settings.company_name == 'Your Company Name'
        assert settings.default_currency == 'USD'
        assert settings.default_tax_rate == '0.00'
        assert settings.quote_validity_days == '30'
        assert settings.pdf_header_color == '#2563eb'
        assert settings.pdf_show_logo is True
        assert settings.smtp_enabled is False
        assert settings.auto_quote_numbering is True
        assert settings.require_customer_approval is False
        assert settings.max_discount_percentage == '20.00'
    
    def test_settings_to_dict(self, app_context):
        """Test settings to_dict method"""
        settings = SystemSettings(
            company_name='Test Company',
            company_email='test@example.com',
            default_currency='EUR',
            default_tax_rate='19.00'
        )
        settings.save()
        
        data = settings.to_dict()
        
        # Check structure
        assert 'company_info' in data
        assert 'system_config' in data
        assert 'pdf_settings' in data
        assert 'email_settings' in data
        assert 'business_rules' in data
        
        # Check company info
        assert data['company_info']['name'] == 'Test Company'
        assert data['company_info']['email'] == 'test@example.com'
        
        # Check system config
        assert data['system_config']['default_currency'] == 'EUR'
        assert data['system_config']['default_tax_rate'] == 19.00
        
        # Check timestamps
        assert 'created_at' in data
        assert 'updated_at' in data
    
    def test_get_settings_singleton(self, app_context):
        """Test get_settings method creates singleton"""
        # First call should create settings
        settings1 = SystemSettings.get_settings()
        assert settings1.id is not None
        
        # Second call should return same settings
        settings2 = SystemSettings.get_settings()
        assert settings1.id == settings2.id
    
    def test_update_settings_company_info(self, app_context):
        """Test updating company information"""
        # Create initial settings
        settings = SystemSettings.get_settings()
        original_name = settings.company_name
        
        # Update company info
        updated_settings = SystemSettings.update_settings(
            company_info={
                'name': 'Updated Company',
                'email': 'updated@example.com',
                'phone': '+1-234-567-8900'
            }
        )
        
        assert updated_settings.company_name == 'Updated Company'
        assert updated_settings.company_email == 'updated@example.com'
        assert updated_settings.company_phone == '+1-234-567-8900'
        assert updated_settings.id == settings.id  # Same record
    
    def test_update_settings_system_config(self, app_context):
        """Test updating system configuration"""
        settings = SystemSettings.get_settings()
        
        # Update system config
        updated_settings = SystemSettings.update_settings(
            system_config={
                'default_currency': 'GBP',
                'default_tax_rate': 20.0,
                'quote_validity_days': 45
            }
        )
        
        assert updated_settings.default_currency == 'GBP'
        assert updated_settings.default_tax_rate == '20.0'
        assert updated_settings.quote_validity_days == '45'
    
    def test_update_settings_pdf_settings(self, app_context):
        """Test updating PDF settings"""
        settings = SystemSettings.get_settings()
        
        # Update PDF settings
        updated_settings = SystemSettings.update_settings(
            pdf_settings={
                'header_color': '#ff0000',
                'footer_text': 'Custom footer text',
                'show_logo': False
            }
        )
        
        assert updated_settings.pdf_header_color == '#ff0000'
        assert updated_settings.pdf_footer_text == 'Custom footer text'
        assert updated_settings.pdf_show_logo is False
    
    def test_update_settings_email_settings(self, app_context):
        """Test updating email settings"""
        settings = SystemSettings.get_settings()
        
        # Update email settings
        updated_settings = SystemSettings.update_settings(
            email_settings={
                'smtp_enabled': True,
                'smtp_host': 'smtp.example.com',
                'smtp_port': 587,
                'smtp_username': 'user@example.com',
                'smtp_use_tls': True
            }
        )
        
        assert updated_settings.smtp_enabled is True
        assert updated_settings.smtp_host == 'smtp.example.com'
        assert updated_settings.smtp_port == '587'
        assert updated_settings.smtp_username == 'user@example.com'
        assert updated_settings.smtp_use_tls is True
    
    def test_update_settings_business_rules(self, app_context):
        """Test updating business rules"""
        settings = SystemSettings.get_settings()
        
        # Update business rules
        updated_settings = SystemSettings.update_settings(
            business_rules={
                'auto_quote_numbering': False,
                'require_customer_approval': True,
                'max_discount_percentage': 15.0
            }
        )
        
        assert updated_settings.auto_quote_numbering is False
        assert updated_settings.require_customer_approval is True
        assert updated_settings.max_discount_percentage == '15.0'
    
    def test_update_settings_multiple_sections(self, app_context):
        """Test updating multiple settings sections at once"""
        # Clear any existing settings to ensure clean state
        from src.models.base import db
        db.session.query(SystemSettings).delete()
        db.session.commit()
        
        # Get fresh settings (will create with defaults)
        settings = SystemSettings.get_settings()
        
        # Verify we start with default values
        assert settings.default_tax_rate == '0.00'
        assert settings.pdf_header_color == '#2563eb'
        
        # Update multiple sections
        updated_settings = SystemSettings.update_settings(
            company_info={'name': 'Multi Update Company'},
            system_config={'default_currency': 'JPY'},
            business_rules={'max_discount_percentage': 25.0}
        )
        
        assert updated_settings.company_name == 'Multi Update Company'
        assert updated_settings.default_currency == 'JPY'
        assert updated_settings.max_discount_percentage == '25.0'
        
        # Other settings should remain unchanged
        assert updated_settings.default_tax_rate == '0.00'  # Default value
        assert updated_settings.pdf_header_color == '#2563eb'  # Default value