"""
Tests for Settings API routes
"""

import pytest
import json
from src.models.settings import SystemSettings


class TestSettingsAPI:
    """Test Settings API endpoints"""
    
    def test_get_settings_success(self, client, auth_headers, app_context):
        """Test GET /api/settings success"""
        # Create some settings
        settings = SystemSettings(
            company_name='Test Company',
            company_email='test@gmail.com',
            default_currency='USD'
        )
        settings.save()
        
        response = client.get('/api/settings', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'data' in data
        
        settings_data = data['data']
        assert settings_data['company_info']['name'] == 'Test Company'
        assert settings_data['company_info']['email'] == 'test@gmail.com'
        assert settings_data['system_config']['default_currency'] == 'USD'
        
        # Sensitive info should be removed
        assert 'smtp_password' not in settings_data.get('email_settings', {})
    
    def test_get_settings_unauthorized(self, client):
        """Test GET /api/settings without authentication"""
        response = client.get('/api/settings')
        
        assert response.status_code == 401
    
    def test_update_settings_success(self, client, admin_auth_headers, app_context):
        """Test PUT /api/settings success"""
        # Create initial settings
        SystemSettings.get_settings()
        
        update_data = {
            'company_info': {
                'name': 'Updated Company',
                'email': 'updated@gmail.com',
                'phone': '+1-234-567-8900'
            },
            'system_config': {
                'default_currency': 'EUR',
                'default_tax_rate': 19.0,
                'quote_validity_days': 45
            }
        }
        
        response = client.put(
            '/api/settings',
            data=json.dumps(update_data),
            content_type='application/json',
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['message'] == 'Settings updated successfully'
        
        # Check updated values
        settings_data = data['data']
        assert settings_data['company_info']['name'] == 'Updated Company'
        assert settings_data['company_info']['email'] == 'updated@gmail.com'
        assert settings_data['system_config']['default_currency'] == 'EUR'
        assert settings_data['system_config']['default_tax_rate'] == 19.0
    
    def test_update_settings_validation_error(self, client, admin_auth_headers, app_context):
        """Test PUT /api/settings with validation errors"""
        # Create initial settings
        SystemSettings.get_settings()
        
        invalid_data = {
            'company_info': {
                'name': '',  # Empty name should fail
                'email': 'invalid-email'  # Invalid email format
            },
            'system_config': {
                'default_tax_rate': 150.0  # Invalid tax rate (>100%)
            }
        }
        
        response = client.put(
            '/api/settings',
            data=json.dumps(invalid_data),
            content_type='application/json',
            headers=admin_auth_headers
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'errors' in data
    
    def test_update_settings_non_admin(self, client, auth_headers, app_context):
        """Test PUT /api/settings with non-admin user"""
        update_data = {
            'company_info': {
                'name': 'Should Not Work'
            }
        }
        
        response = client.put(
            '/api/settings',
            data=json.dumps(update_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['error'] == 'Admin access required'
    
    def test_get_company_info_success(self, client, auth_headers, app_context):
        """Test GET /api/settings/company success"""
        # Create settings with company info
        settings = SystemSettings(
            company_name='Test Company',
            company_address='123 Test St',
            company_phone='+1-555-0123',
            company_email='info@testcompany.com'
        )
        settings.save()
        
        response = client.get('/api/settings/company', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        company_info = data['data']
        assert company_info['name'] == 'Test Company'
        assert company_info['address'] == '123 Test St'
        assert company_info['phone'] == '+1-555-0123'
        assert company_info['email'] == 'info@testcompany.com'
    
    def test_update_company_info_success(self, client, admin_auth_headers, app_context):
        """Test PUT /api/settings/company success"""
        # Create initial settings
        SystemSettings.get_settings()
        
        company_data = {
            'name': 'New Company Name',
            'address': '456 New St',
            'phone': '+1-555-9999',
            'email': 'new@company.com',
            'website': 'https://newcompany.com',
            'tax_number': 'TAX123456'
        }
        
        response = client.put(
            '/api/settings/company',
            data=json.dumps(company_data),
            content_type='application/json',
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['message'] == 'Company information updated successfully'
        
        company_info = data['data']
        assert company_info['name'] == 'New Company Name'
        assert company_info['website'] == 'https://newcompany.com'
    
    def test_reset_settings_success(self, client, admin_auth_headers, app_context):
        """Test POST /api/settings/reset success"""
        # Create and modify settings
        settings = SystemSettings.get_settings()
        settings.company_name = 'Modified Company'
        settings.default_currency = 'EUR'
        settings.save()
        
        response = client.post('/api/settings/reset', headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['message'] == 'Settings reset to default values'
        
        # Check that settings were reset
        settings_data = data['data']
        assert settings_data['company_info']['name'] == 'Your Company Name'
        assert settings_data['system_config']['default_currency'] == 'USD'
    
    def test_reset_settings_non_admin(self, client, auth_headers):
        """Test POST /api/settings/reset with non-admin user"""
        response = client.post('/api/settings/reset', headers=auth_headers)
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['error'] == 'Admin access required'
    
    def test_test_email_settings_not_implemented(self, client, admin_auth_headers, app_context):
        """Test POST /api/settings/test-email (not fully implemented)"""
        # Create settings with email enabled
        settings = SystemSettings.get_settings()
        settings.smtp_enabled = True
        settings.smtp_host = 'smtp.example.com'
        settings.save()
        
        response = client.post('/api/settings/test-email', headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'not implemented' in data['message'].lower()
    
    def test_test_email_settings_disabled(self, client, admin_auth_headers, app_context):
        """Test POST /api/settings/test-email when email is disabled"""
        # Create settings with email disabled
        settings = SystemSettings.get_settings()
        settings.smtp_enabled = False
        settings.save()
        
        response = client.post('/api/settings/test-email', headers=admin_auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['message'] == 'Email is not enabled'