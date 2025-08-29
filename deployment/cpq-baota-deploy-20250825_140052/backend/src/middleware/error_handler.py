from flask import jsonify, current_app
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from jwt.exceptions import InvalidTokenError
import traceback

def register_error_handlers(app):
    """Register global error handlers for the application."""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': str(error.description) if error.description else 'Invalid request parameters'
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication required'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': 'Forbidden',
            'message': 'Insufficient permissions'
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'Resource not found'
        }), 404
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        return jsonify({
            'error': 'Unprocessable Entity',
            'message': 'Validation failed',
            'details': error.description if hasattr(error, 'description') else None
        }), 422
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500
    
    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        if current_app.debug:
            current_app.logger.error(f"Database error: {str(error)}")
        return jsonify({
            'error': 'Database Error',
            'message': 'A database error occurred'
        }), 500
    
    @app.errorhandler(InvalidTokenError)
    def jwt_error(error):
        return jsonify({
            'error': 'Invalid Token',
            'message': 'JWT token is invalid or expired'
        }), 401
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle unexpected exceptions."""
        if isinstance(error, HTTPException):
            return error
        
        # Log the error for debugging
        if current_app.debug:
            current_app.logger.error(f"Unhandled exception: {str(error)}")
            current_app.logger.error(traceback.format_exc())
        
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500