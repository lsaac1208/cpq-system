#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门测试二进制垃圾数据检测和过滤效果
验证.doc文件解析产生的乱码是否能被正确识别和过滤
"""
import requests
import json
import os
import logging
import sys

# 添加项目路径到Python路径
sys.path.insert(0, '/Users/wang/Documents/MyCode/beta/BMad/cpq/apps/api')

from src.services.ai_analyzer import DataQualityValidator
from src.services.document_processor import DocumentProcessor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_binary_garbage_detection():
    """测试二进制垃圾数据检测功能"""
    logger.info("🛡️ 测试二进制垃圾数据检测功能...")
    
    # 创建数据质量验证器
    validator = DataQualityValidator()
    
    # 🚮 用户反馈的具体问题规格（应该被识别为垃圾数据）
    problem_specs = [
        'ToC509006008',     # 异常长的ToC变体
        'ToC509006048',     # 异常长的ToC变体
        '3.2 D',            # 数字+字母无意义组合
        '5.2.14 I-t',       # 数字+字母无意义组合
        'D',                # 单独字母
        'I',                # 单独字母
        'RS',               # 单独字母
        '/λspec_table中提取', # 格式标记泄漏
        '潗摲楍',           # .doc解析乱码汉字
        '㸳㠴㔷',           # 十六进制乱码
        '屜屝屬',           # Word结构字符
        '▉▊▋',             # OLE图形字符
    ]
    
    # ✅ 有效的技术规格（应该被保留）
    valid_specs = [
        '测试电压',         # 正常中文技术参数
        '测试电流',         # 正常中文技术参数
        '精度等级',         # 正常中文技术参数
        '工作频率',         # 正常中文技术参数
        '防护等级',         # 正常中文技术参数
        '通信接口',         # 正常中文技术参数
        '外形尺寸',         # 正常中文技术参数
        '重量',            # 正常中文技术参数
        'Test Voltage',    # 英文技术参数
        'Operating Temperature', # 英文技术参数
        'A703',            # 产品型号
    ]
    
    logger.info(f"📊 测试用例：{len(problem_specs)} 个问题规格，{len(valid_specs)} 个有效规格")
    
    # 测试问题规格的检测效果
    detected_garbage = 0
    missed_garbage = []
    
    logger.info(f"\n🚮 测试问题规格检测（应该被过滤）:")
    for spec in problem_specs:
        is_garbage = validator._is_binary_garbage(spec)
        if is_garbage:
            detected_garbage += 1
            logger.info(f"  ✅ 正确检测垃圾: '{spec}'")
        else:
            missed_garbage.append(spec)
            logger.error(f"  ❌ 漏检垃圾: '{spec}'")
    
    # 测试有效规格的保护效果
    falsely_detected = 0
    false_positives = []
    
    logger.info(f"\n✅ 测试有效规格保护（应该被保留）:")
    for spec in valid_specs:
        is_garbage = validator._is_binary_garbage(spec)
        if not is_garbage:
            logger.info(f"  ✅ 正确保留: '{spec}'")
        else:
            falsely_detected += 1
            false_positives.append(spec)
            logger.error(f"  ❌ 误删有效规格: '{spec}'")
    
    # 统计结果
    logger.info(f"\n📊 检测效果统计:")
    logger.info(f"  问题规格检测率: {detected_garbage}/{len(problem_specs)} ({detected_garbage/len(problem_specs)*100:.1f}%)")
    logger.info(f"  有效规格保护率: {len(valid_specs)-falsely_detected}/{len(valid_specs)} ({(len(valid_specs)-falsely_detected)/len(valid_specs)*100:.1f}%)")
    
    if missed_garbage:
        logger.error(f"  漏检问题规格: {missed_garbage}")
    if false_positives:
        logger.error(f"  误删有效规格: {false_positives}")
    
    # 总体评估
    total_correct = detected_garbage + (len(valid_specs) - falsely_detected)
    total_tests = len(problem_specs) + len(valid_specs)
    accuracy = total_correct / total_tests * 100
    
    logger.info(f"\n🎯 总体准确率: {total_correct}/{total_tests} ({accuracy:.1f}%)")
    
    if accuracy >= 95:
        logger.info("🎉 二进制垃圾检测效果优秀！")
        return True
    elif accuracy >= 85:
        logger.warning("⚠️ 二进制垃圾检测效果良好，但仍有改进空间")
        return True
    else:
        logger.error("❌ 二进制垃圾检测效果不佳，需要进一步优化")
        return False

def test_doc_preprocessing():
    """测试.doc文件预处理效果"""
    logger.info("📄 测试.doc文件预处理效果...")
    
    processor = DocumentProcessor()
    
    # 创建模拟的.doc解析后的垃圾内容
    corrupted_doc_content = """
A703三相继电保护测试仪

产品信息:
产品名称: A703三相继电保护测试仪
ToC509006008潗摲楍牣
3.2 D
5.2.14 I-t
D
I
/λspec_table中提取
潗摲楍牣獯景煅慵楴湯
㸳㠴㔷㤸㜹㈰㐱㠲
屜屝屬屭屨屪屢屣
▉▊▋▌▍▎▏█

技术规格:
测试电压                       0-240V AC
测试电流                       0-60A AC  
精度等级                       0.2级
工作频率                       50Hz
防护等级                       IP54
通信接口                       RS232/RS485
外形尺寸                       480×350×220mm
重量                           约15kg
"""
    
    logger.info("📄 原始内容包含:")
    lines = corrupted_doc_content.strip().split('\n')
    garbage_lines = 0
    valid_lines = 0
    
    for line in lines:
        line = line.strip()
        if line:
            if processor._is_obvious_garbage_line(line):
                garbage_lines += 1
                logger.info(f"  🚮 垃圾行: '{line}'")
            else:
                valid_lines += 1
                logger.info(f"  ✅ 有效行: '{line}'")
    
    # 测试清理效果
    cleaned_content = processor._clean_extracted_text(corrupted_doc_content)
    
    logger.info(f"\n🧹 清理后内容:")
    logger.info(f"  原始行数: {len(lines)}")
    logger.info(f"  垃圾行数: {garbage_lines}")
    logger.info(f"  有效行数: {valid_lines}")
    logger.info(f"  清理后长度: {len(cleaned_content)} 字符")
    
    # 检查清理后是否还包含垃圾内容
    remaining_garbage = []
    problem_patterns = ['ToC509006008', '3.2 D', '5.2.14 I-t', 'D', 'I', '潗摲楍', '㸳㠴㔷', '屜屝屬', '▉▊▋']
    
    for pattern in problem_patterns:
        if pattern in cleaned_content:
            remaining_garbage.append(pattern)
    
    if remaining_garbage:
        logger.error(f"❌ 清理后仍包含垃圾内容: {remaining_garbage}")
        return False
    else:
        logger.info("✅ 清理效果完美，所有垃圾内容已移除")
        return True

def test_live_api_with_enhanced_filtering():
    """测试增强过滤后的实际API效果"""
    logger.info("🔗 测试增强过滤后的实际API...")
    
    # 获取认证
    login_data = {"username": "admin", "password": "admin123"}
    login_response = requests.post("http://127.0.0.1:5000/api/v1/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        logger.error(f"❌ 登录失败: {login_response.status_code}")
        return False
    
    token = login_response.json().get('data', {}).get('tokens', {}).get('access_token')
    if not token:
        logger.error("❌ 无法获取认证token")
        return False
    
    logger.info("✅ 认证成功")
    
    # 创建包含二进制垃圾数据的测试文档
    test_content_with_garbage = """
A703三相继电保护测试仪

产品信息:
产品名称: A703三相继电保护测试仪
产品型号: A703
制造商: 海山电气设备有限公司

技术规格:
ToC509006008           潗摲楍牣獯景煅慵楴湯
ToC509006048           㸳㠴㔷㤸㜹㈰㐱㠲
3.2 D                  屜屝屬屭屨屪屢屣
5.2.14 I-t             ▉▊▋▌▍▎▏█
D                      单独字母D
I                      单独字母I
/λspec_table中提取      格式标记泄漏

测试电压               0-240V AC
测试电流               0-60A AC
精度等级               0.2级
工作频率               50Hz
防护等级               IP54
通信接口               RS232/RS485
外形尺寸               480×350×220mm
重量                   约15kg
工作温度               -10℃~+50℃
相对湿度               ≤90%（25℃）
"""
    
    # 写入临时文件
    temp_file_path = "/tmp/test_binary_garbage_enhanced.txt"
    with open(temp_file_path, 'w', encoding='utf-8') as f:
        f.write(test_content_with_garbage)
    
    try:
        # 发送API请求
        with open(temp_file_path, 'rb') as f:
            files = {'document': ('test_binary_garbage_enhanced.txt', f, 'text/plain')}
            headers = {'Authorization': f'Bearer {token}'}
            
            logger.info("📤 发送包含二进制垃圾数据的测试文档...")
            response = requests.post(
                "http://127.0.0.1:5000/api/v1/ai-analysis/analyze-document",
                files=files,
                headers=headers,
                timeout=180
            )
            
            logger.info(f"📥 API响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                specs = result.get('extracted_data', {}).get('specifications', {})
                validation_report = result.get('validation_report', {})
                
                logger.info(f"✅ API分析成功")
                logger.info(f"📊 返回的技术规格数量: {len(specs)}")
                logger.info(f"📋 验证报告: 原始={validation_report.get('original_specs_count', 'N/A')}, "
                          f"过滤噪声={validation_report.get('noise_removed_count', 'N/A')}, "
                          f"过滤无效={validation_report.get('invalid_removed_count', 'N/A')}")
                
                # 检查是否成功过滤了所有问题规格
                problem_specs = [
                    'ToC509006008', 'ToC509006048', '3.2 D', '5.2.14 I-t', 
                    'D', 'I', '/λspec_table中提取', '潗摲楍牣獯景煅慵楴湯',
                    '㸳㠴㔷㤸㜹㈰㐱㠲', '屜屝屬屭屨屪屢屣', '▉▊▋▌▍▎▏█'
                ]
                
                found_problems = []
                valid_specs_found = []
                
                logger.info(f"\n🔍 API返回的所有规格:")
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
                        valid_specs_found.append(spec_name)
                
                logger.info(f"\n🎯 二进制垃圾过滤效果分析:")
                logger.info(f"  预期过滤的垃圾规格: {len(problem_specs)} 项")
                logger.info(f"  API中发现垃圾规格: {len(found_problems)} 项")
                logger.info(f"  成功保留有效规格: {len(valid_specs_found)} 项")
                
                if found_problems:
                    logger.error(f"\n❌ 仍存在的垃圾规格:")
                    for problem in found_problems:
                        logger.error(f"    - {problem}")
                    logger.error(f"\n💡 结论: 二进制垃圾过滤器需要进一步优化")
                    return False
                else:
                    logger.info(f"\n✅ 过滤效果完美:")
                    logger.info(f"    - 所有二进制垃圾数据已被过滤")
                    logger.info(f"    - 保留了 {len(valid_specs_found)} 项有效规格")
                    logger.info(f"\n🎉 结论: 二进制垃圾过滤优化成功！")
                    return True
                    
            else:
                logger.error(f"❌ API分析失败: {response.status_code}")
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
    logger.info("🚀 开始二进制垃圾数据检测测试...")
    
    # 测试1: 直接检测功能
    logger.info("\n" + "="*60)
    logger.info("测试1: 二进制垃圾数据检测算法")
    logger.info("="*60)
    detection_success = test_binary_garbage_detection()
    
    # 测试2: 文档预处理
    logger.info("\n" + "="*60)
    logger.info("测试2: .doc文件预处理效果")
    logger.info("="*60)
    preprocessing_success = test_doc_preprocessing()
    
    # 测试3: 实际API效果
    logger.info("\n" + "="*60)
    logger.info("测试3: 增强过滤的实际API效果")
    logger.info("="*60)
    api_success = test_live_api_with_enhanced_filtering()
    
    # 最终结论
    logger.info("\n" + "="*60)
    logger.info("最终测试结果")
    logger.info("="*60)
    
    if detection_success and preprocessing_success and api_success:
        logger.info("🎉 所有测试通过！二进制垃圾数据问题已完全解决！")
        logger.info("✅ 系统现在可以正确处理.doc文件，过滤所有垃圾数据")
    elif detection_success and preprocessing_success:
        logger.warning("⚠️ 检测和预处理功能正常，但API可能需要重启才能生效")
        logger.info("💡 建议：重启Flask服务器，然后重新测试")
    else:
        logger.error("❌ 测试发现问题，需要进一步调试和优化")