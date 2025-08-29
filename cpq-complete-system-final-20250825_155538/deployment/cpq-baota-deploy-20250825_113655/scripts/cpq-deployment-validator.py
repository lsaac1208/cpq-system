#!/usr/bin/env python3
"""
CPQ系统宝塔面板部署验证工具
版本: 1.0
作者: DevOps团队
日期: 2025-01-25
"""

import os
import sys
import json
import time
import socket
import subprocess
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

class DeploymentValidator:
    """部署验证器"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.successes = []
        
        # 配置常量
        self.FRONTEND_DOMAIN = "cpq.d1bk.com"
        self.BACKEND_DOMAIN = "cpqh.d1bbk.com"
        self.BACKEND_PORT = 5000
        self.DB_NAME = "cpq_system"
        self.PROJECT_ROOT = "/www/wwwroot"
        
        # 路径配置
        self.frontend_path = f"{self.PROJECT_ROOT}/{self.FRONTEND_DOMAIN}"
        self.backend_path = f"{self.PROJECT_ROOT}/{self.BACKEND_DOMAIN}"
        
    def print_colored(self, message, color_code):
        """打印带颜色的消息"""
        print(f"\033[{color_code}m{message}\033[0m")
        
    def print_success(self, message):
        self.print_colored(f"✅ {message}", "32")
        self.successes.append(message)
        
    def print_error(self, message):
        self.print_colored(f"❌ {message}", "31")
        self.errors.append(message)
        
    def print_warning(self, message):
        self.print_colored(f"⚠️ {message}", "33")
        self.warnings.append(message)
        
    def print_info(self, message):
        self.print_colored(f"ℹ️ {message}", "34")
        
    def print_step(self, message):
        self.print_colored(f"\n🚀 {message}", "35")
        
    def run_command(self, command, capture_output=True, timeout=30):
        """执行系统命令"""
        try:
            if isinstance(command, str):
                result = subprocess.run(
                    command, 
                    shell=True, 
                    capture_output=capture_output,
                    text=True, 
                    timeout=timeout
                )
            else:
                result = subprocess.run(
                    command, 
                    capture_output=capture_output,
                    text=True, 
                    timeout=timeout
                )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "命令执行超时"
        except Exception as e:
            return False, "", str(e)
            
    def check_file_exists(self, filepath, description="文件"):
        """检查文件是否存在"""
        if os.path.exists(filepath):
            self.print_success(f"{description}存在: {filepath}")
            return True
        else:
            self.print_error(f"{description}不存在: {filepath}")
            return False
            
    def check_directory_exists(self, dirpath, description="目录"):
        """检查目录是否存在"""
        if os.path.isdir(dirpath):
            self.print_success(f"{description}存在: {dirpath}")
            return True
        else:
            self.print_error(f"{description}不存在: {dirpath}")
            return False
            
    def check_port_listening(self, port, host='127.0.0.1'):
        """检查端口是否在监听"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                self.print_success(f"端口 {port} 监听正常")
                return True
            else:
                self.print_error(f"端口 {port} 未监听")
                return False
        except Exception as e:
            self.print_error(f"检查端口 {port} 时出错: {e}")
            return False
            
    def check_http_endpoint(self, url, expected_status=200, timeout=10):
        """检查HTTP端点"""
        try:
            request = urllib.request.Request(url)
            response = urllib.request.urlopen(request, timeout=timeout)
            if response.status == expected_status:
                self.print_success(f"HTTP端点正常: {url}")
                return True
            else:
                self.print_error(f"HTTP端点状态异常: {url} (状态码: {response.status})")
                return False
        except urllib.error.URLError as e:
            self.print_error(f"HTTP端点访问失败: {url} ({e})")
            return False
        except Exception as e:
            self.print_error(f"检查HTTP端点时出错: {url} ({e})")
            return False
            
    def check_system_requirements(self):
        """检查系统要求"""
        self.print_step("检查系统要求")
        
        # 检查操作系统
        self.print_info("检查操作系统...")
        success, output, _ = self.run_command("uname -s")
        if success and "Linux" in output:
            self.print_success("Linux系统检测通过")
        else:
            self.print_error("非Linux系统")
            
        # 检查宝塔面板
        self.print_info("检查宝塔面板...")
        if self.check_directory_exists("/www/server/panel", "宝塔面板目录"):
            # 检查宝塔版本
            bt_version_file = "/www/server/panel/class/public.py"
            if os.path.exists(bt_version_file):
                try:
                    with open(bt_version_file, 'r') as f:
                        content = f.read()
                        if 'version' in content:
                            self.print_success("宝塔面板检测通过")
                        else:
                            self.print_warning("宝塔面板版本检测异常")
                except:
                    self.print_warning("无法读取宝塔版本信息")
        
        # 检查Python版本
        self.print_info("检查Python版本...")
        success, output, _ = self.run_command("python3 --version")
        if success:
            version = output.strip().split()[-1]
            major, minor = map(int, version.split('.')[:2])
            if major >= 3 and minor >= 8:
                self.print_success(f"Python版本检测通过: {version}")
            else:
                self.print_error(f"Python版本过低: {version} (需要3.8+)")
        else:
            self.print_error("Python3未安装")
            
        # 检查MySQL
        self.print_info("检查MySQL服务...")
        success, _, _ = self.run_command("systemctl is-active mysqld")
        if not success:
            success, _, _ = self.run_command("systemctl is-active mysql")
        if success:
            self.print_success("MySQL服务运行正常")
        else:
            self.print_error("MySQL服务未运行")
            
        # 检查Nginx
        self.print_info("检查Nginx服务...")
        success, _, _ = self.run_command("systemctl is-active nginx")
        if success:
            self.print_success("Nginx服务运行正常")
            # 检查Nginx配置
            success, _, _ = self.run_command("nginx -t")
            if success:
                self.print_success("Nginx配置语法检查通过")
            else:
                self.print_error("Nginx配置语法错误")
        else:
            self.print_error("Nginx服务未运行")
            
    def check_directory_structure(self):
        """检查目录结构"""
        self.print_step("检查目录结构")
        
        # 检查前端目录
        self.print_info("检查前端目录结构...")
        frontend_dirs = [
            self.frontend_path,
            f"{self.frontend_path}/dist",
            f"{self.frontend_path}/logs",
        ]
        
        for dir_path in frontend_dirs:
            self.check_directory_exists(dir_path)
            
        # 检查前端关键文件
        frontend_files = [
            f"{self.frontend_path}/dist/index.html",
        ]
        
        for file_path in frontend_files:
            self.check_file_exists(file_path)
            
        # 检查后端目录
        self.print_info("检查后端目录结构...")
        backend_dirs = [
            self.backend_path,
            f"{self.backend_path}/logs",
            f"{self.backend_path}/instance",
            f"{self.backend_path}/instance/uploads",
            f"{self.backend_path}/instance/uploads/products",
            f"{self.backend_path}/tmp",
        ]
        
        for dir_path in backend_dirs:
            self.check_directory_exists(dir_path)
            
        # 检查后端关键文件
        backend_files = [
            f"{self.backend_path}/app.py",
            f"{self.backend_path}/.env",
            f"{self.backend_path}/gunicorn.conf.py",
            f"{self.backend_path}/start.sh",
        ]
        
        for file_path in backend_files:
            self.check_file_exists(file_path)
            
    def check_file_permissions(self):
        """检查文件权限"""
        self.print_step("检查文件权限")
        
        # 检查上传目录权限
        upload_dir = f"{self.backend_path}/instance/uploads"
        if os.path.exists(upload_dir):
            stat_info = os.stat(upload_dir)
            mode = oct(stat_info.st_mode)[-3:]
            if mode in ['755', '777']:
                self.print_success(f"上传目录权限正常: {mode}")
            else:
                self.print_warning(f"上传目录权限可能异常: {mode}")
                
        # 检查启动脚本权限
        start_script = f"{self.backend_path}/start.sh"
        if os.path.exists(start_script):
            if os.access(start_script, os.X_OK):
                self.print_success("启动脚本执行权限正常")
            else:
                self.print_error("启动脚本缺少执行权限")
                
    def check_configuration_files(self):
        """检查配置文件"""
        self.print_step("检查配置文件")
        
        # 检查环境配置文件
        env_file = f"{self.backend_path}/.env"
        if os.path.exists(env_file):
            self.print_success("环境配置文件存在")
            try:
                with open(env_file, 'r') as f:
                    content = f.read()
                    required_keys = [
                        'DATABASE_URL', 'SECRET_KEY', 'JWT_SECRET_KEY',
                        'MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE'
                    ]
                    missing_keys = []
                    for key in required_keys:
                        if key not in content:
                            missing_keys.append(key)
                    
                    if not missing_keys:
                        self.print_success("环境配置文件格式正确")
                    else:
                        self.print_error(f"环境配置文件缺少配置项: {', '.join(missing_keys)}")
            except Exception as e:
                self.print_error(f"读取环境配置文件失败: {e}")
        
        # 检查Nginx配置文件
        nginx_config = f"/www/server/panel/vhost/nginx/{self.FRONTEND_DOMAIN}.conf"
        if os.path.exists(nginx_config):
            self.print_success("Nginx前端配置文件存在")
        else:
            self.print_error("Nginx前端配置文件不存在")
            
        # 检查systemd服务文件
        service_file = "/etc/systemd/system/cpq-api.service"
        if os.path.exists(service_file):
            self.print_success("systemd服务文件存在")
        else:
            self.print_error("systemd服务文件不存在")
            
    def check_database_connection(self):
        """检查数据库连接"""
        self.print_step("检查数据库连接")
        
        # 检查数据库是否存在
        mysql_check_cmd = f"mysql -e 'SHOW DATABASES;' | grep {self.DB_NAME}"
        success, output, _ = self.run_command(mysql_check_cmd)
        if success and self.DB_NAME in output:
            self.print_success(f"数据库 {self.DB_NAME} 存在")
        else:
            self.print_error(f"数据库 {self.DB_NAME} 不存在")
            
        # 尝试通过Python连接数据库
        db_test_script = f"""
import sys
sys.path.append('{self.backend_path}')
try:
    from app import app
    with app.app_context():
        from src.models import db
        db.engine.execute('SELECT 1')
        print('数据库连接成功')
except Exception as e:
    print(f'数据库连接失败: {{e}}')
    sys.exit(1)
"""
        
        with open('/tmp/db_test.py', 'w') as f:
            f.write(db_test_script)
            
        success, output, error = self.run_command(f"cd {self.backend_path} && python3 /tmp/db_test.py")
        if success and "数据库连接成功" in output:
            self.print_success("Python数据库连接测试通过")
        else:
            self.print_error(f"Python数据库连接测试失败: {error}")
            
        # 清理测试文件
        try:
            os.remove('/tmp/db_test.py')
        except:
            pass
            
    def check_service_status(self):
        """检查服务状态"""
        self.print_step("检查服务状态")
        
        # 检查CPQ API服务
        success, output, _ = self.run_command("systemctl is-active cpq-api")
        if success:
            self.print_success("CPQ API服务运行正常")
            
            # 获取服务详细信息
            success, status_output, _ = self.run_command("systemctl status cpq-api --no-pager")
            if success:
                lines = status_output.split('\n')
                for line in lines:
                    if 'Active:' in line:
                        self.print_info(f"服务状态: {line.strip()}")
                        break
        else:
            self.print_error("CPQ API服务未运行")
            
        # 检查端口监听
        self.check_port_listening(self.BACKEND_PORT)
        
    def check_api_endpoints(self):
        """检查API端点"""
        self.print_step("检查API端点")
        
        # 检查健康检查端点
        health_url = f"http://127.0.0.1:{self.BACKEND_PORT}/health"
        self.check_http_endpoint(health_url)
        
        # 检查API版本端点
        api_url = f"http://127.0.0.1:{self.BACKEND_PORT}/api/v1/"
        success = self.check_http_endpoint(api_url, expected_status=404)  # 404是正常的，因为根路径不存在
        
    def check_web_access(self):
        """检查Web访问"""
        self.print_step("检查Web访问")
        
        # 检查前端页面访问
        frontend_url = f"http://{self.FRONTEND_DOMAIN}"
        self.check_http_endpoint(frontend_url)
        
        # 检查后端直接访问
        backend_url = f"http://{self.BACKEND_DOMAIN}"
        self.check_http_endpoint(backend_url, expected_status=404)  # 可能没有根路由
        
    def check_log_files(self):
        """检查日志文件"""
        self.print_step("检查日志文件")
        
        log_files = [
            f"{self.backend_path}/logs/app.log",
            f"{self.backend_path}/logs/gunicorn_error.log",
            f"{self.frontend_path}/logs/access.log",
            f"{self.frontend_path}/logs/error.log",
        ]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                size = os.path.getsize(log_file)
                self.print_success(f"日志文件存在: {log_file} ({size} bytes)")
            else:
                self.print_info(f"日志文件不存在: {log_file} (可能尚未生成)")
                
    def performance_test(self):
        """性能测试"""
        self.print_step("性能测试")
        
        # API响应时间测试
        health_url = f"http://127.0.0.1:{self.BACKEND_PORT}/health"
        try:
            start_time = time.time()
            response = urllib.request.urlopen(health_url, timeout=10)
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            if response_time < 1000:
                self.print_success(f"API响应时间良好: {response_time:.2f}ms")
            elif response_time < 3000:
                self.print_warning(f"API响应时间一般: {response_time:.2f}ms")
            else:
                self.print_error(f"API响应时间过慢: {response_time:.2f}ms")
                
        except Exception as e:
            self.print_error(f"API响应时间测试失败: {e}")
            
    def generate_report(self):
        """生成验证报告"""
        self.print_step("生成验证报告")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'validation_summary': {
                'total_checks': len(self.successes) + len(self.errors) + len(self.warnings),
                'successes': len(self.successes),
                'errors': len(self.errors),
                'warnings': len(self.warnings),
                'success_rate': f"{len(self.successes) / (len(self.successes) + len(self.errors)) * 100:.1f}%" if (len(self.successes) + len(self.errors)) > 0 else "0%"
            },
            'successes': self.successes,
            'errors': self.errors,
            'warnings': self.warnings,
            'deployment_info': {
                'frontend_domain': self.FRONTEND_DOMAIN,
                'backend_domain': self.BACKEND_DOMAIN,
                'backend_port': self.BACKEND_PORT,
                'database_name': self.DB_NAME,
                'frontend_path': self.frontend_path,
                'backend_path': self.backend_path
            }
        }
        
        report_file = f"{self.backend_path}/logs/validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            self.print_success(f"验证报告已生成: {report_file}")
        except Exception as e:
            self.print_error(f"生成验证报告失败: {e}")
            
        return report
        
    def print_summary(self, report):
        """打印总结"""
        self.print_colored("\n" + "="*50, "36")
        self.print_colored("          CPQ系统部署验证报告", "36")
        self.print_colored("="*50, "36")
        
        summary = report['validation_summary']
        print(f"\n📊 验证统计:")
        print(f"   总检查项: {summary['total_checks']}")
        print(f"   ✅ 成功: {summary['successes']}")
        print(f"   ❌ 错误: {summary['errors']}")
        print(f"   ⚠️ 警告: {summary['warnings']}")
        print(f"   📈 成功率: {summary['success_rate']}")
        
        if self.errors:
            self.print_colored("\n❌ 发现的问题:", "31")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")
                
        if self.warnings:
            self.print_colored("\n⚠️ 警告信息:", "33")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")
                
        if not self.errors:
            self.print_colored("\n🎉 部署验证通过！", "32")
            print(f"\n🌐 访问地址:")
            print(f"   前端: http://{self.FRONTEND_DOMAIN}")
            print(f"   后端: http://{self.BACKEND_DOMAIN}")
            
            print(f"\n🔐 默认登录:")
            print(f"   用户名: admin")
            print(f"   密码: admin123")
            
            print(f"\n🔧 管理命令:")
            print(f"   启动服务: cd {self.backend_path} && ./start.sh start")
            print(f"   停止服务: cd {self.backend_path} && ./start.sh stop")
            print(f"   重启服务: cd {self.backend_path} && ./start.sh restart")
            print(f"   查看状态: cd {self.backend_path} && ./start.sh status")
            print(f"   查看日志: cd {self.backend_path} && ./start.sh logs")
        else:
            self.print_colored(f"\n❌ 发现 {len(self.errors)} 个错误，请修复后重新验证", "31")
            
    def run_all_checks(self):
        """运行所有检查"""
        print("🔍 CPQ系统部署验证开始...")
        print(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 执行各种检查
        self.check_system_requirements()
        self.check_directory_structure()
        self.check_file_permissions()
        self.check_configuration_files()
        self.check_database_connection()
        self.check_service_status()
        self.check_api_endpoints()
        self.check_web_access()
        self.check_log_files()
        self.performance_test()
        
        # 生成报告
        report = self.generate_report()
        self.print_summary(report)
        
        return len(self.errors) == 0

def main():
    """主函数"""
    validator = DeploymentValidator()
    success = validator.run_all_checks()
    
    # 返回适当的退出代码
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()