#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
置信度修复验证测试
验证修复后的置信度计算是否正常工作
"""

import sys
import os
sys.path.insert(0, os.getcwd())

from app import create_app
from src.services.ai_analyzer import AIAnalyzer
from werkzeug.datastructures import FileStorage
from io import BytesIO
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_confidence_fix():
    """测试置信度修复效果"""
    logger.info("🚀 开始测试置信度修复效果...")
    
    app = create_app()
    with app.app_context():
        try:
            analyzer = AIAnalyzer()
            
            # 创建测试文档 - 包含高质量技术规格
            test_content = """
            变压器综合测试仪技术规格书
            
            产品名称: 变压器综合测试仪
            产品型号: HZBB-II
            产品分类: 电力测试设备
            
            主要技术参数:
            测试电压: 0~500V
            测试电流: 0~5A
            变比范围: 1~10000
            组别测试: 0~11点钟方向
            精度等级: ±0.2%
            工作频率: 50/60Hz
            工作温度: -20℃~+60℃
            存储温度: -30℃~+70℃
            相对湿度: ≤85%RH
            海拔高度: ≤2000m
            
            产品特点:
            1. 自动化测试功能
            2. 数据存储和打印
            3. 中英文界面切换
            4. RS232通讯接口
            
            基础价格: 28000元
            """
            
            # 创建模拟文件对象
            test_file = FileStorage(
                stream=BytesIO(test_content.encode('utf-8')),
                filename='变压器测试仪规格.txt',
                content_type='text/plain'
            )
            
            logger.info("📄 开始AI分析...")
            result = analyzer.analyze_product_document(test_file, user_id=1)
            
            logger.info("=" * 60)
            logger.info("📊 分析结果:")
            logger.info(f"✅ 分析成功: {result.get('success', False)}")
            logger.info(f"📈 总体置信度: {result.get('confidence', 'N/A')}")
            logger.info(f"🎯 数据质量评分: {result.get('data_quality_score', 'N/A')}")
            
            # 检查详细置信度分数
            if 'confidence_details' in result:
                details = result['confidence_details']
                logger.info("\n📋 详细置信度分析:")
                for key, value in details.items():
                    if isinstance(value, (int, float)):
                        logger.info(f"  {key}: {value:.3f}")
                    else:
                        logger.info(f"  {key}: {value}")
            
            # 检查技术规格
            if 'technical_specs' in result:
                specs = result['technical_specs']
                logger.info(f"\n🔧 技术规格数量: {len(specs) if specs else 0}")
                if specs:
                    logger.info("前5个技术规格:")
                    for i, spec in enumerate(specs[:5]):
                        logger.info(f"  {i+1}. {spec.get('parameter', 'N/A')}: {spec.get('value', 'N/A')}")
            
            # 检查产品规格 
            if 'product' in result and 'specifications' in result['product']:
                product_specs = result['product']['specifications']
                logger.info(f"\n📦 产品规格数量: {len(product_specs) if product_specs else 0}")
            
            # 预期结果验证
            overall_confidence = result.get('confidence', 0)
            logger.info("=" * 60)
            
            if overall_confidence >= 0.7:
                logger.info("✅ 测试成功！置信度已修复到正常水平 (≥70%)")
                return True
            elif overall_confidence >= 0.5:
                logger.warning(f"⚠️  测试部分成功！置信度为 {overall_confidence:.1%}，有所改善但仍需优化")
                return False
            else:
                logger.error(f"❌ 测试失败！置信度仍然偏低: {overall_confidence:.1%}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 测试过程中发生异常: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_confidence_fix()
    
    if success:
        logger.info("🎉 置信度修复验证通过！")
        sys.exit(0)
    else:
        logger.error("😞 置信度修复验证失败，需要进一步检查")
        sys.exit(1)