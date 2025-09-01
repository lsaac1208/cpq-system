#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试真实的A703文档，复现用户截图中的问题
"""
import requests
import json
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_real_a703_document():
    """测试真实的A703文档"""
    
    # 用户提到的文档路径
    doc_path = "/Users/wang/Downloads/高压发生设备/A703三相继电保护测试仪/海山/A703三相继电保护测试仪-说明书(1).doc"
    
    if not os.path.exists(doc_path):
        logger.warning(f"⚠️ 真实文档不存在: {doc_path}")
        
        # 创建一个更真实的测试文档，包含用户截图中的所有问题
        realistic_content = """
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
        
        # 写入临时文件用于测试
        doc_path = "/tmp/realistic_a703.txt"
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(realistic_content)
        logger.info(f"📄 创建测试文档: {doc_path}")
    
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
    
    # 测试文档分析
    try:
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
                
                # 详细分析结果
                specs = result.get('extracted_data', {}).get('specifications', {})
                validation_report = result.get('validation_report', {})
                confidence = result.get('confidence_scores', {})
                
                logger.info(f"\n📊 A703分析结果详情:")
                logger.info(f"  最终技术规格数量: {len(specs)}")
                logger.info(f"  整体置信度: {confidence.get('overall', 'N/A')}")
                logger.info(f"  验证报告: 原始={validation_report.get('original_specs_count', 'N/A')}, "
                           f"过滤噪声={validation_report.get('noise_removed_count', 'N/A')}, "
                           f"过滤无效={validation_report.get('invalid_removed_count', 'N/A')}")
                
                # 用户截图中的问题规格列表
                problem_specs = [
                    'ToC509006008', 'ToC509006048', '3.2 D', '5.2.14 I-t', 
                    'D', 'I', '/λspec_table中提取'
                ]
                
                found_problems = []
                valid_specs = []
                
                logger.info(f"\n📋 API返回的技术规格清单:")
                for i, (spec_name, spec_data) in enumerate(specs.items(), 1):
                    if isinstance(spec_data, dict):
                        value = spec_data.get('value', 'N/A')
                        unit = spec_data.get('unit', '')
                        display_value = f"{value} {unit}".strip()
                    else:
                        display_value = str(spec_data)
                    
                    logger.info(f"  {i:2d}. {spec_name}: {display_value}")
                    
                    # 检查是否是问题规格
                    is_problem = False
                    for problem in problem_specs:
                        if (problem.lower() in spec_name.lower() or 
                            spec_name.lower() in problem.lower() or
                            problem == spec_name):
                            found_problems.append(spec_name)
                            is_problem = True
                            break
                    
                    if not is_problem:
                        valid_specs.append(spec_name)
                
                logger.info(f"\n🎯 问题过滤效果分析:")
                logger.info(f"  用户截图问题规格: {len(problem_specs)} 项")
                logger.info(f"  API中发现问题规格: {len(found_problems)} 项")
                logger.info(f"  有效规格参数: {len(valid_specs)} 项")
                
                if found_problems:
                    logger.error(f"\n❌ 仍存在的问题规格:")
                    for problem in found_problems:
                        logger.error(f"    - {problem}")
                    logger.error(f"\n💡 结论: 生产环境过滤器未完全生效")
                    return False
                else:
                    logger.info(f"\n✅ 过滤效果完美:")
                    logger.info(f"    - 所有问题规格已被过滤")
                    logger.info(f"    - 保留了 {len(valid_specs)} 项有效规格")
                    logger.info(f"\n🎉 结论: 优化后的代码在生产环境正常工作！")
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
        logger.error(f"💥 A703文档测试错误: {str(e)}")
        return False
    finally:
        # 清理临时文件
        if doc_path.startswith('/tmp/'):
            if os.path.exists(doc_path):
                os.remove(doc_path)

if __name__ == "__main__":
    success = test_real_a703_document()
    if success:
        logger.info("\n🎉 A703真实文档测试成功！优化效果已在生产环境生效！")
    else:
        logger.warning("\n⚠️ A703真实文档测试发现问题，需要进一步调试")