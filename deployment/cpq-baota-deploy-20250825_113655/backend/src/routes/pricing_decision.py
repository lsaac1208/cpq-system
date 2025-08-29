# -*- coding: utf-8 -*-
"""
报价决策支持API路由
提供基于批量分析结果的智能报价建议
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from ..services.pricing_decision_engine import PricingDecisionEngine
from ..models.batch_analysis import BatchAnalysisJob
from ..models.quote import Quote, QuoteStatus
from ..models.product import Product
from ..utils.error_handler import handle_api_error

# 创建蓝图
pricing_decision_bp = Blueprint('pricing_decision', __name__)
logger = logging.getLogger(__name__)

# 初始化决策引擎
pricing_engine = PricingDecisionEngine()

@pricing_decision_bp.route('/recommendations/<job_id>', methods=['GET'])
@jwt_required()
def generate_recommendations(job_id):
    """
    基于批量分析结果生成报价建议
    """
    try:
        current_user_id = get_jwt_identity()
        
        # 验证任务存在且属于当前用户
        job = BatchAnalysisJob.query.filter_by(
            job_id=job_id,
            user_id=current_user_id
        ).first()
        
        if not job:
            return jsonify({
                'success': False,
                'error': 'Batch analysis job not found'
            }), 404
        
        if job.status.value != 'completed':
            return jsonify({
                'success': False,
                'error': 'Batch analysis job is not completed yet'
            }), 400
        
        # 生成报价建议
        result = pricing_engine.generate_pricing_recommendations(job_id, current_user_id)
        
        if result['success']:
            logger.info(f"Generated pricing recommendations for job {job_id}")
            return jsonify(result), 200
        else:
            logger.error(f"Failed to generate recommendations: {result.get('error')}")
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in generate_recommendations: {str(e)}")
        return handle_api_error(e)

@pricing_decision_bp.route('/create-quote', methods=['POST'])
@jwt_required()
def create_quote_from_recommendation():
    """
    基于报价建议创建正式报价
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['product_id', 'customer_name', 'customer_email', 'recommended_price', 'quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # 验证产品存在
        product = Product.query.get(data['product_id'])
        if not product:
            return jsonify({
                'success': False,
                'error': 'Product not found'
            }), 404
        
        # 创建报价
        quote = Quote(
            customer_name=data['customer_name'],
            customer_email=data['customer_email'],
            customer_company=data.get('customer_company', ''),
            product_id=data['product_id'],
            quantity=data['quantity'],
            unit_price=data['recommended_price'],
            discount_percentage=data.get('discount_percentage', 0),
            notes=data.get('notes', ''),
            terms_conditions=data.get('terms_conditions', ''),
            created_by=current_user_id,
            status=QuoteStatus.DRAFT
        )
        
        # 设置配置
        if 'configuration' in data:
            quote.set_configuration(data['configuration'])
        
        # 计算价格
        quote.calculate_pricing()
        
        # 生成报价号
        quote.save()  # 先保存获取ID
        quote.quote_number = quote.generate_quote_number()
        quote.save()
        
        logger.info(f"Created quote {quote.quote_number} from pricing recommendation")
        
        return jsonify({
            'success': True,
            'data': {
                'quote': quote.to_dict(),
                'message': 'Quote created successfully'
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error in create_quote_from_recommendation: {str(e)}")
        return handle_api_error(e)

@pricing_decision_bp.route('/market-analysis/<job_id>', methods=['GET'])
@jwt_required()
def get_market_analysis(job_id):
    """
    获取基于批量分析的市场分析报告
    """
    try:
        current_user_id = get_jwt_identity()
        
        # 验证任务权限
        job = BatchAnalysisJob.query.filter_by(
            job_id=job_id,
            user_id=current_user_id
        ).first()
        
        if not job:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404
        
        # 提取分析洞察用于市场分析
        analysis_data = pricing_engine._extract_analysis_insights(job_id)
        if not analysis_data:
            return jsonify({
                'success': False,
                'error': 'No analysis data available'
            }), 404
        
        # 生成市场环境分析
        market_context = pricing_engine._analyze_market_context(analysis_data)
        
        # 风险机会分析
        risk_opportunity = pricing_engine._analyze_risks_opportunities(analysis_data, market_context)
        
        from datetime import datetime
        market_report = {
            'job_id': job_id,
            'generated_at': datetime.utcnow().isoformat(),
            'market_context': market_context,
            'insights_summary': analysis_data.get('aggregated_insights', {}),
            'risk_opportunity_analysis': risk_opportunity,
            'recommendations': {
                'market_entry_strategy': _generate_market_entry_strategy(market_context),
                'competitive_positioning': _generate_competitive_positioning(market_context),
                'growth_opportunities': _identify_growth_opportunities(analysis_data)
            }
        }
        
        return jsonify({
            'success': True,
            'data': market_report
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_market_analysis: {str(e)}")
        return handle_api_error(e)

@pricing_decision_bp.route('/product-recommendations/<job_id>', methods=['GET'])
@jwt_required()
def get_product_recommendations(job_id):
    """
    获取基于分析结果的产品推荐
    """
    try:
        current_user_id = get_jwt_identity()
        
        # 验证权限
        job = BatchAnalysisJob.query.filter_by(
            job_id=job_id,
            user_id=current_user_id
        ).first()
        
        if not job:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404
        
        # 获取分析数据
        analysis_data = pricing_engine._extract_analysis_insights(job_id)
        if not analysis_data:
            return jsonify({
                'success': False,
                'error': 'No analysis data available'
            }), 404
        
        # 生成市场环境和产品推荐
        market_context = pricing_engine._analyze_market_context(analysis_data)
        product_recommendations = pricing_engine._generate_product_recommendations(
            analysis_data, market_context
        )
        
        return jsonify({
            'success': True,
            'data': {
                'job_id': job_id,
                'recommendations': product_recommendations,
                'market_context': market_context,
                'total_recommendations': len(product_recommendations)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_product_recommendations: {str(e)}")
        return handle_api_error(e)

@pricing_decision_bp.route('/pricing-strategies/<job_id>', methods=['GET'])
@jwt_required()
def get_pricing_strategies(job_id):
    """
    获取定价策略建议
    """
    try:
        current_user_id = get_jwt_identity()
        
        # 验证权限
        job = BatchAnalysisJob.query.filter_by(
            job_id=job_id,
            user_id=current_user_id
        ).first()
        
        if not job:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404
        
        # 获取分析数据和市场环境
        analysis_data = pricing_engine._extract_analysis_insights(job_id)
        if not analysis_data:
            return jsonify({
                'success': False,
                'error': 'No analysis data available'
            }), 404
        
        market_context = pricing_engine._analyze_market_context(analysis_data)
        product_recommendations = pricing_engine._generate_product_recommendations(
            analysis_data, market_context
        )
        
        # 生成定价策略
        pricing_strategies = pricing_engine._generate_pricing_strategies(
            analysis_data, market_context, product_recommendations
        )
        
        return jsonify({
            'success': True,
            'data': {
                'job_id': job_id,
                'pricing_strategies': pricing_strategies,
                'market_context': market_context
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_pricing_strategies: {str(e)}")
        return handle_api_error(e)

@pricing_decision_bp.route('/batch-jobs', methods=['GET'])
@jwt_required()
def get_completed_jobs():
    """
    获取用户已完成的批量分析任务列表
    """
    try:
        current_user_id = get_jwt_identity()
        
        # 获取已完成的任务
        jobs = BatchAnalysisJob.query.filter_by(
            user_id=current_user_id,
            status='completed'
        ).order_by(BatchAnalysisJob.created_at.desc()).limit(20).all()
        
        job_list = []
        for job in jobs:
            job_data = job.to_dict()
            
            # 检查是否已有报价建议
            # 这里可以添加缓存检查逻辑
            job_data['has_pricing_recommendations'] = True  # 暂时设为True，后续可优化
            
            job_list.append(job_data)
        
        return jsonify({
            'success': True,
            'data': {
                'jobs': job_list,
                'total': len(job_list)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_completed_jobs: {str(e)}")
        return handle_api_error(e)

@pricing_decision_bp.route('/export-recommendations/<job_id>', methods=['GET'])
@jwt_required()
def export_recommendations(job_id):
    """
    导出报价建议报告
    """
    try:
        current_user_id = get_jwt_identity()
        
        # 验证权限
        job = BatchAnalysisJob.query.filter_by(
            job_id=job_id,
            user_id=current_user_id
        ).first()
        
        if not job:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404
        
        # 生成完整报价建议
        result = pricing_engine.generate_pricing_recommendations(job_id, current_user_id)
        
        if not result['success']:
            return jsonify(result), 500
        
        # 格式化导出数据
        export_data = {
            'report_title': f'报价决策建议报告 - {job.job_name}',
            'generated_at': result['data']['generated_at'],
            'job_info': {
                'job_id': job_id,
                'job_name': job.job_name,
                'total_files': job.total_files,
                'analysis_date': job.created_at.isoformat()
            },
            'executive_summary': result['data']['summary'],
            'confidence_score': result['data']['confidence_score'],
            'market_analysis': result['data']['market_context'],
            'product_recommendations': result['data']['product_recommendations'],
            'pricing_strategies': result['data']['pricing_strategies'],
            'risk_opportunity_analysis': result['data']['risk_opportunity_analysis']
        }
        
        return jsonify({
            'success': True,
            'data': export_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error in export_recommendations: {str(e)}")
        return handle_api_error(e)

# 辅助函数
def _generate_market_entry_strategy(market_context: dict) -> dict:
    """生成市场进入策略"""
    competition = market_context.get('competition_intensity', {}).get('level', 'medium')
    demand = market_context.get('demand_heat', {}).get('level', 'medium')
    
    if competition == 'low' and demand == 'high':
        strategy = '快速进入策略'
        description = '市场需求旺盛且竞争较少，建议快速占领市场'
    elif competition == 'high':
        strategy = '差异化进入策略'
        description = '竞争激烈的市场，需要通过差异化获得优势'
    else:
        strategy = '稳健进入策略'
        description = '采用稳健的市场进入方式，逐步建立市场地位'
    
    return {
        'strategy': strategy,
        'description': description,
        'success_factors': ['产品质量', '客户服务', '价格竞争力', '品牌建设']
    }

def _generate_competitive_positioning(market_context: dict) -> dict:
    """生成竞争定位建议"""
    competition = market_context.get('competition_intensity', {})
    
    positioning_options = []
    
    if competition.get('level') == 'high':
        positioning_options.extend([
            '技术领先者 - 通过技术创新获得竞争优势',
            '成本领先者 - 通过规模效应降低成本',
            '细分市场专家 - 专注特定客户群体'
        ])
    else:
        positioning_options.extend([
            '市场领导者 - 建立行业标准和最佳实践',
            '全面解决方案提供商 - 提供端到端服务'
        ])
    
    return {
        'recommended_positioning': positioning_options[0] if positioning_options else '差异化竞争者',
        'alternative_options': positioning_options[1:],
        'key_differentiators': ['产品创新', '服务质量', '行业经验', '解决方案完整性']
    }

def _identify_growth_opportunities(analysis_data: dict) -> list:
    """识别增长机会"""
    insights = analysis_data.get('aggregated_insights', {})
    opportunities = []
    
    # 分析项目机会
    project_opps = insights.get('project_opportunities', [])
    if project_opps:
        opportunities.append({
            'type': '项目机会',
            'description': f'发现{len(project_opps)}个潜在项目机会',
            'potential': 'high'
        })
    
    # 分析产品需求
    product_demands = insights.get('product_demands', [])
    if product_demands:
        opportunities.append({
            'type': '产品需求',
            'description': f'识别{len(product_demands)}个产品需求点',
            'potential': 'medium'
        })
    
    # 分析客户需求
    customer_reqs = insights.get('customer_requirements', [])
    if customer_reqs:
        opportunities.append({
            'type': '客户需求',
            'description': f'发现{len(customer_reqs)}个客户需求',
            'potential': 'high'
        })
    
    return opportunities

# 错误处理
@pricing_decision_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Resource not found'
    }), 404

@pricing_decision_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500