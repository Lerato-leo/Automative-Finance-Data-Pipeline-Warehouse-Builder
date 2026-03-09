-- ============================================================
-- PHASE 1-4: WAREHOUSE ERD DDL (AUTOMOTIVE FINANCE)
-- Complete star schema aligned to source generators + ETL
-- Database: PostgreSQL
-- ============================================================

-- ----------------------------------------------------------------
-- SCHEMAS
-- ----------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS warehouse;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS metadata;

SET search_path TO warehouse, analytics, metadata;

-- ----------------------------------------------------------------
-- DIMENSIONS
-- ----------------------------------------------------------------

-- Date dimension
CREATE TABLE IF NOT EXISTS warehouse.dim_date (
    date_key BIGSERIAL PRIMARY KEY,
    date_actual DATE NOT NULL UNIQUE,
    year SMALLINT NOT NULL,
    quarter SMALLINT NOT NULL CHECK (quarter BETWEEN 1 AND 4),
    month SMALLINT NOT NULL CHECK (month BETWEEN 1 AND 12),
    day SMALLINT NOT NULL CHECK (day BETWEEN 1 AND 31),
    day_of_week SMALLINT NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
    is_weekend BOOLEAN NOT NULL
);

-- Customer dimension (SCD Type 2)
CREATE TABLE IF NOT EXISTS warehouse.dim_customer (
    customer_key BIGSERIAL PRIMARY KEY,
    customer_id VARCHAR(64) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    customer_name VARCHAR(220),
    email VARCHAR(255),
    phone VARCHAR(50),
    date_of_birth DATE,
    gender VARCHAR(20),
    street_number VARCHAR(20),
    street_name VARCHAR(255),
    suburb VARCHAR(100),
    city VARCHAR(100),
    province VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100),
    status VARCHAR(50),
    effective_date DATE NOT NULL,
    expiry_date DATE,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP,
    CONSTRAINT uq_dim_customer_scd UNIQUE (customer_id, effective_date),
    CONSTRAINT ck_dim_customer_dates CHECK (expiry_date IS NULL OR expiry_date >= effective_date)
);

-- Dealer dimension
CREATE TABLE IF NOT EXISTS warehouse.dim_dealer (
    dealer_key BIGSERIAL PRIMARY KEY,
    dealer_id VARCHAR(64) NOT NULL UNIQUE,
    dealer_name VARCHAR(255),
    dealer_code VARCHAR(50),
    dealer_type VARCHAR(50),
    location VARCHAR(150),
    contact_name VARCHAR(100),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    phone VARCHAR(50),
    email VARCHAR(255),
    street_number VARCHAR(20),
    street_name VARCHAR(255),
    city VARCHAR(100),
    province VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100),
    status VARCHAR(50),
    created_at TIMESTAMP
);

-- Vehicle dimension (SCD Type 2)
CREATE TABLE IF NOT EXISTS warehouse.dim_vehicle (
    vehicle_key BIGSERIAL PRIMARY KEY,
    vehicle_id VARCHAR(64),
    vin VARCHAR(64) NOT NULL,
    make VARCHAR(100),
    model VARCHAR(100),
    year SMALLINT,
    color VARCHAR(50),
    engine_type VARCHAR(50),
    transmission VARCHAR(50),
    manufacture_country VARCHAR(100),
    manufacture_date DATE,
    status VARCHAR(50),
    effective_date DATE NOT NULL,
    expiry_date DATE,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP,
    CONSTRAINT uq_dim_vehicle_scd UNIQUE (vin, effective_date),
    CONSTRAINT ck_dim_vehicle_year CHECK (year IS NULL OR year BETWEEN 1980 AND 2100),
    CONSTRAINT ck_dim_vehicle_dates CHECK (expiry_date IS NULL OR expiry_date >= effective_date)
);

-- Supplier dimension
CREATE TABLE IF NOT EXISTS warehouse.dim_supplier (
    supplier_key BIGSERIAL PRIMARY KEY,
    supplier_id VARCHAR(64) NOT NULL UNIQUE,
    supplier_name VARCHAR(255),
    country VARCHAR(100),
    contact_email VARCHAR(255),
    supplier_type VARCHAR(50),
    status VARCHAR(50),
    created_at TIMESTAMP
);

-- ----------------------------------------------------------------
-- FACT TABLES
-- ----------------------------------------------------------------

-- Sales fact
CREATE TABLE IF NOT EXISTS warehouse.fact_sales (
    sales_key BIGSERIAL PRIMARY KEY,
    sale_id VARCHAR(64) NOT NULL UNIQUE,
    sale_date DATE,
    sale_date_key BIGINT REFERENCES warehouse.dim_date(date_key),
    customer_key BIGINT REFERENCES warehouse.dim_customer(customer_key),
    vehicle_key BIGINT REFERENCES warehouse.dim_vehicle(vehicle_key),
    dealer_key BIGINT REFERENCES warehouse.dim_dealer(dealer_key),
    sale_price NUMERIC(14,2),
    discount_amount NUMERIC(14,2) DEFAULT 0,
    final_price NUMERIC(14,2),
    sale_channel VARCHAR(50),
    sale_status VARCHAR(50),
    payment_method VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_fact_sales_price CHECK (sale_price IS NULL OR sale_price >= 0),
    CONSTRAINT ck_fact_sales_discount CHECK (discount_amount IS NULL OR discount_amount >= 0),
    CONSTRAINT ck_fact_sales_final_price CHECK (final_price IS NULL OR final_price >= 0)
);

-- Payments fact
CREATE TABLE IF NOT EXISTS warehouse.fact_payments (
    payment_key BIGSERIAL PRIMARY KEY,
    payment_id VARCHAR(64) NOT NULL UNIQUE,
    sale_id VARCHAR(64),
    sales_key BIGINT REFERENCES warehouse.fact_sales(sales_key),
    payment_date DATE,
    payment_date_key BIGINT REFERENCES warehouse.dim_date(date_key),
    payment_amount NUMERIC(14,2),
    payment_method VARCHAR(50),
    payment_status VARCHAR(50),
    transaction_reference VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_fact_payments_amount CHECK (payment_amount IS NULL OR payment_amount >= 0)
);

-- Procurement fact
CREATE TABLE IF NOT EXISTS warehouse.fact_procurement (
    procurement_key BIGSERIAL PRIMARY KEY,
    procurement_id VARCHAR(64) NOT NULL UNIQUE,
    procurement_date DATE,
    procurement_date_key BIGINT REFERENCES warehouse.dim_date(date_key),
    supplier_key BIGINT REFERENCES warehouse.dim_supplier(supplier_key),
    vehicle_key BIGINT REFERENCES warehouse.dim_vehicle(vehicle_key),
    cost_price NUMERIC(14,2),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_fact_procurement_cost CHECK (cost_price IS NULL OR cost_price >= 0)
);

-- Inventory fact
CREATE TABLE IF NOT EXISTS warehouse.fact_inventory (
    inventory_key BIGSERIAL PRIMARY KEY,
    inventory_id VARCHAR(64) NOT NULL UNIQUE,
    inventory_date DATE,
    inventory_date_key BIGINT REFERENCES warehouse.dim_date(date_key),
    vehicle_key BIGINT REFERENCES warehouse.dim_vehicle(vehicle_key),
    dealer_key BIGINT REFERENCES warehouse.dim_dealer(dealer_key),
    quantity INT,
    stock_status VARCHAR(50),
    last_updated DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_fact_inventory_quantity CHECK (quantity IS NULL OR quantity >= 0)
);

-- Customer interactions fact
CREATE TABLE IF NOT EXISTS warehouse.fact_interactions (
    interaction_key BIGSERIAL PRIMARY KEY,
    interaction_id VARCHAR(64) NOT NULL UNIQUE,
    interaction_date DATE,
    interaction_date_key BIGINT REFERENCES warehouse.dim_date(date_key),
    customer_key BIGINT REFERENCES warehouse.dim_customer(customer_key),
    dealer_key BIGINT REFERENCES warehouse.dim_dealer(dealer_key),
    employee_id VARCHAR(64),
    interaction_type VARCHAR(50),
    interaction_channel VARCHAR(50),
    outcome VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Telemetry fact
CREATE TABLE IF NOT EXISTS warehouse.fact_telemetry (
    telemetry_key BIGSERIAL PRIMARY KEY,
    telemetry_id VARCHAR(64) NOT NULL UNIQUE,
    vehicle_key BIGINT REFERENCES warehouse.dim_vehicle(vehicle_key),
    telemetry_timestamp TIMESTAMP,
    telemetry_date_key BIGINT REFERENCES warehouse.dim_date(date_key),
    speed INT,
    fuel_level INT,
    engine_temperature INT,
    location_lat NUMERIC(9,6),
    location_long NUMERIC(9,6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_fact_telemetry_speed CHECK (speed IS NULL OR speed BETWEEN 0 AND 350),
    CONSTRAINT ck_fact_telemetry_fuel CHECK (fuel_level IS NULL OR fuel_level BETWEEN 0 AND 100),
    CONSTRAINT ck_fact_telemetry_temp CHECK (engine_temperature IS NULL OR engine_temperature BETWEEN -50 AND 250)
);

-- ----------------------------------------------------------------
-- INDEXES (ERD RELATION + PERFORMANCE)
-- ----------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_dim_customer_customer_id_current
    ON warehouse.dim_customer (customer_id, is_current);

CREATE INDEX IF NOT EXISTS idx_dim_vehicle_vin_current
    ON warehouse.dim_vehicle (vin, is_current);

CREATE INDEX IF NOT EXISTS idx_fact_sales_sale_date
    ON warehouse.fact_sales (sale_date);

CREATE INDEX IF NOT EXISTS idx_fact_sales_customer_key
    ON warehouse.fact_sales (customer_key);

CREATE INDEX IF NOT EXISTS idx_fact_sales_vehicle_key
    ON warehouse.fact_sales (vehicle_key);

CREATE INDEX IF NOT EXISTS idx_fact_sales_dealer_key
    ON warehouse.fact_sales (dealer_key);

CREATE INDEX IF NOT EXISTS idx_fact_payments_sale_id
    ON warehouse.fact_payments (sale_id);

CREATE INDEX IF NOT EXISTS idx_fact_payments_sales_key
    ON warehouse.fact_payments (sales_key);

CREATE INDEX IF NOT EXISTS idx_fact_procurement_supplier_key
    ON warehouse.fact_procurement (supplier_key);

CREATE INDEX IF NOT EXISTS idx_fact_inventory_dealer_vehicle
    ON warehouse.fact_inventory (dealer_key, vehicle_key);

CREATE INDEX IF NOT EXISTS idx_fact_interactions_customer_date
    ON warehouse.fact_interactions (customer_key, interaction_date);

CREATE INDEX IF NOT EXISTS idx_fact_telemetry_vehicle_timestamp
    ON warehouse.fact_telemetry (vehicle_key, telemetry_timestamp);

-- ----------------------------------------------------------------
-- OPTIONAL COMMENTS (ERD READABILITY)
-- ----------------------------------------------------------------
COMMENT ON TABLE warehouse.dim_customer IS 'Customer dimension, SCD Type 2';
COMMENT ON TABLE warehouse.dim_vehicle IS 'Vehicle dimension, SCD Type 2';
COMMENT ON TABLE warehouse.fact_sales IS 'Core sales transactions fact';
COMMENT ON TABLE warehouse.fact_payments IS 'Payments linked to sales';
COMMENT ON TABLE warehouse.fact_telemetry IS 'IoT telemetry fact at event grain';
