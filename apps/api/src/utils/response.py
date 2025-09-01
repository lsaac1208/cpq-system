from flask import jsonify
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone

class APIResponse:
    """Standardized API response utility."""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success", status_code: int = 200) -> tuple:
        """Return successful response."""
        response = {
            'success': True,
            'message': message,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        
        if data is not None:
            response['data'] = data
            
        return jsonify(response), status_code
    
    @staticmethod
    def error(message: str, status_code: int = 400, details: Any = None) -> tuple:
        """Return error response."""
        response = {
            'success': False,
            'error': message,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        
        if details is not None:
            response['details'] = details
            
        return jsonify(response), status_code
    
    @staticmethod
    def validation_error(errors: Union[List[str], Dict[str, List[str]]]) -> tuple:
        """Return validation error response."""
        return APIResponse.error(
            message="Validation failed",
            status_code=422,
            details={'validation_errors': errors}
        )
    
    @staticmethod
    def not_found(resource: str = "Resource") -> tuple:
        """Return not found response."""
        return APIResponse.error(
            message=f"{resource} not found",
            status_code=404
        )
    
    @staticmethod
    def unauthorized(message: str = "Authentication required") -> tuple:
        """Return unauthorized response."""
        return APIResponse.error(
            message=message,
            status_code=401
        )
    
    @staticmethod
    def forbidden(message: str = "Access forbidden") -> tuple:
        """Return forbidden response."""
        return APIResponse.error(
            message=message,
            status_code=403
        )
    
    @staticmethod
    def paginated(data: List[Any], page: int, per_page: int, total: int, **kwargs) -> tuple:
        """Return paginated response."""
        has_next = (page * per_page) < total
        has_prev = page > 1
        
        response_data = {
            'items': data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page,  # Ceiling division
                'has_next': has_next,
                'has_prev': has_prev,
            }
        }
        
        # Add any additional data
        response_data.update(kwargs)
        
        return APIResponse.success(data=response_data)