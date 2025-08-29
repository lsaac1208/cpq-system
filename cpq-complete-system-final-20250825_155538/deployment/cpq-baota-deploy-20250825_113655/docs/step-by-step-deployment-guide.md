# CPQ系统宝塔面板分步部署指南

## 📋 部署概览

**目标**: 在宝塔面板中部署完整的CPQ系统
**域名配置**: 
- 前端: `cpq.d1bk.com` (端口80)
- 后端: `cpqh.d1bbk.com` (端口5000)

**预计用时**: 30-45分钟

---

## 🏗️ 第一阶段：环境准备 (10分钟)

### 步骤1: 服务器基础检查

在宝塔面板终端执行以下命令：

```bash
# 检查系统信息
uname -a
free -h
df -h

# 检查必要服务
systemctl status nginx
systemctl status mysql
systemctl status mysqld  # CentOS/RHEL系统
```

**期望结果**: 
- Linux系统，内存>1GB，磁盘空间>5GB
- Nginx和MySQL服务都在运行

### 步骤2: 安装Python环境

1. 在宝塔面板进入 **软件商店** → **Python版本管理器**
2. 安装 **Python 3.8** 或更高版本
3. 验证安装：

```bash
python3 --version
pip3 --version
```

### 步骤3: 准备域名解析

确保以下域名已正确解析到服务器IP：
- `cpq.d1bk.com` → 你的服务器IP
- `cpqh.d1bbk.com` → 你的服务器IP

**验证方法**:
```bash
nslookup cpq.d1bk.com
nslookup cpqh.d1bbk.com
```

---

## 🔧 第二阶段：自动化环境配置 (5分钟)

### 步骤4: 下载并运行自动化配置脚本

1. 创建部署目录：
```bash
mkdir -p /root/cpq-deployment
cd /root/cpq-deployment
```

2. 上传自动化脚本到这个目录:
   - `baota-deploy-automation.sh`
   - `cpq-deployment-validator.py`

3. 运行自动化配置：
```bash
chmod +x baota-deploy-automation.sh
./baota-deploy-automation.sh
```

**脚本会自动完成**:
- ✅ 环境检查
- ✅ 创建MySQL数据库和用户
- ✅ 创建目录结构
- ✅ 生成配置文件
- ✅ 配置Nginx
- ✅ 设置systemd服务
- ✅ 生成管理脚本

**期望输出**:
```
✅ 环境检查通过
✅ 数据库创建成功
✅ 目录结构准备完成
✅ 配置文件生成完成
✅ CPQ系统宝塔面板部署配置完成！
```

---

## 📦 第三阶段：上传项目文件 (10分钟)

### 步骤5: 上传后端代码

1. **压缩本地后端代码**:
```bash
# 在项目根目录执行
cd apps/api
tar -czf cpq-backend.tar.gz \
  --exclude=__pycache__ \
  --exclude=*.pyc \
  --exclude=.git \
  --exclude=instance/cpq_system.db \
  --exclude=logs \
  --exclude=tmp \
  .
```

2. **上传到服务器**:
   - 使用宝塔面板文件管理器上传 `cpq-backend.tar.gz`
   - 上传位置: `/www/wwwroot/cpqh.d1bbk.com/`

3. **解压文件**:
```bash
cd /www/wwwroot/cpqh.d1bbk.com/
tar -xzf cpq-backend.tar.gz
rm cpq-backend.tar.gz

# 设置权限
chown -R www:www /www/wwwroot/cpqh.d1bbk.com/
chmod -R 755 /www/wwwroot/cpqh.d1bbk.com/
chmod -R 777 /www/wwwroot/cpqh.d1bbk.com/instance/uploads/
```

### 步骤6: 上传前端构建文件

1. **压缩前端构建产物**:
```bash
# 在项目根目录执行
cd apps/web
tar -czf cpq-frontend.tar.gz dist/
```

2. **上传到服务器**:
   - 使用宝塔面板文件管理器上传 `cpq-frontend.tar.gz`
   - 上传位置: `/www/wwwroot/cpq.d1bk.com/`

3. **解压文件**:
```bash
cd /www/wwwroot/cpq.d1bk.com/
tar -xzf cpq-frontend.tar.gz
rm cpq-frontend.tar.gz

# 设置权限
chown -R www:www /www/wwwroot/cpq.d1bk.com/
```

---

## ⚙️ 第四阶段：安装依赖和初始化 (10分钟)

### 步骤7: 安装Python依赖

```bash
cd /www/wwwroot/cpqh.d1bbk.com/

# 安装生产环境依赖
pip3 install -r requirements-production.txt

# 如果安装过程中出现错误，可以尝试：
pip3 install --upgrade pip
pip3 install -r requirements-production.txt --no-cache-dir
```

### 步骤8: 修改环境配置

检查并修改环境配置文件 `.env`:

```bash
vi /www/wwwroot/cpqh.d1bbk.com/.env
```

**重要配置项**:
- `SECRET_KEY`: 更改为随机字符串
- `JWT_SECRET_KEY`: 更改为随机字符串  
- `MYSQL_PASSWORD`: 确认数据库密码正确
- `CORS_ORIGINS`: 确认域名正确

### 步骤9: 初始化数据库

```bash
cd /www/wwwroot/cpqh.d1bbk.com/

# 运行数据库初始化脚本
python3 init_database.py
```

**期望输出**:
```
🚀 开始初始化数据库...
📋 创建数据库表...
✅ 数据库表创建完成
👤 创建管理员用户...
✅ 管理员用户创建完成
⚙️ 创建系统默认设置...
✅ 系统默认设置创建完成
🎉 数据库初始化成功！
```

---

## 🚀 第五阶段：启动服务和验证 (10分钟)

### 步骤10: 启动后端服务

```bash
cd /www/wwwroot/cpqh.d1bbk.com/

# 启动CPQ API服务
./start.sh start
```

**期望输出**:
```
ℹ️ 启动CPQ API服务...
✅ CPQ API服务启动成功
```

### 步骤11: 重载Nginx配置

```bash
# 测试Nginx配置
nginx -t

# 重载Nginx
nginx -s reload
```

### 步骤12: 运行部署验证

```bash
cd /www/wwwroot/cpqh.d1bbk.com/

# 运行验证脚本
python3 /root/cpq-deployment/cpq-deployment-validator.py
```

**期望看到**:
```
✅ Linux系统检测通过
✅ 宝塔面板检测通过
✅ Python版本检测通过: 3.8.x
✅ MySQL服务运行正常
✅ Nginx服务运行正常
✅ CPQ API服务运行正常
✅ 端口 5000 监听正常
✅ HTTP端点正常: http://127.0.0.1:5000/health
🎉 部署验证通过！
```

### 步骤13: 验证Web访问

1. **测试前端访问**:
   - 浏览器访问 `http://cpq.d1bk.com`
   - 应该看到CPQ系统登录页面

2. **测试登录功能**:
   - 用户名: `admin`
   - 密码: `admin123`
   - 登录后应能看到仪表板

3. **测试API连接**:
```bash
curl -I http://127.0.0.1:5000/health
curl -I http://cpqh.d1bbk.com/health
```

---

## 🎯 部署完成验证清单

### ✅ 必须通过的检查项

- [ ] 前端页面可以正常访问 (`http://cpq.d1bk.com`)
- [ ] 后端API健康检查通过 (`http://cpqh.d1bbk.com/health`)
- [ ] 用户可以成功登录 (admin/admin123)
- [ ] 可以访问产品管理页面
- [ ] 可以访问报价管理页面
- [ ] API和前端可以正常通信

### ⚠️ 可选检查项

- [ ] SSL证书配置 (生产环境推荐)
- [ ] 防火墙规则配置
- [ ] 日志轮转配置
- [ ] 自动备份配置

---

## 🔧 常用管理命令

### 服务管理

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

### 故障排查

```bash
# 查看系统服务状态
systemctl status cpq-api

# 查看详细日志
journalctl -u cpq-api -f

# 查看应用日志
tail -f /www/wwwroot/cpqh.d1bbk.com/logs/app.log

# 查看Gunicorn日志  
tail -f /www/wwwroot/cpqh.d1bbk.com/logs/gunicorn_error.log

# 查看Nginx日志
tail -f /www/server/nginx/logs/error.log
tail -f /www/wwwroot/cpq.d1bk.com/logs/error.log

# 检查端口监听
netstat -tlnp | grep :5000

# 检查进程
ps aux | grep gunicorn
```

### 数据库管理

```bash
# 连接数据库
mysql -u cpq_user -p cpq_system

# 查看数据库大小
mysql -u cpq_user -p -e "
SELECT 
  table_schema AS 'Database',
  ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'DB Size (MB)'
FROM information_schema.tables 
WHERE table_schema='cpq_system';"
```

---

## 🚨 故障排除指南

### 1. 服务启动失败

**症状**: `./start.sh start` 失败

**解决步骤**:
```bash
# 检查错误日志
journalctl -u cpq-api --no-pager -l

# 检查配置文件
cat /www/wwwroot/cpqh.d1bbk.com/.env

# 检查Python依赖
cd /www/wwwroot/cpqh.d1bbk.com/
python3 -c "import flask; print('Flask OK')"

# 手动测试启动
python3 app.py
```

### 2. 数据库连接失败

**症状**: 数据库连接错误

**解决步骤**:
```bash
# 检查MySQL服务
systemctl status mysql

# 测试数据库连接
mysql -u cpq_user -p cpq_system -e "SELECT 1;"

# 检查环境变量
cat /www/wwwroot/cpqh.d1bbk.com/.env | grep MYSQL
```

### 3. 前端页面显示异常

**症状**: 前端空白或404

**解决步骤**:
```bash
# 检查文件是否存在
ls -la /www/wwwroot/cpq.d1bk.com/dist/

# 检查Nginx配置
nginx -t
cat /www/server/panel/vhost/nginx/cpq.d1bk.com.conf

# 检查Nginx错误日志
tail -f /www/wwwroot/cpq.d1bk.com/logs/error.log
```

### 4. API调用失败

**症状**: 前端无法调用后端API

**解决步骤**:
```bash
# 测试API健康检查
curl -v http://127.0.0.1:5000/health

# 检查跨域设置
cat /www/wwwroot/cpqh.d1bbk.com/.env | grep CORS

# 检查防火墙
iptables -L | grep 5000
```

---

## 📞 技术支持

如果遇到问题，请：

1. **收集错误信息**:
   - 运行验证脚本: `python3 cpq-deployment-validator.py`
   - 保存错误日志文件

2. **查看详细日志**:
   - 系统日志: `/var/log/messages`
   - 应用日志: `/www/wwwroot/cpqh.d1bbk.com/logs/`
   - Nginx日志: `/www/server/nginx/logs/`

3. **提供系统信息**:
   - 操作系统版本
   - 宝塔面板版本
   - Python版本
   - MySQL版本

---

## 🎉 部署成功

当所有步骤完成后，您将拥有：

- ✅ 完整的CPQ系统运行在生产环境
- ✅ 前端SPA应用 (http://cpq.d1bk.com)
- ✅ 后端API服务 (http://cpqh.d1bbk.com)
- ✅ 完整的用户认证和权限管理
- ✅ 产品和报价管理功能
- ✅ 系统监控和日志记录
- ✅ 自动化服务管理脚本

**默认管理员账号**: admin / admin123  
**建议**: 部署完成后立即修改管理员密码！