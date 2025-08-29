#!/usr/bin/env python3
"""
数据库迁移脚本：添加产品图片集支持
为现有产品系统添加图片集功能，包括多图片支持、排序、主图设置等
"""

import sys
import os

# 添加项目路径到sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models import db, Product, ProductImage, ProductImageProcessingLog
from flask import Flask
from config import Config
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """创建Flask应用实例"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 初始化数据库
    db.init_app(app)
    
    return app

def create_product_image_tables():
    """创建产品图片集相关表"""
    logger.info("创建产品图片集数据表...")
    
    try:
        # 创建ProductImage和ProductImageProcessingLog表
        db.create_all()
        
        logger.info("✅ 产品图片集数据表创建成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ 创建数据表失败: {str(e)}")
        return False

def migrate_existing_images():
    """迁移现有产品的image_url到新的图片集系统"""
    logger.info("开始迁移现有产品图片...")
    
    migrated_count = 0
    failed_count = 0
    
    try:
        # 查找所有有图片的产品
        products_with_images = Product.query.filter(
            Product.image_url.isnot(None),
            Product.image_url != ''
        ).all()
        
        logger.info(f"发现 {len(products_with_images)} 个产品有图片需要迁移")
        
        for product in products_with_images:
            try:
                # 检查是否已经迁移过
                existing_image = ProductImage.query.filter_by(
                    product_id=product.id,
                    image_url=product.image_url
                ).first()
                
                if existing_image:
                    logger.info(f"产品 {product.code} 的图片已迁移过，跳过")
                    continue
                
                # 创建图片记录
                filename = product.image_url.split('/')[-1] if '/' in product.image_url else product.image_url
                
                product_image = ProductImage(
                    product_id=product.id,
                    filename=filename,
                    original_filename=filename,
                    image_url=product.image_url,
                    title=f'{product.name} - 产品图片',
                    alt_text=product.name,
                    sort_order=0,
                    is_primary=True,
                    is_active=True,
                    image_type='product'
                )
                
                product_image.save()
                
                # 确保product_image.id已生成
                db.session.flush()  # 确保获得ID
                
                if not product_image.id:
                    raise ValueError(f"Failed to generate image_id for product {product.code}")
                
                # 记录处理日志
                processing_log = ProductImageProcessingLog(
                    image_id=product_image.id,
                    operation='migration',
                    status='success',
                    parameters=f'{{"source": "legacy_image_url", "product_code": "{product.code}"}}'
                )
                processing_log.save()
                
                migrated_count += 1
                logger.info(f"✅ 成功迁移产品 {product.code} 的图片")
                
            except Exception as e:
                failed_count += 1
                logger.error(f"❌ 迁移产品 {product.code} 的图片失败: {str(e)}")
                continue
        
        logger.info(f"图片迁移完成: 成功 {migrated_count} 个，失败 {failed_count} 个")
        return migrated_count, failed_count
        
    except Exception as e:
        logger.error(f"❌ 图片迁移过程中发生错误: {str(e)}")
        return 0, 0

def verify_migration():
    """验证迁移结果"""
    logger.info("验证迁移结果...")
    
    try:
        # 统计信息
        total_products = Product.query.count()
        products_with_legacy_images = Product.query.filter(
            Product.image_url.isnot(None),
            Product.image_url != ''
        ).count()
        
        total_gallery_images = ProductImage.query.filter_by(is_active=True).count()
        products_with_gallery_images = db.session.query(ProductImage.product_id).distinct().count()
        primary_images = ProductImage.query.filter_by(is_primary=True, is_active=True).count()
        
        logger.info("=== 迁移验证结果 ===")
        logger.info(f"总产品数: {total_products}")
        logger.info(f"有旧版图片的产品数: {products_with_legacy_images}")
        logger.info(f"图片集中图片总数: {total_gallery_images}")
        logger.info(f"有图片集的产品数: {products_with_gallery_images}")
        logger.info(f"主图数量: {primary_images}")
        
        # 检查一致性
        issues = []
        if primary_images != products_with_gallery_images:
            issues.append(f"警告: 主图数量({primary_images})与有图片的产品数量({products_with_gallery_images})不匹配")
        
        # 检查是否有产品有多个主图
        products_with_multiple_primary = db.session.query(ProductImage.product_id).filter_by(
            is_primary=True, is_active=True
        ).group_by(ProductImage.product_id).having(
            db.func.count(ProductImage.id) > 1
        ).all()
        
        if products_with_multiple_primary:
            issues.append(f"警告: 发现 {len(products_with_multiple_primary)} 个产品有多个主图")
        
        if issues:
            logger.warning("发现以下问题:")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.info("✅ 迁移验证通过，无问题发现")
        
        return len(issues) == 0
        
    except Exception as e:
        logger.error(f"❌ 迁移验证失败: {str(e)}")
        return False

def create_sample_gallery_data():
    """为测试创建示例图片集数据"""
    logger.info("创建示例图片集数据...")
    
    try:
        # 获取第一个产品用于示例
        sample_product = Product.query.first()
        if not sample_product:
            logger.info("未找到产品，跳过创建示例数据")
            return
        
        # 检查是否已有图片
        existing_images = ProductImage.query.filter_by(product_id=sample_product.id).count()
        if existing_images >= 3:
            logger.info(f"产品 {sample_product.code} 已有足够的图片，跳过")
            return
        
        # 创建多张示例图片
        sample_images = [
            {
                'filename': 'sample_main.jpg',
                'title': '产品主图',
                'description': '产品的主要展示图片',
                'is_primary': True,
                'sort_order': 0,
                'image_type': 'product'
            },
            {
                'filename': 'sample_detail1.jpg',
                'title': '产品细节图1',
                'description': '产品的细节特写图片',
                'is_primary': False,
                'sort_order': 10,
                'image_type': 'detail'
            },
            {
                'filename': 'sample_detail2.jpg',
                'title': '产品细节图2',
                'description': '产品的另一个角度细节',
                'is_primary': False,
                'sort_order': 20,
                'image_type': 'detail'
            },
            {
                'filename': 'sample_usage.jpg',
                'title': '使用场景图',
                'description': '产品的实际使用场景展示',
                'is_primary': False,
                'sort_order': 30,
                'image_type': 'usage'
            }
        ]
        
        created_count = 0
        for img_data in sample_images:
            # 检查是否已存在
            existing = ProductImage.query.filter_by(
                product_id=sample_product.id,
                filename=img_data['filename']
            ).first()
            
            if existing:
                continue
            
            # 创建示例图片记录
            sample_image = ProductImage(
                product_id=sample_product.id,
                filename=img_data['filename'],
                original_filename=img_data['filename'],
                image_url=f"/api/v1/products/uploads/{img_data['filename']}",
                thumbnail_url=f"/api/v1/products/uploads/{img_data['filename'].replace('.jpg', '_thumb.jpg')}",
                title=img_data['title'],
                description=img_data['description'],
                alt_text=f"{sample_product.name} - {img_data['title']}",
                width=800,
                height=600,
                format='jpg',
                file_size=150000,  # 150KB
                sort_order=img_data['sort_order'],
                is_primary=img_data['is_primary'],
                is_active=True,
                image_type=img_data['image_type']
            )
            
            sample_image.save()
            created_count += 1
        
        logger.info(f"✅ 为产品 {sample_product.code} 创建了 {created_count} 张示例图片")
        
    except Exception as e:
        logger.error(f"❌ 创建示例数据失败: {str(e)}")

def main():
    """主函数"""
    logger.info("开始产品图片集功能迁移...")
    
    app = create_app()
    
    with app.app_context():
        # 步骤1: 创建数据表
        if not create_product_image_tables():
            logger.error("数据表创建失败，退出迁移")
            return False
        
        # 步骤2: 迁移现有图片
        migrated, failed = migrate_existing_images()
        
        # 步骤3: 验证迁移结果
        verification_passed = verify_migration()
        
        # 步骤4: 创建示例数据（可选）
        if '--create-samples' in sys.argv:
            create_sample_gallery_data()
        
        # 总结
        logger.info("=== 迁移完成总结 ===")
        logger.info(f"图片迁移: 成功 {migrated} 个，失败 {failed} 个")
        logger.info(f"验证结果: {'通过' if verification_passed else '有问题'}")
        
        if failed == 0 and verification_passed:
            logger.info("🎉 产品图片集功能迁移成功完成！")
            return True
        else:
            logger.warning("⚠️ 迁移完成，但存在一些问题，请检查日志")
            return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)