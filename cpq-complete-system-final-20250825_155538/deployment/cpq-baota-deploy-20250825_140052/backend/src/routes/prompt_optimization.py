# -*- coding: utf-8 -*-
"""
历史数据优化Prompt管理API路由
提供prompt优化相关的API接口
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from datetime import datetime

from src.services.historical_data_analyzer import HistoricalDataAnalyzer
from src.services.prompt_optimization_engine import PromptOptimizationEngine  
from src.services.learning_feedback_system import LearningFeedbackSystem
from src.models.prompt_optimization import (
    PromptTemplate, PromptOptimizationHistory, UserAnalysisPattern, PromptABTest
)
from src.models.ai_analysis import AIAnalysisRecord
from src.models.user import User

logger = logging.getLogger(__name__)

# 创建蓝图
prompt_optimization_bp = Blueprint('prompt_optimization', __name__, url_prefix='/api/v1/prompt-optimization')

# 初始化服务
historical_analyzer = HistoricalDataAnalyzer()
optimization_engine = PromptOptimizationEngine()
feedback_system = LearningFeedbackSystem()

@prompt_optimization_bp.route('/user-stats/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_optimization_stats(user_id):
    """获取用户优化统计信息"""
    try:
        current_user_id = get_jwt_identity()
        
        # 检查权限：用户只能查看自己的统计或管理员可以查看所有
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 401
        
        if user_id != current_user_id and user.role != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        # 获取请求参数
        document_type = request.args.get('document_type')
        days = int(request.args.get('days', 30))
        
        # 分析用户历史模式
        user_analysis = historical_analyzer.analyze_user_patterns(user_id, document_type)
        
        # 获取学习洞察
        learning_insights = feedback_system.get_learning_insights(user_id, days)
        
        # 获取最近的优化记录
        recent_optimizations = PromptOptimizationHistory.query.filter_by(user_id=user_id)\
                                                           .order_by(PromptOptimizationHistory.created_at.desc())\
                                                           .limit(10).all()
        
        response_data = {
            'success': True,
            'user_id': user_id,
            'document_type': document_type,
            'analysis_period_days': days,
            'user_analysis': user_analysis,
            'learning_insights': learning_insights,
            'recent_optimizations': [opt.to_dict() for opt in recent_optimizations],
            'summary': {
                'total_records': user_analysis.get('total_records', 0),
                'overall_accuracy': user_analysis.get('statistics', {}).get('overall_accuracy', 0),
                'avg_confidence': user_analysis.get('statistics', {}).get('avg_confidence', 0),
                'optimization_count': len(recent_optimizations),
                'last_optimization': recent_optimizations[0].created_at.isoformat() if recent_optimizations else None
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"获取用户{user_id}优化统计失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取统计信息失败: {str(e)}'}), 500

@prompt_optimization_bp.route('/patterns', methods=['GET'])
@jwt_required()
def get_analysis_patterns():
    """获取分析模式"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # 获取请求参数
        user_id = request.args.get('user_id', type=int)
        document_type = request.args.get('document_type')
        
        # 检查权限
        if user_id and user_id != current_user_id and user.role != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        target_user_id = user_id or current_user_id
        
        # 获取用户分析模式
        patterns = UserAnalysisPattern.get_user_patterns(target_user_id, document_type)
        
        # 获取全局错误模式（管理员才能看到）
        global_patterns = []
        if user.role == 'admin':
            global_patterns = historical_analyzer.get_global_error_patterns(document_type, 30)
        
        response_data = {
            'success': True,
            'user_id': target_user_id,
            'document_type': document_type,
            'user_patterns': [pattern.to_dict() for pattern in patterns],
            'global_patterns': global_patterns,
            'pattern_count': len(patterns),
            'recommendations': []
        }
        
        # 生成模式建议
        if patterns:
            low_accuracy_patterns = [p for p in patterns if p.accuracy_rate and p.accuracy_rate < 0.7]
            high_error_patterns = [p for p in patterns if p.error_frequency and p.error_frequency > 5]
            
            recommendations = []
            if low_accuracy_patterns:
                field_names = [p.field_name for p in low_accuracy_patterns[:3]]
                recommendations.append(f"重点关注准确率较低的字段: {', '.join(field_names)}")
            
            if high_error_patterns:
                field_names = [p.field_name for p in high_error_patterns[:3]]
                recommendations.append(f"需要加强错误预防的字段: {', '.join(field_names)}")
            
            response_data['recommendations'] = recommendations
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"获取分析模式失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取分析模式失败: {str(e)}'}), 500

@prompt_optimization_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_optimized_prompt():
    """生成优化的提示词"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
        
        # 获取参数
        document_type = data.get('document_type')
        context = data.get('context', {})
        force_regenerate = data.get('force_regenerate', False)
        
        # 生成优化提示词
        optimization_result = optimization_engine.generate_optimized_prompt(
            current_user_id, document_type, context
        )
        
        response_data = {
            'success': True,
            'optimization_result': optimization_result,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"生成优化提示词失败: {str(e)}")
        return jsonify({'success': False, 'message': f'生成优化提示词失败: {str(e)}'}), 500

@prompt_optimization_bp.route('/templates', methods=['GET'])
@jwt_required()
def get_prompt_templates():
    """获取提示词模板列表"""
    try:
        # 获取请求参数
        document_type = request.args.get('document_type')
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        
        # 构建查询
        query = PromptTemplate.query
        
        if not include_inactive:
            query = query.filter_by(is_active=True)
        
        if document_type:
            query = query.filter(PromptTemplate.document_types.contains([document_type]))
        
        templates = query.order_by(
            PromptTemplate.priority.desc(),
            PromptTemplate.success_rate.desc().nullslast(),
            PromptTemplate.usage_count.desc()
        ).all()
        
        response_data = {
            'success': True,
            'templates': [template.to_dict() for template in templates],
            'total_count': len(templates),
            'filter_applied': {
                'document_type': document_type,
                'include_inactive': include_inactive
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"获取模板列表失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取模板列表失败: {str(e)}'}), 500

@prompt_optimization_bp.route('/templates', methods=['POST'])
@jwt_required()
def create_prompt_template():
    """创建新的提示词模板"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # 只有管理员可以创建模板
        if user.role != 'admin':
            return jsonify({'success': False, 'message': '只有管理员可以创建模板'}), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
        
        # 验证必填字段
        required_fields = ['template_name', 'base_prompt']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field}是必填字段'}), 400
        
        # 生成模板ID
        template_id = f"custom_{int(datetime.utcnow().timestamp())}"
        
        # 创建模板
        template = PromptTemplate()
        template.template_id = template_id
        template.template_name = data['template_name']
        template.description = data.get('description', '')
        template.version = data.get('version', '1.0')
        template.document_types = data.get('document_types', [])
        template.target_fields = data.get('target_fields', [])
        template.base_prompt = data['base_prompt']
        template.optimization_rules = data.get('optimization_rules', [])
        template.dynamic_segments = data.get('dynamic_segments', {})
        template.is_active = data.get('is_active', True)
        template.priority = data.get('priority', 0)
        template.created_by = current_user_id
        template.save()
        
        response_data = {
            'success': True,
            'template': template.to_dict(),
            'message': '模板创建成功'
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"创建模板失败: {str(e)}")
        return jsonify({'success': False, 'message': f'创建模板失败: {str(e)}'}), 500

@prompt_optimization_bp.route('/feedback', methods=['POST'])
@jwt_required()
def submit_feedback():
    """提交分析反馈"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
        
        # 获取必要参数
        analysis_record_id = data.get('analysis_record_id')
        if not analysis_record_id:
            return jsonify({'success': False, 'message': '分析记录ID是必填的'}), 400
        
        # 验证分析记录所有权
        record = AIAnalysisRecord.query.get(analysis_record_id)
        if not record:
            return jsonify({'success': False, 'message': '分析记录不存在'}), 404
        
        if record.user_id != current_user_id:
            return jsonify({'success': False, 'message': '只能对自己的分析记录提供反馈'}), 403
        
        # 提取反馈数据
        user_modifications = data.get('user_modifications')
        user_rating = data.get('user_rating')
        comments = data.get('comments')
        
        # 处理反馈
        feedback_result = feedback_system.process_analysis_feedback(
            current_user_id, analysis_record_id, user_modifications, user_rating, comments
        )
        
        response_data = {
            'success': True,
            'feedback_result': feedback_result,
            'message': '反馈提交成功'
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"提交反馈失败: {str(e)}")
        return jsonify({'success': False, 'message': f'提交反馈失败: {str(e)}'}), 500

@prompt_optimization_bp.route('/ab-tests', methods=['GET'])
@jwt_required()
def get_ab_tests():
    """获取A/B测试结果"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # 只有管理员可以查看所有A/B测试
        if user.role != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        # 获取请求参数
        status = request.args.get('status')  # running, completed, stopped
        document_type = request.args.get('document_type')
        
        # 构建查询
        query = PromptABTest.query
        
        if status:
            query = query.filter_by(status=status)
        
        if document_type:
            query = query.filter(PromptABTest.document_types.contains([document_type]))
        
        tests = query.order_by(PromptABTest.created_at.desc()).all()
        
        response_data = {
            'success': True,
            'ab_tests': [test.to_dict() for test in tests],
            'total_count': len(tests),
            'filter_applied': {
                'status': status,
                'document_type': document_type
            },
            'summary': {
                'running_tests': len([t for t in tests if t.status == 'running']),
                'completed_tests': len([t for t in tests if t.status == 'completed']),
                'significant_results': len([t for t in tests if t.is_significant])
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"获取A/B测试失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取A/B测试失败: {str(e)}'}), 500

@prompt_optimization_bp.route('/ab-tests', methods=['POST'])
@jwt_required()
def create_ab_test():
    """创建A/B测试"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # 只有管理员可以创建A/B测试
        if user.role != 'admin':
            return jsonify({'success': False, 'message': '只有管理员可以创建A/B测试'}), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
        
        # 验证必填字段
        required_fields = ['test_name', 'prompt_a', 'prompt_b']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field}是必填字段'}), 400
        
        # 创建A/B测试
        ab_test = optimization_engine.create_ab_test(
            test_name=data['test_name'],
            prompt_a=data['prompt_a'],
            prompt_b=data['prompt_b'],
            target_users=data.get('target_users'),
            document_types=data.get('document_types'),
            test_ratio=data.get('test_ratio', 0.5)
        )
        
        # 设置测试参数
        if data.get('min_sample_size'):
            ab_test.min_sample_size = data['min_sample_size']
        if data.get('max_duration_days'):
            ab_test.max_duration_days = data['max_duration_days']
        if data.get('description'):
            ab_test.description = data['description']
        
        ab_test.created_by = current_user_id
        ab_test.save()
        
        response_data = {
            'success': True,
            'ab_test': ab_test.to_dict(),
            'message': 'A/B测试创建成功'
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"创建A/B测试失败: {str(e)}")
        return jsonify({'success': False, 'message': f'创建A/B测试失败: {str(e)}'}), 500

@prompt_optimization_bp.route('/learning-insights', methods=['GET'])
@jwt_required()
def get_learning_insights():
    """获取学习洞察"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # 获取请求参数
        user_id = request.args.get('user_id', type=int)
        days = int(request.args.get('days', 30))
        
        # 检查权限
        if user_id and user_id != current_user_id and user.role != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        target_user_id = user_id if user.role == 'admin' and user_id else current_user_id
        
        # 获取学习洞察
        insights = feedback_system.get_learning_insights(target_user_id, days)
        
        response_data = {
            'success': True,
            'learning_insights': insights,
            'user_id': target_user_id,
            'analysis_period_days': days
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"获取学习洞察失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取学习洞察失败: {str(e)}'}), 500

@prompt_optimization_bp.route('/optimization/<int:optimization_id>/evaluate', methods=['POST'])
@jwt_required()
def evaluate_optimization(optimization_id):
    """评估优化效果"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # 获取优化记录
        optimization = PromptOptimizationHistory.query.get(optimization_id)
        if not optimization:
            return jsonify({'success': False, 'message': '优化记录不存在'}), 404
        
        # 检查权限：用户只能评估自己的优化或管理员可以评估所有
        if optimization.user_id != current_user_id and user.role != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        # 评估优化效果
        evaluation_result = feedback_system.evaluate_optimization_performance(optimization_id)
        
        response_data = {
            'success': True,
            'evaluation_result': evaluation_result,
            'message': '优化效果评估完成'
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"评估优化效果失败: {str(e)}")
        return jsonify({'success': False, 'message': f'评估优化效果失败: {str(e)}'}), 500

@prompt_optimization_bp.route('/continuous-learning', methods=['POST'])
@jwt_required()
def run_continuous_learning():
    """运行持续学习循环（管理员功能）"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # 只有管理员可以手动触发持续学习
        if user.role != 'admin':
            return jsonify({'success': False, 'message': '只有管理员可以运行持续学习'}), 403
        
        # 运行持续学习循环
        cycle_result = feedback_system.run_continuous_learning_cycle()
        
        response_data = {
            'success': True,
            'cycle_result': cycle_result,
            'message': '持续学习循环执行完成'
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"持续学习循环失败: {str(e)}")
        return jsonify({'success': False, 'message': f'持续学习循环失败: {str(e)}'}), 500

@prompt_optimization_bp.route('/system-stats', methods=['GET'])
@jwt_required()
def get_system_stats():
    """获取系统级优化统计（管理员功能）"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # 只有管理员可以查看系统统计
        if user.role != 'admin':
            return jsonify({'success': False, 'message': '只有管理员可以查看系统统计'}), 403
        
        # 获取各种统计数据
        total_optimizations = PromptOptimizationHistory.query.count()
        total_templates = PromptTemplate.query.count()
        active_templates = PromptTemplate.query.filter_by(is_active=True).count()
        total_ab_tests = PromptABTest.query.count()
        running_ab_tests = PromptABTest.query.filter_by(status='running').count()
        total_patterns = UserAnalysisPattern.query.count()
        
        # 计算平均改进分数
        optimizations_with_score = PromptOptimizationHistory.query.filter(
            PromptOptimizationHistory.improvement_score.isnot(None)
        ).all()
        
        avg_improvement = 0.0
        if optimizations_with_score:
            avg_improvement = sum(opt.improvement_score for opt in optimizations_with_score) / len(optimizations_with_score)
        
        # 按优化类型统计
        optimization_types = {}
        for opt in PromptOptimizationHistory.query.all():
            opt_type = opt.optimization_type.value
            optimization_types[opt_type] = optimization_types.get(opt_type, 0) + 1
        
        response_data = {
            'success': True,
            'system_stats': {
                'total_optimizations': total_optimizations,
                'total_templates': total_templates,
                'active_templates': active_templates,
                'total_ab_tests': total_ab_tests,
                'running_ab_tests': running_ab_tests,
                'total_user_patterns': total_patterns,
                'avg_improvement_score': avg_improvement,
                'optimization_types': optimization_types,
                'system_health': 'healthy' if running_ab_tests > 0 and avg_improvement > 0.02 else 'normal'
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"获取系统统计失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取系统统计失败: {str(e)}'}), 500

# 错误处理
@prompt_optimization_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'success': False, 'message': '请求参数错误'}), 400

@prompt_optimization_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({'success': False, 'message': '未授权访问'}), 401

@prompt_optimization_bp.errorhandler(403)
def forbidden(error):
    return jsonify({'success': False, 'message': '权限不足'}), 403

@prompt_optimization_bp.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'message': '资源不存在'}), 404

@prompt_optimization_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'message': '服务器内部错误'}), 500