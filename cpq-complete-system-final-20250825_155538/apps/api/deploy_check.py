#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPQ系统部署前检查脚本
确保生产环境配置正确
更新时间: 2024-08-24
"""

import os
import sys
import subprocess
from datetime import datetime
from dotenv import load_dotenv
import mysql.connector
from pathlib import Path

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def print_header(message):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

class DeploymentChecker:
    """部署检查器"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.checks_passed = 0
        self.total_checks = 0
        
        # 加载环境变量
        if os.path.exists('.env.production'):
            load_dotenv('.env.production')
            print_info("已加载 .env.production 配置")
        else:
            print_warning("未找到 .env.production 文件，使用默认环境变量")
    
    def check_python_version(self):
        """检查Python版本"""
        print_info("检查Python版本...")
        self.total_checks += 1
        
        version = sys.version_info
        if version.major == 3 and version.minor >= 8:
            print_success(f"Python版本: {version.major}.{version.minor}.{version.micro}")
            self.checks_passed += 1
        else:
            self.errors.append(f"Python版本过低: {version.major}.{version.minor}.{version.micro}，需要3.8+")
            print_error(f"Python版本过低: {version.major}.{version.minor}.{version.micro}，需要3.8+")
    
    def check_required_files(self):
        """检查必需文件"""
        print_info("检查必需文件...")
        
        required_files = [
            'app.py',
            'config.py',
            'gunicorn.conf.py',
            'start.sh',
            '.env.production',
            'requirements-production.txt'
        ]
        
        for file in required_files:
            self.total_checks += 1
            if os.path.exists(file):
                print_success(f"文件存在: {file}")
                self.checks_passed += 1
            else:
                self.errors.append(f"缺少必需文件: {file}")
                print_error(f"缺少必需文件: {file}")
    
    def check_directories(self):
        """检查必需目录"""
        print_info("检查必需目录...")
        
        required_dirs = [
            'src',
            'src/models',
            'src/routes',
            'src/services',
            'instance',
            'instance/uploads'
        ]
        
        for directory in required_dirs:
            self.total_checks += 1
            if os.path.exists(directory):
                print_success(f"目录存在: {directory}")
                self.checks_passed += 1
            else:
                self.warnings.append(f"目录不存在: {directory}")
                print_warning(f"目录不存在: {directory}")
    
    def check_dependencies(self):
        """检查Python依赖"""
        print_info("检查Python依赖...")
        
        required_packages = [
            'flask',
            'flask_sqlalchemy',
            'flask_cors',
            'flask_jwt_extended',
            'gunicorn',
            'pymysql',
            'python_dotenv'
        ]
        
        for package in required_packages:
            self.total_checks += 1
            try:
                __import__(package)
                print_success(f"依赖包已安装: {package}")
                self.checks_passed += 1
            except ImportError:
                self.errors.append(f"缺少依赖包: {package}")
                print_error(f"缺少依赖包: {package}")
    
    def check_environment_variables(self):
        """检查环境变量"""
        print_info("检查环境变量...")
        
        required_env_vars = [
            'SECRET_KEY',
            'JWT_SECRET_KEY',
            'DATABASE_URL',
            'MYSQL_HOST',
            'MYSQL_USER',
            'MYSQL_PASSWORD',
            'MYSQL_DATABASE'
        ]
        
        for var in required_env_vars:
            self.total_checks += 1
            value = os.getenv(var)
            if value and value not in ['your-secret-key', 'your_password', 'change-this']:
                print_success(f"环境变量已设置: {var}")
                self.checks_passed += 1
            else:
                self.errors.append(f"环境变量未正确设置: {var}")
                print_error(f"环境变量未正确设置: {var}")
    
    def check_mysql_connection(self):
        """检查MySQL连接"""
        print_info("检查MySQL数据库连接...")
        self.total_checks += 1
        
        try:
            config = {
                'host': os.getenv('MYSQL_HOST', 'localhost'),
                'port': int(os.getenv('MYSQL_PORT', 3306)),
                'user': os.getenv('MYSQL_USER'),
                'password': os.getenv('MYSQL_PASSWORD'),
                'database': os.getenv('MYSQL_DATABASE'),
                'charset': 'utf8mb4'
            }
            
            conn = mysql.connector.connect(**config)
            conn.close()
            print_success("MySQL数据库连接成功")
            self.checks_passed += 1
            
        except Exception as e:
            self.errors.append(f"MySQL连接失败: {e}")
            print_error(f"MySQL连接失败: {e}")
    
    def check_flask_app(self):
        """检查Flask应用"""
        print_info("检查Flask应用配置...")
        self.total_checks += 1
        
        try:
            # 设置环境变量
            os.environ['FLASK_ENV'] = 'production'
            
            # 导入应用
            from app import create_app
            app = create_app('production')
            
            with app.app_context():
                # 检查应用配置
                if app.config.get('DEBUG') == False:
                    print_success("Flask应用配置正确 (DEBUG=False)")
                    self.checks_passed += 1
                else:
                    self.warnings.append("生产环境应该关闭DEBUG模式")
                    print_warning("生产环境应该关闭DEBUG模式")
                    
        except Exception as e:
            self.errors.append(f"Flask应用检查失败: {e}")
            print_error(f"Flask应用检查失败: {e}")
    
    def check_gunicorn_config(self):
        """检查Gunicorn配置"""
        print_info("检查Gunicorn配置...")
        self.total_checks += 1
        
        try:
            # 检查Gunicorn配置文件语法
            result = subprocess.run(['python', '-m', 'py_compile', 'gunicorn.conf.py'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print_success("Gunicorn配置文件语法正确")
                self.checks_passed += 1
            else:
                self.errors.append(f"Gunicorn配置文件语法错误: {result.stderr}")
                print_error(f"Gunicorn配置文件语法错误")
                
        except Exception as e:
            self.errors.append(f"Gunicorn配置检查失败: {e}")
            print_error(f"Gunicorn配置检查失败: {e}")
    
    def check_permissions(self):
        """检查文件权限"""
        print_info("检查文件权限...")
        
        # 检查启动脚本执行权限
        self.total_checks += 1
        if os.access('start.sh', os.X_OK):
            print_success("start.sh 具有执行权限")
            self.checks_passed += 1
        else:
            self.warnings.append("start.sh 缺少执行权限")
            print_warning("start.sh 缺少执行权限，运行: chmod +x start.sh")
        
        # 检查上传目录权限
        upload_dir = Path('instance/uploads')
        if upload_dir.exists():
            self.total_checks += 1
            if os.access(upload_dir, os.W_OK):
                print_success("uploads 目录可写")
                self.checks_passed += 1
            else:
                self.warnings.append("uploads 目录权限不足")
                print_warning("uploads 目录权限不足")
    
    def check_security_settings(self):
        """检查安全设置"""
        print_info("检查安全设置...")
        
        # 检查密钥强度
        secret_key = os.getenv('SECRET_KEY', '')
        jwt_secret = os.getenv('JWT_SECRET_KEY', '')
        
        self.total_checks += 2
        
        if len(secret_key) >= 32 and secret_key not in ['your-secret-key', 'dev-secret-key']:
            print_success("SECRET_KEY 强度足够")
            self.checks_passed += 1
        else:
            self.errors.append("SECRET_KEY 过于简单或未设置")
            print_error("SECRET_KEY 过于简单或未设置")
        
        if len(jwt_secret) >= 32 and jwt_secret not in ['your-jwt-secret', 'dev-jwt-secret']:
            print_success("JWT_SECRET_KEY 强度足够")
            self.checks_passed += 1
        else:
            self.errors.append("JWT_SECRET_KEY 过于简单或未设置")
            print_error("JWT_SECRET_KEY 过于简单或未设置")
    
    def generate_report(self):
        """生成检查报告"""
        print_header("部署检查报告")
        
        print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"检查项目: {self.total_checks}")
        print(f"通过检查: {self.checks_passed}")
        print(f"错误数量: {len(self.errors)}")
        print(f"警告数量: {len(self.warnings)}")
        print()
        
        if self.errors:
            print_error("发现错误:")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
            print()
        
        if self.warnings:
            print_warning("发现警告:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
            print()
        
        # 计算通过率
        pass_rate = (self.checks_passed / self.total_checks) * 100 if self.total_checks > 0 else 0
        
        if len(self.errors) == 0 and pass_rate >= 90:
            print_success(f"部署检查通过！(通过率: {pass_rate:.1f}%)")
            print_info("可以开始部署到生产环境")
            return True
        elif len(self.errors) == 0:
            print_warning(f"部署检查基本通过，但有警告 (通过率: {pass_rate:.1f}%)")
            print_info("建议修复警告后再部署到生产环境")
            return True
        else:
            print_error(f"部署检查失败！(通过率: {pass_rate:.1f}%)")
            print_error("请修复所有错误后重新检查")
            return False
    
    def run_all_checks(self):
        """运行所有检查"""
        print_header("CPQ系统部署前检查")
        
        self.check_python_version()
        self.check_required_files()
        self.check_directories()
        self.check_dependencies()
        self.check_environment_variables()
        self.check_mysql_connection()
        self.check_flask_app()
        self.check_gunicorn_config()
        self.check_permissions()
        self.check_security_settings()
        
        return self.generate_report()

def main():
    """主函数"""
    try:
        checker = DeploymentChecker()
        success = checker.run_all_checks()
        
        if success:
            print("\n" + "="*60)
            print("📋 后续部署步骤:")
            print("1. 上传文件到服务器")
            print("2. 配置宝塔面板Python项目")
            print("3. 安装生产环境依赖")
            print("4. 执行数据库迁移")
            print("5. 启动应用服务")
            print("="*60)
            return True
        else:
            print("\n" + "="*60)
            print("🔧 修复建议:")
            print("1. 检查并修复上述错误")
            print("2. 更新环境变量配置")
            print("3. 安装缺失的依赖包")
            print("4. 重新运行检查脚本")
            print("="*60)
            return False
            
    except KeyboardInterrupt:
        print("\n\n检查已取消")
        return False
    except Exception as e:
        print_error(f"检查过程中发生错误: {e}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)