#!/usr/bin/env python3
"""
紧急修复脚本 - 创建最小化的后端服务
解决504错误，确保核心功能可用
"""

import os
import sys
import traceback
from datetime import datetime

def create_minimal_app():
    """创建最小化应用，移除所有可能导致问题的组件"""
    
    print("🔧 创建最小化应用...")
    
    minimal_app_code = '''
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
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///cpq_system.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'emergency-jwt-secret-2024')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# 初始化扩展
db = SQLAlchemy(app)
CORS(app, origins=['http://localhost:5173', 'http://cpq.100yse.com'])
JWTManager(app)

# 简化的用户模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 简化的报价模型
class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quote_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    final_price = db.Column(db.Numeric(10, 2), default=0)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='draft')

    def to_dict(self):
        return {
            'id': self.id,
            'quote_number': self.quote_number,
            'customer_name': self.customer_name,
            'customer_email': self.customer_email,
            'final_price': float(self.final_price or 0),
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'status': self.status
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
            'message': '登录成功',
            'access_token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
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
        db.create_all()
        
        # 确保有admin用户
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ 创建默认管理员用户: admin / admin123")

if __name__ == '__main__':
    init_database()
    
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    
    print(f"🚀 紧急模式API服务启动...")
    print(f"📍 地址: http://{host}:{port}")
    print(f"🔐 默认管理员: admin / admin123")
    
    app.run(host=host, port=port, debug=False)
'''
    
    return minimal_app_code

def create_emergency_files():
    """创建紧急修复所需的文件"""
    
    # 创建最小化应用
    minimal_app = create_minimal_app()
    
    # 保存紧急应用文件
    emergency_app_path = '/Users/wang/Documents/MyCode/beta/BMad/cpq/apps/api/emergency_app.py'
    with open(emergency_app_path, 'w', encoding='utf-8') as f:
        f.write(minimal_app)
    
    print(f"✅ 创建紧急应用: {emergency_app_path}")
    
    # 创建最小依赖文件
    minimal_requirements = """# 最小依赖 - 紧急模式
Flask==3.0.3
Flask-SQLAlchemy==3.1.1
Flask-CORS==4.0.1
Flask-JWT-Extended==4.6.0
SQLAlchemy==2.0.30
Werkzeug==3.0.3
python-dotenv==1.0.1
"""
    
    minimal_req_path = '/Users/wang/Documents/MyCode/beta/BMad/cpq/apps/api/requirements-emergency.txt'
    with open(minimal_req_path, 'w', encoding='utf-8') as f:
        f.write(minimal_requirements)
    
    print(f"✅ 创建最小依赖: {minimal_req_path}")
    
    # 创建启动脚本
    start_script = """#!/bin/bash
# 紧急启动脚本

echo "🚨 启动CPQ系统紧急模式..."

# 切换到API目录
cd "$(dirname "$0")"

# 安装最小依赖
echo "📦 安装最小依赖..."
pip install -r requirements-emergency.txt

# 启动紧急服务
echo "🚀 启动紧急服务..."
python emergency_app.py
"""
    
    start_script_path = '/Users/wang/Documents/MyCode/beta/BMad/cpq/apps/api/start_emergency.sh'
    with open(start_script_path, 'w', encoding='utf-8') as f:
        f.write(start_script)
    
    # 设置执行权限
    os.chmod(start_script_path, 0o755)
    
    print(f"✅ 创建启动脚本: {start_script_path}")
    
    return emergency_app_path, minimal_req_path, start_script_path

def create_deployment_guide():
    """创建部署指南"""
    
    guide = """# CPQ系统紧急修复部署指南

## 🚨 紧急情况说明

如果正常的修复版本仍然出现504错误，请使用这个紧急模式。

## 📦 紧急部署步骤

### 1. 停止当前服务
```bash
# 在宝塔面板中停止Python项目
# 或者使用命令行
pkill -f "python.*app.py"
```

### 2. 备份当前代码
```bash
cp -r /path/to/current/api /path/to/backup/api_backup_emergency_$(date +%Y%m%d_%H%M%S)
```

### 3. 部署紧急文件
将以下文件上传到服务器API目录：
- `emergency_app.py` - 最小化应用
- `requirements-emergency.txt` - 最小依赖
- `start_emergency.sh` - 启动脚本

### 4. 启动紧急服务
```bash
cd /path/to/api
chmod +x start_emergency.sh
./start_emergency.sh
```

或者手动启动：
```bash
pip install -r requirements-emergency.txt
python emergency_app.py
```

## 🔧 紧急模式功能

### 可用功能
- ✅ 用户登录 (`/api/v1/auth/login`)
- ✅ 用户信息 (`/api/v1/auth/me`) 
- ✅ 报价列表 (`/api/v1/quotes`) - 核心功能
- ✅ 健康检查 (`/health`)

### 默认管理员
- 用户名: `admin`
- 密码: `admin123`

### 移除的组件
- AI分析功能 (导致依赖问题)
- 性能监控 (psutil依赖)
- 复杂的中间件
- 不必要的路由

## 🔍 验证步骤

### 1. 检查服务状态
```bash
curl http://your-domain/health
```

应该返回:
```json
{
  "status": "healthy",
  "timestamp": "2024-...",
  "service": "CPQ API Emergency Mode"
}
```

### 2. 测试登录
```bash
curl -X POST http://your-domain/api/v1/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{"username": "admin", "password": "admin123"}'
```

### 3. 测试报价接口
```bash
curl -X GET http://your-domain/api/v1/quotes \\
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🎯 预期结果

紧急模式下，系统应该能够：
1. ✅ 正常启动，无504错误
2. ✅ 用户可以登录
3. ✅ 管理员可以查看报价列表
4. ✅ 前端可以正常连接后端

## 📞 如果紧急模式仍然失败

请检查：
1. Python版本 (建议3.8+)
2. 数据库文件权限
3. 端口占用情况
4. 服务器错误日志

## ⚡ 恢复到正常模式

紧急模式验证可用后，可以逐步恢复：
1. 确认核心功能正常
2. 逐个添加其他功能模块
3. 监控日志确保稳定性

## 🔄 回滚计划

如需回滚到修复前版本：
```bash
# 停止紧急服务
pkill -f emergency_app.py

# 恢复备份
cp -r /path/to/backup/api_backup_* /path/to/current/api

# 重启原服务
```

---

**重要**: 紧急模式只包含核心功能，其他功能需要在系统稳定后逐步添加。
"""
    
    guide_path = '/Users/wang/Documents/MyCode/beta/BMad/cpq/apps/api/EMERGENCY_DEPLOYMENT_GUIDE.md'
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(guide)
    
    print(f"✅ 创建部署指南: {guide_path}")
    
    return guide_path

def main():
    """主函数"""
    print("🚨 CPQ系统紧急修复程序")
    print("=" * 50)
    
    try:
        # 创建紧急文件
        emergency_files = create_emergency_files()
        
        # 创建部署指南
        guide_path = create_deployment_guide()
        
        print("\n" + "=" * 50)
        print("🎉 紧急修复文件创建完成！")
        print("\n📁 创建的文件：")
        for file_path in emergency_files:
            print(f"  - {file_path}")
        print(f"  - {guide_path}")
        
        print(f"\n🚀 立即测试:")
        print(f"  cd {os.path.dirname(emergency_files[0])}")
        print(f"  python emergency_app.py")
        
        print(f"\n📖 详细部署说明请查看:")
        print(f"  {guide_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ 紧急修复失败: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)