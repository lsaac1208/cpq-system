import pytest
import time
from datetime import datetime, timedelta
from src.utils.security import (
    PasswordValidator, RateLimiter, SecurityHeaders, 
    IPValidator, CSRFProtection, SecureSession
)


class TestPasswordValidator:
    """Test password validation functionality."""
    
    def test_valid_strong_password(self):
        """Test a strong valid password."""
        result = PasswordValidator.validate_password("StrongPass1@9!")
        assert result['is_valid'] is True
        assert result['strength'] in ['medium', 'strong']
        assert len(result['errors']) == 0
    
    def test_short_password(self):
        """Test password too short."""
        result = PasswordValidator.validate_password("Short1!")
        assert result['is_valid'] is False
        assert "密码长度至少8个字符" in result['errors']
    
    def test_no_uppercase(self):
        """Test password without uppercase letter."""
        result = PasswordValidator.validate_password("lowercase123!")
        assert result['is_valid'] is False
        assert "密码必须包含大写字母" in result['errors']
    
    def test_no_lowercase(self):
        """Test password without lowercase letter."""
        result = PasswordValidator.validate_password("UPPERCASE123!")
        assert result['is_valid'] is False
        assert "密码必须包含小写字母" in result['errors']
    
    def test_no_digit(self):
        """Test password without digit."""
        result = PasswordValidator.validate_password("NoDigitPass!")
        assert result['is_valid'] is False
        assert "密码必须包含数字" in result['errors']
    
    def test_no_special_char(self):
        """Test password without special character."""
        result = PasswordValidator.validate_password("NoSpecialChar123")
        assert result['is_valid'] is False
        assert "密码必须包含特殊字符" in result['errors']
    
    def test_common_password(self):
        """Test common weak password."""
        result = PasswordValidator.validate_password("password")
        assert result['is_valid'] is False
        assert "密码过于简单，请使用复杂密码" in result['errors']
    
    def test_sequential_characters(self):
        """Test password with sequential characters."""
        result = PasswordValidator.validate_password("Password123!")
        assert result['is_valid'] is False
        assert "密码不能包含连续字符" in result['errors']
    
    def test_repeated_characters(self):
        """Test password with repeated characters."""
        result = PasswordValidator.validate_password("Passssword1!")
        assert result['is_valid'] is False
        assert "密码不能包含连续重复字符" in result['errors']
    
    def test_very_long_password(self):
        """Test password that exceeds maximum length."""
        long_password = "A" * 129 + "1!"
        result = PasswordValidator.validate_password(long_password)
        assert result['is_valid'] is False
        assert "密码长度不能超过128个字符" in result['errors']
    
    def test_strength_calculation(self):
        """Test password strength calculation."""
        weak_result = PasswordValidator.validate_password("abc")  # Too short, will be invalid but test strength
        medium_result = PasswordValidator.validate_password("MediumPass1@9!")  # No sequential chars
        strong_result = PasswordValidator.validate_password("VeryStrongPassword1@9#$%")  # Long, no sequential
        
        assert weak_result['strength'] == 'weak'
        assert medium_result['strength'] in ['medium', 'strong']
        assert strong_result['strength'] == 'strong'


class TestRateLimiter:
    """Test rate limiting functionality."""
    
    def test_initial_request_allowed(self):
        """Test that initial request is allowed."""
        limiter = RateLimiter()
        result = limiter.is_allowed("test_user", max_attempts=5, window_minutes=15)
        assert result['is_allowed'] is True
        assert result['remaining_attempts'] == 5
    
    def test_rate_limit_exceeded(self):
        """Test rate limit enforcement."""
        limiter = RateLimiter()
        identifier = "test_user_2"
        
        # Make maximum allowed attempts
        for i in range(5):
            limiter.record_attempt(identifier)
        
        # Next request should be blocked
        result = limiter.is_allowed(identifier, max_attempts=5, window_minutes=15)
        assert result['is_allowed'] is False
        assert result['reason'] == 'rate_limit_exceeded'
        assert 'retry_after' in result
    
    def test_window_expiry(self):
        """Test that rate limit window expires."""
        limiter = RateLimiter()
        identifier = "test_user_3"
        
        # Make attempts beyond the window (simulated)
        past_time = datetime.utcnow() - timedelta(minutes=20)
        limiter._attempts[identifier] = [past_time] * 5
        
        # Should be allowed as attempts are outside window
        result = limiter.is_allowed(identifier, max_attempts=5, window_minutes=15)
        assert result['is_allowed'] is True
    
    def test_blacklist_functionality(self):
        """Test blacklist functionality."""
        limiter = RateLimiter()
        identifier = "test_user_4"
        
        # Trigger blacklist
        for i in range(5):
            limiter.record_attempt(identifier)
        
        # Trigger blacklist by checking after max attempts
        limiter.is_allowed(identifier, max_attempts=5, window_minutes=15)
        
        # Should be blacklisted
        result = limiter.is_allowed(identifier, max_attempts=5, window_minutes=15)
        assert result['is_allowed'] is False
        assert result['reason'] == 'temporarily_blocked'


class TestSecurityHeaders:
    """Test security headers utility."""
    
    def test_get_security_headers(self):
        """Test security headers generation."""
        headers = SecurityHeaders.get_security_headers()
        
        required_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection',
            'Strict-Transport-Security',
            'Content-Security-Policy',
            'Referrer-Policy',
            'Permissions-Policy'
        ]
        
        for header in required_headers:
            assert header in headers
            assert headers[header] is not None
            assert len(headers[header]) > 0


class TestIPValidator:
    """Test IP validation functionality."""
    
    def test_valid_ipv4(self):
        """Test valid IPv4 address."""
        assert IPValidator.is_valid_ip("192.168.1.1") is True
        assert IPValidator.is_valid_ip("8.8.8.8") is True
        assert IPValidator.is_valid_ip("127.0.0.1") is True
    
    def test_valid_ipv6(self):
        """Test valid IPv6 address."""
        assert IPValidator.is_valid_ip("2001:0db8:85a3:0000:0000:8a2e:0370:7334") is True
        assert IPValidator.is_valid_ip("::1") is True
    
    def test_invalid_ip(self):
        """Test invalid IP addresses."""
        assert IPValidator.is_valid_ip("not_an_ip") is False
        assert IPValidator.is_valid_ip("256.256.256.256") is False
        assert IPValidator.is_valid_ip("192.168.1") is False
    
    def test_blocked_ip_ranges(self):
        """Test blocked IP range detection."""
        # Test private networks (if configured as blocked)
        assert IPValidator.is_blocked_ip("192.168.1.1") is True
        assert IPValidator.is_blocked_ip("10.0.0.1") is True
        assert IPValidator.is_blocked_ip("172.16.0.1") is True
        
        # Test public IP (should not be blocked by default)
        assert IPValidator.is_blocked_ip("8.8.8.8") is False


class TestCSRFProtection:
    """Test CSRF protection functionality."""
    
    def test_generate_token(self):
        """Test CSRF token generation."""
        token1 = CSRFProtection.generate_token()
        token2 = CSRFProtection.generate_token()
        
        assert token1 is not None
        assert token2 is not None
        assert len(token1) > 20  # Should be reasonably long
        assert token1 != token2  # Should be unique
    
    def test_validate_token_success(self):
        """Test successful token validation."""
        token = CSRFProtection.generate_token()
        assert CSRFProtection.validate_token(token, token) is True
    
    def test_validate_token_failure(self):
        """Test failed token validation."""
        token1 = CSRFProtection.generate_token()
        token2 = CSRFProtection.generate_token()
        assert CSRFProtection.validate_token(token1, token2) is False
    
    def test_validate_empty_tokens(self):
        """Test validation with empty tokens."""
        assert CSRFProtection.validate_token("", "") is True
        assert CSRFProtection.validate_token("valid_token", "") is False
        assert CSRFProtection.validate_token("", "valid_token") is False


class TestSecureSession:
    """Test secure session management."""
    
    def test_generate_session_id(self):
        """Test session ID generation."""
        id1 = SecureSession.generate_session_id()
        id2 = SecureSession.generate_session_id()
        
        assert id1 is not None
        assert id2 is not None
        assert len(id1) > 20
        assert id1 != id2
    
    def test_hash_session_data(self):
        """Test session data hashing."""
        data = "test_session_data"
        hashed = SecureSession.hash_session_data(data)
        
        assert hashed is not None
        assert ":" in hashed  # Should contain salt separator
        assert len(hashed) > 50  # Should be reasonably long
    
    def test_verify_session_data_success(self):
        """Test successful session data verification."""
        data = "test_session_data"
        hashed = SecureSession.hash_session_data(data)
        
        assert SecureSession.verify_session_data(data, hashed) is True
    
    def test_verify_session_data_failure(self):
        """Test failed session data verification."""
        data1 = "test_session_data"
        data2 = "different_data"
        hashed = SecureSession.hash_session_data(data1)
        
        assert SecureSession.verify_session_data(data2, hashed) is False
    
    def test_verify_malformed_hash(self):
        """Test verification with malformed hash."""
        data = "test_data"
        malformed_hash = "malformed_hash_without_separator"
        
        assert SecureSession.verify_session_data(data, malformed_hash) is False