#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加学习模式相关数据库表的迁移脚本
创建 learning_patterns 和 learning_feedback 表
"""
import os
import sys

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
api_dir = os.path.dirname(current_dir)
sys.path.insert(0, api_dir)

from app import create_app
from src.models import db, LearningPattern, LearningFeedback

def create_learning_tables():
    """创建学习相关的数据库表"""
    
    print("🗄️  Creating learning-related database tables...")
    
    try:
        app = create_app()
        
        with app.app_context():
            # 创建表
            print("  📊 Creating learning tables...")
            db.create_all()
            print("  ✅ All learning tables created successfully")
            
            # 提交事务
            db.session.commit()
            print("  💾 Database changes committed")
            
    except Exception as e:
        print(f"  ❌ Error creating tables: {str(e)}")
        try:
            db.session.rollback()
        except:
            pass
        return False
    
    return True

def verify_tables():
    """验证表是否创建成功"""
    print("🔍 Verifying table creation...")
    
    try:
        app = create_app()
        
        with app.app_context():
            # 检查表是否存在
            inspector = db.inspect(db.engine)
            
            # 验证 learning_patterns 表
            if 'learning_patterns' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('learning_patterns')]
                print(f"  ✅ learning_patterns table verified ({len(columns)} columns)")
                print(f"     Columns: {', '.join(columns[:5])}...")
            else:
                print("  ❌ learning_patterns table not found")
                return False
            
            # 验证 learning_feedback 表
            if 'learning_feedback' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('learning_feedback')]
                print(f"  ✅ learning_feedback table verified ({len(columns)} columns)")
                print(f"     Columns: {', '.join(columns)}")
            else:
                print("  ❌ learning_feedback table not found")
                return False
            
    except Exception as e:
        print(f"  ❌ Error verifying tables: {str(e)}")
        return False
    
    return True

def create_indexes():
    """创建必要的索引以优化查询性能"""
    print("📊 Creating database indexes...")
    
    try:
        app = create_app()
        
        with app.app_context():
            # 创建学习模式表的索引
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_learning_patterns_field_path ON learning_patterns(field_path);",
                "CREATE INDEX IF NOT EXISTS idx_learning_patterns_user_id ON learning_patterns(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_learning_patterns_document_type ON learning_patterns(document_type);",
                "CREATE INDEX IF NOT EXISTS idx_learning_patterns_pattern_type ON learning_patterns(pattern_type);",
                "CREATE INDEX IF NOT EXISTS idx_learning_patterns_frequency ON learning_patterns(frequency);",
                "CREATE INDEX IF NOT EXISTS idx_learning_patterns_last_seen ON learning_patterns(last_seen);",
                "CREATE INDEX IF NOT EXISTS idx_learning_feedback_analysis_record ON learning_feedback(analysis_record_id);",
                "CREATE INDEX IF NOT EXISTS idx_learning_feedback_user_id ON learning_feedback(user_id);"
            ]
            
            for index_sql in indexes:
                try:
                    db.session.execute(db.text(index_sql))
                    print(f"  ✅ Created index: {index_sql.split(' ')[5]}")
                except Exception as e:
                    print(f"  ⚠️  Index creation warning: {str(e)}")
            
            db.session.commit()
            print("  💾 Index creation completed")
            
    except Exception as e:
        print(f"  ❌ Error creating indexes: {str(e)}")
        db.session.rollback()
        return False
    
    return True

def show_table_info():
    """显示表结构信息"""
    print("📋 Table Information:")
    
    try:
        app = create_app()
        
        with app.app_context():
            inspector = db.inspect(db.engine)
            
            # Learning Patterns 表信息
            print("\n  📊 learning_patterns table:")
            if 'learning_patterns' in inspector.get_table_names():
                columns = inspector.get_columns('learning_patterns')
                for col in columns:
                    col_type = str(col['type'])
                    nullable = "NULL" if col['nullable'] else "NOT NULL"
                    print(f"    - {col['name']}: {col_type} {nullable}")
            
            # Learning Feedback 表信息
            print("\n  📝 learning_feedback table:")
            if 'learning_feedback' in inspector.get_table_names():
                columns = inspector.get_columns('learning_feedback')
                for col in columns:
                    col_type = str(col['type'])
                    nullable = "NULL" if col['nullable'] else "NOT NULL"
                    print(f"    - {col['name']}: {col_type} {nullable}")
            
    except Exception as e:
        print(f"  ❌ Error showing table info: {str(e)}")

def main():
    """主函数"""
    print("🚀 Learning Tables Migration Script")
    print("=" * 50)
    
    success_steps = 0
    total_steps = 4
    
    # 步骤 1: 创建表
    if create_learning_tables():
        success_steps += 1
        print("✅ Step 1/4: Tables created successfully\n")
    else:
        print("❌ Step 1/4: Table creation failed\n")
        return False
    
    # 步骤 2: 验证表
    if verify_tables():
        success_steps += 1
        print("✅ Step 2/4: Tables verified successfully\n")
    else:
        print("❌ Step 2/4: Table verification failed\n")
        return False
    
    # 步骤 3: 创建索引
    if create_indexes():
        success_steps += 1
        print("✅ Step 3/4: Indexes created successfully\n")
    else:
        print("❌ Step 3/4: Index creation failed\n")
        return False
    
    # 步骤 4: 显示表信息
    try:
        show_table_info()
        success_steps += 1
        print("\n✅ Step 4/4: Table information displayed\n")
    except Exception as e:
        print(f"❌ Step 4/4: Failed to show table info: {str(e)}\n")
    
    # 总结
    print("=" * 50)
    print(f"📊 Migration Summary: {success_steps}/{total_steps} steps completed")
    
    if success_steps == total_steps:
        print("🎉 Learning tables migration completed successfully!")
        print("\n📝 Next steps:")
        print("  1. Restart the API server")
        print("  2. Test learning functionality through the API")
        print("  3. Monitor learning pattern accumulation")
        return True
    else:
        print("💥 Migration completed with some issues.")
        print("   Please check the errors above and fix them.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)