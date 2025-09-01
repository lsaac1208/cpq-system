#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试A703三相继电保护测试仪AI分析结果
模拟用户遇到的实际问题
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

def create_a703_test_document():
    """创建A703三相继电保护测试仪的测试文档"""
    
    # 模拟真实的A703文档内容，包含用户截图中可能遇到的问题
    sample_text = """
    A703三相继电保护测试仪说明书
    
    产品名称: A703三相继电保护测试仪
    产品型号: A703
    制造商: 某某电力设备有限公司
    产品类别: 继电保护测试设备
    
    产品概述:
    A703三相继电保护测试仪是一款专业的电力系统继电保护装置测试设备。
    该设备采用先进的数字信号处理技术，能够对各种继电保护装置进行精确测试。
    适用于电力系统的变电站、发电厂等场所的继电保护装置检测和维护。
    
    主要技术参数:
    TEST                           # 格式噪声
    A703                           # 产品型号，应该保留
    WIRE1 3RS232                   # OCR错误，应修正
    测试电压                       0-240V AC
    测试电流                       0-60A AC
    RS                             # 单独RS，应过滤
    频率                           45-65Hz
    精度                           0.2级
    工作电源                       AC220V±10%
    功耗                           ≤200VA
    D                              # 单独D，应过滤
    工作温度                       -10℃~+50℃
    相对湿度                       ≤90%（25℃）
    外形尺寸                       480×350×220mm
    重量                           约15kg
    通信接口                       /λspec_table中提取
    保护等级                       IP54
    
    主要功能特点:
    - 三相电压电流输出
    - 高精度测量
    - 数字化操作界面
    - 多种测试模式
    - 数据存储和打印
    - RS232通信接口
    - 自动测试程序
    
    测试项目:
    1. 过流保护测试
    2. 过压保护测试
    3. 欠压保护测试
    4. 频率保护测试
    5. 功率方向保护测试
    6. 差动保护测试
    7. 距离保护测试
    
    安全注意事项:
    1. 使用前请仔细阅读说明书
    2. 确保设备接地良好
    3. 测试时注意人身安全
    4. 定期校准设备
    
    页面分隔符 PAGE 8           # 应该过滤的格式噪声
    HYPERLINK标记               # 应该过滤的格式噪声
    
    附录A: 技术规格详表
    项目                值          单位        说明
    电压输出范围        0-240       V           AC电压
    电流输出范围        0-60        A           AC电流
    频率范围            45-65       Hz          工频范围
    测试精度            0.2         级          精度等级
    """
    
    return sample_text

def test_a703_analysis():
    """测试A703三相继电保护测试仪的AI分析"""
    logger.info("🧪 开始测试A703三相继电保护测试仪AI分析...")
    
    try:
        # 创建测试文档
        document_content = create_a703_test_document()
        file_data = document_content.encode('utf-8')
        
        file_obj = FileStorage(
            stream=BytesIO(file_data),
            filename='A703三相继电保护测试仪-说明书.txt',
            content_type='text/plain'
        )
        
        # 执行AI分析
        analyzer = AIAnalyzer()
        logger.info("📄 开始分析A703文档...")
        
        result = analyzer.analyze_product_document(file_obj, user_id=1)
        
        if result.get('success'):
            logger.info("✅ A703文档分析成功")
            
            # 分析结果详情
            basic_info = result.get('extracted_data', {}).get('basic_info', {})
            specs = result.get('extracted_data', {}).get('specifications', {})
            validation_report = result.get('validation_report', {})
            
            logger.info(f"\\n📋 A703产品基本信息:")
            logger.info(f"  产品名称: {basic_info.get('name', 'N/A')}")
            logger.info(f"  产品代码: {basic_info.get('code', 'N/A')}")  
            logger.info(f"  产品分类: {basic_info.get('category', 'N/A')}")
            
            logger.info(f"\\n🔧 A703技术规格 ({len(specs)}项):")
            
            # 检查具体的技术参数提取情况
            expected_specs = {
                '测试电压': '0-240V AC',
                '测试电流': '0-60A AC', 
                '频率': '45-65Hz',
                '精度': '0.2级',
                '工作电源': 'AC220V±10%',
                '功耗': '≤200VA',
                '工作温度': '-10℃~+50℃',
                '外形尺寸': '480×350×220mm',
                '重量': '约15kg',
                '保护等级': 'IP54'
            }
            
            found_specs = 0
            missing_specs = []
            
            for spec_name, spec_data in specs.items():
                if isinstance(spec_data, dict):
                    value = spec_data.get('value', 'N/A')
                    unit = spec_data.get('unit', '')
                    logger.info(f"  ✅ {spec_name}: {value} {unit}")
                else:
                    logger.info(f"  ✅ {spec_name}: {spec_data}")
                
                # 检查是否包含预期规格
                for expected_name in expected_specs:
                    if expected_name in spec_name or spec_name in expected_name:
                        found_specs += 1
                        break
            
            # 检查遗漏的规格
            for expected_name, expected_value in expected_specs.items():
                found = any(expected_name in spec_name or spec_name in expected_name 
                           for spec_name in specs.keys())
                if not found:
                    missing_specs.append(f"{expected_name}: {expected_value}")
            
            logger.info(f"\\n📊 A703规格提取评估:")
            logger.info(f"  预期规格数量: {len(expected_specs)}")
            logger.info(f"  找到相关规格: {found_specs}")
            logger.info(f"  提取覆盖率: {found_specs/len(expected_specs)*100:.1f}%")
            
            if missing_specs:
                logger.warning(f"\\n⚠️ 遗漏的重要规格:")
                for missing in missing_specs:
                    logger.warning(f"  - {missing}")
            
            # 检查格式噪声过滤效果
            problem_patterns = ['TEST', 'RS', 'D', 'PAGE', 'HYPERLINK', '/λspec_table中提取', 'WIRE1 3RS232']
            noise_found = []
            
            for spec_name in specs.keys():
                for pattern in problem_patterns:
                    if pattern.lower() in spec_name.lower():
                        noise_found.append(spec_name)
                        break
            
            logger.info(f"\\n🧹 噪声过滤效果:")
            if noise_found:
                logger.warning(f"  ❌ 仍存在噪声: {noise_found}")
            else:
                logger.info(f"  ✅ 噪声已完全过滤")
            
            # 数据质量分析
            quality_score = result.get('data_quality_score', 0)
            confidence = result.get('confidence_scores', {}).get('overall', 0)
            
            logger.info(f"\\n📈 A703分析质量:")
            logger.info(f"  数据质量评分: {quality_score:.2f}")
            logger.info(f"  整体置信度: {confidence:.3f}")
            logger.info(f"  噪声移除数量: {validation_report.get('noise_removed_count', 0)}")
            logger.info(f"  无效移除数量: {validation_report.get('invalid_removed_count', 0)}")
            
            # 评估分析质量
            extraction_quality = found_specs / len(expected_specs)
            noise_filter_quality = 1.0 if not noise_found else 0.5
            overall_quality = (extraction_quality + noise_filter_quality) / 2
            
            logger.info(f"\\n🎯 A703分析总评:")
            logger.info(f"  规格提取质量: {extraction_quality:.2f}")
            logger.info(f"  噪声过滤质量: {noise_filter_quality:.2f}")
            logger.info(f"  综合分析质量: {overall_quality:.2f}")
            
            if overall_quality >= 0.8:
                logger.info(f"  ✅ 分析质量良好")
                return True
            elif overall_quality >= 0.6:
                logger.warning(f"  ⚠️ 分析质量中等，需要优化")
                return False
            else:
                logger.error(f"  ❌ 分析质量较差，需要重大改进")
                return False
                
        else:
            logger.error(f"❌ A703文档分析失败: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        logger.error(f"💥 A703测试过程中发生错误: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("🚀 开始A703三相继电保护测试仪分析测试...")
    success = test_a703_analysis()
    
    if success:
        logger.info("\\n🎉 A703分析测试通过！")
        sys.exit(0)
    else:
        logger.warning("\\n⚠️ A703分析测试发现问题，需要进一步优化")
        sys.exit(1)