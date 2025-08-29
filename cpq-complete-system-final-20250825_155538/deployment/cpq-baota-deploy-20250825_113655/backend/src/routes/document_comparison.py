# -*- coding: utf-8 -*-
"""
文档对比分析路由
提供多文档对比分析的API端点
"""
import logging
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError, validate

from src.models import db
from src.models.document_comparison import DocumentComparison, ComparisonDocument, ComparisonResult, ComparisonTemplate
from src.utils.decorators import require_role, require_auth, get_current_user
from src.services.document_comparison_service import DocumentComparisonService, DocumentInfo, ComparisonConfig

logger = logging.getLogger(__name__)
document_comparison_bp = Blueprint('document_comparison', __name__)

# 全局服务实例
comparison_service = DocumentComparisonService()

# Request Schemas
class DocumentInfoSchema(Schema):
    """文档信息Schema"""
    analysis_record_id = fields.Int(required=True)
    label = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    role = fields.Str(missing='secondary', validate=validate.OneOf(['primary', 'secondary', 'reference']))
    weight = fields.Float(missing=1.0, validate=validate.Range(min=0.1, max=10.0))

class ComparisonConfigSchema(Schema):
    """对比配置Schema"""
    comparison_type = fields.Str(missing='product_specs', validate=validate.OneOf([
        'product_specs', 'price_analysis', 'feature_matrix', 'competitive_analysis', 'custom'
    ]))
    focus_areas = fields.List(fields.Str(), missing=[])
    include_similarities = fields.Bool(missing=True)
    include_differences = fields.Bool(missing=True)
    min_confidence_threshold = fields.Float(missing=0.6, validate=validate.Range(min=0.0, max=1.0))
    importance_threshold = fields.Float(missing=0.5, validate=validate.Range(min=0.0, max=1.0))
    max_results_per_category = fields.Int(missing=50, validate=validate.Range(min=1, max=200))
    enable_insights = fields.Bool(missing=True)
    custom_fields = fields.List(fields.Str(), missing=[])

class CreateComparisonSchema(Schema):
    """创建对比分析Schema"""
    name = fields.Str(validate=validate.Length(min=1, max=200))
    description = fields.Str(validate=validate.Length(max=1000))
    documents = fields.List(fields.Nested(DocumentInfoSchema), required=True, validate=validate.Length(min=2, max=10))
    config = fields.Nested(ComparisonConfigSchema, missing={})

class ComparisonTemplateSchema(Schema):
    """对比模板Schema"""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    description = fields.Str(validate=validate.Length(max=1000))
    comparison_type = fields.Str(required=True, validate=validate.OneOf([
        'product_specs', 'price_analysis', 'feature_matrix', 'competitive_analysis', 'custom'
    ]))
    template_config = fields.Dict(required=True)
    comparison_fields = fields.Dict(missing={})
    output_format = fields.Dict(missing={})
    is_public = fields.Bool(missing=False)

@document_comparison_bp.route('/create', methods=['POST'])
@jwt_required()
@require_role('engineer', 'admin', 'manager')
def create_comparison():
    """创建文档对比分析"""
    try:
        # 验证请求数据
        schema = CreateComparisonSchema()
        request_data = schema.load(request.json)
        
        current_user_id = get_jwt_identity()
        
        # 构建文档信息
        documents = []
        for doc_data in request_data['documents']:
            doc_info = DocumentInfo(
                analysis_record_id=doc_data['analysis_record_id'],
                label=doc_data['label'],
                role=doc_data['role'],
                weight=doc_data['weight']
            )
            documents.append(doc_info)
        
        # 构建对比配置
        config_data = request_data.get('config', {})
        config = ComparisonConfig(
            comparison_type=config_data.get('comparison_type', 'product_specs'),
            focus_areas=config_data.get('focus_areas', []),
            include_similarities=config_data.get('include_similarities', True),
            include_differences=config_data.get('include_differences', True),
            min_confidence_threshold=config_data.get('min_confidence_threshold', 0.6),
            importance_threshold=config_data.get('importance_threshold', 0.5),
            max_results_per_category=config_data.get('max_results_per_category', 50),
            enable_insights=config_data.get('enable_insights', True),
            custom_fields=config_data.get('custom_fields', [])
        )
        
        # 创建对比分析
        comparison_id = comparison_service.create_comparison(
            user_id=current_user_id,
            documents=documents,
            config=config,
            name=request_data.get('name'),
            description=request_data.get('description')
        )
        
        logger.info(f"Document comparison created: {comparison_id} by user {current_user_id}")
        
        return jsonify({
            'success': True,
            'comparison_id': comparison_id,
            'message': f'对比分析已创建，包含{len(documents)}个文档'
        }), 201
        
    except ValidationError as err:
        return jsonify({'error': 'Validation error', 'details': err.messages}), 400
    except Exception as e:
        logger.error(f"Error creating comparison: {str(e)}")
        return jsonify({'error': str(e)}), 500

@document_comparison_bp.route('/<comparison_id>/start', methods=['POST'])
@jwt_required()
@require_auth
def start_comparison(comparison_id):
    """启动对比分析"""
    try:
        current_user_id = get_jwt_identity()
        current_user = get_current_user()
        
        # 获取对比记录
        comparison = DocumentComparison.query.filter_by(comparison_id=comparison_id).first()
        if not comparison:
            return jsonify({'error': '对比分析不存在'}), 404
        
        # 权限检查
        if comparison.user_id != current_user_id and current_user.role not in ['admin', 'manager']:
            return jsonify({'error': '无权限访问该对比分析'}), 403
        
        # 启动分析
        success = comparison_service.start_comparison(comparison_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '对比分析已启动'
            })
        else:
            return jsonify({
                'success': False,
                'error': '启动对比分析失败'
            }), 500
            
    except Exception as e:
        logger.error(f"Error starting comparison {comparison_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@document_comparison_bp.route('/<comparison_id>/status', methods=['GET'])
@jwt_required()
@require_auth
def get_comparison_status(comparison_id):
    """获取对比分析状态"""
    try:
        current_user_id = get_jwt_identity()
        current_user = get_current_user()
        
        # 获取对比记录
        comparison = DocumentComparison.query.filter_by(comparison_id=comparison_id).first()
        if not comparison:
            return jsonify({'error': '对比分析不存在'}), 404
        
        # 权限检查
        if comparison.user_id != current_user_id and current_user.role not in ['admin', 'manager']:
            return jsonify({'error': '无权限访问该对比分析'}), 403
        
        # 获取文档信息
        documents = ComparisonDocument.query.filter_by(comparison_id=comparison_id)\
                                          .order_by(ComparisonDocument.display_order).all()
        
        return jsonify({
            'success': True,
            'status': {
                **comparison.to_dict(),
                'documents': [doc.to_dict() for doc in documents]
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting comparison status {comparison_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@document_comparison_bp.route('/<comparison_id>/results', methods=['GET'])
@jwt_required()
@require_auth
def get_comparison_results(comparison_id):
    """获取对比分析结果"""
    try:
        current_user_id = get_jwt_identity()
        current_user = get_current_user()
        
        # 获取对比记录
        comparison = DocumentComparison.query.filter_by(comparison_id=comparison_id).first()
        if not comparison:
            return jsonify({'error': '对比分析不存在'}), 404
        
        # 权限检查
        if comparison.user_id != current_user_id and current_user.role not in ['admin', 'manager']:
            return jsonify({'error': '无权限访问该对比分析'}), 403
        
        # 获取完整结果
        results = comparison_service.get_comparison_results(comparison_id)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error getting comparison results {comparison_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@document_comparison_bp.route('/<comparison_id>/cancel', methods=['POST'])
@jwt_required()
@require_auth
def cancel_comparison(comparison_id):
    """取消对比分析"""
    try:
        current_user_id = get_jwt_identity()
        current_user = get_current_user()
        
        # 获取对比记录
        comparison = DocumentComparison.query.filter_by(comparison_id=comparison_id).first()
        if not comparison:
            return jsonify({'error': '对比分析不存在'}), 404
        
        # 权限检查
        if comparison.user_id != current_user_id and current_user.role not in ['admin', 'manager']:
            return jsonify({'error': '无权限访问该对比分析'}), 403
        
        # 获取取消原因
        reason = request.json.get('reason', '用户主动取消') if request.json else '用户主动取消'
        
        # 取消分析
        success = comparison_service.cancel_comparison(comparison_id, reason)
        
        if success:
            return jsonify({
                'success': True,
                'message': '对比分析已取消'
            })
        else:
            return jsonify({
                'success': False,
                'error': '取消对比分析失败'
            }), 500
            
    except Exception as e:
        logger.error(f"Error cancelling comparison {comparison_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@document_comparison_bp.route('/list', methods=['GET'])
@jwt_required()
@require_auth
def list_comparisons():
    """获取对比分析列表"""
    try:
        current_user_id = get_jwt_identity()
        current_user = get_current_user()
        
        # 查询参数
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        status = request.args.get('status')
        comparison_type = request.args.get('type')
        
        # 构建查询
        query = DocumentComparison.query
        
        # 用户过滤（普通用户只能看到自己的对比）
        if current_user.role not in ['admin', 'manager']:
            query = query.filter_by(user_id=current_user_id)
        
        # 状态过滤
        if status:
            query = query.filter(DocumentComparison.status == status)
        
        # 类型过滤
        if comparison_type:
            query = query.filter(DocumentComparison.comparison_type == comparison_type)
        
        # 分页
        comparisons = query.order_by(DocumentComparison.created_at.desc())\
                          .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'comparisons': [comp.to_dict() for comp in comparisons.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': comparisons.total,
                'pages': comparisons.pages
            }
        })
        
    except Exception as e:
        logger.error(f"Error listing comparisons: {str(e)}")
        return jsonify({'error': str(e)}), 500

@document_comparison_bp.route('/<comparison_id>/export', methods=['POST'])
@jwt_required()
@require_auth
def export_comparison_results(comparison_id):
    """导出对比分析结果"""
    try:
        current_user_id = get_jwt_identity()
        current_user = get_current_user()
        
        # 获取对比记录
        comparison = DocumentComparison.query.filter_by(comparison_id=comparison_id).first()
        if not comparison:
            return jsonify({'error': '对比分析不存在'}), 404
        
        # 权限检查
        if comparison.user_id != current_user_id and current_user.role not in ['admin', 'manager']:
            return jsonify({'error': '无权限访问该对比分析'}), 403
        
        # 获取导出格式
        export_format = request.json.get('format', 'json') if request.json else 'json'
        if export_format not in ['json', 'csv', 'excel', 'pdf']:
            return jsonify({'error': '不支持的导出格式'}), 400
        
        # 获取完整结果
        results = comparison_service.get_comparison_results(comparison_id)
        
        # 这里可以根据需要实现不同格式的导出
        # 目前返回JSON格式
        return jsonify({
            'success': True,
            'export_data': results,
            'format': export_format,
            'filename': f"comparison_{comparison_id}_{comparison.created_at.strftime('%Y%m%d_%H%M%S')}.{export_format}"
        })
        
    except Exception as e:
        logger.error(f"Error exporting comparison results {comparison_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@document_comparison_bp.route('/templates', methods=['GET'])
@jwt_required()
@require_auth
def get_comparison_templates():
    """获取对比模板"""
    try:
        current_user_id = get_jwt_identity()
        comparison_type = request.args.get('type')
        
        # 获取公开模板
        public_templates = ComparisonTemplate.get_public_templates(
            comparison_type=comparison_type
        ) if comparison_type else ComparisonTemplate.get_public_templates()
        
        # 获取用户模板
        user_templates = ComparisonTemplate.get_user_templates(current_user_id)
        
        return jsonify({
            'success': True,
            'templates': {
                'public': [template.to_dict() for template in public_templates],
                'user': [template.to_dict() for template in user_templates]
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting comparison templates: {str(e)}")
        return jsonify({'error': str(e)}), 500

@document_comparison_bp.route('/templates', methods=['POST'])
@jwt_required()
@require_auth
def create_comparison_template():
    """创建对比模板"""
    try:
        # 验证请求数据
        schema = ComparisonTemplateSchema()
        request_data = schema.load(request.json)
        
        current_user_id = get_jwt_identity()
        
        # 创建模板
        template = ComparisonTemplate()
        template.template_id = f"tpl_{int(time.time())}_{current_user_id}"
        template.name = request_data['name']
        template.description = request_data.get('description')
        template.comparison_type = request_data['comparison_type']
        template.template_config = request_data['template_config']
        template.comparison_fields = request_data.get('comparison_fields', {})
        template.output_format = request_data.get('output_format', {})
        template.is_public = request_data.get('is_public', False)
        template.created_by = current_user_id
        template.save()
        
        logger.info(f"Comparison template created: {template.template_id} by user {current_user_id}")
        
        return jsonify({
            'success': True,
            'template_id': template.template_id,
            'message': '对比模板已创建'
        }), 201
        
    except ValidationError as err:
        return jsonify({'error': 'Validation error', 'details': err.messages}), 400
    except Exception as e:
        logger.error(f"Error creating comparison template: {str(e)}")
        return jsonify({'error': str(e)}), 500

@document_comparison_bp.route('/statistics', methods=['GET'])
@jwt_required()
@require_role('admin', 'manager')
def get_comparison_statistics():
    """获取对比分析统计信息"""
    try:
        days = int(request.args.get('days', 30))
        user_id = request.args.get('user_id', type=int)
        
        from datetime import datetime, timedelta
        from sqlalchemy import func, and_
        
        # 时间范围
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # 构建查询
        query = db.session.query(DocumentComparison)
        if user_id:
            query = query.filter(DocumentComparison.user_id == user_id)
        
        query = query.filter(DocumentComparison.created_at >= start_date)
        
        # 基础统计
        total_comparisons = query.count()
        completed_comparisons = query.filter(DocumentComparison.status == 'completed').count()
        failed_comparisons = query.filter(DocumentComparison.status == 'failed').count()
        
        # 按类型统计
        type_stats = db.session.query(
            DocumentComparison.comparison_type,
            func.count(DocumentComparison.id).label('count')
        ).filter(DocumentComparison.created_at >= start_date)
        
        if user_id:
            type_stats = type_stats.filter(DocumentComparison.user_id == user_id)
        
        type_stats = type_stats.group_by(DocumentComparison.comparison_type).all()
        
        # 平均处理时间
        avg_processing_time = db.session.query(
            func.avg(DocumentComparison.processing_duration)
        ).filter(
            and_(
                DocumentComparison.created_at >= start_date,
                DocumentComparison.processing_duration.isnot(None)
            )
        )
        
        if user_id:
            avg_processing_time = avg_processing_time.filter(DocumentComparison.user_id == user_id)
        
        avg_time = avg_processing_time.scalar() or 0
        
        statistics = {
            'period_days': days,
            'total_comparisons': total_comparisons,
            'completed_comparisons': completed_comparisons,
            'failed_comparisons': failed_comparisons,
            'success_rate': round((completed_comparisons / total_comparisons * 100), 2) if total_comparisons > 0 else 0,
            'average_processing_time': round(avg_time, 2),
            'type_distribution': {row[0].value if hasattr(row[0], 'value') else str(row[0]): row[1] for row in type_stats}
        }
        
        return jsonify({
            'success': True,
            'statistics': statistics
        })
        
    except Exception as e:
        logger.error(f"Error getting comparison statistics: {str(e)}")
        return jsonify({'error': str(e)}), 500