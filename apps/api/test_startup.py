#!/usr/bin/env python3
"""
测试后端服务启动脚本
用于验证所有依赖和模块是否能正确导入和初始化
"""

import sys
import os
import traceback

def test_imports():
    """测试关键模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        # 测试 Flask 基础模块
        print("  - Flask 基础模块...")
        from flask import Flask, jsonify
        from flask_cors import CORS
        from flask_jwt_extended import JWTManager
        print("    ✅ Flask 基础模块正常")
        
        # 测试数据库模块
        print("  - 数据库模块...")
        from src.models import db
        print("    ✅ 数据库模块正常")
        
        # 测试路由模块
        print("  - 路由模块...")
        from src.routes import register_routes
        print("    ✅ 路由模块正常")
        
        # 测试中间件
        print("  - 中间件模块...")
        from src.middleware import register_error_handlers
        from src.middleware.performance_monitor import init_performance_monitoring
        print("    ✅ 中间件模块正常")
        
        # 测试配置
        print("  - 配置模块...")
        from config import config
        print("    ✅ 配置模块正常")
        
        return True
        
    except Exception as e:
        print(f"    ❌ 模块导入失败: {str(e)}")
        print(f"    📝 详细错误信息:")
        traceback.print_exc()
        return False

def test_app_creation():
    """测试应用创建"""
    print("🏗️  测试应用创建...")
    
    try:
        from app import create_app
        
        # 使用测试配置创建应用
        app = create_app('testing')
        print(f"    ✅ 应用创建成功: {app}")
        
        # 测试应用配置
        with app.app_context():
            print(f"    📊 数据库URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
            print(f"    🔐 JWT密钥已配置: {'JWT_SECRET_KEY' in app.config}")
            print(f"    🌐 CORS配置: {app.config.get('CORS_ORIGINS')}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ 应用创建失败: {str(e)}")
        print(f"    📝 详细错误信息:")
        traceback.print_exc()
        return False

def test_routes():
    """测试路由注册"""
    print("🛣️  测试路由注册...")
    
    try:
        from app import create_app
        app = create_app('testing')
        
        # 获取已注册的路由
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(f"{rule.methods} {rule.rule}")
        
        print(f"    ✅ 成功注册 {len(routes)} 个路由")
        
        # 显示关键路由
        key_routes = ['/health', '/api/v1/auth', '/api/v1/quotes', '/api/v1/products']
        for key_route in key_routes:
            found = any(key_route in route for route in routes)
            status = "✅" if found else "❌"
            print(f"    {status} {key_route}: {'找到' if found else '未找到'}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ 路由注册失败: {str(e)}")
        print(f"    📝 详细错误信息:")
        traceback.print_exc()
        return False

def test_database():
    """测试数据库连接"""
    print("🗄️  测试数据库连接...")
    
    try:
        from app import create_app
        app = create_app('testing')
        
        with app.app_context():
            from src.models import db
            
            # 创建所有表
            db.create_all()
            print("    ✅ 数据库表创建成功")
            
            # 测试简单查询 (适配不同的SQLAlchemy版本)
            try:
                # SQLAlchemy 2.0+ 语法
                from sqlalchemy import text
                result = db.session.execute(text('SELECT 1 as test')).fetchone()
                print(f"    ✅ 数据库查询成功: {result}")
            except AttributeError:
                # SQLAlchemy 1.x 语法
                result = db.engine.execute('SELECT 1 as test').fetchone()
                print(f"    ✅ 数据库查询成功: {result}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ 数据库连接失败: {str(e)}")
        print(f"    📝 详细错误信息:")
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 开始后端服务启动测试")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_imports),
        ("应用创建", test_app_creation),
        ("路由注册", test_routes),
        ("数据库连接", test_database),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            print()
        except Exception as e:
            print(f"❌ {test_name}测试异常: {str(e)}")
            results.append((test_name, False))
            print()
    
    print("=" * 50)
    print("📊 测试结果汇总:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！后端服务应该可以正常启动")
        return 0
    else:
        print("⚠️  存在问题，需要修复后再部署")
        return 1

if __name__ == '__main__':
    sys.exit(main())