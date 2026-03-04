CREATE SCHEMA IF NOT EXISTS admin;

CREATE TABLE IF NOT EXISTS admin.table_growth_history (
    id BIGSERIAL PRIMARY KEY,
    captured_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    table_schema TEXT NOT NULL,
    table_name TEXT NOT NULL,
    table_size_bytes BIGINT NOT NULL,
    total_size_bytes BIGINT NOT NULL,
    estimated_rows BIGINT
);

CREATE TABLE IF NOT EXISTS admin.query_plan_history (
    id BIGSERIAL PRIMARY KEY,
    captured_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    query_name TEXT NOT NULL,
    execution_plan JSONB NOT NULL,
    total_cost NUMERIC,
    plan_rows BIGINT,
    plan_width BIGINT
);

CREATE TABLE IF NOT EXISTS admin.backup_history (
    id BIGSERIAL PRIMARY KEY,
    executed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    backup_file TEXT NOT NULL,
    backup_size_bytes BIGINT,
    backup_status TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS admin.query_performance_history (
    id BIGSERIAL PRIMARY KEY,
    captured_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    query_name TEXT NOT NULL,
    execution_ms NUMERIC NOT NULL,
    rows_returned BIGINT NOT NULL
);
