#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试真实世界中用户遇到的技术规格抓取问题
基于用户截图中显示的实际问题
"""
import logging
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from io import BytesIO
from werkzeug.datastructures import FileStorage
from src.services.ai_analyzer import AIAnalyzer, DataQualityValidator

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_real_world_problematic_specs():
    """测试真实世界中的问题规格"""
    logger.info("🔍 测试真实世界问题规格过滤...")
    
    validator = DataQualityValidator()
    
    # 模拟用户截图中显示的问题规格
    problematic_specs = {
        # 用户截图中显示的问题规格
        'ToC509006008': {'value': '', 'unit': '', 'description': ''},  # 产品型号变体错误
        'ToC509006048': {'value': '', 'unit': '', 'description': ''},  # 产品型号变体错误  
        '3.2 D': {'value': '', 'unit': '', 'description': ''},         # 数字字母组合噪声
        '5.2.14 I-t': {'value': '', 'unit': '', 'description': ''},   # 数字字母组合噪声
        'D': {'value': '', 'unit': '', 'description': ''},             # 单独字母
        'I': {'value': '', 'unit': '', 'description': ''},             # 单独字母
        '/λspec_table中提取': {'value': '', 'unit': '', 'description': ''},  # 格式标记
        
        # 应该保留的有效技术规格
        '测试电压': {'value': '0-240V', 'unit': 'V', 'description': '输出电压范围'},
        '测试电流': {'value': '0-60A', 'unit': 'A', 'description': '输出电流范围'},
        '精度等级': {'value': '0.2级', 'unit': '', 'description': '测量精度'},
        '工作频率': {'value': '50Hz', 'unit': 'Hz', 'description': '工作频率'},
        '通信接口': {'value': 'RS232', 'unit': '', 'description': '通信方式'},
        '防护等级': {'value': 'IP54', 'unit': '', 'description': '外壳防护'},
        '外形尺寸': {'value': '480×350×220', 'unit': 'mm', 'description': '设备尺寸'},
        '产品型号': {'value': 'A703', 'unit': '', 'description': '产品型号'},  # 有值的型号应保留
    }
    
    # 执行数据清洁
    cleaned_specs, validation_report = validator._clean_specifications(problematic_specs)
    
    logger.info(f"📊 真实问题过滤测试结果:")
    logger.info(f"  原始规格数量: {validation_report['original_specs_count']}")
    logger.info(f"  过滤的问题规格: {validation_report['noise_removed_count'] + validation_report['invalid_removed_count']}")
    logger.info(f"  最终保留规格: {validation_report['final_specs_count']}")
    
    logger.info(f"\\n✅ 保留的有效规格:")
    for spec_name, spec_data in cleaned_specs.items():
        if isinstance(spec_data, dict):
            value = spec_data.get('value', 'N/A')
            logger.info(f"  - {spec_name}: {value}")
        else:
            logger.info(f"  - {spec_name}: {spec_data}")
    
    logger.info(f"\\n❌ 过滤的问题规格:")
    for removed in validation_report['removed_specs']:
        logger.info(f"  - {removed['name']}: {removed['reason']}")
    
    # 验证是否正确过滤了用户截图中的问题
    problem_specs = {'ToC509006008', 'ToC509006048', '3.2 D', '5.2.14 I-t', 'D', 'I', '/λspec_table中提取'}
    correctly_filtered = problem_specs - set(cleaned_specs.keys())
    
    filter_accuracy = len(correctly_filtered) / len(problem_specs) * 100
    
    logger.info(f"\\n📈 真实问题过滤准确率:")
    logger.info(f"  目标过滤规格: {len(problem_specs)}项")
    logger.info(f"  成功过滤规格: {len(correctly_filtered)}项")
    logger.info(f"  过滤准确率: {filter_accuracy:.1f}%")
    
    if correctly_filtered != problem_specs:
        missed = problem_specs - correctly_filtered
        logger.warning(f"  ⚠️ 未能过滤的问题规格: {missed}")
    
    return filter_accuracy >= 95

def test_enhanced_prompt_integration():
    """测试增强版prompt的完整集成效果"""
    logger.info("\\n🚀 测试增强版prompt完整集成...")
    
    # 创建包含所有已知问题的测试文档
    test_document = """
    A703三相继电保护测试仪产品说明书
    
    产品信息:
    产品名称: A703三相继电保护测试仪
    产品型号: A703
    制造商: 海山电气设备有限公司
    产品类别: 继电保护测试设备
    
    技术规格:
    ToC509006008           # 错误的产品型号变体，应过滤
    ToC509006048           # 错误的产品型号变体，应过滤
    3.2 D                  # 数字字母噪声，应过滤
    5.2.14 I-t             # 数字字母噪声，应过滤
    D                      # 单独字母，应过滤
    I                      # 单独字母，应过滤
    /λspec_table中提取      # 格式标记，应过滤
    测试电压               0-240V AC
    测试电流               0-60A AC
    精度等级               0.2级
    工作频率               50Hz
    防护等级               IP54
    通信接口               RS232/RS485
    外形尺寸               480×350×220mm
    重量                   约15kg
    工作温度               -10℃~+50℃
    
    附录A: 技术规格详表    # 文档结构，应过滤
    """
    
    try:
        file_data = test_document.encode('utf-8')
        file_obj = FileStorage(
            stream=BytesIO(file_data),
            filename='A703测试文档.txt',
            content_type='text/plain'
        )
        
        analyzer = AIAnalyzer()
        result = analyzer.analyze_product_document(file_obj, user_id=1)
        
        if result.get('success'):
            specs = result.get('extracted_data', {}).get('specifications', {})
            validation_report = result.get('validation_report', {})
            
            logger.info(f"\\n📊 完整集成测试结果:")
            logger.info(f"  最终技术规格数量: {len(specs)}")
            logger.info(f"  噪声过滤数量: {validation_report.get('noise_removed_count', 0)}")
            logger.info(f"  无效过滤数量: {validation_report.get('invalid_removed_count', 0)}")
            
            # 检查是否还包含问题规格
            problem_specs = ['ToC509006008', 'ToC509006048', '3.2 D', '5.2.14 I-t', 'D', 'I', '/λspec_table中提取', '附录A']
            found_problems = []
            
            for spec_name in specs.keys():
                for problem in problem_specs:
                    if problem.lower() in spec_name.lower():
                        found_problems.append(spec_name)
                        break
            
            logger.info(f"\\n🔍 问题规格检查:")
            if found_problems:
                logger.error(f"  ❌ 仍存在问题规格: {found_problems}")
                return False
            else:
                logger.info(f"  ✅ 所有问题规格已成功过滤")
                
                logger.info(f"\\n📋 最终保留的技术规格:")
                for i, (spec_name, spec_data) in enumerate(specs.items(), 1):
                    if isinstance(spec_data, dict):
                        value = spec_data.get('value', 'N/A')
                        unit = spec_data.get('unit', '')
                        logger.info(f"  {i}. {spec_name}: {value} {unit}")
                    else:
                        logger.info(f"  {i}. {spec_name}: {spec_data}")
                
                return True
        else:
            logger.error(f"❌ 集成测试失败: {result.get('error')}")
            return False
            
    except Exception as e:
        logger.error(f"💥 集成测试错误: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("🚀 开始真实世界问题测试...")
    
    # 测试1: 直接过滤测试
    result1 = test_real_world_problematic_specs()
    
    # 测试2: 完整集成测试
    result2 = test_enhanced_prompt_integration()
    
    if result1 and result2:
        logger.info("\\n🎉 真实世界问题测试全部通过！AI分析质量显著提升")
        sys.exit(0)
    else:
        logger.warning("\\n⚠️ 真实世界问题测试发现需要进一步优化的地方")
        sys.exit(1)