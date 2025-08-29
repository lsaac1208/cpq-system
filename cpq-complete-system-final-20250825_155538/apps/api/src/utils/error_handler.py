# -*- coding: utf-8 -*-
"""
API错误处理工具
提供统一的错误处理和响应格式
"""
import logging
from functools import wraps
from flask import jsonify, request
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

def handle_api_error(func):
    """
    API错误处理装饰器
    统一处理API错误并返回标准格式的错误响应
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPException as e:
            # HTTP异常
            logger.warning(f"HTTP error in {func.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': str(e.description),
                'error_code': e.code,
                'request_id': request.headers.get('X-Request-ID', 'unknown')
            }), e.code
        except ValueError as e:
            # 参数错误
            logger.warning(f"Value error in {func.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': f"Invalid parameter: {str(e)}",
                'error_code': 'INVALID_PARAMETER',
                'request_id': request.headers.get('X-Request-ID', 'unknown')
            }), 400
        except FileNotFoundError as e:
            # 文件未找到
            logger.warning(f"File not found in {func.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': f"Resource not found: {str(e)}",
                'error_code': 'RESOURCE_NOT_FOUND',
                'request_id': request.headers.get('X-Request-ID', 'unknown')
            }), 404
        except PermissionError as e:
            # 权限错误
            logger.warning(f"Permission error in {func.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': f"Permission denied: {str(e)}",
                'error_code': 'PERMISSION_DENIED',
                'request_id': request.headers.get('X-Request-ID', 'unknown')
            }), 403
        except Exception as e:
            # 其他未知错误
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Internal server error',
                'error_code': 'INTERNAL_ERROR',
                'request_id': request.headers.get('X-Request-ID', 'unknown'),
                'debug_info': str(e) if logger.level <= logging.DEBUG else None
            }), 500
    
    return wrapper

def validate_request_data(required_fields=None, optional_fields=None):
    """
    请求数据验证装饰器
    
    Args:
        required_fields: 必需字段列表
        optional_fields: 可选字段列表
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                data = request.get_json() or {}
                
                # 检查必需字段
                if required_fields:
                    missing_fields = [field for field in required_fields if field not in data]
                    if missing_fields:
                        return jsonify({
                            'success': False,
                            'error': f"Missing required fields: {', '.join(missing_fields)}",
                            'error_code': 'MISSING_REQUIRED_FIELDS',
                            'required_fields': required_fields,
                            'missing_fields': missing_fields
                        }), 400
                
                # 过滤无效字段
                if required_fields or optional_fields:
                    allowed_fields = set(required_fields or []) | set(optional_fields or [])
                    filtered_data = {k: v for k, v in data.items() if k in allowed_fields}
                    request._validated_data = filtered_data
                else:
                    request._validated_data = data
                
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Request validation error in {func.__name__}: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': 'Request validation failed',
                    'error_code': 'VALIDATION_ERROR',
                    'details': str(e)
                }), 400
        
        return wrapper
    return decorator

def get_validated_data():
    """获取验证后的请求数据"""
    return getattr(request, '_validated_data', {})

class APIError(Exception):
    """自定义API异常类"""
    
    def __init__(self, message, error_code=None, status_code=400, details=None):
        self.message = message
        self.error_code = error_code or 'API_ERROR'
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)
    
    def to_dict(self):
        return {
            'success': False,
            'error': self.message,
            'error_code': self.error_code,
            'details': self.details,
            'request_id': request.headers.get('X-Request-ID', 'unknown')
        }

def handle_api_exception(e):
    """处理APIError异常"""
    if isinstance(e, APIError):
        return jsonify(e.to_dict()), e.status_code
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'error_code': 'INTERNAL_ERROR'
    }), 500