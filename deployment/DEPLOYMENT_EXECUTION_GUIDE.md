# CPQ系统宝塔面板部署执行指南

## 🎯 总览

本指南提供完整的CPQ系统宝塔面板部署解决方案，包含自动化脚本、验证工具和详细操作步骤。由devops-troubleshooter + cloud-architect + backend-architect联合团队制作。

**部署目标**:
- 前端域名: `cpq.d1bk.com` (HTTP端口80)
- 后端域名: `cpqh.d1bbk.com` (HTTP端口5000)  
- 数据库: MySQL `cpq_system`
- 环境: 宝塔面板 + CentOS/Ubuntu

---

## 📦 准备阶段：创建部署包

### 步骤1: 生成完整部署包

在本地开发环境运行：

```bash
# 进入部署目录
cd deployment/

# 运行部署包准备脚本
chmod +x package-preparation.sh
./package-preparation.sh
```

**输出结果**:
```
✅ 环境检查通过
✅ 后端文件准备完成 (大小: 45MB)
✅ 前端文件准备完成 (大小: 16MB)
✅ 配置文件准备完成
✅ 部署脚本准备完成
✅ 文档准备完成
✅ 压缩包创建完成: cpq-baota-deploy-20250125_143022.tar.gz (大小: 25MB)
```

### 步骤2: 上传到宝塔服务器

1. **通过宝塔文件管理器**:
   - 登录宝塔面板
   - 进入文件管理 → 根目录
   - 上传 `cpq-baota-deploy-*.tar.gz`

2. **通过SCP命令**:
```bash
scp cpq-baota-deploy-*.tar.gz root@YOUR_SERVER_IP:/root/
```

---

## 🚀 执行阶段：服务器部署

### 方式一：一键快速部署 (推荐)

在宝塔服务器终端执行：

```bash
# 1. 解压部署包
cd /root
tar -xzf cpq-baota-deploy-*.tar.gz
cd cpq-baota-deploy-*/

# 2. 运行一键安装
cd scripts/
chmod +x quick-install.sh
./quick-install.sh
```

**期望输出**:
```
======================================
       CPQ系统快速安装向导
======================================

ℹ️ 开始CPQ系统安装...
ℹ️ 步骤1: 运行环境配置...
✅ 环境检查通过
✅ 数据库创建成功
✅ 配置文件生成完成
ℹ️ 步骤2: 部署后端文件...
✅ 后端文件部署完成
ℹ️ 步骤3: 部署前端文件...
✅ 前端文件部署完成
ℹ️ 步骤4: 安装Python依赖...
✅ Python依赖安装完成
ℹ️ 步骤5: 初始化数据库...
✅ 数据库初始化完成
ℹ️ 步骤6: 启动服务...
✅ 服务启动完成
ℹ️ 步骤7: 运行部署验证...
✅ 所有检查项通过！部署验证成功
✅ CPQ系统安装完成！
```

### 方式二：分步手动部署

如果一键部署失败，可以按以下步骤手动执行：

#### 2.1 环境配置

```bash
cd scripts/
chmod +x baota-deploy-automation.sh
./baota-deploy-automation.sh
```

#### 2.2 部署文件

```bash
# 部署后端
rsync -av ../backend/ /www/wwwroot/cpqh.d1bbk.com/
chown -R www:www /www/wwwroot/cpqh.d1bbk.com/
chmod -R 755 /www/wwwroot/cpqh.d1bbk.com/
chmod -R 777 /www/wwwroot/cpqh.d1bbk.com/instance/uploads/

# 部署前端
mkdir -p /www/wwwroot/cpq.d1bk.com/dist
rsync -av ../frontend/ /www/wwwroot/cpq.d1bk.com/dist/
chown -R www:www /www/wwwroot/cpq.d1bk.com/
```

#### 2.3 安装依赖和初始化

```bash
cd /www/wwwroot/cpqh.d1bbk.com/

# 安装Python依赖
pip3 install -r requirements-production.txt

# 初始化数据库
python3 init_database.py

# 启动服务
./start.sh start
```

---

## ✅ 验证阶段：部署检查

### 步骤1: 运行自动验证

```bash
cd /root/cpq-baota-deploy-*/scripts/
python3 cpq-deployment-validator.py
```

**期望看到**:
```
🔍 CPQ系统部署验证开始...

🚀 检查系统要求
✅ Linux系统检测通过
✅ 宝塔面板检测通过
✅ Python版本检测通过: 3.8.10
✅ MySQL服务运行正常
✅ Nginx服务运行正常

🚀 检查服务状态
✅ CPQ API服务运行正常
✅ 端口 5000 监听正常

🚀 检查API端点
✅ HTTP端点正常: http://127.0.0.1:5000/health

🚀 检查Web访问
✅ HTTP端点正常: http://cpq.d1bk.com

🎉 部署验证通过！

🌐 访问地址:
   前端: http://cpq.d1bk.com
   后端: http://cpqh.d1bbk.com

🔐 默认登录:
   用户名: admin
   密码: admin123
```

### 步骤2: 手动功能测试

1. **前端访问测试**:
   - 浏览器访问 `http://cpq.d1bk.com`
   - 应看到CPQ系统登录页面

2. **登录功能测试**:
   - 用户名: `admin`
   - 密码: `admin123`
   - 成功登录后应看到仪表板

3. **API连接测试**:
```bash
# 健康检查
curl -I http://127.0.0.1:5000/health
curl -I http://cpqh.d1bbk.com/health

# API端点测试
curl -s http://127.0.0.1:5000/api/v1/products | head -20
```

4. **基本功能测试**:
   - 访问产品管理页面
   - 访问报价管理页面
   - 尝试创建新产品
   - 检查图片上传功能

---

## 🔧 服务管理

### 常用管理命令

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

### 服务状态检查

```bash
# 检查系统服务
systemctl status cpq-api

# 检查端口监听
netstat -tlnp | grep :5000

# 检查进程
ps aux | grep gunicorn

# 检查数据库连接
mysql -u cpq_user -p cpq_system -e "SELECT COUNT(*) FROM users;"
```

---

## 🚨 故障排除

### 常见问题和解决方案

#### 1. 一键安装失败

**症状**: `quick-install.sh` 执行中断

**排查步骤**:
```bash
# 查看详细错误
cd /root/cpq-baota-deploy-*/scripts/
./quick-install.sh 2>&1 | tee install.log

# 检查各个组件
systemctl status nginx
systemctl status mysql
python3 --version
```

**解决方法**: 根据错误信息，选择手动分步部署

#### 2. 服务启动失败

**症状**: `./start.sh start` 失败

**排查步骤**:
```bash
# 查看系统日志
journalctl -u cpq-api --no-pager -l

# 查看应用日志
tail -f /www/wwwroot/cpqh.d1bbk.com/logs/app.log

# 手动测试启动
cd /www/wwwroot/cpqh.d1bbk.com/
python3 app.py
```

**常见原因**:
- Python依赖缺失: `pip3 install -r requirements-production.txt`
- 数据库连接失败: 检查`.env`配置文件
- 端口被占用: `netstat -tlnp | grep :5000`

#### 3. 前端页面空白

**症状**: 访问 `http://cpq.d1bk.com` 显示空白

**排查步骤**:
```bash
# 检查文件是否存在
ls -la /www/wwwroot/cpq.d1bk.com/dist/

# 检查Nginx配置
nginx -t
cat /www/server/panel/vhost/nginx/cpq.d1bk.com.conf

# 查看Nginx错误日志
tail -f /www/wwwroot/cpq.d1bk.com/logs/error.log
```

**常见原因**:
- 文件权限问题: `chown -R www:www /www/wwwroot/cpq.d1bk.com/`
- Nginx配置错误: 检查配置文件语法
- 文件路径错误: 确认dist目录下有index.html

#### 4. API调用失败  

**症状**: 前端无法调用后端API

**排查步骤**:
```bash
# 测试API端点
curl -v http://127.0.0.1:5000/health
curl -v http://cpq.d1bk.com/api/health

# 检查跨域设置
cat /www/wwwroot/cpqh.d1bbk.com/.env | grep CORS

# 检查反向代理
curl -I http://cpq.d1bk.com/api/v1/products
```

**常见原因**:
- 后端服务未启动: `./start.sh start`
- 反向代理配置错误: 检查Nginx配置
- 跨域设置错误: 检查CORS配置

---

## 📊 性能监控

### 基本监控命令

```bash
# 系统资源监控
htop
df -h
free -h

# 服务监控
systemctl status cpq-api
./start.sh status

# 日志监控
tail -f /www/wwwroot/cpqh.d1bbk.com/logs/app.log
tail -f /www/wwwroot/cpq.d1bk.com/logs/access.log
```

### 性能调优建议

1. **Gunicorn工作进程数**:
```bash
# 编辑配置文件
vi /www/wwwroot/cpqh.d1bbk.com/gunicorn.conf.py

# 调整workers数量 (建议: CPU核心数 * 2 + 1)
workers = 4
```

2. **MySQL连接池**:
```bash
# 编辑环境配置
vi /www/wwwroot/cpqh.d1bbk.com/.env

# 调整数据库连接参数
DATABASE_URL=mysql+pymysql://cpq_user:password@localhost:3306/cpq_system?charset=utf8mb4&pool_size=10&max_overflow=20
```

3. **Nginx缓存优化**:
   - 配置文件中已包含静态资源缓存设置
   - 可根据实际情况调整缓存时间

---

## 🔐 安全建议

### 部署完成后必须执行

1. **修改默认密码**:
```bash
# 登录系统后修改admin用户密码
```

2. **更新安全密钥**:
```bash
vi /www/wwwroot/cpqh.d1bbk.com/.env

# 修改以下配置为随机字符串
SECRET_KEY=your-new-secret-key
JWT_SECRET_KEY=your-new-jwt-secret-key
```

3. **数据库安全**:
```bash
# 修改数据库用户密码
mysql -uroot -p
ALTER USER 'cpq_user'@'localhost' IDENTIFIED BY 'new_secure_password';
FLUSH PRIVILEGES;

# 更新环境配置文件中的数据库密码
```

4. **防火墙配置** (可选):
```bash
# 只开放必要端口
firewall-cmd --permanent --add-port=80/tcp
firewall-cmd --permanent --add-port=443/tcp
firewall-cmd --reload
```

### SSL证书配置 (推荐)

在宝塔面板中为域名申请SSL证书：
1. 网站 → cpq.d1bk.com → SSL → Let's Encrypt
2. 申请免费证书并开启强制HTTPS
3. 对cpqh.d1bbk.com重复相同操作

---

## 📝 部署清单

### ✅ 部署前检查

- [ ] 服务器环境满足要求 (Linux + 宝塔面板 + Python3.8+ + MySQL + Nginx)
- [ ] 域名DNS解析已配置 (cpq.d1bk.com, cpqh.d1bbk.com)
- [ ] 部署包已上传到服务器
- [ ] 具有root权限

### ✅ 部署过程检查

- [ ] 自动化配置脚本执行成功
- [ ] 数据库创建成功
- [ ] 后端文件部署完成
- [ ] 前端文件部署完成  
- [ ] Python依赖安装完成
- [ ] 数据库初始化完成
- [ ] 服务启动成功

### ✅ 部署后验证

- [ ] 验证脚本全部通过
- [ ] 前端页面可以访问
- [ ] 登录功能正常 (admin/admin123)
- [ ] API健康检查通过
- [ ] 基本功能测试通过
- [ ] 文件上传功能正常

### ✅ 安全配置

- [ ] 修改默认管理员密码
- [ ] 更新安全密钥
- [ ] 配置SSL证书 (推荐)
- [ ] 配置防火墙规则 (可选)

---

## 🎉 部署成功

当所有检查项通过后，您将拥有：

- ✅ 完整的生产级CPQ系统
- ✅ 高可用的前后端架构
- ✅ 自动化的服务管理
- ✅ 完善的日志和监控
- ✅ 安全的配置和权限管理

**访问地址**: http://cpq.d1bk.com  
**管理员账号**: admin / admin123 (请及时修改密码)

**恭喜！CPQ系统部署完成，可以开始使用了！** 🎊