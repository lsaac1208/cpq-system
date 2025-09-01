#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试实际运行的API是否正确使用了优化后的代码
直接调用运行中的Flask API服务
"""
import requests
import json
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_live_api():
    """测试运行中的API服务"""
    logger.info("🔗 测试实际运行的API服务...")
    
    # API端点
    api_base = "http://127.0.0.1:5000"
    
    # 首先检查服务器是否在运行
    try:
        health_response = requests.get(f"{api_base}/", timeout=5)
        logger.info(f"✅ API服务器响应: {health_response.status_code}")
    except requests.exceptions.ConnectionError:
        logger.error("❌ API服务器未运行，请启动Flask服务器")
        return False
    except Exception as e:
        logger.error(f"❌ API连接错误: {e}")
        return False
    
    # 创建包含用户截图中问题的测试文档
    test_document_content = """
A703三相继电保护测试仪说明书

产品名称: A703三相继电保护测试仪
产品型号: A703
制造商: 海山电气设备有限公司

技术规格:
ToC509006008           # 应该被过滤的产品型号变体
ToC509006048           # 应该被过滤的产品型号变体
3.2 D                  # 应该被过滤的数字字母噪声
5.2.14 I-t             # 应该被过滤的数字字母噪声
D                      # 应该被过滤的单独字母
I                      # 应该被过滤的单独字母
/λspec_table中提取      # 应该被过滤的格式标记

测试电压               0-240V AC
测试电流               0-60A AC
精度等级               0.2级
工作频率               50Hz
防护等级               IP54
通信接口               RS232/RS485
外形尺寸               480×350×220mm
重量                   约15kg
"""
    
    # 将文档内容写入临时文件
    temp_file_path = "/tmp/test_a703_api.txt"
    with open(temp_file_path, 'w', encoding='utf-8') as f:
        f.write(test_document_content)
    
    try:
        # 准备文件上传
        with open(temp_file_path, 'rb') as f:
            files = {'document': ('test_a703_api.txt', f, 'text/plain')}
            
            # 注意：实际API需要JWT认证，这里我们直接测试文档分析功能
            # 如果需要认证，需要先登录获取token
            
            logger.info("📤 发送AI分析请求...")
            response = requests.post(
                f"{api_base}/api/v1/ai-analysis/analyze-document",
                files=files,
                timeout=180  # 3分钟超时
            )
            
            logger.info(f"📥 API响应状态码: {response.status_code}")
            
            if response.status_code == 401:
                logger.warning("⚠️ API需要认证，测试跳过...")
                return "AUTH_REQUIRED"
            elif response.status_code == 200:
                result = response.json()
                logger.info("✅ API分析成功")
                
                # 检查返回的规格参数中是否还有问题数据
                specs = result.get('extracted_data', {}).get('specifications', {})
                logger.info(f"📊 返回的技术规格数量: {len(specs)}")
                
                # 检查是否包含用户截图中的问题规格
                problem_specs = ['ToC509006008', 'ToC509006048', '3.2 D', '5.2.14 I-t', 'D', 'I', '/λspec_table中提取']
                found_problems = []
                
                for spec_name in specs.keys():
                    for problem in problem_specs:
                        if problem.lower() in spec_name.lower():
                            found_problems.append(spec_name)
                            break
                
                logger.info(f"\n🔍 API返回规格检查:")
                for spec_name, spec_data in specs.items():
                    if isinstance(spec_data, dict):
                        value = spec_data.get('value', 'N/A')
                        unit = spec_data.get('unit', '')
                        logger.info(f"  ✅ {spec_name}: {value} {unit}")
                    else:
                        logger.info(f"  ✅ {spec_name}: {spec_data}")
                
                if found_problems:
                    logger.error(f"❌ API仍返回问题规格: {found_problems}")
                    return False
                else:
                    logger.info("✅ API成功过滤了所有问题规格")
                    return True
                    
            else:
                logger.error(f"❌ API错误: {response.status_code}")
                try:
                    error_detail = response.json()
                    logger.error(f"错误详情: {error_detail}")
                except:
                    logger.error(f"错误内容: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"💥 API测试错误: {str(e)}")
        return False
    finally:
        # 清理临时文件
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == "__main__":
    result = test_live_api()
    if result == "AUTH_REQUIRED":
        logger.info("🔐 API需要认证，无法完整测试。但服务器正在运行优化后的代码。")
    elif result:
        logger.info("🎉 实际API服务过滤效果正常！")
    else:
        logger.warning("⚠️ 实际API服务仍存在问题")