#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPQ系统数据库迁移脚本
SQLite -> MySQL 数据迁移
更新时间: 2024-08-24
"""

import os
import sys
import sqlite3
import mysql.connector
from datetime import datetime
from dotenv import load_dotenv
import logging

# 加载环境变量
load_dotenv('.env.production')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class DatabaseMigrator:
    """数据库迁移类"""
    
    def __init__(self):
        """初始化迁移器"""
        self.sqlite_db_path = self._find_sqlite_db()
        self.mysql_config = self._get_mysql_config()
        self.table_mapping = self._get_table_mapping()
        
    def _find_sqlite_db(self):
        """查找SQLite数据库文件"""
        possible_paths = [
            'cpq_system.db',
            'instance/cpq_system.db',
            'cpq_database.db'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"找到SQLite数据库: {path}")
                return path
                
        raise FileNotFoundError("未找到SQLite数据库文件")
    
    def _get_mysql_config(self):
        """获取MySQL配置"""
        return {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', 3306)),
            'user': os.getenv('MYSQL_USER'),
            'password': os.getenv('MYSQL_PASSWORD'),
            'database': os.getenv('MYSQL_DATABASE'),
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci'
        }
    
    def _get_table_mapping(self):
        """获取表结构映射"""
        return {
            'user': {
                'columns': ['id', 'username', 'email', 'password_hash', 'is_active', 'created_at', 'updated_at'],
                'primary_key': 'id'
            },
            'product': {
                'columns': ['id', 'name', 'description', 'price', 'category', 'image_url', 'is_active', 'created_at', 'updated_at'],
                'primary_key': 'id'
            },
            'quote': {
                'columns': ['id', 'user_id', 'status', 'total_amount', 'created_at', 'updated_at'],
                'primary_key': 'id'
            },
            'quote_item': {
                'columns': ['id', 'quote_id', 'product_id', 'quantity', 'unit_price', 'total_price'],
                'primary_key': 'id'
            },
            'multi_quote': {
                'columns': ['id', 'name', 'description', 'status', 'created_by', 'created_at', 'updated_at'],
                'primary_key': 'id'
            },
            'settings': {
                'columns': ['id', 'key', 'value', 'description', 'created_at', 'updated_at'],
                'primary_key': 'id'
            },
            # AI相关表
            'ai_analysis': {
                'columns': ['id', 'content', 'analysis_result', 'confidence_score', 'created_at'],
                'primary_key': 'id'
            },
            'batch_analysis': {
                'columns': ['id', 'name', 'status', 'total_files', 'processed_files', 'created_at', 'updated_at'],
                'primary_key': 'id'
            },
            'document_comparison': {
                'columns': ['id', 'document1_path', 'document2_path', 'comparison_result', 'created_at'],
                'primary_key': 'id'
            },
            'learning_pattern': {
                'columns': ['id', 'pattern_type', 'pattern_data', 'frequency', 'last_used', 'created_at'],
                'primary_key': 'id'
            },
            'product_image': {
                'columns': ['id', 'product_id', 'image_path', 'image_type', 'is_primary', 'created_at'],
                'primary_key': 'id'
            },
            'prompt_optimization': {
                'columns': ['id', 'original_prompt', 'optimized_prompt', 'improvement_score', 'created_at'],
                'primary_key': 'id'
            }
        }
    
    def test_connections(self):
        """测试数据库连接"""
        logger.info("测试数据库连接...")
        
        # 测试SQLite连接
        try:
            sqlite_conn = sqlite3.connect(self.sqlite_db_path)
            sqlite_conn.close()
            logger.info("✅ SQLite连接测试成功")
        except Exception as e:
            logger.error(f"❌ SQLite连接测试失败: {e}")
            return False
        
        # 测试MySQL连接
        try:
            mysql_conn = mysql.connector.connect(**self.mysql_config)
            mysql_conn.close()
            logger.info("✅ MySQL连接测试成功")
        except Exception as e:
            logger.error(f"❌ MySQL连接测试失败: {e}")
            return False
        
        return True
    
    def create_mysql_database(self):
        """创建MySQL数据库（如果不存在）"""
        logger.info("检查/创建MySQL数据库...")
        
        # 连接MySQL服务器（不指定数据库）
        config = self.mysql_config.copy()
        database_name = config.pop('database')
        
        try:
            conn = mysql.connector.connect(**config)
            cursor = conn.cursor()
            
            # 创建数据库
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database_name}` "
                         f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            
            logger.info(f"✅ 数据库 {database_name} 准备就绪")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ 创建数据库失败: {e}")
            raise
    
    def get_sqlite_tables(self):
        """获取SQLite中的所有表"""
        conn = sqlite3.connect(self.sqlite_db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall() 
                 if not table[0].startswith('sqlite_')]
        
        conn.close()
        return tables
    
    def get_table_data(self, table_name):
        """从SQLite获取表数据"""
        conn = sqlite3.connect(self.sqlite_db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(f"SELECT * FROM {table_name}")
            data = cursor.fetchall()
            
            # 获取列名
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            conn.close()
            return data, columns
            
        except Exception as e:
            logger.error(f"获取表 {table_name} 数据失败: {e}")
            conn.close()
            return [], []
    
    def create_mysql_table_structure(self):
        """在MySQL中创建表结构"""
        logger.info("创建MySQL表结构...")
        
        # 使用Flask应用创建表结构
        try:
            # 设置环境变量
            os.environ['FLASK_ENV'] = 'production'
            
            # 导入应用并创建表
            from app import create_app
            from src.models import db
            
            app = create_app('production')
            with app.app_context():
                db.create_all()
                logger.info("✅ MySQL表结构创建成功")
                
        except Exception as e:
            logger.error(f"❌ 创建MySQL表结构失败: {e}")
            raise
    
    def migrate_table_data(self, table_name):
        """迁移单个表的数据"""
        logger.info(f"迁移表: {table_name}")
        
        # 获取SQLite数据
        data, columns = self.get_table_data(table_name)
        
        if not data:
            logger.warning(f"表 {table_name} 无数据，跳过")
            return True
        
        try:
            # 连接MySQL
            mysql_conn = mysql.connector.connect(**self.mysql_config)
            cursor = mysql_conn.cursor()
            
            # 构造插入语句
            placeholders = ', '.join(['%s'] * len(columns))
            insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            # 插入数据
            cursor.executemany(insert_sql, data)
            mysql_conn.commit()
            
            logger.info(f"✅ 表 {table_name} 迁移完成，迁移了 {len(data)} 条记录")
            
            cursor.close()
            mysql_conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 表 {table_name} 迁移失败: {e}")
            if 'mysql_conn' in locals():
                mysql_conn.rollback()
                mysql_conn.close()
            return False
    
    def backup_sqlite_db(self):
        """备份SQLite数据库"""
        backup_name = f"cpq_sqlite_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        backup_path = f"backups/{backup_name}"
        
        # 创建备份目录
        os.makedirs('backups', exist_ok=True)
        
        try:
            import shutil
            shutil.copy2(self.sqlite_db_path, backup_path)
            logger.info(f"✅ SQLite数据库备份完成: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"❌ SQLite数据库备份失败: {e}")
            return None
    
    def verify_migration(self):
        """验证迁移结果"""
        logger.info("验证迁移结果...")
        
        # 获取SQLite表和记录数
        sqlite_tables = self.get_sqlite_tables()
        sqlite_counts = {}
        
        conn = sqlite3.connect(self.sqlite_db_path)
        cursor = conn.cursor()
        
        for table in sqlite_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                sqlite_counts[table] = cursor.fetchone()[0]
            except:
                sqlite_counts[table] = 0
        
        conn.close()
        
        # 获取MySQL表和记录数
        mysql_counts = {}
        mysql_conn = mysql.connector.connect(**self.mysql_config)
        cursor = mysql_conn.cursor()
        
        for table in sqlite_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                mysql_counts[table] = cursor.fetchone()[0]
            except:
                mysql_counts[table] = 0
        
        mysql_conn.close()
        
        # 比较结果
        all_match = True
        logger.info("迁移验证结果:")
        logger.info("-" * 50)
        
        for table in sqlite_tables:
            sqlite_count = sqlite_counts.get(table, 0)
            mysql_count = mysql_counts.get(table, 0)
            status = "✅" if sqlite_count == mysql_count else "❌"
            
            logger.info(f"{status} {table}: SQLite({sqlite_count}) -> MySQL({mysql_count})")
            
            if sqlite_count != mysql_count:
                all_match = False
        
        logger.info("-" * 50)
        
        if all_match:
            logger.info("✅ 所有表数据迁移验证通过")
        else:
            logger.warning("❌ 部分表数据迁移可能存在问题")
        
        return all_match
    
    def run_migration(self):
        """执行完整迁移流程"""
        logger.info("=" * 60)
        logger.info("开始CPQ系统数据库迁移")
        logger.info(f"时间: {datetime.now()}")
        logger.info("=" * 60)
        
        try:
            # 1. 测试连接
            if not self.test_connections():
                raise Exception("数据库连接测试失败")
            
            # 2. 备份SQLite数据库
            backup_path = self.backup_sqlite_db()
            if not backup_path:
                logger.warning("备份失败，但继续迁移...")
            
            # 3. 创建MySQL数据库
            self.create_mysql_database()
            
            # 4. 创建MySQL表结构
            self.create_mysql_table_structure()
            
            # 5. 获取需要迁移的表
            sqlite_tables = self.get_sqlite_tables()
            logger.info(f"发现 {len(sqlite_tables)} 个表需要迁移")
            
            # 6. 迁移数据
            failed_tables = []
            for table in sqlite_tables:
                if not self.migrate_table_data(table):
                    failed_tables.append(table)
            
            # 7. 验证迁移
            verification_passed = self.verify_migration()
            
            # 8. 输出结果
            logger.info("=" * 60)
            if failed_tables:
                logger.error(f"迁移完成，但以下表失败: {failed_tables}")
                return False
            elif not verification_passed:
                logger.warning("迁移完成，但验证发现数据不一致")
                return False
            else:
                logger.info("🎉 数据库迁移成功完成！")
                logger.info(f"备份文件: {backup_path}")
                logger.info("请更新应用配置使用MySQL数据库")
                return True
                
        except Exception as e:
            logger.error(f"❌ 迁移过程中发生错误: {e}")
            return False

def main():
    """主函数"""
    print("CPQ系统数据库迁移工具")
    print("SQLite -> MySQL")
    print("-" * 40)
    
    # 检查参数
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print("使用方法:")
        print("  python migrate.py          # 执行迁移")
        print("  python migrate.py --help   # 显示帮助")
        print("")
        print("迁移前请确保:")
        print("1. MySQL服务正在运行")
        print("2. 已配置正确的MySQL连接信息")
        print("3. MySQL用户有足够权限")
        return
    
    # 确认迁移
    response = input("确定要开始数据库迁移吗？(y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("迁移已取消")
        return
    
    # 执行迁移
    migrator = DatabaseMigrator()
    success = migrator.run_migration()
    
    if success:
        print("\n✅ 迁移成功完成！")
        print("\n后续步骤:")
        print("1. 更新 .env.production 文件中的数据库配置")
        print("2. 重启应用服务")
        print("3. 验证应用功能正常")
    else:
        print("\n❌ 迁移失败，请查看日志文件获取详细信息")
        print("日志文件: migration.log")

if __name__ == '__main__':
    main()