# CPQ系统前端宝塔部署指南

## 📋 概述

本指南详细说明如何在宝塔面板中部署CPQ系统前端应用，包括站点创建、配置优化、SSL证书配置和性能监控。

**部署信息：**
- 前端域名：`cpq.d1bk.com`
- 后端API：`cpqh.d1bbk.com` (端口5000)
- 技术栈：Vue3 + Vite + Element Plus
- 部署目录：`/www/wwwroot/cpq.d1bk.com/`

## 🚀 快速部署流程

### 第一步：创建网站

1. **登录宝塔面板**
   - 访问服务器的宝塔面板 (通常是 `http://服务器IP:8888`)
   - 使用管理员账户登录

2. **添加站点**
   ```
   网站 → 添加站点
   ```
   - **域名**：`cpq.d1bk.com`
   - **根目录**：`/www/wwwroot/cpq.d1bk.com`
   - **FTP**：不创建
   - **数据库**：不创建（前端无需数据库）
   - **PHP版本**：不安装（Vue应用无需PHP）

3. **创建必要目录结构**
   ```bash
   mkdir -p /www/wwwroot/cpq.d1bk.com/dist
   mkdir -p /www/wwwroot/cpq.d1bk.com/logs
   mkdir -p /www/backup/cpq-frontend
   ```

### 第二步：上传构建文件

1. **构建生产版本**
   ```bash
   # 在本地项目目录执行
   npm run build:prod-skip-check
   ```

2. **上传方式选择**

   **方式一：使用部署脚本（推荐）**
   ```bash
   # 配置脚本中的服务器信息
   REMOTE_HOST="你的服务器IP"
   REMOTE_USER="你的SSH用户名"
   
   # 执行部署
   ./deploy/deploy-frontend.sh
   ```

   **方式二：手动上传**
   - 将 `dist/` 目录下的所有文件打包为 `.zip`
   - 在宝塔面板文件管理中上传并解压到 `/www/wwwroot/cpq.d1bk.com/dist/`

3. **设置文件权限**
   ```bash
   chown -R www:www /www/wwwroot/cpq.d1bk.com/dist
   chmod -R 755 /www/wwwroot/cpq.d1bk.com/dist
   ```

### 第三步：配置Nginx

1. **访问站点设置**
   ```
   网站 → cpq.d1bk.com → 设置 → 配置文件
   ```

2. **替换配置内容**
   - 复制 `deploy/cpq-frontend.conf` 的内容
   - 完全替换现有的nginx配置
   - 点击保存

3. **测试配置**
   ```bash
   nginx -t
   ```

4. **重载Nginx**
   ```bash
   systemctl reload nginx
   ```

### 第四步：SSL证书配置

1. **申请SSL证书**
   ```
   网站 → cpq.d1bk.com → 设置 → SSL → Let's Encrypt
   ```
   - 选择域名：`cpq.d1bk.com`
   - 点击申请
   - 等待证书颁发

2. **强制HTTPS**
   - 开启"强制HTTPS"选项
   - 测试HTTP到HTTPS重定向

### 第五步：性能优化配置

1. **开启Gzip压缩**
   - 配置文件中已包含Gzip设置
   - 验证压缩是否生效：
   ```bash
   curl -I -H "Accept-Encoding: gzip" https://cpq.d1bk.com
   ```

2. **配置静态资源缓存**
   - 配置文件中已设置合适的缓存策略
   - JS/CSS/图片文件：1年缓存
   - HTML文件：不缓存

3. **启用HTTP/2**
   - 宝塔面板会自动启用HTTP/2（需要SSL证书）

## 📊 配置详情说明

### Nginx配置核心特性

1. **SPA路由支持**
   ```nginx
   location / {
       try_files $uri $uri/ /index.html;
   }
   ```

2. **API代理配置**
   ```nginx
   location /api/ {
       proxy_pass http://127.0.0.1:5000/api/;
       # 完整的代理配置和超时设置
   }
   ```

3. **静态资源优化**
   - 自动压缩：Gzip + Brotli
   - 缓存策略：差异化缓存时间
   - 跨域支持：CORS配置

4. **安全头配置**
   ```nginx
   add_header X-Content-Type-Options nosniff;
   add_header X-Frame-Options DENY;
   add_header X-XSS-Protection "1; mode=block";
   add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
   ```

### 目录结构

```
/www/wwwroot/cpq.d1bk.com/
├── dist/                 # 前端构建文件
│   ├── index.html       # 主页面
│   ├── assets/          # CSS样式文件
│   ├── js/              # JavaScript文件
│   ├── images/          # 图片资源
│   └── fonts/           # 字体文件
├── logs/                # 访问日志
│   ├── access.log
│   └── error.log
└── backup/              # 备份目录
```

## 🔧 后端API代理配置

### 确保后端服务运行

1. **检查Flask服务**
   ```bash
   # 检查5000端口是否监听
   netstat -tlnp | grep 5000
   
   # 测试后端健康检查
   curl http://127.0.0.1:5000/health
   ```

2. **配置自启动**
   - 在宝塔面板的进程守护中添加Flask应用
   - 或使用systemd服务配置

### API代理特性

1. **超时配置**
   - 连接超时：300秒
   - 支持AI分析长时间处理

2. **文件上传支持**
   - 最大文件大小：50MB
   - 支持多文件批量上传

3. **CORS配置**
   - 允许跨域请求
   - 预检请求处理

## 🔍 故障排查

### 常见问题及解决方案

1. **页面刷新404错误**
   ```
   原因：SPA路由配置问题
   解决：检查nginx配置中的try_files指令
   ```

2. **API请求失败**
   ```bash
   # 检查后端服务状态
   curl http://127.0.0.1:5000/health
   
   # 检查nginx错误日志
   tail -f /www/wwwroot/cpq.d1bk.com/logs/error.log
   ```

3. **静态资源加载失败**
   ```
   原因：文件权限或路径问题
   解决：检查文件权限和nginx配置的root路径
   ```

4. **SSL证书问题**
   ```bash
   # 检查证书有效性
   openssl x509 -in /path/to/cert.pem -text -noout
   
   # 测试HTTPS连接
   curl -I https://cpq.d1bk.com
   ```

### 日志监控

1. **访问日志**
   ```bash
   tail -f /www/wwwroot/cpq.d1bk.com/logs/access.log
   ```

2. **错误日志**
   ```bash
   tail -f /www/wwwroot/cpq.d1bk.com/logs/error.log
   ```

3. **Nginx主日志**
   ```bash
   tail -f /www/server/nginx/logs/error.log
   ```

## 📈 性能监控

### 关键指标

1. **页面加载时间**
   - 首屏加载：< 3秒
   - 交互响应：< 1秒

2. **资源大小**
   - 总包大小：~16MB
   - Gzip压缩后显著减小

3. **缓存命中率**
   - 静态资源应该有高缓存命中率
   - HTML页面不缓存确保内容更新

### 监控工具

1. **宝塔面板监控**
   - 系统资源：CPU、内存、磁盘
   - 网站流量和访问统计

2. **浏览器开发者工具**
   - Network面板检查资源加载
   - Performance面板分析性能

3. **外部监控**
   - 在线测速工具
   - 用户体验监控

## 🔄 更新部署流程

### 自动化更新

1. **使用部署脚本**
   ```bash
   # 构建并部署新版本
   ./deploy/deploy-frontend.sh
   
   # 仅构建不部署
   ./deploy/deploy-frontend.sh --build-only
   ```

2. **零停机更新**
   - 脚本会自动创建备份
   - 原子化替换文件
   - 失败自动回滚

### 手动更新

1. **备份当前版本**
   ```bash
   cp -r /www/wwwroot/cpq.d1bk.com/dist /www/backup/cpq-frontend/backup-$(date +%Y%m%d_%H%M%S)
   ```

2. **上传新版本**
   - 构建新版本
   - 上传并解压到临时目录
   - 原子化替换

3. **验证部署**
   - 检查网站是否正常访问
   - 验证API调用是否正常

## 💡 最佳实践

1. **版本控制**
   - 每次部署创建备份
   - 记录版本号和变更日志

2. **监控告警**
   - 设置可用性监控
   - 配置异常告警通知

3. **安全策略**
   - 定期更新SSL证书
   - 监控安全漏洞

4. **性能优化**
   - 定期检查资源大小
   - 监控页面加载性能
   - 优化图片和字体文件

---

## 📞 技术支持

如果在部署过程中遇到问题，请检查：

1. **系统要求**
   - Nginx版本 ≥ 1.18
   - SSL证书正确配置
   - 后端服务正常运行

2. **配置文件**
   - nginx配置语法正确
   - 文件路径存在
   - 权限设置正确

3. **网络连接**
   - 域名DNS解析正确
   - 防火墙端口开放
   - API代理连接正常

**部署完成后，访问 https://cpq.d1bk.com 验证部署效果！**