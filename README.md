# CPQ系统 / CPQ System

[中文](#中文说明) | [English](#english-description)

---

## 中文说明

### 📋 项目概述

CPQ系统是一个专业的配置-定价-报价（Configure, Price, Quote）管理平台，为企业提供完整的产品配置、智能定价和报价管理解决方案。

### ✨ 核心功能

#### 🎯 产品管理
- **产品配置器**：灵活的产品属性配置系统
- **产品画廊**：支持多图片管理和展示
- **批量导入**：支持Excel批量导入产品数据
- **产品搜索**：全文搜索和智能筛选

#### 💰 报价管理
- **智能报价**：基于产品配置自动计算价格
- **多产品报价**：支持单一报价包含多个产品
- **报价模板**：可定制的报价单模板
- **PDF导出**：专业的报价单PDF生成

#### 🤖 AI智能分析
- **文档智能解析**：AI自动解析产品文档和技术规格
- **智能推荐**：基于历史数据的产品和价格推荐
- **批量分析**：支持批量文档处理和分析
- **质量评估**：AI驱动的数据质量评估

#### 📊 业务分析
- **仪表盘**：实时业务数据可视化
- **销售统计**：详细的销售数据分析
- **性能监控**：系统性能实时监控
- **用户行为分析**：用户操作行为跟踪

### 🏗️ 技术架构

#### 后端技术栈
- **Flask**：Python Web框架
- **SQLAlchemy**：数据库ORM
- **Flask-JWT-Extended**：JWT认证
- **SQLite**：轻量级数据库
- **OpenAI API**：AI智能分析
- **psutil**：系统性能监控

#### 前端技术栈
- **Vue 3**：现代化前端框架
- **TypeScript**：类型安全的JavaScript
- **Element Plus**：企业级UI组件库
- **Vite**：快速的前端构建工具
- **Pinia**：状态管理
- **Vue Router**：路由管理

### 🚀 快速开始

#### 系统要求
- Node.js >= 18.0.0
- Python >= 3.8
- npm >= 9.0.0

#### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/lsaac1208/cpq-system.git
cd cpq-system
```

2. **后端设置**
```bash
cd apps/api
pip install -r requirements.txt
python scripts/init_db.py  # 初始化数据库
python app.py              # 启动后端服务 (端口 5000)
```

3. **前端设置**
```bash
cd apps/web
npm install
npm run dev                # 启动前端服务 (端口 5173)
```

4. **访问系统**
- 前端地址：http://localhost:5173
- 后端API：http://localhost:5000
- 默认账号：admin / admin123

### 📁 项目结构

```
cpq/
├── apps/
│   ├── api/                    # 后端服务
│   │   ├── src/
│   │   │   ├── models/         # 数据模型
│   │   │   ├── routes/         # API路由
│   │   │   ├── services/       # 业务逻辑
│   │   │   ├── middleware/     # 中间件
│   │   │   └── utils/          # 工具函数
│   │   ├── scripts/            # 脚本文件
│   │   └── tests/              # 测试用例
│   └── web/                    # 前端应用
│       ├── src/
│       │   ├── views/          # 页面组件
│       │   ├── components/     # 公共组件
│       │   ├── api/            # API接口
│       │   ├── stores/         # 状态管理
│       │   ├── types/          # 类型定义
│       │   └── utils/          # 工具函数
│       └── tests/              # 测试用例
├── docs/                       # 项目文档
└── README.md                   # 项目说明
```

### 🔧 开发指南

#### 后端开发
```bash
# 开发模式启动
cd apps/api
export FLASK_ENV=development
python app.py

# 数据库迁移
python migrate.py

# 运行测试
pytest tests/
```

#### 前端开发
```bash
# 开发模式启动
cd apps/web
npm run dev

# 类型检查
npm run type-check

# 代码检查
npm run lint

# 运行测试
npm run test

# 端到端测试
npm run e2e
```

### 📈 版本信息

- **当前版本**：v1.2.0
- **发布日期**：2025-08-31
- **主要更新**：
  - ✅ 修复报价管理数据显示问题
  - ✅ 优化性能监控中间件
  - ✅ 改进AI分析功能
  - ✅ 增强用户体验

### 📝 API文档

主要API端点：

- **认证相关**
  - `POST /api/v1/auth/login` - 用户登录
  - `POST /api/v1/auth/register` - 用户注册
  - `GET /api/v1/auth/me` - 获取用户信息

- **产品管理**
  - `GET /api/v1/products` - 获取产品列表
  - `POST /api/v1/products` - 创建产品
  - `PUT /api/v1/products/:id` - 更新产品
  - `DELETE /api/v1/products/:id` - 删除产品

- **报价管理**
  - `GET /api/v1/quotes` - 获取报价列表
  - `POST /api/v1/quotes` - 创建报价
  - `GET /api/v1/multi-quotes` - 获取多产品报价
  - `POST /api/v1/multi-quotes` - 创建多产品报价

- **AI分析**
  - `POST /api/v1/ai-analysis/analyze` - 文档分析
  - `GET /api/v1/ai-analysis/history` - 分析历史
  - `POST /api/v1/batch-analysis/start` - 批量分析

### 🛠️ 部署指南

#### 开发环境部署
```bash
# 启动开发环境
npm run dev:all
```

#### 生产环境部署
```bash
# 构建前端
cd apps/web
npm run build:prod

# 启动生产服务
cd apps/api
gunicorn -c gunicorn.conf.py app:app
```

### 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交变更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

### 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

### 📞 联系我们

- **项目维护者**：lsaac1208
- **邮箱**：[联系邮箱]
- **项目地址**：https://github.com/lsaac1208/cpq-system

---

## English Description

### 📋 Project Overview

CPQ System is a professional Configure-Price-Quote management platform that provides enterprises with comprehensive product configuration, intelligent pricing, and quote management solutions.

### ✨ Core Features

#### 🎯 Product Management
- **Product Configurator**: Flexible product attribute configuration system
- **Product Gallery**: Multi-image management and display support
- **Batch Import**: Excel batch import for product data
- **Product Search**: Full-text search and intelligent filtering

#### 💰 Quote Management
- **Smart Quoting**: Auto-calculate prices based on product configuration
- **Multi-Product Quotes**: Support multiple products in single quote
- **Quote Templates**: Customizable quote templates
- **PDF Export**: Professional quote PDF generation

#### 🤖 AI Intelligence
- **Document Analysis**: AI-powered parsing of product docs and specifications
- **Smart Recommendations**: Product and pricing recommendations based on historical data
- **Batch Processing**: Support for bulk document processing and analysis
- **Quality Assessment**: AI-driven data quality evaluation

#### 📊 Business Analytics
- **Dashboard**: Real-time business data visualization
- **Sales Statistics**: Detailed sales data analysis
- **Performance Monitoring**: Real-time system performance monitoring
- **User Behavior Analytics**: User operation behavior tracking

### 🏗️ Technical Architecture

#### Backend Stack
- **Flask**: Python web framework
- **SQLAlchemy**: Database ORM
- **Flask-JWT-Extended**: JWT authentication
- **SQLite**: Lightweight database
- **OpenAI API**: AI intelligent analysis
- **psutil**: System performance monitoring

#### Frontend Stack
- **Vue 3**: Modern frontend framework
- **TypeScript**: Type-safe JavaScript
- **Element Plus**: Enterprise-class UI components
- **Vite**: Fast frontend build tool
- **Pinia**: State management
- **Vue Router**: Routing management

### 🚀 Quick Start

#### System Requirements
- Node.js >= 18.0.0
- Python >= 3.8
- npm >= 9.0.0

#### Installation Steps

1. **Clone Project**
```bash
git clone https://github.com/lsaac1208/cpq-system.git
cd cpq-system
```

2. **Backend Setup**
```bash
cd apps/api
pip install -r requirements.txt
python scripts/init_db.py  # Initialize database
python app.py              # Start backend service (port 5000)
```

3. **Frontend Setup**
```bash
cd apps/web
npm install
npm run dev                # Start frontend service (port 5173)
```

4. **Access System**
- Frontend: http://localhost:5173
- Backend API: http://localhost:5000
- Default Account: admin / admin123

### 📈 Version Information

- **Current Version**: v1.2.0
- **Release Date**: 2025-08-31
- **Major Updates**:
  - ✅ Fixed quote management data display issues
  - ✅ Optimized performance monitoring middleware
  - ✅ Improved AI analysis features
  - ✅ Enhanced user experience

### 🛠️ Development Guide

#### Backend Development
```bash
# Development mode
cd apps/api
export FLASK_ENV=development
python app.py

# Database migration
python migrate.py

# Run tests
pytest tests/
```

#### Frontend Development
```bash
# Development mode
cd apps/web
npm run dev

# Type checking
npm run type-check

# Code linting
npm run lint

# Run tests
npm run test

# E2E testing
npm run e2e
```

### 🤝 Contributing

1. Fork the project
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

### 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### 📞 Contact

- **Maintainer**: lsaac1208
- **Email**: [Contact Email]
- **Project URL**: https://github.com/lsaac1208/cpq-system

---

## 🚀 Features at a Glance

| Feature | Status | Description |
|---------|--------|-------------|
| 🏢 Multi-tenant Support | ✅ | Enterprise-grade multi-tenancy |
| 🎨 Product Configuration | ✅ | Flexible product attribute system |
| 💰 Dynamic Pricing | ✅ | AI-powered pricing engine |
| 📊 Analytics Dashboard | ✅ | Real-time business insights |
| 🤖 AI Document Analysis | ✅ | Intelligent document processing |
| 📄 PDF Generation | ✅ | Professional quote documents |
| 🔍 Advanced Search | ✅ | Full-text search capabilities |
| 🌐 Internationalization | ✅ | Chinese & English support |
| 📱 Responsive Design | ✅ | Mobile-friendly interface |
| ⚡ Performance Optimization | ✅ | High-performance architecture |

## 🔧 Technical Highlights

- **Modern Architecture**: Microservices-based design
- **High Performance**: Optimized for large-scale operations
- **Security First**: JWT authentication & authorization
- **Scalable**: Designed for enterprise growth
- **AI-Powered**: Integrated machine learning capabilities
- **User-Friendly**: Intuitive interface design