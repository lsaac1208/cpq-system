"""Enhanced authentication decorators with proper error handling and caching."""
from functools import wraps
from flask import jsonify, current_app, g
from flask_jwt_extended import get_jwt_identity
from src.models import User


def require_role(*allowed_roles):
    """Enhanced role decorator with user caching and proper error handling."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check JWT token
            current_user_id = get_jwt_identity()
            if not current_user_id:
                return jsonify({
                    'error': 'Authentication required',
                    'error_code': 'AUTH_REQUIRED'
                }), 401
            
            try:
                # Cache user in request context to avoid duplicate DB queries
                if not hasattr(g, 'current_user'):
                    g.current_user = User.query.filter_by(username=current_user_id).first()
                
                user = g.current_user
                if not user:
                    return jsonify({
                        'error': 'User not found',
                        'error_code': 'USER_NOT_FOUND'
                    }), 404
                
                if not user.is_active:
                    return jsonify({
                        'error': 'Account is deactivated',
                        'error_code': 'ACCOUNT_INACTIVE'
                    }), 403
                
                # Check role permissions
                if allowed_roles and user.role not in allowed_roles:
                    return jsonify({
                        'error': 'Insufficient permissions',
                        'error_code': 'INSUFFICIENT_PERMISSIONS',
                        'required_roles': list(allowed_roles),
                        'user_role': user.role
                    }), 403
                
                return f(*args, **kwargs)
                
            except Exception as e:
                current_app.logger.error(f'Authentication error: {str(e)}')
                return jsonify({
                    'error': 'Authentication system error',
                    'error_code': 'AUTH_SYSTEM_ERROR'
                }), 500
                
        return decorated_function
    return decorator


def require_auth(f):
    """Enhanced authentication decorator with user caching."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return jsonify({
                'error': 'Authentication required',
                'error_code': 'AUTH_REQUIRED'
            }), 401
        
        try:
            # Cache user in request context
            if not hasattr(g, 'current_user'):
                g.current_user = User.query.filter_by(username=current_user_id).first()
            
            user = g.current_user
            if not user or not user.is_active:
                return jsonify({
                    'error': 'User not found or inactive',
                    'error_code': 'USER_INVALID'
                }), 401
            
            return f(*args, **kwargs)
            
        except Exception as e:
            current_app.logger.error(f'Authentication error: {str(e)}')
            return jsonify({
                'error': 'Authentication system error',
                'error_code': 'AUTH_SYSTEM_ERROR'
            }), 500
            
    return decorated_function


def get_current_user():
    """Get current user with caching support."""
    if hasattr(g, 'current_user'):
        return g.current_user
    
    current_user_id = get_jwt_identity()
    if current_user_id:
        try:
            user = User.query.filter_by(username=current_user_id).first()
            g.current_user = user  # Cache for this request
            return user
        except Exception as e:
            current_app.logger.error(f'Error fetching user: {str(e)}')
    
    return None


def admin_required(f):
    """Enhanced admin decorator with proper error handling."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return jsonify({
                'error': 'Authentication required',
                'error_code': 'AUTH_REQUIRED'
            }), 401
        
        try:
            # Cache user in request context
            if not hasattr(g, 'current_user'):
                g.current_user = User.query.filter_by(username=current_user_id).first()
            
            user = g.current_user
            if not user or not user.is_active:
                return jsonify({
                    'error': 'User not found or inactive',
                    'error_code': 'USER_INVALID'
                }), 401
            
            if user.role != 'admin':
                return jsonify({
                    'error': 'Admin access required',
                    'error_code': 'ADMIN_REQUIRED',
                    'user_role': user.role
                }), 403
            
            return f(*args, **kwargs)
            
        except Exception as e:
            current_app.logger.error(f'Admin auth error: {str(e)}')
            return jsonify({
                'error': 'Authentication system error',
                'error_code': 'AUTH_SYSTEM_ERROR'
            }), 500
            
    return decorated_function