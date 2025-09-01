#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试经过认证的API是否正确使用了优化后的代码
"""
import requests
import json
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_auth_token():
    """获取认证token"""
    api_base = "http://127.0.0.1:5000"
    
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(f"{api_base}/api/v1/auth/login", json=login_data)
        
        if response.status_code == 200:
            token = response.json().get('access_token')
            logger.info("✅ 成功获取认证token")
            return token
        else:
            logger.error(f"❌ 登录失败: {response.status_code}")
            logger.error(f"错误详情: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"💥 登录过程错误: {str(e)}")
        return None

def test_authenticated_api():
    """测试带认证的API"""
    logger.info("🔗 测试带认证的API服务...")
    
    # 获取认证token
    token = get_auth_token()
    if not token:
        return False
    
    api_base = "http://127.0.0.1:5000"
    headers = {'Authorization': f'Bearer {token}'}
    
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
    temp_file_path = "/tmp/test_a703_authenticated.txt"
    with open(temp_file_path, 'w', encoding='utf-8') as f:
        f.write(test_document_content)
    
    try:
        # 准备文件上传
        with open(temp_file_path, 'rb') as f:
            files = {'document': ('test_a703_authenticated.txt', f, 'text/plain')}
            
            logger.info("📤 发送带认证的AI分析请求...")
            try:
                response = requests.post(
                    f"{api_base}/api/v1/ai-analysis/analyze-document",
                    files=files,
                    headers=headers,
                    timeout=180  # 3分钟超时
                )
                
                logger.info(f"📥 API响应状态码: {response.status_code}")
                
            except requests.exceptions.Timeout:
                logger.error("⏰ API请求超时")
                return False
            except Exception as e:
                logger.error(f"💥 API请求异常: {str(e)}")
                return False
            
            if response.status_code == 200:
                result = response.json()
                logger.info("✅ API分析成功")
                
                # 检查返回的规格参数中是否还有问题数据
                specs = result.get('extracted_data', {}).get('specifications', {})
                logger.info(f"📊 返回的技术规格数量: {len(specs)}")
                
                # 记录验证报告信息
                validation_report = result.get('validation_report', {})
                logger.info(f"📋 验证报告: 原始={validation_report.get('original_specs_count', 'N/A')}, "
                           f"过滤噪声={validation_report.get('noise_removed_count', 'N/A')}, "
                           f"过滤无效={validation_report.get('invalid_removed_count', 'N/A')}")
                
                # 检查是否包含用户截图中的问题规格
                problem_specs = ['ToC509006008', 'ToC509006048', '3.2 D', '5.2.14 I-t', 'D', 'I', '/λspec_table中提取']
                found_problems = []
                
                logger.info(f"\n🔍 API返回的所有规格:")
                for spec_name, spec_data in specs.items():
                    if isinstance(spec_data, dict):
                        value = spec_data.get('value', 'N/A')
                        unit = spec_data.get('unit', '')
                        logger.info(f"  📋 {spec_name}: {value} {unit}")
                    else:
                        logger.info(f"  📋 {spec_name}: {spec_data}")
                    
                    # 检查是否是问题规格
                    for problem in problem_specs:
                        if problem.lower() in spec_name.lower() or spec_name.lower() in problem.lower():
                            found_problems.append(spec_name)
                            break
                
                logger.info(f"\n🎯 问题规格检查结果:")
                if found_problems:
                    logger.error(f"❌ API仍返回问题规格: {found_problems}")
                    logger.error("💡 这表明生产环境的过滤器没有生效")
                    return False
                else:
                    logger.info("✅ API成功过滤了所有问题规格")
                    logger.info("🎉 优化后的代码在生产环境中正常工作")
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
    result = test_authenticated_api()
    if result:
        logger.info("🎉 生产环境API过滤效果正常！优化成功！")
    else:
        logger.warning("⚠️ 生产环境API仍存在问题，需要进一步调试")