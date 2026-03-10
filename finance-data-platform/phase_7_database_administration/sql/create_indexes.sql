-- Phase 7 - Create indexes for the PostgreSQL warehouse used by this project.
--
-- Requirement-to-schema mapping:
-- payments_table      -> warehouse.fact_payments / staging.staging_payments
-- interactions_table  -> warehouse.fact_interactions / staging.staging_interactions
-- orders_table        -> warehouse.fact_sales
-- suppliers_table     -> warehouse.fact_procurement / warehouse.dim_supplier / staging.staging_procurement
-- sensor_data_table   -> warehouse.fact_telemetry / staging.staging_telemetry

CREATE OR REPLACE FUNCTION pg_temp.run_if_columns_exist(
    schema_name TEXT,
    relation_name TEXT,
    required_columns TEXT[],
    ddl TEXT
) RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    missing_columns TEXT[];
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = schema_name
                    AND table_name = relation_name
    ) THEN
                RAISE NOTICE 'Skipping %.% because the table does not exist', schema_name, relation_name;
        RETURN;
    END IF;

    SELECT array_agg(required_column)
    INTO missing_columns
    FROM unnest(required_columns) AS required_column
    WHERE NOT EXISTS (
        SELECT 1
        FROM information_schema.columns c
        WHERE c.table_schema = schema_name
                    AND c.table_name = relation_name
          AND c.column_name = required_column
    );

    IF missing_columns IS NOT NULL THEN
                RAISE NOTICE 'Skipping %.% because required columns are missing: %', schema_name, relation_name, missing_columns;
        RETURN;
    END IF;

    EXECUTE ddl;
END;
$$;

-- Customer-driven access paths
SELECT pg_temp.run_if_columns_exist(
    'warehouse',
    'dim_customer',
    ARRAY['customer_id', 'is_current'],
    'CREATE INDEX IF NOT EXISTS idx_dim_customer_customer_id_current ON warehouse.dim_customer (customer_id, is_current)'
);

SELECT pg_temp.run_if_columns_exist(
    'staging',
    'staging_payments',
    ARRAY['customer_id', 'payment_date'],
    'CREATE INDEX IF NOT EXISTS idx_staging_payments_customer_payment_date ON staging.staging_payments (customer_id, payment_date)'
);

SELECT pg_temp.run_if_columns_exist(
    'staging',
    'staging_interactions',
    ARRAY['customer_id', 'interaction_date'],
    'CREATE INDEX IF NOT EXISTS idx_staging_interactions_customer_interaction_date ON staging.staging_interactions (customer_id, interaction_date)'
);

-- Date-driven access paths
SELECT pg_temp.run_if_columns_exist(
    'warehouse',
    'fact_sales',
    ARRAY['sale_date'],
    'CREATE INDEX IF NOT EXISTS idx_fact_sales_sale_date ON warehouse.fact_sales (sale_date)'
);

SELECT pg_temp.run_if_columns_exist(
    'warehouse',
    'fact_payments',
    ARRAY['payment_date'],
    'CREATE INDEX IF NOT EXISTS idx_fact_payments_payment_date ON warehouse.fact_payments (payment_date)'
);

SELECT pg_temp.run_if_columns_exist(
    'warehouse',
    'fact_interactions',
    ARRAY['interaction_date'],
    'CREATE INDEX IF NOT EXISTS idx_fact_interactions_interaction_date ON warehouse.fact_interactions (interaction_date)'
);

SELECT pg_temp.run_if_columns_exist(
    'staging',
    'staging_procurement',
    ARRAY['procurement_date'],
    'CREATE INDEX IF NOT EXISTS idx_staging_procurement_procurement_date ON staging.staging_procurement (procurement_date)'
);

SELECT pg_temp.run_if_columns_exist(
    'staging',
    'staging_telemetry',
    ARRAY['timestamp'],
    'CREATE INDEX IF NOT EXISTS idx_staging_telemetry_timestamp ON staging.staging_telemetry ("timestamp")'
);

-- Supplier-driven access paths
SELECT pg_temp.run_if_columns_exist(
    'warehouse',
    'dim_supplier',
    ARRAY['supplier_id'],
    'CREATE INDEX IF NOT EXISTS idx_dim_supplier_supplier_id ON warehouse.dim_supplier (supplier_id)'
);

SELECT pg_temp.run_if_columns_exist(
    'warehouse',
    'fact_procurement',
    ARRAY['supplier_key', 'procurement_date'],
    'CREATE INDEX IF NOT EXISTS idx_fact_procurement_supplier_date ON warehouse.fact_procurement (supplier_key, procurement_date)'
);

SELECT pg_temp.run_if_columns_exist(
    'staging',
    'staging_procurement',
    ARRAY['supplier_id', 'procurement_date'],
    'CREATE INDEX IF NOT EXISTS idx_staging_procurement_supplier_date ON staging.staging_procurement (supplier_id, procurement_date)'
);

-- Payment and telemetry lookup paths
SELECT pg_temp.run_if_columns_exist(
    'warehouse',
    'fact_payments',
    ARRAY['sales_key'],
    'CREATE INDEX IF NOT EXISTS idx_fact_payments_sales_key ON warehouse.fact_payments (sales_key)'
);

SELECT pg_temp.run_if_columns_exist(
    'warehouse',
    'fact_payments',
    ARRAY['sale_id'],
    'CREATE INDEX IF NOT EXISTS idx_fact_payments_sale_id ON warehouse.fact_payments (sale_id)'
);

SELECT pg_temp.run_if_columns_exist(
    'warehouse',
    'fact_telemetry',
    ARRAY['vehicle_key', 'telemetry_timestamp'],
    'CREATE INDEX IF NOT EXISTS idx_fact_telemetry_vehicle_timestamp ON warehouse.fact_telemetry (vehicle_key, telemetry_timestamp)'
);

SELECT pg_temp.run_if_columns_exist(
    'warehouse',
    'fact_telemetry',
    ARRAY['telemetry_timestamp'],
    'CREATE INDEX IF NOT EXISTS idx_fact_telemetry_telemetry_timestamp ON warehouse.fact_telemetry (telemetry_timestamp)'
);

SELECT pg_temp.run_if_columns_exist(
    'staging',
    'staging_telemetry',
    ARRAY['telemetry_id', 'timestamp'],
    'CREATE INDEX IF NOT EXISTS idx_staging_telemetry_sensor_timestamp ON staging.staging_telemetry (telemetry_id, "timestamp")'
);

-- Interaction access paths
SELECT pg_temp.run_if_columns_exist(
    'warehouse',
    'fact_interactions',
    ARRAY['customer_key', 'interaction_date'],
    'CREATE INDEX IF NOT EXISTS idx_fact_interactions_customer_date ON warehouse.fact_interactions (customer_key, interaction_date)'
);
