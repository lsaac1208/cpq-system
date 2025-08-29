#!/bin/bash
"""
Local Test Runner
运行所有测试并生成报告
"""

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录的父目录
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
WEB_DIR="$BASE_DIR/apps/web"
API_DIR="$BASE_DIR/apps/api"

echo -e "${BLUE}🧪 CPQ系统 - 完整测试套件${NC}"
echo "================================================"

# 检查依赖
echo -e "${YELLOW}📋 检查运行环境...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 未安装${NC}"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm 未安装${NC}"
    exit 1
fi

# 运行后端测试
echo -e "\n${BLUE}🐍 运行后端测试...${NC}"
cd "$API_DIR"

if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ 未找到 requirements.txt${NC}"
    exit 1
fi

echo "安装后端依赖..."
pip install -r requirements.txt
pip install -r test-requirements.txt > /dev/null 2>&1 || echo "部分测试依赖可能缺失"

echo "初始化测试数据库..."
python scripts/init_db.py

echo "执行后端单元测试..."
pytest tests/unit/ -v --tb=short --cov=src --cov-report=xml --cov-report=html --cov-report=term-missing --junitxml=junit.xml || {
    echo -e "${YELLOW}⚠️  后端测试完成，可能存在失败用例${NC}"
}

# 运行前端测试
echo -e "\n${BLUE}⚡ 运行前端测试...${NC}"
cd "$WEB_DIR"

if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ 未找到 package.json${NC}"
    exit 1
fi

echo "安装前端依赖..."
npm ci --silent

echo "执行类型检查..."
npx vue-tsc --noEmit || echo -e "${YELLOW}⚠️  类型检查发现问题${NC}"

echo "执行前端单元测试..."
npm run test -- --coverage --reporter=verbose --reporter=junit --outputFile=test-results.xml || {
    echo -e "${YELLOW}⚠️  前端测试完成，可能存在失败用例${NC}"
}

# 生成测试报告
echo -e "\n${BLUE}📊 生成测试报告...${NC}"
cd "$BASE_DIR"

python scripts/generate-test-report.py

# 检查报告是否生成成功
if [ -f "test-report.html" ]; then
    echo -e "${GREEN}✅ 测试报告生成成功: test-report.html${NC}"
    
    # 尝试在浏览器中打开报告
    if command -v open &> /dev/null; then
        echo "正在浏览器中打开测试报告..."
        open test-report.html
    elif command -v xdg-open &> /dev/null; then
        echo "正在浏览器中打开测试报告..."
        xdg-open test-report.html
    else
        echo "请手动打开 test-report.html 查看详细结果"
    fi
else
    echo -e "${RED}❌ 测试报告生成失败${NC}"
    exit 1
fi

echo -e "\n${GREEN}🎉 所有测试执行完成！${NC}"
echo "================================================"