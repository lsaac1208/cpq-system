"""
Tests for validation utilities
"""

import pytest
from src.utils.validation import SettingsValidator, ValidationError


class TestSettingsValidator:
    """Test SettingsValidator class"""
    
    def test_validate_company_info_valid(self):
        """Test validation of valid company info"""
        valid_data = {
            'name': 'Test Company',
            'email': 'test@example.com',
            'website': 'https://example.com',
            'logo_url': 'https://example.com/logo.png',
            'phone': '+1-234-567-8900',
            'tax_number': 'TAX123456'
        }
        
        errors = SettingsValidator.validate_company_info(valid_data)
        assert errors == []
    
    def test_validate_company_info_missing_name(self):
        """Test validation with missing company name"""
        invalid_data = {
            'name': '',
            'email': 'test@example.com'
        }
        
        errors = SettingsValidator.validate_company_info(invalid_data)
        assert len(errors) == 1
        assert 'Company name is required' in errors
    
    def test_validate_company_info_long_name(self):
        """Test validation with too long company name"""
        invalid_data = {
            'name': 'A' * 201,  # 201 characters
            'email': 'test@example.com'
        }
        
        errors = SettingsValidator.validate_company_info(invalid_data)
        assert len(errors) == 1
        assert 'cannot exceed 200 characters' in errors[0]
    
    def test_validate_company_info_invalid_email(self):
        """Test validation with invalid email"""
        invalid_data = {
            'name': 'Test Company',
            'email': 'invalid-email'
        }
        
        errors = SettingsValidator.validate_company_info(invalid_data)
        assert len(errors) == 1
        assert 'Invalid email address' in errors
    
    def test_validate_company_info_invalid_website(self):
        """Test validation with invalid website URL"""
        invalid_data = {
            'name': 'Test Company',
            'website': 'not-a-valid-url'
        }
        
        errors = SettingsValidator.validate_company_info(invalid_data)
        assert len(errors) == 1
        assert 'Invalid website URL' in errors
    
    def test_validate_system_config_valid(self):
        """Test validation of valid system config"""
        valid_data = {
            'default_currency': 'USD',
            'default_tax_rate': 19.5,
            'quote_validity_days': 30
        }
        
        errors = SettingsValidator.validate_system_config(valid_data)
        assert errors == []
    
    def test_validate_system_config_missing_currency(self):
        """Test validation with missing currency"""
        invalid_data = {
            'default_currency': '',
            'default_tax_rate': 19.5
        }
        
        errors = SettingsValidator.validate_system_config(invalid_data)
        assert len(errors) == 1
        assert 'Default currency is required' in errors
    
    def test_validate_system_config_invalid_tax_rate(self):
        """Test validation with invalid tax rate"""
        invalid_data = {
            'default_currency': 'USD',
            'default_tax_rate': 150.0  # Over 100%
        }
        
        errors = SettingsValidator.validate_system_config(invalid_data)
        assert len(errors) == 1
        assert 'Tax rate must be between 0 and 100' in errors
    
    def test_validate_system_config_invalid_validity_days(self):
        """Test validation with invalid quote validity days"""
        invalid_data = {
            'default_currency': 'USD',
            'quote_validity_days': 500  # Over 365
        }
        
        errors = SettingsValidator.validate_system_config(invalid_data)
        assert len(errors) == 1
        assert 'Quote validity must be between 1 and 365 days' in errors
    
    def test_validate_pdf_settings_valid(self):
        """Test validation of valid PDF settings"""
        valid_data = {
            'header_color': '#ff0000',
            'footer_text': 'Custom footer',
            'show_logo': True
        }
        
        errors = SettingsValidator.validate_pdf_settings(valid_data)
        assert errors == []
    
    def test_validate_pdf_settings_invalid_color(self):
        """Test validation with invalid header color"""
        invalid_data = {
            'header_color': 'red'  # Not hex format
        }
        
        errors = SettingsValidator.validate_pdf_settings(invalid_data)
        assert len(errors) == 1
        assert 'Invalid header color format' in errors
    
    def test_validate_email_settings_disabled(self):
        """Test validation when email is disabled"""
        valid_data = {
            'smtp_enabled': False,
            'smtp_host': '',  # Can be empty when disabled
            'smtp_port': None
        }
        
        errors = SettingsValidator.validate_email_settings(valid_data)
        assert errors == []
    
    def test_validate_email_settings_enabled_missing_host(self):
        """Test validation when email is enabled but host is missing"""
        invalid_data = {
            'smtp_enabled': True,
            'smtp_host': ''  # Required when enabled
        }
        
        errors = SettingsValidator.validate_email_settings(invalid_data)
        assert len(errors) == 1
        assert 'SMTP host is required when email is enabled' in errors
    
    def test_validate_email_settings_invalid_port(self):
        """Test validation with invalid SMTP port"""
        invalid_data = {
            'smtp_enabled': True,
            'smtp_host': 'smtp.example.com',
            'smtp_port': 70000  # Over 65535
        }
        
        errors = SettingsValidator.validate_email_settings(invalid_data)
        assert len(errors) == 1
        assert 'SMTP port must be between 1 and 65535' in errors
    
    def test_validate_business_rules_valid(self):
        """Test validation of valid business rules"""
        valid_data = {
            'auto_quote_numbering': True,
            'require_customer_approval': False,
            'max_discount_percentage': 25.0
        }
        
        errors = SettingsValidator.validate_business_rules(valid_data)
        assert errors == []
    
    def test_validate_business_rules_invalid_discount(self):
        """Test validation with invalid max discount percentage"""
        invalid_data = {
            'max_discount_percentage': 150.0  # Over 100%
        }
        
        errors = SettingsValidator.validate_business_rules(invalid_data)
        assert len(errors) == 1
        assert 'Max discount percentage must be between 0 and 100' in errors
    
    def test_validate_all_settings_multiple_errors(self):
        """Test validation of all settings with multiple errors"""
        invalid_data = {
            'company_info': {
                'name': '',  # Missing name
                'email': 'invalid-email'  # Invalid email
            },
            'system_config': {
                'default_currency': '',  # Missing currency
                'default_tax_rate': 150.0  # Invalid tax rate
            },
            'business_rules': {
                'max_discount_percentage': -5.0  # Invalid discount
            }
        }
        
        all_errors = SettingsValidator.validate_all_settings(invalid_data)
        
        assert 'company_info' in all_errors
        assert 'system_config' in all_errors
        assert 'business_rules' in all_errors
        
        assert len(all_errors['company_info']) == 2
        assert len(all_errors['system_config']) == 2
        assert len(all_errors['business_rules']) == 1
    
    def test_is_valid_url(self):
        """Test URL validation helper method"""
        # Valid URLs
        assert SettingsValidator._is_valid_url('https://example.com')
        assert SettingsValidator._is_valid_url('http://example.com')
        assert SettingsValidator._is_valid_url('https://subdomain.example.com')
        assert SettingsValidator._is_valid_url('https://example.com/path')
        assert SettingsValidator._is_valid_url('https://example.com:8080')
        
        # Invalid URLs
        assert not SettingsValidator._is_valid_url('not-a-url')
        assert not SettingsValidator._is_valid_url('ftp://example.com')
        assert not SettingsValidator._is_valid_url('example.com')
    
    def test_is_valid_hex_color(self):
        """Test hex color validation helper method"""
        # Valid colors
        assert SettingsValidator._is_valid_hex_color('#ff0000')
        assert SettingsValidator._is_valid_hex_color('#00FF00')
        assert SettingsValidator._is_valid_hex_color('#123abc')
        
        # Invalid colors
        assert not SettingsValidator._is_valid_hex_color('red')
        assert not SettingsValidator._is_valid_hex_color('#ff')
        assert not SettingsValidator._is_valid_hex_color('#gggggg')
        assert not SettingsValidator._is_valid_hex_color('ff0000')