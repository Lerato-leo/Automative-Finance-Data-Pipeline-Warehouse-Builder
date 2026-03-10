-- Phase 7 - Maintenance, compression, and execution-plan review queries.

DROP FUNCTION IF EXISTS pg_temp.explain_query_if_valid(TEXT, TEXT, BOOLEAN);
DROP FUNCTION IF EXISTS pg_temp.set_table_option_if_exists(TEXT, TEXT, TEXT);
DROP FUNCTION IF EXISTS pg_temp.first_existing_column(TEXT, TEXT, TEXT[]);
DROP FUNCTION IF EXISTS pg_temp.column_exists(TEXT, TEXT, TEXT);
DROP FUNCTION IF EXISTS pg_temp.table_exists(TEXT, TEXT);

CREATE OR REPLACE FUNCTION pg_temp.table_exists(
    schema_name TEXT,
    relation_name TEXT
) RETURNS BOOLEAN
LANGUAGE sql
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM pg_class c
        JOIN pg_namespace n
            ON n.oid = c.relnamespace
        WHERE n.nspname = schema_name
          AND c.relname = relation_name
          AND c.relkind IN ('r', 'p', 'm')
    );
$$;

CREATE OR REPLACE FUNCTION pg_temp.column_exists(
    schema_name TEXT,
    relation_name TEXT,
    column_name TEXT
) RETURNS BOOLEAN
LANGUAGE sql
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM pg_attribute a
        JOIN pg_class c
            ON c.oid = a.attrelid
        JOIN pg_namespace n
            ON n.oid = c.relnamespace
        WHERE n.nspname = schema_name
          AND c.relname = relation_name
          AND a.attname = column_name
          AND a.attnum > 0
          AND NOT a.attisdropped
    );
$$;

CREATE OR REPLACE FUNCTION pg_temp.first_existing_column(
    schema_name TEXT,
    relation_name TEXT,
    candidate_columns TEXT[]
) RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    candidate_column TEXT;
BEGIN
    FOREACH candidate_column IN ARRAY candidate_columns LOOP
        IF pg_temp.column_exists(schema_name, relation_name, candidate_column) THEN
            RETURN candidate_column;
        END IF;
    END LOOP;

    RETURN NULL;
END;
$$;

CREATE OR REPLACE FUNCTION pg_temp.set_table_option_if_exists(
    schema_name TEXT,
    relation_name TEXT,
    ddl TEXT
) RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    IF pg_temp.table_exists(schema_name, relation_name) THEN
        EXECUTE ddl;
    ELSE
        RAISE NOTICE 'Skipping %.% because the table does not exist', schema_name, relation_name;
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION pg_temp.explain_query_if_valid(
    section_name TEXT,
    query_sql TEXT,
    can_run BOOLEAN
) RETURNS TABLE(section TEXT, plan TEXT)
LANGUAGE plpgsql
AS $$
DECLARE
    plan_row RECORD;
BEGIN
    IF NOT can_run THEN
        RETURN QUERY SELECT section_name, 'SKIPPED: required tables or columns are missing';
        RETURN;
    END IF;

    FOR plan_row IN EXECUTE format('EXPLAIN (ANALYZE, BUFFERS) %s', query_sql)
    LOOP
        section := section_name;
        plan := plan_row."QUERY PLAN";
        RETURN NEXT;
    END LOOP;
END;
$$;

-- Compression for large text columns where PostgreSQL supports TOAST compression.
DO $$
BEGIN
    IF pg_temp.column_exists('warehouse', 'fact_interactions', 'notes') THEN
        BEGIN
            EXECUTE 'ALTER TABLE warehouse.fact_interactions ALTER COLUMN notes SET COMPRESSION lz4';
        EXCEPTION WHEN OTHERS THEN
            BEGIN
                EXECUTE 'ALTER TABLE warehouse.fact_interactions ALTER COLUMN notes SET COMPRESSION pglz';
            EXCEPTION WHEN OTHERS THEN
                RAISE NOTICE 'Compression change skipped for warehouse.fact_interactions.notes';
            END;
        END;
    ELSE
        RAISE NOTICE 'Skipping compression for warehouse.fact_interactions.notes because the column does not exist';
    END IF;

    IF pg_temp.column_exists('warehouse', 'fact_payments', 'transaction_reference') THEN
        BEGIN
            EXECUTE 'ALTER TABLE warehouse.fact_payments ALTER COLUMN transaction_reference SET COMPRESSION lz4';
        EXCEPTION WHEN OTHERS THEN
            BEGIN
                EXECUTE 'ALTER TABLE warehouse.fact_payments ALTER COLUMN transaction_reference SET COMPRESSION pglz';
            EXCEPTION WHEN OTHERS THEN
                RAISE NOTICE 'Compression change skipped for warehouse.fact_payments.transaction_reference';
            END;
        END;
    ELSE
        RAISE NOTICE 'Skipping compression for warehouse.fact_payments.transaction_reference because the column does not exist';
    END IF;
END $$;

-- Autovacuum tuning for the busiest warehouse tables.
SELECT pg_temp.set_table_option_if_exists(
    'warehouse',
    'fact_sales',
    'ALTER TABLE warehouse.fact_sales SET (autovacuum_vacuum_scale_factor = 0.05, autovacuum_analyze_scale_factor = 0.02)'
);

SELECT pg_temp.set_table_option_if_exists(
    'warehouse',
    'fact_payments',
    'ALTER TABLE warehouse.fact_payments SET (autovacuum_vacuum_scale_factor = 0.05, autovacuum_analyze_scale_factor = 0.02)'
);

SELECT pg_temp.set_table_option_if_exists(
    'warehouse',
    'fact_interactions',
    'ALTER TABLE warehouse.fact_interactions SET (autovacuum_vacuum_scale_factor = 0.05, autovacuum_analyze_scale_factor = 0.02)'
);

SELECT pg_temp.set_table_option_if_exists(
    'warehouse',
    'fact_procurement',
    'ALTER TABLE warehouse.fact_procurement SET (autovacuum_vacuum_scale_factor = 0.05, autovacuum_analyze_scale_factor = 0.02)'
);

SELECT pg_temp.set_table_option_if_exists(
    'warehouse',
    'fact_telemetry',
    'ALTER TABLE warehouse.fact_telemetry SET (autovacuum_vacuum_scale_factor = 0.03, autovacuum_analyze_scale_factor = 0.01)'
);

-- Routine maintenance.
SELECT format('VACUUM ANALYZE %I.%I;', schemaname, relname) AS vacuum_command
FROM pg_stat_user_tables
WHERE (schemaname = 'warehouse' AND relname IN (
        'fact_sales',
        'fact_payments',
        'fact_interactions',
        'fact_procurement',
        'fact_telemetry'
    ))
   OR (schemaname = 'staging' AND relname IN (
        'staging_payments',
        'staging_interactions',
        'staging_procurement',
        'staging_telemetry'
    ))
ORDER BY schemaname, relname;

-- Query execution-plan analysis examples.
DO $$
DECLARE
    payments_date_column TEXT;
    interactions_date_column TEXT;
    telemetry_time_column TEXT;
    telemetry_vehicle_column TEXT;
BEGIN
    payments_date_column := pg_temp.first_existing_column(
        'warehouse',
        'fact_payments',
        ARRAY['payment_date', 'transaction_date', 'created_at']
    );

    interactions_date_column := pg_temp.first_existing_column(
        'warehouse',
        'fact_interactions',
        ARRAY['interaction_date', 'timestamp', 'created_at']
    );

    telemetry_time_column := pg_temp.first_existing_column(
        'warehouse',
        'fact_telemetry',
        ARRAY['telemetry_timestamp', 'timestamp', 'created_at']
    );

    telemetry_vehicle_column := pg_temp.first_existing_column(
        'warehouse',
        'fact_telemetry',
        ARRAY['vehicle_key', 'telemetry_id']
    );

    RAISE NOTICE 'maintenance payments date column: %', payments_date_column;
    RAISE NOTICE 'maintenance interactions date column: %', interactions_date_column;
    RAISE NOTICE 'maintenance telemetry time column: %', telemetry_time_column;
    RAISE NOTICE 'maintenance telemetry grouping column: %', telemetry_vehicle_column;
END $$;

SELECT *
FROM pg_temp.explain_query_if_valid(
    'fact_payments_daily_rollup',
    format(
        'SELECT %1$I, COUNT(*) AS payment_count, SUM(payment_amount) AS total_payment_amount FROM warehouse.fact_payments WHERE %1$I >= CURRENT_DATE - INTERVAL ''90 days'' GROUP BY %1$I ORDER BY %1$I DESC',
        pg_temp.first_existing_column('warehouse', 'fact_payments', ARRAY['payment_date', 'transaction_date', 'created_at'])
    ),
    pg_temp.first_existing_column('warehouse', 'fact_payments', ARRAY['payment_date', 'transaction_date', 'created_at']) IS NOT NULL
    AND pg_temp.column_exists('warehouse', 'fact_payments', 'payment_amount')
);

SELECT *
FROM pg_temp.explain_query_if_valid(
    'fact_interactions_customer_join',
    format(
        'SELECT fi.%1$I, COUNT(*) AS interaction_count FROM warehouse.fact_interactions fi JOIN warehouse.dim_customer dc ON dc.customer_key = fi.customer_key WHERE dc.customer_id IS NOT NULL AND fi.%1$I >= CURRENT_DATE - INTERVAL ''30 days'' GROUP BY fi.%1$I ORDER BY fi.%1$I DESC',
        pg_temp.first_existing_column('warehouse', 'fact_interactions', ARRAY['interaction_date', 'timestamp', 'created_at'])
    ),
    pg_temp.first_existing_column('warehouse', 'fact_interactions', ARRAY['interaction_date', 'timestamp', 'created_at']) IS NOT NULL
    AND pg_temp.column_exists('warehouse', 'fact_interactions', 'customer_key')
    AND pg_temp.column_exists('warehouse', 'dim_customer', 'customer_key')
    AND pg_temp.column_exists('warehouse', 'dim_customer', 'customer_id')
);

SELECT *
FROM pg_temp.explain_query_if_valid(
    'fact_telemetry_recent_vehicle_stats',
    format(
        'SELECT ft.%1$I, MAX(ft.%2$I) AS latest_event, AVG(ft.speed) AS avg_speed FROM warehouse.fact_telemetry ft WHERE ft.%2$I >= NOW() - INTERVAL ''7 days'' GROUP BY ft.%1$I ORDER BY latest_event DESC',
        pg_temp.first_existing_column('warehouse', 'fact_telemetry', ARRAY['vehicle_key', 'telemetry_id']),
        pg_temp.first_existing_column('warehouse', 'fact_telemetry', ARRAY['telemetry_timestamp', 'timestamp', 'created_at'])
    ),
    pg_temp.first_existing_column('warehouse', 'fact_telemetry', ARRAY['vehicle_key', 'telemetry_id']) IS NOT NULL
    AND pg_temp.first_existing_column('warehouse', 'fact_telemetry', ARRAY['telemetry_timestamp', 'timestamp', 'created_at']) IS NOT NULL
    AND pg_temp.column_exists('warehouse', 'fact_telemetry', 'speed')
);
