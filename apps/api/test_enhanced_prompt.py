#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强版AI分析prompt的效果
验证对页面截图中显示问题的修复效果
"""
import logging
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from io import BytesIO
from werkzeug.datastructures import FileStorage
from src.services.ai_analyzer import AIAnalyzer

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_enhanced_prompt_with_sample_data():
    """测试增强版prompt对页面截图问题的修复能力"""
    
    # 创建模拟的问题文档，包含页面截图中显示的各种问题
    # 添加更多正常文本内容以通过乱码检测
    sample_text = """
    六相微机继电保护测试仪技术规格书
    
    产品名称: 六相微机继电保护测试仪
    产品型号: ToC50900608
    产品分类: 继电保护测试设备
    
    产品描述:
    这是一款专业的六相微机继电保护测试仪，用于电力系统继电保护装置的全面测试和校验。
    该设备采用先进的微机控制技术，能够同时输出六相电压和电流信号，满足各种保护装置的测试需求。
    设备具有高精度、高稳定性、操作简便等特点，是电力部门进行设备检测的理想工具。
    
    主要技术规格参数:
    TEST                    # 这是无效的测试标记，应该被过滤
    WIRE1 3RS232           # 这是OCR错误，应该修正为RS232通信接口
    RS                     # 单独的RS，应该被过滤
    ToC50900608            # 产品型号，应该保持原样
    3.2 D                  # 无效参数，D应该被过滤
    ToC509006048           # 变体型号
    5.2.14 I-t             # OCR错误，I可能是A
    分辨率                  16位
    功率消耗               75 VA
    工作频率               50 Hz
    工作温度               -10~+50℃
    存储温度               -20~+60℃  
    外形尺寸               340×280×180 mm
    重量                   5.2 kg
    通信接口               /λspec_table中提取    # 这是格式噪声，应该被过滤
    测试电压               0-220V AC
    测试电流               0-125A AC
    精度等级               0.2级
    防护等级               IP65
    电源电压               220V AC ±10%
    绝缘强度               2000V AC/1min
    
    主要功能特性:
    - 六相同时输出测试信号
    - 自动量程切换功能
    - RS232/RS485通信接口
    - 高精度数字化测量
    - 液晶显示屏操作界面
    - 存储测试结果和历史记录
    - 多种保护功能（过压、过流、短路保护）
    
    应用场景:
    - 电力系统继电保护测试
    - 变电站设备检测维护
    - 电力设备出厂试验
    - 科研院所技术研发
    """
    
    logger.info("🧪 开始测试增强版AI分析prompt...")
    
    try:
        # 创建测试文件对象
        file_data = sample_text.encode('utf-8')
        file_obj = FileStorage(
            stream=BytesIO(file_data),
            filename='继电保护测试仪技术规格.txt',
            content_type='text/plain'
        )
        
        # 初始化AI分析器
        analyzer = AIAnalyzer()
        
        # 执行分析
        logger.info("📄 执行AI文档分析...")
        result = analyzer.analyze_product_document(file_obj, user_id=1)
        
        if result.get('success'):
            logger.info("✅ AI分析成功完成")
            
            # 检查基本信息
            basic_info = result.get('extracted_data', {}).get('basic_info', {})
            logger.info(f"\n📋 产品基本信息:")
            logger.info(f"  产品名称: {basic_info.get('name', 'N/A')}")
            logger.info(f"  产品代码: {basic_info.get('code', 'N/A')}")
            logger.info(f"  产品分类: {basic_info.get('category', 'N/A')}")
            
            # 检查技术规格（重点验证问题修复）
            specs = result.get('extracted_data', {}).get('specifications', {})
            logger.info(f"\n🔧 技术规格提取结果 ({len(specs)}项):")
            
            problem_cases = {
                'TEST': '应被过滤',
                'WIRE1 3RS232': '应修正为RS232通信接口',
                'RS': '应被过滤',
                'D': '应被过滤', 
                'I': '应被过滤',
                '/λspec_table中提取': '应被过滤'
            }
            
            fixed_cases = {
                'RS232': '通信接口修正',
                'ToC50900608': '产品型号识别',
                '通信接口': '接口规格',
                '测试电压': '电压范围',
                '测试电流': '电流范围'
            }
            
            # 检查问题案例是否被正确处理
            logger.info(f"\n❌ 问题案例检查:")
            for problem_key, expected_result in problem_cases.items():
                if problem_key in specs:
                    logger.error(f"  {problem_key}: 未被过滤 ❌ ({expected_result})")
                else:
                    logger.info(f"  {problem_key}: 已正确过滤 ✅ ({expected_result})")
            
            # 检查修复案例是否正确识别
            logger.info(f"\n✅ 修复案例检查:")
            for fix_key, description in fixed_cases.items():
                found_similar = False
                for spec_name in specs.keys():
                    if fix_key.lower() in spec_name.lower() or spec_name.lower() in fix_key.lower():
                        logger.info(f"  {fix_key} → {spec_name}: 已识别 ✅ ({description})")
                        found_similar = True
                        break
                if not found_similar:
                    logger.warning(f"  {fix_key}: 未找到相关参数 ⚠️ ({description})")
            
            # 显示前10个技术规格
            logger.info(f"\n📊 提取的技术规格示例:")
            for i, (spec_name, spec_data) in enumerate(list(specs.items())[:10]):
                if isinstance(spec_data, dict):
                    value = spec_data.get('value', 'N/A')
                    unit = spec_data.get('unit', '')
                    logger.info(f"  {i+1}. {spec_name}: {value} {unit}")
                else:
                    logger.info(f"  {i+1}. {spec_name}: {spec_data}")
            
            # 检查置信度
            confidence = result.get('confidence_scores', {})
            logger.info(f"\n📈 置信度评分:")
            for key, score in confidence.items():
                logger.info(f"  {key}: {score:.3f}")
            
            # 检查数据质量
            quality_score = result.get('data_quality_score', 0)
            validation_report = result.get('validation_report', {})
            logger.info(f"\n🎯 数据质量评估:")
            logger.info(f"  质量评分: {quality_score:.2f}")
            logger.info(f"  噪声移除: {validation_report.get('noise_removed_count', 0)}项")
            logger.info(f"  无效移除: {validation_report.get('invalid_removed_count', 0)}项")
            logger.info(f"  最终规格: {validation_report.get('final_specs_count', 0)}项")
            
            # 检查调试信息
            debug_info = result.get('debug_info', {})
            pipeline = debug_info.get('processing_pipeline', [])
            logger.info(f"\n🔍 处理流程:")
            for step in pipeline:
                logger.info(f"  - {step}")
            
            # 总结测试结果
            logger.info(f"\n📊 测试总结:")
            total_problems = len(problem_cases)
            filtered_problems = sum(1 for key in problem_cases.keys() if key not in specs)
            filter_rate = filtered_problems / total_problems * 100
            
            total_fixes = len(fixed_cases)
            found_fixes = sum(1 for fix_key in fixed_cases.keys() 
                            if any(fix_key.lower() in spec_name.lower() or spec_name.lower() in fix_key.lower() 
                                  for spec_name in specs.keys()))
            fix_rate = found_fixes / total_fixes * 100
            
            logger.info(f"  问题过滤率: {filter_rate:.1f}% ({filtered_problems}/{total_problems})")
            logger.info(f"  修复识别率: {fix_rate:.1f}% ({found_fixes}/{total_fixes})")
            logger.info(f"  数据质量评分: {quality_score:.2f}")
            logger.info(f"  置信度评分: {confidence.get('overall', 0):.3f}")
            
            if filter_rate >= 80 and fix_rate >= 60 and quality_score >= 0.7:
                logger.info("🎉 测试通过！增强版prompt效果良好")
                return True
            else:
                logger.warning("⚠️ 测试部分通过，仍有改进空间")
                return False
                
        else:
            logger.error(f"❌ AI分析失败: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        logger.error(f"💥 测试过程中发生错误: {str(e)}")
        return False

def test_ocr_correction_functionality():
    """专门测试OCR智能修正功能"""
    logger.info("\n🔧 测试OCR智能修正功能...")
    
    from src.services.ai_analyzer import DataQualityValidator
    
    validator = DataQualityValidator()
    
    test_cases = [
        ("WIRE1 3RS232", "RS232通信接口"),
        ("3RS232", "RS232"),
        ("TEST", ""),  # 应该被过滤
        ("ToC50900608", "ToC50900608"),  # 产品型号保持原样
        ("5.2.14 I-t", "5.2.14 A-t"),  # OCR错误修正
    ]
    
    logger.info("OCR修正测试结果:")
    for original, expected in test_cases:
        corrected_name, corrected_data, was_corrected = validator._apply_intelligent_correction(original, original)
        
        if expected == "":  # 期望被过滤的情况
            result = "✅ 正确" if not was_corrected else "❌ 错误"
            logger.info(f"  '{original}' → 应过滤 | {result}")
        else:
            result = "✅ 正确" if corrected_name == expected else "❌ 错误"
            logger.info(f"  '{original}' → '{corrected_name}' (期望: '{expected}') | {result}")

if __name__ == "__main__":
    logger.info("🚀 开始测试增强版AI分析prompt...")
    
    # 测试OCR修正功能
    test_ocr_correction_functionality()
    
    # 测试完整的prompt效果
    success = test_enhanced_prompt_with_sample_data()
    
    if success:
        logger.info("\n🎉 所有测试通过！增强版prompt优化成功")
        sys.exit(0)
    else:
        logger.warning("\n⚠️ 测试未完全通过，需要进一步优化")
        sys.exit(1)