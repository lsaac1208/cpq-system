from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError, validate
from src.models.settings import SystemSettings
from src.utils.decorators import admin_required
from src.utils.validation import SettingsValidator
import logging

# Setup logging
logger = logging.getLogger(__name__)

settings_bp = Blueprint('settings', __name__)


# Validation schemas
class CompanyInfoSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    address = fields.Str(load_default=None, allow_none=True)
    phone = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=50))
    email = fields.Email(load_default=None, allow_none=True)
    website = fields.Url(load_default=None, allow_none=True)
    logo_url = fields.Url(load_default=None, allow_none=True)
    tax_number = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=100))


class SystemConfigSchema(Schema):
    default_currency = fields.Str(load_default='USD', validate=validate.Length(min=3, max=10))
    default_tax_rate = fields.Float(load_default=0.0, validate=validate.Range(min=0, max=100))
    quote_validity_days = fields.Int(load_default=30, validate=validate.Range(min=1, max=365))


class PDFSettingsSchema(Schema):
    header_color = fields.Str(load_default='#2563eb', validate=validate.Regexp(r'^#[0-9A-Fa-f]{6}$'))
    footer_text = fields.Str(load_default=None, allow_none=True)
    show_logo = fields.Bool(load_default=True)


class EmailSettingsSchema(Schema):
    smtp_enabled = fields.Bool(load_default=False)
    smtp_host = fields.Str(load_default=None, allow_none=True)
    smtp_port = fields.Int(load_default=587, allow_none=True, validate=validate.Range(min=1, max=65535))
    smtp_username = fields.Str(load_default=None, allow_none=True)
    smtp_password = fields.Str(load_default=None, allow_none=True, load_only=True)  # Don't return in response
    smtp_use_tls = fields.Bool(load_default=True)


class BusinessRulesSchema(Schema):
    auto_quote_numbering = fields.Bool(load_default=True)
    require_customer_approval = fields.Bool(load_default=False)
    max_discount_percentage = fields.Float(load_default=20.0, validate=validate.Range(min=0, max=100))


class UpdateSettingsSchema(Schema):
    company_info = fields.Nested(CompanyInfoSchema, load_default=None)
    system_config = fields.Nested(SystemConfigSchema, load_default=None)
    pdf_settings = fields.Nested(PDFSettingsSchema, load_default=None)
    email_settings = fields.Nested(EmailSettingsSchema, load_default=None)
    business_rules = fields.Nested(BusinessRulesSchema, load_default=None)


@settings_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_settings():
    """Get current system settings."""
    try:
        settings = SystemSettings.get_settings()
        settings_data = settings.to_dict()
        
        # Remove sensitive information from response
        if 'email_settings' in settings_data and settings_data['email_settings']:
            settings_data['email_settings'].pop('smtp_password', None)
        
        return jsonify({
            'success': True,
            'data': settings_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching settings: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch settings'
        }), 500


@settings_bp.route('/settings', methods=['PUT'])
@jwt_required()
@admin_required  # Only admins can update settings
def update_settings():
    """Update system settings."""
    try:
        # Validate request data
        schema = UpdateSettingsSchema()
        data = schema.load(request.json or {})
        
        # Additional custom validation
        validation_errors = SettingsValidator.validate_all_settings(data)
        if validation_errors:
            return jsonify({
                'success': False,
                'message': 'Validation error',
                'errors': validation_errors
            }), 400
        
        # Update settings
        settings = SystemSettings.update_settings(**data)
        settings_data = settings.to_dict()
        
        # Remove sensitive information from response
        if 'email_settings' in settings_data and settings_data['email_settings']:
            settings_data['email_settings'].pop('smtp_password', None)
        
        logger.info(f"Settings updated by user {get_jwt_identity()}")
        
        return jsonify({
            'success': True,
            'message': 'Settings updated successfully',
            'data': settings_data
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': e.messages
        }), 400
        
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to update settings'
        }), 500


@settings_bp.route('/settings/company', methods=['GET'])
@jwt_required()
def get_company_info():
    """Get company information only (for PDF generation, etc.)."""
    try:
        settings = SystemSettings.get_settings()
        settings_data = settings.to_dict()
        
        return jsonify({
            'success': True,
            'data': settings_data['company_info']
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching company info: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch company information'
        }), 500


@settings_bp.route('/settings/company', methods=['PUT'])
@jwt_required()
@admin_required
def update_company_info():
    """Update company information only."""
    try:
        # Validate request data
        schema = CompanyInfoSchema()
        company_info = schema.load(request.json or {})
        
        # Update settings
        settings = SystemSettings.update_settings(company_info=company_info)
        settings_data = settings.to_dict()
        
        logger.info(f"Company info updated by user {get_jwt_identity()}")
        
        return jsonify({
            'success': True,
            'message': 'Company information updated successfully',
            'data': settings_data['company_info']
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': e.messages
        }), 400
        
    except Exception as e:
        logger.error(f"Error updating company info: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to update company information'
        }), 500


@settings_bp.route('/settings/test-email', methods=['POST'])
@jwt_required()
@admin_required
def test_email_settings():
    """Test email configuration."""
    try:
        settings = SystemSettings.get_settings()
        
        if not settings.smtp_enabled:
            return jsonify({
                'success': False,
                'message': 'Email is not enabled'
            }), 400
        
        # TODO: Implement actual email testing logic here
        # This would involve sending a test email using the configured SMTP settings
        
        return jsonify({
            'success': True,
            'message': 'Email test functionality not implemented yet'
        }), 200
        
    except Exception as e:
        logger.error(f"Error testing email settings: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to test email settings'
        }), 500


@settings_bp.route('/settings/reset', methods=['POST'])
@jwt_required()
@admin_required
def reset_settings():
    """Reset settings to default values."""
    try:
        # Get current settings
        settings = SystemSettings.get_settings()
        
        # Delete current settings
        settings.delete()
        
        # Create new default settings
        new_settings = SystemSettings()
        new_settings.save()
        
        settings_data = new_settings.to_dict()
        
        # Remove sensitive information from response
        if 'email_settings' in settings_data and settings_data['email_settings']:
            settings_data['email_settings'].pop('smtp_password', None)
        
        logger.info(f"Settings reset to defaults by user {get_jwt_identity()}")
        
        return jsonify({
            'success': True,
            'message': 'Settings reset to default values',
            'data': settings_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error resetting settings: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to reset settings'
        }), 500