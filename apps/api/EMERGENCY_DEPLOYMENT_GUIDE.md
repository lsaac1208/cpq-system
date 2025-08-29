# CPQ系统紧急修复部署指南

## 🚨 紧急情况说明

如果正常的修复版本仍然出现504错误，请使用这个紧急模式。

## 📦 紧急部署步骤

### 1. 停止当前服务
```bash
# 在宝塔面板中停止Python项目
# 或者使用命令行
pkill -f "python.*app.py"
```

### 2. 备份当前代码
```bash
cp -r /path/to/current/api /path/to/backup/api_backup_emergency_$(date +%Y%m%d_%H%M%S)
```

### 3. 部署紧急文件
将以下文件上传到服务器API目录：
- `emergency_app.py` - 最小化应用
- `requirements-emergency.txt` - 最小依赖
- `start_emergency.sh` - 启动脚本

### 4. 启动紧急服务
```bash
cd /path/to/api
chmod +x start_emergency.sh
./start_emergency.sh
```

或者手动启动：
```bash
pip install -r requirements-emergency.txt
python emergency_app.py
```

## 🔧 紧急模式功能

### 可用功能
- ✅ 用户登录 (`/api/v1/auth/login`)
- ✅ 用户信息 (`/api/v1/auth/me`) 
- ✅ 报价列表 (`/api/v1/quotes`) - 核心功能
- ✅ 健康检查 (`/health`)

### 默认管理员
- 用户名: `admin`
- 密码: `admin123`

### 移除的组件
- AI分析功能 (导致依赖问题)
- 性能监控 (psutil依赖)
- 复杂的中间件
- 不必要的路由

## 🔍 验证步骤

### 1. 检查服务状态
```bash
curl http://your-domain/health
```

应该返回:
```json
{
  "status": "healthy",
  "timestamp": "2024-...",
  "service": "CPQ API Emergency Mode"
}
```

### 2. 测试登录
```bash
curl -X POST http://your-domain/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### 3. 测试报价接口
```bash
curl -X GET http://your-domain/api/v1/quotes \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🎯 预期结果

紧急模式下，系统应该能够：
1. ✅ 正常启动，无504错误
2. ✅ 用户可以登录
3. ✅ 管理员可以查看报价列表
4. ✅ 前端可以正常连接后端

## 📞 如果紧急模式仍然失败

请检查：
1. Python版本 (建议3.8+)
2. 数据库文件权限
3. 端口占用情况
4. 服务器错误日志

## ⚡ 恢复到正常模式

紧急模式验证可用后，可以逐步恢复：
1. 确认核心功能正常
2. 逐个添加其他功能模块
3. 监控日志确保稳定性

## 🔄 回滚计划

如需回滚到修复前版本：
```bash
# 停止紧急服务
pkill -f emergency_app.py

# 恢复备份
cp -r /path/to/backup/api_backup_* /path/to/current/api

# 重启原服务
```

---

**重要**: 紧急模式只包含核心功能，其他功能需要在系统稳定后逐步添加。
