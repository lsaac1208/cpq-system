#!/bin/bash

# =============================================================================
# CPQ系统宝塔面板一键部署脚本
# 版本: 1.0
# 作者: DevOps团队
# 日期: 2025-01-25
# =============================================================================

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 配置常量
PROJECT_NAME="CPQ系统"
FRONTEND_DOMAIN="cpq.d1bk.com"
BACKEND_DOMAIN="cpqh.d1bbk.com"
BACKEND_PORT="5000"
DB_NAME="cpq_system"
DB_USER="cpq_user"
PROJECT_ROOT="/www/wwwroot"
FRONTEND_PATH="${PROJECT_ROOT}/${FRONTEND_DOMAIN}"
BACKEND_PATH="${PROJECT_ROOT}/${BACKEND_DOMAIN}"
LOG_FILE="/tmp/cpq_deploy_$(date +%Y%m%d_%H%M%S).log"

# 函数：打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}[$(date '+%Y-%m-%d %H:%M:%S')] ${message}${NC}" | tee -a "$LOG_FILE"
}

print_success() { print_message "$GREEN" "✅ $1"; }
print_error() { print_message "$RED" "❌ $1"; }
print_warning() { print_message "$YELLOW" "⚠️ $1"; }
print_info() { print_message "$BLUE" "ℹ️ $1"; }
print_step() { print_message "$PURPLE" "🚀 步骤: $1"; }

# 函数：检查命令是否存在
check_command() {
    if command -v "$1" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# 函数：检查服务状态
check_service() {
    if systemctl is-active --quiet "$1"; then
        return 0
    else
        return 1
    fi
}

# 函数：检查端口是否被占用
check_port() {
    if netstat -tlnp | grep ":$1 " >/dev/null; then
        return 0
    else
        return 1
    fi
}

# 函数：等待用户确认
wait_for_confirm() {
    local message=$1
    print_warning "$message"
    read -p "是否继续? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "用户取消操作"
        exit 1
    fi
}

# 函数：环境检查
check_environment() {
    print_step "环境检查"
    
    local errors=0
    
    # 检查操作系统
    print_info "检查操作系统..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_success "Linux系统检测通过"
    else
        print_error "不支持的操作系统: $OSTYPE"
        ((errors++))
    fi
    
    # 检查是否为root用户
    print_info "检查用户权限..."
    if [[ $EUID -eq 0 ]]; then
        print_success "Root权限检测通过"
    else
        print_error "需要root权限执行部署"
        ((errors++))
    fi
    
    # 检查宝塔面板
    print_info "检查宝塔面板..."
    if [[ -d "/www/server/panel" ]]; then
        print_success "宝塔面板检测通过"
    else
        print_error "宝塔面板未安装，请先安装宝塔面板"
        ((errors++))
    fi
    
    # 检查Python版本
    print_info "检查Python环境..."
    if check_command python3; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        if [[ $(echo "$PYTHON_VERSION >= 3.8" | bc -l) -eq 1 ]]; then
            print_success "Python版本检测通过: $PYTHON_VERSION"
        else
            print_error "Python版本过低: $PYTHON_VERSION (需要3.8+)"
            ((errors++))
        fi
    else
        print_error "Python3未安装"
        ((errors++))
    fi
    
    # 检查MySQL服务
    print_info "检查MySQL服务..."
    if check_service mysqld; then
        print_success "MySQL服务运行正常"
    elif check_service mysql; then
        print_success "MySQL服务运行正常"
    else
        print_error "MySQL服务未运行"
        ((errors++))
    fi
    
    # 检查Nginx服务
    print_info "检查Nginx服务..."
    if check_service nginx; then
        print_success "Nginx服务运行正常"
    else
        print_error "Nginx服务未运行"
        ((errors++))
    fi
    
    # 检查磁盘空间
    print_info "检查磁盘空间..."
    available_space=$(df / | awk 'NR==2 {print int($4/1024/1024)}')
    if [[ $available_space -gt 2 ]]; then
        print_success "磁盘空间充足: ${available_space}GB"
    else
        print_warning "磁盘空间不足: ${available_space}GB (建议>2GB)"
        wait_for_confirm "磁盘空间不足，是否继续部署？"
    fi
    
    # 检查内存
    print_info "检查系统内存..."
    total_memory=$(free -m | awk 'NR==2{print int($2/1024)}')
    if [[ $total_memory -gt 1 ]]; then
        print_success "系统内存充足: ${total_memory}GB"
    else
        print_warning "系统内存较少: ${total_memory}GB (建议>1GB)"
    fi
    
    if [[ $errors -gt 0 ]]; then
        print_error "环境检查发现 $errors 个问题，请解决后重新运行"
        exit 1
    fi
    
    print_success "环境检查通过"
}

# 函数：创建数据库
create_database() {
    print_step "创建MySQL数据库"
    
    # 获取MySQL root密码
    if [[ -f "/www/server/mysql/default.pl" ]]; then
        MYSQL_ROOT_PASSWORD=$(cat /www/server/mysql/default.pl | grep password | awk -F"'" '{print $2}')
    elif [[ -f "/www/server/mysql/.pass" ]]; then
        MYSQL_ROOT_PASSWORD=$(cat /www/server/mysql/.pass)
    else
        print_warning "无法自动获取MySQL root密码"
        read -p "请输入MySQL root密码: " -s MYSQL_ROOT_PASSWORD
        echo
    fi
    
    # 生成随机密码
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-16)
    
    print_info "创建数据库和用户..."
    mysql -uroot -p"$MYSQL_ROOT_PASSWORD" <<EOF
CREATE DATABASE IF NOT EXISTS \`$DB_NAME\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON \`$DB_NAME\`.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
EOF
    
    if [[ $? -eq 0 ]]; then
        print_success "数据库创建成功"
        echo "DB_PASSWORD=$DB_PASSWORD" >> "$LOG_FILE"
    else
        print_error "数据库创建失败"
        exit 1
    fi
}

# 函数：准备后端目录和文件
prepare_backend() {
    print_step "准备后端部署"
    
    # 创建后端目录
    print_info "创建后端目录..."
    mkdir -p "$BACKEND_PATH"
    mkdir -p "$BACKEND_PATH/logs"
    mkdir -p "$BACKEND_PATH/instance/uploads/products/{originals,compressed,thumbnails}"
    mkdir -p "$BACKEND_PATH/tmp"
    
    # 设置目录权限
    chown -R www:www "$BACKEND_PATH"
    chmod -R 755 "$BACKEND_PATH"
    chmod -R 777 "$BACKEND_PATH/instance/uploads"
    chmod -R 755 "$BACKEND_PATH/logs"
    chmod -R 755 "$BACKEND_PATH/tmp"
    
    print_success "后端目录准备完成"
    
    # 生成环境配置文件
    print_info "生成后端环境配置..."
    cat > "$BACKEND_PATH/.env" <<EOF
# CPQ系统生产环境配置
# 自动生成时间: $(date '+%Y-%m-%d %H:%M:%S')

# 应用配置
FLASK_ENV=production
DEBUG=False
TESTING=False

# 数据库配置
DATABASE_URL=mysql+pymysql://$DB_USER:$DB_PASSWORD@localhost:3306/$DB_NAME?charset=utf8mb4
MYSQL_HOST=localhost
MYSQL_USER=$DB_USER
MYSQL_PASSWORD=$DB_PASSWORD
MYSQL_DATABASE=$DB_NAME
MYSQL_PORT=3306

# 安全密钥 (请在生产环境中修改这些值)
SECRET_KEY=$(openssl rand -base64 32 | tr -d "=+/")
JWT_SECRET_KEY=$(openssl rand -base64 32 | tr -d "=+/")

# CORS配置
CORS_ORIGINS=http://$FRONTEND_DOMAIN,http://$BACKEND_DOMAIN

# 文件上传配置
UPLOAD_FOLDER=instance/uploads
MAX_CONTENT_LENGTH=52428800
ALLOWED_EXTENSIONS=jpg,jpeg,png,gif,pdf,doc,docx,xls,xlsx

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# AI服务配置 (可选)
# OPENAI_API_KEY=your-openai-api-key
# ZHIPUAI_API_KEY=your-zhipuai-api-key

# 服务器配置
HOST=0.0.0.0
PORT=$BACKEND_PORT
WORKERS=4
EOF
    
    print_success "环境配置文件生成完成"
}

# 函数：准备前端目录
prepare_frontend() {
    print_step "准备前端部署"
    
    # 创建前端目录
    print_info "创建前端目录..."
    mkdir -p "$FRONTEND_PATH"
    mkdir -p "$FRONTEND_PATH/logs"
    mkdir -p "/www/backup/cpq-frontend"
    
    # 设置目录权限
    chown -R www:www "$FRONTEND_PATH"
    chmod -R 755 "$FRONTEND_PATH"
    
    print_success "前端目录准备完成"
}

# 函数：生成Nginx配置
generate_nginx_config() {
    print_step "生成Nginx配置"
    
    # 前端Nginx配置
    print_info "生成前端Nginx配置..."
    cat > "/www/server/panel/vhost/nginx/$FRONTEND_DOMAIN.conf" <<'EOF'
server {
    listen 80;
    server_name cpq.d1bk.com;
    index index.php index.html index.htm default.php default.htm default.html;
    root /www/wwwroot/cpq.d1bk.com/dist;
    
    # 访问日志
    access_log /www/wwwroot/cpq.d1bk.com/logs/access.log;
    error_log /www/wwwroot/cpq.d1bk.com/logs/error.log;
    
    # 安全头
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # API反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时配置
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # 文件上传大小限制
        client_max_body_size 50M;
        
        # 跨域处理
        add_header Access-Control-Allow-Origin * always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
        
        # 预检请求处理
        if ($request_method = 'OPTIONS') {
            return 204;
        }
    }
    
    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        access_log off;
    }
    
    # 上传文件访问
    location /uploads/ {
        alias /www/wwwroot/cpqh.d1bbk.com/instance/uploads/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # SPA路由支持
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # 静态资源优化
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        gzip on;
        gzip_vary on;
        gzip_types text/plain text/css text/javascript application/javascript text/xml application/xml application/xml+rss application/json;
    }
    
    # 禁止访问敏感文件
    location ~ /\. { deny all; }
    location ~ ~$ { deny all; }
    location ~ #.*# { deny all; }
    
    # 禁止PHP执行
    location ~ \.php$ { deny all; }
}
EOF
    
    # 后端域名配置（可选）
    print_info "生成后端域名配置..."
    cat > "/www/server/panel/vhost/nginx/$BACKEND_DOMAIN.conf" <<'EOF'
server {
    listen 80;
    server_name cpqh.d1bbk.com;
    
    # 访问日志
    access_log /www/wwwroot/cpqh.d1bbk.com/logs/nginx_access.log;
    error_log /www/wwwroot/cpqh.d1bbk.com/logs/nginx_error.log;
    
    # 直接代理到Flask应用
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时配置
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # 文件上传大小限制
        client_max_body_size 50M;
    }
}
EOF
    
    print_success "Nginx配置生成完成"
}

# 函数：生成systemd服务文件
generate_systemd_service() {
    print_step "生成systemd服务配置"
    
    cat > "/etc/systemd/system/cpq-api.service" <<EOF
[Unit]
Description=CPQ System API Server
After=network.target mysql.service
Wants=mysql.service

[Service]
Type=exec
User=www
Group=www
WorkingDirectory=$BACKEND_PATH
Environment=PATH=/usr/local/bin:/usr/bin:/bin
ExecStart=/usr/bin/python3 -m gunicorn --config gunicorn.conf.py app:app
ExecReload=/bin/kill -s HUP \$MAINPID
ExecStop=/bin/kill -s QUIT \$MAINPID
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
SyslogIdentifier=cpq-api

[Install]
WantedBy=multi-user.target
EOF
    
    # 生成Gunicorn配置文件
    cat > "$BACKEND_PATH/gunicorn.conf.py" <<EOF
# CPQ系统Gunicorn配置
import multiprocessing
import os

# 基本配置
bind = "127.0.0.1:$BACKEND_PORT"
workers = min(4, multiprocessing.cpu_count() * 2 + 1)
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 300
keepalive = 5

# 用户和权限
user = "www"
group = "www"

# 进程名
proc_name = "cpq-api"

# 日志配置
accesslog = "$BACKEND_PATH/logs/gunicorn_access.log"
errorlog = "$BACKEND_PATH/logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 性能优化
preload_app = True
worker_tmp_dir = "/dev/shm"

# 重载配置
reload = False
reload_engine = "auto"

# PID文件
pidfile = "$BACKEND_PATH/tmp/gunicorn.pid"

# 错误处理
def when_ready(server):
    server.log.info("CPQ API服务器启动完成")

def on_exit(server):
    server.log.info("CPQ API服务器关闭")
EOF
    
    # 重载systemd配置
    systemctl daemon-reload
    
    print_success "systemd服务配置完成"
}

# 函数：生成启动脚本
generate_start_script() {
    print_step "生成启动脚本"
    
    cat > "$BACKEND_PATH/start.sh" <<'EOF'
#!/bin/bash

# CPQ系统服务管理脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${YELLOW}ℹ️ $1${NC}"; }

case "$1" in
    start)
        print_info "启动CPQ API服务..."
        sudo systemctl start cpq-api
        if systemctl is-active --quiet cpq-api; then
            print_success "CPQ API服务启动成功"
            print_info "服务状态:"
            systemctl status cpq-api --no-pager -l
        else
            print_error "CPQ API服务启动失败"
            print_info "查看错误日志:"
            journalctl -u cpq-api --no-pager -l
            exit 1
        fi
        ;;
    stop)
        print_info "停止CPQ API服务..."
        sudo systemctl stop cpq-api
        print_success "CPQ API服务已停止"
        ;;
    restart)
        print_info "重启CPQ API服务..."
        sudo systemctl restart cpq-api
        if systemctl is-active --quiet cpq-api; then
            print_success "CPQ API服务重启成功"
        else
            print_error "CPQ API服务重启失败"
            exit 1
        fi
        ;;
    status)
        print_info "CPQ API服务状态:"
        systemctl status cpq-api --no-pager
        ;;
    logs)
        print_info "查看CPQ API服务日志:"
        journalctl -u cpq-api -f
        ;;
    health)
        print_info "检查API健康状态..."
        if curl -sf http://127.0.0.1:5000/health >/dev/null; then
            print_success "API健康检查通过"
        else
            print_error "API健康检查失败"
            exit 1
        fi
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|logs|health}"
        exit 1
        ;;
esac
EOF
    
    chmod +x "$BACKEND_PATH/start.sh"
    print_success "启动脚本生成完成"
}

# 函数：生成部署验证脚本
generate_validation_script() {
    print_step "生成部署验证脚本"
    
    cat > "$BACKEND_PATH/validate_deployment.sh" <<'EOF'
#!/bin/bash

# CPQ系统部署验证脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️ $1${NC}"; }

errors=0

echo "=========================================="
echo "        CPQ系统部署验证检查"
echo "=========================================="
echo

# 检查服务状态
print_info "检查CPQ API服务状态..."
if systemctl is-active --quiet cpq-api; then
    print_success "CPQ API服务运行正常"
else
    print_error "CPQ API服务未运行"
    ((errors++))
fi

# 检查端口监听
print_info "检查端口监听状态..."
if netstat -tlnp | grep ":5000 " >/dev/null; then
    print_success "端口5000监听正常"
else
    print_error "端口5000未监听"
    ((errors++))
fi

# 检查数据库连接
print_info "检查数据库连接..."
if python3 -c "
from app import app
with app.app_context():
    from src.models import db
    try:
        db.engine.execute('SELECT 1')
        print('数据库连接成功')
    except Exception as e:
        print(f'数据库连接失败: {e}')
        exit(1)
" 2>/dev/null; then
    print_success "数据库连接正常"
else
    print_error "数据库连接失败"
    ((errors++))
fi

# 检查API健康状态
print_info "检查API健康状态..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/health 2>/dev/null)
if [[ "$response" == "200" ]]; then
    print_success "API健康检查通过"
else
    print_error "API健康检查失败 (HTTP: $response)"
    ((errors++))
fi

# 检查Nginx配置
print_info "检查Nginx配置..."
if nginx -t 2>/dev/null; then
    print_success "Nginx配置检查通过"
else
    print_error "Nginx配置检查失败"
    ((errors++))
fi

# 检查前端访问
print_info "检查前端页面访问..."
if curl -s http://cpq.d1bk.com >/dev/null; then
    print_success "前端页面访问正常"
else
    print_warning "前端页面访问异常（可能是DNS解析问题）"
fi

# 检查文件权限
print_info "检查文件权限..."
upload_dir="/www/wwwroot/cpqh.d1bbk.com/instance/uploads"
if [[ -d "$upload_dir" && -w "$upload_dir" ]]; then
    print_success "上传目录权限正常"
else
    print_error "上传目录权限异常"
    ((errors++))
fi

echo
echo "=========================================="
if [[ $errors -eq 0 ]]; then
    print_success "所有检查项通过！部署验证成功"
    echo
    print_info "访问信息:"
    echo "  前端地址: http://cpq.d1bk.com"
    echo "  后端地址: http://cpqh.d1bbk.com"
    echo "  管理员账号: admin / admin123"
    echo
    print_info "服务管理命令:"
    echo "  启动服务: ./start.sh start"
    echo "  停止服务: ./start.sh stop"
    echo "  重启服务: ./start.sh restart"
    echo "  查看状态: ./start.sh status"
    echo "  查看日志: ./start.sh logs"
else
    print_error "发现 $errors 个问题，请检查并修复"
    echo
    print_info "常用故障排除命令:"
    echo "  查看服务日志: journalctl -u cpq-api -f"
    echo "  查看应用日志: tail -f logs/app.log"
    echo "  查看Nginx日志: tail -f /www/server/nginx/logs/error.log"
    exit 1
fi
EOF
    
    chmod +x "$BACKEND_PATH/validate_deployment.sh"
    print_success "验证脚本生成完成"
}

# 函数：创建数据库初始化脚本
create_db_init_script() {
    print_step "创建数据库初始化脚本"
    
    cat > "$BACKEND_PATH/init_database.py" <<'EOF'
#!/usr/bin/env python3
"""
CPQ系统数据库初始化脚本
"""

import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def init_database():
    """初始化数据库"""
    try:
        from app import app
        from src.models import db
        from src.models.user import User
        from src.models.settings import Settings
        
        print("🚀 开始初始化数据库...")
        
        with app.app_context():
            # 创建所有表
            print("📋 创建数据库表...")
            db.create_all()
            print("✅ 数据库表创建完成")
            
            # 检查是否已有管理员用户
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                print("👤 创建管理员用户...")
                admin_user = User(
                    username='admin',
                    email='admin@example.com',
                    full_name='系统管理员',
                    role='admin'
                )
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                print("✅ 管理员用户创建完成")
            else:
                print("✅ 管理员用户已存在")
            
            # 检查是否已有系统设置
            settings = Settings.query.first()
            if not settings:
                print("⚙️ 创建系统默认设置...")
                settings = Settings(
                    company_name='CPQ演示公司',
                    company_address='演示地址',
                    company_phone='000-0000-0000',
                    company_email='demo@example.com',
                    tax_rate=0.13,
                    currency_symbol='¥',
                    invoice_prefix='INV',
                    quote_prefix='QUO',
                    email_smtp_server='smtp.example.com',
                    email_smtp_port=587,
                    email_username='',
                    email_password='',
                    pdf_company_logo='',
                    pdf_footer_text='感谢您的业务！',
                    created_by=admin_user.id,
                    updated_by=admin_user.id
                )
                db.session.add(settings)
                print("✅ 系统默认设置创建完成")
            else:
                print("✅ 系统设置已存在")
            
            # 提交所有更改
            db.session.commit()
            print("✅ 数据库初始化完成")
            
            print("\n🎉 数据库初始化成功！")
            print("📋 系统信息:")
            print(f"   管理员用户: admin")
            print(f"   管理员密码: admin123")
            print(f"   数据库表数量: {len(db.metadata.tables)}")
            print(f"   初始化时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        print("请确保已安装所需的Python依赖包")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    init_database()
EOF
    
    chmod +x "$BACKEND_PATH/init_database.py"
    print_success "数据库初始化脚本创建完成"
}

# 函数：显示部署摘要
show_deployment_summary() {
    print_step "部署摘要"
    
    cat <<EOF

========================================
       CPQ系统部署配置完成
========================================

📋 部署信息:
   前端域名: http://$FRONTEND_DOMAIN
   后端域名: http://$BACKEND_DOMAIN  
   数据库名: $DB_NAME
   数据库用户: $DB_USER
   
🗂️ 目录结构:
   前端目录: $FRONTEND_PATH
   后端目录: $BACKEND_PATH
   日志目录: $BACKEND_PATH/logs
   上传目录: $BACKEND_PATH/instance/uploads
   
⚙️ 配置文件:
   环境配置: $BACKEND_PATH/.env
   Nginx配置: /www/server/panel/vhost/nginx/$FRONTEND_DOMAIN.conf
   系统服务: /etc/systemd/system/cpq-api.service
   
🔧 管理命令:
   启动服务: cd $BACKEND_PATH && ./start.sh start
   停止服务: cd $BACKEND_PATH && ./start.sh stop
   重启服务: cd $BACKEND_PATH && ./start.sh restart
   查看状态: cd $BACKEND_PATH && ./start.sh status
   查看日志: cd $BACKEND_PATH && ./start.sh logs
   验证部署: cd $BACKEND_PATH && ./validate_deployment.sh
   
📝 日志文件:
   部署日志: $LOG_FILE
   应用日志: $BACKEND_PATH/logs/app.log
   Gunicorn日志: $BACKEND_PATH/logs/gunicorn_error.log
   Nginx日志: $FRONTEND_PATH/logs/error.log

🔐 安全提醒:
   1. 请修改 $BACKEND_PATH/.env 中的安全密钥
   2. 数据库密码已保存在部署日志中
   3. 请及时修改admin用户的默认密码
   4. 建议配置SSL证书启用HTTPS

========================================

EOF
    
    print_success "部署配置完成！"
    print_info "请按以下步骤继续:"
    echo "  1. 上传项目代码文件到对应目录"
    echo "  2. 安装Python依赖: pip install -r requirements-production.txt"
    echo "  3. 初始化数据库: python3 init_database.py"
    echo "  4. 启动服务: ./start.sh start"
    echo "  5. 验证部署: ./validate_deployment.sh"
}

# 主函数
main() {
    print_info "开始CPQ系统宝塔面板一键部署配置"
    print_info "部署日志: $LOG_FILE"
    echo
    
    # 环境检查
    check_environment
    echo
    
    # 用户确认
    wait_for_confirm "环境检查通过，是否开始部署配置？"
    echo
    
    # 创建数据库
    create_database
    echo
    
    # 准备目录结构
    prepare_backend
    prepare_frontend
    echo
    
    # 生成配置文件
    generate_nginx_config
    generate_systemd_service
    generate_start_script
    generate_validation_script
    create_db_init_script
    echo
    
    # 重载Nginx配置
    print_info "重载Nginx配置..."
    nginx -t && nginx -s reload
    if [[ $? -eq 0 ]]; then
        print_success "Nginx配置重载成功"
    else
        print_error "Nginx配置重载失败"
    fi
    echo
    
    # 显示摘要
    show_deployment_summary
    
    print_success "CPQ系统宝塔面板部署配置完成！"
}

# 执行主函数
main "$@"