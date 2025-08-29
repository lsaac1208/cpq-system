import os
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required
from marshmallow import Schema, fields, ValidationError, validate
from src.models import db, Product
from src.utils.decorators import require_role, require_auth, get_current_user
from src.utils.file_handler import FileHandler

products_bp = Blueprint('products', __name__)

# Schemas for request validation
class ProductSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    code = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    description = fields.Str(validate=validate.Length(max=1000))
    category = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    base_price = fields.Decimal(required=True, places=2, validate=validate.Range(min=0))
    image_url = fields.Str(validate=validate.Length(max=255))
    configuration_schema = fields.Dict()
    specifications = fields.Dict()
    is_active = fields.Bool()
    is_configurable = fields.Bool()
    # Extended AI analysis fields
    detailed_description = fields.Str()
    features = fields.List(fields.Dict())
    application_scenarios = fields.List(fields.Dict())
    accessories = fields.List(fields.Dict())
    certificates = fields.List(fields.Dict())
    support_info = fields.Dict()

@products_bp.route('', methods=['GET'])
@jwt_required()
def get_products():
    """Get all products with enhanced filtering and performance optimization."""
    try:
        # Query parameters with validation
        category = request.args.get('category', '').strip()
        is_active_param = request.args.get('is_active', 'true').lower()
        is_active = is_active_param in ['true', '1', 'yes']
        configurable = request.args.get('configurable', '').strip()
        search = request.args.get('search', '').strip()
        
        # Pagination parameters with limits
        try:
            page = max(1, int(request.args.get('page', 1)))
            per_page = min(100, max(1, int(request.args.get('per_page', 20))))
        except ValueError:
            page, per_page = 1, 20
        
        # Build optimized query with indexes
        query = Product.query
        
        # Apply filters efficiently
        if category:
            query = query.filter(Product.category == category)
        
        query = query.filter(Product.is_active == is_active)
        
        if configurable:
            is_configurable = configurable.lower() in ['true', '1', 'yes']
            query = query.filter(Product.is_configurable == is_configurable)
        
        # Search functionality (basic implementation)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Product.name.ilike(search_term),
                    Product.description.ilike(search_term),
                    Product.code.ilike(search_term)
                )
            )
        
        # Order by ID for consistent pagination
        query = query.order_by(Product.id.desc())
        
        # Execute paginated query
        products = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Optimize response data
        products_data = []
        for product in products.items:
            # Use lighter serialization for list view
            product_dict = {
                'id': product.id,
                'name': product.name,
                'code': product.code,
                'category': product.category,
                'base_price': float(product.base_price) if product.base_price else 0,
                'image_url': product.image_url,
                'is_active': product.is_active,
                'is_configurable': product.is_configurable,
                'created_at': product.created_at.isoformat() if product.created_at else None,
                'updated_at': product.updated_at.isoformat() if product.updated_at else None,
                # Include summary fields but not full complex data
                'has_features': bool(product.features),
                'has_accessories': bool(product.accessories),
                'description': product.description[:200] + '...' if product.description and len(product.description) > 200 else product.description
            }
            products_data.append(product_dict)
        
        return jsonify({
            'products': products_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': products.total,
                'pages': products.pages,
                'has_prev': products.has_prev,
                'has_next': products.has_next
            },
            'filters_applied': {
                'category': category or None,
                'is_active': is_active,
                'configurable': configurable or None,
                'search': search or None
            }
        })
        
    except Exception as e:
        current_app.logger.error(f'Error fetching products: {str(e)}')
        return jsonify({
            'error': 'Failed to fetch products',
            'error_code': 'PRODUCTS_FETCH_ERROR'
        }), 500

@products_bp.route('/<int:product_id>', methods=['GET'])
@jwt_required()
def get_product(product_id):
    """Get a specific product with full details."""
    try:
        # Validate product_id
        if product_id <= 0:
            return jsonify({
                'error': 'Invalid product ID',
                'error_code': 'INVALID_PRODUCT_ID'
            }), 400
        
        # Fetch product with error handling
        product = Product.query.filter_by(id=product_id).first()
        if not product:
            return jsonify({
                'error': 'Product not found',
                'error_code': 'PRODUCT_NOT_FOUND'
            }), 404
        
        # Check if product is active (optional restriction)
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        if not product.is_active and not include_inactive:
            return jsonify({
                'error': 'Product is not available',
                'error_code': 'PRODUCT_INACTIVE'
            }), 404
        
        # Return full product details
        product_data = product.to_dict()
        
        # Add computed fields for frontend convenience
        product_data['display_price'] = f"¥{float(product.base_price):,.2f}" if product.base_price else "¥0.00"
        product_data['has_image'] = bool(product.image_url)
        product_data['feature_count'] = len(product.features) if product.features else 0
        product_data['accessory_count'] = len(product.accessories) if product.accessories else 0
        
        from datetime import datetime
        return jsonify({
            'product': product_data,
            'meta': {
                'retrieved_at': datetime.utcnow().isoformat(),
                'is_full_details': True
            }
        })
        
    except Exception as e:
        current_app.logger.error(f'Error fetching product {product_id}: {str(e)}')
        return jsonify({
            'error': 'Failed to fetch product details',
            'error_code': 'PRODUCT_FETCH_ERROR'
        }), 500

@products_bp.route('', methods=['POST'])
@jwt_required()
@require_role('engineer', 'admin', 'manager')
def create_product():
    """Create a new product."""
    try:
        # Validate request data
        schema = ProductSchema()
        data = schema.load(request.json)
        
        # Check if product code already exists
        if Product.query.filter_by(code=data['code']).first():
            return jsonify({'error': 'Product code already exists'}), 400
        
        # Create new product with basic fields first
        basic_fields = {k: v for k, v in data.items() 
                       if k not in ['configuration_schema', 'specifications', 'features', 
                                  'application_scenarios', 'accessories', 'certificates', 'support_info']}
        product = Product(**basic_fields)
        
        # Set complex fields using specialized methods
        if 'configuration_schema' in data:
            product.set_configuration_schema(data['configuration_schema'])
        
        if 'specifications' in data:
            product.set_specifications(data['specifications'])
            
        if 'features' in data:
            product.set_features(data['features'])
            
        if 'application_scenarios' in data:
            product.set_application_scenarios(data['application_scenarios'])
            
        if 'accessories' in data:
            product.set_accessories(data['accessories'])
            
        if 'certificates' in data:
            product.set_certificates(data['certificates'])
            
        if 'support_info' in data:
            product.set_support_info(data['support_info'])
        
        product.save()
        
        return jsonify({
            'message': 'Product created successfully',
            'product': product.to_dict()
        }), 201
        
    except ValidationError as err:
        return jsonify({'error': 'Validation error', 'details': err.messages}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@products_bp.route('/<int:product_id>', methods=['PUT'])
@jwt_required()
@require_role('engineer', 'admin', 'manager')
def update_product(product_id):
    """Update a product."""
    try:
        product = Product.query.get_or_404(product_id)
        
        # Validate request data
        schema = ProductSchema(partial=True)
        data = schema.load(request.json)
        
        # Check if new code conflicts with existing products
        if 'code' in data and data['code'] != product.code:
            if Product.query.filter_by(code=data['code']).first():
                return jsonify({'error': 'Product code already exists'}), 400
        
        # Update fields
        for key, value in data.items():
            if key == 'configuration_schema':
                product.set_configuration_schema(value)
            elif key == 'specifications':
                product.set_specifications(value)
            elif key == 'features':
                product.set_features(value)
            elif key == 'application_scenarios':
                product.set_application_scenarios(value)
            elif key == 'accessories':
                product.set_accessories(value)
            elif key == 'certificates':
                product.set_certificates(value)
            elif key == 'support_info':
                product.set_support_info(value)
            else:
                setattr(product, key, value)
        
        product.save()
        
        return jsonify({
            'message': 'Product updated successfully',
            'product': product.to_dict()
        })
        
    except ValidationError as err:
        return jsonify({'error': 'Validation error', 'details': err.messages}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@products_bp.route('/<int:product_id>', methods=['DELETE'])
@jwt_required()
@require_role('engineer', 'admin', 'manager')
def delete_product(product_id):
    """Delete a product (soft delete by setting is_active to False)."""
    try:
        product = Product.query.get_or_404(product_id)
        product.is_active = False
        product.save()
        
        return jsonify({
            'message': 'Product deactivated successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@products_bp.route('/<int:product_id>/hard-delete', methods=['DELETE'])
@jwt_required()
@require_role('admin')
def hard_delete_product(product_id):
    """Permanently delete a product (admin only)."""
    try:
        product = Product.query.get_or_404(product_id)
        
        # Check if product has associated quotes
        if product.quotes:
            return jsonify({
                'error': 'Cannot delete product with associated quotes',
                'quote_count': len(product.quotes)
            }), 400
        
        product.delete()
        
        return jsonify({
            'message': 'Product permanently deleted'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@products_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    """Get all product categories."""
    try:
        categories = db.session.query(Product.category).distinct().all()
        category_list = [cat[0] for cat in categories if cat[0]]
        
        return jsonify({
            'categories': category_list
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@products_bp.route('/<int:product_id>/upload-image', methods=['POST'])
@jwt_required()
@require_role('engineer', 'admin', 'manager')
def upload_product_image(product_id):
    """Upload image for a specific product."""
    try:
        # Check if product exists
        product = Product.query.get_or_404(product_id)
        
        # Check if file was uploaded
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Initialize file handler
        file_handler = FileHandler()
        
        # Read file data and get file info
        file_data = file.read()
        filename = file.filename
        mimetype = file.mimetype
        
        # Validate file data is not empty
        if not file_data:
            return jsonify({'error': 'Empty file data'}), 400
        
        # Process the upload
        result = file_handler.process_upload(
            file_data, 
            filename, 
            mimetype
        )
        
        if not result['success']:
            return jsonify({
                'error': 'File upload failed',
                'details': result['errors']
            }), 400
        
        # Clean up old image if exists
        if product.image_url:
            file_handler.cleanup_old_files(product.image_url)
        
        # Update product with new image URL
        product.image_url = result['image_url']
        product.save()
        
        return jsonify({
            'message': 'Image uploaded successfully',
            'image_url': result['image_url'],
            'thumbnail_url': result['thumbnail_url'],
            'file_info': {
                'filename': result['filename'],
                'file_size': result['file_size'],
                'original_filename': result['original_filename']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@products_bp.route('/<int:product_id>/delete-image', methods=['DELETE'])
@jwt_required()
@require_role('engineer', 'admin', 'manager')
def delete_product_image(product_id):
    """Delete image for a specific product."""
    try:
        # Check if product exists
        product = Product.query.get_or_404(product_id)
        
        if not product.image_url:
            return jsonify({'error': 'Product has no image to delete'}), 400
        
        # Initialize file handler and clean up files
        file_handler = FileHandler()
        file_handler.cleanup_old_files(product.image_url)
        
        # Clear image URL from product
        product.image_url = None
        product.save()
        
        return jsonify({
            'message': 'Image deleted successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@products_bp.route('/uploads/<path:filename>')
def serve_uploaded_file(filename):
    """Serve uploaded files (images)."""
    try:
        # 验证文件名安全性
        if not filename or '..' in filename or filename.startswith('/'):
            return jsonify({'error': 'Invalid filename'}), 400
        
        # Get upload folder path
        file_handler = FileHandler()
        upload_folder = file_handler.upload_folder
        
        # Determine which subdirectory to serve from based on filename
        subdir = None
        file_found = False
        
        # 按优先级检查不同目录
        search_dirs = []
        if '_thumb.' in filename:
            search_dirs = ['thumbnails', 'compressed', 'originals']
        else:
            search_dirs = ['compressed', 'originals', 'thumbnails']
        
        for check_subdir in search_dirs:
            check_path = os.path.join(upload_folder, check_subdir)
            file_path = os.path.join(check_path, filename)
            
            if os.path.exists(file_path) and os.path.isfile(file_path):
                # 安全检查 - 确保文件在上传目录内
                try:
                    if os.path.commonpath([file_path, upload_folder]) == upload_folder:
                        subdir = check_subdir
                        file_found = True
                        break
                except ValueError:
                    # 路径不在同一个根目录下
                    continue
        
        if not file_found or not subdir:
            # 记录404错误以便调试
            current_app.logger.warning(f"File not found: {filename} in upload folder: {upload_folder}")
            return jsonify({'error': 'File not found'}), 404
        
        full_path = os.path.join(upload_folder, subdir)
        
        # 设置适当的缓存头
        response = send_from_directory(
            full_path, 
            filename,
            max_age=3600  # 1小时缓存
        )
        
        # 设置适当的Content-Type
        if filename.lower().endswith(('.jpg', '.jpeg')):
            response.headers['Content-Type'] = 'image/jpeg'
        elif filename.lower().endswith('.png'):
            response.headers['Content-Type'] = 'image/png'
        elif filename.lower().endswith('.webp'):
            response.headers['Content-Type'] = 'image/webp'
        elif filename.lower().endswith('.gif'):
            response.headers['Content-Type'] = 'image/gif'
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Error serving file {filename}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500