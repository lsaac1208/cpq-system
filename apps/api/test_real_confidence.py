#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实际置信度效果验证
测试实际的用户文档分析效果
"""

import sys
import os
sys.path.insert(0, os.getcwd())

from app import create_app
from src.services.ai_analyzer import AIAnalyzer
from werkzeug.datastructures import FileStorage
from io import BytesIO
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_realistic_document():
    """测试真实场景的文档分析"""
    logger.info("🚀 测试修复后的置信度效果...")
    
    app = create_app()
    with app.app_context():
        try:
            analyzer = AIAnalyzer()
            
            # 模拟真实的电力设备技术文档
            realistic_content = """
            智能配电开关技术参数表
            
            产品信息:
            设备名称: 智能负荷开关
            产品型号: FZN21-12
            设备分类: 高压开关设备
            制造商: 某电气公司
            
            主要技术参数:
            额定电压: 12kV
            额定电流: 630A  
            额定短路开断电流: 20kA
            额定峰值耐受电流: 50kA
            机械寿命: 10000次
            三相不同期: ≤2ms
            灭弧介质: SF6气体
            操作机构: 弹簧储能
            防护等级: IP67
            抗地震等级: 8度
            海拔高度: ≤1000m
            
            控制特性:
            远程控制: 支持
            就地控制: 支持  
            通讯协议: IEC 61850
            监测功能: 电流、开关状态
            故障指示: LED显示
            
            环境条件:
            工作温度: -40℃~+40℃
            存储温度: -40℃~+60℃
            相对湿度: ≤95%
            污染等级: IV级
            
            价格信息:
            设备单价: 65000元
            质保期限: 3年
            """
            
            # 创建文件对象
            test_file = FileStorage(
                stream=BytesIO(realistic_content.encode('utf-8')),
                filename='智能开关技术规格.txt',
                content_type='text/plain'
            )
            
            logger.info("📄 开始分析真实技术文档...")
            start_time = time.time()
            result = analyzer.analyze_product_document(test_file, user_id=1)
            analysis_time = time.time() - start_time
            
            logger.info("=" * 80)
            logger.info("📊 实际分析结果:")
            logger.info("=" * 80)
            
            # 核心指标
            confidence = result.get('confidence', 0)
            confidence_level = result.get('confidence_level', 'unknown')
            data_quality = result.get('data_quality_score', 0)
            
            logger.info(f"🎯 总体置信度: {confidence:.1%} ({confidence_level})")
            logger.info(f"📊 数据质量评分: {data_quality:.1%}")
            logger.info(f"⏱️  分析耗时: {analysis_time:.1f}秒")
            
            # 详细置信度分析
            if 'confidence_details' in result:
                details = result['confidence_details']
                logger.info(f"\n📋 详细置信度分析:")
                logger.info(f"  基础信息置信度: {details.get('basic_info', 0):.1%}")
                logger.info(f"  技术规格置信度: {details.get('specifications', 0):.1%}")
                logger.info(f"  产品特性置信度: {details.get('features', 0):.1%}")
                logger.info(f"  完整性评分: {details.get('completeness', 0):.1%}")
                logger.info(f"  质量评分: {details.get('quality', 0):.1%}")
                logger.info(f"  格式评分: {details.get('format', 0):.1%}")
            
            # 提取的技术规格
            if 'extracted_data' in result and 'specifications' in result['extracted_data']:
                specs = result['extracted_data']['specifications']
                logger.info(f"\n🔧 提取的技术规格数量: {len(specs) if specs else 0}")
                
                if specs:
                    logger.info("代表性技术规格:")
                    count = 0
                    for param, spec_data in specs.items():
                        if count >= 5:  # 只显示前5个
                            break
                        value = spec_data.get('value', 'N/A') if isinstance(spec_data, dict) else spec_data
                        unit = spec_data.get('unit', '') if isinstance(spec_data, dict) else ''
                        logger.info(f"  • {param}: {value} {unit}".strip())
                        count += 1
            
            # 成功标准验证
            logger.info("=" * 80)
            if confidence >= 0.7:
                logger.info("✅ 修复成功！置信度达到预期目标 (≥70%)")
                if confidence >= 0.8:
                    logger.info("🌟 优秀表现！置信度达到优秀水平 (≥80%)")
                return True
            else:
                logger.warning(f"⚠️  置信度仍需改进: {confidence:.1%} < 70%")
                return False
                
        except Exception as e:
            logger.error(f"❌ 测试失败: {e}")
            return False

if __name__ == "__main__":
    import time
    success = test_realistic_document()
    
    if success:
        logger.info("\n🎉 置信度优化修复验证成功！")
        logger.info("📈 技术规格置信度问题已解决")
        logger.info("🚀 系统已准备好用于生产环境")
    else:
        logger.error("\n😞 置信度仍需进一步优化")
    
    sys.exit(0 if success else 1)