from .auth import auth_bp
from .products import products_bp
from .product_gallery import product_gallery_bp
from .quotes import quotes_bp
from .multi_quotes import multi_quotes_bp
from .health import health_bp
from .settings import settings_bp
from .search import search_bp
from .ai_analysis import ai_analysis_bp
from .batch_analysis import batch_analysis_bp
from .document_comparison import document_comparison_bp
from .prompt_optimization import prompt_optimization_bp
from .pricing_decision import pricing_decision_bp

def register_routes(app):
    """Register all route blueprints."""
    
    # Get API prefix from config
    api_prefix = app.config.get('API_PREFIX', '/api/v1')
    
    # Register blueprints
    app.register_blueprint(health_bp)  # Health check doesn't need API prefix
    app.register_blueprint(auth_bp, url_prefix=f'{api_prefix}/auth')
    app.register_blueprint(products_bp, url_prefix=f'{api_prefix}/products')
    app.register_blueprint(product_gallery_bp, url_prefix=f'{api_prefix}/products')  # 图片集API
    app.register_blueprint(quotes_bp, url_prefix=f'{api_prefix}/quotes')
    app.register_blueprint(multi_quotes_bp, url_prefix=f'{api_prefix}/multi-quotes')
    app.register_blueprint(settings_bp, url_prefix=f'{api_prefix}')
    app.register_blueprint(search_bp, url_prefix=f'{api_prefix}/search')
    app.register_blueprint(ai_analysis_bp, url_prefix=f'{api_prefix}/ai-analysis')  # AI分析API
    app.register_blueprint(batch_analysis_bp, url_prefix=f'{api_prefix}/batch-analysis')  # 批量分析API
    app.register_blueprint(document_comparison_bp, url_prefix=f'{api_prefix}/document-comparison')  # 文档对比分析API
    app.register_blueprint(prompt_optimization_bp, url_prefix=f'{api_prefix}/prompt-optimization')  # 历史数据优化prompt API
    app.register_blueprint(pricing_decision_bp, url_prefix=f'{api_prefix}/pricing-decision')  # 报价决策支持API