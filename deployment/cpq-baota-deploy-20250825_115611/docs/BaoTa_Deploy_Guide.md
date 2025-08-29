# CPQ系统宝塔面板部署指南

## 📋 系统环境要求

### 服务器配置
- **操作系统**: CentOS 7+ / Ubuntu 18+ / Debian 9+
- **内存**: 2GB+ 推荐
- **硬盘**: 20GB+ 可用空间
- **CPU**: 2核+ 推荐

### 软件版本
- **宝塔面板**: 7.7.0+
- **Python**: 3.8+
- **MySQL**: 5.7+ / 8.0+
- **Nginx**: 1.20+ (可选)

## 🚀 部署步骤

### 1. 宝塔面板基础配置

#### 1.1 安装Python版本管理器
```bash
# 在宝塔面板终端执行
cd /www/server/panel && python tools.py install
```

#### 1.2 安装Python 3.8+
- 进入宝塔面板 → 软件商店 → Python版本管理器
- 安装Python 3.8或更高版本

#### 1.3 安装MySQL
- 进入宝塔面板 → 软件商店 → MySQL
- 安装MySQL 5.7或8.0版本

### 2. 项目部署配置

#### 2.1 创建网站
1. 进入宝塔面板 → 网站 → 添加站点
2. 填写配置:
   - **域名**: `cpqh.d1bbk.com`
   - **根目录**: `/www/wwwroot/cpqh.d1bbk.com`
   - **PHP版本**: 纯静态 (不选PHP)

#### 2.2 上传项目文件
```bash
# 方法1: 通过宝塔文件管理器上传压缩包并解压

# 方法2: 通过Git拉取 (推荐)
cd /www/wwwroot/cpqh.d1bbk.com
git clone <your-repository-url> .

# 设置文件权限
chown -R www:www /www/wwwroot/cpqh.d1bbk.com
chmod -R 755 /www/wwwroot/cpqh.d1bbk.com
```

#### 2.3 创建数据库
1. 进入宝塔面板 → 数据库 → 添加数据库
2. 填写配置:
   - **数据库名**: `cpq_database`
   - **用户名**: `cpq_user`
   - **密码**: `your_secure_password`
   - **访问权限**: 本地服务器

### 3. Python环境配置

#### 3.1 创建Python项目
1. 进入宝塔面板 → Python项目管理器 → 添加项目
2. 填写配置:
   - **项目名称**: `CPQ-API`
   - **Python版本**: 选择已安装的3.8+版本
   - **项目路径**: `/www/wwwroot/cpqh.d1bbk.com`
   - **启动文件**: `app.py`
   - **端口**: `5000`

#### 3.2 安装项目依赖
```bash
# 进入项目目录
cd /www/wwwroot/cpqh.d1bbk.com

# 激活虚拟环境 (宝塔会自动创建)
source /www/server/python_manager/venv/cpq-api/bin/activate

# 安装生产环境依赖
pip install -r requirements-production.txt
```

### 4. 环境配置

#### 4.1 配置环境变量文件
```bash
# 复制并编辑生产环境配置
cp .env.production .env

# 编辑环境变量 (使用宝塔文件管理器或vim)
vi .env
```

关键配置项:
```bash
# 数据库连接 - 修改为实际配置
DATABASE_URL=mysql+pymysql://cpq_user:your_secure_password@localhost:3306/cpq_database?charset=utf8mb4
MYSQL_HOST=localhost
MYSQL_USER=cpq_user
MYSQL_PASSWORD=your_secure_password
MYSQL_DATABASE=cpq_database

# 安全密钥 - 必须修改为随机字符串
SECRET_KEY=your-production-secret-key-change-this
JWT_SECRET_KEY=your-jwt-production-secret-key-change-this

# CORS域名 - 修改为实际前端域名
CORS_ORIGINS=https://cpq.d1bbk.com,https://cpqh.d1bbk.com
```

#### 4.2 创建必要目录
```bash
# 创建日志目录
mkdir -p /www/wwwroot/cpqh.d1bbk.com/logs
mkdir -p /www/wwwroot/cpqh.d1bbk.com/tmp

# 设置权限
chown -R www:www /www/wwwroot/cpqh.d1bbk.com/logs
chown -R www:www /www/wwwroot/cpqh.d1bbk.com/tmp
chmod -R 755 /www/wwwroot/cpqh.d1bbk.com/logs
chmod -R 755 /www/wwwroot/cpqh.d1bbk.com/tmp
```

### 5. 数据库迁移

#### 5.1 执行数据库迁移 (如果从SQLite迁移)
```bash
cd /www/wwwroot/cpqh.d1bbk.com
python migrate.py
```

#### 5.2 初始化数据库 (新安装)
```bash
cd /www/wwwroot/cpqh.d1bbk.com
python scripts/init_db.py
```

### 6. 宝塔Python项目管理器配置

#### 6.1 配置项目启动参数
在宝塔面板 → Python项目管理器 → 项目设置中配置:

**基本设置**:
- **项目名称**: CPQ-API
- **运行目录**: `/www/wwwroot/cpqh.d1bbk.com`
- **启动文件名**: `app.py`
- **端口**: `5000`

**高级设置**:
- **启动方式**: `Gunicorn`
- **进程数**: `4` (根据CPU核心数调整)
- **线程数**: `2`
- **最大请求数**: `1000`

#### 6.2 自定义启动脚本 (可选)
如果需要使用自定义启动脚本:
- **启动文件名**: `start.sh`
- **启动方式**: `Shell脚本`

### 7. Nginx反向代理配置 (可选)

#### 7.1 配置反向代理
在宝塔面板 → 网站 → cpqh.d1bbk.com → 配置文件中添加:

```nginx
location /api {
    proxy_pass http://127.0.0.1:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # 处理跨域
    add_header Access-Control-Allow-Origin * always;
    add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
    add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
    
    # 预检请求
    if ($request_method = 'OPTIONS') {
        return 204;
    }
}

# 静态文件处理
location /uploads {
    alias /www/wwwroot/cpqh.d1bbk.com/instance/uploads;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

#### 7.2 SSL证书配置
1. 进入宝塔面板 → 网站 → cpqh.d1bbk.com → SSL
2. 申请Let's Encrypt免费证书或上传自有证书
3. 开启强制HTTPS

### 8. 防火墙和安全配置

#### 8.1 配置防火墙
```bash
# 开放必要端口
firewall-cmd --permanent --add-port=5000/tcp
firewall-cmd --permanent --add-port=80/tcp
firewall-cmd --permanent --add-port=443/tcp
firewall-cmd --reload
```

#### 8.2 宝塔面板安全设置
1. 进入宝塔面板 → 安全 → 系统防火墙
2. 添加规则:
   - **端口**: `5000`
   - **协议**: `TCP`
   - **策略**: `放行`
   - **备注**: `CPQ API服务`

### 9. 启动和测试

#### 9.1 启动项目
1. 进入宝塔面板 → Python项目管理器
2. 找到CPQ-API项目
3. 点击"启动"按钮

#### 9.2 检查服务状态
```bash
# 检查进程
ps aux | grep gunicorn

# 检查端口
netstat -tlnp | grep :5000

# 查看日志
tail -f /www/wwwroot/cpqh.d1bbk.com/logs/error.log
```

#### 9.3 API测试
```bash
# 健康检查
curl http://127.0.0.1:5000/health

# API测试
curl http://127.0.0.1:5000/api/v1/products
```

### 10. 监控和维护

#### 10.1 日志监控
定期检查以下日志文件:
- `/www/wwwroot/cpqh.d1bbk.com/logs/error.log` - 错误日志
- `/www/wwwroot/cpqh.d1bbk.com/logs/access.log` - 访问日志
- `/www/wwwroot/cpqh.d1bbk.com/logs/app.log` - 应用日志

#### 10.2 性能监控
使用宝塔面板监控功能:
1. 进入宝塔面板 → 监控
2. 查看CPU、内存、硬盘使用情况
3. 监控Python进程资源占用

#### 10.3 自动备份
1. 进入宝塔面板 → 计划任务
2. 添加数据库备份任务:
   - **任务类型**: 备份数据库
   - **执行周期**: 每天
   - **备份保留**: 7天

## 🔧 故障排除

### 常见问题及解决方案

#### 问题1: 项目启动失败
**解决方案**:
```bash
# 检查Python环境
which python
python --version

# 检查依赖安装
pip list | grep Flask

# 查看错误日志
tail -100 /www/wwwroot/cpqh.d1bbk.com/logs/error.log
```

#### 问题2: 数据库连接失败
**解决方案**:
```bash
# 检查MySQL服务
systemctl status mysqld

# 测试数据库连接
mysql -u cpq_user -p -h localhost cpq_database

# 检查防火墙
firewall-cmd --list-all
```

#### 问题3: 端口占用
**解决方案**:
```bash
# 查看端口占用
netstat -tlnp | grep :5000

# 杀死占用进程
kill -9 <PID>

# 重启项目
```

#### 问题4: 权限问题
**解决方案**:
```bash
# 设置正确权限
chown -R www:www /www/wwwroot/cpqh.d1bbk.com
chmod -R 755 /www/wwwroot/cpqh.d1bbk.com

# 特殊目录权限
chmod -R 777 /www/wwwroot/cpqh.d1bbk.com/instance/uploads
chmod -R 755 /www/wwwroot/cpqh.d1bbk.com/logs
```

## 📞 技术支持

### 联系信息
- **文档更新**: 2024-08-24
- **技术支持**: 请查看项目文档或联系开发团队

### 有用链接
- [宝塔官方文档](https://www.bt.cn/bbs)
- [Flask官方文档](https://flask.palletsprojects.com)
- [Gunicorn官方文档](https://gunicorn.org)
- [MySQL官方文档](https://dev.mysql.com/doc)

---

**注意**: 生产环境部署前请务必修改所有默认密码和安全配置！