#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据质量优化系统测试脚本
测试文档处理、噪声过滤、AI分析和质量验证的完整流程
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app import create_app
from src.services.document_processor import DocumentProcessor
from src.services.ai_analyzer import AIAnalyzer
from src.models.ai_analysis import AIAnalysisRecord
from src.models.base import db
import logging
import json

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_document_content_cleaner():
    """测试文档内容清理器"""
    logger.info("🧪 测试1：文档内容清理器...")
    
    processor = DocumentProcessor()
    cleaner = processor.content_cleaner
    
    # 测试噪声内容
    test_content = """
    产品技术规格：
    电压: 220V
    PAGE 7
    功率: 1000W
    A A AB X B
    频率: 50Hz
    Ca a a a b
    HYPERLINK "http://example.com"
    额定电流: 4.5A
    h 9 HYPERLINK HYPE
    绝缘等级: IP65
    第 8 页
    """
    
    result = cleaner.clean_document_content(test_content)
    cleaned_content = result['cleaned_content']
    
    logger.info(f"原始内容行数: {len(test_content.strip().split('\\n'))}")
    logger.info(f"清理后行数: {len(cleaned_content.strip().split('\\n'))}")
    logger.info(f"移除的噪声行数: {result.get('total_noise_lines', 0)}")
    logger.info(f"清理后内容预览:\\n{cleaned_content}")
    
    # 验证噪声是否被移除
    noise_patterns = ["PAGE 7", "A A AB X B", "Ca a a a b", "HYPERLINK", "h 9 HYPERLINK", "第 8 页"]
    remaining_noise = [pattern for pattern in noise_patterns if pattern in cleaned_content]
    
    if remaining_noise:
        logger.error(f"❌ 仍存在噪声: {remaining_noise}")
        return False
    else:
        logger.info("✅ 所有噪声已成功移除")
        return True

def test_ai_analysis_with_quality_validation():
    """测试AI分析和质量验证"""
    logger.info("🧪 测试2：AI分析和质量验证...")
    
    app = create_app()
    with app.app_context():
        try:
            analyzer = AIAnalyzer()
            
            # 模拟包含噪声的文档内容
            test_content = """
            设备名称: 电机控制器
            电压: AC 380V
            PAGE 15
            功率: 15kW
            A X C B D
            频率: 50/60Hz
            HYPERLINK测试
            防护等级: IP54
            Ca a b c d
            工作温度: -20℃~+60℃
            """
            
            # 创建模拟文件对象
            from werkzeug.datastructures import FileStorage
            from io import BytesIO
            
            test_file = FileStorage(
                stream=BytesIO(test_content.encode('utf-8')),
                filename='测试文档.txt',
                content_type='text/plain'
            )
            
            # 执行AI分析（包含质量验证）
            result = analyzer.analyze_product_document(test_file, user_id=1)
            
            logger.info("📊 分析结果：")
            logger.info(f"- 原始结果键: {list(result.keys())}")
            logger.info(f"- 置信度: {result.get('confidence', 'N/A')}")
            logger.info(f"- 数据质量评分: {result.get('data_quality_score', 'N/A')}")
            logger.info(f"- 提取的规格数量: {len(result.get('technical_specs', []))}")
            
            # 如果有产品记录，检查里面的规格
            if 'product' in result and 'specifications' in result['product']:
                specs_from_product = result['product']['specifications']
                logger.info(f"- 产品记录中的规格数量: {len(specs_from_product)}")
                logger.info(f"- 前5个规格预览: {specs_from_product[:5] if specs_from_product else '无'}")
            
            # 检查质量验证报告
            logger.info(f"- 质量报告存在: {'quality_validation_report' in result}")
            
            # 检查质量验证报告
            if 'quality_validation_report' in result:
                report = result['quality_validation_report']
                logger.info("📋 质量验证报告：")
                logger.info(f"- 原始规格数量: {report.get('original_specs_count', 0)}")
                logger.info(f"- 噪声移除数量: {report.get('noise_removed_count', 0)}")
                logger.info(f"- 无效数据移除数量: {report.get('invalid_removed_count', 0)}")
                logger.info(f"- 最终有效规格数量: {report.get('final_specs_count', 0)}")
                
                if report.get('quality_issues'):
                    logger.info(f"- 发现的质量问题: {report['quality_issues']}")
                
                # 验证噪声是否被检测和移除
                if report.get('noise_removed_count', 0) > 0:
                    logger.info("✅ 噪声检测和移除功能正常")
                else:
                    logger.warning("⚠️  未检测到噪声移除")
            
            # 检查提取的技术规格
            specs = result.get('technical_specs', [])
            if specs:
                logger.info("🔧 提取的技术规格:")
                for spec in specs[:5]:  # 显示前5个
                    logger.info(f"  - {spec.get('parameter', 'N/A')}: {spec.get('value', 'N/A')}")
                
                # 验证是否包含有效规格且不包含噪声
                valid_specs = [s for s in specs if s.get('parameter') not in ['PAGE 15', 'A X C B D', 'Ca a b c d']]
                if len(valid_specs) == len(specs):
                    logger.info("✅ 技术规格提取质量良好，无噪声数据")
                    return True
                else:
                    logger.error(f"❌ 发现噪声数据在技术规格中，有效: {len(valid_specs)}, 总数: {len(specs)}")
                    return False
            else:
                logger.error("❌ 未提取到任何技术规格")
                return False
                
        except Exception as e:
            logger.error(f"❌ AI分析测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

def test_database_quality_fields():
    """测试数据库质量字段"""
    logger.info("🧪 测试3：数据库质量字段存储...")
    
    app = create_app()
    with app.app_context():
        try:
            # 查询最新的分析记录
            latest_record = AIAnalysisRecord.query.order_by(AIAnalysisRecord.created_at.desc()).first()
            
            if latest_record:
                logger.info("📝 最新分析记录质量字段：")
                logger.info(f"- 数据质量评分: {latest_record.data_quality_score}")
                logger.info(f"- 噪声移除数量: {latest_record.noise_removed_count}")
                logger.info(f"- 无效数据移除数量: {latest_record.invalid_removed_count}")
                logger.info(f"- 最终有效规格数量: {latest_record.final_specs_count}")
                
                if latest_record.quality_validation_report:
                    logger.info("- 质量验证报告已存储")
                    
                logger.info("✅ 数据库质量字段存储正常")
                return True
            else:
                logger.warning("⚠️  数据库中没有分析记录")
                return False
                
        except Exception as e:
            logger.error(f"❌ 数据库质量字段测试失败: {e}")
            return False

def main():
    """运行所有测试"""
    logger.info("🚀 开始数据质量优化系统测试...")
    
    tests = [
        ("文档内容清理器", test_document_content_cleaner),
        ("AI分析和质量验证", test_ai_analysis_with_quality_validation),
        ("数据库质量字段", test_database_quality_fields)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            logger.info(f"\\n{'='*50}")
            if test_func():
                logger.info(f"✅ {test_name} - 通过")
                passed += 1
            else:
                logger.error(f"❌ {test_name} - 失败")
                failed += 1
        except Exception as e:
            logger.error(f"❌ {test_name} - 异常: {e}")
            failed += 1
    
    logger.info(f"\\n{'='*50}")
    logger.info(f"📊 测试结果: 通过 {passed}/{len(tests)}, 失败 {failed}")
    
    if failed == 0:
        logger.info("🎉 所有测试通过！数据质量优化系统运行正常")
        return True
    else:
        logger.error(f"😞 有 {failed} 个测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)