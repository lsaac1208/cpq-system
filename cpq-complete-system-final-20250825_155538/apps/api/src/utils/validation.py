"""
Validation utilities for the CPQ system
"""

import re
from typing import Dict, Any, List, Optional
from email_validator import validate_email, EmailNotValidError


class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)


class SettingsValidator:
    """Validator for system settings"""
    
    @staticmethod
    def validate_company_info(data: Dict[str, Any]) -> List[str]:
        """Validate company information"""
        errors = []
        
        # Company name is required
        name = (data.get('name') or '').strip()
        if not name:
            errors.append('Company name is required')
        elif len(name) > 200:
            errors.append('Company name cannot exceed 200 characters')
        
        # Validate email if provided
        email = (data.get('email') or '').strip()
        if email:
            try:
                validate_email(email)
            except EmailNotValidError:
                errors.append('Invalid email address')
        
        # Validate website URL if provided
        website = (data.get('website') or '').strip()
        if website:
            if not SettingsValidator._is_valid_url(website):
                errors.append('Invalid website URL')
        
        # Validate logo URL if provided
        logo_url = (data.get('logo_url') or '').strip()
        if logo_url:
            if not SettingsValidator._is_valid_url(logo_url):
                errors.append('Invalid logo URL')
        
        # Validate phone number if provided
        phone = (data.get('phone') or '').strip()
        if phone and len(phone) > 50:
            errors.append('Phone number cannot exceed 50 characters')
        
        # Validate tax number if provided
        tax_number = (data.get('tax_number') or '').strip()
        if tax_number and len(tax_number) > 100:
            errors.append('Tax number cannot exceed 100 characters')
        
        return errors
    
    @staticmethod
    def validate_system_config(data: Dict[str, Any]) -> List[str]:
        """Validate system configuration"""
        errors = []
        
        # Validate currency code
        currency = (data.get('default_currency') or '').strip().upper()
        if not currency:
            errors.append('Default currency is required')
        elif len(currency) < 3 or len(currency) > 10:
            errors.append('Currency code must be 3-10 characters')
        
        # Validate tax rate
        tax_rate = data.get('default_tax_rate')
        if tax_rate is not None:
            try:
                rate = float(tax_rate)
                if rate < 0 or rate > 100:
                    errors.append('Tax rate must be between 0 and 100')
            except (ValueError, TypeError):
                errors.append('Invalid tax rate format')
        
        # Validate quote validity days
        validity_days = data.get('quote_validity_days')
        if validity_days is not None:
            try:
                days = int(validity_days)
                if days < 1 or days > 365:
                    errors.append('Quote validity must be between 1 and 365 days')
            except (ValueError, TypeError):
                errors.append('Invalid quote validity days format')
        
        return errors
    
    @staticmethod
    def validate_pdf_settings(data: Dict[str, Any]) -> List[str]:
        """Validate PDF settings"""
        errors = []
        
        # Validate header color
        header_color = (data.get('header_color') or '').strip()
        if header_color:
            if not SettingsValidator._is_valid_hex_color(header_color):
                errors.append('Invalid header color format (use #RRGGBB)')
        
        return errors
    
    @staticmethod
    def validate_email_settings(data: Dict[str, Any]) -> List[str]:
        """Validate email settings"""
        errors = []
        
        smtp_enabled = data.get('smtp_enabled', False)
        
        if smtp_enabled:
            # SMTP host is required when email is enabled
            smtp_host = (data.get('smtp_host') or '').strip()
            if not smtp_host:
                errors.append('SMTP host is required when email is enabled')
            
            # Validate SMTP port
            smtp_port = data.get('smtp_port')
            if smtp_port is not None:
                try:
                    port = int(smtp_port)
                    if port < 1 or port > 65535:
                        errors.append('SMTP port must be between 1 and 65535')
                except (ValueError, TypeError):
                    errors.append('Invalid SMTP port format')
            
            # Validate SMTP username (email format)
            smtp_username = (data.get('smtp_username') or '').strip()
            if smtp_username:
                try:
                    validate_email(smtp_username)
                except EmailNotValidError:
                    errors.append('SMTP username must be a valid email address')
        
        return errors
    
    @staticmethod
    def validate_business_rules(data: Dict[str, Any]) -> List[str]:
        """Validate business rules"""
        errors = []
        
        # Validate max discount percentage
        max_discount = data.get('max_discount_percentage')
        if max_discount is not None:
            try:
                discount = float(max_discount)
                if discount < 0 or discount > 100:
                    errors.append('Max discount percentage must be between 0 and 100')
            except (ValueError, TypeError):
                errors.append('Invalid max discount percentage format')
        
        return errors
    
    @staticmethod
    def validate_all_settings(data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate all settings sections"""
        all_errors = {}
        
        if 'company_info' in data and data['company_info'] is not None:
            company_errors = SettingsValidator.validate_company_info(data['company_info'])
            if company_errors:
                all_errors['company_info'] = company_errors
        
        if 'system_config' in data and data['system_config'] is not None:
            system_errors = SettingsValidator.validate_system_config(data['system_config'])
            if system_errors:
                all_errors['system_config'] = system_errors
        
        if 'pdf_settings' in data and data['pdf_settings'] is not None:
            pdf_errors = SettingsValidator.validate_pdf_settings(data['pdf_settings'])
            if pdf_errors:
                all_errors['pdf_settings'] = pdf_errors
        
        if 'email_settings' in data and data['email_settings'] is not None:
            email_errors = SettingsValidator.validate_email_settings(data['email_settings'])
            if email_errors:
                all_errors['email_settings'] = email_errors
        
        if 'business_rules' in data and data['business_rules'] is not None:
            business_errors = SettingsValidator.validate_business_rules(data['business_rules'])
            if business_errors:
                all_errors['business_rules'] = business_errors
        
        return all_errors
    
    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """Validate URL format"""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None
    
    @staticmethod
    def _is_valid_hex_color(color: str) -> bool:
        """Validate hex color format"""
        hex_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')
        return hex_pattern.match(color) is not None


# Utility functions for common validations
def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """Validate that required fields are present and not empty"""
    errors = []
    for field in required_fields:
        if field not in data or not str(data[field]).strip():
            errors.append(f'{field} is required')
    return errors


def validate_string_length(value: str, max_length: int, field_name: str) -> Optional[str]:
    """Validate string length"""
    if len(value) > max_length:
        return f'{field_name} cannot exceed {max_length} characters'
    return None


def validate_numeric_range(value: Any, min_val: float, max_val: float, field_name: str) -> Optional[str]:
    """Validate numeric value is within range"""
    try:
        num_val = float(value)
        if num_val < min_val or num_val > max_val:
            return f'{field_name} must be between {min_val} and {max_val}'
    except (ValueError, TypeError):
        return f'{field_name} must be a valid number'
    return None


class ProductValidator:
    """Validator for product data"""
    
    @staticmethod
    def validate_product_data(data: Dict[str, Any]) -> List[str]:
        """Validate product creation/update data"""
        errors = []
        
        # Required fields
        required_fields = ['name', 'code', 'category', 'base_price']
        errors.extend(validate_required_fields(data, required_fields))
        
        # Validate product code format (alphanumeric, dashes, underscores)
        code = data.get('code', '').strip()
        if code and not re.match(r'^[a-zA-Z0-9_-]+$', code):
            errors.append('Product code can only contain letters, numbers, dashes, and underscores')
        
        # Validate base price
        base_price = data.get('base_price')
        if base_price is not None:
            try:
                price = float(base_price)
                if price < 0:
                    errors.append('Base price cannot be negative')
                elif price > 999999.99:
                    errors.append('Base price cannot exceed 999,999.99')
            except (ValueError, TypeError):
                errors.append('Base price must be a valid number')
        
        # Validate string lengths
        name = data.get('name', '')
        if name and len(name) > 200:
            errors.append('Product name cannot exceed 200 characters')
            
        code = data.get('code', '')
        if code and len(code) > 50:
            errors.append('Product code cannot exceed 50 characters')
            
        category = data.get('category', '')
        if category and len(category) > 100:
            errors.append('Category cannot exceed 100 characters')
        
        return errors