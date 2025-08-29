# CPQ系统宝塔面板部署故障排除指南

## 🔍 常见部署问题

### 1. 前端部署问题

#### ❌ 问题：页面显示空白或404错误
**症状**：访问 cpq.d1bk.com 显示空白页面或Nginx 404错误

**排查步骤**：
```bash
# 1. 检查文件是否上传成功
ls -la /www/wwwroot/cpq.d1bk.com/
# 应该看到 index.html, css/, js/ 等文件

# 2. 检查文件权限
chown -R www:www /www/wwwroot/cpq.d1bk.com/
chmod -R 755 /www/wwwroot/cpq.d1bk.com/

# 3. 检查Nginx配置
nginx -t
# 检查配置文件语法是否正确

# 4. 查看错误日志
tail -f /www/wwwlogs/cpq.d1bk.com.error.log
```

**解决方案**：
- 确保构建文件正确上传到网站根目录
- 检查Nginx配置文件语法正确性
- 确保文件权限设置正确（755/644）

#### ❌ 问题：路由刷新后404
**症状**：直接访问 `/products` 等路由返回404

**解决方案**：
```nginx
# 在nginx配置中添加SPA路由支持
location / {
    try_files $uri $uri/ /index.html;
}
```

#### ❌ 问题：API请求失败
**症状**：前端无法连接到后端API，CORS错误

**排查步骤**：
```bash
# 1. 检查后端服务是否启动
ps aux | grep gunicorn
systemctl status cpq-api

# 2. 检查端口监听
netstat -tlnp | grep 5000

# 3. 测试API连接
curl http://localhost:5000/health
```

**解决方案**：
- 检查CORS配置是否正确
- 确保后端服务正常运行
- 验证Nginx代理配置正确

### 2. 后端部署问题

#### ❌ 问题：Python项目启动失败
**症状**：宝塔面板显示Python项目状态为"停止"

**排查步骤**：
```bash
# 1. 检查Python环境
cd /www/wwwroot/cpqh.d1bbk.com
source venv/bin/activate
python --version

# 2. 检查依赖安装
pip list | grep -i flask

# 3. 手动启动测试
python app.py
```

**解决方案**：
```bash
# 重新安装依赖
pip install -r requirements.txt

# 检查环境变量
cat .env

# 检查数据库连接
python -c "from app import create_app; app=create_app(); print('App created successfully')"
```

#### ❌ 问题：数据库连接失败
**症状**：应用启动时报数据库连接错误

**排查步骤**：
```bash
# 1. 检查MySQL服务状态
systemctl status mysql

# 2. 测试数据库连接
mysql -u cpq_user -p -h localhost cpq_production

# 3. 检查数据库配置
grep DATABASE_URL /www/wwwroot/cpqh.d1bbk.com/.env
```

**解决方案**：
- 确保MySQL服务正常运行
- 验证数据库用户名密码正确
- 检查数据库是否存在
- 运行数据库迁移：`flask db upgrade`

#### ❌ 问题：文件上传失败
**症状**：图片上传功能无法工作

**排查步骤**：
```bash
# 1. 检查上传目录权限
ls -la /www/wwwroot/cpqh.d1bbk.com/instance/uploads/
chmod -R 755 /www/wwwroot/cpqh.d1bbk.com/instance/uploads/
chown -R www:www /www/wwwroot/cpqh.d1bbk.com/instance/uploads/

# 2. 检查磁盘空间
df -h

# 3. 检查Nginx文件大小限制
grep client_max_body_size /www/server/panel/vhost/nginx/cpqh.d1bbk.com.conf
```

### 3. 性能优化问题

#### ❌ 问题：响应速度慢
**症状**：页面加载时间超过5秒

**优化方案**：
```bash
# 1. 启用Gzip压缩
# 在nginx配置中已包含gzip配置

# 2. 优化数据库查询
# 检查数据库慢查询日志
mysql -e "SHOW VARIABLES LIKE 'slow_query_log';"

# 3. 增加Gunicorn worker数量
# 在gunicorn.conf.py中调整workers数量

# 4. 启用静态文件缓存
# nginx配置中已包含缓存设置
```

#### ❌ 问题：内存使用过高
**症状**：服务器内存占用超过80%

**解决方案**：
```bash
# 1. 监控内存使用
free -h
ps aux --sort=-%mem | head -10

# 2. 调整Gunicorn配置
# 减少worker数量
# 设置max_requests重启worker

# 3. 优化数据库连接池
# 在config.py中调整SQLALCHEMY_ENGINE_OPTIONS
```

### 4. 安全问题

#### ❌ 问题：SSL证书配置
**症状**：需要HTTPS访问

**解决方案**：
```bash
# 1. 申请SSL证书（宝塔面板）
# 网站设置 → SSL → Let's Encrypt

# 2. 强制HTTPS重定向
server {
    listen 80;
    server_name cpq.d1bk.com;
    return 301 https://$server_name$request_uri;
}
```

#### ❌ 问题：安全防护配置
**建议配置**：
```nginx
# 隐藏Nginx版本
server_tokens off;

# 防止XSS攻击
add_header X-XSS-Protection "1; mode=block";
add_header X-Content-Type-Options "nosniff";
add_header X-Frame-Options "SAMEORIGIN";

# 限制请求频率
limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;
location /api/auth/login {
    limit_req zone=login burst=3 nodelay;
}
```

## 🛠️ 监控和维护

### 系统监控脚本
```bash
#!/bin/bash
# 系统健康检查脚本
# 位置: /www/wwwroot/scripts/health_check.sh

echo "=== CPQ System Health Check ==="
echo "Time: $(date)"
echo

# 检查服务状态
echo "1. Service Status:"
systemctl is-active cpq-api && echo "✅ CPQ API: Running" || echo "❌ CPQ API: Stopped"
systemctl is-active nginx && echo "✅ Nginx: Running" || echo "❌ Nginx: Stopped"
systemctl is-active mysql && echo "✅ MySQL: Running" || echo "❌ MySQL: Stopped"
echo

# 检查端口监听
echo "2. Port Status:"
netstat -tlnp | grep :80 > /dev/null && echo "✅ Port 80: Listening" || echo "❌ Port 80: Not listening"
netstat -tlnp | grep :5000 > /dev/null && echo "✅ Port 5000: Listening" || echo "❌ Port 5000: Not listening"
echo

# 检查磁盘空间
echo "3. Disk Usage:"
df -h | grep -E "(/$|/www)" | while read filesystem size used avail percent mount; do
    usage=$(echo $percent | sed 's/%//')
    if [ $usage -gt 80 ]; then
        echo "⚠️  $mount: $percent used"
    else
        echo "✅ $mount: $percent used"
    fi
done
echo

# 检查内存使用
echo "4. Memory Usage:"
total_mem=$(free -m | awk 'NR==2{printf "%.0f", $3*100/$2}')
if [ $total_mem -gt 80 ]; then
    echo "⚠️  Memory: ${total_mem}% used"
else
    echo "✅ Memory: ${total_mem}% used"
fi
echo

# 检查API健康状态
echo "5. API Health:"
curl -s http://localhost:5000/health > /dev/null && echo "✅ API Health: OK" || echo "❌ API Health: Failed"
echo

echo "=== Health Check Complete ==="
```

### 日志轮转配置
```bash
# /etc/logrotate.d/cpq-system
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

/www/wwwroot/cpqh.d1bbk.com/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
}
```

## 🔧 快速修复命令

### 重启所有服务
```bash
#!/bin/bash
# 快速重启脚本
systemctl restart nginx
systemctl restart cpq-api
systemctl restart mysql
echo "All services restarted"
```

### 清理缓存和日志
```bash
#!/bin/bash
# 系统清理脚本
# 清理Nginx缓存
rm -rf /tmp/nginx_cache/*

# 清理应用日志（保留最近7天）
find /www/wwwlogs/ -name "*.log" -mtime +7 -delete
find /www/wwwroot/cpqh.d1bbk.com/logs/ -name "*.log" -mtime +7 -delete

# 清理临时文件
rm -rf /tmp/cpq_*

echo "Cache and logs cleaned"
```

### 数据库备份脚本
```bash
#!/bin/bash
# 数据库备份脚本
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/www/backup/mysql"
DB_NAME="cpq_production"

mkdir -p $BACKUP_DIR
mysqldump -u root -p $DB_NAME > $BACKUP_DIR/cpq_backup_$DATE.sql
gzip $BACKUP_DIR/cpq_backup_$DATE.sql

# 删除7天前的备份
find $BACKUP_DIR -name "cpq_backup_*.sql.gz" -mtime +7 -delete

echo "Database backup completed: cpq_backup_$DATE.sql.gz"
```

## 📞 紧急联系和支持

### 故障处理优先级
1. **P0 - 紧急**: 系统完全不可访问
2. **P1 - 高优先级**: 核心功能异常
3. **P2 - 中优先级**: 部分功能异常
4. **P3 - 低优先级**: 性能问题或小功能异常

### 日志文件位置
- **前端访问日志**: `/www/wwwlogs/cpq.d1bk.com.log`
- **前端错误日志**: `/www/wwwlogs/cpq.d1bk.com.error.log`
- **后端访问日志**: `/www/wwwlogs/cpqh.d1bbk.com.log`
- **后端错误日志**: `/www/wwwlogs/cpqh.d1bbk.com.error.log`
- **应用程序日志**: `/www/wwwroot/cpqh.d1bbk.com/logs/`
- **系统日志**: `journalctl -u cpq-api`