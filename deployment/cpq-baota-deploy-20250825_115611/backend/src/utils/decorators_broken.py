"""Utility decorators for authorization and validation."""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from src.models import User


def require_role(*allowed_roles):
    """Decorator to require specific user roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get current user from JWT token
            current_user_id = get_jwt_identity()
            if not current_user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Get user from database
        # 🔧 修复：JWT存储的是用户名而不是用户ID
        user = User.query.filter_by(username=current_user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 403
            
            # Check if user has required role
            if user.role not in allowed_roles:
                return jsonify({
                    'error': 'Insufficient permissions',
                    'required_roles': list(allowed_roles),
                    'user_role': user.role
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_current_user():
    """Get current user from JWT token."""
    current_user_id = get_jwt_identity()
    if current_user_id:
        return User.query.get(int(current_user_id))
    return None


def require_auth(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # 🔧 修复：JWT存储的是用户名而不是用户ID
        user = User.query.filter_by(username=current_user_id).first()
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 401
        
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # 🔧 修复：JWT存储的是用户名而不是用户ID
        user = User.query.filter_by(username=current_user_id).first()
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 401
        
        # Check if user is admin (assuming 'admin' role exists)
        if user.role != 'admin':
            return jsonify({
                'error': 'Admin access required',
                'user_role': user.role
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function