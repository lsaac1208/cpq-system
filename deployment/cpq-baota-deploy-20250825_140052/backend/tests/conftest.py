"""Test configuration and fixtures for CPQ API tests."""

import pytest
import tempfile
import os
import shutil
from unittest.mock import Mock, patch
from app import create_app
from src.models.base import db
from src.models.user import User
from src.models.product import Product
from src.models.quote import Quote, QuoteStatus
from src.models.batch_analysis import BatchAnalysisJob, BatchAnalysisFile, BatchStatus, FileStatus
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from decimal import Decimal

# 设置测试环境变量
os.environ['FLASK_ENV'] = 'testing'
os.environ['TESTING'] = '1'


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'JWT_SECRET_KEY': 'test-secret-key',
        'JWT_ACCESS_TOKEN_EXPIRES': timedelta(hours=1),
        'JWT_REFRESH_TOKEN_EXPIRES': timedelta(days=30),
        'WTF_CSRF_ENABLED': False
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
    
    # Clean up
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create test client for Flask app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test runner for Flask CLI commands."""
    return app.test_cli_runner()


@pytest.fixture
def app_context(app):
    """Create application context for tests."""
    with app.app_context():
        yield app


@pytest.fixture
def db_session(app_context):
    """Create database session for tests."""
    # 清空所有表数据
    db.session.query(BatchAnalysisJob).delete()
    db.session.query(BatchAnalysisFile).delete()
    db.session.query(Quote).delete()
    db.session.query(Product).delete()
    db.session.query(User).delete()
    db.session.commit()
    
    # 开始新的事务
    db.session.begin()
    yield db.session
    db.session.rollback()
    db.session.close()


# User fixtures
@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'StrongTestPass1@9!',
        'first_name': 'Test',
        'last_name': 'User',
        'role': 'user'
    }


@pytest.fixture
def admin_user_data():
    """Sample admin user data for testing."""
    return {
        'username': 'admin',
        'email': 'admin@example.com',
        'password': 'AdminPass1@9!',
        'first_name': 'Admin',
        'last_name': 'User',
        'role': 'admin'
    }


@pytest.fixture
def engineer_user_data():
    """Sample engineer user data for testing."""
    return {
        'username': 'engineer',
        'email': 'engineer@example.com',
        'password': 'EngineerPass1@9!',
        'first_name': 'Engineer',
        'last_name': 'User',
        'role': 'engineer'
    }


@pytest.fixture
def test_user(db_session, sample_user_data):
    """Create test user in database."""
    user = User(
        username=sample_user_data['username'],
        email=sample_user_data['email'],
        first_name=sample_user_data['first_name'],
        last_name=sample_user_data['last_name'],
        role=sample_user_data['role']
    )
    user.set_password(sample_user_data['password'])
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def admin_user(db_session, admin_user_data):
    """Create admin user in database."""
    user = User(
        username=admin_user_data['username'],
        email=admin_user_data['email'],
        first_name=admin_user_data['first_name'],
        last_name=admin_user_data['last_name'],
        role=admin_user_data['role']
    )
    user.set_password(admin_user_data['password'])
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def engineer_user(db_session, engineer_user_data):
    """Create engineer user in database."""
    user = User(
        username=engineer_user_data['username'],
        email=engineer_user_data['email'],
        first_name=engineer_user_data['first_name'],
        last_name=engineer_user_data['last_name'],
        role=engineer_user_data['role']
    )
    user.set_password(engineer_user_data['password'])
    db.session.add(user)
    db.session.commit()
    return user


# Product fixtures
@pytest.fixture
def sample_product_data():
    """Sample product data for testing."""
    return {
        'name': 'Test Product',
        'code': 'TEST-001',
        'description': 'A test product for unit testing',
        'category': 'Testing',
        'base_price': Decimal('999.99'),
        'configuration_schema': {
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
        },
        'specifications': {
            'weight': '2.5kg',
            'dimensions': '35x25x2cm',
            'warranty': '2 years'
        },
        'is_active': True,
        'is_configurable': True
    }


@pytest.fixture
def test_product(db_session, sample_product_data):
    """Create test product in database."""
    product = Product(
        name=sample_product_data['name'],
        code=sample_product_data['code'],
        description=sample_product_data['description'],
        category=sample_product_data['category'],
        base_price=sample_product_data['base_price'],
        is_active=sample_product_data['is_active'],
        is_configurable=sample_product_data['is_configurable']
    )
    product.set_configuration_schema(sample_product_data['configuration_schema'])
    product.set_specifications(sample_product_data['specifications'])
    db.session.add(product)
    db.session.commit()
    return product


# Quote fixtures
@pytest.fixture
def sample_quote_data():
    """Sample quote data for testing."""
    return {
        'quote_number': 'Q-20240101120000-0001',
        'customer_name': 'John Doe',
        'customer_email': 'john.doe@example.com',
        'customer_company': 'Acme Corp',
        'configuration': {
            'cpu': 'Intel i7',
            'memory': '16GB'
        },
        'quantity': 2,
        'unit_price': Decimal('1499.99'),
        'total_price': Decimal('2999.98'),
        'discount_percentage': Decimal('10.00'),
        'discount_amount': Decimal('299.998'),
        'final_price': Decimal('2699.98'),
        'status': QuoteStatus.DRAFT,
        'valid_until': datetime.now() + timedelta(days=30),
        'notes': 'Test quote for integration testing',
        'terms_conditions': 'Standard terms and conditions apply'
    }


@pytest.fixture
def test_quote(db_session, test_product, test_user, sample_quote_data):
    """Create test quote in database."""
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
    quote.set_configuration(sample_quote_data['configuration'])
    db.session.add(quote)
    db.session.commit()
    return quote


# Authentication fixtures
@pytest.fixture
def auth_headers(client, test_user, sample_user_data):
    """Get authentication headers for test user."""
    response = client.post('/api/v1/auth/login', json={
        'username': test_user.username,
        'password': sample_user_data['password']
    })
    assert response.status_code == 200
    data = response.get_json()['data']
    return {
        'Authorization': f'Bearer {data["tokens"]["access_token"]}'
    }


@pytest.fixture
def admin_auth_headers(client, admin_user):
    """Get authentication headers for admin user."""
    response = client.post('/api/v1/auth/login', json={
        'username': admin_user.username,
        'password': 'AdminPass1@9!'
    })
    assert response.status_code == 200
    data = response.get_json()['data']
    return {
        'Authorization': f'Bearer {data["tokens"]["access_token"]}'
    }


@pytest.fixture
def engineer_auth_headers(client, engineer_user):
    """Get authentication headers for engineer user."""
    response = client.post('/api/v1/auth/login', json={
        'username': engineer_user.username,
        'password': 'EngineerPass1@9!'
    })
    assert response.status_code == 200
    data = response.get_json()['data']
    return {
        'Authorization': f'Bearer {data["tokens"]["access_token"]}'
    }


# Batch Analysis fixtures
@pytest.fixture
def batch_job_data():
    """Sample batch analysis job data for testing."""
    return {
        'job_id': 'batch_test_123456',
        'job_name': '测试批量分析任务',
        'total_files': 3,
        'settings': {
            'analysis_type': 'customer_requirements',
            'auto_start': False,
            'business_context': {
                'industry': 'technology',
                'project_type': 'development'
            }
        }
    }


@pytest.fixture
def test_batch_job(db_session, test_user, batch_job_data):
    """Create test batch analysis job in database."""
    job = BatchAnalysisJob(
        job_id=batch_job_data['job_id'],
        job_name=batch_job_data['job_name'],
        user_id=test_user.id,
        total_files=batch_job_data['total_files'],
        settings=batch_job_data['settings'],
        status=BatchStatus.PENDING,
        estimated_duration=45.0
    )
    db.session.add(job)
    db.session.commit()
    return job


@pytest.fixture
def test_batch_files(db_session, test_batch_job):
    """Create test batch analysis files in database."""
    files = []
    for i in range(3):
        file = BatchAnalysisFile(
            job_id=test_batch_job.job_id,
            file_id=f'file_test_{i}',
            filename=f'test_document_{i}.txt',
            original_filename=f'original_test_{i}.txt',
            file_size=1000 + i * 200,
            file_type='txt',
            status=FileStatus.QUEUED,
            priority=5
        )
        db.session.add(file)
        files.append(file)
    db.session.commit()
    return files


@pytest.fixture
def test_documents():
    """Test document contents for analysis."""
    return {
        'customer_requirements': """
客户需求文档

项目名称: 企业级ERP系统
技术需求:
- 高性能处理能力，支持10000+并发用户
- 低延迟响应，页面加载时间<2秒  
- 高可靠性，99.9%服务可用性
- 模块化设计，便于扩展
- 云原生架构，支持容器化部署

商务需求:
- 预算范围: 150-300万元
- 项目周期: 8个月内完成
- 维护期: 3年技术支持

风险评估:
- 技术风险: 中等
- 进度风险: 低
- 预算风险: 低
        """,
        'competitor_analysis': """
竞品分析报告

产品名称: 用友NC Cloud
产品类型: 大型企业ERP解决方案
价格信息:
- 基础版: 80-120万元
- 标准版: 120-200万元
- 企业版: 200-500万元

技术特点:
- 基于云原生架构
- 支持多租户
- 丰富的API接口
- 移动端支持

市场地位: 国内ERP市场领导者之一
客户群体: 大中型企业
        """,
        'product_extraction': """
产品规格说明书

产品名称: 智能制造执行系统 (MES)
产品版本: V3.0
产品类型: 制造执行系统

核心功能:
- 生产计划管理
- 车间作业管理
- 质量管理
- 设备管理
- 物料管理

技术规格:
- 架构: 微服务架构
- 数据库: MySQL 8.0+
- 运行环境: Linux/Windows
- 部署方式: 容器化部署

价格信息:
- 标准版: 50万元/年
- 企业版: 100万元/年
- 定制版: 面议
        """
    }


@pytest.fixture
def temp_test_files(test_documents):
    """Create temporary test files for upload testing."""
    temp_dir = tempfile.mkdtemp()
    files = {}
    
    for doc_type, content in test_documents.items():
        file_path = os.path.join(temp_dir, f'{doc_type}.txt')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        files[doc_type] = file_path
    
    yield files
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_ai_analyzer():
    """Mock AI analyzer for testing."""
    with patch('src.services.ai_analyzer.AIAnalyzer') as mock:
        analyzer = Mock()
        analyzer.analyze_document.return_value = {
            'analysis_type': 'customer_requirements',
            'business_insights': {
                'customer_requirements': {
                    'raw_analysis': '{"技术需求": {"性能规格要求": ["高性能", "低延迟", "高可靠性"]}, "商务需求": {"预算范围": "150-300万元"}}',
                    'risk_assessment': {
                        'technical_risk': 'medium',
                        'schedule_risk': 'low', 
                        'budget_risk': 'low'
                    }
                }
            },
            'confidence_scores': {
                'overall': 0.85,
                'technical': 0.90,
                'business': 0.80
            },
            'processing_time': 12.5
        }
        mock.return_value = analyzer
        yield analyzer


@pytest.fixture
def mock_batch_processor():
    """Mock batch processor for testing."""
    with patch('src.services.batch_processor.BatchProcessor') as mock:
        processor = Mock()
        processor.create_batch_job.return_value = 'batch_test_123456'
        processor.start_batch_processing.return_value = True
        processor.get_batch_status.return_value = {
            'job_id': 'batch_test_123456',
            'status': 'pending',
            'progress_percentage': 0,
            'files_status': []
        }
        processor.get_batch_results.return_value = {
            'job_id': 'batch_test_123456',
            'status': 'completed',
            'total_files': 3,
            'successful_files': 3,
            'failed_files': 0,
            'results': []
        }
        processor.get_processing_statistics.return_value = {
            'total_jobs': 1,
            'active_jobs': 0,
            'average_file_time': 15.0,
            'success_rate': 95.0,
            'total_files_processed': 0
        }
        mock.return_value = processor
        yield processor


# Utility functions for tests
def assert_response_success(response, expected_status=200):
    """Assert response is successful."""
    assert response.status_code == expected_status
    data = response.get_json()
    assert data.get('success') == True


def assert_response_error(response, expected_status=400):
    """Assert response is an error."""
    assert response.status_code == expected_status
    data = response.get_json()
    assert 'msg' in data or 'error' in data


def create_test_file(content, filename='test.txt'):
    """Create a temporary test file."""
    temp_file = tempfile.NamedTemporaryFile(
        mode='w', 
        suffix=f'_{filename}', 
        delete=False, 
        encoding='utf-8'
    )
    temp_file.write(content)
    temp_file.flush()
    temp_file.close()
    return temp_file.name