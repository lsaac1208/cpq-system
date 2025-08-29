
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import sqlite3
import json

# 创建Flask应用
app = Flask(__name__)

# 基础配置
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'emergency-secret-key-2024')
# 使用绝对路径指向真实数据库
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'cpq_system.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'emergency-jwt-secret-2024')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# 初始化扩展
db = SQLAlchemy(app)
CORS(app, origins=['http://localhost:5173', 'http://cpq.100yse.com'])
JWTManager(app)

# 修正的用户模型 - 使用正确的表名 'users'
class User(db.Model):
    __tablename__ = 'users'  # 指定使用existing users表
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 修正的报价模型 - 使用正确的表名 'quotes'
class Quote(db.Model):
    __tablename__ = 'quotes'  # 指定使用existing quotes表
    
    id = db.Column(db.Integer, primary_key=True)
    quote_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    customer_company = db.Column(db.String(200))  # 添加公司字段
    product_id = db.Column(db.Integer)  # 产品ID
    configuration = db.Column(db.Text)  # 配置信息
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Numeric(10, 2), default=0)
    total_price = db.Column(db.Numeric(10, 2), default=0)
    discount_percentage = db.Column(db.Numeric(5, 2), default=0)
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    final_price = db.Column(db.Numeric(10, 2), default=0)
    status = db.Column(db.String(20), default='DRAFT')
    valid_until = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approved_by = db.Column(db.Integer)
    notes = db.Column(db.Text)
    terms_conditions = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        import json
        
        # Parse configuration if it's a JSON string
        configuration = self.configuration
        if isinstance(configuration, str) and configuration:
            try:
                configuration = json.loads(configuration)
            except json.JSONDecodeError:
                configuration = {}
        elif not configuration:
            configuration = {}
        
        return {
            'id': self.id,
            'quote_number': self.quote_number,
            'customer_name': self.customer_name,
            'customer_email': self.customer_email,
            'customer_company': self.customer_company,
            'product_id': self.product_id,
            'configuration': configuration,  # 现在返回对象而不是字符串
            'quantity': self.quantity,
            'unit_price': float(self.unit_price or 0),
            'subtotal': float(self.total_price or 0),  # 添加subtotal字段，映射到total_price
            'total_price': float(self.total_price or 0),
            'discount_percentage': float(self.discount_percentage or 0),
            'discount_amount': float(self.discount_amount or 0),
            'final_price': float(self.final_price or 0),
            'status': self.status.lower() if self.status else 'draft',  # 转换为小写
            'version': 1,  # 添加version字段，默认为1
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'created_by': self.created_by,
            'approved_by': self.approved_by,
            'notes': self.notes,
            'terms_conditions': self.terms_conditions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# 获取当前用户的辅助函数
def get_current_user():
    try:
        current_user_identity = get_jwt_identity()
        if current_user_identity:
            return User.query.filter_by(username=current_user_identity).first()
        return None
    except:
        return None

# 健康检查端点
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'CPQ API Emergency Mode'
    })

# 认证端点
@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': '用户名和密码不能为空'}), 400
        
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return jsonify({'error': '用户名或密码错误'}), 401
        
        access_token = create_access_token(identity=username)
        
        return jsonify({
            'success': True,
            'data': {
                'tokens': {
                    'access_token': access_token,
                    'refresh_token': access_token  # 简化版本，使用相同token
                },
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role
                }
            },
            'message': '登录成功'
        })
    except Exception as e:
        return jsonify({'error': f'登录失败: {str(e)}'}), 500

# 报价列表端点 - 核心功能
@app.route('/api/v1/quotes', methods=['GET'])
@jwt_required()
def get_quotes():
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '用户认证失败'}), 401
        
        # 获取查询参数
        created_by = request.args.get('created_by')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # 构建查询
        query = Quote.query
        
        # 用户权限控制
        if current_user.role == 'admin':
            if created_by and created_by != 'all':
                try:
                    query = query.filter(Quote.created_by == int(created_by))
                except ValueError:
                    return jsonify({'error': 'Invalid created_by value'}), 400
        else:
            query = query.filter(Quote.created_by == current_user.id)
        
        # 按创建时间倒序
        query = query.order_by(Quote.created_at.desc())
        
        # 分页
        quotes = query.paginate(page=page, per_page=per_page, error_out=False)
        
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
        return jsonify({'error': f'获取报价失败: {str(e)}'}), 500

# 创建报价端点
@app.route('/api/v1/quotes', methods=['POST'])
@jwt_required()
def create_quote():
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '用户认证失败'}), 401
            
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据不能为空'}), 400
            
        # 生成报价单号
        from datetime import datetime
        now = datetime.now()
        quote_number = f"Q-{now.strftime('%Y%m%d%H%M%S')}-{str(now.microsecond)[:4]}"
        
        # 创建新报价
        quote = Quote(
            quote_number=quote_number,
            customer_name=data.get('customer_name', ''),
            customer_email=data.get('customer_email', ''),
            customer_company=data.get('customer_company', ''),
            product_id=data.get('product_id'),
            configuration=json.dumps(data.get('configuration', {})),
            quantity=data.get('quantity', 1),
            unit_price=data.get('unit_price', 0),
            total_price=data.get('total_price', 0),
            discount_percentage=data.get('discount_percentage', 0),
            discount_amount=data.get('discount_amount', 0),
            final_price=data.get('final_price', 0),
            status=data.get('status', 'DRAFT'),
            notes=data.get('notes'),
            terms_conditions=data.get('terms_conditions'),
            created_by=current_user.id
        )
        
        db.session.add(quote)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'quote': quote.to_dict(),
            'message': '报价创建成功'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'创建报价失败: {str(e)}'}), 500

# 产品列表端点 - 模拟数据
@app.route('/api/v1/products', methods=['GET'])
@jwt_required()
def get_products():
    """返回模拟产品数据，支持报价创建功能"""
    # 模拟产品数据
    mock_products = [
        {
            'id': 1,
            'name': '电机产品A',
            'model': 'MOTOR-A-380V',
            'price': 1299.99,
            'description': '380V三相异步电机',
            'is_active': True,
            'category': 'motor',
            'specifications': {
                'voltage': '380V',
                'power': '5.5kW',
                'speed': '1440rpm'
            }
        },
        {
            'id': 2,
            'name': '变频器产品B',
            'model': 'VFD-B-440V',
            'price': 1899.99,
            'description': '440V变频调速器',
            'is_active': True,
            'category': 'vfd',
            'specifications': {
                'voltage': '440V',
                'power': '7.5kW',
                'control': '矢量控制'
            }
        },
        {
            'id': 3,
            'name': '控制器产品C',
            'model': 'CTRL-C-24V',
            'price': 899.99,
            'description': '24V智能控制器',
            'is_active': True,
            'category': 'controller',
            'specifications': {
                'voltage': '24V',
                'io_points': '32点',
                'communication': 'Modbus/Ethernet'
            }
        }
    ]
    
    # 处理查询参数
    is_active = request.args.get('is_active')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    # 过滤活跃产品
    if is_active == 'true':
        products = [p for p in mock_products if p['is_active']]
    else:
        products = mock_products
    
    # 分页处理
    start = (page - 1) * per_page
    end = start + per_page
    paginated_products = products[start:end]
    
    return jsonify({
        'products': paginated_products,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': len(products),
            'pages': (len(products) + per_page - 1) // per_page
        }
    })

# 多报价列表端点 - 空实现
@app.route('/api/v1/multi-quotes', methods=['GET'])
@jwt_required()
def get_multi_quotes():
    """返回空的多报价列表，保持前端兼容性"""
    return jsonify({
        'quotes': [],
        'pagination': {
            'page': 1,
            'per_page': 20,
            'total': 0,
            'pages': 0
        }
    })

# AI分析历史端点 - 模拟实现
@app.route('/api/v1/ai-analysis/history', methods=['GET'])
@jwt_required()
def get_ai_analysis_history():
    """返回AI分析历史记录，模拟数据确保Dashboard正常显示"""
    try:
        # 获取查询参数
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        status = request.args.get('status', '')
        
        # 模拟AI分析历史数据
        mock_records = [
            {
                'id': 1,
                'document_name': '电机产品规格书.pdf',
                'success': True,
                'overall_confidence': 0.92,
                'extracted_data': {
                    'basic_info': {
                        'name': '三相异步电机 YE3-160M-4',
                        'code': 'YE3-160M-4',
                        'category': 'motor'
                    }
                },
                'created_at': '2025-08-27T10:30:00Z'
            },
            {
                'id': 2,
                'document_name': '变频器技术手册.pdf',
                'success': True,
                'overall_confidence': 0.87,
                'extracted_data': {
                    'basic_info': {
                        'name': '矢量变频器 VFD-M500',
                        'code': 'VFD-M500',
                        'category': 'vfd'
                    }
                },
                'created_at': '2025-08-27T09:15:00Z'
            },
            {
                'id': 3,
                'document_name': '控制器说明文档.pdf',
                'success': False,
                'overall_confidence': 0.45,
                'extracted_data': {
                    'basic_info': {
                        'name': '解析失败',
                        'code': '',
                        'category': ''
                    }
                },
                'created_at': '2025-08-27T08:45:00Z'
            }
        ]
        
        # 根据状态过滤
        if status == 'completed':
            filtered_records = [r for r in mock_records if r['success']]
        elif status == 'failed':
            filtered_records = [r for r in mock_records if not r['success']]
        else:
            filtered_records = mock_records
        
        # 分页处理
        start = (page - 1) * per_page
        end = start + per_page
        paginated_records = filtered_records[start:end]
        
        return jsonify({
            'success': True,
            'records': paginated_records,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': len(filtered_records),
                'pages': (len(filtered_records) + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'获取AI分析历史失败: {str(e)}'}), 500

# AI分析统计端点 - 模拟实现
@app.route('/api/v1/ai-analysis/statistics', methods=['GET'])
@jwt_required()
def get_ai_analysis_statistics():
    """返回AI分析统计信息"""
    try:
        return jsonify({
            'success': True,
            'statistics': {
                'total_analyses': 12,
                'successful_analyses': 9,
                'failed_analyses': 3,
                'success_rate': 0.75,
                'avg_confidence': 0.83,
                'recent_analyses': 3
            }
        })
    except Exception as e:
        return jsonify({'error': f'获取统计信息失败: {str(e)}'}), 500

# AI分析支持格式端点 - 模拟实现
@app.route('/api/v1/ai-analysis/supported-formats', methods=['GET'])
@jwt_required()
def get_supported_formats():
    """返回支持的文档格式"""
    return jsonify({
        'success': True,
        'supported_formats': {
            'document_types': ['pdf', 'docx', 'doc', 'txt'],
            'image_types': ['jpg', 'jpeg', 'png'],
            'max_file_size': 10485760,  # 10MB
            'max_files_per_batch': 10
        }
    })

# 获取单个报价详情端点
@app.route('/api/v1/quotes/<int:quote_id>', methods=['GET'])
@jwt_required()
def get_quote_detail(quote_id):
    """获取单个报价的详细信息"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '用户认证失败'}), 401
        
        # 查找报价
        quote = Quote.query.get(quote_id)
        if not quote:
            return jsonify({'error': 'Quote not found'}), 404
        
        # 权限检查：管理员可以查看所有报价，普通用户只能查看自己创建的报价
        if current_user.role != 'admin' and quote.created_by != current_user.id:
            return jsonify({'error': 'Permission denied'}), 403
        
        # 返回报价详情，格式与前端期望匹配
        return jsonify({
            'quote': quote.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': f'获取报价详情失败: {str(e)}'}), 500

# 获取多产品报价详情端点 - 兼容性实现
@app.route('/api/v1/multi-quotes/<int:quote_id>', methods=['GET'])
@jwt_required()
def get_multi_quote_detail(quote_id):
    """获取多产品报价详情，为了前端兼容性总是返回404"""
    return jsonify({'error': 'Multi-quote not found'}), 404

# 获取产品分类端点
@app.route('/api/v1/products/categories', methods=['GET'])
@jwt_required()
def get_product_categories():
    """返回产品分类列表"""
    try:
        # 模拟产品分类数据
        categories = [
            {
                'id': 1,
                'name': '电机',
                'code': 'motor',
                'description': '各类电机产品',
                'is_active': True,
                'product_count': 15
            },
            {
                'id': 2,
                'name': '变频器',
                'code': 'vfd',
                'description': '变频调速设备',
                'is_active': True,
                'product_count': 8
            },
            {
                'id': 3,
                'name': '控制器',
                'code': 'controller',
                'description': '智能控制设备',
                'is_active': True,
                'product_count': 12
            }
        ]
        
        return jsonify({
            'categories': categories,
            'total': len(categories)
        })
        
    except Exception as e:
        return jsonify({'error': f'获取产品分类失败: {str(e)}'}), 500

# 获取单个产品详情端点
@app.route('/api/v1/products/<int:product_id>', methods=['GET'])
@jwt_required()
def get_product_detail(product_id):
    """获取单个产品的详细信息"""
    try:
        # 模拟产品详情数据
        mock_products = {
            1: {
                'id': 1,
                'name': '电机产品A',
                'code': 'MOTOR-A-380V',
                'model': 'MOTOR-A-380V',
                'base_price': 1299.99,
                'current_price': 1299.99,
                'description': '380V三相异步电机，高效节能，适用于工业自动化场景',
                'category': 'motor',
                'category_name': '电机',
                'is_active': True,
                'is_configurable': True,
                'specifications': {
                    'voltage': '380V',
                    'power': '5.5kW',
                    'speed': '1440rpm',
                    'efficiency': '95%',
                    'protection_class': 'IP55'
                },
                'features': [
                    '高效节能',
                    '低噪音运行',
                    '维护简单',
                    '防护等级IP55'
                ],
                'applications': [
                    '风机',
                    '水泵',
                    '输送设备',
                    '工业自动化'
                ],
                'accessories': [
                    {
                        'id': '1',
                        'name': '编码器',
                        'description': '高精度光电编码器',
                        'type': 'optional',
                        'sort_order': 1
                    },
                    {
                        'id': '2', 
                        'name': '刹车器',
                        'description': '电磁刹车器',
                        'type': 'standard',
                        'sort_order': 2
                    }
                ],
                'support_info': {
                    'warranty': {
                        'period': '3年',
                        'coverage': '整机保修，主要部件终身维护',
                        'terms': ['免费上门服务', '24小时响应', '原厂配件保证']
                    },
                    'contact_info': {
                        'sales_phone': '+86-21-12345678',
                        'sales_email': 'sales@cpqsystems.com',
                        'support_phone': '+86-21-87654321',
                        'support_email': 'support@cpqsystems.com',
                        'service_wechat': 'CPQ-Service'
                    },
                    'service_promises': [
                        '24小时技术支持热线',
                        '48小时内上门服务',
                        '终身技术咨询',
                        '免费培训服务'
                    ]
                },
                'images': [],
                'created_at': '2025-01-15T10:00:00Z',
                'updated_at': '2025-08-15T14:30:00Z'
            },
            2: {
                'id': 2,
                'name': '变频器产品B',
                'code': 'VFD-B-440V',
                'model': 'VFD-B-440V',
                'base_price': 1899.99,
                'current_price': 1899.99,
                'description': '440V变频调速器，支持矢量控制和开环控制',
                'category': 'vfd',
                'category_name': '变频器',
                'is_active': True,
                'is_configurable': True,
                'specifications': {
                    'voltage': '440V',
                    'power': '7.5kW',
                    'control': '矢量控制',
                    'frequency': '0-400Hz',
                    'protection_class': 'IP20'
                },
                'features': [
                    '矢量控制',
                    '开环/闭环控制',
                    '多种通讯接口',
                    '丰富的保护功能'
                ],
                'applications': [
                    '风机控制',
                    '泵类控制',
                    '传送带控制',
                    '机床控制'
                ],
                'accessories': [
                    'EMC滤波器',
                    '制动电阻',
                    '操作面板'
                ],
                'images': [],
                'created_at': '2025-01-20T09:00:00Z',
                'updated_at': '2025-08-20T16:15:00Z'
            },
            3: {
                'id': 3,
                'name': '控制器产品C',
                'code': 'CTRL-C-24V',
                'model': 'CTRL-C-24V',
                'base_price': 899.99,
                'current_price': 899.99,
                'description': '24V智能控制器，支持多种通讯协议',
                'category': 'controller',
                'category_name': '控制器',
                'is_active': True,
                'is_configurable': True,
                'specifications': {
                    'voltage': '24V',
                    'io_points': '32点',
                    'communication': 'Modbus/Ethernet',
                    'memory': '128KB',
                    'operating_temp': '-20°C~60°C'
                },
                'features': [
                    '32点数字I/O',
                    '多种通讯接口',
                    '编程简单',
                    '工业级设计'
                ],
                'applications': [
                    '过程控制',
                    '数据采集',
                    '设备监控',
                    '自动化系统'
                ],
                'accessories': [
                    '扩展模块',
                    '通讯模块',
                    '电源模块'
                ],
                'images': [],
                'created_at': '2025-02-01T11:00:00Z',
                'updated_at': '2025-08-25T13:45:00Z'
            }
        }
        
        if product_id not in mock_products:
            return jsonify({'error': 'Product not found'}), 404
            
        return jsonify({
            'product': mock_products[product_id]
        })
        
    except Exception as e:
        return jsonify({'error': f'获取产品详情失败: {str(e)}'}), 500

# AI文档分析端点
@app.route('/api/v1/ai-analysis/analyze-document', methods=['POST'])
@jwt_required()
def analyze_document():
    """AI文档分析端点"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '用户认证失败'}), 401
        
        # 检查是否有文件上传
        if 'document' not in request.files:
            return jsonify({'error': '未上传文档文件'}), 400
            
        file = request.files['document']
        if file.filename == '':
            return jsonify({'error': '文件名不能为空'}), 400
        
        # 模拟AI分析结果
        import time
        time.sleep(1)  # 模拟处理时间
        
        mock_analysis_result = {
            'success': True,
            'document_info': {
                'filename': file.filename,
                'mimetype': file.content_type,
                'size': len(file.read()),
                'type': file.filename.split('.')[-1] if '.' in file.filename else 'unknown'
            },
            'extracted_data': {
                'basic_info': {
                    'name': f'分析产品 - {file.filename}',
                    'code': f'PROD-{int(time.time())}',
                    'category': 'motor',
                    'base_price': 1299.99,
                    'description': f'通过AI分析{file.filename}提取的产品信息'
                },
                'specifications': {
                    'voltage': '380V',
                    'power': '5.5kW',
                    'speed': '1440rpm',
                    'efficiency': '95%'
                },
                'features': [
                    '高效节能',
                    '智能控制',
                    '低维护成本'
                ],
                'application_scenarios': [
                    '工业自动化',
                    '机械设备',
                    '生产线控制'
                ]
            },
            'confidence_scores': {
                'basic_info': 0.95,
                'specifications': 0.88,
                'features': 0.92,
                'overall': 0.91
            },
            'analysis_timestamp': int(time.time() * 1000),
            'processing_time': 850
        }
        
        return jsonify(mock_analysis_result)
        
    except Exception as e:
        return jsonify({'error': f'AI文档分析失败: {str(e)}'}), 500

# 产品图库端点
@app.route('/api/v1/products/<int:product_id>/gallery', methods=['GET'])
@jwt_required()
def get_product_gallery(product_id):
    """获取产品图库"""
    try:
        # 模拟产品图库数据
        mock_gallery = {
            'images': [],
            'stats': {
                'total_images': 0,
                'total_size': 0,
                'by_type': {
                    'product': 0,
                    'detail': 0,
                    'usage': 0,
                    'comparison': 0
                },
                'has_primary': False
            }
        }
        
        return jsonify(mock_gallery)
        
    except Exception as e:
        return jsonify({'error': f'获取产品图库失败: {str(e)}'}), 500

# 系统设置端点
@app.route('/api/v1/settings', methods=['GET'])
@jwt_required()
def get_settings():
    """获取系统设置"""
    try:
        # 模拟系统设置数据
        settings = {
            'company': {
                'name': 'CPQ Industrial Systems',
                'address': '上海市浦东新区科技园区123号',
                'phone': '+86-21-12345678',
                'email': 'info@cpqsystems.com',
                'website': 'www.cpqsystems.com',
                'tax_number': '310000123456789',
                'logo_url': '/images/company-logo.png'
            },
            'quote': {
                'default_currency': 'CNY',
                'default_tax_rate': 0.13,
                'default_valid_days': 30,
                'quote_number_prefix': 'Q-',
                'auto_approval_threshold': 10000
            },
            'system': {
                'timezone': 'Asia/Shanghai',
                'date_format': 'YYYY-MM-DD',
                'decimal_places': 2,
                'language': 'zh-CN'
            },
            'ai': {
                'enabled': True,
                'provider': 'openai',
                'model': 'gpt-4',
                'max_tokens': 4000,
                'temperature': 0.7
            },
            'notification': {
                'email_enabled': True,
                'sms_enabled': False,
                'webhook_enabled': True
            }
        }
        
        return jsonify({
            'settings': settings
        })
        
    except Exception as e:
        return jsonify({'error': f'获取系统设置失败: {str(e)}'}), 500

# 用户信息端点
@app.route('/api/v1/auth/me', methods=['GET'])
@jwt_required()
def get_current_user_info():
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '用户认证失败'}), 401
        
        return jsonify({
            'user': {
                'id': current_user.id,
                'username': current_user.username,
                'email': current_user.email,
                'role': current_user.role
            }
        })
    except Exception as e:
        return jsonify({'error': f'获取用户信息失败: {str(e)}'}), 500

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# 初始化数据库
def init_database():
    with app.app_context():
        # 不需要创建表，因为使用existing database
        print("🔄 连接到现有数据库...")
        
        # 检查admin用户是否存在
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print(f"✅ 管理员用户已存在: {admin.username} (role: {admin.role})")
        else:
            print("❌ 未找到管理员用户")

if __name__ == '__main__':
    init_database()
    
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    
    print(f"🚀 紧急模式API服务启动...")
    print(f"📍 地址: http://{host}:{port}")
    print(f"🔐 默认管理员: admin / admin123")
    
    app.run(host=host, port=port, debug=False)
