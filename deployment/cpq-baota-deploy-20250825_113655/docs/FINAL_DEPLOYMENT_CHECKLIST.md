# 🚀 CPQ系统宝塔面板部署总清单

## 📋 部署完成确认清单

### 🔧 服务器环境准备
- [ ] 宝塔面板已安装并可正常访问
- [ ] Nginx 已安装并运行
- [ ] Python 3.8+ 已安装
- [ ] MySQL 5.7+ 已安装并运行
- [ ] 域名 DNS 解析已配置：
  - [ ] cpq.d1bk.com → 服务器IP
  - [ ] cpqh.d1bbk.com → 服务器IP

### 🔷 后端部署步骤

#### 1. 创建Python项目
```bash
# 在宝塔面板 > 网站 > Python项目
项目名称: CPQ-API
域名: cpqh.d1bbk.com
端口: 5000
Python版本: 3.8+
启动文件: app.py
```

#### 2. 上传后端代码
- [ ] 上传 apps/api/ 目录到项目根目录
- [ ] 上传 deploy/.env.production 到项目根目录并重命名为 .env
- [ ] 上传 deploy/gunicorn.conf.py 到项目根目录
- [ ] 上传 deploy/requirements-production.txt 到项目根目录

#### 3. 安装依赖和配置
```bash
# SSH连接服务器执行
cd /www/wwwroot/cpqh.d1bbk.com
pip install -r requirements-production.txt
chmod +x deploy/start.sh
```

#### 4. 数据库配置
- [ ] 在宝塔面板创建MySQL数据库：cpq_system
- [ ] 修改 .env 中的数据库配置：
```bash
DATABASE_URL=mysql://用户名:密码@localhost/cpq_system
```
- [ ] 运行数据库迁移：`python deploy/migrate.py`

#### 5. 启动后端服务
```bash
# 方式1：直接启动
./deploy/start.sh start

# 方式2：使用systemd服务
sudo cp deploy/cpq-api.service /etc/systemd/system/
sudo systemctl enable cpq-api
sudo systemctl start cpq-api
```

### 🔶 前端部署步骤

#### 1. 创建HTML站点
```bash
# 在宝塔面板 > 网站 > 添加站点
域名: cpq.d1bk.com
根目录: /www/wwwroot/cpq.d1bk.com/
PHP版本: 纯静态
```

#### 2. 上传前端文件
- [ ] 上传 apps/web/dist/ 目录的所有文件到网站根目录
- [ ] 确认 index.html 在根目录

#### 3. 配置Nginx
- [ ] 在宝塔面板 > 网站 > cpq.d1bk.com > 设置 > 配置文件
- [ ] 替换为 deploy/cpq-frontend.conf 的内容
- [ ] 保存并重载Nginx配置

### 🔍 功能测试清单

#### 后端API测试
```bash
# 1. 健康检查
curl http://cpqh.d1bbk.com/api/v1/health

# 2. 登录测试
curl -X POST http://cpqh.d1bbk.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 3. 产品列表
curl http://cpqh.d1bbk.com/api/v1/products?page=1&per_page=10
```

#### 前端功能测试
- [ ] 访问 http://cpq.d1bk.com 可正常打开
- [ ] 登录页面正常显示
- [ ] 使用 admin/admin123 可成功登录
- [ ] 仪表盘数据正常加载
- [ ] 产品管理功能正常
- [ ] 报价管理功能正常
- [ ] AI功能菜单正常（如已配置API密钥）
- [ ] 系统设置菜单对管理员可见

#### 网络连通性测试
- [ ] 前端可正常调用后端API
- [ ] CORS跨域配置正确
- [ ] 文件上传功能正常
- [ ] 静态资源加载正常

### 🔒 安全配置检查
- [ ] 生产环境密钥已修改（不使用默认值）
- [ ] 数据库访问权限配置正确
- [ ] 文件上传目录权限设置正确
- [ ] Nginx安全头配置生效

### 📊 性能验证
- [ ] 首页加载时间 < 3秒
- [ ] API响应时间 < 500ms
- [ ] 静态资源正确缓存
- [ ] Gzip压缩正常工作

### 🚨 常见问题排查

#### 问题1: 前端空白页面
```bash
# 检查Nginx错误日志
tail -f /www/wwwroot/cpq.d1bk.com/log/error.log

# 检查控制台是否有JavaScript错误
# 确认API地址配置正确
```

#### 问题2: API连接失败
```bash
# 检查后端服务状态
systemctl status cpq-api

# 检查端口是否监听
netstat -tlnp | grep :5000

# 检查防火墙规则
ufw status
```

#### 问题3: 数据库连接失败
```bash
# 检查MySQL服务
systemctl status mysql

# 测试数据库连接
mysql -u用户名 -p密码 -h localhost cpq_system
```

#### 问题4: 文件上传失败
```bash
# 检查上传目录权限
ls -la /www/wwwroot/cpqh.d1bbk.com/instance/uploads/
chmod 755 /www/wwwroot/cpqh.d1bbk.com/instance/uploads/
```

### 🔄 维护操作

#### 重启服务
```bash
# 重启后端服务
systemctl restart cpq-api

# 重启Nginx
systemctl restart nginx

# 重启前端（仅重新加载配置）
nginx -s reload
```

#### 查看日志
```bash
# 后端应用日志
tail -f /www/wwwroot/cpqh.d1bbk.com/logs/app.log

# Nginx访问日志
tail -f /www/wwwroot/cpq.d1bk.com/log/access.log

# 系统服务日志
journalctl -u cpq-api -f
```

#### 数据库备份
```bash
# 手动备份
mysqldump -u用户名 -p密码 cpq_system > backup_$(date +%Y%m%d).sql

# 恢复数据库
mysql -u用户名 -p密码 cpq_system < backup_20250824.sql
```

### 🎯 部署完成标准

✅ **成功标准**：
- 前端页面可正常访问并显示
- 管理员可成功登录系统
- 仪表盘数据正常显示
- 产品和报价功能正常工作
- 系统设置菜单对管理员可见
- API响应正常，无错误日志

🎊 **部署完成！** 

当所有检查项都完成后，你的CPQ系统就已经成功部署到宝塔面板了！

---

## 📞 技术支持

如果在部署过程中遇到问题，请检查：
1. 相关日志文件
2. 网络连接状态  
3. 服务运行状态
4. 配置文件语法

按照此清单逐步完成，确保每一项都正确配置！