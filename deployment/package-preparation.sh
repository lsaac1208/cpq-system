#!/bin/bash

# =============================================================================
# CPQ系统部署包准备脚本
# 版本: 1.0
# 作者: DevOps团队  
# 日期: 2025-01-25
# 功能: 创建完整的宝塔面板部署包
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# 项目配置
PROJECT_NAME="CPQ系统"
VERSION="1.0.0"
BUILD_DATE=$(date '+%Y%m%d_%H%M%S')
DEPLOY_PACKAGE_NAME="cpq-baota-deploy-${BUILD_DATE}"

# 路径配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PACKAGE_DIR="${SCRIPT_DIR}/${DEPLOY_PACKAGE_NAME}"

# 函数定义
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}[$(date '+%H:%M:%S')] ${message}${NC}"
}

print_success() { print_message "$GREEN" "✅ $1"; }
print_error() { print_message "$RED" "❌ $1"; }
print_warning() { print_message "$YELLOW" "⚠️ $1"; }
print_info() { print_message "$BLUE" "ℹ️ $1"; }
print_step() { print_message "$PURPLE" "🚀 步骤: $1"; }

# 检查依赖
check_dependencies() {
    print_step "检查依赖环境"
    
    local deps=("tar" "gzip" "find" "du")
    for dep in "${deps[@]}"; do
        if command -v "$dep" >/dev/null 2>&1; then
            print_success "$dep 可用"
        else
            print_error "$dep 不可用"
            exit 1
        fi
    done
}

# 清理旧的构建目录
clean_build_dir() {
    print_step "清理构建环境"
    
    if [[ -d "$PACKAGE_DIR" ]]; then
        print_info "删除旧的构建目录..."
        rm -rf "$PACKAGE_DIR"
    fi
    
    mkdir -p "$PACKAGE_DIR"
    print_success "构建目录创建: $PACKAGE_DIR"
}

# 准备后端文件
prepare_backend_files() {
    print_step "准备后端文件"
    
    local backend_src="${PROJECT_ROOT}/apps/api"
    local backend_dst="${PACKAGE_DIR}/backend"
    
    if [[ ! -d "$backend_src" ]]; then
        print_error "后端源码目录不存在: $backend_src"
        exit 1
    fi
    
    print_info "创建后端部署目录..."
    mkdir -p "$backend_dst"
    
    # 复制核心文件，排除不需要的文件
    print_info "复制后端核心文件..."
    rsync -av \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='*.pyo' \
        --exclude='.git' \
        --exclude='node_modules' \
        --exclude='instance/cpq_system.db' \
        --exclude='instance/cpq_database.db' \
        --exclude='logs' \
        --exclude='tmp' \
        --exclude='.pytest_cache' \
        --exclude='coverage' \
        --exclude='.coverage' \
        --exclude='htmlcov' \
        "$backend_src/" "$backend_dst/"
    
    # 确保关键目录存在
    print_info "创建必要的目录结构..."
    mkdir -p "$backend_dst/instance/uploads/products/"{originals,compressed,thumbnails}
    mkdir -p "$backend_dst/logs"
    mkdir -p "$backend_dst/tmp"
    
    # 添加部署配置文件
    print_info "添加部署配置文件..."
    
    # 复制生产环境配置
    if [[ -f "$backend_src/.env.production" ]]; then
        cp "$backend_src/.env.production" "$backend_dst/"
        print_success ".env.production 复制完成"
    fi
    
    if [[ -f "$backend_src/gunicorn.conf.py" ]]; then
        cp "$backend_src/gunicorn.conf.py" "$backend_dst/"
        print_success "gunicorn.conf.py 复制完成"
    fi
    
    if [[ -f "$backend_src/cpq-api.service" ]]; then
        cp "$backend_src/cpq-api.service" "$backend_dst/"
        print_success "cpq-api.service 复制完成"
    fi
    
    # 计算后端文件大小
    local backend_size=$(du -sh "$backend_dst" | cut -f1)
    print_success "后端文件准备完成 (大小: $backend_size)"
}

# 准备前端文件  
prepare_frontend_files() {
    print_step "准备前端文件"
    
    local frontend_dist="${PROJECT_ROOT}/apps/web/dist"
    local frontend_dst="${PACKAGE_DIR}/frontend"
    
    if [[ ! -d "$frontend_dist" ]]; then
        print_error "前端构建产物不存在: $frontend_dist"
        print_info "请先运行: cd apps/web && npm run build:prod"
        exit 1
    fi
    
    print_info "创建前端部署目录..."
    mkdir -p "$frontend_dst"
    
    # 复制前端构建产物
    print_info "复制前端构建文件..."
    cp -r "$frontend_dist"/* "$frontend_dst/"
    
    # 添加前端配置文件
    local frontend_config="${PROJECT_ROOT}/apps/web/deploy"
    if [[ -d "$frontend_config" ]]; then
        print_info "复制前端配置文件..."
        cp "$frontend_config/cpq-frontend.conf" "$frontend_dst/" 2>/dev/null || true
        cp "$frontend_config/deploy-frontend.sh" "$frontend_dst/" 2>/dev/null || true
    fi
    
    # 计算前端文件大小
    local frontend_size=$(du -sh "$frontend_dst" | cut -f1)
    print_success "前端文件准备完成 (大小: $frontend_size)"
}

# 准备配置文件
prepare_config_files() {
    print_step "准备配置文件"
    
    local config_dst="${PACKAGE_DIR}/config"
    mkdir -p "$config_dst"
    
    # Nginx配置文件
    print_info "准备Nginx配置文件..."
    cat > "$config_dst/nginx-frontend.conf" <<'EOF'
server {
    listen 80;
    server_name cpq.d1bk.com;
    index index.html;
    root /www/wwwroot/cpq.d1bk.com/dist;
    
    # 访问日志
    access_log /www/wwwroot/cpq.d1bk.com/logs/access.log;
    error_log /www/wwwroot/cpq.d1bk.com/logs/error.log;
    
    # 安全头
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # API反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        client_max_body_size 50M;
        
        add_header Access-Control-Allow-Origin * always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
        
        if ($request_method = 'OPTIONS') {
            return 204;
        }
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
    
    location ~ /\. { deny all; }
    location ~ \.php$ { deny all; }
}
EOF
    
    # systemd服务文件
    print_info "准备systemd服务文件..."
    cat > "$config_dst/cpq-api.service" <<'EOF'
[Unit]
Description=CPQ System API Server
After=network.target mysql.service
Wants=mysql.service

[Service]
Type=exec
User=www
Group=www
WorkingDirectory=/www/wwwroot/cpqh.d1bbk.com
Environment=PATH=/usr/local/bin:/usr/bin:/bin
ExecStart=/usr/bin/python3 -m gunicorn --config gunicorn.conf.py app:app
ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s QUIT $MAINPID
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
SyslogIdentifier=cpq-api

[Install]
WantedBy=multi-user.target
EOF
    
    # 环境变量模板
    print_info "准备环境变量模板..."
    cat > "$config_dst/.env.template" <<'EOF'
# CPQ系统生产环境配置模板
# 使用前请复制为 .env 并修改相关配置

# 应用配置
FLASK_ENV=production
DEBUG=False
TESTING=False

# 数据库配置 (请修改为实际值)
DATABASE_URL=mysql+pymysql://cpq_user:YOUR_DB_PASSWORD@localhost:3306/cpq_system?charset=utf8mb4
MYSQL_HOST=localhost
MYSQL_USER=cpq_user
MYSQL_PASSWORD=YOUR_DB_PASSWORD
MYSQL_DATABASE=cpq_system
MYSQL_PORT=3306

# 安全密钥 (请修改为随机字符串)
SECRET_KEY=YOUR_SECRET_KEY_HERE
JWT_SECRET_KEY=YOUR_JWT_SECRET_KEY_HERE

# CORS配置
CORS_ORIGINS=http://cpq.d1bk.com,http://cpqh.d1bbk.com

# 文件上传配置
UPLOAD_FOLDER=instance/uploads
MAX_CONTENT_LENGTH=52428800
ALLOWED_EXTENSIONS=jpg,jpeg,png,gif,pdf,doc,docx,xls,xlsx

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# 服务器配置
HOST=0.0.0.0
PORT=5000
WORKERS=4
EOF
    
    print_success "配置文件准备完成"
}

# 准备部署脚本
prepare_deployment_scripts() {
    print_step "准备部署脚本"
    
    local scripts_dst="${PACKAGE_DIR}/scripts"
    mkdir -p "$scripts_dst"
    
    # 复制自动化脚本
    if [[ -f "$SCRIPT_DIR/baota-deploy-automation.sh" ]]; then
        cp "$SCRIPT_DIR/baota-deploy-automation.sh" "$scripts_dst/"
        chmod +x "$scripts_dst/baota-deploy-automation.sh"
        print_success "自动化部署脚本复制完成"
    fi
    
    if [[ -f "$SCRIPT_DIR/cpq-deployment-validator.py" ]]; then
        cp "$SCRIPT_DIR/cpq-deployment-validator.py" "$scripts_dst/"
        chmod +x "$scripts_dst/cpq-deployment-validator.py"
        print_success "部署验证脚本复制完成"
    fi
    
    # 创建快速安装脚本
    print_info "创建快速安装脚本..."
    cat > "$scripts_dst/quick-install.sh" <<'EOF'
#!/bin/bash

# CPQ系统快速安装脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${YELLOW}ℹ️ $1${NC}"; }

echo "======================================"
echo "       CPQ系统快速安装向导"
echo "======================================"
echo

# 检查root权限
if [[ $EUID -ne 0 ]]; then
    print_error "请使用root权限运行此脚本"
    exit 1
fi

# 检查宝塔面板
if [[ ! -d "/www/server/panel" ]]; then
    print_error "宝塔面板未安装，请先安装宝塔面板"
    exit 1
fi

print_info "开始CPQ系统安装..."

# 1. 运行自动化配置脚本
print_info "步骤1: 运行环境配置..."
if [[ -f "./baota-deploy-automation.sh" ]]; then
    chmod +x ./baota-deploy-automation.sh
    ./baota-deploy-automation.sh
else
    print_error "自动化配置脚本不存在"
    exit 1
fi

# 2. 部署后端文件
print_info "步骤2: 部署后端文件..."
if [[ -d "../backend" ]]; then
    rsync -av ../backend/ /www/wwwroot/cpqh.d1bbk.com/
    chown -R www:www /www/wwwroot/cpqh.d1bbk.com/
    chmod -R 755 /www/wwwroot/cpqh.d1bbk.com/
    chmod -R 777 /www/wwwroot/cpqh.d1bbk.com/instance/uploads/
    print_success "后端文件部署完成"
else
    print_error "后端文件目录不存在"
    exit 1
fi

# 3. 部署前端文件
print_info "步骤3: 部署前端文件..."
if [[ -d "../frontend" ]]; then
    mkdir -p /www/wwwroot/cpq.d1bk.com/dist
    rsync -av ../frontend/ /www/wwwroot/cpq.d1bk.com/dist/
    chown -R www:www /www/wwwroot/cpq.d1bk.com/
    print_success "前端文件部署完成"
else
    print_error "前端文件目录不存在"
    exit 1
fi

# 4. 安装Python依赖
print_info "步骤4: 安装Python依赖..."
cd /www/wwwroot/cpqh.d1bbk.com/
pip3 install -r requirements-production.txt
print_success "Python依赖安装完成"

# 5. 初始化数据库
print_info "步骤5: 初始化数据库..."
python3 init_database.py
print_success "数据库初始化完成"

# 6. 启动服务
print_info "步骤6: 启动服务..."
./start.sh start
print_success "服务启动完成"

# 7. 运行验证
print_info "步骤7: 运行部署验证..."
python3 ../scripts/cpq-deployment-validator.py

echo
print_success "CPQ系统安装完成！"
print_info "访问地址: http://cpq.d1bk.com"
print_info "管理员账号: admin / admin123"
EOF
    
    chmod +x "$scripts_dst/quick-install.sh"
    
    print_success "部署脚本准备完成"
}

# 准备文档
prepare_documentation() {
    print_step "准备部署文档"
    
    local docs_dst="${PACKAGE_DIR}/docs"
    mkdir -p "$docs_dst"
    
    # 复制已有的文档
    if [[ -f "$SCRIPT_DIR/step-by-step-deployment-guide.md" ]]; then
        cp "$SCRIPT_DIR/step-by-step-deployment-guide.md" "$docs_dst/"
        print_success "分步部署指南复制完成"
    fi
    
    # 复制现有的部署文档
    local existing_docs=(
        "${PROJECT_ROOT}/apps/api/BaoTa_Deploy_Guide.md"
        "${PROJECT_ROOT}/apps/web/deploy/Frontend_BaoTa_Guide.md"
        "${PROJECT_ROOT}/deploy/FINAL_DEPLOYMENT_CHECKLIST.md"
        "${PROJECT_ROOT}/宝塔部署完整包说明.md"
    )
    
    for doc in "${existing_docs[@]}"; do
        if [[ -f "$doc" ]]; then
            cp "$doc" "$docs_dst/"
            print_success "文档复制完成: $(basename "$doc")"
        fi
    done
    
    # 创建README
    cat > "$docs_dst/README.md" <<EOF
# CPQ系统宝塔面板部署包

## 📦 部署包信息

- **项目名称**: $PROJECT_NAME
- **版本**: $VERSION  
- **构建时间**: $(date '+%Y-%m-%d %H:%M:%S')
- **构建包**: $DEPLOY_PACKAGE_NAME

## 🚀 快速开始

### 最简单的安装方式：

1. 解压部署包到服务器
2. 进入 scripts/ 目录
3. 运行快速安装脚本：
   \`\`\`bash
   cd scripts/
   chmod +x quick-install.sh
   ./quick-install.sh
   \`\`\`

### 详细安装步骤：

请查看 **step-by-step-deployment-guide.md** 获取详细的分步安装指南。

## 📁 包结构

\`\`\`
$DEPLOY_PACKAGE_NAME/
├── backend/                    # 后端源码和配置
├── frontend/                   # 前端构建产物  
├── config/                     # 配置文件模板
├── scripts/                    # 自动化部署脚本
├── docs/                       # 部署文档
└── README.md                   # 本文件
\`\`\`

## 🔧 系统要求

- **操作系统**: CentOS 7+ / Ubuntu 18+ / Debian 9+
- **宝塔面板**: 7.7.0+
- **Python**: 3.8+
- **MySQL**: 5.7+ / 8.0+
- **Nginx**: 1.18+
- **内存**: 2GB+ 推荐
- **硬盘**: 5GB+ 可用空间

## 🌐 域名配置

安装前请确保以下域名已解析到服务器IP：
- \`cpq.d1bk.com\` (前端)
- \`cpqh.d1bbk.com\` (后端)

## 📞 技术支持

如果遇到问题，请：

1. 查看详细的部署文档
2. 运行验证脚本检查部署状态
3. 检查日志文件获取错误信息

**构建信息**: $BUILD_DATE
EOF
    
    print_success "文档准备完成"
}

# 生成包信息
generate_package_info() {
    print_step "生成包信息"
    
    # 计算各部分大小
    local backend_size=$(du -sh "$PACKAGE_DIR/backend" 2>/dev/null | cut -f1 || echo "N/A")
    local frontend_size=$(du -sh "$PACKAGE_DIR/frontend" 2>/dev/null | cut -f1 || echo "N/A")
    local total_size=$(du -sh "$PACKAGE_DIR" | cut -f1)
    
    # 统计文件数量
    local total_files=$(find "$PACKAGE_DIR" -type f | wc -l)
    
    # 生成信息文件
    cat > "$PACKAGE_DIR/package-info.json" <<EOF
{
  "package_name": "$DEPLOY_PACKAGE_NAME",
  "project_name": "$PROJECT_NAME",
  "version": "$VERSION",
  "build_date": "$BUILD_DATE",
  "build_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "sizes": {
    "backend": "$backend_size",
    "frontend": "$frontend_size", 
    "total": "$total_size"
  },
  "file_count": $total_files,
  "components": {
    "backend_included": $(test -d "$PACKAGE_DIR/backend" && echo "true" || echo "false"),
    "frontend_included": $(test -d "$PACKAGE_DIR/frontend" && echo "true" || echo "false"),
    "config_included": $(test -d "$PACKAGE_DIR/config" && echo "true" || echo "false"),
    "scripts_included": $(test -d "$PACKAGE_DIR/scripts" && echo "true" || echo "false"),
    "docs_included": $(test -d "$PACKAGE_DIR/docs" && echo "true" || echo "false")
  },
  "requirements": {
    "os": "Linux (CentOS 7+ / Ubuntu 18+ / Debian 9+)",
    "python": "3.8+",
    "mysql": "5.7+ / 8.0+",
    "nginx": "1.18+",
    "baota_panel": "7.7.0+",
    "memory": "2GB+",
    "disk": "5GB+"
  }
}
EOF
    
    print_success "包信息生成完成"
}

# 创建压缩包
create_archive() {
    print_step "创建部署压缩包"
    
    local archive_name="${DEPLOY_PACKAGE_NAME}.tar.gz"
    local archive_path="${SCRIPT_DIR}/${archive_name}"
    
    print_info "创建压缩包: $archive_name"
    cd "$SCRIPT_DIR"
    tar -czf "$archive_name" "$DEPLOY_PACKAGE_NAME/"
    
    if [[ -f "$archive_path" ]]; then
        local archive_size=$(du -sh "$archive_path" | cut -f1)
        print_success "压缩包创建完成: $archive_path (大小: $archive_size)"
        
        # 生成MD5校验
        local md5_hash=$(md5sum "$archive_path" | cut -d' ' -f1)
        echo "$md5_hash  $archive_name" > "${archive_path}.md5"
        print_success "MD5校验文件生成: ${archive_path}.md5"
    else
        print_error "压缩包创建失败"
        exit 1
    fi
}

# 显示完成信息
show_completion_info() {
    print_step "部署包准备完成"
    
    local archive_name="${DEPLOY_PACKAGE_NAME}.tar.gz"
    local archive_path="${SCRIPT_DIR}/${archive_name}"
    local archive_size=$(du -sh "$archive_path" | cut -f1)
    local total_files=$(find "$PACKAGE_DIR" -type f | wc -l)
    
    cat <<EOF

========================================
       CPQ系统部署包准备完成
========================================

📦 部署包信息:
   包名称: $DEPLOY_PACKAGE_NAME
   版本: $VERSION
   构建时间: $(date '+%Y-%m-%d %H:%M:%S')

📊 包统计:
   压缩包大小: $archive_size
   文件总数: $total_files
   包含组件: 后端 + 前端 + 配置 + 脚本 + 文档

📁 生成的文件:
   部署包: $archive_path  
   校验文件: ${archive_path}.md5
   解压目录: $PACKAGE_DIR

🚀 使用方法:
   1. 上传压缩包到宝塔服务器
   2. 解压: tar -xzf $archive_name
   3. 进入目录: cd $DEPLOY_PACKAGE_NAME
   4. 运行安装: cd scripts && ./quick-install.sh

📝 详细文档:
   - 查看 docs/step-by-step-deployment-guide.md
   - 查看 docs/README.md

========================================

EOF
    
    print_success "部署包准备完成！"
    print_info "部署包路径: $archive_path"
}

# 主函数
main() {
    print_info "开始准备CPQ系统宝塔面板部署包"
    print_info "构建时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo
    
    # 执行各个步骤
    check_dependencies
    clean_build_dir
    prepare_backend_files
    prepare_frontend_files  
    prepare_config_files
    prepare_deployment_scripts
    prepare_documentation
    generate_package_info
    create_archive
    
    # 显示完成信息
    show_completion_info
}

# 执行主函数
main "$@"