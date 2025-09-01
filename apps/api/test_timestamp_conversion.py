#!/usr/bin/env python3
"""
测试timestamp转换逻辑，分析时间显示问题
"""
import requests
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_timestamp_conversion():
    """测试前端timestamp转换逻辑"""
    
    try:
        # 获取认证
        login_data = {"username": "admin", "password": "admin123"}
        login_response = requests.post("http://127.0.0.1:5001/api/v1/auth/login", json=login_data)
        
        if login_response.status_code != 200:
            logger.error("❌ 登录失败")
            return False
        
        token = login_response.json().get('data', {}).get('tokens', {}).get('access_token')
        headers = {'Authorization': f'Bearer {token}'}
        
        # 获取API数据
        response = requests.get(
            "http://127.0.0.1:5001/api/v1/ai-analysis/recent-results?limit=1",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('results'):
                api_result = result['results'][0]
                analysis_date = api_result.get('analysis_date')
                
                logger.info(f"\n🕐 时间戳转换分析:")
                logger.info(f"  API返回的analysis_date: '{analysis_date}'")
                
                # 模拟前端转换
                try:
                    # 前端转换：new Date(result.analysis_date).getTime()
                    js_timestamp = int(datetime.fromisoformat(analysis_date.replace('Z', '+00:00')).timestamp() * 1000)
                    logger.info(f"  转换后的timestamp: {js_timestamp}")
                    
                    # 模拟前端formatTime逻辑
                    now_timestamp = int(datetime.now().timestamp() * 1000)
                    logger.info(f"  当前时间timestamp: {now_timestamp}")
                    
                    # 计算时间差（毫秒）
                    diff_ms = now_timestamp - js_timestamp
                    logger.info(f"  时间差(毫秒): {diff_ms}")
                    
                    # 转换为小时
                    diff_hours = diff_ms / (1000 * 60 * 60)
                    logger.info(f"  时间差(小时): {diff_hours:.2f}")
                    
                    # 模拟前端显示逻辑
                    minutes = diff_ms // (1000 * 60)
                    hours = diff_ms // (1000 * 60 * 60)
                    days = diff_ms // (1000 * 60 * 60 * 24)
                    
                    logger.info(f"\n📱 前端显示逻辑模拟:")
                    logger.info(f"  分钟数: {minutes}")
                    logger.info(f"  小时数: {hours}")
                    logger.info(f"  天数: {days}")
                    
                    # 显示结果
                    if minutes < 1:
                        display_time = '刚刚'
                    elif minutes < 60:
                        display_time = f'{minutes}分钟前'
                    elif hours < 24:
                        display_time = f'{hours}小时前'
                    elif days < 7:
                        display_time = f'{days}天前'
                    else:
                        display_time = datetime.fromtimestamp(js_timestamp/1000).strftime('%Y-%m-%d')
                    
                    logger.info(f"  显示结果: '{display_time}'")
                    
                    # 检查是否异常
                    if hours >= 8:
                        logger.error(f"❌ 时间显示异常：{display_time}")
                        logger.error(f"   分析时间: {analysis_date}")
                        logger.error(f"   可能原因: 时间戳转换错误或系统时间不同步")
                        return False
                    else:
                        logger.info(f"✅ 时间显示正常: {display_time}")
                        return True
                        
                except Exception as e:
                    logger.error(f"❌ 时间转换失败: {e}")
                    return False
            else:
                logger.warning("⚠️ 没有分析结果数据")
                return False
                
        else:
            logger.error(f"❌ API调用失败: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"💥 测试错误: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_timestamp_conversion()
    if success:
        logger.info("\n🎉 时间显示正常！")
    else:
        logger.warning("\n⚠️ 时间显示有问题，需要修复")