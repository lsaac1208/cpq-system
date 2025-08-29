import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class."""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///cpq_system.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'dev-jwt-secret'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # API Configuration
    API_PREFIX = os.environ.get('API_PREFIX', '/api/v1')
    
    # CORS Configuration
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:5173').split(',')
    
    # Server Configuration
    HOST = os.environ.get('HOST', '127.0.0.1')
    PORT = int(os.environ.get('PORT', 5000))

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    
    # MySQL配置优化
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('SQLALCHEMY_POOL_SIZE', 20)),
        'max_overflow': int(os.environ.get('SQLALCHEMY_MAX_OVERFLOW', 30)),
        'pool_timeout': int(os.environ.get('SQLALCHEMY_POOL_TIMEOUT', 30)),
        'pool_recycle': int(os.environ.get('SQLALCHEMY_POOL_RECYCLE', 3600)),
        'pool_pre_ping': os.environ.get('SQLALCHEMY_POOL_PRE_PING', 'true').lower() == 'true',
        'echo': False  # 生产环境关闭SQL日志
    }
    
    # 安全配置
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'instance/uploads')
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/app.log')
    
    # 性能监控
    ENABLE_PERFORMANCE_MONITORING = os.environ.get('ENABLE_PERFORMANCE_MONITORING', 'true').lower() == 'true'

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    API_PREFIX = '/api/v1'  # Use consistent API prefix with development

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}