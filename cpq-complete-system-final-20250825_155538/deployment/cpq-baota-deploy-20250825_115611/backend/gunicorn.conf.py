#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPQ系统 Gunicorn 生产环境配置
适配宝塔面板Python项目管理器
更新时间: 2024-08-24
"""

import os
import multiprocessing
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('.env.production')

# ==============================================
# 服务器套接字配置
# ==============================================
# 绑定地址和端口
bind = f"{os.getenv('HOST', '127.0.0.1')}:{os.getenv('PORT', '5000')}"

# 待处理连接的最大数量
backlog = 2048

# ==============================================
# 工作进程配置
# ==============================================
# 工作进程数量 (建议: CPU核心数 * 2 + 1)
workers = int(os.getenv('WORKERS', multiprocessing.cpu_count() * 2 + 1))

# 工作进程类型
worker_class = os.getenv('WORKER_CLASS', 'sync')

# 每个工作进程的线程数 (仅对 gthread 工作类型有效)
threads = 2

# 工作进程连接数
worker_connections = int(os.getenv('WORKER_CONNECTIONS', 1000))

# 工作进程重启前处理的最大请求数
max_requests = int(os.getenv('MAX_REQUESTS', 1000))

# 工作进程重启前处理请求数的随机抖动值
max_requests_jitter = int(os.getenv('MAX_REQUESTS_JITTER', 100))

# 工作进程超时时间 (秒)
timeout = int(os.getenv('TIMEOUT', 120))

# 保持连接活跃时间 (秒)
keepalive = int(os.getenv('KEEPALIVE', 2))

# ==============================================
# 应用配置
# ==============================================
# WSGI 模块和应用
wsgi_module = "app:app"

# ==============================================
# 日志配置
# ==============================================
# 访问日志文件路径
accesslog = os.getenv('ACCESS_LOG_FILE', '/www/wwwroot/cpqh.d1bbk.com/logs/access.log')

# 错误日志文件路径
errorlog = os.getenv('ERROR_LOG_FILE', '/www/wwwroot/cpqh.d1bbk.com/logs/error.log')

# 日志级别
loglevel = os.getenv('LOG_LEVEL', 'info').lower()

# 访问日志格式
access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s '
    '"%(f)s" "%(a)s" %(D)s %(p)s'
)

# 捕获输出到错误日志
capture_output = True

# ==============================================
# 进程命名
# ==============================================
# 进程名前缀
proc_name = 'cpq-api'

# ==============================================
# 服务器机制
# ==============================================
# 守护进程模式
daemon = False

# PID文件路径
pidfile = '/www/wwwroot/cpqh.d1bbk.com/tmp/gunicorn.pid'

# 用户和组 (宝塔面板推荐使用www)
user = 'www'
group = 'www'

# ==============================================
# SSL配置 (如果需要HTTPS)
# ==============================================
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'

# ==============================================
# 性能调优
# ==============================================
# 预加载应用
preload_app = True

# 最大客户端连接数
max_requests_jitter = 50

# 工作进程内存限制 (字节)
# worker_tmp_dir = '/dev/shm'

# ==============================================
# 钩子函数
# ==============================================
def when_ready(server):
    """服务器准备就绪时调用"""
    print(f"🚀 CPQ API Server ready. PID: {os.getpid()}")
    print(f"📍 Listening on: {bind}")
    print(f"👷 Workers: {workers}")
    
def worker_int(worker):
    """工作进程接收到 SIGINT 信号时调用"""
    print(f"🔄 Worker {worker.pid} received SIGINT")

def pre_fork(server, worker):
    """工作进程 fork 前调用"""
    print(f"🔧 Worker {worker.pid} about to fork")

def post_fork(server, worker):
    """工作进程 fork 后调用"""
    print(f"✅ Worker {worker.pid} forked")
    
def worker_abort(worker):
    """工作进程异常退出时调用"""
    print(f"💥 Worker {worker.pid} aborted")

def pre_exec(server):
    """执行前调用"""
    print("🏁 Pre-exec hook called")

def on_starting(server):
    """服务器启动时调用"""
    print("🎬 CPQ API Server starting...")
    # 确保日志目录存在
    log_dir = os.path.dirname(accesslog)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

def on_reload(server):
    """服务器重载时调用"""
    print("🔄 CPQ API Server reloading...")

def on_exit(server):
    """服务器退出时调用"""
    print("👋 CPQ API Server shutting down...")

# ==============================================
# 环境变量设置
# ==============================================
raw_env = [
    f'FLASK_ENV=production',
    f'PYTHONPATH={os.getcwd()}',
]

# ==============================================
# 宝塔面板兼容性配置
# ==============================================
# 确保与宝塔面板Python项目管理器兼容
if 'BT_PANEL' in os.environ:
    # 宝塔面板环境下的特殊配置
    daemon = False  # 宝塔面板管理进程，不需要守护进程模式
    capture_output = True  # 捕获输出以便宝塔面板显示日志
    
    # 调整进程数量以适应宝塔面板资源限制
    if workers > 4:
        workers = 4
        
    print("🔧 Running in BaoTa Panel mode")

# ==============================================
# 开发调试配置
# ==============================================
if os.getenv('FLASK_ENV') == 'development':
    workers = 1
    reload = True
    loglevel = 'debug'
    print("⚠️  Running in development mode")