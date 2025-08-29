"""
产品搜索API端点
提供普通搜索、批量搜索、搜索建议等功能
"""

import io
import csv
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError, validate
from werkzeug.utils import secure_filename
from src.models import db
from src.services.product_search import ProductSearchService, BatchSearchService
from src.utils.decorators import require_auth, get_current_user

logger = logging.getLogger(__name__)
search_bp = Blueprint('search', __name__)

# 初始化服务
search_service = ProductSearchService()
batch_search_service = BatchSearchService()

# Schema定义
class SearchSchema(Schema):
    """搜索请求Schema"""
    query = fields.Str(validate=validate.Length(max=500))
    filters = fields.Dict(load_default={})
    sort = fields.Str(validate=validate.OneOf([
        'relevance', 'name', 'price', 'price_desc', 'newest', 'oldest'
    ]), load_default='relevance')
    page = fields.Int(validate=validate.Range(min=1), load_default=1)
    per_page = fields.Int(validate=validate.Range(min=1, max=100), load_default=20)

class BatchSearchSchema(Schema):
    """批量搜索请求Schema"""
    queries = fields.List(fields.Str(), required=True, validate=validate.Length(min=1, max=1000))
    options = fields.Dict(load_default={})

class SearchFiltersSchema(Schema):
    """搜索过滤器Schema"""
    category = fields.Str(validate=validate.Length(max=100))
    price_min = fields.Decimal(validate=validate.Range(min=0))
    price_max = fields.Decimal(validate=validate.Range(min=0))
    is_configurable = fields.Bool()
    is_active = fields.Bool(load_default=True)
    specs = fields.Dict()


@search_bp.route('/products', methods=['GET'])
@jwt_required()
@require_auth
def search_products():
    """
    搜索产品
    ---
    tags:
      - Search
    parameters:
      - name: query
        in: query
        type: string
        description: 搜索查询字符串
        maxLength: 500
      - name: category
        in: query
        type: string
        description: 产品分类过滤
      - name: price_min
        in: query
        type: number
        description: 最低价格
      - name: price_max
        in: query
        type: number
        description: 最高价格
      - name: sort
        in: query
        type: string
        enum: [relevance, name, price, price_desc, newest, oldest]
        description: 排序方式
        default: relevance
      - name: page
        in: query
        type: integer
        description: 页码
        default: 1
        minimum: 1
      - name: per_page
        in: query
        type: integer
        description: 每页数量
        default: 20
        minimum: 1
        maximum: 100
    responses:
      200:
        description: 搜索成功
        schema:
          type: object
          properties:
            products:
              type: array
              items:
                type: object
            pagination:
              type: object
            search_info:
              type: object
      400:
        description: 请求参数错误
      500:
        description: 服务器错误
    """
    try:
        # 解析查询参数
        query = request.args.get('query', '').strip()
        
        # 构建过滤器
        filters = {}
        if request.args.get('category'):
            filters['category'] = request.args.get('category')
        if request.args.get('price_min'):
            filters['price_min'] = float(request.args.get('price_min'))
        if request.args.get('price_max'):
            filters['price_max'] = float(request.args.get('price_max'))
        if request.args.get('is_configurable'):
            filters['is_configurable'] = request.args.get('is_configurable').lower() == 'true'
        
        # 搜索参数
        sort = request.args.get('sort', 'relevance')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # 验证参数
        if page < 1:
            return jsonify({'error': '页码必须大于0'}), 400
        if per_page < 1 or per_page > 100:
            return jsonify({'error': '每页数量必须在1-100之间'}), 400
        
        # 获取当前用户
        current_user = get_current_user()
        user_id = current_user.id if current_user else None
        
        # 执行搜索
        result = search_service.search(
            query=query,
            filters=filters,
            sort=sort,
            page=page,
            per_page=per_page,
            user_id=user_id
        )
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except ValueError as e:
        return jsonify({'error': f'参数错误: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"产品搜索失败: {str(e)}")
        return jsonify({'error': '搜索失败，请稍后重试'}), 500


@search_bp.route('/products/suggestions', methods=['GET'])
@jwt_required()
@require_auth
def get_search_suggestions():
    """
    获取搜索建议
    ---
    tags:
      - Search
    parameters:
      - name: query
        in: query
        type: string
        required: true
        description: 搜索查询字符串
        minLength: 2
      - name: limit
        in: query
        type: integer
        description: 建议数量限制
        default: 10
        minimum: 1
        maximum: 20
    responses:
      200:
        description: 获取建议成功
        schema:
          type: object
          properties:
            suggestions:
              type: array
              items:
                type: object
    """
    try:
        query = request.args.get('query', '').strip()
        limit = int(request.args.get('limit', 10))
        
        if len(query) < 2:
            return jsonify({
                'success': True,
                'suggestions': []
            })
        
        if limit < 1 or limit > 20:
            limit = 10
        
        suggestions = search_service.get_search_suggestions(query, limit)
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
        
    except Exception as e:
        logger.error(f"获取搜索建议失败: {str(e)}")
        return jsonify({'error': '获取建议失败'}), 500


@search_bp.route('/products/hot', methods=['GET'])
@jwt_required()
@require_auth
def get_hot_searches():
    """
    获取热门搜索
    ---
    tags:
      - Search
    parameters:
      - name: limit
        in: query
        type: integer
        description: 返回数量限制
        default: 10
        minimum: 1
        maximum: 50
      - name: days
        in: query
        type: integer
        description: 统计天数
        default: 7
        minimum: 1
        maximum: 90
    responses:
      200:
        description: 获取热门搜索成功
        schema:
          type: object
          properties:
            hot_searches:
              type: array
              items:
                type: object
    """
    try:
        limit = int(request.args.get('limit', 10))
        days = int(request.args.get('days', 7))
        
        if limit < 1 or limit > 50:
            limit = 10
        if days < 1 or days > 90:
            days = 7
        
        hot_searches = search_service.get_hot_searches(limit, days)
        
        return jsonify({
            'success': True,
            'hot_searches': hot_searches,
            'period': f'最近{days}天'
        })
        
    except Exception as e:
        logger.error(f"获取热门搜索失败: {str(e)}")
        return jsonify({'error': '获取热门搜索失败'}), 500


@search_bp.route('/products/batch', methods=['POST'])
@jwt_required()
@require_auth
def batch_search_products():
    """
    批量搜索产品
    ---
    tags:
      - Search
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            queries:
              type: array
              items:
                type: string
              description: 搜索查询列表
              minItems: 1
              maxItems: 1000
            options:
              type: object
              properties:
                per_query:
                  type: integer
                  description: 每个查询返回的结果数
                  default: 5
                  minimum: 1
                  maximum: 20
                filters:
                  type: object
                  description: 通用过滤条件
    responses:
      200:
        description: 批量搜索成功
        schema:
          type: object
          properties:
            results:
              type: array
              items:
                type: object
            summary:
              type: object
      400:
        description: 请求参数错误
      500:
        description: 服务器错误
    """
    try:
        # 验证请求数据
        schema = BatchSearchSchema()
        data = schema.load(request.json)
        
        queries = data['queries']
        options = data.get('options', {})
        
        # 参数验证
        if len(queries) > 1000:
            return jsonify({'error': '批量搜索数量不能超过1000'}), 400
        
        # 清理空查询
        queries = [q.strip() for q in queries if q and q.strip()]
        if not queries:
            return jsonify({'error': '没有有效的搜索查询'}), 400
        
        # 获取当前用户
        current_user = get_current_user()
        user_id = current_user.id if current_user else None
        
        # 执行批量搜索
        results = batch_search_service.batch_search(
            queries=queries,
            options=options,
            user_id=user_id
        )
        
        # 统计结果
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        total_products_found = sum(r.get('total_found', 0) for r in results if r['success'])
        
        return jsonify({
            'success': True,
            'results': results,
            'summary': {
                'total_queries': len(results),
                'successful': successful,
                'failed': failed,
                'total_products_found': total_products_found
            }
        })
        
    except ValidationError as err:
        return jsonify({'error': '请求参数错误', 'details': err.messages}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"批量搜索失败: {str(e)}")
        return jsonify({'error': '批量搜索失败，请稍后重试'}), 500


@search_bp.route('/products/batch/upload', methods=['POST'])
@jwt_required()
@require_auth
def batch_search_upload():
    """
    上传文件执行批量搜索
    ---
    tags:
      - Search
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: CSV文件（第一列为搜索词）
      - name: query_column
        in: formData
        type: string
        description: 搜索词列名
        default: query
      - name: per_query
        in: formData
        type: integer
        description: 每个查询返回的结果数
        default: 5
        minimum: 1
        maximum: 20
    responses:
      200:
        description: 文件上传和搜索成功
        schema:
          type: object
          properties:
            results:
              type: array
            summary:
              type: object
      400:
        description: 文件格式错误或参数错误
      500:
        description: 服务器错误
    """
    try:
        # 检查文件
        if 'file' not in request.files:
            return jsonify({'error': '请选择要上传的文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '请选择要上传的文件'}), 400
        
        # 检查文件类型
        if not file.filename.lower().endswith('.csv'):
            return jsonify({'error': '只支持CSV文件格式'}), 400
        
        # 解析参数
        query_column = request.form.get('query_column', 'query')
        per_query = int(request.form.get('per_query', 5))
        
        if per_query < 1 or per_query > 20:
            per_query = 5
        
        # 读取CSV文件
        try:
            # 读取文件内容
            file_content = file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(file_content))
            file_data = list(csv_reader)
            
            if not file_data:
                return jsonify({'error': 'CSV文件为空'}), 400
            
            if len(file_data) > 1000:
                return jsonify({'error': 'CSV文件行数不能超过1000行'}), 400
            
        except UnicodeDecodeError:
            return jsonify({'error': 'CSV文件编码错误，请使用UTF-8编码'}), 400
        except Exception as e:
            return jsonify({'error': f'CSV文件解析失败: {str(e)}'}), 400
        
        # 检查查询列是否存在
        if query_column not in file_data[0]:
            available_columns = list(file_data[0].keys())
            return jsonify({
                'error': f'CSV文件中不存在列 "{query_column}"',
                'available_columns': available_columns
            }), 400
        
        # 获取当前用户
        current_user = get_current_user()
        user_id = current_user.id if current_user else None
        
        # 执行批量搜索
        options = {'per_query': per_query}
        results = batch_search_service.search_from_file_data(
            file_data=file_data,
            query_field=query_column,
            options=options,
            user_id=user_id
        )
        
        # 统计结果
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        total_products_found = sum(r.get('total_found', 0) for r in results if r['success'])
        
        return jsonify({
            'success': True,
            'results': results,
            'summary': {
                'total_queries': len(results),
                'successful': successful,
                'failed': failed,
                'total_products_found': total_products_found,
                'file_info': {
                    'filename': secure_filename(file.filename),
                    'rows_processed': len(file_data),
                    'query_column': query_column
                }
            }
        })
        
    except Exception as e:
        logger.error(f"文件批量搜索失败: {str(e)}")
        return jsonify({'error': '文件处理失败，请稍后重试'}), 500


@search_bp.route('/products/batch/export', methods=['POST'])
@jwt_required()
@require_auth
def export_batch_search_results():
    """
    导出批量搜索结果为CSV
    ---
    tags:
      - Search
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            results:
              type: array
              description: 批量搜索结果
              items:
                type: object
    responses:
      200:
        description: 导出成功
        content:
          text/csv:
            schema:
              type: string
      400:
        description: 请求参数错误
      500:
        description: 服务器错误
    """
    try:
        data = request.get_json()
        if not data or 'results' not in data:
            return jsonify({'error': '请提供搜索结果数据'}), 400
        
        results = data['results']
        if not results:
            return jsonify({'error': '搜索结果为空'}), 400
        
        # 创建CSV内容
        output = io.StringIO()
        fieldnames = [
            '搜索词', '成功', '找到数量', '第一个结果名称', '第一个结果代码', 
            '第一个结果价格', '第一个结果分类', '错误信息'
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            row = {
                '搜索词': result.get('query', ''),
                '成功': '是' if result.get('success') else '否',
                '找到数量': result.get('total_found', 0),
                '错误信息': result.get('error', '')
            }
            
            # 如果有搜索结果，添加第一个产品的信息
            if result.get('success') and result.get('results'):
                first_product = result['results'][0]
                row['第一个结果名称'] = first_product.get('name', '')
                row['第一个结果代码'] = first_product.get('code', '')
                row['第一个结果价格'] = first_product.get('base_price', '')
                row['第一个结果分类'] = first_product.get('category', '')
            
            writer.writerow(row)
        
        # 准备文件下载
        output.seek(0)
        file_content = output.getvalue().encode('utf-8-sig')  # 添加BOM以支持Excel
        output.close()
        
        # 创建文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'batch_search_results_{timestamp}.csv'
        
        return send_file(
            io.BytesIO(file_content),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"导出批量搜索结果失败: {str(e)}")
        return jsonify({'error': '导出失败，请稍后重试'}), 500


@search_bp.route('/stats', methods=['GET'])
@jwt_required()
@require_auth
def get_search_stats():
    """
    获取搜索统计信息
    ---
    tags:
      - Search
    parameters:
      - name: days
        in: query
        type: integer
        description: 统计天数
        default: 30
        minimum: 1
        maximum: 365
    responses:
      200:
        description: 获取统计信息成功
        schema:
          type: object
          properties:
            stats:
              type: object
    """
    try:
        days = int(request.args.get('days', 30))
        
        if days < 1 or days > 365:
            days = 30
        
        stats = search_service.get_search_stats(days)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"获取搜索统计失败: {str(e)}")
        return jsonify({'error': '获取统计信息失败'}), 500


# 错误处理
@search_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': '请求的资源不存在'}), 404


@search_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': '不支持的请求方法'}), 405


@search_bp.errorhandler(413)
def payload_too_large(error):
    return jsonify({'error': '上传文件过大'}), 413