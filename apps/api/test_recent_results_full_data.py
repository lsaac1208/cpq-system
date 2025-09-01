#!/usr/bin/env python3
"""
详细测试recent-results API返回的数据结构，分析缺少的字段
"""
import requests
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_api_data_structure():
    """详细分析API数据结构，找出缺少的字段"""
    
    try:
        # 获取认证
        login_data = {"username": "admin", "password": "admin123"}
        login_response = requests.post("http://127.0.0.1:5001/api/v1/auth/login", json=login_data)
        
        if login_response.status_code != 200:
            logger.error("❌ 登录失败")
            return False
        
        token = login_response.json().get('data', {}).get('tokens', {}).get('access_token')
        headers = {'Authorization': f'Bearer {token}'}
        
        # 测试recent-results API
        logger.info("📤 调用recent-results API...")
        response = requests.get(
            "http://127.0.0.1:5001/api/v1/ai-analysis/recent-results?limit=1",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('results'):
                api_result = result['results'][0]
                logger.info(f"\n📊 API返回的数据字段:")
                logger.info(f"  id: {api_result.get('id')}")
                logger.info(f"  document_name: {api_result.get('document_name')}")
                logger.info(f"  analysis_date: {api_result.get('analysis_date')}")
                logger.info(f"  status: {api_result.get('status')}")
                logger.info(f"  success: {api_result.get('success')}")
                logger.info(f"  confidence: {api_result.get('confidence')}")
                logger.info(f"  product_info: {api_result.get('product_info')}")
                logger.info(f"  analysis_duration: {api_result.get('analysis_duration')}")
                logger.info(f"  created_product_id: {api_result.get('created_product_id')}")
                
                logger.info(f"\n🔍 前端需要但API缺少的字段:")
                missing_fields = []
                
                # 检查文档信息相关
                if 'file_size' not in api_result:
                    missing_fields.append("file_size - 文件大小")
                if 'file_type' not in api_result:
                    missing_fields.append("file_type - 文件类型")
                
                # 检查详细extracted_data (规格、特性、认证)
                if 'extracted_data' not in api_result:
                    missing_fields.append("extracted_data.specifications - 规格数据详情")
                    missing_fields.append("extracted_data.features - 特性数据详情")  
                    missing_fields.append("extracted_data.certificates - 认证数据详情")
                
                if missing_fields:
                    logger.error(f"❌ API缺少关键字段:")
                    for field in missing_fields:
                        logger.error(f"    - {field}")
                    
                    logger.info(f"\n💡 解决方案:")
                    logger.info(f"    1. 修改backend API返回完整数据")
                    logger.info(f"    2. 或在前端使用现有数据(product_info.specs_count)")
                    
                    return False
                else:
                    logger.info(f"✅ API数据字段完整")
                    return True
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
    success = test_api_data_structure()
    if success:
        logger.info("\n🎉 API数据结构完整！")
    else:
        logger.warning("\n⚠️ API数据结构需要改进")