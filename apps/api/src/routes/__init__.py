from .auth import auth_bp
from .products import products_bp
from .product_gallery import product_gallery_bp
from .quotes import quotes_bp
from .multi_quotes import multi_quotes_bp
from .health import health_bp
from .settings import settings_bp
from .search import search_bp
# 尝试导入AI分析模块，如果失败则使用降级版本
try:
    from .ai_analysis import ai_analysis_bp
    AI_ANALYSIS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  AI Analysis modules not available: {e}")
    from .ai_analysis_fallback import ai_analysis_fallback_bp as ai_analysis_bp
    AI_ANALYSIS_AVAILABLE = False
# 尝试导入其他AI相关模块，如果失败则跳过
try:
    from .batch_analysis import batch_analysis_bp
    BATCH_ANALYSIS_AVAILABLE = True
except ImportError:
    batch_analysis_bp = None
    BATCH_ANALYSIS_AVAILABLE = False

try:
    from .document_comparison import document_comparison_bp  
    DOCUMENT_COMPARISON_AVAILABLE = True
except ImportError:
    document_comparison_bp = None
    DOCUMENT_COMPARISON_AVAILABLE = False

try:
    from .prompt_optimization import prompt_optimization_bp
    PROMPT_OPTIMIZATION_AVAILABLE = True
except ImportError:
    prompt_optimization_bp = None
    PROMPT_OPTIMIZATION_AVAILABLE = False

try:
    from .pricing_decision import pricing_decision_bp
    PRICING_DECISION_AVAILABLE = True
except ImportError:
    pricing_decision_bp = None
    PRICING_DECISION_AVAILABLE = False

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
    # AI分析API - 总是可用（如果失败会使用降级版本）
    app.register_blueprint(ai_analysis_bp, url_prefix=f'{api_prefix}/ai-analysis')
    
    # 其他AI相关API - 仅在可用时注册
    if BATCH_ANALYSIS_AVAILABLE and batch_analysis_bp:
        app.register_blueprint(batch_analysis_bp, url_prefix=f'{api_prefix}/batch-analysis')
        print("✅ 批量分析API已注册")
    else:
        print("⚠️  批量分析API不可用")
        
    if DOCUMENT_COMPARISON_AVAILABLE and document_comparison_bp:
        app.register_blueprint(document_comparison_bp, url_prefix=f'{api_prefix}/document-comparison')
        print("✅ 文档对比分析API已注册")
    else:
        print("⚠️  文档对比分析API不可用")
        
    if PROMPT_OPTIMIZATION_AVAILABLE and prompt_optimization_bp:
        app.register_blueprint(prompt_optimization_bp, url_prefix=f'{api_prefix}/prompt-optimization')
        print("✅ 历史数据优化prompt API已注册")
    else:
        print("⚠️  历史数据优化prompt API不可用")
        
    if PRICING_DECISION_AVAILABLE and pricing_decision_bp:
        app.register_blueprint(pricing_decision_bp, url_prefix=f'{api_prefix}/pricing-decision')
        print("✅ 报价决策支持API已注册")
    else:
        print("⚠️  报价决策支持API不可用")