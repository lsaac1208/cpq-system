#!/usr/bin/env python3
"""
Database Migration Runner for CPQ System
Executes SQL migration files in order.
"""

import os
import sys
import logging
from datetime import datetime

# Optional PostgreSQL import
try:
    import psycopg2
    from psycopg2 import sql
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection - supports SQLite, MySQL, PostgreSQL."""
    try:
        # Check for SQLite first (default for this project)
        database_url = os.getenv('DATABASE_URL', 'sqlite:///cpq_system.db')
        
        if database_url.startswith('sqlite:'):
            # SQLite connection
            import sqlite3
            db_path = database_url.replace('sqlite:///', '').replace('sqlite://', '')
            if not os.path.isabs(db_path):
                # Relative path - make it relative to the script directory
                db_path = os.path.join(os.path.dirname(__file__), db_path)
            logger.info(f"Connecting to SQLite database: {db_path}")
            return sqlite3.connect(db_path)
            
        elif database_url.startswith('mysql:'):
            # MySQL connection
            try:
                import mysql.connector
                from urllib.parse import urlparse
                parsed = urlparse(database_url)
                return mysql.connector.connect(
                    host=parsed.hostname,
                    port=parsed.port or 3306,
                    database=parsed.path[1:],  # Remove leading /
                    user=parsed.username,
                    password=parsed.password
                )
            except ImportError:
                logger.error("MySQL connector not available - install mysql-connector-python")
                return None
            
        elif database_url.startswith('postgresql:'):
            # PostgreSQL connection
            if not POSTGRES_AVAILABLE:
                logger.error("PostgreSQL adapter not available - install psycopg2")
                return None
            return psycopg2.connect(database_url)
            
        else:
            logger.error(f"Unsupported database URL: {database_url}")
            return None
            
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def create_migrations_table(conn):
    """Create migrations tracking table if it doesn't exist."""
    cursor = conn.cursor()
    try:
        # SQLite syntax (compatible with most databases)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                migration_name TEXT NOT NULL UNIQUE,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        logger.info("Schema migrations table ready")
    except Exception as e:
        logger.error(f"Failed to create migrations table: {e}")
        raise
    finally:
        cursor.close()

def get_applied_migrations(conn):
    """Get list of already applied migrations."""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT migration_name FROM schema_migrations")
        applied = [row[0] for row in cursor.fetchall()]
        return set(applied)
    except Exception as e:
        logger.error(f"Error fetching applied migrations: {e}")
        return set()
    finally:
        cursor.close()

def apply_migration(conn, migration_file):
    """Apply a single migration file."""
    migration_name = os.path.basename(migration_file)
    logger.info(f"Applying migration: {migration_name}")
    
    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        cursor = conn.cursor()
        
        # Execute the SQL
        cursor.execute(sql_content)
        
        # Record the migration (use appropriate placeholder for database)
        database_url = os.getenv('DATABASE_URL', 'sqlite:///cpq_system.db')
        if database_url.startswith('sqlite:'):
            cursor.execute(
                "INSERT INTO schema_migrations (migration_name) VALUES (?)",
                (migration_name,)
            )
        else:
            cursor.execute(
                "INSERT INTO schema_migrations (migration_name) VALUES (%s)",
                (migration_name,)
            )
        
        conn.commit()
        logger.info(f"✅ Successfully applied: {migration_name}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Failed to apply {migration_name}: {e}")
        raise
    finally:
        cursor.close()

def run_migrations():
    """Run all pending migrations."""
    migrations_dir = os.path.join(os.path.dirname(__file__), 'scripts', 'migrations')
    
    if not os.path.exists(migrations_dir):
        logger.error(f"Migrations directory not found: {migrations_dir}")
        return False
    
    # Get database connection
    conn = get_db_connection()
    if not conn:
        logger.error("Could not connect to database")
        return False
    
    try:
        # Setup migrations tracking
        create_migrations_table(conn)
        applied = get_applied_migrations(conn)
        
        # Get all migration files
        migration_files = []
        for filename in os.listdir(migrations_dir):
            if filename.endswith('.sql'):
                migration_files.append(os.path.join(migrations_dir, filename))
        
        # Sort by filename (should be numbered)
        migration_files.sort()
        
        # Apply pending migrations
        pending_count = 0
        for migration_file in migration_files:
            migration_name = os.path.basename(migration_file)
            
            if migration_name not in applied:
                apply_migration(conn, migration_file)
                pending_count += 1
            else:
                logger.info(f"⏭️  Skipping already applied: {migration_name}")
        
        if pending_count == 0:
            logger.info("🎉 No pending migrations - database is up to date")
        else:
            logger.info(f"🎉 Successfully applied {pending_count} migrations")
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False
        
    finally:
        conn.close()

if __name__ == '__main__':
    success = run_migrations()
    sys.exit(0 if success else 1)