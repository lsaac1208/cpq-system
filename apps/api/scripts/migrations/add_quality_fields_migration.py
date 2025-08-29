#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据质量字段迁移脚本
为AI分析记录添加数据质量验证相关字段
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app import create_app
from src.models.base import db
from sqlalchemy import text
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_quality_fields():
    """添加数据质量验证字段到ai_analysis_records表"""
    
    try:
        app = create_app()
        with app.app_context():
            logger.info("🚀 开始数据库迁移：添加数据质量验证字段...")
            
            # 检查表是否存在 - 使用SQLite语法
            with db.engine.connect() as conn:
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_analysis_records'"))
                if not result.fetchone():
                    logger.error("❌ ai_analysis_records表不存在")
                    return False
                
                # 检查字段是否已经存在 - 使用SQLite语法
                result = conn.execute(text("PRAGMA table_info(ai_analysis_records)"))
                existing_columns = [row[1] for row in result.fetchall()]  # SQLite的PRAGMA返回的字段名在索引1
                
                fields_to_add = [
                    ('data_quality_score', 'REAL'),
                    ('quality_validation_report', 'TEXT'),
                    ('noise_removed_count', 'INTEGER DEFAULT 0'),
                    ('invalid_removed_count', 'INTEGER DEFAULT 0'),
                    ('final_specs_count', 'INTEGER DEFAULT 0')
                ]
                
                added_fields = 0
                # 使用transaction处理所有字段添加
                with db.engine.begin() as conn:
                    for field_name, field_definition in fields_to_add:
                        if field_name not in existing_columns:
                            try:
                                sql = f"ALTER TABLE ai_analysis_records ADD COLUMN {field_name} {field_definition}"
                                conn.execute(text(sql))
                                logger.info(f"✅ 添加字段: {field_name}")
                                added_fields += 1
                            except Exception as e:
                                logger.error(f"❌ 添加字段 {field_name} 失败: {e}")
                                return False
                        else:
                            logger.info(f"⏭️  字段 {field_name} 已存在，跳过")
                
                if added_fields > 0:
                    logger.info(f"🎉 迁移成功完成！添加了 {added_fields} 个新字段")
                else:
                    logger.info("✅ 所有字段都已存在，无需迁移")
                
                # 验证迁移结果
                with db.engine.connect() as conn:
                    result = conn.execute(text("PRAGMA table_info(ai_analysis_records)"))
                    final_columns = [row[1] for row in result.fetchall()]  # SQLite的PRAGMA返回的字段名在索引1
            
                missing_fields = []
                for field_name, _ in fields_to_add:
                    if field_name not in final_columns:
                        missing_fields.append(field_name)
                
                if missing_fields:
                    logger.error(f"❌ 迁移验证失败，缺少字段: {missing_fields}")
                    return False
                else:
                    logger.info("✅ 迁移验证成功，所有字段都已存在")
                    return True
                    
    except Exception as e:
        logger.error(f"❌ 数据库迁移失败: {e}")
        return False

def rollback_quality_fields():
    """回滚数据质量字段迁移"""
    try:
        app = create_app()
        with app.app_context():
            logger.info("🔄 开始回滚数据质量字段迁移...")
            
            fields_to_remove = [
                'data_quality_score',
                'quality_validation_report', 
                'noise_removed_count',
                'invalid_removed_count',
                'final_specs_count'
            ]
            
            with db.engine.begin() as conn:
                for field_name in fields_to_remove:
                    try:
                        sql = f"ALTER TABLE ai_analysis_records DROP COLUMN {field_name}"
                        conn.execute(text(sql))
                        logger.info(f"✅ 删除字段: {field_name}")
                    except Exception as e:
                        if "doesn't exist" in str(e).lower():
                            logger.info(f"⏭️  字段 {field_name} 不存在，跳过")
                        else:
                            logger.error(f"❌ 删除字段 {field_name} 失败: {e}")
            
            logger.info("🎉 回滚完成！")
            return True
            
    except Exception as e:
        logger.error(f"❌ 回滚失败: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        success = rollback_quality_fields()
    else:
        success = add_quality_fields()
    
    if success:
        logger.info("✅ 操作完成")
        sys.exit(0)
    else:
        logger.error("❌ 操作失败")
        sys.exit(1)