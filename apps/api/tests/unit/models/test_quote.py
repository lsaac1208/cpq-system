"""Unit tests for Quote model."""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from src.models.quote import Quote, QuoteStatus
from src.models.base import db


class TestQuoteModel:
    """Test Quote model functionality."""
    
    def test_quote_creation(self, db_session, test_product, test_user, sample_quote_data):
        """Test creating a new quote."""
        quote = Quote(
            quote_number=sample_quote_data['quote_number'],
            customer_name=sample_quote_data['customer_name'],
            customer_email=sample_quote_data['customer_email'],
            customer_company=sample_quote_data['customer_company'],
            product_id=test_product.id,
            quantity=sample_quote_data['quantity'],
            unit_price=sample_quote_data['unit_price'],
            total_price=sample_quote_data['total_price'],
            discount_percentage=sample_quote_data['discount_percentage'],
            discount_amount=sample_quote_data['discount_amount'],
            final_price=sample_quote_data['final_price'],
            status=sample_quote_data['status'],
            valid_until=sample_quote_data['valid_until'],
            created_by=test_user.id,
            notes=sample_quote_data['notes'],
            terms_conditions=sample_quote_data['terms_conditions']
        )
        
        db.session.add(quote)
        db.session.commit()
        
        assert quote.id is not None
        assert quote.quote_number == sample_quote_data['quote_number']
        assert quote.customer_name == sample_quote_data['customer_name']
        assert quote.customer_email == sample_quote_data['customer_email']
        assert quote.customer_company == sample_quote_data['customer_company']
        assert quote.product_id == test_product.id
        assert quote.quantity == sample_quote_data['quantity']
        assert quote.unit_price == sample_quote_data['unit_price']
        assert quote.status == sample_quote_data['status']
        assert quote.created_by == test_user.id
        assert quote.created_at is not None
        assert quote.updated_at is not None
    
    def test_configuration_methods(self, sample_quote_data, test_product, test_user):
        """Test configuration getter and setter methods."""
        quote = Quote(
            quote_number=sample_quote_data['quote_number'],
            customer_name=sample_quote_data['customer_name'], 
            customer_email=sample_quote_data['customer_email'],
            product_id=test_product.id,
            quantity=sample_quote_data['quantity'],
            unit_price=sample_quote_data['unit_price'],
            total_price=sample_quote_data['total_price'],
            final_price=sample_quote_data['final_price'],
            created_by=test_user.id
        )
        
        # Test setting configuration
        config = sample_quote_data['configuration']
        quote.set_configuration(config)
        
        # Verify it's stored as JSON string
        assert quote.configuration is not None
        assert isinstance(quote.configuration, str)
        
        # Test getting configuration
        retrieved_config = quote.get_configuration()
        assert retrieved_config == config
        assert isinstance(retrieved_config, dict)
    
    def test_empty_configuration(self, test_product, test_user):
        """Test behavior with empty configuration."""
        quote = Quote(
            quote_number='Q-TEST-001',
            customer_name='Test Customer',
            customer_email='test@example.com',
            product_id=test_product.id,
            quantity=1,
            unit_price=Decimal('100.00'),
            total_price=Decimal('100.00'),
            final_price=Decimal('100.00'),
            created_by=test_user.id
        )
        
        # Test empty configuration
        assert quote.get_configuration() == {}
    
    def test_calculate_pricing_basic(self, test_product, test_user):
        """Test basic pricing calculation."""
        quote = Quote(
            quote_number='Q-TEST-002',
            customer_name='Test Customer',
            customer_email='test@example.com',
            product_id=test_product.id,
            quantity=3,
            unit_price=Decimal('100.00'),
            discount_percentage=Decimal('10.00'),
            created_by=test_user.id
        )
        
        quote.calculate_pricing()
        
        assert quote.total_price == Decimal('300.00')  # 100 * 3
        assert quote.discount_amount == Decimal('30.00')  # 300 * 0.10
        assert quote.final_price == Decimal('270.00')  # 300 - 30
    
    def test_calculate_pricing_no_discount(self, test_product, test_user):
        """Test pricing calculation without discount."""
        quote = Quote(
            quote_number='Q-TEST-003',
            customer_name='Test Customer',
            customer_email='test@example.com',
            product_id=test_product.id,
            quantity=2,
            unit_price=Decimal('250.50'),
            created_by=test_user.id
        )
        
        quote.calculate_pricing()
        
        assert quote.total_price == Decimal('501.00')  # 250.50 * 2
        assert quote.discount_amount == Decimal('0.00')
        assert quote.final_price == Decimal('501.00')
    
    def test_calculate_pricing_with_decimal_precision(self, test_product, test_user):
        """Test pricing calculation with decimal precision."""
        quote = Quote(
            quote_number='Q-TEST-004',
            customer_name='Test Customer',
            customer_email='test@example.com',
            product_id=test_product.id,
            quantity=3,
            unit_price=Decimal('33.33'),
            discount_percentage=Decimal('15.75'),
            created_by=test_user.id
        )
        
        quote.calculate_pricing()
        
        assert quote.total_price == Decimal('99.99')  # 33.33 * 3
        expected_discount = Decimal('99.99') * (Decimal('15.75') / Decimal('100'))
        assert quote.discount_amount == expected_discount.quantize(Decimal('0.01'))
        assert quote.final_price == quote.total_price - quote.discount_amount
    
    def test_generate_quote_number_format(self, test_quote):
        """Test quote number generation format."""
        quote_number = test_quote.generate_quote_number()
        
        # Should start with 'Q-'
        assert quote_number.startswith('Q-')
        
        # Should contain timestamp and ID parts
        parts = quote_number.split('-')
        assert len(parts) == 3
        assert parts[0] == 'Q'
        assert len(parts[1]) == 14  # YYYYMMDDHHMMSS format
        assert len(parts[2]) == 4   # 4-digit ID with zero padding
    
    def test_quote_status_enum(self, db_session, test_product, test_user):
        """Test quote status enumeration."""
        quote = Quote(
            quote_number='Q-TEST-005',
            customer_name='Test Customer',
            customer_email='test@example.com',
            product_id=test_product.id,
            quantity=1,
            unit_price=Decimal('100.00'),
            total_price=Decimal('100.00'),
            final_price=Decimal('100.00'),
            created_by=test_user.id
        )
        
        # Save to database to apply default values
        db.session.add(quote)
        db.session.commit()
        
        # Test default status
        assert quote.status == QuoteStatus.DRAFT
        
        # Test setting different statuses
        quote.status = QuoteStatus.PENDING
        assert quote.status == QuoteStatus.PENDING
        
        quote.status = QuoteStatus.APPROVED
        assert quote.status == QuoteStatus.APPROVED
        
        quote.status = QuoteStatus.REJECTED
        assert quote.status == QuoteStatus.REJECTED
        
        quote.status = QuoteStatus.EXPIRED
        assert quote.status == QuoteStatus.EXPIRED
    
    def test_to_dict_method(self, test_quote):
        """Test to_dict method includes all fields properly."""
        quote_dict = test_quote.to_dict()
        
        assert 'id' in quote_dict
        assert 'quote_number' in quote_dict
        assert 'customer_name' in quote_dict
        assert 'customer_email' in quote_dict
        assert 'customer_company' in quote_dict
        assert 'product_id' in quote_dict
        assert 'configuration' in quote_dict
        assert 'quantity' in quote_dict
        assert 'unit_price' in quote_dict
        assert 'total_price' in quote_dict
        assert 'discount_percentage' in quote_dict
        assert 'discount_amount' in quote_dict
        assert 'final_price' in quote_dict
        assert 'status' in quote_dict
        assert 'valid_until' in quote_dict
        assert 'created_by' in quote_dict
        assert 'notes' in quote_dict
        assert 'terms_conditions' in quote_dict
        assert 'created_at' in quote_dict
        assert 'updated_at' in quote_dict
        
        # Check that configuration is properly parsed
        assert isinstance(quote_dict['configuration'], dict)
        
        # Check that status is converted to string value
        assert quote_dict['status'] == test_quote.status.value
    
    def test_quote_repr(self, test_quote):
        """Test quote string representation."""
        repr_str = repr(test_quote)
        expected = f'<Quote {test_quote.quote_number}: {test_quote.customer_name}>'
        assert repr_str == expected
    
    def test_unique_quote_number_constraint(self, db_session, test_product, test_user):
        """Test unique constraint for quote number."""
        quote_number = 'Q-UNIQUE-TEST-001'
        
        # Create first quote
        quote1 = Quote(
            quote_number=quote_number,
            customer_name='Customer 1',
            customer_email='customer1@example.com',
            product_id=test_product.id,
            quantity=1,
            unit_price=Decimal('100.00'),
            total_price=Decimal('100.00'),
            final_price=Decimal('100.00'),
            created_by=test_user.id
        )
        db.session.add(quote1)
        db.session.commit()
        
        # Try to create second quote with same number
        quote2 = Quote(
            quote_number=quote_number,  # Same quote number
            customer_name='Customer 2',
            customer_email='customer2@example.com',
            product_id=test_product.id,
            quantity=1,
            unit_price=Decimal('200.00'),
            total_price=Decimal('200.00'),
            final_price=Decimal('200.00'),
            created_by=test_user.id
        )
        db.session.add(quote2)
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            db.session.commit()
    
    def test_quote_relationships(self, test_quote, test_product, test_user):
        """Test quote relationships with product and user."""
        # Test product relationship
        assert test_quote.product is not None
        assert test_quote.product.id == test_product.id
        assert test_quote.product.name == test_product.name
        
        # Test creator relationship
        assert test_quote.creator is not None
        assert test_quote.creator.id == test_user.id
        assert test_quote.creator.username == test_user.username
    
    def test_default_values(self, db_session, test_product, test_user):
        """Test default values for optional fields."""
        quote = Quote(
            quote_number='Q-DEFAULT-001',
            customer_name='Test Customer',
            customer_email='test@example.com',
            product_id=test_product.id,
            unit_price=Decimal('100.00'),
            total_price=Decimal('100.00'),
            final_price=Decimal('100.00'),
            created_by=test_user.id
        )
        
        db.session.add(quote)
        db.session.commit()
        
        assert quote.quantity == 1  # Default quantity
        assert quote.status == QuoteStatus.DRAFT  # Default status
        assert quote.discount_percentage == Decimal('0')  # Default discount
        assert quote.discount_amount == Decimal('0')  # Default discount amount
        assert quote.customer_company is None
        assert quote.configuration is None
        assert quote.valid_until is None
        assert quote.approved_by is None
        assert quote.notes is None
        assert quote.terms_conditions is None
    
    def test_complex_configuration(self, db_session, test_product, test_user):
        """Test complex configuration with nested structures."""
        complex_config = {
            'hardware': {
                'cpu': 'Intel i7-12700K',
                'memory': '32GB DDR4',
                'storage': '1TB NVMe SSD',
                'gpu': 'NVIDIA RTX 4070'
            },
            'software': {
                'os': 'Windows 11 Pro',
                'office': 'Microsoft Office 365',
                'antivirus': 'Windows Defender'
            },
            'services': {
                'warranty': '3 Year Premium',
                'support': '24/7 Phone Support',
                'installation': 'On-site Setup'
            },
            'customizations': [
                'Custom Logo Engraving',
                'Additional USB Ports',
                'Upgraded Cooling System'
            ]
        }
        
        quote = Quote(
            quote_number='Q-COMPLEX-001',
            customer_name='Enterprise Customer',
            customer_email='enterprise@example.com',
            product_id=test_product.id,
            quantity=1,
            unit_price=Decimal('3999.99'),
            total_price=Decimal('3999.99'),
            final_price=Decimal('3999.99'),
            created_by=test_user.id
        )
        quote.set_configuration(complex_config)
        
        db.session.add(quote)
        db.session.commit()
        
        # Retrieve and verify complex configuration
        retrieved_config = quote.get_configuration()
        assert retrieved_config == complex_config
        assert 'hardware' in retrieved_config
        assert 'software' in retrieved_config
        assert 'services' in retrieved_config
        assert 'customizations' in retrieved_config
        assert retrieved_config['hardware']['cpu'] == 'Intel i7-12700K'
        assert len(retrieved_config['customizations']) == 3