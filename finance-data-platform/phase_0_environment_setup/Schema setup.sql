-- ============================================================
-- PHASE 0: Schema Setup for Automotive Finance Warehouse
-- Database: automative_warehouse_ygg3
-- ============================================================

-- Create schemas if they don’t exist
CREATE SCHEMA IF NOT EXISTS staging;     -- Raw normalized loads
CREATE SCHEMA IF NOT EXISTS warehouse;   -- Star schema fact + dimensions
CREATE SCHEMA IF NOT EXISTS analytics;   -- BI-ready views
CREATE SCHEMA IF NOT EXISTS metadata;    -- Audit logs, ETL run history

-- Set default search path (correct syntax)
SET search_path TO staging, warehouse, analytics, metadata;

