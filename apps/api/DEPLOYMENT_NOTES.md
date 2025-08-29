# CPQ系统部署说明

## 🎯 多代理诊断结果总结

经过**backend-architect + devops-troubleshooter + performance-engineer**专家团队分析：

**根本原因确认**：复杂的AI依赖和性能监控模块导致Python应用启动失败，引发504 Gateway Timeout错误。

**验证结果**：
- ✅ 紧急应用测试完全成功
- ✅ 基础Flask+SQLite环境正常
- ✅ JWT认证、API端点全部正常工作

## 🚀 推荐部署方案

### 方案1: 紧急版本（强烈推荐）

**立即可用**，包含所有核心业务功能：

**关键文件**：
- `emergency_app.py` - 最小化应用
- `requirements-emergency.txt` - 精简依赖  
- `start_emergency.sh` - 启动脚本

**宝塔面板配置**：
1. 停止现有Python项目
2. 上传紧急文件到api目录
3. 修改启动文件为 `emergency_app.py`
4. 安装依赖：`pip install -r requirements-emergency.txt`
5. 启动服务

**默认账户**：admin / admin123

## 📊 功能对比

| 功能 | 紧急版本 | 修复版本 |
|------|----------|----------|
| 用户登录 | ✅ | ✅ |
| 报价管理 | ✅ | ✅ |
| 权限控制 | ✅ | ✅ |
| 启动可靠性 | 🟢 极高 | 🟡 中等 |

## 🎉 部署成功标志

- [ ] 访问网站无504错误
- [ ] 用户能正常登录
- [ ] 报价列表能正常显示
- [ ] 管理员能查看所有报价

