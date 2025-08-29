#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
历史数据优化Prompt功能数据库迁移脚本
创建历史数据优化相关的数据表
"""

import os
import sys
import logging
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app
from src.models.base import db
from src.models.prompt_optimization import (
    PromptOptimizationHistory, UserAnalysisPattern, 
    PromptTemplate, PromptABTest, OptimizationType
)

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('prompt_optimization_migration.log')
        ]
    )
    return logging.getLogger(__name__)

def create_tables(app, logger):
    """创建历史数据优化相关表"""
    logger.info("开始创建历史数据优化相关表...")
    
    with app.app_context():
        try:
            # 创建表
            logger.info("创建 prompt_optimization_history 表...")
            PromptOptimizationHistory.__table__.create(db.engine, checkfirst=True)
            
            logger.info("创建 user_analysis_patterns 表...")
            UserAnalysisPattern.__table__.create(db.engine, checkfirst=True)
            
            logger.info("创建 prompt_templates 表...")
            PromptTemplate.__table__.create(db.engine, checkfirst=True)
            
            logger.info("创建 prompt_ab_tests 表...")
            PromptABTest.__table__.create(db.engine, checkfirst=True)
            
            # 提交事务
            db.session.commit()
            logger.info("✅ 所有历史数据优化表创建成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 创建表失败: {str(e)}")
            try:
                db.session.rollback()
            except Exception:
                pass
            return False

def verify_tables(app, logger):
    """验证表是否正确创建"""
    logger.info("验证表结构...")
    
    with app.app_context():
        try:
            # 检查表是否存在
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            expected_tables = [
                'prompt_optimization_history',
                'user_analysis_patterns',
                'prompt_templates', 
                'prompt_ab_tests'
            ]
            
            missing_tables = []
            for table in expected_tables:
                if table not in tables:
                    missing_tables.append(table)
                else:
                    logger.info(f"✅ 表 {table} 存在")
            
            if missing_tables:
                logger.error(f"❌ 缺少表: {missing_tables}")
                return False
            
            # 检查关键表结构
            logger.info("检查 prompt_optimization_history 表结构...")
            columns = [col['name'] for col in inspector.get_columns('prompt_optimization_history')]
            expected_columns = [
                'id', 'user_id', 'optimization_type', 'optimization_name', 'description',
                'before_prompt', 'after_prompt', 'optimization_diff', 'performance_before',
                'performance_after', 'improvement_score', 'document_types', 'target_fields',
                'is_active', 'usage_count', 'success_rate', 'created_at', 'updated_at', 'created_by'
            ]
            
            missing_columns = [col for col in expected_columns if col not in columns]
            if missing_columns:
                logger.error(f"❌ prompt_optimization_history 缺少列: {missing_columns}")
                return False
            
            logger.info("检查 user_analysis_patterns 表结构...")
            columns = [col['name'] for col in inspector.get_columns('user_analysis_patterns')]
            expected_columns = [
                'id', 'user_id', 'document_type', 'field_name', 'field_category',
                'error_patterns', 'error_frequency', 'error_types', 'success_patterns',
                'success_examples', 'total_analyses', 'correct_analyses', 'accuracy_rate',
                'modification_frequency', 'avg_confidence', 'confidence_distribution',
                'analysis_duration_avg', 'last_analysis_at', 'last_updated', 'created_at'
            ]
            
            missing_columns = [col for col in expected_columns if col not in columns]
            if missing_columns:
                logger.error(f"❌ user_analysis_patterns 缺少列: {missing_columns}")
                return False
            
            logger.info("检查 prompt_templates 表结构...")
            columns = [col['name'] for col in inspector.get_columns('prompt_templates')]
            expected_columns = [
                'id', 'template_id', 'template_name', 'description', 'version',
                'document_types', 'target_fields', 'user_groups', 'base_prompt',
                'optimization_rules', 'dynamic_segments', 'success_rate', 'avg_confidence',
                'usage_count', 'positive_feedback', 'negative_feedback', 'optimization_history',
                'parent_template_id', 'is_active', 'is_default', 'priority',
                'created_at', 'updated_at', 'created_by'
            ]
            
            missing_columns = [col for col in expected_columns if col not in columns]
            if missing_columns:
                logger.error(f"❌ prompt_templates 缺少列: {missing_columns}")
                return False
            
            logger.info("检查 prompt_ab_tests 表结构...")
            columns = [col['name'] for col in inspector.get_columns('prompt_ab_tests')]
            expected_columns = [
                'id', 'test_id', 'test_name', 'description', 'prompt_a', 'prompt_b',
                'template_a_id', 'template_b_id', 'target_users', 'document_types',
                'test_ratio', 'total_tests_a', 'total_tests_b', 'success_rate_a',
                'success_rate_b', 'avg_confidence_a', 'avg_confidence_b', 'p_value',
                'confidence_interval', 'is_significant', 'winner', 'status',
                'min_sample_size', 'max_duration_days', 'start_time', 'end_time',
                'created_at', 'created_by'
            ]
            
            missing_columns = [col for col in expected_columns if col not in columns]
            if missing_columns:
                logger.error(f"❌ prompt_ab_tests 缺少列: {missing_columns}")
                return False
            
            logger.info("✅ 所有表结构验证通过")
            return True
            
        except Exception as e:
            logger.error(f"❌ 表结构验证失败: {str(e)}")
            return False

def create_default_templates(app, logger):
    """创建默认提示词模板"""
    logger.info("创建默认提示词模板...")
    
    with app.app_context():
        try:
            # 检查是否已存在默认模板
            existing = PromptTemplate.query.filter_by(template_id='default_base_template').first()
            if existing:
                logger.info("默认模板已存在，跳过创建")
                return True
            
            # 基础模板
            base_template = PromptTemplate()
            base_template.template_id = 'default_base_template'
            base_template.template_name = '基础产品分析模板'
            base_template.description = '通用的产品规格文档分析模板，适用于各类产品文档'
            base_template.version = '1.0'
            base_template.document_types = ["txt", "pdf", "docx", "xlsx"]
            base_template.base_prompt = """请分析以下产品规格文档，提取结构化的产品信息。

分析要求：
1. 仔细阅读文档内容，理解产品的基本信息
2. 提取以下关键字段的准确信息：
   - 产品名称（name）
   - 产品型号/编号（model/code）  
   - 品牌（brand）
   - 价格（price）
   - 主要规格参数（specifications）
   - 产品描述（description）

3. 确保提取的信息准确、完整，避免遗漏重要细节
4. 对于不确定的信息，请标注置信度较低
5. 使用标准化的格式返回结构化数据

{dynamic_content}

请开始分析："""
            base_template.optimization_rules = [
                {"type": "error_prevention", "enabled": True, "weight": 0.4},
                {"type": "success_pattern", "enabled": True, "weight": 0.3},
                {"type": "field_focus", "enabled": True, "weight": 0.2},
                {"type": "personalization", "enabled": True, "weight": 0.1}
            ]
            base_template.dynamic_segments = {
                "user_guidance": {
                    "type": "conditional",
                    "conditions": [
                        {
                            "condition": "len(value) > 0",
                            "content": "基于分析经验，请特别注意：\n{value}"
                        }
                    ]
                }
            }
            base_template.is_active = True
            base_template.is_default = True
            base_template.priority = 10
            base_template.save()
            
            # 错误预防优化模板
            error_prevention_template = PromptTemplate()
            error_prevention_template.template_id = 'error_prevention_template'
            error_prevention_template.template_name = '错误预防优化模板'
            error_prevention_template.description = '专注于预防常见分析错误的优化模板'
            error_prevention_template.version = '1.0'
            error_prevention_template.document_types = ["txt", "pdf", "docx"]
            error_prevention_template.base_prompt = """请分析以下产品规格文档，特别注意避免常见的分析错误。

**错误预防指导：**
- 仔细区分产品名称和品牌名称，避免混淆
- 准确识别价格信息，注意货币单位和数量
- 规格参数要完整提取，避免遗漏关键参数
- 对于模糊或不清楚的信息，不要猜测，标记为低置信度

分析要求：
1. 按照结构化格式提取产品信息
2. 重点验证以下容易出错的字段：
   - 产品名称 vs 品牌名称
   - 价格数值和单位
   - 技术规格的准确性
   - 型号编号的完整性

{dynamic_content}

请开始分析："""
            error_prevention_template.optimization_rules = [
                {"type": "error_prevention", "enabled": True, "weight": 0.8},
                {"type": "field_focus", "enabled": True, "weight": 0.2}
            ]
            error_prevention_template.is_active = True
            error_prevention_template.priority = 8
            error_prevention_template.save()
            
            # 高置信度模板
            confidence_template = PromptTemplate()
            confidence_template.template_id = 'high_confidence_template'
            confidence_template.template_name = '高置信度分析模板'
            confidence_template.description = '专注于提高分析置信度的优化模板'
            confidence_template.version = '1.0'
            confidence_template.document_types = ["pdf", "docx"]
            confidence_template.base_prompt = """请高质量地分析以下产品规格文档，确保提取信息的可靠性。

**高置信度分析策略：**
1. 多次验证关键信息，确保准确性
2. 对每个提取的字段评估置信度
3. 明确标识不确定或模糊的信息
4. 提供信息来源位置（如第几段、第几行）

分析重点：
- 产品基本信息的准确提取
- 技术规格的完整识别  
- 价格信息的精确提取
- 描述内容的合理总结

置信度评估标准：
- 高（0.8-1.0）：信息明确，来源可靠
- 中（0.6-0.8）：信息基本清楚，有小幅不确定性
- 低（0.0-0.6）：信息模糊或需要推断

{dynamic_content}

请开始高质量分析："""
            confidence_template.optimization_rules = [
                {"type": "success_pattern", "enabled": True, "weight": 0.5},
                {"type": "field_focus", "enabled": True, "weight": 0.3},
                {"type": "error_prevention", "enabled": True, "weight": 0.2}
            ]
            confidence_template.is_active = True
            confidence_template.priority = 6
            confidence_template.save()
            
            logger.info("✅ 默认提示词模板创建成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 创建默认模板失败: {str(e)}")
            return False

def add_ai_analysis_fields(app, logger):
    """为AIAnalysisRecord表添加prompt优化相关字段"""
    logger.info("为AIAnalysisRecord表添加优化相关字段...")
    
    with app.app_context():
        try:
            # 检查字段是否已存在
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('ai_analysis_records')]
            
            # 需要添加的字段
            new_fields = ['prompt_version', 'optimization_applied']
            
            missing_fields = [field for field in new_fields if field not in columns]
            
            if not missing_fields:
                logger.info("字段已存在，跳过添加")
                return True
            
            # 使用ALTER TABLE添加字段（SQLite支持有限，这里用简化方法）
            for field in missing_fields:
                try:
                    if field == 'prompt_version':
                        db.engine.execute(
                            'ALTER TABLE ai_analysis_records ADD COLUMN prompt_version VARCHAR(50) DEFAULT NULL'
                        )
                    elif field == 'optimization_applied':
                        db.engine.execute(
                            'ALTER TABLE ai_analysis_records ADD COLUMN optimization_applied BOOLEAN DEFAULT FALSE'
                        )
                    logger.info(f"添加字段: {field}")
                except Exception as e:
                    logger.warning(f"添加字段{field}失败（可能已存在）: {str(e)}")
            
            db.session.commit()
            logger.info("✅ AIAnalysisRecord字段扩展完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 扩展AIAnalysisRecord失败: {str(e)}")
            return False

def main():
    """主函数"""
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("历史数据优化Prompt数据库迁移脚本")
    logger.info("=" * 60)
    
    try:
        # 创建应用
        logger.info("创建Flask应用...")
        app = create_app()
        
        if not app:
            logger.error("❌ 无法创建Flask应用")
            return False
        
        logger.info("✅ Flask应用创建成功")
        
        # 步骤1: 创建表
        logger.info("\n步骤 1/5: 创建数据表")
        logger.info("-" * 40)
        if not create_tables(app, logger):
            return False
        
        # 步骤2: 验证表结构
        logger.info("\n步骤 2/5: 验证表结构")
        logger.info("-" * 40)
        if not verify_tables(app, logger):
            return False
        
        # 步骤3: 创建默认模板
        logger.info("\n步骤 3/5: 创建默认模板")
        logger.info("-" * 40)
        if not create_default_templates(app, logger):
            return False
        
        # 步骤4: 扩展现有表
        logger.info("\n步骤 4/5: 扩展现有表字段")
        logger.info("-" * 40)
        if not add_ai_analysis_fields(app, logger):
            return False
        
        # 步骤5: 验证完整性
        logger.info("\n步骤 5/5: 验证功能完整性")
        logger.info("-" * 40)
        
        with app.app_context():
            # 验证模板数量
            template_count = PromptTemplate.query.count()
            logger.info(f"创建的模板数量: {template_count}")
            
            if template_count >= 3:
                logger.info("✅ 模板创建验证通过")
            else:
                logger.warning("⚠️ 模板数量少于预期")
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 历史数据优化Prompt数据库迁移完成!")
        logger.info("=" * 60)
        logger.info("新功能包括:")
        logger.info("- 历史数据分析和模式识别")
        logger.info("- 智能Prompt优化引擎")  
        logger.info("- 用户个性化学习机制")
        logger.info("- A/B测试和持续优化")
        logger.info("- 反馈循环和自动改进")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 迁移过程发生错误: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)