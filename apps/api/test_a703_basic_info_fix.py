#!/usr/bin/env python3
"""
测试A703基础信息修复逻辑
"""
import requests
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_a703_basic_info_fix():
    """测试A703基础信息的修复"""
    
    # 创建A703测试文档
    doc_content = """
A703三相继电保护测试仪

产品信息:
产品名称: A703三相继电保护测试仪
产品型号: A703
制造商: 海山电气设备有限公司

技术规格表:
ToC509006008
ToC509006048
3.2 D
5.2.14 I-t
D
I
/λspec_table中提取

主要技术参数:
测试电压                       0-240V AC
测试电流                       0-60A AC  
精度等级                       0.2级
工作频率                       50Hz
防护等级                       IP54
通信接口                       RS232/RS485
外形尺寸                       480×350×220mm
重量                           约15kg
工作温度                       -10℃~+50℃
相对湿度                       ≤90%（25℃）
    """
    
    # 写入临时文件 - 使用准确的文件名触发A703逻辑
    doc_path = "/tmp/A703三相继电保护测试仪-说明书.txt"
    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write(doc_content)
    logger.info(f"📄 创建A703测试文档: {doc_path}")
    
    try:
        # 获取认证
        login_data = {"username": "admin", "password": "admin123"}
        login_response = requests.post("http://127.0.0.1:5001/api/v1/auth/login", json=login_data)
        
        if login_response.status_code != 200:
            logger.error(f"❌ 登录失败")
            return False
        
        token = login_response.json().get('data', {}).get('tokens', {}).get('access_token')
        if not token:
            logger.error("❌ 无法获取认证token")
            return False
        
        # 测试文档分析 - 重点检查basic_info修复
        with open(doc_path, 'rb') as f:
            files = {'document': (doc_path.split('/')[-1], f, 'text/plain')}
            headers = {'Authorization': f'Bearer {token}'}
            
            logger.info("📤 发送A703文档分析请求...")
            response = requests.post(
                "http://127.0.0.1:5001/api/v1/ai-analysis/analyze-document",
                files=files,
                headers=headers,
                timeout=180
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # 检查basic_info结构
                extracted_data = result.get('extracted_data', {})
                basic_info = extracted_data.get('basic_info', {})
                
                logger.info(f"\n📋 A703基础信息修复验证:")
                logger.info(f"  产品名称: '{basic_info.get('name', '')}' (应包含A703)")
                logger.info(f"  产品代码: '{basic_info.get('code', '')}' (应该是A703)")
                logger.info(f"  产品分类: '{basic_info.get('category', '')}' (应该是测量仪表)")
                
                # 验证修复效果
                issues = []
                if not basic_info.get('name') or 'A703' not in basic_info.get('name', ''):
                    issues.append("产品名称不正确或缺少A703前缀")
                if not basic_info.get('code') or basic_info.get('code') != 'A703':
                    issues.append("产品代码不正确，应该是A703")
                if not basic_info.get('category'):
                    issues.append("产品分类缺失")
                
                if issues:
                    logger.error(f"❌ 基础信息修复失败:")
                    for issue in issues:
                        logger.error(f"    - {issue}")
                    logger.error(f"💡 这就是用户看到'处理后的基础信息仍然不完整'错误的原因！")
                    return False
                else:
                    logger.info(f"\n✅ A703基础信息修复成功:")
                    logger.info(f"    - 名称: {basic_info.get('name')}")
                    logger.info(f"    - 代码: {basic_info.get('code')}")  
                    logger.info(f"    - 分类: {basic_info.get('category')}")
                    logger.info(f"\n🎉 前端验证应该能通过！")
                    return True
                    
            else:
                logger.error(f"❌ 分析失败: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"💥 测试错误: {str(e)}")
        return False
    finally:
        # 清理临时文件
        import os
        if os.path.exists(doc_path):
            os.remove(doc_path)

if __name__ == "__main__":
    success = test_a703_basic_info_fix()
    if success:
        logger.info("\n🎉 A703基础信息修复测试成功！")
    else:
        logger.warning("\n⚠️ A703基础信息修复失败，需要进一步调试")