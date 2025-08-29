#!/usr/bin/env python3
"""
Seed script to populate the database with sample data for testing.
"""

import sys
import os
import json

# Add the parent directory to Python path to import modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from app import create_app
from src.models import db, User, Product

def create_sample_users():
    """Create sample users with different roles."""
    users_data = [
        {
            'username': 'admin',
            'email': 'admin@cpq.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'role': 'admin'
        },
        {
            'username': 'engineer',
            'email': 'engineer@cpq.com',
            'first_name': 'John',
            'last_name': 'Engineer',
            'role': 'engineer'
        },
        {
            'username': 'sales',
            'email': 'sales@cpq.com',
            'first_name': 'Jane',
            'last_name': 'Sales',
            'role': 'sales'
        },
        {
            'username': 'manager',
            'email': 'manager@cpq.com',
            'first_name': 'Mike',
            'last_name': 'Manager',
            'role': 'manager'
        }
    ]
    
    for user_data in users_data:
        # Check if user already exists
        existing_user = User.query.filter_by(username=user_data['username']).first()
        if not existing_user:
            user = User(**user_data)
            user.set_password('password123')  # Default password for all test users
            user.save()
            print(f"Created user: {user_data['username']} ({user_data['role']})")
        else:
            print(f"User already exists: {user_data['username']}")

def create_sample_products():
    """Create sample products with specifications and configuration schemas."""
    
    products_data = [
        {
            'name': 'Industrial Server Rack',
            'code': 'ISR-001',
            'description': 'High-performance server rack for industrial applications',
            'category': 'Server Hardware',
            'base_price': 5999.99,
            'specifications': {
                'height': {'value': '42U', 'unit': 'units', 'description': 'Standard rack height'},
                'depth': {'value': '1000', 'unit': 'mm', 'description': 'Rack depth'},
                'max_weight': {'value': '1500', 'unit': 'kg', 'description': 'Maximum load capacity'},
                'power_supply': {'value': '220V', 'unit': 'volts', 'description': 'Power supply voltage'},
                'cooling': {'value': 'Active', 'description': 'Built-in cooling system'}
            },
            'configuration_schema': {
                'color': {
                    'type': 'select',
                    'label': 'Rack Color',
                    'description': 'Color of the server rack',
                    'required': True,
                    'default': 'black',
                    'options': [
                        {'label': 'Black', 'value': 'black'},
                        {'label': 'White', 'value': 'white'},
                        {'label': 'Gray', 'value': 'gray'}
                    ]
                },
                'cable_management': {
                    'type': 'boolean',
                    'label': 'Cable Management System',
                    'description': 'Include advanced cable management',
                    'required': False,
                    'default': True
                },
                'extra_fans': {
                    'type': 'number',
                    'label': 'Additional Cooling Fans',
                    'description': 'Number of extra cooling fans',
                    'required': False,
                    'default': 0,
                    'validation': {'min': 0, 'max': 8}
                }
            },
            'is_active': True,
            'is_configurable': True
        },
        {
            'name': 'Network Switch 24-Port',
            'code': 'NS-24P',
            'description': '24-port managed Gigabit Ethernet switch',
            'category': 'Network Equipment',
            'base_price': 899.99,
            'specifications': {
                'ports': {'value': '24', 'unit': 'ports', 'description': 'Gigabit Ethernet ports'},
                'speed': {'value': '1000', 'unit': 'Mbps', 'description': 'Port speed'},
                'poe_support': {'value': 'Yes', 'description': 'Power over Ethernet support'},
                'management': {'value': 'Web-based', 'description': 'Management interface'},
                'mounting': {'value': 'Rack-mount', 'description': 'Mounting type'}
            },
            'configuration_schema': {
                'poe_budget': {
                    'type': 'select',
                    'label': 'PoE Budget',
                    'description': 'Power over Ethernet budget',
                    'required': True,
                    'default': '370W',
                    'options': [
                        {'label': '185W', 'value': '185W'},
                        {'label': '370W', 'value': '370W'},
                        {'label': '740W', 'value': '740W'}
                    ]
                },
                'sfp_ports': {
                    'type': 'number',
                    'label': 'SFP+ Ports',
                    'description': 'Number of 10G SFP+ ports',
                    'required': False,
                    'default': 2,
                    'validation': {'min': 0, 'max': 4}
                }
            },
            'is_active': True,
            'is_configurable': True
        },
        {
            'name': 'UPS Battery Backup',
            'code': 'UPS-1500',
            'description': '1500VA/900W uninterruptible power supply',
            'category': 'Power Management',
            'base_price': 299.99,
            'specifications': {
                'capacity': {'value': '1500', 'unit': 'VA', 'description': 'Power capacity'},
                'runtime': {'value': '15', 'unit': 'minutes', 'description': 'Runtime at full load'},
                'outlets': {'value': '8', 'unit': 'outlets', 'description': 'Power outlets'},
                'input_voltage': {'value': '120', 'unit': 'V', 'description': 'Input voltage'},
                'battery_type': {'value': 'Sealed Lead Acid', 'description': 'Battery technology'}
            },
            'configuration_schema': {
                'extended_runtime': {
                    'type': 'boolean',
                    'label': 'Extended Runtime Module',
                    'description': 'Add external battery pack for longer runtime',
                    'required': False,
                    'default': False
                },
                'network_card': {
                    'type': 'boolean',
                    'label': 'SNMP Network Card',
                    'description': 'Remote monitoring capability',
                    'required': False,
                    'default': False
                }
            },
            'is_active': True,
            'is_configurable': True
        },
        {
            'name': 'LED Display Panel',
            'code': 'LED-55-4K',
            'description': '55-inch 4K LED display panel for digital signage',
            'category': 'Display Systems',
            'base_price': 1299.99,
            'specifications': {
                'screen_size': {'value': '55', 'unit': 'inches', 'description': 'Diagonal screen size'},
                'resolution': {'value': '3840x2160', 'description': '4K Ultra HD resolution'},
                'brightness': {'value': '400', 'unit': 'cd/m²', 'description': 'Display brightness'},
                'contrast_ratio': {'value': '4000:1', 'description': 'Static contrast ratio'},
                'viewing_angle': {'value': '178°', 'description': 'Horizontal and vertical viewing angle'}
            },
            'configuration_schema': {
                'mounting_type': {
                    'type': 'select',
                    'label': 'Mounting Type',
                    'description': 'How the display will be mounted',
                    'required': True,
                    'default': 'wall',
                    'options': [
                        {'label': 'Wall Mount', 'value': 'wall'},
                        {'label': 'Ceiling Mount', 'value': 'ceiling'},
                        {'label': 'Floor Stand', 'value': 'floor'}
                    ]
                },
                'touch_screen': {
                    'type': 'boolean',
                    'label': 'Touch Screen',
                    'description': 'Add touch screen capability',
                    'required': False,
                    'default': False
                }
            },
            'is_active': True,
            'is_configurable': True
        },
        {
            'name': 'Basic Cable - CAT6',
            'code': 'CBL-CAT6-100',
            'description': '100ft CAT6 Ethernet cable',
            'category': 'Cables & Accessories',
            'base_price': 29.99,
            'specifications': {
                'length': {'value': '100', 'unit': 'feet', 'description': 'Cable length'},
                'category': {'value': 'CAT6', 'description': 'Cable category'},
                'bandwidth': {'value': '250', 'unit': 'MHz', 'description': 'Bandwidth capacity'},
                'connector': {'value': 'RJ45', 'description': 'Connector type'}
            },
            'configuration_schema': {},
            'is_active': True,
            'is_configurable': False
        }
    ]
    
    for product_data in products_data:
        # Check if product already exists
        existing_product = Product.query.filter_by(code=product_data['code']).first()
        if not existing_product:
            # Separate complex fields
            specifications = product_data.pop('specifications', {})
            configuration_schema = product_data.pop('configuration_schema', {})
            
            # Create product
            product = Product(**product_data)
            
            # Set complex fields
            if specifications:
                product.set_specifications(specifications)
            if configuration_schema:
                product.set_configuration_schema(configuration_schema)
            
            product.save()
            print(f"Created product: {product.code} - {product.name}")
        else:
            print(f"Product already exists: {product_data['code']}")

def main():
    """Main function to seed the database."""
    app = create_app()
    
    with app.app_context():
        print("Seeding database with sample data...")
        
        # Create tables if they don't exist
        db.create_all()
        
        # Create sample users
        print("\nCreating sample users...")
        create_sample_users()
        
        # Create sample products
        print("\nCreating sample products...")
        create_sample_products()
        
        print("\nDatabase seeding completed!")
        print("\nSample login credentials:")
        print("- admin/password123 (Admin role)")
        print("- engineer/password123 (Engineer role)")
        print("- sales/password123 (Sales role)")
        print("- manager/password123 (Manager role)")

if __name__ == '__main__':
    main()