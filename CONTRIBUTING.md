# 贡献指南 / Contributing Guide

[中文](#贡献指南) | [English](#contributing-guide)

---

## 贡献指南

感谢您对CPQ系统项目的兴趣！我们欢迎所有形式的贡献。

### 🚀 快速开始

1. **Fork 项目**
2. **克隆到本地**
```bash
git clone https://github.com/your-username/cpq-system.git
cd cpq-system
```

3. **设置开发环境**
```bash
# 后端设置
cd apps/api
pip install -r requirements.txt
python scripts/init_db.py

# 前端设置
cd ../web
npm install
```

4. **创建功能分支**
```bash
git checkout -b feature/amazing-feature
```

### 📋 贡献类型

#### 🐛 Bug 修复
- 在Issues中报告bug
- 提供详细的重现步骤
- 包含系统环境信息
- 提交修复的Pull Request

#### ✨ 新功能
- 先创建Issue讨论功能需求
- 确保功能符合项目方向
- 编写相应的测试用例
- 更新相关文档

#### 📚 文档改进
- 修正错别字和语法错误
- 改进API文档说明
- 添加使用示例
- 翻译文档内容

#### 🔧 代码重构
- 提高代码质量
- 性能优化
- 代码风格统一
- 技术债务清理

### 💻 开发规范

#### 代码风格
**前端 (Vue/TypeScript)**:
- 使用 Vue 3 Composition API
- 遵循TypeScript严格模式
- 使用ESLint和Prettier
- 组件命名使用PascalCase

**后端 (Python/Flask)**:
- 遵循PEP 8代码风格
- 使用类型注解
- 函数命名使用snake_case
- 类命名使用PascalCase

#### 提交信息规范
使用约定式提交格式：
```
<类型>(<范围>): <描述>

[可选的正文]

[可选的脚注]
```

**类型标识**:
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具变动

**示例**:
```bash
feat(quotes): 添加多产品报价支持
fix(auth): 修复JWT认证中间件问题
docs(api): 更新API文档示例
```

#### 分支命名规范
- `feature/功能名称` - 新功能开发
- `fix/问题描述` - Bug修复
- `docs/文档更新` - 文档相关
- `refactor/重构描述` - 代码重构

### 🧪 测试要求

#### 前端测试
```bash
cd apps/web
npm run test        # 单元测试
npm run e2e         # 端到端测试
npm run type-check  # 类型检查
npm run lint        # 代码检查
```

#### 后端测试
```bash
cd apps/api
pytest tests/       # 运行测试
python -m coverage run -m pytest  # 覆盖率测试
```

#### 测试覆盖率要求
- 单元测试覆盖率 ≥ 80%
- 集成测试覆盖核心业务流程
- E2E测试覆盖主要用户场景

### 📝 Pull Request 流程

1. **确保代码质量**
   - 所有测试通过
   - 代码风格符合规范
   - 无TypeScript类型错误

2. **提交前检查**
```bash
# 前端检查
cd apps/web
npm run lint
npm run type-check
npm run test

# 后端检查
cd apps/api
python -m flake8 src/
pytest tests/
```

3. **创建Pull Request**
   - 使用清晰的标题和描述
   - 关联相关的Issue
   - 包含变更截图（如有UI变更）
   - 添加测试说明

4. **代码审查**
   - 响应审查意见
   - 进行必要的修改
   - 保持讨论专业和友好

### 🔍 Issue 报告

#### Bug 报告模板
```markdown
**Bug 描述**
简洁清晰的bug描述

**重现步骤**
1. 进入页面 '...'
2. 点击 '....'
3. 输入 '....'
4. 查看错误

**预期行为**
描述您期望发生的情况

**实际行为**
描述实际发生的情况

**环境信息**
- OS: [例如 macOS 12.0]
- 浏览器: [例如 Chrome 91]
- Node.js版本: [例如 18.0.0]
- Python版本: [例如 3.9.0]

**附加信息**
添加截图或其他有助于说明问题的信息
```

#### 功能请求模板
```markdown
**功能描述**
清晰描述您希望添加的功能

**问题背景**
描述这个功能要解决什么问题

**解决方案**
描述您希望的解决方案

**替代方案**
描述您考虑过的其他解决方案

**附加信息**
添加任何其他相关信息
```

---

## Contributing Guide (English)

Thank you for your interest in contributing to the CPQ System project! We welcome all forms of contributions.

### 🚀 Getting Started

1. **Fork the project**
2. **Clone locally**
```bash
git clone https://github.com/your-username/cpq-system.git
cd cpq-system
```

3. **Set up development environment**
```bash
# Backend setup
cd apps/api
pip install -r requirements.txt
python scripts/init_db.py

# Frontend setup
cd ../web
npm install
```

4. **Create feature branch**
```bash
git checkout -b feature/amazing-feature
```

### 📋 Types of Contributions

#### 🐛 Bug Fixes
- Report bugs in Issues
- Provide detailed reproduction steps
- Include system environment info
- Submit fixing Pull Request

#### ✨ New Features
- Create Issue to discuss feature requirements first
- Ensure feature aligns with project direction
- Write corresponding test cases
- Update relevant documentation

#### 📚 Documentation
- Fix typos and grammar errors
- Improve API documentation
- Add usage examples
- Translate documentation

#### 🔧 Refactoring
- Improve code quality
- Performance optimization
- Code style consistency
- Technical debt cleanup

### 💻 Development Standards

#### Code Style
**Frontend (Vue/TypeScript)**:
- Use Vue 3 Composition API
- Follow TypeScript strict mode
- Use ESLint and Prettier
- Component naming with PascalCase

**Backend (Python/Flask)**:
- Follow PEP 8 code style
- Use type annotations
- Function naming with snake_case
- Class naming with PascalCase

#### Commit Message Convention
Use conventional commit format:
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Type identifiers**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation update
- `style`: Code formatting
- `refactor`: Code refactoring
- `test`: Test related
- `chore`: Build process or auxiliary tools

**Examples**:
```bash
feat(quotes): add multi-product quote support
fix(auth): resolve JWT authentication middleware issue
docs(api): update API documentation examples
```

### 🧪 Testing Requirements

#### Frontend Testing
```bash
cd apps/web
npm run test        # Unit tests
npm run e2e         # End-to-end tests
npm run type-check  # Type checking
npm run lint        # Code linting
```

#### Backend Testing
```bash
cd apps/api
pytest tests/       # Run tests
python -m coverage run -m pytest  # Coverage testing
```

#### Coverage Requirements
- Unit test coverage ≥ 80%
- Integration tests cover core business flows
- E2E tests cover main user scenarios

### 📝 Pull Request Process

1. **Ensure code quality**
   - All tests pass
   - Code style compliant
   - No TypeScript type errors

2. **Pre-commit checks**
```bash
# Frontend checks
cd apps/web
npm run lint
npm run type-check
npm run test

# Backend checks
cd apps/api
python -m flake8 src/
pytest tests/
```

3. **Create Pull Request**
   - Use clear title and description
   - Link related Issues
   - Include screenshots for UI changes
   - Add testing instructions

4. **Code Review**
   - Respond to review comments
   - Make necessary changes
   - Keep discussions professional and friendly

### 📞 Contact

- **GitHub Issues**: https://github.com/lsaac1208/cpq-system/issues
- **Project Maintainer**: lsaac1208
- **Documentation**: Check the docs directory

---

## 🙏 致谢 / Acknowledgments

感谢所有为CPQ系统做出贡献的开发者和用户！

Thanks to all developers and users who contribute to the CPQ System!