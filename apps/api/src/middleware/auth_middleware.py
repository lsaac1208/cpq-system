from functools import wraps
from flask import jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from src.models import User

def require_auth(f):
    """Decorator to require authentication for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.warning(f"Authentication failed: {str(e)}")
            return jsonify({'error': 'Authentication required'}), 401
    return decorated_function

def require_admin(f):
    """Decorator to require admin privileges for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            username = get_jwt_identity()
            user = User.query.filter_by(username=username).first()
            
            if not user:
                return jsonify({'error': 'User not found'}), 401
            
            if user.role != 'admin':
                return jsonify({'error': 'Admin privileges required'}), 403
                
            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.warning(f"Admin check failed: {str(e)}")
            return jsonify({'error': 'Authentication required'}), 401
    return decorated_function

def get_current_user():
    """Get the current authenticated user."""
    try:
        verify_jwt_in_request()
        username = get_jwt_identity()
        return User.query.filter_by(username=username).first()
    except Exception:
        return None