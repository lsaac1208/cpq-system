#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量分析数据库迁移脚本
创建批量分析相关的数据表
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
from src.models.batch_analysis import BatchAnalysisJob, BatchAnalysisFile, BatchProcessingSummary

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('batch_analysis_migration.log')
        ]
    )
    return logging.getLogger(__name__)

def create_tables(app, logger):
    """创建批量分析相关表"""
    logger.info("开始创建批量分析表...")
    
    with app.app_context():
        try:
            # 创建表
            logger.info("创建 batch_analysis_jobs 表...")
            BatchAnalysisJob.__table__.create(db.engine, checkfirst=True)
            
            logger.info("创建 batch_analysis_files 表...")
            BatchAnalysisFile.__table__.create(db.engine, checkfirst=True)
            
            logger.info("创建 batch_processing_summaries 表...")
            BatchProcessingSummary.__table__.create(db.engine, checkfirst=True)
            
            # 提交事务
            db.session.commit()
            logger.info("✅ 所有批量分析表创建成功")
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
                'batch_analysis_jobs',
                'batch_analysis_files', 
                'batch_processing_summaries'
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
            
            # 检查表结构
            logger.info("检查 batch_analysis_jobs 表结构...")
            columns = [col['name'] for col in inspector.get_columns('batch_analysis_jobs')]
            expected_columns = [
                'id', 'job_id', 'user_id', 'status', 'total_files',
                'processed_files', 'successful_files', 'failed_files',
                'estimated_duration', 'actual_duration', 'start_time', 'end_time', 
                'settings', 'total_size', 'average_confidence', 'error_message', 
                'created_at', 'updated_at'
            ]
            
            missing_columns = [col for col in expected_columns if col not in columns]
            if missing_columns:
                logger.error(f"❌ batch_analysis_jobs 缺少列: {missing_columns}")
                return False
            
            logger.info("检查 batch_analysis_files 表结构...")
            columns = [col['name'] for col in inspector.get_columns('batch_analysis_files')]
            expected_columns = [
                'id', 'job_id', 'analysis_record_id', 'file_id', 'filename', 
                'original_filename', 'file_size', 'file_type', 'file_hash', 'status', 
                'priority', 'start_time', 'end_time', 'processing_duration', 
                'analysis_result', 'confidence_score', 'error_message', 
                'created_at', 'updated_at'
            ]
            
            missing_columns = [col for col in expected_columns if col not in columns]
            if missing_columns:
                logger.error(f"❌ batch_analysis_files 缺少列: {missing_columns}")
                return False
            
            logger.info("检查 batch_processing_summaries 表结构...")
            columns = [col['name'] for col in inspector.get_columns('batch_processing_summaries')]
            expected_columns = [
                'id', 'job_id', 'total_files', 'successful_files', 'failed_files', 
                'skipped_files', 'total_processing_time', 'average_file_time',
                'fastest_file_time', 'slowest_file_time', 'average_confidence',
                'high_confidence_count', 'low_confidence_count', 'file_type_stats',
                'common_errors', 'error_categories', 'created_at', 'updated_at'
            ]
            
            missing_columns = [col for col in expected_columns if col not in columns]
            if missing_columns:
                logger.error(f"❌ batch_processing_summaries 缺少列: {missing_columns}")
                return False
            
            logger.info("✅ 所有表结构验证通过")
            return True
            
        except Exception as e:
            logger.error(f"❌ 表结构验证失败: {str(e)}")
            return False

def main():
    """主函数"""
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("批量分析数据库迁移脚本")
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
        logger.info("\n步骤 1/2: 创建数据表")
        logger.info("-" * 40)
        if not create_tables(app, logger):
            return False
        
        # 步骤2: 验证表结构
        logger.info("\n步骤 2/2: 验证表结构")
        logger.info("-" * 40)
        if not verify_tables(app, logger):
            return False
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 批量分析数据库迁移完成!")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 迁移过程发生错误: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)