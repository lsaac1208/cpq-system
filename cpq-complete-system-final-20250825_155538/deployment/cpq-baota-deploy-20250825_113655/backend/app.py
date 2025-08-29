import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

from config import config
from src.models import db
from src.routes import register_routes
from src.middleware import register_error_handlers
from src.middleware.performance_monitor import init_performance_monitoring

def create_app(config_name=None):
    """Create and configure Flask application."""
    
    # Get configuration name from environment or use default
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    # Enhanced CORS configuration
    CORS(app, 
         origins=app.config['CORS_ORIGINS'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         allow_headers=['Content-Type', 'Authorization'],
         supports_credentials=True)
    
    JWTManager(app)
    Migrate(app, db)
    
    # Register routes
    register_routes(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Initialize performance monitoring
    init_performance_monitoring(app)
    
    # Note: Static file serving is now handled in products blueprint
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    # Get host and port from config
    host = app.config.get('HOST', '127.0.0.1')
    port = app.config.get('PORT', 5000)
    debug = app.config.get('DEBUG', True)
    
    print(f"🚀 CPQ API Server starting...")
    print(f"📍 Running on http://{host}:{port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"📊 Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    app.run(host=host, port=port, debug=debug)