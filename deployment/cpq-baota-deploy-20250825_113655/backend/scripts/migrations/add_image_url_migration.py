#!/usr/bin/env python3
"""
Add image_url field to products table
Migration script for CPQ system
"""

import sys
import os
import logging
from datetime import datetime

# Add the parent directory to the path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 直接使用Flask和SQLAlchemy配置，避免导入冲突
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from src.models import db

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('migration.log'),
            logging.StreamHandler()
        ]
    )

def create_app():
    """Create Flask app with database configuration"""
    app = Flask(__name__)
    
    # Basic configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cpq_system.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    return app

def add_image_url_column():
    """Add image_url column to products table"""
    logger = logging.getLogger(__name__)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Check if column already exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('products')]
            
            if 'image_url' in columns:
                logger.info("image_url column already exists in products table")
                return True
            
            # Add the column using raw SQL since it's simpler than using Flask-Migrate for this case
            with db.engine.connect() as conn:
                conn.execute(db.text("""
                    ALTER TABLE products 
                    ADD COLUMN image_url VARCHAR(255)
                """))
                conn.commit()
            
            logger.info("✅ Successfully added image_url column to products table")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add image_url column: {str(e)}")
            return False

def verify_migration():
    """Verify that the migration was successful"""
    logger = logging.getLogger(__name__)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Check if we can query the new column
            result = db.session.execute(db.text("SELECT image_url FROM products LIMIT 1"))
            logger.info("✅ Migration verification successful - image_url column is accessible")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration verification failed: {str(e)}")
            return False

def main():
    """Main migration function"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Starting image_url migration for products table")
    logger.info(f"📅 Migration timestamp: {datetime.now().isoformat()}")
    
    # Backup database first (optional but recommended)
    logger.info("💾 Consider backing up your database before running this migration")
    
    # Add the column
    if add_image_url_column():
        # Verify the migration
        if verify_migration():
            logger.info("🎉 Migration completed successfully!")
            return 0
        else:
            logger.error("❌ Migration verification failed")
            return 1
    else:
        logger.error("❌ Migration failed")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)