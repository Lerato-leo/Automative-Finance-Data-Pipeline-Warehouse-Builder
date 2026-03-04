-- Phase 7: Performance Optimization

-- 1) Indexes for common warehouse query patterns
CREATE INDEX IF NOT EXISTS idx_fact_sales_sale_date
    ON warehouse.fact_sales (sale_date);

CREATE INDEX IF NOT EXISTS idx_fact_sales_customer_key
    ON warehouse.fact_sales (customer_key);

CREATE INDEX IF NOT EXISTS idx_fact_sales_dealer_key
    ON warehouse.fact_sales (dealer_key);

CREATE INDEX IF NOT EXISTS idx_fact_payments_payment_date
    ON warehouse.fact_payments (payment_date);

CREATE INDEX IF NOT EXISTS idx_fact_payments_sale_id
    ON warehouse.fact_payments (sale_id);

CREATE INDEX IF NOT EXISTS idx_fact_interactions_interaction_date
    ON warehouse.fact_interactions (interaction_date);

CREATE INDEX IF NOT EXISTS idx_fact_telemetry_timestamp
    ON warehouse.fact_telemetry ("timestamp");

CREATE INDEX IF NOT EXISTS idx_dim_customer_current
    ON warehouse.dim_customer (customer_id, is_current);

CREATE INDEX IF NOT EXISTS idx_dim_vehicle_current
    ON warehouse.dim_vehicle (vin, is_current);

-- 2) Partitioned table templates (date-based) for large facts
CREATE TABLE IF NOT EXISTS warehouse.fact_sales_partitioned (
    sales_key BIGINT NOT NULL,
    sale_id VARCHAR(50) NOT NULL,
    sale_date DATE NOT NULL,
    customer_key INT,
    vehicle_key INT,
    dealer_key INT,
    sale_price NUMERIC(12,2),
    discount_amount NUMERIC(12,2),
    final_price NUMERIC(12,2),
    sale_channel VARCHAR(50),
    sale_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (sales_key, sale_date)
) PARTITION BY RANGE (sale_date);

CREATE TABLE IF NOT EXISTS warehouse.fact_payments_partitioned (
    payment_key BIGINT NOT NULL,
    payment_id VARCHAR(50) NOT NULL,
    sale_id VARCHAR(50),
    payment_date DATE NOT NULL,
    payment_amount NUMERIC(12,2),
    payment_method VARCHAR(50),
    payment_status VARCHAR(50),
    transaction_reference VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (payment_key, payment_date)
) PARTITION BY RANGE (payment_date);

-- Current/next monthly partitions (extend with db_admin.py command)
CREATE TABLE IF NOT EXISTS warehouse.fact_sales_2026_02
    PARTITION OF warehouse.fact_sales_partitioned
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

CREATE TABLE IF NOT EXISTS warehouse.fact_sales_2026_03
    PARTITION OF warehouse.fact_sales_partitioned
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');

CREATE TABLE IF NOT EXISTS warehouse.fact_payments_2026_02
    PARTITION OF warehouse.fact_payments_partitioned
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

CREATE TABLE IF NOT EXISTS warehouse.fact_payments_2026_03
    PARTITION OF warehouse.fact_payments_partitioned
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');

-- 3) Table compression hints (TOAST compression for large text fields)
DO $$
BEGIN
    BEGIN
        EXECUTE 'ALTER TABLE warehouse.fact_interactions ALTER COLUMN notes SET COMPRESSION lz4';
    EXCEPTION WHEN OTHERS THEN
        EXECUTE 'ALTER TABLE warehouse.fact_interactions ALTER COLUMN notes SET COMPRESSION pglz';
    END;
END $$;

ANALYZE warehouse.fact_sales;
ANALYZE warehouse.fact_payments;
ANALYZE warehouse.fact_interactions;
ANALYZE warehouse.fact_telemetry;
