#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
置信度性能验证测试套件
验证修复后的置信度计算在各种场景下的表现
"""

import sys
import os
sys.path.insert(0, os.getcwd())

from app import create_app
from src.services.ai_analyzer import AIAnalyzer
from src.services.confidence_scorer import ConfidenceScorer
from werkzeug.datastructures import FileStorage
from io import BytesIO
import logging
import time
import json

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfidencePerformanceTest:
    """置信度性能测试类"""
    
    def __init__(self):
        self.analyzer = AIAnalyzer()
        self.scorer = ConfidenceScorer()
        self.test_cases = []
        self.results = []
    
    def create_test_case(self, name: str, content: str, expected_confidence_range: tuple):
        """创建测试用例"""
        self.test_cases.append({
            'name': name,
            'content': content,
            'expected_range': expected_confidence_range,  # (min, max)
        })
    
    def run_all_tests(self):
        """运行所有测试用例"""
        logger.info(f"🚀 开始运行 {len(self.test_cases)} 个置信度性能测试用例...")
        
        app = create_app()
        with app.app_context():
            for i, test_case in enumerate(self.test_cases, 1):
                logger.info(f"\n{'='*60}")
                logger.info(f"📝 测试用例 {i}: {test_case['name']}")
                logger.info(f"{'='*60}")
                
                result = self._run_single_test(test_case)
                self.results.append(result)
                
                # 实时结果反馈
                status = "✅ PASS" if result['passed'] else "❌ FAIL"
                logger.info(f"{status} - 置信度: {result['confidence']:.1%} (期望: {result['expected_range'][0]:.1%}-{result['expected_range'][1]:.1%})")
        
        self._generate_summary_report()
    
    def _run_single_test(self, test_case: dict) -> dict:
        """运行单个测试用例"""
        try:
            start_time = time.time()
            
            # 创建模拟文件
            test_file = FileStorage(
                stream=BytesIO(test_case['content'].encode('utf-8')),
                filename=f"{test_case['name']}.txt",
                content_type='text/plain'
            )
            
            # 执行AI分析
            analysis_result = self.analyzer.analyze_product_document(test_file, user_id=1)
            execution_time = time.time() - start_time
            
            # 提取结果
            confidence = analysis_result.get('confidence', 0.0)
            confidence_details = analysis_result.get('confidence_details', {})
            data_quality_score = analysis_result.get('data_quality_score', 0.0)
            
            # 验证置信度范围
            min_expected, max_expected = test_case['expected_range']
            passed = min_expected <= confidence <= max_expected
            
            return {
                'name': test_case['name'],
                'passed': passed,
                'confidence': confidence,
                'confidence_level': confidence_details.get('level', 'unknown'),
                'data_quality_score': data_quality_score,
                'execution_time': execution_time,
                'expected_range': test_case['expected_range'],
                'confidence_breakdown': {
                    'completeness': confidence_details.get('completeness', 0),
                    'quality': confidence_details.get('quality', 0),
                    'format': confidence_details.get('format', 0),
                    'specifications': confidence_details.get('specifications', 0),
                    'basic_info': confidence_details.get('basic_info', 0)
                }
            }
            
        except Exception as e:
            logger.error(f"测试用例执行失败: {test_case['name']}, 错误: {e}")
            return {
                'name': test_case['name'],
                'passed': False,
                'confidence': 0.0,
                'error': str(e),
                'execution_time': 0,
                'expected_range': test_case['expected_range']
            }
    
    def _generate_summary_report(self):
        """生成测试总结报告"""
        logger.info(f"\n{'='*80}")
        logger.info(f"📊 置信度性能测试总结报告")
        logger.info(f"{'='*80}")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['passed'])
        failed_tests = total_tests - passed_tests
        
        # 总体统计
        logger.info(f"📈 总体结果:")
        logger.info(f"  总测试数: {total_tests}")
        logger.info(f"  通过: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
        logger.info(f"  失败: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
        
        # 性能统计
        execution_times = [r['execution_time'] for r in self.results if 'execution_time' in r]
        if execution_times:
            avg_time = sum(execution_times) / len(execution_times)
            logger.info(f"\n⏱️  性能统计:")
            logger.info(f"  平均执行时间: {avg_time:.2f}秒")
            logger.info(f"  最快执行时间: {min(execution_times):.2f}秒")
            logger.info(f"  最慢执行时间: {max(execution_times):.2f}秒")
        
        # 置信度分布
        confidences = [r['confidence'] for r in self.results if 'confidence' in r]
        if confidences:
            avg_confidence = sum(confidences) / len(confidences)
            logger.info(f"\n🎯 置信度分布:")
            logger.info(f"  平均置信度: {avg_confidence:.1%}")
            logger.info(f"  最高置信度: {max(confidences):.1%}")
            logger.info(f"  最低置信度: {min(confidences):.1%}")
            
            # 置信度等级分布
            levels = [r.get('confidence_level', 'unknown') for r in self.results]
            level_counts = {}
            for level in levels:
                level_counts[level] = level_counts.get(level, 0) + 1
            
            logger.info(f"  置信度等级分布:")
            for level, count in level_counts.items():
                logger.info(f"    {level}: {count}个 ({count/total_tests*100:.1f}%)")
        
        # 详细结果
        logger.info(f"\n📋 详细测试结果:")
        for result in self.results:
            status = "✅" if result['passed'] else "❌"
            confidence = result.get('confidence', 0)
            expected = result['expected_range']
            logger.info(f"  {status} {result['name']}: {confidence:.1%} (期望: {expected[0]:.1%}-{expected[1]:.1%})")
        
        return passed_tests == total_tests

def create_test_cases(tester: ConfidencePerformanceTest):
    """创建各种场景的测试用例"""
    
    # 测试用例1: 高质量技术文档 - 期望高置信度 (80%-95%)
    tester.create_test_case(
        name="高质量技术文档",
        content="""
        智能电表技术规格书
        产品名称: 三相智能电表
        产品代码: DTS866-Z
        产品分类: 电力计量设备
        
        技术参数:
        额定电压: 3×220V/380V
        额定电流: 1.5(6)A, 5(20)A, 10(40)A
        精度等级: 1.0级
        工作频率: 50Hz
        功耗: ≤2W
        工作温度: -25℃~+60℃
        存储温度: -40℃~+85℃
        相对湿度: ≤95%
        绝缘电压: 4kV
        
        产品特性:
        1. LCD液晶显示
        2. 红外通讯功能
        3. RS485通讯接口
        4. 防窃电功能
        
        基础价格: 580元
        """,
        expected_confidence_range=(0.80, 0.95)
    )
    
    # 测试用例2: 中等质量文档 - 期望中等置信度 (60%-80%)
    tester.create_test_case(
        name="中等质量文档",
        content="""
        变压器测试仪
        型号: BCT-200
        分类: 测试设备
        
        参数:
        电压: 0-500V
        电流: 0-20A
        精度: ±0.5%
        频率: 50/60Hz
        
        特点: 自动测试、数据存储
        价格: 15000
        """,
        expected_confidence_range=(0.60, 0.80)
    )
    
    # 测试用例3: 不完整文档 - 期望较低置信度 (30%-60%)
    tester.create_test_case(
        name="不完整文档",
        content="""
        电机控制器
        一些电压和电流参数
        工作在工业环境中
        价格待定
        """,
        expected_confidence_range=(0.30, 0.60)
    )
    
    # 测试用例4: 包含噪声的文档 - 期望中等置信度 (50%-80%)
    tester.create_test_case(
        name="包含噪声的文档",
        content="""
        PAGE 1
        继电器技术规格
        产品名称: 时间继电器
        型号: HHS15
        A A AB X B
        额定电压: 220V AC
        触点容量: 5A
        HYPERLINK http://example.com
        延时范围: 0.1s-30h
        Ca a a a b  
        工作温度: -5℃~+40℃
        h 9 HYPERLINK HYPE
        基础价格: 120元
        """,
        expected_confidence_range=(0.50, 0.80)
    )
    
    # 测试用例5: 英文技术文档 - 期望高置信度 (75%-90%)
    tester.create_test_case(
        name="英文技术文档",
        content="""
        Motor Controller Specification
        
        Product Name: AC Motor Controller
        Model: MC-3000
        Category: Industrial Control
        
        Technical Specifications:
        Voltage: 380V AC ±10%
        Current: 0-50A
        Power: 22kW
        Frequency: 50/60Hz
        Protection: IP65
        Temperature: -20°C to +60°C
        Efficiency: >95%
        
        Features:
        - Vector control
        - PID regulation  
        - RS485 communication
        - Overload protection
        
        Price: $2,500
        """,
        expected_confidence_range=(0.75, 0.90)
    )

def main():
    """主测试函数"""
    logger.info("🔬 置信度性能测试套件启动...")
    
    # 创建测试器
    tester = ConfidencePerformanceTest()
    
    # 加载测试用例
    create_test_cases(tester)
    
    # 运行测试
    success = tester.run_all_tests()
    
    if success:
        logger.info("\n🎉 所有测试用例通过！置信度算法性能验证成功！")
        return True
    else:
        logger.error("\n😞 部分测试用例失败，需要进一步优化")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)