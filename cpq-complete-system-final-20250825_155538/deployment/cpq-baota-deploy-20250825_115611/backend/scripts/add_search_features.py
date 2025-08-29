#!/usr/bin/env python3
"""
添加产品搜索功能的数据库迁移脚本
- 创建搜索相关表
- 添加产品表的搜索索引
- 插入初始搜索建议数据
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from sqlalchemy import text
from src.models import db, Product
from src.models.search import SearchLog, PopularSearch, SearchSuggestion, SearchAnalytics

# 避免配置导入错误，直接设置Flask app
from flask import Flask
from src.models import db as database

def create_simple_app():
    """创建简单的Flask应用用于数据库操作"""
    app = Flask(__name__)
    
    # 基本配置
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "instance", "cpq_system.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'dev-secret-key'
    
    # 初始化数据库
    database.init_app(app)
    
    return app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_search_indexes():
    """添加产品搜索相关索引"""
    try:
        logger.info("添加产品搜索索引...")
        
        # 为产品表添加搜索索引
        indexes = [
            # 单列索引
            "CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);",
            "CREATE INDEX IF NOT EXISTS idx_products_code ON products(code);",
            "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);",
            "CREATE INDEX IF NOT EXISTS idx_products_is_active ON products(is_active);",
            "CREATE INDEX IF NOT EXISTS idx_products_base_price ON products(base_price);",
            
            # 复合索引
            "CREATE INDEX IF NOT EXISTS idx_products_active_category ON products(is_active, category);",
            "CREATE INDEX IF NOT EXISTS idx_products_active_price ON products(is_active, base_price);",
            
            # 全文搜索索引（SQLite的FTS）
            """CREATE VIRTUAL TABLE IF NOT EXISTS products_fts USING fts5(
                name, description, category, specifications, 
                content=products, content_rowid=id
            );""",
            
            # FTS触发器 - 插入
            """CREATE TRIGGER IF NOT EXISTS products_fts_insert AFTER INSERT ON products
            BEGIN
                INSERT INTO products_fts(rowid, name, description, category, specifications) 
                VALUES (new.id, new.name, new.description, new.category, new.specifications);
            END;""",
            
            # FTS触发器 - 更新
            """CREATE TRIGGER IF NOT EXISTS products_fts_update AFTER UPDATE ON products
            BEGIN
                UPDATE products_fts SET 
                    name = new.name, 
                    description = new.description, 
                    category = new.category, 
                    specifications = new.specifications
                WHERE rowid = new.id;
            END;""",
            
            # FTS触发器 - 删除
            """CREATE TRIGGER IF NOT EXISTS products_fts_delete AFTER DELETE ON products
            BEGIN
                DELETE FROM products_fts WHERE rowid = old.id;
            END;""",
        ]
        
        for index_sql in indexes:
            try:
                db.session.execute(text(index_sql))
                logger.info(f"执行索引SQL: {index_sql[:50]}...")
            except Exception as e:
                logger.warning(f"索引创建失败 (可能已存在): {str(e)}")
        
        db.session.commit()
        logger.info("产品搜索索引添加完成")
        
    except Exception as e:
        logger.error(f"添加搜索索引失败: {str(e)}")
        db.session.rollback()
        raise

def populate_fts_table():
    """填充全文搜索表"""
    try:
        logger.info("填充全文搜索表...")
        
        # 清空FTS表
        db.session.execute(text("DELETE FROM products_fts;"))
        
        # 重新填充FTS表
        products = Product.query.filter(Product.is_active == True).all()
        
        for product in products:
            try:
                insert_sql = text("""
                INSERT INTO products_fts(rowid, name, description, category, specifications) 
                VALUES (:id, :name, :description, :category, :specifications)
                """)
                db.session.execute(insert_sql, {
                    'id': product.id,
                    'name': product.name or '',
                    'description': product.description or '',
                    'category': product.category or '',
                    'specifications': product.specifications or ''
                })
            except Exception as e:
                logger.warning(f"FTS插入产品 {product.id} 失败: {str(e)}")
        
        db.session.commit()
        logger.info(f"FTS表填充完成，处理了 {len(products)} 个产品")
        
    except Exception as e:
        logger.error(f"填充FTS表失败: {str(e)}")
        db.session.rollback()
        raise

def create_search_suggestions():
    """创建初始搜索建议"""
    try:
        logger.info("创建初始搜索建议...")
        
        # 从现有产品生成搜索建议
        products = Product.query.filter(Product.is_active == True).all()
        
        suggestions_to_add = []
        
        for product in products:
            # 产品名称建议
            if product.name and len(product.name.strip()) > 2:
                suggestions_to_add.append({
                    'term': product.name.strip(),
                    'category': product.category,
                    'source_type': 'product_name',
                    'source_id': product.id,
                    'weight': 10
                })
            
            # 产品代码建议
            if product.code and len(product.code.strip()) > 1:
                suggestions_to_add.append({
                    'term': product.code.strip(),
                    'category': product.category,
                    'source_type': 'product_code',
                    'source_id': product.id,
                    'weight': 15  # 代码权重更高
                })
        
        # 分类建议
        categories = db.session.query(Product.category).filter(
            Product.is_active == True
        ).distinct().all()
        
        for category_tuple in categories:
            category = category_tuple[0]
            if category and len(category.strip()) > 2:
                suggestions_to_add.append({
                    'term': category.strip(),
                    'category': category,
                    'source_type': 'category',
                    'weight': 5
                })
        
        # 批量插入建议（去重）
        existing_terms = set()
        existing_suggestions = SearchSuggestion.query.all()
        for suggestion in existing_suggestions:
            existing_terms.add(suggestion.term.lower())
        
        new_suggestions = []
        for suggestion_data in suggestions_to_add:
            term_lower = suggestion_data['term'].lower()
            if term_lower not in existing_terms:
                new_suggestions.append(SearchSuggestion(**suggestion_data))
                existing_terms.add(term_lower)
        
        if new_suggestions:
            for suggestion in new_suggestions:
                suggestion.save()
            
            logger.info(f"添加了 {len(new_suggestions)} 个搜索建议")
        else:
            logger.info("没有新的搜索建议需要添加")
            
    except Exception as e:
        logger.error(f"创建搜索建议失败: {str(e)}")
        db.session.rollback()
        raise

def verify_search_setup():
    """验证搜索功能设置"""
    try:
        logger.info("验证搜索功能设置...")
        
        # 检查表是否创建
        tables_to_check = ['search_logs', 'popular_searches', 'search_suggestions', 'search_analytics']
        
        for table_name in tables_to_check:
            result = db.session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"), 
                {'table_name': table_name}
            ).fetchone()
            
            if result:
                logger.info(f"✓ 表 {table_name} 存在")
            else:
                logger.warning(f"✗ 表 {table_name} 不存在")
        
        # 检查FTS表
        fts_result = db.session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='products_fts'")
        ).fetchone()
        
        if fts_result:
            logger.info("✓ FTS全文搜索表存在")
            
            # 检查FTS表记录数
            fts_count = db.session.execute(text("SELECT COUNT(*) FROM products_fts")).fetchone()[0]
            product_count = Product.query.filter(Product.is_active == True).count()
            logger.info(f"✓ FTS表记录数: {fts_count}, 活跃产品数: {product_count}")
            
        else:
            logger.warning("✗ FTS全文搜索表不存在")
        
        # 检查索引
        indexes = db.session.execute(
            text("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_products_%'")
        ).fetchall()
        
        logger.info(f"✓ 产品表索引数量: {len(indexes)}")
        for index in indexes:
            logger.info(f"  - {index[0]}")
        
        # 检查搜索建议
        suggestion_count = SearchSuggestion.query.count()
        logger.info(f"✓ 搜索建议数量: {suggestion_count}")
        
        logger.info("搜索功能设置验证完成")
        
    except Exception as e:
        logger.error(f"验证搜索设置失败: {str(e)}")
        raise

def main():
    """主函数"""
    app = create_simple_app()
    
    with app.app_context():
        try:
            logger.info("开始设置产品搜索功能...")
            
            # 创建表
            logger.info("创建搜索相关表...")
            db.create_all()
            
            # 添加索引
            add_search_indexes()
            
            # 填充FTS表
            populate_fts_table()
            
            # 创建搜索建议
            create_search_suggestions()
            
            # 验证设置
            verify_search_setup()
            
            logger.info("✅ 产品搜索功能设置完成！")
            
            # 显示使用指南
            print("\n" + "="*60)
            print("🔍 产品搜索功能已成功设置！")
            print("="*60)
            print("\n📋 API端点:")
            print("  - GET /api/v1/search/products - 产品搜索")
            print("  - GET /api/v1/search/products/suggestions - 搜索建议")
            print("  - GET /api/v1/search/products/hot - 热门搜索")
            print("  - POST /api/v1/search/products/batch - 批量搜索")
            print("  - POST /api/v1/search/products/batch/upload - 文件批量搜索")
            print("  - POST /api/v1/search/products/batch/export - 导出搜索结果")
            print("  - GET /api/v1/search/stats - 搜索统计")
            
            print(f"\n📊 当前数据:")
            print(f"  - 活跃产品: {Product.query.filter(Product.is_active == True).count()} 个")
            print(f"  - 搜索建议: {SearchSuggestion.query.count()} 个")
            print(f"  - FTS索引: 已建立")
            
            print(f"\n🚀 下一步:")
            print("  1. 重启API服务器")
            print("  2. 实现前端搜索界面")
            print("  3. 测试搜索功能")
            
        except Exception as e:
            logger.error(f"设置搜索功能失败: {str(e)}")
            return 1
    
    return 0

if __name__ == '__main__':
    exit(main())