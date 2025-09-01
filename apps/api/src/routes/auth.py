from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, get_jwt
from marshmallow import Schema, fields, ValidationError
from src.models import db, User
from src.utils.security import PasswordValidator, rate_limiter, SecurityHeaders, IPValidator
from src.utils.response import APIResponse
import logging

auth_bp = Blueprint('auth', __name__)

# Setup logging
logger = logging.getLogger(__name__)

# Schemas for request validation
class RegisterSchema(Schema):
    username = fields.Str(required=True, validate=lambda x: 3 <= len(x) <= 50)
    email = fields.Email(required=True)
    password = fields.Str(required=True)  # Validation moved to PasswordValidator
    first_name = fields.Str(required=True, validate=lambda x: len(x) <= 50)
    last_name = fields.Str(required=True, validate=lambda x: len(x) <= 50)

class LoginSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user with enhanced security."""
    try:
        # Get client IP
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        
        # Check IP validity
        if not IPValidator.is_valid_ip(client_ip) or IPValidator.is_blocked_ip(client_ip):
            logger.warning(f"Registration attempt from invalid/blocked IP: {client_ip}")
            return APIResponse.error("访问被拒绝", 403)
        
        # Rate limiting (skip in testing mode)
        if not current_app.config.get('TESTING', False):
            rate_check = rate_limiter.is_allowed(f"register:{client_ip}", max_attempts=3, window_minutes=60)
            if not rate_check['is_allowed']:
                logger.warning(f"Rate limit exceeded for registration from IP: {client_ip}")
                return APIResponse.error("注册尝试过于频繁，请稍后再试", 429)
        
        # Validate request data
        schema = RegisterSchema()
        data = schema.load(request.json or {})
        
        # Validate password strength
        password_validation = PasswordValidator.validate_password(data['password'])
        if not password_validation['is_valid']:
            rate_limiter.record_attempt(f"register:{client_ip}")
            return APIResponse.validation_error(password_validation['errors'])
        
        # Check if user already exists
        if User.query.filter_by(username=data['username']).first():
            rate_limiter.record_attempt(f"register:{client_ip}")
            return APIResponse.error('用户名已存在', 400)
        
        if User.query.filter_by(email=data['email']).first():
            rate_limiter.record_attempt(f"register:{client_ip}")
            return APIResponse.error('邮箱已存在', 400)
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name']
        )
        user.set_password(data['password'])
        user.save()
        
        # Log successful registration
        logger.info(f"New user registered: {user.username} from IP: {client_ip}")
        
        # Generate tokens
        tokens = user.get_tokens()
        
        return APIResponse.success({
            'user': user.to_dict(),
            'tokens': tokens
        }, "用户注册成功", 201)
        
    except ValidationError as err:
        rate_limiter.record_attempt(f"register:{client_ip}")
        logger.warning(f"Registration validation error from IP {client_ip}: {err.messages}")
        return APIResponse.validation_error(err.messages)
    except Exception as e:
        rate_limiter.record_attempt(f"register:{client_ip}")
        logger.error(f"Registration error from IP {client_ip}: {str(e)}")
        return APIResponse.error("注册失败，请稍后重试", 500)

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user with enhanced security."""
    try:
        # Get client IP
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        
        # Check IP validity
        if not IPValidator.is_valid_ip(client_ip) or IPValidator.is_blocked_ip(client_ip):
            logger.warning(f"Login attempt from invalid/blocked IP: {client_ip}")
            return APIResponse.error("访问被拒绝", 403)
        
        # Validate request data
        schema = LoginSchema()
        data = schema.load(request.json or {})
        
        username = data['username']
        
        # Rate limiting by IP and username (skip in testing mode)
        if not current_app.config.get('TESTING', False):
            ip_rate_check = rate_limiter.is_allowed(f"login_ip:{client_ip}", max_attempts=10, window_minutes=15)
            user_rate_check = rate_limiter.is_allowed(f"login_user:{username}", max_attempts=5, window_minutes=15)
            
            if not ip_rate_check['is_allowed']:
                logger.warning(f"Login rate limit exceeded for IP: {client_ip}")
                return APIResponse.error("登录尝试过于频繁，请稍后再试", 429)
            
            if not user_rate_check['is_allowed']:
                logger.warning(f"Login rate limit exceeded for user: {username} from IP: {client_ip}")
                return APIResponse.error("登录尝试过于频繁，请稍后再试", 429)
        
        # Find user and check password
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(data['password']):
            # Record failed attempt
            rate_limiter.record_attempt(f"login_ip:{client_ip}")
            rate_limiter.record_attempt(f"login_user:{username}")
            
            logger.warning(f"Failed login attempt for user: {username} from IP: {client_ip}")
            return APIResponse.error('用户名或密码错误', 401)
        
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {username} from IP: {client_ip}")
            return APIResponse.error('账户已停用', 401)
        
        # Log successful login
        logger.info(f"Successful login for user: {username} from IP: {client_ip}")
        
        # Generate tokens
        tokens = user.get_tokens()
        
        return APIResponse.success({
            'user': user.to_dict(),
            'tokens': tokens
        }, "登录成功")
        
    except ValidationError as err:
        rate_limiter.record_attempt(f"login_ip:{client_ip}")
        logger.warning(f"Login validation error from IP {client_ip}: {err.messages}")
        return APIResponse.validation_error(err.messages)
    except Exception as e:
        rate_limiter.record_attempt(f"login_ip:{client_ip}")
        logger.error(f"Login error from IP {client_ip}: {str(e)}")
        return APIResponse.error("登录失败，请稍后重试", 500)

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token."""
    try:
        current_user_id = get_jwt_identity()
        # 🔧 修复：JWT存储的是用户名，不是用户ID
        user = User.query.filter_by(username=current_user_id).first()
        
        if not user or not user.is_active:
            return jsonify({'error': '用户不存在或已停用'}), 404
        
        new_token = create_access_token(identity=current_user_id)
        
        return jsonify({
            'access_token': new_token
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user information."""
    try:
        current_user_id = get_jwt_identity()
        # 🔧 修复：JWT存储的是用户名，不是用户ID
        user = User.query.filter_by(username=current_user_id).first()
        
        if not user:
            return jsonify({'error': '用户未找到'}), 404
        
        return jsonify({
            'user': user.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user."""
    try:
        # In a real application, you might want to blacklist the token
        # For now, we just return a success message
        return jsonify({
            'message': '登出成功'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500