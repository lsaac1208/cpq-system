#!/bin/bash

# CPQ系统前端部署脚本
# 用途: 构建生产版本并部署到宝塔面板
# 作者: DevOps Team
# 创建时间: 2025-01-24
# 使用方法: ./deploy-frontend.sh [--build-only] [--upload-only] [--skip-backup]

set -e # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
PROJECT_NAME="CPQ-Frontend"
LOCAL_BUILD_DIR="./dist"
REMOTE_HOST=""  # 需要填入服务器IP
REMOTE_USER=""  # 需要填入SSH用户名
REMOTE_PATH="/www/wwwroot/cpq.d1bk.com"
BACKUP_DIR="/www/backup/cpq-frontend"
NGINX_CONFIG_PATH="/www/server/panel/vhost/nginx/cpq.d1bk.com.conf"
LOG_FILE="./deploy.log"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# 默认选项
BUILD_ONLY=false
UPLOAD_ONLY=false
SKIP_BACKUP=false

# 函数：打印彩色消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}[$(date '+%Y-%m-%d %H:%M:%S')] ${message}${NC}" | tee -a "$LOG_FILE"
}

# 函数：检查依赖
check_dependencies() {
    print_message "$BLUE" "检查构建依赖..."
    
    # 检查Node.js
    if ! command -v node &> /dev/null; then
        print_message "$RED" "错误: Node.js 未安装"
        exit 1
    fi
    
    # 检查npm
    if ! command -v npm &> /dev/null; then
        print_message "$RED" "错误: npm 未安装"
        exit 1
    fi
    
    # 检查项目依赖
    if [ ! -d "node_modules" ]; then
        print_message "$YELLOW" "安装项目依赖..."
        npm install
    fi
    
    print_message "$GREEN" "依赖检查完成"
}

# 函数：清理旧的构建文件
clean_build() {
    print_message "$BLUE" "清理旧的构建文件..."
    
    if [ -d "$LOCAL_BUILD_DIR" ]; then
        rm -rf "$LOCAL_BUILD_DIR"
        print_message "$GREEN" "已清理旧的构建文件"
    fi
}

# 函数：构建生产版本
build_production() {
    print_message "$BLUE" "开始构建生产版本..."
    
    # 检查环境变量文件
    if [ ! -f ".env.production" ]; then
        print_message "$RED" "错误: .env.production 文件不存在"
        exit 1
    fi
    
    # 执行构建
    NODE_ENV=production npm run build:prod-skip-check
    
    if [ $? -eq 0 ]; then
        print_message "$GREEN" "构建成功完成"
        
        # 显示构建统计
        if [ -d "$LOCAL_BUILD_DIR" ]; then
            local build_size=$(du -sh "$LOCAL_BUILD_DIR" | cut -f1)
            local file_count=$(find "$LOCAL_BUILD_DIR" -type f | wc -l | tr -d ' ')
            print_message "$GREEN" "构建统计: 大小=${build_size}, 文件数=${file_count}"
        fi
    else
        print_message "$RED" "构建失败"
        exit 1
    fi
}

# 函数：验证构建结果
validate_build() {
    print_message "$BLUE" "验证构建结果..."
    
    # 检查必要文件
    local required_files=("index.html" "assets" "js")
    
    for file in "${required_files[@]}"; do
        if [ ! -e "$LOCAL_BUILD_DIR/$file" ]; then
            print_message "$RED" "错误: 构建文件缺失 - $file"
            exit 1
        fi
    done
    
    # 检查index.html内容
    if ! grep -q "CPQ System" "$LOCAL_BUILD_DIR/index.html"; then
        print_message "$YELLOW" "警告: index.html 中未找到预期的标题"
    fi
    
    print_message "$GREEN" "构建结果验证通过"
}

# 函数：创建部署包
create_deployment_package() {
    print_message "$BLUE" "创建部署包..."
    
    local package_name="cpq-frontend-${TIMESTAMP}.tar.gz"
    
    cd "$LOCAL_BUILD_DIR"
    tar -czf "../$package_name" .
    cd ..
    
    if [ -f "$package_name" ]; then
        local package_size=$(du -sh "$package_name" | cut -f1)
        print_message "$GREEN" "部署包创建成功: $package_name (${package_size})"
        echo "$package_name" > .last_package
    else
        print_message "$RED" "部署包创建失败"
        exit 1
    fi
}

# 函数：上传到服务器
upload_to_server() {
    if [ -z "$REMOTE_HOST" ] || [ -z "$REMOTE_USER" ]; then
        print_message "$YELLOW" "跳过上传: 服务器配置未设置"
        print_message "$YELLOW" "请手动将 dist/ 目录内容上传到服务器"
        return
    fi
    
    print_message "$BLUE" "上传到服务器 $REMOTE_HOST..."
    
    local package_file=$(cat .last_package 2>/dev/null || echo "")
    
    if [ -z "$package_file" ] || [ ! -f "$package_file" ]; then
        print_message "$RED" "错误: 找不到部署包"
        exit 1
    fi
    
    # 上传部署包
    scp "$package_file" "$REMOTE_USER@$REMOTE_HOST:/tmp/" || {
        print_message "$RED" "上传失败"
        exit 1
    }
    
    # 在服务器上执行部署
    ssh "$REMOTE_USER@$REMOTE_HOST" << EOF
        set -e
        
        # 创建备份
        if [ -d "$REMOTE_PATH/dist" ] && [ "$SKIP_BACKUP" = false ]; then
            echo "创建备份..."
            mkdir -p "$BACKUP_DIR"
            cp -r "$REMOTE_PATH/dist" "$BACKUP_DIR/backup-$TIMESTAMP"
        fi
        
        # 创建目录
        mkdir -p "$REMOTE_PATH/dist"
        mkdir -p "$REMOTE_PATH/logs"
        
        # 解压新版本
        cd "$REMOTE_PATH/dist"
        rm -rf *
        tar -xzf "/tmp/$package_file"
        
        # 设置权限
        chown -R www:www "$REMOTE_PATH/dist"
        chmod -R 755 "$REMOTE_PATH/dist"
        
        # 清理临时文件
        rm -f "/tmp/$package_file"
        
        echo "部署完成"
EOF
    
    if [ $? -eq 0 ]; then
        print_message "$GREEN" "上传部署成功"
    else
        print_message "$RED" "远程部署失败"
        exit 1
    fi
}

# 函数：更新Nginx配置
update_nginx_config() {
    if [ -z "$REMOTE_HOST" ] || [ -z "$REMOTE_USER" ]; then
        print_message "$YELLOW" "跳过Nginx配置更新: 服务器配置未设置"
        return
    fi
    
    print_message "$BLUE" "更新Nginx配置..."
    
    # 上传Nginx配置
    if [ -f "./deploy/cpq-frontend.conf" ]; then
        scp "./deploy/cpq-frontend.conf" "$REMOTE_USER@$REMOTE_HOST:/tmp/" || {
            print_message "$YELLOW" "Nginx配置上传失败，请手动更新"
            return
        }
        
        # 在服务器上更新配置
        ssh "$REMOTE_USER@$REMOTE_HOST" << EOF
            # 备份现有配置
            if [ -f "$NGINX_CONFIG_PATH" ]; then
                cp "$NGINX_CONFIG_PATH" "$NGINX_CONFIG_PATH.backup-$TIMESTAMP"
            fi
            
            # 复制新配置
            cp "/tmp/cpq-frontend.conf" "$NGINX_CONFIG_PATH"
            
            # 测试Nginx配置
            nginx -t && systemctl reload nginx || {
                echo "Nginx配置测试失败，恢复备份"
                cp "$NGINX_CONFIG_PATH.backup-$TIMESTAMP" "$NGINX_CONFIG_PATH"
                exit 1
            }
            
            # 清理临时文件
            rm -f "/tmp/cpq-frontend.conf"
            
            echo "Nginx配置更新成功"
EOF
        
        if [ $? -eq 0 ]; then
            print_message "$GREEN" "Nginx配置更新成功"
        else
            print_message "$RED" "Nginx配置更新失败"
            exit 1
        fi
    else
        print_message "$YELLOW" "未找到Nginx配置文件"
    fi
}

# 函数：健康检查
health_check() {
    if [ -z "$REMOTE_HOST" ]; then
        print_message "$YELLOW" "跳过健康检查: 服务器配置未设置"
        return
    fi
    
    print_message "$BLUE" "执行健康检查..."
    
    local max_attempts=5
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        print_message "$BLUE" "健康检查尝试 $attempt/$max_attempts..."
        
        if curl -f -s -k "https://cpq.d1bk.com" > /dev/null; then
            print_message "$GREEN" "健康检查通过"
            return 0
        fi
        
        sleep 5
        ((attempt++))
    done
    
    print_message "$RED" "健康检查失败"
    exit 1
}

# 函数：清理临时文件
cleanup() {
    print_message "$BLUE" "清理临时文件..."
    
    # 清理部署包
    if [ -f ".last_package" ]; then
        local package_file=$(cat .last_package)
        if [ -f "$package_file" ]; then
            rm -f "$package_file"
        fi
        rm -f ".last_package"
    fi
    
    print_message "$GREEN" "清理完成"
}

# 函数：显示使用帮助
show_help() {
    echo "CPQ系统前端部署脚本"
    echo ""
    echo "使用方法:"
    echo "  $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --build-only      只执行构建，不上传"
    echo "  --upload-only     跳过构建，只上传现有dist目录"
    echo "  --skip-backup     跳过服务器备份"
    echo "  --help           显示此帮助信息"
    echo ""
    echo "配置："
    echo "  请在脚本中设置 REMOTE_HOST 和 REMOTE_USER 变量"
    echo ""
}

# 主函数
main() {
    print_message "$GREEN" "=== CPQ前端部署开始 ==="
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --build-only)
                BUILD_ONLY=true
                shift
                ;;
            --upload-only)
                UPLOAD_ONLY=true
                shift
                ;;
            --skip-backup)
                SKIP_BACKUP=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                print_message "$RED" "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 开始部署流程
    if [ "$UPLOAD_ONLY" = false ]; then
        check_dependencies
        clean_build
        build_production
        validate_build
        create_deployment_package
    fi
    
    if [ "$BUILD_ONLY" = false ]; then
        upload_to_server
        update_nginx_config
        health_check
    fi
    
    cleanup
    
    print_message "$GREEN" "=== CPQ前端部署完成 ==="
    print_message "$BLUE" "访问地址: https://cpq.d1bk.com"
    
    # 显示部署总结
    echo ""
    echo "部署总结:"
    echo "- 时间戳: $TIMESTAMP"
    echo "- 构建目录: $LOCAL_BUILD_DIR"
    if [ -d "$LOCAL_BUILD_DIR" ]; then
        echo "- 构建大小: $(du -sh $LOCAL_BUILD_DIR | cut -f1)"
    fi
    echo "- 日志文件: $LOG_FILE"
}

# 执行主函数
main "$@"