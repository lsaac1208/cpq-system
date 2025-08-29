# -*- coding: utf-8 -*-
"""
AI分析路由
提供AI文档分析和产品信息提取的API端点
"""
import os
import logging
import time
import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError, validate

from src.models import db, Product, AIAnalysisRecord
from src.utils.decorators import require_role, require_auth, get_current_user
from src.services.ai_analyzer import AIAnalyzer
from src.middleware.performance_monitor import performance_monitor, monitor_performance
from src.middleware.ai_service_manager import ai_service_manager, RequestContext

logger = logging.getLogger(__name__)
ai_analysis_bp = Blueprint('ai_analysis', __name__)

# 初始化AI分析器
ai_analyzer = AIAnalyzer()

def safe_string_conversion(value, default=''):
    """
    安全地将任意值转换为字符串
    
    Args:
        value: 待转换的值
        default: 转换失败时的默认值
        
    Returns:
        str: 转换后的字符串
    """
    try:
        if value is None:
            return default
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float, bool)):
            return str(value)
        # 对于复杂对象，尝试转换但限制长度
        str_value = str(value)
        return str_value if len(str_value) < 1000 else default
    except Exception:
        return default

def validate_and_transform_product_data(product_data):
    """
    验证和转换产品数据，确保数据结构一致性 - 增强版本
    
    Args:
        product_data: 从AI分析或前端提交的产品数据
        
    Returns:
        dict: 验证和标准化后的产品数据
        
    Raises:
        ValueError: 数据验证失败时抛出
    """
    try:
        # 🔍 日志记录原始数据结构
        logger.info(f"🔧 开始验证产品数据，原始结构: {list(product_data.keys()) if isinstance(product_data, dict) else type(product_data)}")
        
        # 🛡️ 容错性增强：处理None和非dict输入
        if product_data is None:
            logger.warning("⚠️ 收到None产品数据，使用默认空结构")
            product_data = {}
        
        if not isinstance(product_data, dict):
            logger.error(f"❌ 产品数据类型错误: 期望dict，收到{type(product_data)}")
            raise ValueError(f"Expected dict, got {type(product_data)}. Received data: {repr(product_data)[:200]}")
        
        # ✅ 验证和标准化基础信息 - 增强容错性
        basic_info = product_data.get('basic_info')
        
        # 🛡️ 处理basic_info为None或非dict的情况
        if basic_info is None:
            logger.warning("⚠️ basic_info为None，创建默认结构")
            basic_info = {}
        elif not isinstance(basic_info, dict):
            logger.warning(f"⚠️ basic_info类型错误: 期望dict，收到{type(basic_info)}，重置为空dict")
            basic_info = {}
        
        # 🔧 标准化基础信息字段 - 增强安全处理
        normalized_basic_info = {
            'name': safe_string_conversion(basic_info.get('name', ''), '').strip(),
            'code': safe_string_conversion(basic_info.get('code', ''), '').strip(), 
            'category': safe_string_conversion(basic_info.get('category', ''), '').strip(),
            'description': safe_string_conversion(basic_info.get('description', ''), '').strip(),
            'base_price': 0.0,
            'is_active': bool(basic_info.get('is_active', True)),
            'is_configurable': bool(basic_info.get('is_configurable', False))
        }
        
        # 安全处理价格字段
        try:
            price_value = basic_info.get('base_price', 0)
            if isinstance(price_value, (int, float, str)):
                normalized_basic_info['base_price'] = float(str(price_value).replace(',', '')) if price_value else 0.0
        except (ValueError, TypeError) as e:
            logger.warning(f"⚠️ 价格字段转换失败，使用默认值0: {e}")
            normalized_basic_info['base_price'] = 0.0
        
        # 🔧 智能必填字段验证 - 提供自动修复建议
        validation_errors = []
        auto_fixes = {}
        
        if not normalized_basic_info['name']:
            validation_errors.append("Product name is required")
            # 🤖 尝试从其他字段推断产品名称
            if product_data.get('summary') and 'product:' in product_data.get('summary', '').lower():
                # 从摘要中提取产品名称
                import re
                match = re.search(r'product:\s*([^|]+)', product_data.get('summary', ''), re.IGNORECASE)
                if match:
                    auto_fixes['name'] = match.group(1).strip()
                    
        if not normalized_basic_info['code']:
            validation_errors.append("Product code is required")
            # 🤖 尝试生成产品代码
            if normalized_basic_info['name']:
                import hashlib, time
                name_hash = hashlib.md5(normalized_basic_info['name'].encode()).hexdigest()[:6]
                auto_fixes['code'] = f"AUTO_{name_hash}_{int(time.time() % 10000)}"
            else:
                auto_fixes['code'] = f"AUTO_{int(time.time())}"
                
        # 🔧 应用自动修复
        if auto_fixes:
            logger.info(f"🤖 应用自动数据修复: {auto_fixes}")
            normalized_basic_info.update(auto_fixes)
            # 重新验证
            validation_errors = [err for err in validation_errors if not any(field in err.lower() for field in auto_fixes.keys())]
            
        # 🚨 如果仍有验证错误，抛出异常
        if validation_errors:
            error_msg = "; ".join(validation_errors)
            logger.error(f"❌ 数据验证失败: {error_msg}")
            raise ValueError(f"Data validation failed: {error_msg}")
        
        # 🔧 标准化规格信息 - 增强容错和过滤
        specifications = product_data.get('specifications', {})
        normalized_specifications = {}
        
        # 🛡️ 确保specifications是dict类型
        if not isinstance(specifications, dict):
            logger.warning(f"⚠️ specifications类型错误: 期望dict，收到{type(specifications)}，重置为空dict")
            specifications = {}
        
        # 🧹 无效规格参数过滤模式
        invalid_patterns = [
            r'^h$',  # 单个字符"h"
            r'^[a-z]$',  # 单个字母
            r'^\d+$',  # 单纯数字
            r'hyperlink',  # 包含HYPERLINK
            r'^(EMBED|MERGEFORMAT|CERTIFICATE|PACKING|PAGE|TEST)$',  # Word格式标识
            r'^(Toc\d+|_Toc|_Ref)',  # 文档结构标识
            r'^\d+\s+(HYPERLINK|PAGE|EMBED)',  # 数字+文档格式
            r'^[\s\-_=]+$'  # 只有格式字符
        ]
        
        import re
        compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in invalid_patterns]
        
        if isinstance(specifications, dict):
            for spec_key, spec_value in specifications.items():
                if not spec_key or not spec_key.strip():
                    continue
                    
                # 🧹 检查是否为无效规格参数
                key_str = spec_key.strip()
                value_str = safe_string_conversion(spec_value if not isinstance(spec_value, dict) else spec_value.get('value', ''), '')
                combined_text = f"{key_str} {value_str}"
                
                # 跳过明显无效的参数
                is_invalid = any(pattern.search(combined_text) for pattern in compiled_patterns)
                if is_invalid:
                    logger.debug(f"🧹 过滤无效规格参数: '{key_str}' = '{value_str}'")
                    continue
                
                # 处理不同格式的规格值
                if isinstance(spec_value, dict):
                    # 如果是复杂对象，保持结构但确保必要字段
                    normalized_spec = {
                        'value': safe_string_conversion(spec_value.get('value', ''), ''),
                        'unit': safe_string_conversion(spec_value.get('unit', ''), ''),
                        'description': safe_string_conversion(spec_value.get('description', ''), '')
                    }
                    # 如果有数值字段，保留它
                    if 'numeric_value' in spec_value:
                        try:
                            normalized_spec['numeric_value'] = float(spec_value['numeric_value'])
                        except (ValueError, TypeError):
                            pass
                    normalized_specifications[key_str] = normalized_spec
                else:
                    # 简单值转换为标准格式
                    normalized_specifications[key_str] = {
                        'value': safe_string_conversion(spec_value, ''),
                        'unit': '',
                        'description': ''
                    }
        
        # 🔧 处理其他字段，确保安全性和类型正确性
        def safe_list_conversion(value, field_name):
            """安全地转换为列表类型"""
            if value is None:
                return []
            if isinstance(value, list):
                return value
            logger.warning(f"⚠️ {field_name}类型错误: 期望list，收到{type(value)}，重置为空list")
            return []
            
        def safe_dict_conversion(value, field_name):
            """安全地转换为字典类型"""
            if value is None:
                return {}
            if isinstance(value, dict):
                return value
            logger.warning(f"⚠️ {field_name}类型错误: 期望dict，收到{type(value)}，重置为空dict")
            return {}
        
        validated_data = {
            'basic_info': normalized_basic_info,
            'specifications': normalized_specifications,
            'configuration_schema': safe_dict_conversion(product_data.get('configuration_schema'), 'configuration_schema'),
            'detailed_description': safe_string_conversion(product_data.get('detailed_description', ''), ''),
            'features': safe_list_conversion(product_data.get('features'), 'features'),
            'application_scenarios': safe_list_conversion(product_data.get('application_scenarios'), 'application_scenarios'),
            'accessories': safe_list_conversion(product_data.get('accessories'), 'accessories'),
            'certificates': safe_list_conversion(product_data.get('certificates'), 'certificates'),
            'support_info': safe_dict_conversion(product_data.get('support_info'), 'support_info')
        }
        
        # 📊 日志记录验证结果
        logger.info(f"✅ 数据验证成功: {normalized_basic_info['name']} ({normalized_basic_info['code']})")
        logger.info(f"📊 规格参数数量: {len(normalized_specifications)}")
        
        return validated_data
        
    except Exception as e:
        # 🔍 增强错误处理和调试信息
        error_type = type(e).__name__
        error_msg = str(e)
        
        # 📊 生成详细的调试信息
        debug_info = {
            'error_type': error_type,
            'error_message': error_msg,
            'data_type': type(product_data).__name__,
            'data_keys': list(product_data.keys()) if isinstance(product_data, dict) else 'N/A',
            'basic_info_present': 'basic_info' in product_data if isinstance(product_data, dict) else False,
            'basic_info_type': type(product_data.get('basic_info')).__name__ if isinstance(product_data, dict) else 'N/A'
        }
        
        logger.error(f"❌ 产品数据验证失败 [{error_type}]: {error_msg}")
        logger.error(f"🔍 调试信息: {debug_info}")
        
        # 🔒 安全地记录部分数据结构（避免敏感信息泄露）
        if isinstance(product_data, dict):
            safe_sample = {k: f"<{type(v).__name__}>" for k, v in list(product_data.items())[:5]}
            logger.error(f"📄 数据结构示例 (前5个字段): {safe_sample}")
        else:
            logger.error(f"📄 数据内容: {repr(product_data)[:200]}...")
            
        # 🎯 提供用户友好的错误信息
        if "name is required" in error_msg.lower() or "code is required" in error_msg.lower():
            user_friendly_msg = "产品基础信息不完整，请确保包含产品名称和产品代码"
        elif "basic_info must be a dictionary" in error_msg:
            user_friendly_msg = "产品基础信息格式错误，期望字典格式"
        elif "Expected dict" in error_msg:
            user_friendly_msg = "产品数据格式错误，期望JSON对象格式"
        else:
            user_friendly_msg = f"数据验证失败: {error_msg}"
            
        raise ValueError(user_friendly_msg)

# Schemas for request validation
class ProductCreateFromAISchema(Schema):
    """从AI分析结果创建产品的请求模式"""
    analysis_id = fields.Int(required=True, validate=validate.Range(min=1))
    product_data = fields.Dict(required=True)
    user_modifications = fields.Dict(missing={})

@ai_analysis_bp.route('/supported-formats', methods=['GET'])
@jwt_required()
@require_auth
def get_supported_formats():
    """获取支持的文档格式信息"""
    try:
        formats_info = ai_analyzer.get_supported_formats()
        
        return jsonify({
            'success': True,
            'formats': formats_info
        })
        
    except Exception as e:
        logger.error(f"Error getting supported formats: {str(e)}")
        return jsonify({'error': 'Failed to get format information'}), 500

@ai_analysis_bp.route('/analyze-document', methods=['POST'])
@jwt_required()
@require_role('engineer', 'admin', 'manager')
@monitor_performance
def analyze_document():
    """分析产品文档，提取产品信息 - 增强版本"""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # 检查是否有文件上传
        if 'document' not in request.files:
            return jsonify({'error': 'No document file provided'}), 400
        
        file = request.files['document']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # 获取当前用户
        current_user_id = get_jwt_identity()
        
        # 获取文件信息
        file_size = len(file.read())
        file.seek(0)  # 重置文件指针
        file_type = file.content_type or 'unknown'
        
        logger.info(f"🚀 AI分析请求 {request_id}: 文件={file.filename}, 大小={file_size}bytes, 用户={current_user_id}")
        
        # 📊 检查服务状态和队列
        queue_status = ai_service_manager.get_queue_status()
        service_status = queue_status['service_status']
        
        if service_status == 'unavailable':
            logger.error(f"❌ AI服务不可用，拒绝请求 {request_id}")
            return jsonify({
                'success': False,
                'error': 'AI分析服务暂时不可用，请稍后重试',
                'service_status': service_status,
                'queue_info': {
                    'queue_size': queue_status['queue_size'],
                    'processing_count': queue_status['processing_count']
                }
            }), 503
        
        # 🔧 创建请求上下文
        context = RequestContext(
            request_id=request_id,
            user_id=current_user_id,
            priority=8 if file_size < 1024*1024 else 6,  # 小文件高优先级
            timeout=180.0,  # 3分钟超时
            created_at=start_time,
            file_size=file_size,
            file_type=file_type
        )
        
        # 如果服务降级，提供快速响应选项
        if service_status == 'degraded':
            logger.warning(f"⚠️ AI服务降级模式，请求 {request_id} 将使用简化处理")
            # 可以选择直接处理或排队
            if queue_status['queue_size'] > 20:
                return jsonify({
                    'success': False,
                    'error': 'AI分析服务负载较高，建议稍后重试',
                    'service_status': service_status,
                    'estimated_wait_time': queue_status['queue_size'] * 30,  # 估算等待时间
                    'recommendations': ai_service_manager.get_service_recommendations()
                }), 429
        
        # 🎯 提交到AI服务管理器队列
        queued = ai_service_manager.submit_analysis_request(context)
        if not queued:
            logger.error(f"❌ 请求 {request_id} 无法加入处理队列")
            return jsonify({
                'success': False,
                'error': 'AI分析队列已满，请稍后重试',
                'queue_info': queue_status,
                'recommendations': ai_service_manager.get_service_recommendations()
            }), 429
        
        # ⚡ 直接处理（在实际实现中，这里应该是异步处理）
        # 为了保持API兼容性，我们仍然同步处理
        logger.info(f"🔄 开始处理AI分析请求 {request_id}")
        
        # 使用AI分析器处理文档（包含用户ID以获得个性化分析）
        analysis_result = ai_analyzer.analyze_product_document(file, user_id=current_user_id)
        
        # 📝 保存分析记录到数据库
        analysis_record = AIAnalysisRecord.create_from_analysis(
            analysis_result,
            user_id=current_user_id
        )
        analysis_record.save()
        
        # ✅ 验证分析结果
        validation = ai_analyzer.validate_analysis_result(analysis_result)
        
        # 📋 生成分析摘要
        summary = ai_analyzer.generate_analysis_summary(analysis_result)
        
        # 📊 记录性能指标
        processing_time = time.time() - start_time
        performance_monitor.record_request(
            endpoint='/ai-analysis/analyze-document',
            method='POST',
            duration=processing_time,
            status_code=200 if analysis_result.get('success') else 400
        )
        
        # 📤 构建响应
        response_data = {
            'success': analysis_result.get('success', False),
            'request_id': request_id,
            'analysis_id': analysis_record.id,
            'document_info': analysis_result.get('document_info', {}),
            'extracted_data': analysis_result.get('extracted_data', {}),
            'confidence_scores': analysis_result.get('confidence_scores', {}),
            'personalized_hints': analysis_result.get('personalized_hints', []),
            'predicted_modifications': analysis_result.get('predicted_modifications', {}),
            'validation': validation,
            'summary': summary,
            'text_preview': analysis_result.get('text_preview', ''),
            'analysis_timestamp': analysis_result.get('analysis_timestamp'),
            'processing_time': round(processing_time, 2),
            'service_status': service_status,
            'queue_info': {
                'queue_size': ai_service_manager.get_queue_status()['queue_size'],
                'processing_count': len(ai_service_manager.get_processing_requests())
            }
        }
        
        if not analysis_result.get('success'):
            response_data['error'] = analysis_result.get('error')
            logger.warning(f"⚠️ AI分析失败 {request_id}: {analysis_result.get('error')}")
            return jsonify(response_data), 400
        
        logger.info(f"✅ AI分析成功完成 {request_id}: 记录ID={analysis_record.id}, 耗时={processing_time:.2f}s")
        return jsonify(response_data), 200
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = str(e)
        
        # 📊 记录错误指标
        performance_monitor.record_request(
            endpoint='/ai-analysis/analyze-document',
            method='POST',
            duration=processing_time,
            status_code=500,
            error_msg=error_msg
        )
        
        logger.error(f"💥 AI分析异常 {request_id}: {error_msg}, 耗时={processing_time:.2f}s")
        
        return jsonify({
            'success': False,
            'request_id': request_id,
            'error': f'AI分析失败: {error_msg}',
            'processing_time': round(processing_time, 2),
            'service_status': ai_service_manager.get_queue_status()['service_status']
        }), 500

@ai_analysis_bp.route('/analysis/<int:analysis_id>', methods=['GET'])
@jwt_required()
@require_auth
def get_analysis_result(analysis_id):
    """获取指定分析记录的结果"""
    try:
        analysis_record = AIAnalysisRecord.query.get_or_404(analysis_id)
        
        return jsonify({
            'success': True,
            'analysis': analysis_record.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting analysis result {analysis_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_analysis_bp.route('/debug/<int:analysis_id>', methods=['GET'])
def debug_analysis_data(analysis_id):
    """🔧 调试端点 - 检查AI分析结果的原始数据结构"""
    try:
        analysis_record = AIAnalysisRecord.query.get_or_404(analysis_id)
        extracted_data = analysis_record.get_extracted_data()
        confidence_scores = analysis_record.get_confidence_scores()
        
        # 详细的数据结构检查
        debug_info = {
            'analysis_id': analysis_id,
            'record_found': True,
            'document_name': analysis_record.document_name,
            'analysis_summary': analysis_record.analysis_summary,
            'success': analysis_record.success,
            'has_extracted_data': bool(extracted_data),
            'extracted_data_type': type(extracted_data).__name__,
            'extracted_data_keys': list(extracted_data.keys()) if isinstance(extracted_data, dict) else 'Not a dict',
            'basic_info_debug': {},
            'confidence_info': confidence_scores,
            'raw_extracted_data': extracted_data
        }
        
        # 详细检查basic_info
        if isinstance(extracted_data, dict) and 'basic_info' in extracted_data:
            basic_info = extracted_data['basic_info']
            debug_info['basic_info_debug'] = {
                'type': type(basic_info).__name__,
                'keys': list(basic_info.keys()) if isinstance(basic_info, dict) else 'Not a dict',
                'name_value': repr(basic_info.get('name', 'KEY_MISSING')) if isinstance(basic_info, dict) else 'N/A',
                'code_value': repr(basic_info.get('code', 'KEY_MISSING')) if isinstance(basic_info, dict) else 'N/A',
                'category_value': repr(basic_info.get('category', 'KEY_MISSING')) if isinstance(basic_info, dict) else 'N/A',
                'description_value': repr(basic_info.get('description', 'KEY_MISSING'))[:100] + '...' if isinstance(basic_info, dict) else 'N/A',
                'full_basic_info': basic_info if isinstance(basic_info, dict) else str(basic_info)
            }
        
        logger.info(f"🔧 调试分析ID {analysis_id}: {debug_info}")
        return jsonify(debug_info)
        
    except Exception as e:
        logger.error(f"调试端点错误: {str(e)}")
        return jsonify({'error': str(e), 'analysis_id': analysis_id}), 500

@ai_analysis_bp.route('/analysis/<int:analysis_id>', methods=['PUT'])
@jwt_required()
@require_role('engineer', 'admin', 'manager')
def update_analysis_modifications(analysis_id):
    """更新分析记录的用户修正信息"""
    try:
        analysis_record = AIAnalysisRecord.query.get_or_404(analysis_id)
        
        request_data = request.get_json()
        if not request_data:
            return jsonify({'error': 'No data provided'}), 400
        
        # 更新用户修正记录
        if 'user_modifications' in request_data:
            analysis_record.set_user_modifications(request_data['user_modifications'])
        
        if 'final_data' in request_data:
            analysis_record.set_final_data(request_data['final_data'])
        
        analysis_record.save()
        
        return jsonify({
            'success': True,
            'message': 'Analysis modifications updated successfully',
            'analysis': analysis_record.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating analysis modifications {analysis_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_analysis_bp.route('/validate-data/<int:analysis_id>', methods=['GET'])
@jwt_required()
@require_auth
def validate_analysis_data(analysis_id):
    """
    验证分析数据的一致性和完整性
    """
    try:
        # 获取分析记录
        analysis_record = AIAnalysisRecord.query.get_or_404(analysis_id)
        extracted_data = analysis_record.get_extracted_data()
        
        # 执行数据验证
        validation_result = {
            'analysis_id': analysis_id,
            'validation_passed': False,
            'issues': [],
            'warnings': [],
            'data_structure': {},
            'suggestions': []
        }
        
        try:
            # 尝试验证数据结构
            validated_data = validate_and_transform_product_data(extracted_data)
            validation_result['validation_passed'] = True
            validation_result['data_structure'] = {
                'basic_info_fields': list(validated_data['basic_info'].keys()),
                'specifications_count': len(validated_data['specifications']),
                'features_count': len(validated_data['features']),
                'has_extended_data': bool(validated_data.get('detailed_description'))
            }
            
        except ValueError as e:
            validation_result['issues'].append(str(e))
            validation_result['suggestions'].append('请检查AI分析结果的数据格式是否正确')
        
        # 检查数据完整性
        if not extracted_data.get('basic_info', {}).get('name'):
            validation_result['warnings'].append('产品名称缺失')
        if not extracted_data.get('basic_info', {}).get('code'):
            validation_result['warnings'].append('产品编码缺失')
        if not extracted_data.get('specifications'):
            validation_result['warnings'].append('技术规格参数缺失')
            
        return jsonify(validation_result)
        
    except Exception as e:
        logger.error(f"数据验证失败: {str(e)}")
        return jsonify({'error': f'Validation failed: {str(e)}'}), 500

@ai_analysis_bp.route('/create-product', methods=['POST'])
@jwt_required()
@require_role('engineer', 'admin', 'manager')
def create_product_from_analysis():
    """基于AI分析结果创建产品"""
    try:
        # 验证请求数据
        schema = ProductCreateFromAISchema()
        request_data = schema.load(request.get_json())
        
        analysis_id = request_data['analysis_id']
        product_data = request_data['product_data']
        user_modifications = request_data['user_modifications']
        
        # 获取分析记录
        analysis_record = AIAnalysisRecord.query.get_or_404(analysis_id)
        
        # 检查是否已经创建过产品
        if analysis_record.created_product_id:
            return jsonify({
                'error': 'Product has already been created from this analysis',
                'existing_product_id': analysis_record.created_product_id
            }), 400
        
        # 🔧 数据验证和转换层
        try:
            validated_data = validate_and_transform_product_data(product_data)
            logger.info(f"✅ 产品数据验证通过: {validated_data.get('basic_info', {}).get('name', 'Unknown')}")
        except ValueError as e:
            logger.error(f"❌ 产品数据验证失败: {str(e)}")
            return jsonify({'error': f'Data validation failed: {str(e)}'}), 400
        
        # 验证并处理产品代码重复问题
        product_code = validated_data.get('basic_info', {}).get('code', '')
        if Product.query.filter_by(code=product_code).first():
            # 生成唯一的产品代码
            import time
            import hashlib
            timestamp = str(int(time.time()))
            original_code = product_code
            
            # 尝试不同的唯一化策略
            for i in range(1, 100):  # 最多尝试99次
                if i == 1:
                    # 第一次尝试：添加时间戳后缀
                    new_code = f"{original_code}_{timestamp[-4:]}"
                elif i <= 10:
                    # 2-10次：添加递增数字
                    new_code = f"{original_code}_{i:02d}"
                else:
                    # 11+次：使用哈希值确保唯一性
                    hash_input = f"{original_code}_{timestamp}_{i}"
                    hash_suffix = hashlib.md5(hash_input.encode()).hexdigest()[:6]
                    new_code = f"{original_code}_{hash_suffix}"
                
                if not Product.query.filter_by(code=new_code).first():
                    logger.info(f"🔧 产品代码冲突已解决: '{original_code}' → '{new_code}'")
                    validated_data['basic_info']['code'] = new_code
                    product_code = new_code
                    break
            else:
                # 如果所有尝试都失败，返回错误
                logger.error(f"❌ 无法生成唯一的产品代码，原始代码: {original_code}")
                return jsonify({
                    'error': f'Unable to generate unique product code. Original code "{original_code}" conflicts with existing products.'
                }), 400
        
        # 创建产品
        product = Product()
        
        # 设置基础信息 - 使用验证后的数据
        basic_info = validated_data.get('basic_info', {})
        product.name = basic_info.get('name', '')
        product.code = basic_info.get('code', '')
        product.description = basic_info.get('description', '')
        product.category = basic_info.get('category', '')
        product.base_price = basic_info.get('base_price', 0)
        product.is_active = basic_info.get('is_active', True)
        product.is_configurable = basic_info.get('is_configurable', False)
        
        # 设置规格信息 - 使用标准化后的格式
        specifications = validated_data.get('specifications', {})
        if specifications:
            product.set_specifications(specifications)
        
        # 设置配置架构
        configuration_schema = validated_data.get('configuration_schema', {})
        if configuration_schema:
            product.set_configuration_schema(configuration_schema)
        
        # 设置扩展信息 - 使用验证后的数据和新的模型方法
        if validated_data.get('detailed_description'):
            product.detailed_description = validated_data['detailed_description']
        if validated_data.get('application_scenarios'):
            product.set_application_scenarios(validated_data['application_scenarios'])
        if validated_data.get('features'):
            product.set_features(validated_data['features'])
        if validated_data.get('accessories'):
            product.set_accessories(validated_data['accessories'])
        if validated_data.get('certificates'):
            product.set_certificates(validated_data['certificates'])
        if validated_data.get('support_info'):
            product.set_support_info(validated_data['support_info'])
        
        # 保存产品
        product.save()
        
        # 更新分析记录 - 使用验证后的数据
        analysis_record.created_product_id = product.id
        analysis_record.set_user_modifications(user_modifications)
        analysis_record.set_final_data(validated_data)  # 保存验证后的数据
        analysis_record.save()
        
        # 📊 记录数据转换日志
        logger.info(f"✅ 产品创建成功: ID={product.id}, Name={product.name}, Code={product.code}")
        logger.info(f"📊 数据一致性检查 - 原始字段数: {len(product_data.keys())}, 验证后字段数: {len(validated_data.keys())}")
        
        # 触发学习机制（如果有用户修正）
        if user_modifications:
            try:
                learning_result = ai_analyzer.learn_from_user_modifications(
                    analysis_record_id=analysis_id,
                    original_data=analysis_record.get_extracted_data(),
                    final_data=product_data,
                    user_modifications=user_modifications
                )
                logger.info(f"Learning completed for analysis {analysis_id}: "
                           f"{learning_result.get('patterns_identified', 0)} patterns identified")
            except Exception as e:
                logger.error(f"Learning failed for analysis {analysis_id}: {str(e)}")
                # 学习失败不影响产品创建，只记录错误
        
        logger.info(f"Product created successfully from AI analysis {analysis_id}: {product.id}")
        
        return jsonify({
            'success': True,
            'message': 'Product created successfully from AI analysis',
            'product': product.to_dict(),
            'product_id': product.id,
            'product_detail_url': f'/products/{product.id}',
            'analysis_id': analysis_id
        }), 201
        
    except ValidationError as err:
        return jsonify({'error': 'Validation error', 'details': err.messages}), 400
    except Exception as e:
        logger.error(f"Error creating product from AI analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_analysis_bp.route('/history', methods=['GET'])
@jwt_required()
@require_auth
def get_analysis_history():
    """获取AI分析历史记录"""
    try:
        current_user_id = get_jwt_identity()
        
        # 查询参数
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 50)
        status = request.args.get('status')  # completed, failed
        
        # 构建查询
        query = AIAnalysisRecord.query
        
        # 用户过滤（普通用户只能看到自己的记录）
        current_user = get_current_user()
        if current_user and current_user.role not in ['admin', 'manager']:
            query = query.filter_by(user_id=current_user_id)
        
        # 状态过滤
        if status:
            query = query.filter_by(status=status)
        
        # 分页
        records = query.order_by(AIAnalysisRecord.created_at.desc())\
                      .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'records': [record.to_dict() for record in records.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': records.total,
                'pages': records.pages
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting analysis history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_analysis_bp.route('/statistics', methods=['GET'])
@jwt_required()
@require_role('admin', 'manager')
def get_analysis_statistics():
    """获取AI分析统计信息"""
    try:
        days = int(request.args.get('days', 30))
        
        # 计算统计数据
        success_rate = AIAnalysisRecord.get_success_rate(days)
        avg_confidence = AIAnalysisRecord.get_average_confidence(days)
        
        # 获取总记录数
        total_records = AIAnalysisRecord.query.count()
        successful_records = AIAnalysisRecord.query.filter_by(success=True).count()
        
        # 获取最近的分析记录
        recent_records = AIAnalysisRecord.query\
                                        .order_by(AIAnalysisRecord.created_at.desc())\
                                        .limit(5).all()
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_analyses': total_records,
                'successful_analyses': successful_records,
                'success_rate': success_rate,
                'average_confidence': avg_confidence,
                'period_days': days
            },
            'recent_analyses': [record.to_dict() for record in recent_records]
        })
        
    except Exception as e:
        logger.error(f"Error getting analysis statistics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_analysis_bp.route('/analysis/<int:analysis_id>', methods=['DELETE'])
@jwt_required()
@require_role('admin', 'manager')
def delete_analysis_record(analysis_id):
    """删除分析记录"""
    try:
        analysis_record = AIAnalysisRecord.query.get_or_404(analysis_id)
        
        # 检查是否有关联的产品
        if analysis_record.created_product_id:
            return jsonify({
                'error': 'Cannot delete analysis record that has created a product'
            }), 400
        
        analysis_record.delete()
        
        return jsonify({
            'success': True,
            'message': 'Analysis record deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting analysis record {analysis_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_analysis_bp.route('/learning/statistics', methods=['GET'])
@jwt_required()
@require_role('admin', 'manager')
def get_learning_statistics():
    """获取学习统计信息"""
    try:
        days = int(request.args.get('days', 30))
        
        # 获取学习统计
        stats = ai_analyzer.get_learning_statistics(days=days)
        
        return jsonify({
            'success': True,
            'statistics': stats,
            'period_days': days
        })
        
    except Exception as e:
        logger.error(f"Error getting learning statistics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_analysis_bp.route('/learning/hints/<int:user_id>', methods=['POST'])
@jwt_required()
@require_auth
def get_personalized_hints(user_id):
    """获取用户个性化提示"""
    try:
        # 验证权限（用户只能查看自己的提示，管理员可以查看所有）
        current_user_id = get_jwt_identity()
        current_user = get_current_user()
        
        if current_user.role not in ['admin', 'manager'] and current_user_id != user_id:
            return jsonify({'error': 'Unauthorized access to user hints'}), 403
        
        request_data = request.get_json() or {}
        document_type = request_data.get('document_type', 'unknown')
        extracted_data = request_data.get('extracted_data', {})
        
        # 获取个性化提示
        hints = ai_analyzer.get_personalized_analysis_hints(
            user_id=user_id,
            document_type=document_type,
            extracted_data=extracted_data
        )
        
        return jsonify({
            'success': True,
            'hints': hints
        })
        
    except Exception as e:
        logger.error(f"Error getting personalized hints: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_analysis_bp.route('/learning/feedback', methods=['POST'])
@jwt_required()
@require_auth
def submit_learning_feedback():
    """提交学习反馈"""
    try:
        from src.models.learning_pattern import LearningFeedback
        
        current_user_id = get_jwt_identity()
        request_data = request.get_json()
        
        # 验证请求数据
        required_fields = ['analysis_record_id', 'field_path', 'user_rating']
        for field in required_fields:
            if field not in request_data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # 创建反馈记录
        feedback = LearningFeedback()
        feedback.analysis_record_id = request_data['analysis_record_id']
        feedback.user_id = current_user_id
        feedback.field_path = request_data['field_path']
        feedback.original_confidence = request_data.get('original_confidence')
        feedback.user_rating = request_data['user_rating']
        feedback.is_accurate = request_data.get('is_accurate', True)
        feedback.improvement_suggestion = request_data.get('improvement_suggestion', '')
        feedback.feedback_type = request_data.get('feedback_type', 'accuracy')
        
        feedback.save()
        
        return jsonify({
            'success': True,
            'message': 'Feedback submitted successfully',
            'feedback_id': feedback.id
        })
        
    except Exception as e:
        logger.error(f"Error submitting learning feedback: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_analysis_bp.route('/learning/optimization/<document_type>', methods=['GET'])
@jwt_required()
@require_role('engineer', 'admin', 'manager')
def get_analysis_optimization(document_type):
    """获取文档类型的分析优化配置"""
    try:
        category = request.args.get('category')
        
        # 获取优化配置
        optimization = ai_analyzer.optimize_analysis_for_document_type(
            document_type=document_type,
            category=category
        )
        
        return jsonify({
            'success': True,
            'optimization': optimization,
            'document_type': document_type,
            'category': category
        })
        
    except Exception as e:
        logger.error(f"Error getting analysis optimization: {str(e)}")
        return jsonify({'error': str(e)}), 500