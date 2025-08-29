#!/usr/bin/env python3
"""
简化的搜索功能数据库设置脚本
直接使用sqlite3操作数据库，避免SQLAlchemy的复杂性
"""

import sqlite3
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_path():
    """获取数据库文件路径"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    api_dir = os.path.dirname(script_dir)
    db_path = os.path.join(api_dir, 'instance', 'cpq_system.db')
    return db_path

def create_search_tables(cursor):
    """创建搜索相关表"""
    logger.info("创建搜索相关表...")
    
    tables = [
        # 搜索日志表
        """
        CREATE TABLE IF NOT EXISTS search_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            query TEXT NOT NULL,
            filters TEXT,
            result_count INTEGER DEFAULT 0,
            clicked_product_id INTEGER,
            search_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (clicked_product_id) REFERENCES products(id)
        );
        """,
        
        # 热门搜索表
        """
        CREATE TABLE IF NOT EXISTS popular_searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT UNIQUE NOT NULL,
            search_count INTEGER DEFAULT 1,
            click_count INTEGER DEFAULT 0,
            last_searched DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # 搜索建议表
        """
        CREATE TABLE IF NOT EXISTS search_suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT UNIQUE NOT NULL,
            category TEXT,
            source_type TEXT NOT NULL,
            source_id INTEGER,
            weight INTEGER DEFAULT 1,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # 搜索分析表
        """
        CREATE TABLE IF NOT EXISTS search_analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE UNIQUE NOT NULL,
            total_searches INTEGER DEFAULT 0,
            unique_users INTEGER DEFAULT 0,
            no_results_count INTEGER DEFAULT 0,
            avg_results_per_search REAL DEFAULT 0.0,
            top_categories TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
    ]
    
    for table_sql in tables:
        try:
            cursor.execute(table_sql)
            logger.info(f"创建表成功: {table_sql.split()[5]}")
        except Exception as e:
            logger.error(f"创建表失败: {str(e)}")
            raise

def create_search_indexes(cursor):
    """创建搜索索引"""
    logger.info("创建产品搜索索引...")
    
    indexes = [
        # 产品表基本索引
        "CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);",
        "CREATE INDEX IF NOT EXISTS idx_products_code ON products(code);", 
        "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);",
        "CREATE INDEX IF NOT EXISTS idx_products_is_active ON products(is_active);",
        "CREATE INDEX IF NOT EXISTS idx_products_base_price ON products(base_price);",
        
        # 复合索引
        "CREATE INDEX IF NOT EXISTS idx_products_active_category ON products(is_active, category);",
        "CREATE INDEX IF NOT EXISTS idx_products_active_price ON products(is_active, base_price);",
        
        # 搜索相关表索引
        "CREATE INDEX IF NOT EXISTS idx_search_logs_user_id ON search_logs(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_search_logs_query ON search_logs(query);",
        "CREATE INDEX IF NOT EXISTS idx_search_logs_search_time ON search_logs(search_time);",
        "CREATE INDEX IF NOT EXISTS idx_popular_searches_query ON popular_searches(query);",
        "CREATE INDEX IF NOT EXISTS idx_search_suggestions_term ON search_suggestions(term);",
        "CREATE INDEX IF NOT EXISTS idx_search_suggestions_active ON search_suggestions(is_active);",
    ]
    
    for index_sql in indexes:
        try:
            cursor.execute(index_sql)
            logger.info(f"创建索引: {index_sql.split()[5]}")
        except Exception as e:
            logger.warning(f"索引创建失败 (可能已存在): {str(e)}")

def create_fts_table(cursor):
    """创建全文搜索表"""
    logger.info("创建FTS5全文搜索表...")
    
    try:
        # 删除旧的触发器（如果存在）
        cursor.execute("DROP TRIGGER IF EXISTS products_fts_insert;")
        cursor.execute("DROP TRIGGER IF EXISTS products_fts_update;")
        cursor.execute("DROP TRIGGER IF EXISTS products_fts_delete;")
        
        # 删除旧的FTS表（如果存在）
        cursor.execute("DROP TABLE IF EXISTS products_fts;")
        
        # 创建FTS5虚拟表
        fts_sql = """
        CREATE VIRTUAL TABLE products_fts USING fts5(
            name, 
            description, 
            category, 
            specifications,
            content='products',
            content_rowid='id'
        );
        """
        cursor.execute(fts_sql)
        logger.info("✓ FTS5表创建成功")
        
        # 创建FTS触发器 - 插入
        insert_trigger = """
        CREATE TRIGGER products_fts_insert AFTER INSERT ON products 
        BEGIN
            INSERT INTO products_fts(rowid, name, description, category, specifications) 
            VALUES (new.id, new.name, COALESCE(new.description, ''), new.category, COALESCE(new.specifications, ''));
        END;
        """
        cursor.execute(insert_trigger)
        
        # 创建FTS触发器 - 更新
        update_trigger = """
        CREATE TRIGGER products_fts_update AFTER UPDATE ON products 
        BEGIN
            UPDATE products_fts SET 
                name = new.name, 
                description = COALESCE(new.description, ''), 
                category = new.category, 
                specifications = COALESCE(new.specifications, '')
            WHERE rowid = new.id;
        END;
        """
        cursor.execute(update_trigger)
        
        # 创建FTS触发器 - 删除
        delete_trigger = """
        CREATE TRIGGER products_fts_delete AFTER DELETE ON products 
        BEGIN
            DELETE FROM products_fts WHERE rowid = old.id;
        END;
        """
        cursor.execute(delete_trigger)
        
        logger.info("✓ FTS触发器创建成功")
        
    except Exception as e:
        logger.error(f"FTS表创建失败: {str(e)}")
        raise

def populate_fts_table(cursor):
    """填充FTS表"""
    logger.info("填充FTS表...")
    
    try:
        # 获取所有活跃产品
        cursor.execute("SELECT id, name, description, category, specifications FROM products WHERE is_active = 1")
        products = cursor.fetchall()
        
        logger.info(f"找到 {len(products)} 个活跃产品")
        
        # 批量插入FTS表
        for product in products:
            try:
                cursor.execute("""
                    INSERT INTO products_fts(rowid, name, description, category, specifications) 
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    product[0],  # id
                    product[1] or '',  # name
                    product[2] or '',  # description  
                    product[3] or '',  # category
                    product[4] or ''   # specifications
                ))
            except Exception as e:
                logger.warning(f"FTS插入产品 {product[0]} 失败: {str(e)}")
        
        logger.info(f"✓ FTS表填充完成，处理了 {len(products)} 个产品")
        
    except Exception as e:
        logger.error(f"填充FTS表失败: {str(e)}")
        raise

def create_search_suggestions(cursor):
    """创建初始搜索建议"""
    logger.info("创建初始搜索建议...")
    
    try:
        # 从产品名称生成建议
        cursor.execute("SELECT DISTINCT name, category FROM products WHERE is_active = 1 AND name IS NOT NULL AND LENGTH(TRIM(name)) > 2")
        names = cursor.fetchall()
        
        # 从产品代码生成建议
        cursor.execute("SELECT DISTINCT code, category FROM products WHERE is_active = 1 AND code IS NOT NULL AND LENGTH(TRIM(code)) > 1")
        codes = cursor.fetchall()
        
        # 从分类生成建议
        cursor.execute("SELECT DISTINCT category FROM products WHERE is_active = 1 AND category IS NOT NULL AND LENGTH(TRIM(category)) > 2")
        categories = cursor.fetchall()
        
        suggestions = []
        
        # 添加产品名称建议
        for name, category in names:
            suggestions.append((name.strip(), category, 'product_name', 10))
        
        # 添加产品代码建议
        for code, category in codes:
            suggestions.append((code.strip(), category, 'product_code', 15))
        
        # 添加分类建议
        for (category,) in categories:
            suggestions.append((category.strip(), category, 'category', 5))
        
        # 批量插入建议（使用INSERT OR IGNORE避免重复）
        cursor.execute("DELETE FROM search_suggestions")  # 清空旧建议
        
        for term, category, source_type, weight in suggestions:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO search_suggestions (term, category, source_type, weight)
                    VALUES (?, ?, ?, ?)
                """, (term, category, source_type, weight))
            except Exception as e:
                logger.warning(f"插入搜索建议失败: {term} - {str(e)}")
        
        logger.info(f"✓ 添加了 {len(suggestions)} 个搜索建议")
        
    except Exception as e:
        logger.error(f"创建搜索建议失败: {str(e)}")
        raise

def verify_setup(cursor):
    """验证设置结果"""
    logger.info("验证搜索功能设置...")
    
    try:
        # 检查表
        tables_to_check = ['search_logs', 'popular_searches', 'search_suggestions', 'search_analytics', 'products_fts']
        
        for table_name in tables_to_check:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if cursor.fetchone():
                logger.info(f"✓ 表 {table_name} 存在")
            else:
                logger.warning(f"✗ 表 {table_name} 不存在")
        
        # 检查FTS表记录数
        cursor.execute("SELECT COUNT(*) FROM products_fts")
        fts_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM products WHERE is_active = 1")
        product_count = cursor.fetchone()[0]
        
        logger.info(f"✓ FTS表记录数: {fts_count}, 活跃产品数: {product_count}")
        
        # 检查搜索建议
        cursor.execute("SELECT COUNT(*) FROM search_suggestions")
        suggestion_count = cursor.fetchone()[0]
        logger.info(f"✓ 搜索建议数量: {suggestion_count}")
        
        # 检查索引
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_products_%'")
        indexes = cursor.fetchall()
        logger.info(f"✓ 产品表索引数量: {len(indexes)}")
        
        logger.info("✅ 搜索功能设置验证完成")
        
    except Exception as e:
        logger.error(f"验证失败: {str(e)}")
        raise

def main():
    """主函数"""
    db_path = get_db_path()
    logger.info(f"数据库路径: {db_path}")
    
    if not os.path.exists(db_path):
        logger.error(f"数据库文件不存在: {db_path}")
        return 1
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info("🔍 开始设置产品搜索功能...")
        
        # 执行设置步骤
        create_search_tables(cursor)
        create_search_indexes(cursor)
        create_fts_table(cursor)
        populate_fts_table(cursor)
        create_search_suggestions(cursor)
        
        # 提交更改
        conn.commit()
        
        # 验证设置
        verify_setup(cursor)
        
        logger.info("✅ 产品搜索功能设置完成！")
        
        # 显示统计信息
        cursor.execute("SELECT COUNT(*) FROM products WHERE is_active = 1")
        product_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM search_suggestions")
        suggestion_count = cursor.fetchone()[0]
        
        print("\n" + "="*60)
        print("🎉 产品搜索功能已成功设置！")
        print("="*60)
        print(f"\n📊 数据统计:")
        print(f"  - 活跃产品: {product_count} 个")
        print(f"  - 搜索建议: {suggestion_count} 个")
        print(f"  - 全文搜索索引: 已建立")
        
        print(f"\n🚀 API端点:")
        print("  - GET /api/v1/search/products - 产品搜索")
        print("  - GET /api/v1/search/products/suggestions - 搜索建议")
        print("  - GET /api/v1/search/products/hot - 热门搜索")
        print("  - POST /api/v1/search/products/batch - 批量搜索")
        print("  - POST /api/v1/search/products/batch/upload - 文件批量搜索")
        
        print(f"\n📋 下一步:")
        print("  1. 重启API服务器以加载搜索路由")
        print("  2. 实现前端搜索界面")
        print("  3. 测试搜索功能")
        
    except Exception as e:
        logger.error(f"设置失败: {str(e)}")
        return 1
    finally:
        if 'conn' in locals():
            conn.close()
    
    return 0

if __name__ == '__main__':
    exit(main())