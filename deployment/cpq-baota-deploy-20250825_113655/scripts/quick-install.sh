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
