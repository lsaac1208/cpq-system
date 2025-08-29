#!/bin/bash
# 紧急启动脚本

echo "🚨 启动CPQ系统紧急模式..."

# 切换到API目录
cd "$(dirname "$0")"

# 安装最小依赖
echo "📦 安装最小依赖..."
pip install -r requirements-emergency.txt

# 启动紧急服务
echo "🚀 启动紧急服务..."
python emergency_app.py
