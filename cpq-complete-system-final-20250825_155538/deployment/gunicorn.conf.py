# Gunicorn配置文件
# 位置: /www/wwwroot/cpqh.d1bbk.com/gunicorn.conf.py

import multiprocessing
import os

# 基础配置
bind = "0.0.0.0:5000"
workers = multiprocessing.cpu_count() * 2 + 1  # CPU核数 * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 300  # 5分钟超时，支持AI长时间分析
keepalive = 2

# 性能优化
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# 日志配置
accesslog = "/www/wwwroot/cpqh.d1bbk.com/logs/gunicorn_access.log"
errorlog = "/www/wwwroot/cpqh.d1bbk.com/logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程管理
user = "www"
group = "www"
tmp_upload_dir = None

# 安全配置
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# SSL配置 (如果需要HTTPS)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# 开发模式配置 (生产环境设为False)
reload = False
reload_engine = "auto"

# 钩子函数
def on_starting(server):
    """服务器启动时执行"""
    server.log.info("CPQ API Server is starting...")

def on_reload(server):
    """重载时执行"""
    server.log.info("CPQ API Server is reloading...")

def when_ready(server):
    """服务器准备就绪时执行"""
    server.log.info("CPQ API Server is ready. Listening on: %s", server.address)

def on_exit(server):
    """服务器退出时执行"""
    server.log.info("CPQ API Server is shutting down...")

def worker_int(worker):
    """Worker收到SIGINT信号时执行"""
    worker.log.info("Worker received SIGINT signal")

def pre_fork(server, worker):
    """Fork worker进程前执行"""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    """Fork worker进程后执行"""
    server.log.info("Worker process is ready (pid: %s)", worker.pid)

def post_worker_init(worker):
    """Worker初始化完成后执行"""
    worker.log.info("Worker initialized (pid: %s)", worker.pid)

def worker_abort(worker):
    """Worker异常退出时执行"""
    worker.log.info("Worker aborted (pid: %s)", worker.pid)