-- Performance optimization indexes for quote queries (SQLite版本)
-- Migration: 001_add_quote_performance_indexes_sqlite.sql

-- SQLite indexes for single quotes
CREATE INDEX IF NOT EXISTS idx_quotes_created_by ON quotes(created_by);
CREATE INDEX IF NOT EXISTS idx_quotes_created_at ON quotes(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_quotes_status ON quotes(status);
CREATE INDEX IF NOT EXISTS idx_quotes_customer_email ON quotes(customer_email);

-- Composite index for common query patterns (SQLite)
CREATE INDEX IF NOT EXISTS idx_quotes_user_status_date 
ON quotes(created_by, status, created_at DESC);

-- SQLite Full-text search (如果需要的话)
-- CREATE VIRTUAL TABLE IF NOT EXISTS quotes_fts USING fts5(
--     content='quotes',
--     customer_name,
--     customer_email,
--     customer_company,
--     quote_number
-- );

-- Multi-quotes performance indexes (SQLite)
CREATE INDEX IF NOT EXISTS idx_multi_quotes_created_by ON multi_quotes(created_by);
CREATE INDEX IF NOT EXISTS idx_multi_quotes_created_at ON multi_quotes(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_multi_quotes_status ON multi_quotes(status);
CREATE INDEX IF NOT EXISTS idx_multi_quotes_customer_email ON multi_quotes(customer_email);

-- Composite index for multi-quotes (SQLite)
CREATE INDEX IF NOT EXISTS idx_multi_quotes_user_status_date 
ON multi_quotes(created_by, status, created_at DESC);

-- SQLite优化设置
PRAGMA optimize;