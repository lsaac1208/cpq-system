#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档对比分析数据库迁移脚本
创建文档对比分析相关的数据表
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
from src.models.document_comparison import (
    DocumentComparison, ComparisonDocument, ComparisonResult, ComparisonTemplate, ComparisonType
)

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('document_comparison_migration.log')
        ]
    )
    return logging.getLogger(__name__)

def create_tables(app, logger):
    """创建文档对比分析相关表"""
    logger.info("开始创建文档对比分析表...")
    
    with app.app_context():
        try:
            # 创建表
            logger.info("创建 document_comparisons 表...")
            DocumentComparison.__table__.create(db.engine, checkfirst=True)
            
            logger.info("创建 comparison_documents 表...")
            ComparisonDocument.__table__.create(db.engine, checkfirst=True)
            
            logger.info("创建 comparison_results 表...")
            ComparisonResult.__table__.create(db.engine, checkfirst=True)
            
            logger.info("创建 comparison_templates 表...")
            ComparisonTemplate.__table__.create(db.engine, checkfirst=True)
            
            # 提交事务
            db.session.commit()
            logger.info("✅ 所有文档对比分析表创建成功")
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
                'document_comparisons',
                'comparison_documents', 
                'comparison_results',
                'comparison_templates'
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
            logger.info("检查 document_comparisons 表结构...")
            columns = [col['name'] for col in inspector.get_columns('document_comparisons')]
            expected_columns = [
                'id', 'comparison_id', 'user_id', 'name', 'description', 'comparison_type',
                'status', 'document_count', 'primary_document_id', 'comparison_settings',
                'start_time', 'end_time', 'processing_duration', 'total_differences',
                'significant_differences', 'similarities_count', 'confidence_score',
                'error_message', 'created_at', 'updated_at'
            ]
            
            missing_columns = [col for col in expected_columns if col not in columns]
            if missing_columns:
                logger.error(f"❌ document_comparisons 缺少列: {missing_columns}")
                return False
            
            logger.info("检查 comparison_documents 表结构...")
            columns = [col['name'] for col in inspector.get_columns('comparison_documents')]
            expected_columns = [
                'id', 'comparison_id', 'analysis_record_id', 'document_role',
                'document_label', 'display_order', 'comparison_weight', 'created_at'
            ]
            
            missing_columns = [col for col in expected_columns if col not in columns]
            if missing_columns:
                logger.error(f"❌ comparison_documents 缺少列: {missing_columns}")
                return False
            
            logger.info("检查 comparison_results 表结构...")
            columns = [col['name'] for col in inspector.get_columns('comparison_results')]
            expected_columns = [
                'id', 'comparison_id', 'result_type', 'category', 'subcategory',
                'title', 'description', 'details', 'importance_score', 'confidence_score',
                'involved_documents', 'source_locations', 'created_at'
            ]
            
            missing_columns = [col for col in expected_columns if col not in columns]
            if missing_columns:
                logger.error(f"❌ comparison_results 缺少列: {missing_columns}")
                return False
            
            logger.info("检查 comparison_templates 表结构...")
            columns = [col['name'] for col in inspector.get_columns('comparison_templates')]
            expected_columns = [
                'id', 'template_id', 'name', 'description', 'comparison_type',
                'template_config', 'comparison_fields', 'output_format', 'usage_count',
                'is_public', 'created_by', 'created_at', 'updated_at'
            ]
            
            missing_columns = [col for col in expected_columns if col not in columns]
            if missing_columns:
                logger.error(f"❌ comparison_templates 缺少列: {missing_columns}")
                return False
            
            logger.info("✅ 所有表结构验证通过")
            return True
            
        except Exception as e:
            logger.error(f"❌ 表结构验证失败: {str(e)}")
            return False

def create_default_templates(app, logger):
    """创建默认对比模板"""
    logger.info("创建默认对比模板...")
    
    with app.app_context():
        try:
            # 检查是否已存在默认模板
            existing = ComparisonTemplate.query.filter_by(template_id='default_product_specs').first()
            if existing:
                logger.info("默认模板已存在，跳过创建")
                return True
            
            # 产品规格对比模板
            template1 = ComparisonTemplate()
            template1.template_id = 'default_product_specs'
            template1.name = '产品规格对比'
            template1.description = '专注于产品规格、价格、功能、性能等核心属性的对比分析'
            template1.comparison_type = ComparisonType.PRODUCT_SPECS
            template1.template_config = {
                'focus_areas': ['价格', '规格', '功能', '性能', '尺寸', '重量', '材质', '颜色', '品牌'],
                'include_similarities': True,
                'include_differences': True,
                'enable_insights': True,
                'min_confidence_threshold': 0.6,
                'importance_threshold': 0.5
            }
            template1.comparison_fields = {
                'price': {'weight': 1.0, 'required': True},
                'specifications': {'weight': 0.9, 'required': True},
                'features': {'weight': 0.8, 'required': False},
                'performance': {'weight': 0.7, 'required': False}
            }
            template1.output_format = {
                'categories': ['价格差异', '规格对比', '功能比较', '性能分析', '物理属性'],
                'max_results_per_category': 20
            }
            template1.is_public = True
            template1.save()
            
            # 价格分析模板
            template2 = ComparisonTemplate()
            template2.template_id = 'default_price_analysis'
            template2.name = '价格分析对比'
            template2.description = '专注于价格、性价比、成本效益等价格相关的对比分析'
            template2.comparison_type = ComparisonType.PRICE_ANALYSIS
            template2.template_config = {
                'focus_areas': ['价格', '性价比', '成本', '优惠', '折扣', '套餐'],
                'include_similarities': True,
                'include_differences': True,
                'enable_insights': True,
                'min_confidence_threshold': 0.7,
                'importance_threshold': 0.6
            }
            template2.comparison_fields = {
                'price': {'weight': 1.0, 'required': True},
                'value_for_money': {'weight': 0.9, 'required': True},
                'discounts': {'weight': 0.6, 'required': False},
                'packages': {'weight': 0.5, 'required': False}
            }
            template2.output_format = {
                'categories': ['价格对比', '性价比分析', '优惠政策', '成本效益'],
                'max_results_per_category': 15
            }
            template2.is_public = True
            template2.save()
            
            # 功能特性矩阵模板
            template3 = ComparisonTemplate()
            template3.template_id = 'default_feature_matrix'
            template3.name = '功能特性矩阵'
            template3.description = '专注于功能、特性、能力、兼容性等功能相关的对比分析'
            template3.comparison_type = ComparisonType.FEATURE_MATRIX
            template3.template_config = {
                'focus_areas': ['功能', '特性', '能力', '支持', '兼容性', '限制'],
                'include_similarities': True,
                'include_differences': True,
                'enable_insights': True,
                'min_confidence_threshold': 0.6,
                'importance_threshold': 0.5
            }
            template3.comparison_fields = {
                'features': {'weight': 1.0, 'required': True},
                'capabilities': {'weight': 0.9, 'required': True},
                'compatibility': {'weight': 0.7, 'required': False},
                'limitations': {'weight': 0.6, 'required': False}
            }
            template3.output_format = {
                'categories': ['核心功能', '扩展特性', '技术支持', '兼容性分析'],
                'max_results_per_category': 25
            }
            template3.is_public = True
            template3.save()
            
            logger.info("✅ 默认对比模板创建成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 创建默认模板失败: {str(e)}")
            return False

def main():
    """主函数"""
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("文档对比分析数据库迁移脚本")
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
        logger.info("\n步骤 1/3: 创建数据表")
        logger.info("-" * 40)
        if not create_tables(app, logger):
            return False
        
        # 步骤2: 验证表结构
        logger.info("\n步骤 2/3: 验证表结构")
        logger.info("-" * 40)
        if not verify_tables(app, logger):
            return False
        
        # 步骤3: 创建默认模板
        logger.info("\n步骤 3/3: 创建默认模板")
        logger.info("-" * 40)
        if not create_default_templates(app, logger):
            return False
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 文档对比分析数据库迁移完成!")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 迁移过程发生错误: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)