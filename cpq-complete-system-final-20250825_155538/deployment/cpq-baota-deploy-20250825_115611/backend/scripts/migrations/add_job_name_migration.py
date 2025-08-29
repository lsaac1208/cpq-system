#!/usr/bin/env python3
"""
为批量分析任务表添加 job_name 字段的数据库迁移脚本
"""
import os
import sys
sys.path.append('.')

# 设置环境变量
os.environ['FLASK_ENV'] = 'development'

import logging
from sqlalchemy import create_engine, text, inspect

logger = logging.getLogger(__name__)

def add_job_name_field():
    """添加 job_name 字段到 batch_analysis_jobs 表"""
    try:
        # 直接连接数据库
        database_url = "sqlite:///cpq_database.db"
        engine = create_engine(database_url)
        
        # 检查字段是否已经存在
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('batch_analysis_jobs')]
        
        if 'job_name' in columns:
            print("✅ job_name 字段已存在")
            return True
        
        # 添加 job_name 字段
        print("🔧 添加 job_name 字段到 batch_analysis_jobs 表...")
        
        with engine.connect() as conn:
            # 添加新字段
            conn.execute(text("""
                ALTER TABLE batch_analysis_jobs 
                ADD COLUMN job_name VARCHAR(200)
            """))
            
            # 为现有记录设置默认值
            conn.execute(text("""
                UPDATE batch_analysis_jobs 
                SET job_name = '批量分析任务 #' || id
                WHERE job_name IS NULL
            """))
            
            conn.commit()
        
        print("✅ 成功添加 job_name 字段")
        return True
        
    except Exception as e:
        print(f"❌ 添加字段失败: {str(e)}")
        logger.error(f"Migration failed: {str(e)}")
        return False

if __name__ == '__main__':
    add_job_name_field()