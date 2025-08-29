from .base import db, BaseModel
import json
from enum import Enum

class QuoteStatus(Enum):
    """Quote status enumeration."""
    DRAFT = 'draft'
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    EXPIRED = 'expired'

class Quote(BaseModel):
    """Quote model for CPQ system."""
    
    __tablename__ = 'quotes'
    
    quote_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(200), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    customer_company = db.Column(db.String(200))
    
    # Product and configuration
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    configuration = db.Column(db.Text)  # JSON for selected configuration
    quantity = db.Column(db.Integer, default=1, nullable=False)
    
    # Pricing
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    discount_percentage = db.Column(db.Numeric(5, 2), default=0)
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    final_price = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Status and validity
    status = db.Column(db.Enum(QuoteStatus), default=QuoteStatus.DRAFT, nullable=False)
    valid_until = db.Column(db.DateTime)
    
    # User relationships
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Additional information
    notes = db.Column(db.Text)
    terms_conditions = db.Column(db.Text)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_quotes')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_quotes')
    
    def get_configuration(self):
        """Get configuration as dict."""
        if self.configuration:
            return json.loads(self.configuration)
        return {}
    
    def set_configuration(self, config_dict):
        """Set configuration from dict."""
        self.configuration = json.dumps(config_dict)
    
    def calculate_pricing(self):
        """Calculate pricing based on configuration and quantity."""
        from decimal import Decimal, ROUND_HALF_UP
        # Basic calculation - can be extended with complex pricing rules
        total = self.unit_price * self.quantity
        discount_percent = Decimal(self.discount_percentage or 0)
        discount_amt = total * (discount_percent / Decimal('100'))
        
        # Round to 2 decimal places to match database precision
        self.total_price = total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.discount_amount = discount_amt.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.final_price = (total - discount_amt).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def generate_quote_number(self):
        """Generate unique quote number."""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"Q-{timestamp}-{str(self.id or '').zfill(4)}"
    
    def to_dict(self):
        """Convert quote to dictionary."""
        data = super().to_dict()
        data['configuration'] = self.get_configuration()
        data['status'] = self.status.value if self.status else None
        # Map final_price to total_price for frontend consistency
        data['total_price'] = float(self.final_price) if self.final_price else 0
        # Keep final_price for backward compatibility
        data['final_price'] = float(self.final_price) if self.final_price else 0
        return data
    
    def __repr__(self):
        return f'<Quote {self.quote_number}: {self.customer_name}>'