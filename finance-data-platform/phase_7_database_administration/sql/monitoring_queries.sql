-- Phase 7 - Database health monitoring queries.

CREATE SCHEMA IF NOT EXISTS admin;

CREATE TABLE IF NOT EXISTS admin.table_growth_history (
    captured_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    table_schema TEXT NOT NULL,
    table_name TEXT NOT NULL,
    table_size_bytes BIGINT NOT NULL,
    total_size_bytes BIGINT NOT NULL,
    estimated_rows BIGINT,
    PRIMARY KEY (captured_at, table_schema, table_name)
);

-- 1. Table sizes and growth snapshot.
INSERT INTO admin.table_growth_history (
    table_schema,
    table_name,
    table_size_bytes,
    total_size_bytes,
    estimated_rows
)
SELECT
    schemaname,
    relname,
    pg_table_size(relid) AS table_size_bytes,
    pg_total_relation_size(relid) AS total_size_bytes,
    n_live_tup::BIGINT AS estimated_rows
FROM pg_stat_user_tables
WHERE schemaname IN ('staging', 'warehouse');

SELECT
    table_schema,
    table_name,
    pg_size_pretty(table_size_bytes) AS table_size,
    pg_size_pretty(total_size_bytes) AS total_size,
    estimated_rows,
    captured_at
FROM admin.table_growth_history
ORDER BY total_size_bytes DESC, captured_at DESC;

SELECT
    current_snap.table_schema,
    current_snap.table_name,
    current_snap.captured_at AS current_capture,
    previous_snap.captured_at AS previous_capture,
    current_snap.total_size_bytes - COALESCE(previous_snap.total_size_bytes, 0) AS growth_bytes,
    pg_size_pretty(current_snap.total_size_bytes - COALESCE(previous_snap.total_size_bytes, 0)) AS growth_pretty
FROM admin.table_growth_history current_snap
LEFT JOIN LATERAL (
    SELECT prev.*
    FROM admin.table_growth_history prev
    WHERE prev.table_schema = current_snap.table_schema
      AND prev.table_name = current_snap.table_name
      AND prev.captured_at < current_snap.captured_at
    ORDER BY prev.captured_at DESC
    LIMIT 1
) previous_snap ON TRUE
WHERE current_snap.captured_at = (
    SELECT MAX(latest.captured_at)
    FROM admin.table_growth_history latest
    WHERE latest.table_schema = current_snap.table_schema
      AND latest.table_name = current_snap.table_name
)
ORDER BY growth_bytes DESC NULLS LAST;

-- 2. Slow queries and execution statistics.
-- Enable pg_stat_statements if your PostgreSQL service allows it.
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

SELECT
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    rows,
    shared_blks_hit,
    shared_blks_read
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;

SELECT
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    rows
FROM pg_stat_statements
WHERE query ILIKE '%warehouse.%'
ORDER BY total_exec_time DESC
LIMIT 20;

-- 3. Current query activity.
SELECT
    pid,
    usename,
    application_name,
    client_addr,
    state,
    wait_event_type,
    wait_event,
    now() - query_start AS runtime,
    LEFT(query, 200) AS query_preview
FROM pg_stat_activity
WHERE datname = current_database()
  AND state <> 'idle'
ORDER BY runtime DESC;

-- 4. Database connections.
SELECT
    datname,
    usename,
    application_name,
    state,
    COUNT(*) AS connection_count
FROM pg_stat_activity
WHERE datname = current_database()
GROUP BY datname, usename, application_name, state
ORDER BY connection_count DESC;

SELECT
    current_setting('max_connections') AS max_connections,
    COUNT(*) AS current_connections,
    ROUND(COUNT(*)::numeric / NULLIF(current_setting('max_connections')::numeric, 0) * 100, 2) AS pct_used
FROM pg_stat_activity;
