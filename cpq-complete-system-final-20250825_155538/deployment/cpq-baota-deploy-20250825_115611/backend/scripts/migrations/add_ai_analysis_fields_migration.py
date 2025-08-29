#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本 - 为Product模型添加AI分析字段
"""

import sys
import os

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..')
sys.path.insert(0, project_root)

from sqlalchemy import text
from src.models import db
from app import create_app

def add_ai_analysis_fields():
    """为Product表添加AI分析相关字段"""
    
    print("🔧 开始为Product表添加AI分析字段...")
    
    try:
        # 检查字段是否已存在的SQL（SQLite适配）
        check_columns_sql = """
        PRAGMA table_info(products);
        """
        
        result = db.session.execute(text(check_columns_sql))
        existing_columns = [row[1] for row in result.fetchall()]  # SQLite PRAGMA返回的第二列是字段名
        
        # 需要添加的字段定义（SQLite适配）
        fields_to_add = {
            'detailed_description': "detailed_description TEXT",
            'features': "features TEXT",
            'application_scenarios': "application_scenarios TEXT", 
            'accessories': "accessories TEXT",
            'certificates': "certificates TEXT",
            'support_info': "support_info TEXT"
        }
        
        # 逐个添加不存在的字段
        added_count = 0
        for field_name, field_definition in fields_to_add.items():
            if field_name not in existing_columns:
                try:
                    alter_sql = f"ALTER TABLE products ADD COLUMN {field_definition}"
                    db.session.execute(text(alter_sql))
                    print(f"✅ 已添加字段: {field_name}")
                    added_count += 1
                except Exception as e:
                    print(f"❌ 添加字段 {field_name} 失败: {str(e)}")
            else:
                print(f"⚠️ 字段 {field_name} 已存在，跳过")
        
        if added_count > 0:
            db.session.commit()
            print(f"🎉 成功添加 {added_count} 个AI分析字段到Product表")
        else:
            print("ℹ️ 所有AI分析字段都已存在，无需添加")
            
    except Exception as e:
        db.session.rollback()
        print(f"❌ 添加AI分析字段失败: {str(e)}")
        raise e

def verify_fields():
    """验证字段是否添加成功"""
    print("\n🔍 验证字段添加结果...")
    
    try:
        # 查询所有产品表字段（SQLite适配）
        check_sql = "PRAGMA table_info(products);"
        
        result = db.session.execute(text(check_sql))
        columns = result.fetchall()
        
        print("\n📊 当前Product表字段结构:")
        print("-" * 70)
        print(f"{'字段名':<25} {'类型':<15} {'允许NULL':<10} {'默认值':<10}")
        print("-" * 70)
        
        ai_fields = ['detailed_description', 'features', 'application_scenarios', 
                    'accessories', 'certificates', 'support_info']
        ai_field_count = 0
        
        for column in columns:
            # SQLite PRAGMA table_info格式: cid, name, type, notnull, dflt_value, pk
            cid, column_name, data_type, notnull, default_value, pk = column
            nullable = "NO" if notnull else "YES"
            default_str = str(default_value) if default_value is not None else ""
            
            if column_name in ai_fields:
                ai_field_count += 1
                print(f"✅ {column_name:<25} {data_type:<15} {nullable:<10} {default_str:<10}")
            else:
                print(f"   {column_name:<25} {data_type:<15} {nullable:<10} {default_str:<10}")
        
        print("-" * 70)
        print(f"📈 AI分析字段统计: {ai_field_count}/{len(ai_fields)} 个字段已存在")
        
        if ai_field_count == len(ai_fields):
            print("🎉 所有AI分析字段都已成功添加!")
        else:
            print("⚠️ 部分AI分析字段缺失，请检查迁移过程")
            
    except Exception as e:
        print(f"❌ 验证字段失败: {str(e)}")

def main():
    """主函数"""
    print("🚀 Product表AI分析字段迁移工具")
    print("=" * 60)
    
    # 创建应用上下文
    app = create_app()
    
    with app.app_context():
        try:
            # 添加字段
            add_ai_analysis_fields()
            
            # 验证结果
            verify_fields()
            
            print("\n✅ AI分析字段迁移完成!")
            
        except Exception as e:
            print(f"\n❌ 迁移过程中发生错误: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    main()