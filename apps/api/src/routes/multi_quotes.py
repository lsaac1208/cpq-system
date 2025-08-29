from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
from datetime import datetime, date
from sqlalchemy import func
from src.models import db, Product
from src.models.multi_quote import MultiQuote, MultiQuoteItem, MultiQuoteStatus
from src.utils.decorators import get_current_user

multi_quotes_bp = Blueprint('multi_quotes', __name__)

# Schemas for request validation
class MultiQuoteItemSchema(Schema):
    product_id = fields.Int(required=True)
    quantity = fields.Int(load_default=1)
    unit_price = fields.Decimal(places=2, required=True)
    discount_percentage = fields.Decimal(places=2, load_default=0)
    notes = fields.Str()

class MultiQuoteSchema(Schema):
    customer_name = fields.Str(required=True)
    customer_email = fields.Email(required=True)
    customer_company = fields.Str()
    customer_phone = fields.Str()
    customer_address = fields.Str()
    items = fields.List(fields.Nested(MultiQuoteItemSchema), required=True)
    discount_percentage = fields.Decimal(places=2, load_default=0)
    tax_percentage = fields.Decimal(places=2, load_default=0)
    valid_until = fields.Date()
    notes = fields.Str()
    terms_conditions = fields.Str()

@multi_quotes_bp.route('', methods=['GET'])
@jwt_required()
def get_multi_quotes():
    """Get multi-product quotes with user-based access control."""
    try:
        # Get current user for authorization
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '用户认证失败'}), 401
        
        # Query parameters
        search = request.args.get('search')
        status = request.args.get('status')
        customer_email = request.args.get('customer_email')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        min_amount = request.args.get('min_amount')
        max_amount = request.args.get('max_amount')
        created_by = request.args.get('created_by')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Build query with user-based security filtering
        query = MultiQuote.query
        
        # 🔒 SECURITY: Apply user-based access control
        if current_user.role == 'admin':
            # Admin can access all quotes or filter by specific user
            if created_by and created_by != 'all':
                try:
                    query = query.filter(MultiQuote.created_by == int(created_by))
                except ValueError:
                    return jsonify({'error': 'Invalid created_by value'}), 400
            # If no created_by or created_by='all', admin sees all quotes
        else:
            # 🔒 Non-admin users can only see their own quotes
            query = query.filter(MultiQuote.created_by == current_user.id)
        
        # Search across multiple fields (SQLite compatible)
        if search and search.strip():
            search_term = f"%{search.strip().lower()}%"
            query = query.filter(
                db.or_(
                    func.lower(MultiQuote.quote_number).like(search_term),
                    func.lower(MultiQuote.customer_name).like(search_term),
                    func.lower(MultiQuote.customer_email).like(search_term),
                    func.lower(MultiQuote.customer_company).like(search_term)
                )
            )
        
        # Filter by status
        if status:
            try:
                status_enum = MultiQuoteStatus(status)
                query = query.filter(MultiQuote.status == status_enum)
            except ValueError:
                return jsonify({'error': 'Invalid status value'}), 400
        
        # Filter by customer email
        if customer_email:
            query = query.filter(MultiQuote.customer_email.contains(customer_email))
        
        # Date range filters
        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                query = query.filter(MultiQuote.created_at >= from_date)
            except ValueError:
                return jsonify({'error': 'Invalid date_from format. Use YYYY-MM-DD'}), 400
                
        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
                # Add one day to include the entire day
                to_date_end = datetime.combine(to_date, datetime.max.time())
                query = query.filter(MultiQuote.created_at <= to_date_end)
            except ValueError:
                return jsonify({'error': 'Invalid date_to format. Use YYYY-MM-DD'}), 400
        
        # Amount filters
        if min_amount:
            try:
                query = query.filter(MultiQuote.total_price >= float(min_amount))
            except ValueError:
                return jsonify({'error': 'Invalid min_amount value'}), 400
                
        if max_amount:
            try:
                query = query.filter(MultiQuote.total_price <= float(max_amount))
            except ValueError:
                return jsonify({'error': 'Invalid max_amount value'}), 400
        
        # Note: User-based filtering already applied above for security
        
        # Sorting
        valid_sort_fields = ['created_at', 'total_price', 'customer_name', 'quote_number']
        if sort_by in valid_sort_fields:
            sort_column = getattr(MultiQuote, sort_by)
            if sort_order.lower() == 'asc':
                query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(sort_column.desc())
        else:
            # Default sorting
            query = query.order_by(MultiQuote.created_at.desc())
        
        # Paginate results
        quotes = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'quotes': [quote.to_dict() for quote in quotes.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': quotes.total,
                'pages': quotes.pages
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@multi_quotes_bp.route('/<int:quote_id>', methods=['GET'])
@jwt_required()
def get_multi_quote(quote_id):
    """Get a specific multi-product quote."""
    try:
        quote = MultiQuote.query.get(quote_id)
        if not quote:
            return jsonify({'error': '报价不存在'}), 404
            
        return jsonify({'quote': quote.to_dict()})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@multi_quotes_bp.route('', methods=['POST'])
@jwt_required()
def create_multi_quote():
    """Create a new multi-product quote."""
    try:
        # Get current user object (not just username)
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '用户认证失败'}), 401
        current_user_id = current_user.id
        
        # Validate request data
        schema = MultiQuoteSchema()
        data = schema.load(request.json)
        
        if not data.get('items') or len(data['items']) == 0:
            return jsonify({'error': '报价必须包含至少一个产品项目'}), 400
        
        # Verify all products exist and are active
        product_ids = [item['product_id'] for item in data['items']]
        products = Product.query.filter(Product.id.in_(product_ids)).all()
        
        if len(products) != len(product_ids):
            return jsonify({'error': '一个或多个产品不存在'}), 404
        
        inactive_products = [p for p in products if not p.is_active]
        if inactive_products:
            return jsonify({'error': f'产品 {[p.name for p in inactive_products]} 已停用'}), 400
        
        # Create product lookup dict
        product_dict = {p.id: p for p in products}
        
        # Create new quote with temporary quote number
        quote = MultiQuote(
            quote_number='TEMP',  # Temporary placeholder
            customer_name=data['customer_name'],
            customer_email=data['customer_email'],
            customer_company=data.get('customer_company'),
            customer_phone=data.get('customer_phone'),
            customer_address=data.get('customer_address'),
            discount_percentage=data.get('discount_percentage', 0),
            tax_percentage=data.get('tax_percentage', 0),
            valid_until=data.get('valid_until'),
            notes=data.get('notes'),
            terms_conditions=data.get('terms_conditions'),
            created_by=current_user_id
        )
        
        # Add quote to session to get ID
        db.session.add(quote)
        db.session.flush()  # This assigns ID without committing
        
        # Create quote items
        for item_data in data['items']:
            product = product_dict[item_data['product_id']]
            
            item = MultiQuoteItem(
                quote_id=quote.id,
                product_id=item_data['product_id'],
                quantity=item_data.get('quantity', 1),
                unit_price=item_data.get('unit_price', product.base_price),
                discount_percentage=item_data.get('discount_percentage', 0),
                notes=item_data.get('notes')
            )
            
            # Calculate item totals
            item.calculate_totals()
            quote.items.append(item)
        
        # Calculate quote totals
        quote.calculate_totals()
        
        # Generate quote number
        quote.quote_number = quote.generate_quote_number()
        
        # Save everything
        db.session.commit()
        
        return jsonify({
            'message': '多产品报价创建成功',
            'quote': quote.to_dict()
        }), 201
        
    except ValidationError as err:
        db.session.rollback()
        return jsonify({'error': '数据验证错误', 'details': err.messages}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@multi_quotes_bp.route('/<int:quote_id>', methods=['PUT'])
@jwt_required()
def update_multi_quote(quote_id):
    """Update a multi-product quote."""
    try:
        quote = MultiQuote.query.get_or_404(quote_id)
        
        # Only allow updates for draft quotes
        if quote.status != MultiQuoteStatus.DRAFT:
            return jsonify({'error': '只有草稿状态的报价可以修改'}), 400
        
        # Validate request data
        schema = MultiQuoteSchema(partial=True)
        data = schema.load(request.json)
        
        # Update basic quote fields
        for key in ['customer_name', 'customer_email', 'customer_company', 
                   'customer_phone', 'customer_address', 'discount_percentage', 
                   'tax_percentage', 'valid_until', 'notes', 'terms_conditions']:
            if key in data:
                setattr(quote, key, data[key])
        
        # If items are provided, update them
        if 'items' in data:
            # Remove existing items
            MultiQuoteItem.query.filter_by(quote_id=quote.id).delete()
            
            # Add new items
            product_ids = [item['product_id'] for item in data['items']]
            products = Product.query.filter(Product.id.in_(product_ids)).all()
            product_dict = {p.id: p for p in products}
            
            for item_data in data['items']:
                product = product_dict[item_data['product_id']]
                
                item = MultiQuoteItem(
                    quote_id=quote.id,
                    product_id=item_data['product_id'],
                    quantity=item_data.get('quantity', 1),
                    unit_price=item_data.get('unit_price', product.base_price),
                    discount_percentage=item_data.get('discount_percentage', 0),
                    notes=item_data.get('notes')
                )
                
                item.calculate_totals()
                quote.items.append(item)
        
        # Recalculate totals
        quote.calculate_totals()
        
        db.session.commit()
        
        return jsonify({
            'message': '报价更新成功',
            'quote': quote.to_dict()
        })
        
    except ValidationError as err:
        db.session.rollback()
        return jsonify({'error': '数据验证错误', 'details': err.messages}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@multi_quotes_bp.route('/<int:quote_id>/status', methods=['PUT'])
@jwt_required()
def update_quote_status(quote_id):
    """Update quote status."""
    try:
        quote = MultiQuote.query.get_or_404(quote_id)
        
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({'error': '请提供状态信息'}), 400
        
        try:
            new_status = MultiQuoteStatus(data['status'])
        except ValueError:
            return jsonify({'error': '无效的状态值'}), 400
        
        quote.status = new_status
        db.session.commit()
        
        return jsonify({
            'message': '状态更新成功',
            'quote': quote.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@multi_quotes_bp.route('/<int:quote_id>', methods=['DELETE'])
@jwt_required()
def delete_multi_quote(quote_id):
    """Delete a multi-product quote."""
    try:
        # Get current user object (not just username)
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '用户认证失败'}), 401
        current_user_id = current_user.id
        
        # Use get() instead of get_or_404() to handle race conditions
        quote = MultiQuote.query.get(quote_id)
        if not quote:
            return jsonify({'error': '报价不存在或已被删除'}), 404
        
        # Check permissions - only creator or admin can delete
        # For now, allow deletion by quote creator only
        if quote.created_by != current_user_id:
            return jsonify({'error': '您没有权限删除这个报价'}), 403
        
        # Allow deletion of quotes in various statuses with appropriate warnings
        status_messages = {
            MultiQuoteStatus.DRAFT: '草稿报价已删除',
            MultiQuoteStatus.PENDING: '待审批报价已删除',
            MultiQuoteStatus.APPROVED: '已审批报价已删除',
            MultiQuoteStatus.REJECTED: '已拒绝报价已删除',
            MultiQuoteStatus.EXPIRED: '已过期报价已删除'
        }
        
        status_message = status_messages.get(quote.status, '报价已删除')
        
        # Store quote info for logging before deletion
        quote_number = quote.quote_number
        quote_status = quote.status.value
        
        # Begin database transaction with explicit handling
        try:
            # Verify the quote still exists before deletion (race condition check)
            quote_check = MultiQuote.query.get(quote_id)
            if not quote_check:
                return jsonify({'error': '报价不存在或已被删除'}), 404
            
            # Explicitly delete related items first (though cascade should handle this)
            MultiQuoteItem.query.filter_by(quote_id=quote_id).delete()
            
            # Delete the quote
            db.session.delete(quote)
            db.session.flush()  # Flush to catch constraint errors before commit
            db.session.commit()
            
            # Log the deletion for audit purposes
            print(f"Quote {quote_number} (status: {quote_status}) deleted by user {current_user_id}")
            
            return jsonify({
                'message': status_message,
                'quote_number': quote_number,
                'status': quote_status
            })
            
        except Exception as db_error:
            db.session.rollback()
            print(f"Database error deleting quote {quote_id}: {str(db_error)}")
            
            # Handle specific database errors
            error_message = str(db_error)
            if 'FOREIGN KEY constraint failed' in error_message:
                return jsonify({'error': '无法删除报价：存在相关联的数据记录'}), 400
            elif 'does not exist' in error_message or 'not found' in error_message:
                return jsonify({'error': '报价不存在或已被删除'}), 404
            else:
                return jsonify({'error': f'删除报价时发生数据库错误: {error_message}'}), 500
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting quote {quote_id}: {str(e)}")
        return jsonify({'error': f'删除报价时发生错误: {str(e)}'}), 500