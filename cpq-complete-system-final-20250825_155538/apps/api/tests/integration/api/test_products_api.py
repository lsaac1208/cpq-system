"""Integration tests for Products API endpoints."""

import pytest
import json
from decimal import Decimal
from src.models.product import Product
from src.models.base import db


class TestProductsAPI:
    """Test Products API endpoints integration."""
    
    def test_get_products_success(self, client, auth_headers):
        """Test GET /api/products returns products list."""
        response = client.get('/api/products', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'products' in data
        assert 'pagination' in data
        assert isinstance(data['products'], list)
        assert 'page' in data['pagination']
        assert 'per_page' in data['pagination']
        assert 'total' in data['pagination']
        assert 'pages' in data['pagination']
    
    def test_get_products_with_filters(self, client, auth_headers, test_product):
        """Test GET /api/products with filters."""
        # Test category filter
        response = client.get(f'/api/products?category={test_product.category}', 
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert len(data['products']) > 0
        for product in data['products']:
            assert product['category'] == test_product.category
    
    def test_get_products_with_pagination(self, client, auth_headers):
        """Test GET /api/products with pagination parameters."""
        response = client.get('/api/products?page=1&per_page=5', 
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['pagination']['page'] == 1
        assert data['pagination']['per_page'] == 5
        assert len(data['products']) <= 5
    
    def test_get_products_unauthorized(self, client):
        """Test GET /api/products without authentication."""
        response = client.get('/api/products')
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'msg' in data or 'error' in data
    
    def test_get_product_success(self, client, auth_headers, test_product):
        """Test GET /api/products/<id> returns single product."""
        response = client.get(f'/api/products/{test_product.id}', 
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'product' in data
        assert data['product']['id'] == test_product.id
        assert data['product']['name'] == test_product.name
        assert data['product']['code'] == test_product.code
        assert data['product']['category'] == test_product.category
        assert 'configuration_schema' in data['product']
        assert 'specifications' in data['product']
    
    def test_get_product_not_found(self, client, auth_headers):
        """Test GET /api/products/<id> with non-existent product."""
        response = client.get('/api/products/99999', headers=auth_headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'msg' in data or 'error' in data
    
    def test_create_product_success(self, client, engineer_auth_headers):
        """Test POST /api/products creates new product."""
        product_data = {
            'name': 'New Test Product',
            'code': 'NEW-TEST-001',
            'description': 'A new test product',
            'category': 'New Category',
            'base_price': 1299.99,
            'configuration_schema': {
                'cpu': {
                    'type': 'select',
                    'options': ['Intel i5', 'Intel i7'],
                    'default': 'Intel i5'
                }
            },
            'specifications': {
                'weight': '3.0kg',
                'warranty': '1 year'
            },
            'is_active': True,
            'is_configurable': True
        }
        
        response = client.post('/api/products',
                             json=product_data,
                             headers=engineer_auth_headers,
                             content_type='application/json')
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert 'product' in data
        assert data['product']['name'] == product_data['name']
        assert data['product']['code'] == product_data['code']
        assert data['product']['category'] == product_data['category']
        assert data['product']['base_price'] == product_data['base_price']
        assert data['product']['configuration_schema'] == product_data['configuration_schema']
        assert data['product']['specifications'] == product_data['specifications']
        
        # Verify product was created in database
        product = db.session.query(Product).filter_by(code=product_data['code']).first()
        assert product is not None
        assert product.name == product_data['name']
    
    def test_create_product_missing_fields(self, client, engineer_auth_headers):
        """Test POST /api/products with missing required fields."""
        incomplete_data = {
            'name': 'Incomplete Product'
            # Missing required fields: code, category, base_price
        }
        
        response = client.post('/api/products',
                             json=incomplete_data,
                             headers=engineer_auth_headers,
                             content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'msg' in data or 'error' in data
    
    def test_create_product_duplicate_code(self, client, engineer_auth_headers, test_product):
        """Test POST /api/products with duplicate product code."""
        product_data = {
            'name': 'Duplicate Code Product',
            'code': test_product.code,  # Duplicate code
            'category': 'Test Category',
            'base_price': 999.99
        }
        
        response = client.post('/api/products',
                             json=product_data,
                             headers=engineer_auth_headers,
                             content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'msg' in data or 'error' in data
    
    def test_create_product_insufficient_permissions(self, client, auth_headers):
        """Test POST /api/products with insufficient permissions."""
        product_data = {
            'name': 'Unauthorized Product',
            'code': 'UNAUTH-001',
            'category': 'Test',
            'base_price': 999.99
        }
        
        response = client.post('/api/products',
                             json=product_data,
                             headers=auth_headers,  # Regular user, not engineer
                             content_type='application/json')
        
        assert response.status_code == 403
        data = response.get_json()
        assert 'msg' in data or 'error' in data
    
    def test_update_product_success(self, client, engineer_auth_headers, test_product):
        """Test PUT /api/products/<id> updates product."""
        update_data = {
            'name': 'Updated Product Name',
            'description': 'Updated description',
            'base_price': 1599.99
        }
        
        response = client.put(f'/api/products/{test_product.id}',
                            json=update_data,
                            headers=engineer_auth_headers,
                            content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'product' in data
        assert data['product']['name'] == update_data['name']
        assert data['product']['description'] == update_data['description']
        assert data['product']['base_price'] == update_data['base_price']
        
        # Verify product was updated in database
        updated_product = db.session.query(Product).get(test_product.id)
        assert updated_product.name == update_data['name']
        assert updated_product.description == update_data['description']
        assert updated_product.base_price == Decimal(str(update_data['base_price']))
    
    def test_update_product_not_found(self, client, engineer_auth_headers):
        """Test PUT /api/products/<id> with non-existent product."""
        update_data = {
            'name': 'Non-existent Product'
        }
        
        response = client.put('/api/products/99999',
                            json=update_data,
                            headers=engineer_auth_headers,
                            content_type='application/json')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'msg' in data or 'error' in data
    
    def test_update_product_insufficient_permissions(self, client, auth_headers, test_product):
        """Test PUT /api/products/<id> with insufficient permissions."""
        update_data = {
            'name': 'Unauthorized Update'
        }
        
        response = client.put(f'/api/products/{test_product.id}',
                            json=update_data,
                            headers=auth_headers,  # Regular user, not engineer
                            content_type='application/json')
        
        assert response.status_code == 403
        data = response.get_json()
        assert 'msg' in data or 'error' in data
    
    def test_delete_product_success(self, client, engineer_auth_headers, test_product):
        """Test DELETE /api/products/<id> marks product as inactive."""
        response = client.delete(f'/api/products/{test_product.id}',
                               headers=engineer_auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        
        # Verify product was marked as inactive in database
        product = db.session.query(Product).get(test_product.id)
        assert product is not None  # Still exists
        assert product.is_active is False  # But marked inactive
    
    def test_delete_product_not_found(self, client, engineer_auth_headers):
        """Test DELETE /api/products/<id> with non-existent product."""
        response = client.delete('/api/products/99999',
                               headers=engineer_auth_headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'msg' in data or 'error' in data
    
    def test_delete_product_insufficient_permissions(self, client, auth_headers, test_product):
        """Test DELETE /api/products/<id> with insufficient permissions."""
        response = client.delete(f'/api/products/{test_product.id}',
                               headers=auth_headers)  # Regular user, not engineer
        
        assert response.status_code == 403
        data = response.get_json()
        assert 'msg' in data or 'error' in data
    
    def test_get_categories_success(self, client, auth_headers, test_product):
        """Test GET /api/products/categories returns unique categories."""
        response = client.get('/api/products/categories', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'categories' in data
        assert isinstance(data['categories'], list)
        assert test_product.category in data['categories']
    
    def test_product_search(self, client, auth_headers, test_product):
        """Test product search functionality."""
        # Search by name
        response = client.get(f'/api/products?search={test_product.name[:5]}',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should find the test product
        found = False
        for product in data['products']:
            if product['id'] == test_product.id:
                found = True
                break
        assert found
    
    def test_product_json_fields_handling(self, client, engineer_auth_headers):
        """Test handling of JSON fields in product creation and retrieval."""
        complex_schema = {
            'hardware': {
                'cpu': {
                    'type': 'select',
                    'options': [
                        {'name': 'Intel i5', 'price': 0},
                        {'name': 'Intel i7', 'price': 200}
                    ]
                },
                'memory': {
                    'type': 'multiselect',
                    'options': ['8GB', '16GB', '32GB']
                }
            }
        }
        
        complex_specs = {
            'dimensions': {
                'width': '30cm',
                'height': '20cm',
                'depth': '5cm'
            },
            'connectivity': ['USB-C', 'HDMI', 'WiFi'],
            'certifications': {
                'safety': ['CE', 'FCC'],
                'environmental': ['Energy Star']
            }
        }
        
        product_data = {
            'name': 'Complex Product',
            'code': 'COMPLEX-001',
            'category': 'Advanced',
            'base_price': 2499.99,
            'configuration_schema': complex_schema,
            'specifications': complex_specs
        }
        
        # Create product
        response = client.post('/api/products',
                             json=product_data,
                             headers=engineer_auth_headers,
                             content_type='application/json')
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Verify complex JSON fields are properly handled
        assert data['product']['configuration_schema'] == complex_schema
        assert data['product']['specifications'] == complex_specs
        
        # Retrieve product and verify JSON fields persist
        product_id = data['product']['id']
        response = client.get(f'/api/products/{product_id}',
                            headers=engineer_auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['product']['configuration_schema'] == complex_schema
        assert data['product']['specifications'] == complex_specs
    
    def test_product_price_precision(self, client, engineer_auth_headers):
        """Test decimal precision handling for product prices."""
        product_data = {
            'name': 'Precision Price Product',
            'code': 'PRECISION-001',
            'category': 'Testing',
            'base_price': 1234.567  # Should be rounded to 2 decimal places
        }
        
        response = client.post('/api/products',
                             json=product_data,
                             headers=engineer_auth_headers,
                             content_type='application/json')
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Price should be properly formatted with 2 decimal places
        assert data['product']['base_price'] == 1234.57  # Rounded
    
    def test_product_activation_status(self, client, engineer_auth_headers, test_product):
        """Test product activation/deactivation."""
        # Deactivate product
        response = client.put(f'/api/products/{test_product.id}',
                            json={'is_active': False},
                            headers=engineer_auth_headers,
                            content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['product']['is_active'] is False
        
        # Test filter by active status
        response = client.get('/api/products?is_active=false',
                            headers=engineer_auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should include the deactivated product
        found = False
        for product in data['products']:
            if product['id'] == test_product.id:
                found = True
                assert product['is_active'] is False
                break
        assert found