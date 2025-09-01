import re
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from flask import current_app
from typing import Optional, Dict, List
import ipaddress

class PasswordValidator:
    """Password strength validation utility."""
    
    @staticmethod
    def validate_password(password: str) -> Dict[str, any]:
        """
        Validate password strength.
        Returns dict with is_valid boolean and list of errors.
        """
        errors = []
        
        # Minimum length check
        if len(password) < 8:
            errors.append("密码长度至少8个字符")
        
        # Maximum length check
        if len(password) > 128:
            errors.append("密码长度不能超过128个字符")
        
        # Character type requirements
        if not re.search(r'[a-z]', password):
            errors.append("密码必须包含小写字母")
        
        if not re.search(r'[A-Z]', password):
            errors.append("密码必须包含大写字母")
        
        if not re.search(r'\d', password):
            errors.append("密码必须包含数字")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("密码必须包含特殊字符")
        
        # Common password patterns
        if password.lower() in ['password', '12345678', 'qwerty123']:
            errors.append("密码过于简单，请使用复杂密码")
        
        # Sequential characters
        if re.search(r'(012|123|234|345|456|567|678|789|890|abc|bcd|cde)', password.lower()):
            errors.append("密码不能包含连续字符")
        
        # Repeated characters
        if re.search(r'(.)\1{2,}', password):
            errors.append("密码不能包含连续重复字符")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'strength': PasswordValidator._calculate_strength(password)
        }
    
    @staticmethod
    def _calculate_strength(password: str) -> str:
        """Calculate password strength score."""
        score = 0
        
        # Length bonus
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if len(password) >= 16:
            score += 1
        
        # Character types
        if re.search(r'[a-z]', password):
            score += 1
        if re.search(r'[A-Z]', password):
            score += 1
        if re.search(r'\d', password):
            score += 1
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        
        # Entropy bonus
        if len(set(password)) >= 8:
            score += 1
        
        if score <= 3:
            return 'weak'
        elif score <= 6:
            return 'medium'
        else:
            return 'strong'


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self):
        self._attempts = {}
        self._blacklist = {}
    
    def is_allowed(self, identifier: str, max_attempts: int = 5, window_minutes: int = 15) -> Dict[str, any]:
        """
        Check if request is allowed based on rate limiting.
        
        Args:
            identifier: Unique identifier (IP, username, etc.)
            max_attempts: Maximum attempts allowed in time window
            window_minutes: Time window in minutes
        
        Returns:
            Dict with is_allowed boolean and remaining attempts
        """
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=window_minutes)
        
        # Check if permanently blacklisted
        if identifier in self._blacklist:
            blacklist_until = self._blacklist[identifier]
            if now < blacklist_until:
                return {
                    'is_allowed': False,
                    'reason': 'temporarily_blocked',
                    'retry_after': blacklist_until
                }
            else:
                # Remove from blacklist
                del self._blacklist[identifier]
        
        # Clean old attempts
        if identifier in self._attempts:
            self._attempts[identifier] = [
                attempt_time for attempt_time in self._attempts[identifier]
                if attempt_time > window_start
            ]
        
        # Check current attempts
        current_attempts = len(self._attempts.get(identifier, []))
        
        if current_attempts >= max_attempts:
            # Temporarily blacklist
            self._blacklist[identifier] = now + timedelta(minutes=window_minutes)
            return {
                'is_allowed': False,
                'reason': 'rate_limit_exceeded',
                'retry_after': self._blacklist[identifier]
            }
        
        return {
            'is_allowed': True,
            'remaining_attempts': max_attempts - current_attempts
        }
    
    def record_attempt(self, identifier: str):
        """Record a failed attempt."""
        if identifier not in self._attempts:
            self._attempts[identifier] = []
        self._attempts[identifier].append(datetime.now(timezone.utc))


class SecurityHeaders:
    """Security headers utility."""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get recommended security headers."""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-eval'; style-src 'self' 'unsafe-inline'",
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'camera=(), microphone=(), geolocation=()'
        }


class IPValidator:
    """IP address validation and filtering."""
    
    # Common malicious IP ranges (example)
    BLOCKED_RANGES = [
        '10.0.0.0/8',      # Private network
        '172.16.0.0/12',   # Private network
        '192.168.0.0/16',  # Private network
    ]
    
    @staticmethod
    def is_valid_ip(ip_address: str) -> bool:
        """Check if IP address is valid."""
        try:
            ipaddress.ip_address(ip_address)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def is_blocked_ip(ip_address: str) -> bool:
        """Check if IP is in blocked ranges."""
        try:
            ip = ipaddress.ip_address(ip_address)
            for blocked_range in IPValidator.BLOCKED_RANGES:
                if ip in ipaddress.ip_network(blocked_range, strict=False):
                    return True
            return False
        except ValueError:
            return True  # Block invalid IPs


class CSRFProtection:
    """CSRF token generation and validation."""
    
    @staticmethod
    def generate_token() -> str:
        """Generate a secure CSRF token."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_token(token: str, expected_token: str) -> bool:
        """Validate CSRF token using secure comparison."""
        return secrets.compare_digest(token, expected_token)


class SecureSession:
    """Secure session management utilities."""
    
    @staticmethod
    def generate_session_id() -> str:
        """Generate a secure session ID."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_session_data(data: str, salt: Optional[str] = None) -> str:
        """Hash session data securely."""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Use SHA-256 with salt
        hash_object = hashlib.sha256()
        hash_object.update(f"{data}{salt}".encode('utf-8'))
        return f"{salt}:{hash_object.hexdigest()}"
    
    @staticmethod
    def verify_session_data(data: str, hashed_data: str) -> bool:
        """Verify session data against hash."""
        try:
            salt, expected_hash = hashed_data.split(':', 1)
            hash_object = hashlib.sha256()
            hash_object.update(f"{data}{salt}".encode('utf-8'))
            actual_hash = hash_object.hexdigest()
            return secrets.compare_digest(actual_hash, expected_hash)
        except ValueError:
            return False


# Global rate limiter instance
rate_limiter = RateLimiter()