from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
from datetime import datetime, timedelta
from sqlalchemy import func
from src.models import db, Quote, Product, QuoteStatus
from src.utils.decorators import get_current_user

quotes_bp = Blueprint('quotes', __name__)

# Schemas for request validation
class QuoteSchema(Schema):
    customer_name = fields.Str(required=True)
    customer_email = fields.Email(required=True)
    customer_company = fields.Str()
    product_id = fields.Int(required=True)
    configuration = fields.Dict()
    quantity = fields.Int(load_default=1)
    discount_percentage = fields.Decimal(places=2, load_default=0)
    notes = fields.Str()

@quotes_bp.route('', methods=['GET'])
@jwt_required()
def get_quotes():
    """Get quotes with user-based access control."""
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
        query = Quote.query
        
        # 🔒 SECURITY: Apply user-based access control
        if current_user.role == 'admin':
            # Admin can access all quotes or filter by specific user
            if created_by and created_by != 'all':
                try:
                    query = query.filter(Quote.created_by == int(created_by))
                except ValueError:
                    return jsonify({'error': 'Invalid created_by value'}), 400
            # If no created_by or created_by='all', admin sees all quotes
        else:
            # 🔒 Non-admin users can only see their own quotes
            query = query.filter(Quote.created_by == current_user.id)
        
        # Search across multiple fields (SQLite compatible)
        if search and search.strip():
            search_term = f"%{search.strip().lower()}%"
            query = query.filter(
                db.or_(
                    func.lower(Quote.quote_number).like(search_term),
                    func.lower(Quote.customer_name).like(search_term),
                    func.lower(Quote.customer_email).like(search_term),
                    func.lower(Quote.customer_company).like(search_term)
                )
            )
        
        # Filter by status
        if status:
            try:
                status_enum = QuoteStatus(status)
                query = query.filter(Quote.status == status_enum)
            except ValueError:
                return jsonify({'error': 'Invalid status value'}), 400
        
        # Filter by customer email
        if customer_email:
            query = query.filter(Quote.customer_email.contains(customer_email))
        
        # Date range filters
        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                query = query.filter(Quote.created_at >= from_date)
            except ValueError:
                return jsonify({'error': 'Invalid date_from format. Use YYYY-MM-DD'}), 400
                
        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
                # Add one day to include the entire day
                to_date_end = datetime.combine(to_date, datetime.max.time())
                query = query.filter(Quote.created_at <= to_date_end)
            except ValueError:
                return jsonify({'error': 'Invalid date_to format. Use YYYY-MM-DD'}), 400
        
        # Amount filters
        if min_amount:
            try:
                query = query.filter(Quote.final_price >= float(min_amount))
            except ValueError:
                return jsonify({'error': 'Invalid min_amount value'}), 400
                
        if max_amount:
            try:
                query = query.filter(Quote.final_price <= float(max_amount))
            except ValueError:
                return jsonify({'error': 'Invalid max_amount value'}), 400
        
        # Note: User-based filtering already applied above for security
        
        # Sorting
        valid_sort_fields = ['created_at', 'total_price', 'customer_name', 'quote_number']
        if sort_by in valid_sort_fields:
            # Map total_price to final_price for single quotes
            if sort_by == 'total_price':
                sort_column = Quote.final_price
            else:
                sort_column = getattr(Quote, sort_by)
            
            if sort_order.lower() == 'asc':
                query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(sort_column.desc())
        else:
            # Default sorting
            query = query.order_by(Quote.created_at.desc())
        
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

@quotes_bp.route('/<int:quote_id>', methods=['GET'])
@jwt_required()
def get_quote(quote_id):
    """Get a specific quote."""
    try:
        quote = Quote.query.get(quote_id)
        if not quote:
            return jsonify({'error': '报价不存在'}), 404
            
        return jsonify({'quote': quote.to_dict()})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@quotes_bp.route('', methods=['POST'])
@jwt_required()
def create_quote():
    """Create a new quote."""
    try:
        # Get current user object (not just username)
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '用户认证失败'}), 401
        current_user_id = current_user.id
        
        # Validate request data
        schema = QuoteSchema()
        data = schema.load(request.json)
        
        # Verify product exists
        product = Product.query.get(data['product_id'])
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        if not product.is_active:
            return jsonify({'error': 'Product is not active'}), 400
        
        # Create new quote
        quote = Quote(
            customer_name=data['customer_name'],
            customer_email=data['customer_email'],
            customer_company=data.get('customer_company'),
            product_id=data['product_id'],
            quantity=data['quantity'],
            unit_price=product.base_price,
            discount_percentage=data['discount_percentage'],
            created_by=current_user_id,
            notes=data.get('notes'),
            valid_until=datetime.utcnow() + timedelta(days=30)  # Valid for 30 days
        )
        
        # Set configuration
        if 'configuration' in data:
            quote.set_configuration(data['configuration'])
        
        # Calculate pricing
        quote.calculate_pricing()
        
        # Save quote
        quote.save()
        
        # Generate quote number after saving (to get ID)
        quote.quote_number = quote.generate_quote_number()
        quote.save()
        
        return jsonify({
            'message': 'Quote created successfully',
            'quote': quote.to_dict()
        }), 201
        
    except ValidationError as err:
        return jsonify({'error': 'Validation error', 'details': err.messages}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@quotes_bp.route('/<int:quote_id>', methods=['PUT'])
@jwt_required()
def update_quote(quote_id):
    """Update a quote."""
    try:
        quote = Quote.query.get_or_404(quote_id)
        
        # Only allow updates for draft quotes
        if quote.status != QuoteStatus.DRAFT:
            return jsonify({'error': 'Only draft quotes can be updated'}), 400
        
        # Validate request data
        schema = QuoteSchema(partial=True)
        data = schema.load(request.json)
        
        # Update fields
        for key, value in data.items():
            if key == 'configuration':
                quote.set_configuration(value)
            elif key == 'product_id':
                # Verify new product exists
                product = Product.query.get(value)
                if not product or not product.is_active:
                    return jsonify({'error': 'Invalid product'}), 400
                quote.product_id = value
                quote.unit_price = product.base_price  # Update unit price
            else:
                setattr(quote, key, value)
        
        # Recalculate pricing
        quote.calculate_pricing()
        quote.save()
        
        return jsonify({
            'message': 'Quote updated successfully',
            'quote': quote.to_dict()
        })
        
    except ValidationError as err:
        return jsonify({'error': 'Validation error', 'details': err.messages}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@quotes_bp.route('/<int:quote_id>/status', methods=['PATCH'])
@jwt_required()
def update_quote_status(quote_id):
    """Update quote status."""
    try:
        # Get current user object (not just username)
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '用户认证失败'}), 401
        current_user_id = current_user.id
        quote = Quote.query.get_or_404(quote_id)
        
        status = request.json.get('status')
        if not status:
            return jsonify({'error': 'Status is required'}), 400
        
        try:
            new_status = QuoteStatus(status)
        except ValueError:
            return jsonify({'error': 'Invalid status value'}), 400
        
        # Update status
        quote.status = new_status
        
        # Set approver if approving
        if new_status == QuoteStatus.APPROVED:
            quote.approved_by = current_user_id
        
        quote.save()
        
        return jsonify({
            'message': 'Quote status updated successfully',
            'quote': quote.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@quotes_bp.route('/<int:quote_id>', methods=['DELETE'])
@jwt_required()
def delete_quote(quote_id):
    """Delete a quote."""
    try:
        # Get current user object (not just username)
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '用户认证失败'}), 401
        current_user_id = current_user.id
        
        # Use get() instead of get_or_404() to handle race conditions
        quote = Quote.query.get(quote_id)
        if not quote:
            return jsonify({'error': '报价不存在或已被删除'}), 404
        
        # Check permissions - only creator or admin can delete
        if quote.created_by != current_user_id:
            return jsonify({'error': '您没有权限删除这个报价'}), 403
        
        # Allow deletion of quotes in various statuses with appropriate warnings
        status_messages = {
            QuoteStatus.DRAFT: '草稿报价已删除',
            QuoteStatus.PENDING: '待审批报价已删除', 
            QuoteStatus.APPROVED: '已审批报价已删除',
            QuoteStatus.REJECTED: '已拒绝报价已删除',
            QuoteStatus.EXPIRED: '已过期报价已删除'
        }
        
        status_message = status_messages.get(quote.status, '报价已删除')
        
        # Store quote info for logging before deletion
        quote_number = quote.quote_number
        quote_status = quote.status.value
        
        try:
            quote.delete()
            
            # Log the deletion for audit purposes
            print(f"Single quote {quote_number} (status: {quote_status}) deleted by user {current_user_id}")
            
            return jsonify({
                'message': status_message,
                'quote_number': quote_number,
                'status': quote_status
            })
            
        except Exception as db_error:
            print(f"Database error deleting single quote {quote_id}: {str(db_error)}")
            return jsonify({'error': f'删除报价时发生数据库错误: {str(db_error)}'}), 500
        
    except Exception as e:
        print(f"Error deleting single quote {quote_id}: {str(e)}")
        return jsonify({'error': f'删除报价时发生错误: {str(e)}'}), 500