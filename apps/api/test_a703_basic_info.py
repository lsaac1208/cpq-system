#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试A703文档的基础信息完整性问题
"""
import requests
import json
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_a703_basic_info():
    """测试A703文档基础信息的完整性"""
    
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
    
    # 写入临时文件
    doc_path = "/tmp/a703_test.txt"
    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write(doc_content)
    logger.info(f"📄 创建A703测试文档: {doc_path}")
    
    try:
        # 获取认证
        logger.info("🔐 获取认证token...")
        login_data = {"username": "admin", "password": "admin123"}
        login_response = requests.post("http://127.0.0.1:5001/api/v1/auth/login", json=login_data)
        
        if login_response.status_code != 200:
            logger.error(f"❌ 登录失败: {login_response.status_code}")
            return False
        
        token = login_response.json().get('data', {}).get('tokens', {}).get('access_token')
        if not token:
            logger.error("❌ 无法获取认证token")
            return False
        
        logger.info("✅ 认证成功")
        
        # 测试文档分析 - 重点检查basic_info
        with open(doc_path, 'rb') as f:
            files = {'document': (os.path.basename(doc_path), f, 'text/plain')}
            headers = {'Authorization': f'Bearer {token}'}
            
            logger.info("📤 发送A703文档分析请求...")
            response = requests.post(
                "http://127.0.0.1:5001/api/v1/ai-analysis/analyze-document",
                files=files,
                headers=headers,
                timeout=180
            )
            
            logger.info(f"📥 API响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info("✅ A703文档分析成功")
                
                # 重点检查basic_info结构
                extracted_data = result.get('extracted_data', {})
                basic_info = extracted_data.get('basic_info', {})
                
                logger.info(f"\n📋 基础信息完整性检查:")
                logger.info(f"  basic_info 结构: {type(basic_info)}")
                logger.info(f"  basic_info 内容: {json.dumps(basic_info, ensure_ascii=False, indent=2)}")
                
                # 检查必需字段
                required_fields = ['name', 'code', 'category']
                missing_fields = []
                
                for field in required_fields:
                    value = basic_info.get(field, '')
                    logger.info(f"  {field}: '{value}' (长度: {len(value) if value else 0})")
                    if not value or not value.strip():
                        missing_fields.append(field)
                
                if missing_fields:
                    logger.error(f"❌ 缺失的基础信息字段: {missing_fields}")
                    logger.error(f"💡 这就是用户看到'基础信息不完整'错误的原因！")
                    
                    # 检查AI分析结果中是否有相关信息可以用来补全
                    specs = extracted_data.get('specifications', {})
                    logger.info(f"\n🔍 从技术规格中查找可用的基础信息:")
                    for spec_name, spec_data in specs.items():
                        if '产品' in spec_name or '型号' in spec_name or '名称' in spec_name:
                            logger.info(f"  可能的基础信息: {spec_name} = {spec_data}")
                    
                    return False
                else:
                    logger.info(f"✅ 基础信息完整: 包含所有必需字段")
                    return True
                    
            else:
                logger.error(f"❌ A703文档分析失败: {response.status_code}")
                try:
                    error_detail = response.json()
                    logger.error(f"错误详情: {error_detail}")
                except:
                    logger.error(f"错误内容: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"💥 A703基础信息测试错误: {str(e)}")
        return False
    finally:
        # 清理临时文件
        if os.path.exists(doc_path):
            os.remove(doc_path)

if __name__ == "__main__":
    success = test_a703_basic_info()
    if success:
        logger.info("\n🎉 A703基础信息完整！")
    else:
        logger.warning("\n⚠️ A703基础信息不完整，需要修复AI分析逻辑")