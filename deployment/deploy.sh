#!/bin/bash
# CPQ系统宝塔面板一键部署脚本
# 使用方法: chmod +x deploy.sh && ./deploy.sh

set -e

# 配置变量
FRONTEND_DOMAIN="cpq.d1bk.com"
BACKEND_DOMAIN="cpqh.d1bbk.com"
FRONTEND_PATH="/www/wwwroot/$FRONTEND_DOMAIN"
BACKEND_PATH="/www/wwwroot/$BACKEND_DOMAIN"
DB_NAME="cpq_production"
DB_USER="cpq_user"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "此脚本需要root权限运行"
        exit 1
    fi
}

# 检查宝塔面板是否安装
check_bt_panel() {
    print_status "检查宝塔面板安装状态..."
    if ! command -v bt >/dev/null 2>&1; then
        print_error "未检测到宝塔面板，请先安装宝塔面板"
        exit 1
    fi
    print_success "宝塔面板已安装"
}

# 检查必要服务
check_services() {
    print_status "检查必要服务..."
    
    services=("nginx" "mysql")
    for service in "${services[@]}"; do
        if systemctl is-active --quiet $service; then
            print_success "$service 服务正在运行"
        else
            print_warning "$service 服务未运行，正在启动..."
            systemctl start $service
        fi
    done
}

# 创建数据库
create_database() {
    print_status "创建数据库..."
    
    read -s -p "请输入MySQL root密码: " mysql_root_password
    echo
    
    read -s -p "请设置数据库用户密码: " db_password
    echo
    
    mysql -u root -p$mysql_root_password << EOF
CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$db_password';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
EOF
    
    print_success "数据库创建完成"
    echo "数据库连接信息:"
    echo "  数据库名: $DB_NAME"
    echo "  用户名: $DB_USER"
    echo "  密码: $db_password"
}

# 部署后端
deploy_backend() {
    print_status "部署后端应用..."
    
    # 创建项目目录
    mkdir -p $BACKEND_PATH
    cd $BACKEND_PATH
    
    # 创建Python虚拟环境
    python3 -m venv venv
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装Gunicorn
    pip install gunicorn
    
    print_success "后端环境准备完成"
    print_warning "请上传后端代码到: $BACKEND_PATH"
    print_warning "然后运行: pip install -r requirements.txt"
}

# 部署前端
deploy_frontend() {
    print_status "部署前端应用..."
    
    # 创建前端目录
    mkdir -p $FRONTEND_PATH
    
    # 设置权限
    chown -R www:www $FRONTEND_PATH
    chmod -R 755 $FRONTEND_PATH
    
    print_success "前端环境准备完成"
    print_warning "请构建前端项目并上传到: $FRONTEND_PATH"
}

# 配置Nginx
configure_nginx() {
    print_status "配置Nginx..."
    
    # 前端Nginx配置
    cat > /www/server/panel/vhost/nginx/$FRONTEND_DOMAIN.conf << 'EOF'
server {
    listen 80;
    server_name cpq.d1bk.com;
    root /www/wwwroot/cpq.d1bk.com;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
    }
    
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 30d;
    }
}
EOF
    
    # 后端Nginx配置
    cat > /www/server/panel/vhost/nginx/$BACKEND_DOMAIN.conf << 'EOF'
server {
    listen 80;
    server_name cpqh.d1bbk.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        add_header Access-Control-Allow-Origin "http://cpq.d1bk.com" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
    }
    
    location /uploads/ {
        alias /www/wwwroot/cpqh.d1bbk.com/instance/uploads/;
    }
}
EOF
    
    # 重载Nginx配置
    nginx -t && systemctl reload nginx
    print_success "Nginx配置完成"
}

# 创建systemd服务
create_systemd_service() {
    print_status "创建systemd服务..."
    
    cat > /etc/systemd/system/cpq-api.service << EOF
[Unit]
Description=CPQ API Server
After=network.target mysql.service

[Service]
Type=notify
User=www
Group=www
WorkingDirectory=$BACKEND_PATH
Environment=PATH=$BACKEND_PATH/venv/bin
EnvironmentFile=$BACKEND_PATH/.env
ExecStart=$BACKEND_PATH/venv/bin/gunicorn --config $BACKEND_PATH/gunicorn.conf.py app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable cpq-api
    
    print_success "Systemd服务创建完成"
}

# 创建监控脚本
create_monitoring() {
    print_status "创建监控脚本..."
    
    mkdir -p /www/server/scripts
    
    cat > /www/server/scripts/cpq_health_check.sh << 'EOF'
#!/bin/bash
# CPQ系统健康检查

echo "=== CPQ Health Check $(date) ==="

# 检查服务状态
systemctl is-active --quiet cpq-api && echo "✅ CPQ API: Running" || echo "❌ CPQ API: Stopped"
systemctl is-active --quiet nginx && echo "✅ Nginx: Running" || echo "❌ Nginx: Stopped"
systemctl is-active --quiet mysql && echo "✅ MySQL: Running" || echo "❌ MySQL: Stopped"

# 检查端口
netstat -tlnp | grep :80 > /dev/null && echo "✅ Port 80: Listening" || echo "❌ Port 80: Not listening"
netstat -tlnp | grep :5000 > /dev/null && echo "✅ Port 5000: Listening" || echo "❌ Port 5000: Not listening"

# 检查磁盘空间
df -h | grep -E "/$" | awk '{print "💾 Disk Usage: " $5}'

# 检查内存
free -m | awk 'NR==2{printf "🧠 Memory Usage: %.0f%%\n", $3*100/$2}'

# 检查API健康
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "✅ API Health: OK"
else
    echo "❌ API Health: Failed"
fi

echo "=========================="
EOF
    
    chmod +x /www/server/scripts/cpq_health_check.sh
    
    # 添加到crontab (每5分钟检查一次)
    (crontab -l 2>/dev/null; echo "*/5 * * * * /www/server/scripts/cpq_health_check.sh >> /www/wwwlogs/health_check.log") | crontab -
    
    print_success "监控脚本创建完成"
}

# 设置日志轮转
setup_log_rotation() {
    print_status "设置日志轮转..."
    
    cat > /etc/logrotate.d/cpq-system << EOF
/www/wwwlogs/cpq*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    sharedscripts
    postrotate
        systemctl reload nginx
    endscript
}

$BACKEND_PATH/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF
    
    print_success "日志轮转设置完成"
}

# 主函数
main() {
    print_status "开始CPQ系统部署..."
    
    check_root
    check_bt_panel
    check_services
    
    echo
    print_warning "即将执行以下操作:"
    echo "1. 创建数据库"
    echo "2. 部署后端应用"
    echo "3. 部署前端应用" 
    echo "4. 配置Nginx"
    echo "5. 创建系统服务"
    echo "6. 设置监控和日志"
    echo
    
    read -p "是否继续? (y/N): " confirm
    if [[ $confirm != "y" && $confirm != "Y" ]]; then
        print_warning "部署已取消"
        exit 0
    fi
    
    create_database
    deploy_backend
    deploy_frontend
    configure_nginx
    create_systemd_service
    create_monitoring
    setup_log_rotation
    
    print_success "CPQ系统部署完成!"
    echo
    echo "📋 后续步骤:"
    echo "1. 上传后端代码到: $BACKEND_PATH"
    echo "2. 安装Python依赖: cd $BACKEND_PATH && source venv/bin/activate && pip install -r requirements.txt"
    echo "3. 配置环境变量: 编辑 $BACKEND_PATH/.env"
    echo "4. 初始化数据库: python scripts/init_db.py"
    echo "5. 构建并上传前端代码到: $FRONTEND_PATH"
    echo "6. 启动服务: systemctl start cpq-api"
    echo
    echo "🌐 访问地址:"
    echo "前端: http://$FRONTEND_DOMAIN"
    echo "后端: http://$BACKEND_DOMAIN"
    echo
    echo "📊 监控日志: /www/wwwlogs/health_check.log"
}

# 运行主函数
main "$@"