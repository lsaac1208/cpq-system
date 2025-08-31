# 更新日志 / Changelog

所有重要的项目变更都会记录在此文件中。

All notable changes to this project will be documented in this file.

---

## [v1.2.0] - 2025-08-31

### ✨ 新增功能 / Added
- 🔧 完善的性能监控中间件，支持实时系统指标收集
- 📊 优化的仪表盘数据展示，支持多数据源统一
- 🤖 AI文档分析历史记录管理
- 🛠️ 改进的错误处理和日志系统
- 📱 响应式设计优化，更好的移动端体验

### 🐛 修复问题 / Fixed
- **关键修复**: 修复报价管理列表数据显示问题
- **关键修复**: 修复axios响应数据结构处理错误
- **性能优化**: 修复性能监控中间件的系统指标收集错误
- **认证修复**: 修复JWT认证中间件用户验证逻辑
- **数据修复**: 修复多产品报价与单产品报价数据统一显示问题

### ⚡ 性能优化 / Performance
- 优化数据库查询性能
- 改进前端打包和加载速度
- 减少不必要的API调用
- 优化内存使用和垃圾回收

### 🔒 安全更新 / Security
- 增强JWT Token安全验证
- 改进用户权限验证机制
- 加强API接口安全防护
- 优化错误信息披露控制

---

## [v1.1.0] - 2025-08-25

### ✨ 新增功能 / Added
- 🏢 完整的CPQ系统基础架构
- 👥 用户认证和授权系统
- 📦 产品管理和配置功能
- 💰 报价管理和生成系统
- 🤖 AI智能文档分析功能
- 📊 业务数据仪表盘
- 🔍 产品搜索和筛选
- 📄 PDF报价单生成

### 🏗️ 技术架构 / Architecture
- **后端**: Flask + SQLAlchemy + JWT
- **前端**: Vue 3 + TypeScript + Element Plus
- **数据库**: SQLite
- **AI服务**: OpenAI API集成
- **构建工具**: Vite + Vue CLI

### 📱 用户体验 / UX/UI
- 现代化的用户界面设计
- 响应式布局适配
- 中英文双语支持
- 直观的操作流程

---

## [v1.0.0] - 2025-08-20

### 🎉 项目初始化 / Initial Release
- 📂 项目基础结构搭建
- ⚙️ 开发环境配置
- 📚 基础文档编写
- 🚀 CI/CD 流水线设置

---

## 版本规范 / Version Convention

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范：

- **主版本号 MAJOR**: 不兼容的API修改
- **次版本号 MINOR**: 向下兼容的功能性新增
- **修订号 PATCH**: 向下兼容的问题修正

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: Backward compatible functionality additions
- **PATCH**: Backward compatible bug fixes

---

## 图标说明 / Icon Legend

- ✨ 新增功能 / New Features
- 🐛 修复问题 / Bug Fixes
- ⚡ 性能优化 / Performance Improvements
- 🔒 安全更新 / Security Updates
- 🏗️ 架构变更 / Architecture Changes
- 📱 用户体验 / UX/UI Improvements
- 📚 文档更新 / Documentation
- 🔧 配置变更 / Configuration Changes
- 🎉 重大里程碑 / Major Milestones
- ⚠️ 破坏性变更 / Breaking Changes
- 🗑️ 移除功能 / Deprecated Features