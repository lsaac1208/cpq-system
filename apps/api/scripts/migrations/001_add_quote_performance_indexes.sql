-- Performance optimization indexes for quote queries
-- Migration: 001_add_quote_performance_indexes.sql

-- Single quotes performance indexes
CREATE INDEX IF NOT EXISTS idx_quotes_created_by ON quotes(created_by);
CREATE INDEX IF NOT EXISTS idx_quotes_created_at ON quotes(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_quotes_status ON quotes(status);
CREATE INDEX IF NOT EXISTS idx_quotes_customer_email ON quotes(customer_email);

-- Composite index for common query patterns
CREATE INDEX IF NOT EXISTS idx_quotes_user_status_date 
ON quotes(created_by, status, created_at DESC);

-- Full-text search index for customer information
CREATE INDEX IF NOT EXISTS idx_quotes_search_gin 
ON quotes USING gin(to_tsvector('english', 
    COALESCE(customer_name, '') || ' ' || 
    COALESCE(customer_email, '') || ' ' || 
    COALESCE(customer_company, '') || ' ' ||
    COALESCE(quote_number, '')
));

-- Multi-quotes performance indexes
CREATE INDEX IF NOT EXISTS idx_multi_quotes_created_by ON multi_quotes(created_by);
CREATE INDEX IF NOT EXISTS idx_multi_quotes_created_at ON multi_quotes(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_multi_quotes_status ON multi_quotes(status);
CREATE INDEX IF NOT EXISTS idx_multi_quotes_customer_email ON multi_quotes(customer_email);

-- Composite index for multi-quotes common query patterns
CREATE INDEX IF NOT EXISTS idx_multi_quotes_user_status_date 
ON multi_quotes(created_by, status, created_at DESC);

-- Full-text search index for multi-quotes customer information
CREATE INDEX IF NOT EXISTS idx_multi_quotes_search_gin 
ON multi_quotes USING gin(to_tsvector('english', 
    COALESCE(customer_name, '') || ' ' || 
    COALESCE(customer_email, '') || ' ' || 
    COALESCE(customer_company, '') || ' ' ||
    COALESCE(quote_number, '')
));

-- Performance monitoring queries
-- You can use these to check index usage:
-- SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch 
-- FROM pg_stat_user_indexes WHERE tablename IN ('quotes', 'multi_quotes');

COMMIT;