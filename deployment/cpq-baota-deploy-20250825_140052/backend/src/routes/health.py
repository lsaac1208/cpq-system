from flask import Blueprint, jsonify, current_app
from datetime import datetime
from src.models.base import db
import os
import sys

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Enhanced health check endpoint with environment details."""
    health_data = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'environment': current_app.config.get('ENV', 'unknown'),
        'version': '1.0.0',
        'services': {},
        'configuration': {},
        'runtime': {}
    }
    
    # Test database connection
    try:
        db.session.execute(db.text('SELECT 1'))
        health_data['services']['database'] = {
            'status': 'healthy',
            'type': 'sqlite' if 'sqlite' in current_app.config.get('SQLALCHEMY_DATABASE_URI', '') else 'other'
        }
    except Exception as e:
        health_data['services']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_data['status'] = 'degraded'
    
    # Configuration status
    health_data['configuration'] = {
        'cors_origins': current_app.config.get('CORS_ORIGINS', []),
        'debug_mode': current_app.config.get('DEBUG', False),
        'host': current_app.config.get('HOST', '127.0.0.1'),
        'port': current_app.config.get('PORT', 5000),
        'api_prefix': current_app.config.get('API_PREFIX', '/api/v1')
    }
    
    # Runtime information
    health_data['runtime'] = {
        'python_version': sys.version.split()[0],
        'flask_env': os.environ.get('FLASK_ENV', 'development'),
        'start_time': datetime.utcnow().isoformat(),  # This would be better stored globally
        'pid': os.getpid()
    }
    
    # Overall health determination
    unhealthy_services = [name for name, service in health_data['services'].items() 
                         if isinstance(service, dict) and service.get('status') != 'healthy']
    
    if unhealthy_services:
        health_data['status'] = 'unhealthy'
        health_data['unhealthy_services'] = unhealthy_services
    
    return jsonify(health_data)

@health_bp.route('/', methods=['GET'])
def root():
    """Root endpoint for server status."""
    return jsonify({
        'message': 'CPQ System API Server',
        'version': '1.0.0',
        'status': 'running',
        'timestamp': datetime.utcnow().isoformat(),
        'api_prefix': '/api/v1',
        'endpoints': {
            'health': '/health',
            'ping': '/ping',
            'api_docs': '/api/v1'
        }
    })

@health_bp.route('/ping', methods=['GET'])
def ping():
    """Simple ping endpoint.""" 
    return jsonify({
        'message': 'pong',
        'timestamp': datetime.utcnow().isoformat()
    })