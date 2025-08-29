#!/bin/bash

# 激活虚拟环境并启动API服务器
cd "$(dirname "$0")"
source venv/bin/activate
python app.py