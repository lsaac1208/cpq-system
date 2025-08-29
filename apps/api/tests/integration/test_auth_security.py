import pytest
import json
from flask import url_for
from src.models import User, db


@pytest.mark.integration
@pytest.mark.auth
class TestAuthSecurity:
    """Test authentication security features."""
    
    def test_registration_rate_limiting(self, client):
        """Test registration rate limiting."""
        registration_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "StrongPass1@9!",
            "first_name": "Test",
            "last_name": "User"
        }
        
        # Make multiple registration attempts
        for i in range(4):  # Should allow 3 attempts, block 4th
            response = client.post('/api/auth/register', 
                                 json={**registration_data, "username": f"testuser{i}"})
        
        # 4th attempt should be rate limited
        response = client.post('/api/auth/register', json=registration_data)
        assert response.status_code == 429
        assert "注册尝试过于频繁" in response.get_json()['error']
    
    def test_login_rate_limiting(self, client, test_user):
        """Test login rate limiting."""
        login_data = {
            "username": test_user.username,
            "password": "wrongpassword"
        }
        
        # Make multiple failed login attempts
        for i in range(6):  # Should allow 5 attempts, block 6th
            response = client.post('/api/auth/login', json=login_data)
        
        # 6th attempt should be rate limited
        response = client.post('/api/auth/login', json=login_data)
        assert response.status_code == 429
        assert "登录尝试过于频繁" in response.get_json()['error']
    
    def test_password_strength_validation(self, client):
        """Test password strength validation during registration."""
        weak_passwords = [
            "short",           # Too short
            "nouppercase123!", # No uppercase
            "NOLOWERCASE123!", # No lowercase
            "NoDigitPass!",    # No digit
            "NoSpecialChar123", # No special character
            "password",        # Common password
            "Password123!",    # Sequential characters
            "Passssword1!",    # Repeated characters
        ]
        
        for weak_password in weak_passwords:
            registration_data = {
                "username": "testuser",
                "email": "test@example.com", 
                "password": weak_password,
                "first_name": "Test",
                "last_name": "User"
            }
            
            response = client.post('/api/auth/register', json=registration_data)
            assert response.status_code == 422
            assert 'validation_errors' in response.get_json()['details']
    
    def test_sql_injection_protection(self, client):
        """Test SQL injection protection in login."""
        malicious_inputs = [
            "admin'; DROP TABLE users; --",
            "admin' OR '1'='1",
            "admin' UNION SELECT * FROM users --",
            "'; UPDATE users SET password='hacked' --"
        ]
        
        for malicious_input in malicious_inputs:
            login_data = {
                "username": malicious_input,
                "password": "password"
            }
            
            response = client.post('/api/auth/login', json=login_data)
            # Should return 401 (not 500 which would indicate SQL error)
            assert response.status_code in [401, 422]
    
    def test_xss_protection_in_registration(self, client):
        """Test XSS protection in registration fields."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "&#60;script&#62;alert('xss')&#60;/script&#62;"
        ]
        
        for payload in xss_payloads:
            registration_data = {
                "username": payload,
                "email": "test@example.com",
                "password": "StrongPass1@9!",
                "first_name": payload,
                "last_name": "User"
            }
            
            response = client.post('/api/auth/register', json=registration_data)
            
            # Should either reject the input or sanitize it
            if response.status_code == 201:
                user_data = response.get_json()['data']['user']
                # Check that script tags are not present in response
                assert '<script>' not in str(user_data)
                assert 'javascript:' not in str(user_data)
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access to protected endpoints."""
        protected_endpoints = [
            ('/api/auth/me', 'GET'),
            ('/api/auth/logout', 'POST'),
            ('/api/products', 'POST'),
            ('/api/quotes', 'POST'),
        ]
        
        for endpoint, method in protected_endpoints:
            if method == 'GET':
                response = client.get(endpoint)
            elif method == 'POST':
                response = client.post(endpoint, json={})
            elif method == 'PUT':
                response = client.put(endpoint, json={})
            elif method == 'DELETE':
                response = client.delete(endpoint)
            
            assert response.status_code == 401
    
    def test_token_refresh_security(self, client, test_user, auth_headers):
        """Test token refresh security."""
        # Test with invalid refresh token
        invalid_headers = {'Authorization': 'Bearer invalid_token'}
        response = client.post('/api/auth/refresh', headers=invalid_headers)
        assert response.status_code == 401
        
        # Test with access token instead of refresh token
        response = client.post('/api/auth/refresh', headers=auth_headers)
        # This should fail as we're using access token for refresh
        assert response.status_code == 422
    
    def test_csrf_protection(self, client):
        """Test CSRF protection for state-changing operations."""
        # This is a placeholder - actual CSRF testing would require
        # implementing CSRF tokens in the application
        pass
    
    def test_content_type_validation(self, client):
        """Test content type validation."""
        # Test with invalid content type
        response = client.post('/api/auth/login',
                             data="username=test&password=test",
                             content_type='application/x-www-form-urlencoded')
        
        # Should expect JSON
        assert response.status_code in [400, 415]
    
    def test_large_payload_protection(self, client):
        """Test protection against large payloads."""
        # Create a very large payload
        large_data = {
            "username": "a" * 10000,
            "email": "test@example.com",
            "password": "StrongPass1@9!",
            "first_name": "a" * 10000,
            "last_name": "a" * 10000
        }
        
        response = client.post('/api/auth/register', json=large_data)
        # Should reject or handle gracefully
        assert response.status_code in [400, 413, 422]
    
    def test_empty_request_handling(self, client):
        """Test handling of empty requests."""
        # Test with empty JSON
        response = client.post('/api/auth/login', json={})
        assert response.status_code == 422
        
        # Test with no body
        response = client.post('/api/auth/login')
        assert response.status_code in [400, 422]
    
    def test_malformed_json_handling(self, client):
        """Test handling of malformed JSON."""
        malformed_json = '{"username": "test", "password": '
        
        response = client.post('/api/auth/login',
                             data=malformed_json,
                             content_type='application/json')
        assert response.status_code == 400
    
    def test_sensitive_data_not_logged(self, client, caplog):
        """Test that sensitive data is not logged."""
        login_data = {
            "username": "testuser",
            "password": "secret_password"
        }
        
        response = client.post('/api/auth/login', json=login_data)
        
        # Check that password is not in logs
        log_output = caplog.text
        assert "secret_password" not in log_output
    
    def test_user_enumeration_protection(self, client, test_user):
        """Test protection against user enumeration."""
        # Login with existing user but wrong password
        response1 = client.post('/api/auth/login', json={
            "username": test_user.username,
            "password": "wrongpassword"
        })
        
        # Login with non-existing user
        response2 = client.post('/api/auth/login', json={
            "username": "nonexistentuser",
            "password": "wrongpassword"
        })
        
        # Both should return the same error message
        assert response1.status_code == response2.status_code == 401
        assert response1.get_json()['error'] == response2.get_json()['error']
    
    def test_account_lockout_simulation(self, client, test_user):
        """Test account lockout after multiple failed attempts."""
        # Make multiple failed login attempts for the same user
        for i in range(6):
            response = client.post('/api/auth/login', json={
                "username": test_user.username,
                "password": "wrongpassword"
            })
        
        # Account should be temporarily locked
        # Even with correct password, should be blocked due to rate limiting
        response = client.post('/api/auth/login', json={
            "username": test_user.username,
            "password": "correctpassword"  # Assuming this is the correct password
        })
        
        assert response.status_code == 429