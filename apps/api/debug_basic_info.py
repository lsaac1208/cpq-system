#!/usr/bin/env python3
"""
调试基础信息验证问题
"""
import requests
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_basic_info_validation():
    """调试基础信息验证逻辑"""
    
    # 获取认证
    login_data = {"username": "admin", "password": "admin123"}
    login_response = requests.post("http://127.0.0.1:5001/api/v1/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        logger.error("登录失败")
        return
    
    token = login_response.json().get('data', {}).get('tokens', {}).get('access_token')
    headers = {'Authorization': f'Bearer {token}'}
    
    # 创建问题数据来复现错误
    logger.info("🔍 测试不同的基础信息场景:")
    
    test_cases = [
        {
            "name": "完整基础信息",
            "data": {
                "basic_info": {
                    "name": "A703三相继电保护测试仪",
                    "code": "A703",
                    "category": "测量仪表"
                },
                "specifications": {}
            }
        },
        {
            "name": "缺少产品代码",
            "data": {
                "basic_info": {
                    "name": "三相继电保护测试仪",
                    "code": "",  # 空代码
                    "category": "测量仪表"
                },
                "specifications": {}
            }
        },
        {
            "name": "缺少产品名称",
            "data": {
                "basic_info": {
                    "name": "",  # 空名称
                    "code": "A703",
                    "category": "测量仪表"
                },
                "specifications": {}
            }
        },
        {
            "name": "真实A703服务器日志情况",
            "data": {
                "basic_info": {
                    "name": "三相继电保护测试仪",  # 缺少A703前缀
                    "code": "",  # 可能为空
                    "category": "测量仪表"
                },
                "specifications": {
                    "测试电压": "0-240V AC",
                    "测试电流": "0-60A AC"
                }
            }
        }
    ]
    
    for test_case in test_cases:
        logger.info(f"\n--- 测试: {test_case['name']} ---")
        
        # 模拟产品创建请求
        try:
            response = requests.post(
                "http://127.0.0.1:5001/api/v1/products",
                json=test_case['data'],
                headers=headers,
                timeout=30
            )
            
            logger.info(f"状态码: {response.status_code}")
            
            if response.status_code != 200:
                result = response.json()
                logger.error(f"❌ 验证失败: {result.get('error', 'Unknown')}")
                if 'user_friendly_message' in result:
                    logger.error(f"💬 用户友好消息: {result['user_friendly_message']}")
            else:
                logger.info("✅ 验证通过")
                
        except Exception as e:
            logger.error(f"请求错误: {e}")

if __name__ == "__main__":
    debug_basic_info_validation()