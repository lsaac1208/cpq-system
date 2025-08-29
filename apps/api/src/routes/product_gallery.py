#!/usr/bin/env python3
"""
Product Gallery API routes for CPQ system
Handles multiple images per product with advanced gallery features
"""

import os
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required
from marshmallow import Schema, fields, ValidationError, validate
from src.models import db, Product, ProductImage, ProductImageProcessingLog
from src.utils.decorators import require_role, require_auth, get_current_user
from src.utils.file_handler import FileHandler
import json
import logging

logger = logging.getLogger(__name__)

product_gallery_bp = Blueprint('product_gallery', __name__)

# 请求验证Schema
class ProductImageSchema(Schema):
    title = fields.Str(validate=validate.Length(max=200))
    description = fields.Str(validate=validate.Length(max=1000))
    alt_text = fields.Str(validate=validate.Length(max=200))
    image_type = fields.Str(validate=validate.OneOf(['product', 'detail', 'usage', 'comparison']))
    is_primary = fields.Bool()

class ImageReorderSchema(Schema):
    id = fields.Int(required=True)
    sort_order = fields.Int(required=True)

class BatchImageReorderSchema(Schema):
    images = fields.List(fields.Nested(ImageReorderSchema), required=True)


@product_gallery_bp.route('/<int:product_id>/gallery', methods=['GET'])
@jwt_required()
@require_auth
def get_product_gallery(product_id):
    """获取产品图片集"""
    try:
        # 验证产品存在
        product = Product.query.get_or_404(product_id)
        
        # 获取查询参数
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        image_type = request.args.get('type')
        
        # 构建查询
        query = ProductImage.query.filter_by(product_id=product_id)
        
        if active_only:
            query = query.filter_by(is_active=True)
            
        if image_type:
            query = query.filter_by(image_type=image_type)
        
        # 按排序顺序获取图片
        images = query.order_by(ProductImage.sort_order, ProductImage.created_at).all()
        
        # 获取主图信息
        primary_image = ProductImage.get_primary_image(product_id)
        
        # 统计信息
        stats = {
            'total_images': len(images),
            'by_type': {},
            'has_primary': primary_image is not None
        }
        
        # 按类型统计
        for img in images:
            img_type = img.image_type
            if img_type not in stats['by_type']:
                stats['by_type'][img_type] = 0
            stats['by_type'][img_type] += 1
        
        return jsonify({
            'images': [img.to_dict() for img in images],
            'primary_image': primary_image.to_dict() if primary_image else None,
            'stats': stats,
            'product': {
                'id': product.id,
                'name': product.name,
                'code': product.code
            }
        })
        
    except Exception as e:
        logger.error(f"获取产品图片集失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


@product_gallery_bp.route('/<int:product_id>/gallery/upload', methods=['POST'])
@jwt_required()
@require_role('engineer', 'admin', 'manager')
def upload_gallery_image(product_id):
    """上传图片到产品图片集"""
    try:
        # 验证产品存在
        product = Product.query.get_or_404(product_id)
        
        # 检查文件
        if 'image' not in request.files:
            return jsonify({'error': '没有上传图片文件'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        # 获取额外参数
        title = request.form.get('title', '')
        description = request.form.get('description', '')
        alt_text = request.form.get('alt_text', '')
        image_type = request.form.get('image_type', 'product')
        is_primary = request.form.get('is_primary', 'false').lower() == 'true'
        
        # 验证图片元数据
        try:
            image_data = {
                'title': title,
                'description': description,
                'alt_text': alt_text,
                'image_type': image_type,
                'is_primary': is_primary
            }
            schema = ProductImageSchema()
            validated_data = schema.load(image_data)
        except ValidationError as err:
            return jsonify({'error': '图片信息验证失败', 'details': err.messages}), 400
        
        # 处理文件上传
        file_handler = FileHandler()
        file_data = file.read()
        filename = file.filename
        mimetype = file.mimetype
        
        if not file_data:
            return jsonify({'error': '文件内容为空'}), 400
        
        # 处理图片
        result = file_handler.process_upload(file_data, filename, mimetype)
        
        if not result['success']:
            return jsonify({
                'error': '图片处理失败',
                'details': result['errors']
            }), 400
        
        # 如果设置为主图，先取消其他主图状态
        if is_primary:
            ProductImage.query.filter_by(product_id=product_id).update({'is_primary': False})
            db.session.commit()
        
        # 获取下一个排序号
        next_order = ProductImage.get_next_sort_order(product_id)
        
        # 创建图片记录
        product_image = ProductImage(
            product_id=product_id,
            filename=result['filename'],
            original_filename=result['original_filename'],
            image_url=result['image_url'],
            thumbnail_url=result.get('thumbnail_url'),
            title=validated_data.get('title') or f'{product.name} - 图片',
            description=validated_data.get('description'),
            alt_text=validated_data.get('alt_text') or product.name,
            file_size=result.get('file_size'),
            format=result['filename'].split('.')[-1].lower(),
            sort_order=next_order,
            is_primary=is_primary,
            image_type=validated_data.get('image_type', 'product')
        )
        
        # 使用数据库事务确保原子性操作
        try:
            # 保存图片记录并提交以获得ID
            product_image.save()
            db.session.flush()  # 确保获得ID但不提交事务
            
            # 验证image_id已生成
            if not product_image.id:
                raise ValueError("Failed to generate image_id after save")
            
            # 记录处理日志
            processing_log = ProductImageProcessingLog(
                image_id=product_image.id,
                operation='upload',
                original_size=result.get('file_size'),
                processed_size=result.get('file_size'),
                status='success',
                parameters=json.dumps({
                    'filename': result['filename'],
                    'image_type': validated_data.get('image_type'),
                    'is_primary': is_primary
                })
            )
            processing_log.save()
            
            # 提交事务
            db.session.commit()
            
        except Exception as db_error:
            # 回滚事务并重新抛出错误
            db.session.rollback()
            logger.error(f"图片保存或日志记录失败: {str(db_error)}")
            raise db_error
        
        # 如果这是第一张图片且没有设置主图，自动设为主图
        if not is_primary:
            existing_primary = ProductImage.get_primary_image(product_id)
            if not existing_primary:
                product_image.is_primary = True
                product_image.save()
        
        # 更新产品的image_url以保持向后兼容
        if is_primary or not product.image_url:
            product.image_url = result['image_url']
            product.save()
        
        return jsonify({
            'message': '图片上传成功',
            'image': product_image.to_dict(),
            'upload_info': {
                'filename': result['filename'],
                'file_size': result.get('file_size'),
                'image_url': result['image_url'],
                'thumbnail_url': result.get('thumbnail_url')
            }
        }), 201
        
    except Exception as e:
        logger.error(f"图片上传失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


@product_gallery_bp.route('/<int:product_id>/gallery/<int:image_id>', methods=['PUT'])
@jwt_required()
@require_role('engineer', 'admin', 'manager')
def update_gallery_image(product_id, image_id):
    """更新图片信息"""
    try:
        # 验证图片存在
        image = ProductImage.query.filter_by(
            id=image_id, 
            product_id=product_id
        ).first_or_404()
        
        # 验证请求数据
        try:
            schema = ProductImageSchema(partial=True)
            validated_data = schema.load(request.json or {})
        except ValidationError as err:
            return jsonify({'error': '数据验证失败', 'details': err.messages}), 400
        
        # 如果要设置为主图
        if validated_data.get('is_primary') and not image.is_primary:
            # 取消其他主图状态
            ProductImage.query.filter_by(product_id=product_id).update({'is_primary': False})
            db.session.commit()
            
            # 更新产品的image_url
            product = Product.query.get(product_id)
            if product:
                product.image_url = image.image_url
                product.save()
        
        # 更新图片信息
        for key, value in validated_data.items():
            setattr(image, key, value)
        
        image.save()
        
        return jsonify({
            'message': '图片信息更新成功',
            'image': image.to_dict()
        })
        
    except Exception as e:
        logger.error(f"更新图片信息失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


@product_gallery_bp.route('/<int:product_id>/gallery/<int:image_id>', methods=['DELETE'])
@jwt_required()
@require_role('engineer', 'admin', 'manager')
def delete_gallery_image(product_id, image_id):
    """删除图片"""
    try:
        # 验证图片存在
        image = ProductImage.query.filter_by(
            id=image_id, 
            product_id=product_id
        ).first_or_404()
        
        # 保存图片信息（在删除前）
        was_primary = image.is_primary
        image_filename = image.filename
        image_url = image.image_url
        
        # 使用数据库事务确保操作原子性
        try:
            # 删除物理文件
            file_handler = FileHandler()
            file_handler.cleanup_old_files(image_filename)
            
            # 手动删除相关的处理日志记录（避免CASCADE问题）
            ProductImageProcessingLog.query.filter_by(image_id=image_id).delete()
            db.session.flush()
            
            # 删除图片记录
            db.session.delete(image)
            db.session.flush()  # 确保删除操作被执行，但事务未提交
            
            # 如果删除的是主图，设置下一张图片为主图
            if was_primary:
                next_primary = ProductImage.query.filter_by(
                    product_id=product_id,
                    is_active=True
                ).order_by(ProductImage.sort_order).first()
                
                if next_primary:
                    next_primary.is_primary = True
                    db.session.flush()
                    
                    # 更新产品的image_url
                    product = Product.query.get(product_id)
                    if product:
                        product.image_url = next_primary.image_url
                        db.session.flush()
                else:
                    # 没有其他图片，清除产品的image_url
                    product = Product.query.get(product_id)
                    if product:
                        product.image_url = None
                        db.session.flush()
            
            # 提交事务
            db.session.commit()
            
            logger.info(f"图片删除成功: {image_filename} (ID: {image_id})")
            
            return jsonify({
                'message': '图片删除成功',
                'deleted_image_id': image_id
            })
            
        except Exception as db_error:
            # 回滚事务
            db.session.rollback()
            logger.error(f"数据库操作失败，已回滚: {str(db_error)}")
            raise db_error
        
    except Exception as e:
        logger.error(f"删除图片失败: {str(e)}")
        # 确保数据库会话被回滚
        try:
            db.session.rollback()
        except:
            pass
        return jsonify({'error': f'删除图片失败: {str(e)}'}), 500


@product_gallery_bp.route('/<int:product_id>/gallery/reorder', methods=['POST'])
@jwt_required()
@require_role('engineer', 'admin', 'manager')
def reorder_gallery_images(product_id):
    """重新排序图片"""
    try:
        # 验证产品存在
        Product.query.get_or_404(product_id)
        
        # 验证请求数据
        try:
            schema = BatchImageReorderSchema()
            validated_data = schema.load(request.json)
        except ValidationError as err:
            return jsonify({'error': '数据验证失败', 'details': err.messages}), 400
        
        image_orders = validated_data['images']
        
        # 验证所有图片都属于该产品
        image_ids = [item['id'] for item in image_orders]
        valid_images = ProductImage.query.filter(
            ProductImage.id.in_(image_ids),
            ProductImage.product_id == product_id
        ).count()
        
        if valid_images != len(image_ids):
            return jsonify({'error': '部分图片不属于该产品'}), 400
        
        # 重新排序
        ProductImage.reorder_images(product_id, image_orders)
        
        # 获取更新后的图片列表
        updated_images = ProductImage.query.filter_by(
            product_id=product_id,
            is_active=True
        ).order_by(ProductImage.sort_order).all()
        
        return jsonify({
            'message': '图片排序更新成功',
            'images': [img.to_dict() for img in updated_images]
        })
        
    except Exception as e:
        logger.error(f"图片排序失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


@product_gallery_bp.route('/<int:product_id>/gallery/<int:image_id>/primary', methods=['PUT'])
@product_gallery_bp.route('/<int:product_id>/gallery/<int:image_id>/set-primary', methods=['POST'])
@jwt_required()
@require_role('engineer', 'admin', 'manager')
def set_primary_image(product_id, image_id):
    """设置主图"""
    try:
        # 设置主图
        primary_image = ProductImage.set_primary_image(product_id, image_id)
        
        if not primary_image:
            return jsonify({'error': '图片不存在或不属于该产品'}), 404
        
        # 更新产品的image_url
        product = Product.query.get(product_id)
        if product:
            product.image_url = primary_image.image_url
            product.save()
        
        return jsonify({
            'message': '主图设置成功',
            'primary_image': primary_image.to_dict()
        })
        
    except Exception as e:
        logger.error(f"设置主图失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


@product_gallery_bp.route('/<int:product_id>/gallery/batch-upload', methods=['POST'])
@jwt_required()
@require_role('engineer', 'admin', 'manager')
def batch_upload_gallery_images(product_id):
    """批量上传图片"""
    try:
        # 验证产品存在
        product = Product.query.get_or_404(product_id)
        
        # 检查文件
        if 'images' not in request.files:
            return jsonify({'error': '没有上传图片文件'}), 400
        
        files = request.files.getlist('images')
        if not files or len(files) == 0:
            return jsonify({'error': '没有选择文件'}), 400
        
        # 限制批量上传数量
        max_batch_size = 10
        if len(files) > max_batch_size:
            return jsonify({'error': f'批量上传最多支持 {max_batch_size} 张图片'}), 400
        
        # 获取公共参数
        image_type = request.form.get('image_type', 'product')
        auto_set_primary = request.form.get('auto_set_primary', 'false').lower() == 'true'
        
        file_handler = FileHandler()
        results = []
        success_count = 0
        
        # 获取当前最大排序号
        current_max_order = db.session.query(
            db.func.max(ProductImage.sort_order)
        ).filter_by(product_id=product_id).scalar() or 0
        
        for i, file in enumerate(files):
            try:
                if file.filename == '':
                    results.append({
                        'filename': '空文件名',
                        'success': False,
                        'error': '文件名为空'
                    })
                    continue
                
                # 处理文件
                file_data = file.read()
                if not file_data:
                    results.append({
                        'filename': file.filename,
                        'success': False,
                        'error': '文件内容为空'
                    })
                    continue
                
                # 图片处理
                result = file_handler.process_upload(file_data, file.filename, file.mimetype)
                
                if not result['success']:
                    results.append({
                        'filename': file.filename,
                        'success': False,
                        'error': ', '.join(result['errors'])
                    })
                    continue
                
                # 确定是否设为主图
                is_primary = False
                if auto_set_primary and i == 0:  # 第一张图片
                    existing_primary = ProductImage.get_primary_image(product_id)
                    if not existing_primary:
                        is_primary = True
                
                # 创建图片记录
                sort_order = current_max_order + (i + 1) * 10
                
                product_image = ProductImage(
                    product_id=product_id,
                    filename=result['filename'],
                    original_filename=result['original_filename'],
                    image_url=result['image_url'],
                    thumbnail_url=result.get('thumbnail_url'),
                    title=f'{product.name} - {file.filename}',
                    alt_text=product.name,
                    file_size=result.get('file_size'),
                    format=result['filename'].split('.')[-1].lower(),
                    sort_order=sort_order,
                    is_primary=is_primary,
                    image_type=image_type
                )
                
                # 使用数据库事务确保原子性操作
                try:
                    # 保存图片记录并提交以获得ID
                    product_image.save()
                    db.session.flush()  # 确保获得ID但不提交事务
                    
                    # 验证image_id已生成
                    if not product_image.id:
                        raise ValueError(f"Failed to generate image_id for file {file.filename}")
                    
                    # 记录处理日志
                    processing_log = ProductImageProcessingLog(
                        image_id=product_image.id,
                        operation='batch_upload',
                        original_size=result.get('file_size'),
                        processed_size=result.get('file_size'),
                        status='success',
                        parameters=json.dumps({
                            'filename': result['filename'],
                            'batch_index': i,
                            'image_type': image_type
                        })
                    )
                    processing_log.save()
                    
                    # 提交事务
                    db.session.commit()
                    
                except Exception as db_error:
                    # 回滚事务
                    db.session.rollback()
                    logger.error(f"图片保存或日志记录失败 (文件: {file.filename}): {str(db_error)}")
                    # 将此作为处理错误，继续处理其他文件
                    results.append({
                        'filename': file.filename,
                        'success': False,
                        'error': f'数据库操作失败: {str(db_error)}'
                    })
                    continue
                
                results.append({
                    'filename': file.filename,
                    'success': True,
                    'image': product_image.to_dict()
                })
                
                success_count += 1
                
                # 更新产品主图
                if is_primary:
                    product.image_url = result['image_url']
                    product.save()
                
            except Exception as e:
                logger.error(f"处理文件 {file.filename} 失败: {str(e)}")
                results.append({
                    'filename': file.filename,
                    'success': False,
                    'error': str(e)
                })
        
        return jsonify({
            'message': f'批量上传完成，成功 {success_count}/{len(files)} 张',
            'success_count': success_count,
            'total_count': len(files),
            'results': results
        })
        
    except Exception as e:
        logger.error(f"批量上传失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


@product_gallery_bp.route('/<int:product_id>/gallery/stats', methods=['GET'])
@jwt_required()
@require_auth
def get_gallery_stats(product_id):
    """获取图片集统计信息"""
    try:
        # 验证产品存在
        Product.query.get_or_404(product_id)
        
        # 获取统计信息
        total_images = ProductImage.query.filter_by(
            product_id=product_id,
            is_active=True
        ).count()
        
        # 按类型统计
        type_stats = db.session.query(
            ProductImage.image_type,
            db.func.count(ProductImage.id).label('count')
        ).filter_by(
            product_id=product_id,
            is_active=True
        ).group_by(ProductImage.image_type).all()
        
        # 总文件大小
        total_size = db.session.query(
            db.func.sum(ProductImage.file_size)
        ).filter_by(
            product_id=product_id,
            is_active=True
        ).scalar() or 0
        
        # 主图信息
        primary_image = ProductImage.get_primary_image(product_id)
        
        return jsonify({
            'total_images': total_images,
            'total_size': total_size,
            'by_type': {stat.image_type: stat.count for stat in type_stats},
            'has_primary': primary_image is not None,
            'primary_image_id': primary_image.id if primary_image else None
        })
        
    except Exception as e:
        logger.error(f"获取图片集统计失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


# 兼容旧版API的路由
@product_gallery_bp.route('/<int:product_id>/migrate-legacy-image', methods=['POST'])
@jwt_required()
@require_role('admin')
def migrate_legacy_image(product_id):
    """迁移旧版单张图片到图片集系统"""
    try:
        product = Product.query.get_or_404(product_id)
        
        if not product.image_url:
            return jsonify({'message': '产品没有旧版图片需要迁移'}), 200
        
        # 检查是否已经迁移过
        existing = ProductImage.query.filter_by(
            product_id=product_id,
            image_url=product.image_url
        ).first()
        
        if existing:
            return jsonify({
                'message': '图片已经迁移过',
                'image': existing.to_dict()
            }), 200
        
        # 执行迁移
        migrated_image = product.migrate_legacy_image()
        
        if migrated_image:
            return jsonify({
                'message': '图片迁移成功',
                'image': migrated_image.to_dict()
            })
        else:
            return jsonify({'error': '图片迁移失败'}), 500
        
    except Exception as e:
        logger.error(f"迁移旧版图片失败: {str(e)}")
        return jsonify({'error': str(e)}), 500