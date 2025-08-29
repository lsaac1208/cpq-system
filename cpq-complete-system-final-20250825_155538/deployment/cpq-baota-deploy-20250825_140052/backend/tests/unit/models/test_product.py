"""Unit tests for Product model."""

import pytest
import json
from decimal import Decimal
from src.models.product import Product
from src.models.base import db


class TestProductModel:
    """Test Product model functionality."""
    
    def test_product_creation(self, db_session, sample_product_data):
        """Test creating a new product."""
        product = Product(
            name=sample_product_data['name'],
            code=sample_product_data['code'],
            description=sample_product_data['description'],
            category=sample_product_data['category'],
            base_price=sample_product_data['base_price'],
            is_active=sample_product_data['is_active'],
            is_configurable=sample_product_data['is_configurable']
        )
        
        db.session.add(product)
        db.session.commit()
        
        assert product.id is not None
        assert product.name == sample_product_data['name']
        assert product.code == sample_product_data['code']
        assert product.description == sample_product_data['description']
        assert product.category == sample_product_data['category']
        assert product.base_price == sample_product_data['base_price']
        assert product.is_active == sample_product_data['is_active']
        assert product.is_configurable == sample_product_data['is_configurable']
        assert product.created_at is not None
        assert product.updated_at is not None
    
    def test_configuration_schema_methods(self, sample_product_data):
        """Test configuration schema getter and setter methods."""
        product = Product(
            name=sample_product_data['name'],
            code=sample_product_data['code'],
            category=sample_product_data['category'],
            base_price=sample_product_data['base_price']
        )
        
        # Test setting configuration schema
        schema = sample_product_data['configuration_schema']
        product.set_configuration_schema(schema)
        
        # Verify it's stored as JSON string
        assert product.configuration_schema is not None
        assert isinstance(product.configuration_schema, str)
        
        # Test getting configuration schema
        retrieved_schema = product.get_configuration_schema()
        assert retrieved_schema == schema
        assert isinstance(retrieved_schema, dict)
    
    def test_specifications_methods(self, sample_product_data):
        """Test specifications getter and setter methods."""
        product = Product(
            name=sample_product_data['name'],
            code=sample_product_data['code'],
            category=sample_product_data['category'],
            base_price=sample_product_data['base_price']
        )
        
        # Test setting specifications
        specs = sample_product_data['specifications']
        product.set_specifications(specs)
        
        # Verify it's stored as JSON string
        assert product.specifications is not None
        assert isinstance(product.specifications, str)
        
        # Test getting specifications
        retrieved_specs = product.get_specifications()
        assert retrieved_specs == specs
        assert isinstance(retrieved_specs, dict)
    
    def test_empty_json_fields(self):
        """Test behavior with empty JSON fields."""
        product = Product(
            name='Test Product',
            code='TEST-002',
            category='Testing',
            base_price=Decimal('100.00')
        )
        
        # Test empty configuration schema
        assert product.get_configuration_schema() == {}
        
        # Test empty specifications
        assert product.get_specifications() == {}
    
    def test_to_dict_method(self, test_product):
        """Test to_dict method includes JSON fields."""
        product_dict = test_product.to_dict()
        
        assert 'id' in product_dict
        assert 'name' in product_dict
        assert 'code' in product_dict
        assert 'description' in product_dict
        assert 'category' in product_dict
        assert 'base_price' in product_dict
        assert 'configuration_schema' in product_dict
        assert 'specifications' in product_dict
        assert 'is_active' in product_dict
        assert 'is_configurable' in product_dict
        assert 'created_at' in product_dict
        assert 'updated_at' in product_dict
        
        # Check that JSON fields are properly parsed
        assert isinstance(product_dict['configuration_schema'], dict)
        assert isinstance(product_dict['specifications'], dict)
    
    def test_product_repr(self, test_product):
        """Test product string representation."""
        repr_str = repr(test_product)
        expected = f'<Product {test_product.code}: {test_product.name}>'
        assert repr_str == expected
    
    def test_unique_code_constraint(self, db_session, sample_product_data):
        """Test unique constraint for product code."""
        # Create first product
        product1 = Product(
            name=sample_product_data['name'],
            code=sample_product_data['code'],
            category=sample_product_data['category'],
            base_price=sample_product_data['base_price']
        )
        db.session.add(product1)
        db.session.commit()
        
        # Try to create second product with same code
        product2 = Product(
            name='Different Product',
            code=sample_product_data['code'],  # Same code
            category='Different Category',
            base_price=Decimal('200.00')
        )
        db.session.add(product2)
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            db.session.commit()
    
    def test_default_values(self, db_session):
        """Test default values for optional fields."""
        product = Product(
            name='Test Product',
            code='TEST-003',
            category='Testing',
            base_price=Decimal('100.00')
        )
        
        db.session.add(product)
        db.session.commit()
        
        assert product.is_active is True
        assert product.is_configurable is True
        assert product.description is None
        assert product.configuration_schema is None
        assert product.specifications is None
    
    def test_decimal_precision(self, db_session):
        """Test decimal precision for base_price."""
        product = Product(
            name='Precision Test',
            code='PRECISION-001',
            category='Testing',
            base_price=Decimal('999.99')
        )
        
        db.session.add(product)
        db.session.commit()
        
        # Retrieve and check precision
        retrieved_product = db.session.query(Product).filter_by(code='PRECISION-001').first()
        assert retrieved_product.base_price == Decimal('999.99')
    
    def test_json_serialization_error_handling(self):
        """Test error handling for invalid JSON in configuration schema."""
        product = Product(
            name='Test Product',
            code='TEST-004',
            category='Testing',
            base_price=Decimal('100.00')
        )
        
        # Set invalid JSON manually
        product.configuration_schema = 'invalid json'
        
        # Should handle JSON decode error gracefully
        with pytest.raises(json.JSONDecodeError):
            product.get_configuration_schema()
    
    def test_complex_configuration_schema(self, db_session):
        """Test complex configuration schema with nested structures."""
        complex_schema = {
            'hardware': {
                'cpu': {
                    'type': 'select',
                    'options': [
                        {'name': 'Intel i5', 'price': 0, 'specs': {'cores': 4, 'ghz': 3.2}},
                        {'name': 'Intel i7', 'price': 200, 'specs': {'cores': 8, 'ghz': 3.8}},
                        {'name': 'AMD Ryzen 5', 'price': 150, 'specs': {'cores': 6, 'ghz': 3.6}}
                    ],
                    'default': 0
                },
                'memory': {
                    'type': 'multiselect',
                    'options': ['8GB', '16GB', '32GB', '64GB'],
                    'price_per_unit': [0, 300, 800, 1800],
                    'max_selection': 4
                }
            },
            'software': {
                'os': {
                    'type': 'radio',
                    'options': ['Windows', 'macOS', 'Linux'],
                    'prices': [0, 100, 0],
                    'default': 'Windows'
                }
            },
            'services': {
                'warranty': {
                    'type': 'checkbox',
                    'options': [
                        {'name': '1 Year Standard', 'price': 0},
                        {'name': '2 Year Extended', 'price': 200},
                        {'name': '3 Year Premium', 'price': 500}
                    ]
                }
            }
        }
        
        product = Product(
            name='Complex Product',
            code='COMPLEX-001',
            category='High-End',
            base_price=Decimal('2999.99')
        )
        product.set_configuration_schema(complex_schema)
        
        db.session.add(product)
        db.session.commit()
        
        # Retrieve and verify complex schema
        retrieved_schema = product.get_configuration_schema()
        assert retrieved_schema == complex_schema
        assert 'hardware' in retrieved_schema
        assert 'software' in retrieved_schema
        assert 'services' in retrieved_schema
        assert retrieved_schema['hardware']['cpu']['options'][0]['specs']['cores'] == 4