#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强版prompt的核心功能
专注于测试数据质量验证和OCR修正功能
"""
import logging
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.ai_analyzer import DataQualityValidator

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_noise_detection_and_filtering():
    """测试噪声检测和过滤功能"""
    logger.info("🔍 测试噪声检测和过滤功能...")
    
    validator = DataQualityValidator()
    
    # 模拟包含各种问题的规格参数
    mock_specifications = {
        # 格式噪声 - 应该被过滤
        'TEST': {'value': '', 'unit': '', 'description': ''},
        'RS': {'value': '', 'unit': '', 'description': ''},
        'WIRE1 3RS232': {'value': '', 'unit': '', 'description': ''},
        'D': {'value': '', 'unit': '', 'description': ''},
        'PAGE 7': {'value': '', 'unit': '', 'description': ''},
        'HYPERLINK': {'value': '', 'unit': '', 'description': ''},
        'λspec_table中提取': {'value': '', 'unit': '', 'description': ''},
        
        # 有效的技术参数 - 应该保留
        '测试电压': {'value': '0-220V', 'unit': 'V', 'description': '测试电压范围'},
        '测试电流': {'value': '0-125A', 'unit': 'A', 'description': '测试电流范围'},
        '工作频率': {'value': '50Hz', 'unit': 'Hz', 'description': '工作频率'},
        '精度等级': {'value': '0.2级', 'unit': '', 'description': '测量精度'},
        '通信接口': {'value': 'RS232', 'unit': '', 'description': '通信接口'},
        '产品型号': {'value': 'ToC50900608', 'unit': '', 'description': '产品型号'},
        '外形尺寸': {'value': '340×280×180', 'unit': 'mm', 'description': '设备尺寸'},
    }
    
    # 执行验证
    validation_result = validator.validate_extracted_data({
        'basic_info': {
            'name': '六相微机继电保护测试仪',
            'code': 'ToC50900608',
            'category': '继电保护测试设备'
        },
        'specifications': mock_specifications,
        'confidence': {
            'basic_info': 0.9,
            'specifications': 0.8,
            'overall': 0.85
        }
    })
    
    cleaned_data = validation_result['cleaned_data']
    validation_report = validation_result['validation_report']
    quality_score = validation_result['data_quality_score']
    
    logger.info(f"📊 验证结果统计:")
    logger.info(f"  原始规格数量: {validation_report['original_specs_count']}")
    logger.info(f"  噪声移除数量: {validation_report['noise_removed_count']}")
    logger.info(f"  无效移除数量: {validation_report['invalid_removed_count']}")
    logger.info(f"  最终规格数量: {validation_report['final_specs_count']}")
    logger.info(f"  数据质量评分: {quality_score:.2f}")
    
    # 检查哪些参数被保留
    final_specs = cleaned_data.get('specifications', {})
    logger.info(f"\n✅ 保留的有效规格参数 ({len(final_specs)}项):")
    for spec_name, spec_data in final_specs.items():
        value = spec_data.get('value', 'N/A') if isinstance(spec_data, dict) else spec_data
        logger.info(f"  - {spec_name}: {value}")
    
    # 检查哪些参数被移除
    removed_specs = validation_report.get('removed_specs', [])
    logger.info(f"\n❌ 移除的问题参数 ({len(removed_specs)}项):")
    for removed in removed_specs:
        logger.info(f"  - {removed['name']}: {removed['reason']}")
    
    # 评估过滤效果
    expected_noise = {'TEST', 'RS', 'WIRE1 3RS232', 'D', 'PAGE 7', 'HYPERLINK', 'λspec_table中提取'}
    expected_valid = {'测试电压', '测试电流', '工作频率', '精度等级', '通信接口', '产品型号', '外形尺寸'}
    
    actual_final = set(final_specs.keys())
    
    # 计算准确率
    correctly_filtered = expected_noise - actual_final  # 应该过滤且确实过滤的
    correctly_kept = expected_valid & actual_final      # 应该保留且确实保留的
    wrongly_kept = expected_noise & actual_final        # 应该过滤但保留的
    wrongly_filtered = expected_valid - actual_final    # 应该保留但过滤的
    
    filter_accuracy = len(correctly_filtered) / len(expected_noise) * 100
    keep_accuracy = len(correctly_kept) / len(expected_valid) * 100
    
    logger.info(f"\n📈 过滤准确性评估:")
    logger.info(f"  噪声过滤准确率: {filter_accuracy:.1f}% ({len(correctly_filtered)}/{len(expected_noise)})")
    logger.info(f"  有效参数保留率: {keep_accuracy:.1f}% ({len(correctly_kept)}/{len(expected_valid)})")
    
    if wrongly_kept:
        logger.warning(f"  错误保留的噪声: {wrongly_kept}")
    if wrongly_filtered:
        logger.warning(f"  错误过滤的有效参数: {wrongly_filtered}")
    
    return filter_accuracy >= 80 and keep_accuracy >= 80

def test_ocr_intelligent_correction():
    """测试OCR智能修正功能"""
    logger.info("\n🔧 测试OCR智能修正功能...")
    
    validator = DataQualityValidator()
    
    test_cases = [
        # (原始输入, 期望输出, 描述)
        ('WIRE1 3RS232', 'RS232通信接口', '通信接口OCR错误修正'),
        ('3RS232', 'RS232', 'RS232协议识别'),
        ('TEST', 'TEST', '无效标记不修正'),
        ('ToC50900608', 'ToC50900608', '产品型号保持原样'),
        ('WIRE1', '串口1', 'WIRE标识修正'),
        ('2RS485', 'RS485', 'RS485识别修正'),
    ]
    
    logger.info("OCR修正测试结果:")
    passed_tests = 0
    
    for original, expected, description in test_cases:
        corrected_name, corrected_data, was_corrected = validator._apply_intelligent_correction(original, {'value': original})
        
        if corrected_name == expected:
            logger.info(f"  ✅ {description}: '{original}' → '{corrected_name}'")
            passed_tests += 1
        else:
            logger.warning(f"  ❌ {description}: '{original}' → '{corrected_name}' (期望: '{expected}')")
    
    accuracy = passed_tests / len(test_cases) * 100
    logger.info(f"\nOCR修正准确率: {accuracy:.1f}% ({passed_tests}/{len(test_cases)})")
    
    return accuracy >= 70

def test_technical_parameter_recognition():
    """测试技术参数识别功能"""
    logger.info("\n🔍 测试技术参数识别功能...")
    
    validator = DataQualityValidator()
    
    # 模拟各种技术参数模式
    test_params = {
        # 应该识别为有效技术参数
        '电压范围': '220V AC',
        '电流范围': '5A DC', 
        '工作温度': '-10~+50℃',
        '通信接口': 'RS232',
        '防护等级': 'IP65',
        '产品型号': 'ToC50900608',
        '精度': '±0.5%',
        '频率': '50/60Hz',
        '功率': '100W',
        
        # 应该识别为无效/噪声
        'TEST': '',
        'A': '',
        'D': '',
        'HYPERLINK': '',
        'page': '7',
        '': 'empty',
    }
    
    valid_count = 0
    invalid_count = 0
    
    for param_name, param_value in test_params.items():
        # 使用验证器的内部逻辑判断
        if not param_name or not param_name.strip():
            continue
            
        # 检查是否为格式噪声
        is_noise = any(validator.noise_patterns[i] for i in range(len(validator.noise_patterns)) 
                      if __import__('re').search(validator.noise_patterns[i], param_name, __import__('re').IGNORECASE))
        
        # 检查是否为有效技术参数
        combined_text = f"{param_name} {param_value}"
        is_valid_tech = any(__import__('re').search(pattern, combined_text, __import__('re').IGNORECASE) 
                           for pattern in validator.valid_tech_patterns)
        
        # 基本有效性检查
        if (len(param_name) > 1 and 
            (__import__('re').search(r'\d', combined_text) or  
             __import__('re').search(r'[电压流功率频温度精量]', combined_text) or  
             __import__('re').search(r'[VvAaWwHh℃℉%]', combined_text))):
            is_valid_tech = True
        
        expected_valid = param_name in ['电压范围', '电流范围', '工作温度', '通信接口', '防护等级', '产品型号', '精度', '频率', '功率']
        
        if expected_valid:
            if not is_noise and is_valid_tech:
                logger.info(f"  ✅ 正确识别有效参数: {param_name}")
                valid_count += 1
            else:
                logger.warning(f"  ❌ 误判有效参数为无效: {param_name}")
        else:
            if is_noise or not is_valid_tech:
                logger.info(f"  ✅ 正确识别无效参数: {param_name}")
                invalid_count += 1
            else:
                logger.warning(f"  ❌ 误判无效参数为有效: {param_name}")
    
    total_expected_valid = 9
    total_expected_invalid = 6
    
    valid_accuracy = valid_count / total_expected_valid * 100
    invalid_accuracy = invalid_count / total_expected_invalid * 100
    overall_accuracy = (valid_count + invalid_count) / (total_expected_valid + total_expected_invalid) * 100
    
    logger.info(f"\n📊 技术参数识别准确率:")
    logger.info(f"  有效参数识别率: {valid_accuracy:.1f}% ({valid_count}/{total_expected_valid})")
    logger.info(f"  无效参数识别率: {invalid_accuracy:.1f}% ({invalid_count}/{total_expected_invalid})")
    logger.info(f"  总体识别准确率: {overall_accuracy:.1f}%")
    
    return overall_accuracy >= 75

def main():
    """主测试函数"""
    logger.info("🚀 开始测试增强版prompt的核心功能...")
    
    test_results = []
    
    # 测试1: 噪声检测和过滤
    logger.info("\n" + "="*60)
    result1 = test_noise_detection_and_filtering()
    test_results.append(('噪声检测和过滤', result1))
    
    # 测试2: OCR智能修正
    logger.info("\n" + "="*60)
    result2 = test_ocr_intelligent_correction()
    test_results.append(('OCR智能修正', result2))
    
    # 测试3: 技术参数识别
    logger.info("\n" + "="*60)
    result3 = test_technical_parameter_recognition()
    test_results.append(('技术参数识别', result3))
    
    # 总结测试结果
    logger.info("\n" + "="*60)
    logger.info("📊 测试结果总结:")
    
    passed_tests = 0
    for test_name, passed in test_results:
        status = "✅ 通过" if passed else "❌ 失败"
        logger.info(f"  {test_name}: {status}")
        if passed:
            passed_tests += 1
    
    overall_success_rate = passed_tests / len(test_results) * 100
    logger.info(f"\n总体成功率: {overall_success_rate:.1f}% ({passed_tests}/{len(test_results)})")
    
    if overall_success_rate >= 80:
        logger.info("\n🎉 核心功能测试通过！增强版prompt优化成功")
        return True
    else:
        logger.warning("\n⚠️ 部分核心功能需要进一步优化")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)