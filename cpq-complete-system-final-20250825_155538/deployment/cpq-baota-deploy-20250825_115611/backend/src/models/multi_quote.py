from .base import db, BaseModel
import json
from enum import Enum
from datetime import datetime
from decimal import Decimal

class MultiQuoteStatus(Enum):
    """Multi-product quote status enumeration."""
    DRAFT = 'draft'
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    EXPIRED = 'expired'

class MultiQuote(BaseModel):
    """Multi-product quote model for CPQ system."""
    
    __tablename__ = 'multi_quotes'
    
    quote_number = db.Column(db.String(50), unique=True, nullable=False)
    version = db.Column(db.Integer, default=1, nullable=False)
    
    # Customer information
    customer_name = db.Column(db.String(200), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    customer_company = db.Column(db.String(200))
    customer_phone = db.Column(db.String(50))
    customer_address = db.Column(db.Text)
    
    # Pricing totals
    subtotal = db.Column(db.Numeric(12, 2), default=0)
    discount_percentage = db.Column(db.Numeric(5, 2), default=0)
    discount_amount = db.Column(db.Numeric(12, 2), default=0)
    tax_percentage = db.Column(db.Numeric(5, 2), default=0)
    tax_amount = db.Column(db.Numeric(12, 2), default=0)
    total_price = db.Column(db.Numeric(12, 2), default=0)
    
    # Status and validity
    status = db.Column(db.Enum(MultiQuoteStatus), default=MultiQuoteStatus.DRAFT, nullable=False)
    valid_until = db.Column(db.Date)
    
    # Additional information
    notes = db.Column(db.Text)
    terms_conditions = db.Column(db.Text)
    
    # User relationships
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by_user = db.relationship('User', foreign_keys=[created_by], backref='created_multi_quotes')
    
    # Relationships
    items = db.relationship('MultiQuoteItem', backref='quote', cascade='all, delete-orphan')
    
    def generate_quote_number(self):
        """Generate a unique quote number."""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        if self.id:
            return f"MQ-{timestamp}-{self.id:04d}"
        else:
            # Use a random number if ID is not available yet
            import random
            return f"MQ-{timestamp}-{random.randint(1000, 9999)}"
    
    def calculate_totals(self):
        """Calculate quote totals from items."""
        self.subtotal = sum(item.line_total for item in self.items)
        
        # Apply quote-level discount
        if self.discount_percentage:
            self.discount_amount = self.subtotal * (self.discount_percentage / 100)
        else:
            self.discount_amount = 0
        
        # Calculate tax on discounted subtotal
        taxable_amount = self.subtotal - self.discount_amount
        if self.tax_percentage:
            self.tax_amount = taxable_amount * (self.tax_percentage / 100)
        else:
            self.tax_amount = 0
        
        # Final total
        self.total_price = taxable_amount + self.tax_amount
    
    def to_dict(self):
        """Convert quote to dictionary for JSON response."""
        try:
            # Safely get created_by_user info
            created_by_user_data = None
            try:
                if self.created_by_user:
                    created_by_user_data = self.created_by_user.to_dict()
            except Exception:
                created_by_user_data = None
            
            # Safely get items info
            items_data = []
            try:
                items_data = [item.to_dict() for item in self.items]
            except Exception:
                items_data = []
            
            return {
                'id': self.id,
                'quote_number': self.quote_number,
                'version': self.version,
                'customer_name': self.customer_name,
                'customer_email': self.customer_email,
                'customer_company': self.customer_company,
                'customer_phone': self.customer_phone,
                'customer_address': self.customer_address,
                'subtotal': float(self.subtotal) if self.subtotal else 0,
                'discount_percentage': float(self.discount_percentage) if self.discount_percentage else 0,
                'discount_amount': float(self.discount_amount) if self.discount_amount else 0,
                'tax_percentage': float(self.tax_percentage) if self.tax_percentage else 0,
                'tax_amount': float(self.tax_amount) if self.tax_amount else 0,
                'total_price': float(self.total_price) if self.total_price else 0,
                'status': self.status.value,
                'valid_until': self.valid_until.isoformat() if self.valid_until else None,
                'notes': self.notes,
                'terms_conditions': self.terms_conditions,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'created_by_user': created_by_user_data,
                'items': items_data
            }
        except Exception as e:
            # Fallback minimal dict if there are any issues
            return {
                'id': self.id,
                'quote_number': getattr(self, 'quote_number', None),
                'status': self.status.value if hasattr(self, 'status') and self.status else None,
                'customer_name': getattr(self, 'customer_name', None),
                'error': 'Data access error in to_dict()'
            }

class MultiQuoteItem(BaseModel):
    """Individual items in a multi-product quote."""
    
    __tablename__ = 'multi_quote_items'
    
    quote_id = db.Column(db.Integer, db.ForeignKey('multi_quotes.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    # Item details
    quantity = db.Column(db.Integer, default=1, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    discount_percentage = db.Column(db.Numeric(5, 2), default=0)
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    line_total = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Additional information
    notes = db.Column(db.Text)
    
    # Relationships
    product = db.relationship('Product', backref='quote_items')
    
    def calculate_totals(self):
        """Calculate line item totals."""
        subtotal = self.quantity * self.unit_price
        
        if self.discount_percentage:
            self.discount_amount = subtotal * (self.discount_percentage / 100)
        else:
            self.discount_amount = 0
            
        self.line_total = subtotal - self.discount_amount
    
    def to_dict(self):
        """Convert item to dictionary for JSON response."""
        return {
            'id': self.id,
            'quote_id': self.quote_id,
            'product_id': self.product_id,
            'product': self.product.to_dict() if self.product else None,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'discount_percentage': float(self.discount_percentage) if self.discount_percentage else 0,
            'discount_amount': float(self.discount_amount) if self.discount_amount else 0,
            'line_total': float(self.line_total),
            'notes': self.notes
        }