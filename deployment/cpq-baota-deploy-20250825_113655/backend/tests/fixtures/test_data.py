"""Test data fixtures and factories for CPQ system tests."""

import factory
import factory.fuzzy
from faker import Faker
from decimal import Decimal
from datetime import datetime, timedelta
from src.models.user import User
from src.models.product import Product
from src.models.quote import Quote, QuoteStatus
from src.models.base import db

fake = Faker()


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating User instances."""
    
    class Meta:
        model = User
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    role = 'user'
    is_active = True
    
    @factory.post_generation
    def set_password(obj, create, extracted, **kwargs):
        if not create:
            return
        password = extracted or 'testpass123'
        obj.set_password(password)


class AdminUserFactory(UserFactory):
    """Factory for creating Admin User instances."""
    
    role = 'admin'
    username = factory.Sequence(lambda n: f'admin{n}')


class EngineerUserFactory(UserFactory):
    """Factory for creating Engineer User instances."""
    
    role = 'engineer'
    username = factory.Sequence(lambda n: f'engineer{n}')


class ManagerUserFactory(UserFactory):
    """Factory for creating Manager User instances."""
    
    role = 'manager'
    username = factory.Sequence(lambda n: f'manager{n}')


class ProductFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating Product instances."""
    
    class Meta:
        model = Product
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'
    
    name = factory.Faker('word')
    code = factory.Sequence(lambda n: f'PROD-{n:04d}')
    description = factory.Faker('text', max_nb_chars=200)
    category = factory.Faker('word')
    base_price = factory.fuzzy.FuzzyDecimal(100.00, 5000.00, 2)
    is_active = True
    is_configurable = True
    
    @factory.post_generation
    def set_configuration_schema(obj, create, extracted, **kwargs):
        if not create:
            return
        
        if extracted:
            schema = extracted
        else:
            schema = {
                'cpu': {
                    'type': 'select',
                    'options': ['Intel i5', 'Intel i7', 'AMD Ryzen 5'],
                    'default': 'Intel i5',
                    'price_modifier': [0, 200, 150]
                },
                'memory': {
                    'type': 'select',
                    'options': ['8GB', '16GB', '32GB'],
                    'default': '8GB',
                    'price_modifier': [0, 300, 800]
                }
            }
        obj.set_configuration_schema(schema)
    
    @factory.post_generation
    def set_specifications(obj, create, extracted, **kwargs):
        if not create:
            return
        
        if extracted:
            specs = extracted
        else:
            specs = {
                'weight': f'{fake.random_int(1, 10)}.{fake.random_int(0, 9)}kg',
                'dimensions': f'{fake.random_int(20, 50)}x{fake.random_int(15, 40)}x{fake.random_int(1, 10)}cm',
                'warranty': f'{fake.random_int(1, 5)} years'
            }
        obj.set_specifications(specs)


class SimpleProductFactory(ProductFactory):
    """Factory for creating simple (non-configurable) Product instances."""
    
    is_configurable = False
    
    @factory.post_generation
    def set_configuration_schema(obj, create, extracted, **kwargs):
        # Override to not set configuration schema for simple products
        pass


class ConfigurableProductFactory(ProductFactory):
    """Factory for creating complex configurable Product instances."""
    
    @factory.post_generation
    def set_configuration_schema(obj, create, extracted, **kwargs):
        if not create:
            return
        
        complex_schema = {
            'hardware': {
                'cpu': {
                    'type': 'select',
                    'options': [
                        {'name': 'Intel i5-12400', 'price': 0, 'specs': {'cores': 6, 'threads': 12}},
                        {'name': 'Intel i7-12700K', 'price': 200, 'specs': {'cores': 12, 'threads': 20}},
                        {'name': 'AMD Ryzen 5 5600X', 'price': 150, 'specs': {'cores': 6, 'threads': 12}},
                        {'name': 'AMD Ryzen 7 5800X', 'price': 300, 'specs': {'cores': 8, 'threads': 16}}
                    ],
                    'default': 0
                },
                'memory': {
                    'type': 'multiselect',
                    'options': ['8GB DDR4', '16GB DDR4', '32GB DDR4', '64GB DDR4'],
                    'price_per_unit': [0, 300, 800, 1800],
                    'max_selection': 4
                },
                'storage': {
                    'type': 'select',
                    'options': [
                        {'name': '256GB SSD', 'price': 0},
                        {'name': '512GB SSD', 'price': 150},
                        {'name': '1TB SSD', 'price': 300},
                        {'name': '2TB SSD', 'price': 600}
                    ]
                }
            },
            'software': {
                'os': {
                    'type': 'radio',
                    'options': ['Windows 11 Home', 'Windows 11 Pro', 'Ubuntu Linux'],
                    'prices': [0, 100, 0],
                    'default': 'Windows 11 Home'
                },
                'office': {
                    'type': 'checkbox',
                    'options': [
                        {'name': 'Microsoft Office 365', 'price': 120},
                        {'name': 'LibreOffice', 'price': 0}
                    ]
                }
            },
            'services': {
                'warranty': {
                    'type': 'select',
                    'options': [
                        {'name': '1 Year Standard', 'price': 0},
                        {'name': '2 Year Extended', 'price': 200},
                        {'name': '3 Year Premium', 'price': 500}
                    ],
                    'default': 0
                },
                'support': {
                    'type': 'checkbox',
                    'options': [
                        {'name': '24/7 Phone Support', 'price': 300},
                        {'name': 'On-site Installation', 'price': 150},
                        {'name': 'Data Migration', 'price': 200}
                    ]
                }
            }
        }
        obj.set_configuration_schema(complex_schema)


class QuoteFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating Quote instances."""
    
    class Meta:
        model = Quote
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'
    
    quote_number = factory.LazyAttribute(lambda obj: f'Q-{datetime.now().strftime("%Y%m%d%H%M%S")}-{fake.random_int(1000, 9999)}')
    customer_name = factory.Faker('name')
    customer_email = factory.Faker('email')
    customer_company = factory.Faker('company')
    
    # Foreign keys
    product = factory.SubFactory(ProductFactory)
    created_by = factory.SubFactory(UserFactory)
    
    # Configuration and pricing
    quantity = factory.fuzzy.FuzzyInteger(1, 10)
    unit_price = factory.fuzzy.FuzzyDecimal(500.00, 3000.00, 2)
    discount_percentage = factory.fuzzy.FuzzyDecimal(0, 20, 2)
    
    # Status and validity
    status = QuoteStatus.DRAFT
    valid_until = factory.LazyFunction(lambda: datetime.now() + timedelta(days=30))
    
    # Additional information
    notes = factory.Faker('text', max_nb_chars=500)
    terms_conditions = 'Standard terms and conditions apply'
    
    @factory.post_generation
    def set_configuration(obj, create, extracted, **kwargs):
        if not create:
            return
        
        if extracted:
            config = extracted
        else:
            config = {
                'cpu': 'Intel i7',
                'memory': '16GB',
                'storage': '512GB SSD'
            }
        obj.set_configuration(config)
    
    @factory.post_generation
    def calculate_pricing(obj, create, extracted, **kwargs):
        if not create:
            return
        obj.calculate_pricing()


class PendingQuoteFactory(QuoteFactory):
    """Factory for creating Quote instances in pending status."""
    
    status = QuoteStatus.PENDING


class ApprovedQuoteFactory(QuoteFactory):
    """Factory for creating Quote instances in approved status."""
    
    status = QuoteStatus.APPROVED
    approved_by = factory.SubFactory(ManagerUserFactory)


class RejectedQuoteFactory(QuoteFactory):
    """Factory for creating Quote instances in rejected status."""
    
    status = QuoteStatus.REJECTED
    approved_by = factory.SubFactory(ManagerUserFactory)


class ExpiredQuoteFactory(QuoteFactory):
    """Factory for creating Quote instances in expired status."""
    
    status = QuoteStatus.EXPIRED
    valid_until = factory.LazyFunction(lambda: datetime.now() - timedelta(days=1))


# Sample data sets for consistent testing
SAMPLE_USERS = {
    'user': {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass123',
        'first_name': 'Test',
        'last_name': 'User',
        'role': 'user'
    },
    'admin': {
        'username': 'admin',
        'email': 'admin@example.com',
        'password': 'adminpass123',
        'first_name': 'Admin',
        'last_name': 'User',  
        'role': 'admin'
    },
    'engineer': {
        'username': 'engineer',
        'email': 'engineer@example.com',
        'password': 'engineerpass123',
        'first_name': 'Engineer',
        'last_name': 'User',
        'role': 'engineer'
    },
    'manager': {
        'username': 'manager',
        'email': 'manager@example.com',
        'password': 'managerpass123',
        'first_name': 'Manager',
        'last_name': 'User',
        'role': 'manager'
    }
}

SAMPLE_PRODUCTS = [
    {
        'name': 'Basic Laptop',
        'code': 'LAPTOP-BASIC-001',
        'description': 'Entry-level laptop for basic computing needs',
        'category': 'Electronics',
        'base_price': Decimal('799.99'),
        'is_configurable': False
    },
    {
        'name': 'Gaming Desktop',
        'code': 'DESKTOP-GAMING-001',
        'description': 'High-performance gaming desktop computer',
        'category': 'Electronics',
        'base_price': Decimal('1999.99'),
        'is_configurable': True
    },
    {
        'name': 'Office Workstation',
        'code': 'WORKSTATION-OFFICE-001',
        'description': 'Professional workstation for office use',
        'category': 'Electronics',
        'base_price': Decimal('2499.99'),
        'is_configurable': True
    }
]

SAMPLE_QUOTES = [
    {
        'customer_name': 'John Doe',
        'customer_email': 'john.doe@example.com',
        'customer_company': 'Acme Corp',
        'quantity': 2,
        'status': 'draft',
        'configuration': {
            'cpu': 'Intel i7',
            'memory': '16GB',
            'storage': '512GB SSD'
        }
    },
    {
        'customer_name': 'Jane Smith',
        'customer_email': 'jane.smith@example.com',
        'customer_company': 'Tech Solutions Inc',
        'quantity': 5,
        'status': 'pending',
        'configuration': {
            'cpu': 'AMD Ryzen 7',
            'memory': '32GB',
            'storage': '1TB SSD'
        }
    },
    {
        'customer_name': 'Bob Johnson',
        'customer_email': 'bob.johnson@example.com',
        'customer_company': 'Enterprise Systems LLC',
        'quantity': 10,
        'status': 'approved',
        'configuration': {
            'cpu': 'Intel i9',
            'memory': '64GB',
            'storage': '2TB SSD'
        }
    }
]


def create_sample_users():
    """Create sample users for testing."""
    users = {}
    for role, user_data in SAMPLE_USERS.items():
        user = User(
            username=user_data['username'],
            email=user_data['email'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            role=user_data['role']
        )
        user.set_password(user_data['password'])
        db.session.add(user)
        users[role] = user
    
    db.session.commit()
    return users


def create_sample_products():
    """Create sample products for testing."""
    products = []
    for product_data in SAMPLE_PRODUCTS:
        product = Product(**product_data)
        
        if product.is_configurable:
            # Add configuration schema for configurable products
            if 'Gaming' in product.name:
                schema = {
                    'cpu': {
                        'type': 'select',
                        'options': ['Intel i5', 'Intel i7', 'Intel i9'],
                        'prices': [0, 300, 600]
                    },
                    'gpu': {
                        'type': 'select',
                        'options': ['GTX 1660', 'RTX 3070', 'RTX 4080'],
                        'prices': [0, 500, 1200]
                    },
                    'memory': {
                        'type': 'select',
                        'options': ['16GB', '32GB', '64GB'],
                        'prices': [0, 400, 1200]
                    }
                }
            else:
                schema = {
                    'cpu': {
                        'type': 'select',
                        'options': ['Intel i5', 'Intel i7', 'AMD Ryzen 5'],
                        'prices': [0, 200, 150]
                    },
                    'memory': {
                        'type': 'select',
                        'options': ['8GB', '16GB', '32GB'],
                        'prices': [0, 300, 800]
                    }
                }
            product.set_configuration_schema(schema)
        
        db.session.add(product)
        products.append(product)
    
    db.session.commit()
    return products


def create_sample_quotes(users, products):
    """Create sample quotes for testing."""
    quotes = []
    for i, quote_data in enumerate(SAMPLE_QUOTES):
        quote = Quote(
            quote_number=f'Q-{datetime.now().strftime("%Y%m%d")}-{i+1:04d}',
            customer_name=quote_data['customer_name'],
            customer_email=quote_data['customer_email'],
            customer_company=quote_data['customer_company'],
            product_id=products[i % len(products)].id,
            quantity=quote_data['quantity'],
            unit_price=products[i % len(products)].base_price,
            status=QuoteStatus(quote_data['status']),
            created_by=users['user'].id,
            valid_until=datetime.now() + timedelta(days=30)
        )
        
        quote.set_configuration(quote_data['configuration'])
        quote.calculate_pricing()
        
        if quote.status == QuoteStatus.APPROVED:
            quote.approved_by = users['manager'].id
        
        db.session.add(quote)
        quotes.append(quote)
    
    db.session.commit()
    return quotes


def setup_test_data():
    """Set up complete test data set."""
    users = create_sample_users()
    products = create_sample_products()
    quotes = create_sample_quotes(users, products)
    
    return {
        'users': users,
        'products': products,
        'quotes': quotes
    }