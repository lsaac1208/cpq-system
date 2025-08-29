# -*- coding: utf-8 -*-
"""
AI分析路由 - 简化版本（生产环境降级处理）
当AI服务不可用时的备用处理方案
"""
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.utils.decorators import require_role, require_auth

logger = logging.getLogger(__name__)
ai_analysis_fallback_bp = Blueprint('ai_analysis_fallback', __name__)

@ai_analysis_fallback_bp.route('/supported-formats', methods=['GET'])
@jwt_required()
@require_auth
def get_supported_formats():
    """获取支持的文档格式信息 - 简化版"""
    try:
        return jsonify({
            'success': True,
            'formats': {
                'pdf': {'extensions': ['.pdf'], 'max_size_mb': 10},
                'word': {'extensions': ['.docx', '.doc'], 'max_size_mb': 5},
                'excel': {'extensions': ['.xlsx', '.xls'], 'max_size_mb': 5},
                'text': {'extensions': ['.txt'], 'max_size_mb': 2},
            },
            'note': 'AI分析服务正在维护中，暂时不可用'
        })
    except Exception as e:
        logger.error(f"Error getting supported formats: {str(e)}")
        return jsonify({'error': 'Failed to get format information'}), 500

@ai_analysis_fallback_bp.route('/analyze-document', methods=['POST'])
@jwt_required()
@require_role('engineer', 'admin', 'manager')
def analyze_document():
    """文档分析 - 维护模式响应"""
    try:
        return jsonify({
            'success': False,
            'error': 'AI分析服务正在维护中，请稍后重试',
            'message': '系统正在升级AI分析功能，预计恢复时间：2小时内',
            'status': 'maintenance',
            'alternatives': [
                '您可以手动创建产品并填写相关信息',
                '联系系统管理员获取帮助',
                '稍后重试此功能'
            ]
        }), 503  # Service Unavailable
        
    except Exception as e:
        logger.error(f"AI analysis fallback error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'AI分析服务暂时不可用',
            'status': 'error'
        }), 500

@ai_analysis_fallback_bp.route('/analysis/<int:analysis_id>', methods=['GET'])
@jwt_required()
@require_auth
def get_analysis_result(analysis_id):
    """获取分析结果 - 维护模式响应"""
    return jsonify({
        'success': False,
        'error': f'分析记录 {analysis_id} 暂时无法访问，AI服务正在维护中'
    }), 503

@ai_analysis_fallback_bp.route('/history', methods=['GET'])
@jwt_required()
@require_auth
def get_analysis_history():
    """获取分析历史 - 维护模式响应"""
    return jsonify({
        'success': False,
        'error': 'AI分析历史记录暂时不可用，服务正在维护中',
        'records': [],
        'pagination': {
            'page': 1,
            'per_page': 10,
            'total': 0,
            'pages': 0
        }
    }), 503

@ai_analysis_fallback_bp.route('/statistics', methods=['GET'])
@jwt_required()
@require_role('admin', 'manager')
def get_analysis_statistics():
    """获取统计信息 - 维护模式响应"""
    return jsonify({
        'success': False,
        'error': 'AI分析统计信息暂时不可用，服务正在维护中',
        'statistics': {
            'total_analyses': 0,
            'successful_analyses': 0,
            'success_rate': 0,
            'average_confidence': 0,
            'period_days': 30
        },
        'recent_analyses': []
    }), 503

# 其他端点的维护模式响应
@ai_analysis_fallback_bp.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@jwt_required()
@require_auth
def catch_all_ai_routes(path):
    """捕获所有AI相关路由的维护模式响应"""
    return jsonify({
        'success': False,
        'error': 'AI功能正在维护中，请稍后重试',
        'message': f'路径 /{path} 对应的AI功能暂时不可用',
        'status': 'maintenance'
    }), 503