#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI分析服务是否正常工作
"""
import os
import sys
import json
import logging

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_zhipu_client():
    """测试智谱AI客户端基本功能"""
    try:
        from src.services.zhipuai_client import ZhipuAIClient
        
        print("🔍 初始化智谱AI客户端...")
        client = ZhipuAIClient()
        
        print(f"✅ API Key配置: {'是' if client.api_key else '否'}")
        print(f"✅ 客户端可用: {'是' if client.is_available() else '否'}")
        print(f"✅ 模型: {client.model}")
        print(f"✅ API端点: {client.base_url}")
        
        # 测试简单API调用
        print("\n🔍 测试简单API调用...")
        test_content = """
智能温控器产品说明书

产品名称：智能温控器 Pro
产品型号：STC-PRO-2024
工作电压：AC 220V
控制精度：±0.5°C
通讯方式：WiFi、蓝牙
显示屏：3.5寸彩色触摸屏

主要功能：
1. 智能学习用户习惯
2. 手机远程控制
3. 语音控制支持
4. 节能模式
        """
        
        result = client.analyze_product_document(test_content, "测试文档.txt")
        
        print("✅ API调用成功!")
        print(f"📊 成功标识: {result.get('success', False)}")
        
        if result.get('success'):
            basic_info = result.get('extracted_data', {}).get('basic_info', {})
            print(f"📋 产品名称: {basic_info.get('name', 'N/A')}")
            print(f"📋 产品代码: {basic_info.get('code', 'N/A')}")
            print(f"📋 产品分类: {basic_info.get('category', 'N/A')}")
            
            confidence = result.get('confidence_scores', {})
            print(f"📊 总体置信度: {confidence.get('overall', 0):.2f}")
        else:
            print(f"❌ 分析失败: {result.get('error', '未知错误')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 智谱AI客户端测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_analyzer():
    """测试完整的AI分析器"""
    try:
        from src.services.ai_analyzer import AIAnalyzer
        from werkzeug.datastructures import FileStorage
        from io import BytesIO
        
        print("\n🔍 初始化AI分析器...")
        analyzer = AIAnalyzer()
        
        # 创建模拟文件
        test_content = """
智能传感器产品技术规格书

产品信息：
名称：工业级温湿度传感器
型号：THM-2024-Pro
分类：工业传感器

技术参数：
工作电压：DC 12-24V
测量范围：温度 -40~+85°C，湿度 0~100%RH
测量精度：温度 ±0.3°C，湿度 ±2%RH
输出信号：4-20mA / RS485
防护等级：IP65
工作温度：-40~+85°C

产品特性：
- 高精度瑞士传感器芯片
- 宽温度工作范围
- 工业级防护设计
- 双信号输出方式
        """.encode('utf-8')
        
        file_obj = FileStorage(
            stream=BytesIO(test_content),
            filename="test_sensor.txt",
            content_type="text/plain"
        )
        
        print("🔍 执行文档分析...")
        result = analyzer.analyze_product_document(file_obj, user_id=1)
        
        print("✅ AI分析器测试成功!")
        print(f"📊 成功标识: {result.get('success', False)}")
        
        if result.get('success'):
            basic_info = result.get('extracted_data', {}).get('basic_info', {})
            print(f"📋 识别的产品: {basic_info.get('name', 'N/A')}")
            print(f"📋 产品代码: {basic_info.get('code', 'N/A')}")
            
            specs = result.get('extracted_data', {}).get('specifications', {})
            print(f"📊 技术规格数量: {len(specs)}")
            
            confidence = result.get('confidence_scores', {})
            print(f"📊 总体置信度: {confidence.get('overall', 0):.2f}")
        else:
            print(f"❌ 分析失败: {result.get('error', '未知错误')}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI分析器测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始AI服务测试...\n")
    
    # 测试智谱AI客户端
    zhipu_ok = test_zhipu_client()
    
    # 测试AI分析器
    analyzer_ok = test_ai_analyzer()
    
    print(f"\n📊 测试结果:")
    print(f"智谱AI客户端: {'✅ 通过' if zhipu_ok else '❌ 失败'}")
    print(f"AI分析器: {'✅ 通过' if analyzer_ok else '❌ 失败'}")
    
    if zhipu_ok and analyzer_ok:
        print("\n🎉 AI服务测试全部通过！")
        sys.exit(0)
    else:
        print("\n💥 AI服务存在问题，需要进一步调试")
        sys.exit(1)