#!/usr/bin/env python3
"""
Database initialization script for CPQ System.
Creates tables and optionally seeds with sample data.
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Add the parent directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from src.models import db, User, Product, Quote, QuoteStatus

def init_database():
    """Initialize database with tables and sample data."""
    
    app = create_app()
    
    with app.app_context():
        print("🗄️  Initializing database...")
        
        # Drop all tables and recreate (for development)
        db.drop_all()
        db.create_all()
        
        print("✅ Database tables created successfully!")
        
        # Create sample data
        create_sample_data()
        
        print("🎉 Database initialization completed!")

def create_sample_data():
    """Create sample data for development and testing."""
    
    print("📝 Creating sample data...")
    
    # Create comprehensive sample users
    users_data = [
        {
            'username': 'admin',
            'email': 'admin@cpq-system.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'role': 'admin'
        },
        {
            'username': 'engineer',
            'email': 'engineer@cpq-system.com',
            'first_name': 'John',
            'last_name': 'Engineer',
            'role': 'engineer'
        },
        {
            'username': 'sales',
            'email': 'sales@cpq-system.com',
            'first_name': 'Jane',
            'last_name': 'Sales',
            'role': 'sales'
        },
        {
            'username': 'manager',
            'email': 'manager@cpq-system.com',
            'first_name': 'Mike',
            'last_name': 'Manager',
            'role': 'manager'
        }
    ]
    
    created_users = []
    for user_data in users_data:
        user = User(**user_data)
        user.set_password('password123')  # Consistent password for all users
        user.save()
        created_users.append(user)
        if user_data['username'] == 'admin':
            admin_user = user
    
    print("👥 Sample users created")
    
    # Create sample products
    products_data = [
        {
            'name': 'Industrial Motor 5HP',
            'code': 'IM-5HP-001',
            'description': 'High-efficiency industrial motor, 5 horsepower',
            'category': 'Motors',
            'base_price': 1299.99,
            'configuration_schema': {
                'voltage': {
                    'type': 'select',
                    'label': 'Voltage',
                    'options': ['220V', '380V', '440V'],
                    'required': True,
                    'price_modifier': {
                        '220V': 0,
                        '380V': 50,
                        '440V': 100
                    }
                },
                'mounting': {
                    'type': 'select',
                    'label': 'Mounting Type',
                    'options': ['Foot Mount', 'Flange Mount', 'Face Mount'],
                    'required': True,
                    'price_modifier': {
                        'Foot Mount': 0,
                        'Flange Mount': 75,
                        'Face Mount': 125
                    }
                },
                'protection': {
                    'type': 'select',
                    'label': 'Protection Class',
                    'options': ['IP54', 'IP55', 'IP65'],
                    'required': True,
                    'price_modifier': {
                        'IP54': 0,
                        'IP55': 25,
                        'IP65': 75
                    }
                }
            },
            'specifications': {
                'power': '5 HP (3.7 kW)',
                'speed': '1450 RPM',
                'efficiency': '92%',
                'weight': '45 kg',
                'dimensions': '400x300x250 mm'
            }
        },
        {
            'name': 'Industrial Motor 10HP',
            'code': 'IM-10HP-001',
            'description': 'High-efficiency industrial motor, 10 horsepower',
            'category': 'Motors',
            'base_price': 1899.99,
            'configuration_schema': {
                'voltage': {
                    'type': 'select',
                    'label': 'Voltage',
                    'options': ['380V', '440V', '660V'],
                    'required': True,
                    'price_modifier': {
                        '380V': 0,
                        '440V': 75,
                        '660V': 150
                    }
                },
                'mounting': {
                    'type': 'select',
                    'label': 'Mounting Type',
                    'options': ['Foot Mount', 'Flange Mount'],
                    'required': True,
                    'price_modifier': {
                        'Foot Mount': 0,
                        'Flange Mount': 100
                    }
                },
                'cooling': {
                    'type': 'select',
                    'label': 'Cooling Type',
                    'options': ['Air Cooled', 'Water Cooled'],
                    'required': True,
                    'price_modifier': {
                        'Air Cooled': 0,
                        'Water Cooled': 200
                    }
                }
            },
            'specifications': {
                'power': '10 HP (7.5 kW)',
                'speed': '1450 RPM',
                'efficiency': '93%',
                'weight': '65 kg',
                'dimensions': '500x350x300 mm'
            }
        },
        {
            'name': 'Variable Frequency Drive 5HP',
            'code': 'VFD-5HP-001',
            'description': 'Variable frequency drive for motor speed control',
            'category': 'Drives',
            'base_price': 899.99,
            'configuration_schema': {
                'input_voltage': {
                    'type': 'select',
                    'label': 'Input Voltage',
                    'options': ['220V Single Phase', '380V Three Phase', '440V Three Phase'],
                    'required': True,
                    'price_modifier': {
                        '220V Single Phase': 0,
                        '380V Three Phase': 50,
                        '440V Three Phase': 100
                    }
                },
                'communication': {
                    'type': 'multiselect',
                    'label': 'Communication Protocols',
                    'options': ['Modbus RTU', 'Ethernet/IP', 'Profibus', 'DeviceNet'],
                    'price_modifier': {
                        'Modbus RTU': 50,
                        'Ethernet/IP': 150,
                        'Profibus': 200,
                        'DeviceNet': 180
                    }
                },
                'display': {
                    'type': 'select',
                    'label': 'Display Type',
                    'options': ['LED', 'LCD', 'Touchscreen'],
                    'required': True,
                    'price_modifier': {
                        'LED': 0,
                        'LCD': 75,
                        'Touchscreen': 250
                    }
                }
            },
            'specifications': {
                'power_rating': '5 HP (3.7 kW)',
                'frequency_range': '0-400 Hz',
                'control_method': 'Vector Control',
                'efficiency': '97%',
                'dimensions': '200x150x120 mm'
            }
        }
    ]
    
    for product_data in products_data:
        product = Product(
            name=product_data['name'],
            code=product_data['code'],
            description=product_data['description'],
            category=product_data['category'],
            base_price=product_data['base_price']
        )
        product.set_configuration_schema(product_data['configuration_schema'])
        product.set_specifications(product_data['specifications'])
        product.save()
    
    print("🏭 Sample products created")
    
    # Create sample quotes
    products = Product.query.all()
    
    sample_quotes = [
        {
            'customer_name': 'John Manufacturing Co.',
            'customer_email': 'john@manufacturing.com',
            'customer_company': 'John Manufacturing Co.',
            'product': products[0],
            'configuration': {
                'voltage': '380V',
                'mounting': 'Flange Mount',
                'protection': 'IP65'
            },
            'quantity': 2,
            'status': QuoteStatus.PENDING
        },
        {
            'customer_name': 'Tech Industries Ltd.',
            'customer_email': 'procurement@techind.com',
            'customer_company': 'Tech Industries Ltd.',
            'product': products[1],
            'configuration': {
                'voltage': '440V',
                'mounting': 'Foot Mount',
                'cooling': 'Water Cooled'
            },
            'quantity': 1,
            'status': QuoteStatus.APPROVED
        },
        {
            'customer_name': 'Power Solutions Inc.',
            'customer_email': 'orders@powersol.com',
            'customer_company': 'Power Solutions Inc.',
            'product': products[2],
            'configuration': {
                'input_voltage': '380V Three Phase',
                'communication': ['Modbus RTU', 'Ethernet/IP'],
                'display': 'Touchscreen'
            },
            'quantity': 3,
            'status': QuoteStatus.DRAFT
        }
    ]
    
    for quote_data in sample_quotes:
        quote = Quote(
            quote_number=f"Q-TEMP-{hash(quote_data['customer_email'])}"[:20],  # Temporary quote number
            customer_name=quote_data['customer_name'],
            customer_email=quote_data['customer_email'],
            customer_company=quote_data['customer_company'],
            product_id=quote_data['product'].id,
            quantity=quote_data['quantity'],
            unit_price=quote_data['product'].base_price,
            status=quote_data['status'],
            created_by=admin_user.id,
            valid_until=datetime.utcnow() + timedelta(days=30)
        )
        quote.set_configuration(quote_data['configuration'])
        quote.calculate_pricing()
        quote.save()
        
        # Generate proper quote number after saving (to get ID)
        quote.quote_number = quote.generate_quote_number()
        quote.save()
    
    print("📋 Sample quotes created")
    print(f"✨ Created {len(products_data)} products, {len(users_data)} users, and {len(sample_quotes)} quotes")
    
    print("\n🔑 Login credentials:")
    print("| 角色 | 用户名 | 密码 | 权限范围 |")
    print("|------|-------|------|---------|")
    print("| **管理员** | admin | password123 | 全部功能 + 用户管理 |")
    print("| **工程师** | engineer | password123 | 产品管理 + 查看报价 |")
    print("| **销售人员** | sales | password123 | 创建报价 + 查看产品 |")
    print("| **经理** | manager | password123 | 查看报表 + 监督流程 |")

if __name__ == '__main__':
    init_database()