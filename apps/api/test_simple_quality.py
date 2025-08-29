#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的数据质量优化测试脚本
专注测试核心质量优化功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app import create_app
from src.services.document_processor import DocumentProcessor
from src.services.ai_analyzer import AIAnalyzer
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_noise_removal():
    """测试噪声移除功能"""
    logger.info("🧪 测试文档噪声移除功能...")
    
    processor = DocumentProcessor()
    cleaner = processor.content_cleaner
    
    # 测试单独的噪声行
    test_lines = [
        "设备名称: 电机控制器",  # 正常内容
        "PAGE 7",              # 页面标记
        "电压: 380V",          # 正常内容  
        "A A AB X B",          # 表格噪声
        "功率: 15kW",          # 正常内容
        "HYPERLINK http://example.com",  # 超链接标记
        "频率: 50Hz",          # 正常内容
        "Ca a a a b",          # 表格噪声
    ]
    
    logger.info("📝 测试输入:")
    for i, line in enumerate(test_lines, 1):
        logger.info(f"  {i}. {line}")
    
    # 逐行测试噪声检测
    def is_line_noise(line: str) -> bool:
        """检测单行是否为噪声"""
        line = line.strip()
        if not line:
            return True
            
        # 检查是否为保护内容
        if cleaner._is_protected_content(line):
            return False
            
        # 检查各种噪声模式
        if cleaner._matches_patterns(line, cleaner.word_noise_patterns):
            return True
        if cleaner._matches_patterns(line, cleaner.page_nav_patterns):
            return True  
        if cleaner._matches_patterns(line, cleaner.table_noise_patterns):
            return True
        if cleaner._matches_patterns(line, cleaner.meaningless_patterns):
            return True
            
        return False
    
    valid_lines = []
    noise_count = 0
    
    for line in test_lines:
        is_noise_result = is_line_noise(line)
        if is_noise_result:
            logger.info(f"❌ 检测为噪声: '{line}'")
            noise_count += 1
        else:
            # 对于HYPERLINK特别测试
            if "HYPERLINK" in line:
                import re
                logger.info(f"🔍 HYPERLINK测试: '{line}'")
                
                # 测试保护模式
                is_protected = cleaner._is_protected_content(line)
                logger.info(f"  - 被保护内容: {is_protected}")
                
                if is_protected:
                    # 找出是哪个保护模式匹配的
                    import re
                    for pattern in cleaner.protect_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            logger.info(f"  - 匹配保护模式: {pattern}")
                            break
                
                # 测试噪声模式匹配
                for pattern in cleaner.word_noise_patterns:
                    if re.search(pattern, line):
                        logger.info(f"  - 匹配噪声模式: {pattern}")
                        break
                else:
                    logger.info(f"  - 未匹配任何HYPERLINK模式")
            logger.info(f"✅ 保留有效内容: '{line}'")
            valid_lines.append(line)
    
    logger.info(f"\n📊 统计结果:")
    logger.info(f"- 原始行数: {len(test_lines)}")
    logger.info(f"- 检测为噪声: {noise_count}")
    logger.info(f"- 保留有效: {len(valid_lines)}")
    
    # 验证预期的噪声是否被正确识别
    expected_noise = ["PAGE 7", "A A AB X B", "HYPERLINK http://example.com", "Ca a a a b"]
    expected_valid = ["设备名称: 电机控制器", "电压: 380V", "功率: 15kW", "频率: 50Hz"]
    
    success = True
    for noise_line in expected_noise:
        if noise_line in [line for line in test_lines if line not in [v.strip() for v in valid_lines]]:
            continue  # 正确识别为噪声
        else:
            logger.error(f"❌ 未正确识别噪声: {noise_line}")
            success = False
    
    for valid_line in expected_valid:
        if valid_line in valid_lines:
            continue  # 正确保留
        else:
            logger.error(f"❌ 错误移除有效内容: {valid_line}")
            success = False
    
    return success

def main():
    """运行简化测试"""
    logger.info("🚀 开始简化的数据质量测试...")
    
    # 测试噪声移除
    if test_noise_removal():
        logger.info("✅ 噪声移除测试通过")
        logger.info("🎉 数据质量优化的核心噪声过滤功能正常工作！")
        return True
    else:
        logger.error("❌ 噪声移除测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)