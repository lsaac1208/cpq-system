# CPQ系统宝塔部署命令速查表

## 🚀 快速部署命令

### 在本地准备部署包
```bash
cd deployment/
chmod +x package-preparation.sh
./package-preparation.sh
```

### 在服务器端一键部署
```bash
# 1. 上传并解压部署包
tar -xzf cpq-baota-deploy-*.tar.gz
cd cpq-baota-deploy-*/scripts/

# 2. 运行一键安装
chmod +x quick-install.sh
./quick-install.sh
```

### 验证部署
```bash
python3 cpq-deployment-validator.py
```

---

## 🔧 服务管理命令

```bash
cd /www/wwwroot/cpqh.d1bbk.com/

# 启动服务
./start.sh start

# 停止服务
./start.sh stop

# 重启服务
./start.sh restart

# 查看状态
./start.sh status

# 查看日志
./start.sh logs

# 健康检查
./start.sh health
```

---

## 🔍 故障排查命令

### 检查服务状态
```bash
# 系统服务状态
systemctl status cpq-api
systemctl status nginx
systemctl status mysql

# 端口监听状态
netstat -tlnp | grep :5000
netstat -tlnp | grep :80

# 进程状态
ps aux | grep gunicorn
ps aux | grep nginx
```

### 查看日志
```bash
# 应用日志
tail -f /www/wwwroot/cpqh.d1bbk.com/logs/app.log

# Gunicorn日志
tail -f /www/wwwroot/cpqh.d1bbk.com/logs/gunicorn_error.log

# 系统日志
journalctl -u cpq-api -f

# Nginx日志
tail -f /www/server/nginx/logs/error.log
tail -f /www/wwwroot/cpq.d1bk.com/logs/error.log
```

### API测试
```bash
# 健康检查
curl -I http://127.0.0.1:5000/health
curl -I http://cpqh.d1bbk.com/health

# API端点测试
curl -s http://127.0.0.1:5000/api/v1/products
curl -s http://cpq.d1bk.com/api/v1/products
```

---

## 🗄️ 数据库命令

```bash
# 连接数据库
mysql -u cpq_user -p cpq_system

# 查看表结构
mysql -u cpq_user -p cpq_system -e "SHOW TABLES;"

# 查看用户数量
mysql -u cpq_user -p cpq_system -e "SELECT COUNT(*) FROM users;"

# 重置管理员密码 (在Python中执行)
cd /www/wwwroot/cpqh.d1bbk.com/
python3 -c "
from app import app
from src.models import db
from src.models.user import User
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    admin.set_password('new_password')
    db.session.commit()
    print('密码重置成功')
"
```

---

## 📊 系统监控命令

```bash
# 系统资源
htop
df -h
free -h
iostat -x 1

# 网络连接
ss -tlnp | grep :5000
netstat -an | grep :80

# 磁盘使用
du -sh /www/wwwroot/cpqh.d1bbk.com/
du -sh /www/wwwroot/cpq.d1bk.com/
```

---

## 🔐 安全维护命令

### 更新系统
```bash
# CentOS/RHEL
yum update -y

# Ubuntu/Debian  
apt update && apt upgrade -y
```

### 备份数据
```bash
# 备份数据库
mysqldump -u cpq_user -p cpq_system > cpq_backup_$(date +%Y%m%d).sql

# 备份上传文件
tar -czf cpq_uploads_$(date +%Y%m%d).tar.gz /www/wwwroot/cpqh.d1bbk.com/instance/uploads/

# 备份配置文件
cp /www/wwwroot/cpqh.d1bbk.com/.env /root/cpq_env_backup_$(date +%Y%m%d)
```

### 清理日志
```bash
# 清理应用日志 (保留最近7天)
find /www/wwwroot/cpqh.d1bbk.com/logs/ -name "*.log" -mtime +7 -delete

# 清理Nginx日志
find /www/server/nginx/logs/ -name "*.log" -mtime +7 -delete
```

---

## 🔄 更新部署命令

```bash
# 停止服务
cd /www/wwwroot/cpqh.d1bbk.com/
./start.sh stop

# 备份当前版本
cp -r /www/wwwroot/cpqh.d1bbk.com /www/backup/cpqh_$(date +%Y%m%d_%H%M%S)

# 更新代码 (假设有新版本)
# ... 更新步骤 ...

# 重新安装依赖
pip3 install -r requirements-production.txt

# 数据库迁移 (如需要)
python3 migrate.py

# 重启服务
./start.sh restart

# 验证更新
python3 /root/cpq-deployment-scripts/cpq-deployment-validator.py
```

---

## 🚨 紧急处理命令

### 服务无响应
```bash
# 强制重启服务
systemctl stop cpq-api
pkill -f gunicorn
systemctl start cpq-api

# 重启Nginx
systemctl restart nginx
```

### 数据库连接失败
```bash
# 重启MySQL
systemctl restart mysql

# 检查MySQL状态
systemctl status mysql
mysql -uroot -p -e "SHOW PROCESSLIST;"
```

### 磁盘空间不足
```bash
# 清理临时文件
rm -rf /tmp/*
rm -rf /www/wwwroot/cpqh.d1bbk.com/tmp/*

# 清理旧日志
find /www/wwwroot/cpqh.d1bbk.com/logs/ -name "*.log" -mtime +3 -delete

# 清理Python缓存
find /www/wwwroot/cpqh.d1bbk.com/ -name "__pycache__" -exec rm -rf {} +
```

---

## 📞 技术支持信息收集

当需要技术支持时，请收集以下信息：

```bash
# 系统信息
uname -a
cat /etc/os-release
python3 --version
mysql --version
nginx -v

# 服务状态
systemctl status cpq-api --no-pager
systemctl status nginx --no-pager  
systemctl status mysql --no-pager

# 错误日志
tail -100 /www/wwwroot/cpqh.d1bbk.com/logs/app.log
tail -100 /www/server/nginx/logs/error.log
journalctl -u cpq-api --no-pager -l | tail -100

# 配置文件检查
nginx -t
cat /www/wwwroot/cpqh.d1bbk.com/.env | grep -v PASSWORD | grep -v SECRET

# 运行验证
python3 /root/cpq-deployment-scripts/cpq-deployment-validator.py
```