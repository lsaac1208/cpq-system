# CPQ系统完整部署指南

**部署包**: `cpq-complete-system-20250825_154455.tar.gz` (78MB)  
**版本**: v2.0 - 修复所有已知问题  
**时间**: 2025-08-25

## 🎉 本版本修复的问题

### ✅ 已修复问题
1. **JavaScript模块初始化错误** - 修复 `Cannot access 'ze' before initialization`
2. **CORS跨域访问问题** - 修复前端无法访问后端API
3. **创建报价页面错误** - 修复 `Invalid literal for int() with base 10: 'admin'`
4. **AI功能依赖缺失** - 提供完整的AI功能依赖安装方案
5. **登录页面演示账户** - 更新完整的演示账户列表

### 🔧 技术改进
- 优化Vite构建配置，避免模块循环依赖
- 增强CORS配置，支持本地开发和生产环境
- 修复JWT用户身份识别问题
- 提供AI功能降级处理方案

## 📦 部署包内容

```
cpq-complete-system-20250825_154455.tar.gz
├── apps/web/dist/                    # 前端构建产物
├── apps/api/                         # 后端API完整代码
│   ├── requirements.txt              # 核心Python依赖
│   ├── requirements-ai.txt           # AI功能依赖
│   ├── requirements-production.txt   # 生产环境依赖
│   ├── install_ai_dependencies.sh    # AI依赖自动安装脚本
│   ├── .env.template                 # 环境配置模板
│   ├── .env.production              # 生产环境配置示例
│   ├── gunicorn.conf.py             # Gunicorn配置
│   └── src/                         # 源代码
├── deployment/                      # 部署配置
└── scripts/                         # 辅助脚本
```

## 🚀 快速部署步骤

### 1. 上传部署包
```bash
# 上传到服务器
scp cpq-complete-system-20250825_154455.tar.gz root@your-server:/root/

# 解压
cd /root
tar -xzf cpq-complete-system-20250825_154455.tar.gz
```

### 2. 部署前端
```bash
# 备份现有前端（可选）
mv /www/wwwroot/cpq /www/wwwroot/cpq.backup

# 部署新前端
mkdir -p /www/wwwroot/cpq
cp -r apps/web/dist/* /www/wwwroot/cpq/
```

### 3. 部署后端
```bash
# 备份现有后端（可选）
mv /www/wwwroot/cpq-api /www/wwwroot/cpq-api.backup

# 部署新后端
cp -r apps/api /www/wwwroot/cpq-api

# 设置权限
chown -R www:www /www/wwwroot/cpq-api/
```

### 4. 配置环境
```bash
cd /www/wwwroot/cpq-api

# 复制环境配置
cp .env.template .env.production

# 编辑生产配置
vim .env.production
```

**重要配置项**:
```bash
# 数据库配置
DATABASE_URL=mysql+pymysql://cpq_user:your_password@localhost/cpq_system

# JWT配置
JWT_SECRET_KEY=your_super_secret_jwt_key_here

# CORS配置（已配置好）
CORS_ORIGINS=http://cpq.100yse.com,http://localhost:5173

# 可选：AI功能配置
OPENAI_API_KEY=your_openai_key
ZHIPUAI_API_KEY=your_zhipuai_key
```

### 5. 安装Python依赖
```bash
cd /www/wwwroot/cpq-api

# 安装基础依赖
pip install -r requirements.txt

# 可选：安装AI功能依赖
chmod +x install_ai_dependencies.sh
./install_ai_dependencies.sh
```

### 6. 初始化数据库
```bash
cd /www/wwwroot/cpq-api

# 初始化数据库和示例数据
python scripts/init_db.py
```

### 7. 配置Nginx
```nginx
# 前端配置 (cpq.100yse.com)
location /api/ {
    proxy_pass http://cpqh.100yse.com/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### 8. 启动服务
```bash
# 使用Gunicorn启动（推荐）
cd /www/wwwroot/cpq-api
gunicorn -c gunicorn.conf.py app:app

# 或在宝塔面板中重启Python项目
```

## 🔍 功能验证

### 登录测试
访问: `http://cpq.100yse.com/login`

**演示账户**:
- **管理员**: admin / password123
- **销售员**: sales / password123  
- **工程师**: engineer / password123
- **经理**: manager / password123

### 功能检查清单
- [ ] 用户登录正常
- [ ] 创建报价不报错
- [ ] 产品管理功能正常
- [ ] 报价管理功能正常
- [ ] AI功能可用（如已安装AI依赖）

## 🛠️ 故障排除

### 常见问题

**1. 前端页面空白**
- 检查Nginx配置是否正确
- 确认静态文件路径正确

**2. 登录失败**
- 检查后端服务是否启动
- 验证CORS配置
- 检查数据库连接

**3. 创建报价报错**
- 确认使用最新版本部署包
- 检查JWT配置
- 验证用户权限

**4. AI功能不可用**
- 运行AI依赖安装脚本
- 配置API密钥
- 检查系统依赖

### 日志查看
```bash
# 查看应用日志
tail -f /www/wwwroot/cpq-api/logs/app.log

# 查看Nginx日志
tail -f /www/logs/nginx/cpq.100yse.com.log
```

## 📞 技术支持

如遇到问题，请提供：
1. 具体错误信息
2. 浏览器控制台截图
3. 服务器日志片段
4. 系统环境信息

---

**🎉 部署完成后，您将拥有一个功能完整、无错误的CPQ配置报价系统！**