#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI分析功能数据库迁移脚本
创建AI分析记录和设置表
"""
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from src.models import db, AIAnalysisRecord, AIAnalysisSettings

def create_ai_analysis_tables():
    """创建AI分析相关表"""
    app = create_app()
    
    with app.app_context():
        print("Creating AI analysis tables...")
        
        try:
            # 创建表
            db.create_all()
            
            # 初始化默认设置
            default_settings = [
                {
                    'setting_key': 'openai_model',
                    'setting_value': 'gpt-4o-mini',
                    'description': 'OpenAI模型名称',
                    'category': 'ai'
                },
                {
                    'setting_key': 'max_file_size_mb',
                    'setting_value': 10,
                    'description': '最大文件大小(MB)',
                    'category': 'upload'
                },
                {
                    'setting_key': 'max_text_length',
                    'setting_value': 50000,
                    'description': '最大文本长度',
                    'category': 'processing'
                },
                {
                    'setting_key': 'analysis_timeout_seconds',
                    'setting_value': 120,
                    'description': 'AI分析超时时间(秒)',
                    'category': 'ai'
                },
                {
                    'setting_key': 'enable_ocr',
                    'setting_value': True,
                    'description': '启用OCR图片文字识别',
                    'category': 'processing'
                }
            ]
            
            for setting_data in default_settings:
                existing = AIAnalysisSettings.query.filter_by(
                    setting_key=setting_data['setting_key']
                ).first()
                
                if not existing:
                    setting = AIAnalysisSettings(**setting_data)
                    db.session.add(setting)
            
            db.session.commit()
            print("✅ AI analysis tables created successfully!")
            print("✅ Default settings initialized!")
            
            # 显示表结构信息
            print("\n📋 Created tables:")
            print(f"  - {AIAnalysisRecord.__tablename__}: AI分析记录表")
            print(f"  - {AIAnalysisSettings.__tablename__}: AI分析设置表")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating tables: {str(e)}")
            raise

def verify_installation():
    """验证安装"""
    app = create_app()
    
    with app.app_context():
        print("\n🔍 Verifying installation...")
        
        # 检查表是否存在
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        required_tables = ['ai_analysis_records', 'ai_analysis_settings']
        for table in required_tables:
            if table in tables:
                print(f"  ✅ Table '{table}' exists")
            else:
                print(f"  ❌ Table '{table}' missing")
        
        # 检查默认设置
        settings_count = AIAnalysisSettings.query.count()
        print(f"  📊 Settings count: {settings_count}")
        
        if settings_count > 0:
            print("  ✅ Default settings loaded")
        else:
            print("  ⚠️  No default settings found")

if __name__ == '__main__':
    print("🚀 Starting AI Analysis feature migration...")
    
    try:
        create_ai_analysis_tables()
        verify_installation()
        print("\n🎉 Migration completed successfully!")
        print("\n📝 Next steps:")
        print("1. Set OPENAI_API_KEY environment variable")
        print("2. Restart the API server")
        print("3. Test the /api/v1/ai-analysis/supported-formats endpoint")
        
    except Exception as e:
        print(f"\n💥 Migration failed: {str(e)}")
        sys.exit(1)