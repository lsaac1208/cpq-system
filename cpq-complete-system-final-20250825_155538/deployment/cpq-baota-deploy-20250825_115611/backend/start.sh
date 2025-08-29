#!/bin/bash
# CPQ系统生产环境启动脚本
# 适配宝塔面板和systemd服务管理
# 更新时间: 2024-08-24

set -e  # 遇到错误立即退出

# ==============================================
# 配置变量
# ==============================================
APP_NAME="CPQ-API"
APP_DIR="/www/wwwroot/cpqh.d1bbk.com"
VENV_PATH="$APP_DIR/venv"
PID_FILE="$APP_DIR/tmp/gunicorn.pid"
LOG_DIR="$APP_DIR/logs"
ENV_FILE="$APP_DIR/.env.production"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==============================================
# 日志函数
# ==============================================
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# ==============================================
# 环境检查函数
# ==============================================
check_environment() {
    log_step "检查运行环境..."
    
    # 检查是否在项目目录
    if [ ! -f "app.py" ]; then
        log_error "未找到app.py，请确保在正确的项目目录中运行"
        exit 1
    fi
    
    # 检查环境配置文件
    if [ ! -f "$ENV_FILE" ]; then
        log_warn "未找到生产环境配置文件: $ENV_FILE"
        log_info "使用默认配置文件..."
        ENV_FILE=".env"
    fi
    
    # 检查虚拟环境
    if [ ! -d "$VENV_PATH" ]; then
        log_warn "虚拟环境不存在，尝试查找系统Python环境"
        VENV_PATH=""
    fi
    
    # 创建必要目录
    mkdir -p "$LOG_DIR"
    mkdir -p "$(dirname $PID_FILE)"
    
    log_info "环境检查完成"
}

# ==============================================
# 虚拟环境激活
# ==============================================
activate_venv() {
    if [ -n "$VENV_PATH" ] && [ -d "$VENV_PATH" ]; then
        log_step "激活虚拟环境: $VENV_PATH"
        source "$VENV_PATH/bin/activate"
        log_info "虚拟环境已激活"
    else
        log_warn "使用系统Python环境"
    fi
}

# ==============================================
# 依赖检查
# ==============================================
check_dependencies() {
    log_step "检查Python依赖..."
    
    # 检查关键依赖
    python -c "import flask, gunicorn" 2>/dev/null || {
        log_error "缺少关键依赖包，请运行: pip install -r requirements.txt"
        exit 1
    }
    
    log_info "依赖检查完成"
}

# ==============================================
# 数据库迁移
# ==============================================
migrate_database() {
    log_step "执行数据库迁移..."
    
    export FLASK_APP=app.py
    export FLASK_ENV=production
    
    # 检查是否需要初始化数据库
    python -c "
from app import create_app
from src.models import db
app = create_app('production')
with app.app_context():
    try:
        db.create_all()
        print('数据库表创建成功')
    except Exception as e:
        print(f'数据库操作失败: {e}')
        exit(1)
" || {
        log_error "数据库迁移失败"
        exit 1
    }
    
    log_info "数据库迁移完成"
}

# ==============================================
# 进程管理函数
# ==============================================
get_pid() {
    if [ -f "$PID_FILE" ]; then
        cat "$PID_FILE"
    fi
}

is_running() {
    local pid=$(get_pid)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

start_app() {
    log_step "启动 $APP_NAME 服务..."
    
    if is_running; then
        log_warn "$APP_NAME 已在运行中 (PID: $(get_pid))"
        return 0
    fi
    
    # 检查环境
    check_environment
    activate_venv
    check_dependencies
    migrate_database
    
    # 启动Gunicorn
    log_info "使用Gunicorn启动应用..."
    
    # 环境变量设置
    export FLASK_ENV=production
    export PYTHONPATH="$(pwd):$PYTHONPATH"
    
    # 启动命令
    nohup gunicorn \
        --config gunicorn.conf.py \
        --env FLASK_ENV=production \
        app:app \
        > "$LOG_DIR/startup.log" 2>&1 &
    
    # 等待启动
    sleep 3
    
    if is_running; then
        log_info "$APP_NAME 启动成功 (PID: $(get_pid))"
        log_info "访问地址: http://cpqh.d1bbk.com:5000"
        log_info "API文档: http://cpqh.d1bbk.com:5000/api/v1/health"
    else
        log_error "$APP_NAME 启动失败"
        log_error "检查启动日志: $LOG_DIR/startup.log"
        exit 1
    fi
}

stop_app() {
    log_step "停止 $APP_NAME 服务..."
    
    if ! is_running; then
        log_warn "$APP_NAME 没有运行"
        return 0
    fi
    
    local pid=$(get_pid)
    log_info "终止进程 (PID: $pid)..."
    
    # 优雅关闭
    kill -TERM "$pid" 2>/dev/null || true
    
    # 等待进程结束
    local count=0
    while is_running && [ $count -lt 30 ]; do
        sleep 1
        count=$((count + 1))
    done
    
    if is_running; then
        log_warn "优雅关闭超时，强制终止..."
        kill -KILL "$pid" 2>/dev/null || true
        sleep 2
    fi
    
    # 清理PID文件
    rm -f "$PID_FILE"
    
    if is_running; then
        log_error "$APP_NAME 停止失败"
        exit 1
    else
        log_info "$APP_NAME 已停止"
    fi
}

restart_app() {
    log_step "重启 $APP_NAME 服务..."
    stop_app
    sleep 2
    start_app
}

status_app() {
    if is_running; then
        local pid=$(get_pid)
        log_info "$APP_NAME 正在运行 (PID: $pid)"
        
        # 显示进程信息
        ps aux | grep -E "(gunicorn|$pid)" | grep -v grep || true
        
        # 显示端口信息
        netstat -tlnp 2>/dev/null | grep :5000 || true
        
        return 0
    else
        log_warn "$APP_NAME 没有运行"
        return 1
    fi
}

logs_app() {
    log_step "显示应用日志..."
    
    if [ -f "$LOG_DIR/error.log" ]; then
        echo -e "\n${BLUE}=== 错误日志 ===${NC}"
        tail -n 50 "$LOG_DIR/error.log"
    fi
    
    if [ -f "$LOG_DIR/access.log" ]; then
        echo -e "\n${BLUE}=== 访问日志 ===${NC}"
        tail -n 20 "$LOG_DIR/access.log"
    fi
    
    if [ -f "$LOG_DIR/app.log" ]; then
        echo -e "\n${BLUE}=== 应用日志 ===${NC}"
        tail -n 30 "$LOG_DIR/app.log"
    fi
}

# ==============================================
# 健康检查
# ==============================================
health_check() {
    log_step "执行健康检查..."
    
    if ! is_running; then
        log_error "服务未运行"
        return 1
    fi
    
    # HTTP健康检查
    local health_url="http://127.0.0.1:5000/health"
    
    if command -v curl >/dev/null 2>&1; then
        if curl -f -s "$health_url" >/dev/null; then
            log_info "健康检查通过"
            return 0
        else
            log_error "健康检查失败 - HTTP请求失败"
            return 1
        fi
    else
        log_warn "curl未安装，跳过HTTP健康检查"
        log_info "进程检查通过"
        return 0
    fi
}

# ==============================================
# 主程序
# ==============================================
case "$1" in
    start)
        start_app
        ;;
    stop)
        stop_app
        ;;
    restart|reload)
        restart_app
        ;;
    status)
        status_app
        ;;
    logs)
        logs_app
        ;;
    health)
        health_check
        ;;
    *)
        echo "使用方法: $0 {start|stop|restart|status|logs|health}"
        echo ""
        echo "命令说明:"
        echo "  start   - 启动服务"
        echo "  stop    - 停止服务"
        echo "  restart - 重启服务"
        echo "  status  - 查看状态"
        echo "  logs    - 查看日志"
        echo "  health  - 健康检查"
        echo ""
        exit 1
        ;;
esac

exit 0