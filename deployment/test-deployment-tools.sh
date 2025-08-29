#!/bin/bash

# =============================================================================
# CPQ系统部署工具测试脚本
# 用于验证部署脚本的功能和完整性
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️ $1${NC}"; }

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "    CPQ系统部署工具测试"
echo "=========================================="
echo

# 测试1: 检查必要文件存在
print_info "测试1: 检查部署文件完整性..."

required_files=(
    "baota-deploy-automation.sh"
    "cpq-deployment-validator.py"
    "package-preparation.sh"
    "step-by-step-deployment-guide.md"
    "DEPLOYMENT_EXECUTION_GUIDE.md"
    "deployment-commands.md"
    "FINAL_DEPLOYMENT_SUMMARY.md"
)

missing_files=0
for file in "${required_files[@]}"; do
    if [[ -f "$SCRIPT_DIR/$file" ]]; then
        print_success "$file 存在"
    else
        print_error "$file 缺失"
        ((missing_files++))
    fi
done

if [[ $missing_files -eq 0 ]]; then
    print_success "所有必要文件都存在"
else
    print_error "缺失 $missing_files 个文件"
fi

echo

# 测试2: 检查脚本执行权限
print_info "测试2: 检查脚本执行权限..."

script_files=(
    "baota-deploy-automation.sh"
    "cpq-deployment-validator.py"
    "package-preparation.sh"
    "test-deployment-tools.sh"
)

permission_errors=0
for script in "${script_files[@]}"; do
    if [[ -f "$SCRIPT_DIR/$script" ]]; then
        if [[ -x "$SCRIPT_DIR/$script" ]]; then
            print_success "$script 有执行权限"
        else
            print_warning "$script 缺少执行权限"
            chmod +x "$SCRIPT_DIR/$script"
            print_success "$script 执行权限已修复"
        fi
    fi
done

echo

# 测试3: 检查项目结构
print_info "测试3: 检查项目结构完整性..."

required_dirs=(
    "apps/api"
    "apps/web/dist"
)

structure_errors=0
for dir in "${required_dirs[@]}"; do
    if [[ -d "$PROJECT_ROOT/$dir" ]]; then
        print_success "$dir 目录存在"
    else
        print_error "$dir 目录缺失"
        ((structure_errors++))
    fi
done

# 检查关键文件
key_files=(
    "apps/api/app.py"
    "apps/api/requirements-production.txt"
    "apps/web/dist/index.html"
)

for file in "${key_files[@]}"; do
    if [[ -f "$PROJECT_ROOT/$file" ]]; then
        print_success "$file 文件存在"
    else
        print_error "$file 文件缺失"
        ((structure_errors++))
    fi
done

if [[ $structure_errors -eq 0 ]]; then
    print_success "项目结构检查通过"
else
    print_error "项目结构检查发现 $structure_errors 个问题"
fi

echo

# 测试4: 检查前端构建产物
print_info "测试4: 检查前端构建产物..."

dist_dir="$PROJECT_ROOT/apps/web/dist"
if [[ -d "$dist_dir" ]]; then
    file_count=$(find "$dist_dir" -type f | wc -l)
    dist_size=$(du -sh "$dist_dir" | cut -f1)
    
    if [[ $file_count -gt 0 ]]; then
        print_success "前端构建产物存在: $file_count 个文件, 大小: $dist_size"
        
        # 检查关键文件
        if [[ -f "$dist_dir/index.html" ]]; then
            print_success "index.html 存在"
        else
            print_error "index.html 缺失"
        fi
        
        js_files=$(find "$dist_dir" -name "*.js" | wc -l)
        css_files=$(find "$dist_dir" -name "*.css" | wc -l)
        print_info "JS文件: $js_files 个, CSS文件: $css_files 个"
    else
        print_error "前端构建产物为空"
    fi
else
    print_error "前端dist目录不存在"
fi

echo

# 测试5: 验证Python脚本语法
print_info "测试5: 验证Python脚本语法..."

if command -v python3 >/dev/null 2>&1; then
    python_scripts=(
        "cpq-deployment-validator.py"
    )
    
    for script in "${python_scripts[@]}"; do
        if [[ -f "$SCRIPT_DIR/$script" ]]; then
            if python3 -m py_compile "$SCRIPT_DIR/$script" 2>/dev/null; then
                print_success "$script 语法检查通过"
            else
                print_error "$script 语法检查失败"
            fi
        fi
    done
else
    print_warning "Python3 不可用，跳过语法检查"
fi

echo

# 测试6: 检查Bash脚本语法
print_info "测试6: 检查Bash脚本语法..."

if command -v bash >/dev/null 2>&1; then
    bash_scripts=(
        "baota-deploy-automation.sh"
        "package-preparation.sh"
    )
    
    for script in "${bash_scripts[@]}"; do
        if [[ -f "$SCRIPT_DIR/$script" ]]; then
            if bash -n "$SCRIPT_DIR/$script" 2>/dev/null; then
                print_success "$script 语法检查通过"
            else
                print_error "$script 语法检查失败"
            fi
        fi
    done
else
    print_warning "Bash 不可用，跳过语法检查"
fi

echo

# 测试7: 检查文档完整性
print_info "测试7: 检查文档完整性..."

doc_files=(
    "step-by-step-deployment-guide.md"
    "DEPLOYMENT_EXECUTION_GUIDE.md"
    "deployment-commands.md"
    "FINAL_DEPLOYMENT_SUMMARY.md"
)

doc_errors=0
for doc in "${doc_files[@]}"; do
    if [[ -f "$SCRIPT_DIR/$doc" ]]; then
        word_count=$(wc -w < "$SCRIPT_DIR/$doc")
        if [[ $word_count -gt 100 ]]; then
            print_success "$doc 内容充实 (${word_count} 词)"
        else
            print_warning "$doc 内容较少 (${word_count} 词)"
        fi
    else
        print_error "$doc 文档缺失"
        ((doc_errors++))
    fi
done

if [[ $doc_errors -eq 0 ]]; then
    print_success "所有文档都存在"
else
    print_error "$doc_errors 个文档缺失"
fi

echo

# 总结
echo "=========================================="
echo "           测试结果总结"
echo "=========================================="

total_errors=$((missing_files + structure_errors + doc_errors))

if [[ $total_errors -eq 0 ]]; then
    print_success "所有测试通过！部署工具准备就绪"
    echo
    print_info "下一步操作:"
    echo "  1. 运行部署包准备: ./package-preparation.sh"
    echo "  2. 上传到宝塔服务器"
    echo "  3. 解压并运行安装脚本"
    echo "  4. 运行验证脚本"
else
    print_error "发现 $total_errors 个问题，请修复后重新测试"
fi

echo
print_info "测试完成时间: $(date '+%Y-%m-%d %H:%M:%S')"