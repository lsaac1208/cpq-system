#!/bin/bash

# CPQ系统AI功能依赖安装脚本
# 适用于CentOS/RHEL系统的宝塔面板环境

echo "🚀 开始安装CPQ系统AI功能依赖..."

# 获取当前脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 检查Python环境
echo "🔍 检查Python环境..."
PYTHON_CMD=""
if command -v python3.9 &> /dev/null; then
    PYTHON_CMD="python3.9"
elif command -v python3.8 &> /dev/null; then
    PYTHON_CMD="python3.8"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo "❌ 未找到Python3环境，请先安装Python3"
    exit 1
fi

echo "✅ 找到Python: $PYTHON_CMD"
$PYTHON_CMD --version

# 检查pip
echo "🔍 检查pip..."
PIP_CMD="${PYTHON_CMD} -m pip"
if ! $PIP_CMD --version &> /dev/null; then
    echo "❌ pip不可用，请先安装pip"
    exit 1
fi

echo "✅ pip可用"

# 1. 安装系统依赖
echo "📦 安装系统依赖..."

# 检查是否为CentOS/RHEL
if command -v yum &> /dev/null; then
    echo "🐧 检测到CentOS/RHEL系统，使用yum安装系统依赖..."
    
    # 安装基础工具
    sudo yum update -y
    sudo yum groupinstall -y "Development Tools"
    sudo yum install -y python3-devel libffi-devel openssl-devel
    
    # 安装图像处理依赖
    sudo yum install -y libjpeg-devel zlib-devel libtiff-devel freetype-devel lcms2-devel libwebp-devel
    
    # 安装tesseract OCR
    echo "🔍 安装Tesseract OCR..."
    sudo yum install -y epel-release
    sudo yum install -y tesseract tesseract-langpack-chi-sim tesseract-langpack-eng
    
elif command -v apt-get &> /dev/null; then
    echo "🐧 检测到Ubuntu/Debian系统，使用apt安装系统依赖..."
    
    # 更新包列表
    sudo apt-get update
    
    # 安装基础依赖
    sudo apt-get install -y python3-dev libffi-dev libssl-dev build-essential
    
    # 安装图像处理依赖
    sudo apt-get install -y libjpeg-dev zlib1g-dev libtiff-dev libfreetype6-dev liblcms2-dev libwebp-dev
    
    # 安装tesseract OCR
    echo "🔍 安装Tesseract OCR..."
    sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-eng
    
else
    echo "⚠️  未识别的Linux发行版，请手动安装以下系统依赖:"
    echo "   - 编译工具 (build-essential, gcc, python3-dev)"
    echo "   - 图像处理库 (libjpeg, zlib, libtiff, freetype, lcms2, libwebp)"
    echo "   - Tesseract OCR (tesseract-ocr, 中文语言包)"
fi

# 2. 验证tesseract安装
echo "🔍 验证Tesseract OCR安装..."
if command -v tesseract &> /dev/null; then
    echo "✅ Tesseract已安装: $(tesseract --version | head -n1)"
    echo "📝 已安装的语言包:"
    tesseract --list-langs
else
    echo "❌ Tesseract安装失败，请手动安装"
    echo "   CentOS: sudo yum install tesseract tesseract-langpack-chi-sim"
    echo "   Ubuntu: sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim"
fi

# 3. 升级pip
echo "📦 升级pip..."
$PIP_CMD install --upgrade pip

# 4. 安装AI依赖包
echo "🤖 安装AI功能Python依赖..."

# 首先安装基础依赖，避免编译错误
echo "🔧 安装基础依赖..."
$PIP_CMD install wheel setuptools

# 安装数值计算库
echo "🔢 安装数值计算库..."
$PIP_CMD install numpy==1.24.3

# 安装AI功能依赖
echo "📚 安装AI功能依赖包..."
$PIP_CMD install -r "$SCRIPT_DIR/requirements-ai.txt"

# 5. 验证关键包安装
echo "🔍 验证关键包安装..."
declare -a packages=("PyPDF2" "docx" "openpyxl" "PIL" "pytesseract" "chardet" "openai" "numpy" "pandas")

for package in "${packages[@]}"; do
    if $PYTHON_CMD -c "import $package" 2>/dev/null; then
        echo "✅ $package - 安装成功"
    else
        echo "❌ $package - 安装失败"
    fi
done

# 6. 测试OCR功能
echo "🧪 测试OCR功能..."
$PYTHON_CMD -c "
try:
    import pytesseract
    from PIL import Image
    print('✅ OCR功能可用')
    print('🔧 Tesseract路径:', pytesseract.pytesseract.tesseract_cmd)
except Exception as e:
    print('❌ OCR功能测试失败:', e)
"

# 7. 创建环境配置
echo "⚙️  创建AI环境配置..."
cat > "$SCRIPT_DIR/.env.ai" << EOF
# AI功能环境配置
AI_FEATURES_ENABLED=True
TESSERACT_CMD=$(which tesseract || echo "/usr/bin/tesseract")
OCR_LANGUAGES=chi_sim,eng

# OpenAI配置 (需要手动设置API密钥)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo

# 智谱AI配置 (需要手动设置API密钥)
ZHIPUAI_API_KEY=your_zhipuai_api_key_here
EOF

echo "📄 AI配置文件已创建: $SCRIPT_DIR/.env.ai"

# 8. 生成安装报告
echo "📊 生成安装报告..."
REPORT_FILE="$SCRIPT_DIR/ai_installation_report.txt"
cat > "$REPORT_FILE" << EOF
CPQ系统AI功能依赖安装报告
生成时间: $(date)
系统信息: $(uname -a)
Python版本: $($PYTHON_CMD --version)
pip版本: $($PIP_CMD --version)

已安装的Python包:
$($PIP_CMD list | grep -E "(PyPDF2|docx|openpyxl|Pillow|pytesseract|chardet|openai|numpy|pandas|scikit-learn)")

系统工具:
Tesseract: $(which tesseract || echo "未找到")
Tesseract版本: $(tesseract --version 2>/dev/null | head -n1 || echo "无法获取版本")

下一步操作:
1. 在.env.production文件中设置AI相关的API密钥
2. 重启CPQ系统后端服务
3. 在前端测试AI文档分析功能
EOF

echo "📄 安装报告已保存到: $REPORT_FILE"

# 9. 完成
echo ""
echo "🎉 AI功能依赖安装完成！"
echo ""
echo "⚠️  重要提醒:"
echo "1. 请在 .env.production 文件中配置API密钥:"
echo "   - OPENAI_API_KEY=你的OpenAI密钥"
echo "   - ZHIPUAI_API_KEY=你的智谱AI密钥"
echo ""
echo "2. 重启后端服务:"
echo "   sudo systemctl restart cpq-api"
echo "   # 或在宝塔面板中重启Python项目"
echo ""
echo "3. 如遇到权限问题，可能需要:"
echo "   sudo chown -R www:www /www/wwwroot/cpq-api/"
echo ""
echo "4. 检查安装报告: $REPORT_FILE"
echo ""
echo "✅ 安装完成，现在可以测试AI功能了！"