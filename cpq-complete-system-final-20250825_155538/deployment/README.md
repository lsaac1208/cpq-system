# CPQ系统宝塔面板部署工具包

## 🎯 概述

这是CPQ系统在宝塔面板的完整部署解决方案，由 **devops-troubleshooter + cloud-architect + backend-architect** 联合团队开发。包含自动化脚本、验证工具和详细文档，让您可以在30分钟内完成完整的生产环境部署。

## 📦 工具包内容

### 🤖 自动化脚本
- **`baota-deploy-automation.sh`** - 宝塔环境一键配置脚本
- **`package-preparation.sh`** - 部署包自动生成脚本
- **`cpq-deployment-validator.py`** - 智能部署验证工具
- **`test-deployment-tools.sh`** - 工具包完整性测试

### 📚 详细文档  
- **`DEPLOYMENT_EXECUTION_GUIDE.md`** - 完整部署执行指南
- **`step-by-step-deployment-guide.md`** - 分步详细操作手册
- **`deployment-commands.md`** - 常用命令速查表
- **`FINAL_DEPLOYMENT_SUMMARY.md`** - 部署方案总结

### ⚙️ 配置模板
- Nginx前后端配置模板
- systemd服务配置文件
- 环境变量配置模板
- Gunicorn WSGI服务配置

## 🚀 快速开始

### 第一步：验证工具包完整性

```bash
cd deployment/
./test-deployment-tools.sh
```

应该看到：
```
✅ 所有测试通过！部署工具准备就绪
```

### 第二步：生成部署包

```bash
./package-preparation.sh
```

将生成完整的部署包：`cpq-baota-deploy-YYYYMMDD_HHMMSS.tar.gz`

### 第三步：上传到宝塔服务器

通过宝塔面板文件管理器或SCP命令上传部署包到服务器。

### 第四步：服务器端一键部署

在宝塔服务器终端执行：

```bash
# 解压部署包
tar -xzf cpq-baota-deploy-*.tar.gz
cd cpq-baota-deploy-*/scripts/

# 一键安装
./quick-install.sh
```

### 第五步：验证部署

```bash
python3 cpq-deployment-validator.py
```

应该看到：
```
🎉 部署验证通过！
🌐 访问地址: http://cpq.d1bk.com  
🔐 默认登录: admin / admin123
```

## 📊 部署目标

- **前端域名**: `cpq.d1bk.com` (HTTP端口80)
- **后端域名**: `cpqh.d1bbk.com` (HTTP端口5000)
- **数据库**: MySQL `cpq_system`
- **预计用时**: 30-45分钟

## ✅ 系统要求

### 服务器环境
- **操作系统**: CentOS 7+ / Ubuntu 18+ / Debian 9+
- **宝塔面板**: 7.7.0+
- **内存**: 2GB+ 推荐
- **硬盘**: 5GB+ 可用空间
- **CPU**: 2核+ 推荐

### 软件版本
- **Python**: 3.8+
- **MySQL**: 5.7+ / 8.0+  
- **Nginx**: 1.18+

### 域名准备
确保以下域名已解析到服务器IP：
- `cpq.d1bk.com` (前端)
- `cpqh.d1bbk.com` (后端)

## 🔧 常用管理命令

```bash
# 服务管理 (在后端目录执行)
cd /www/wwwroot/cpqh.d1bbk.com/
./start.sh start    # 启动服务
./start.sh stop     # 停止服务
./start.sh restart  # 重启服务
./start.sh status   # 查看状态
./start.sh logs     # 查看日志
./start.sh health   # 健康检查

# 部署验证
python3 /root/cpq-baota-deploy-*/scripts/cpq-deployment-validator.py
```

## 📋 部署后检查清单

- [ ] 前端页面可访问 (`http://cpq.d1bk.com`)
- [ ] 后端API健康检查通过 (`http://cpqh.d1bbk.com/health`)
- [ ] 管理员账号可正常登录 (admin/admin123)
- [ ] 产品管理功能正常
- [ ] 报价管理功能正常
- [ ] 文件上传功能正常

## 🚨 故障排查

### 1. 如果一键安装失败
```bash
# 查看详细错误日志
./quick-install.sh 2>&1 | tee install.log

# 然后参考 step-by-step-deployment-guide.md 进行手动部署
```

### 2. 如果服务启动失败
```bash
# 查看系统服务日志
journalctl -u cpq-api --no-pager -l

# 查看应用日志
tail -f /www/wwwroot/cpqh.d1bbk.com/logs/app.log

# 手动测试启动
cd /www/wwwroot/cpqh.d1bbk.com/
python3 app.py
```

### 3. 如果前端页面空白
```bash
# 检查Nginx配置
nginx -t

# 检查文件权限
ls -la /www/wwwroot/cpq.d1bk.com/dist/

# 查看Nginx错误日志
tail -f /www/server/nginx/logs/error.log
```

## 📞 技术支持

### 获取帮助的步骤

1. **运行验证脚本**: `python3 cpq-deployment-validator.py`
2. **查看详细文档**: 参考对应的.md文档文件
3. **收集错误信息**: 保存相关的日志文件
4. **检查命令参考**: 查看 `deployment-commands.md`

### 日志文件位置
- 应用日志: `/www/wwwroot/cpqh.d1bbk.com/logs/app.log`
- 系统日志: `journalctl -u cpq-api`
- Nginx日志: `/www/server/nginx/logs/error.log`
- 验证报告: `/www/wwwroot/cpqh.d1bbk.com/logs/validation_report_*.json`

## 🎉 部署成功后

恭喜！您将拥有：

- ✅ 完整的生产级CPQ系统
- ✅ 现代化的前端SPA应用 (16MB，已优化)
- ✅ 高性能的Flask API后端
- ✅ 完整的用户认证和权限管理
- ✅ 产品和报价管理功能
- ✅ AI智能分析功能 (需配置API密钥)
- ✅ 自动化的服务管理脚本
- ✅ 完善的日志和监控系统

**访问地址**: http://cpq.d1bk.com  
**管理员账号**: admin / admin123 (请及时修改密码)

---

## 📝 版本信息

- **版本**: 1.0.0
- **构建时间**: 2025-01-25
- **兼容性**: 宝塔面板 7.7.0+
- **支持系统**: CentOS 7+, Ubuntu 18+, Debian 9+

---

**🚀 祝您部署顺利！**