-- ============================================================
-- PHASE 1: Warehouse Star Schema DDL (Automotive Finance)
-- Only schema definitions, no data inserts
-- ============================================================

-- Date Dimension
CREATE TABLE warehouse.dim_date (
    date_key SERIAL PRIMARY KEY,
    date_actual DATE NOT NULL UNIQUE,
    year INT,
    quarter INT,
    month INT,
    day INT,
    day_of_week INT,
    is_weekend BOOLEAN
);

-- Customer Dimension (SCD Type 2)
CREATE TABLE warehouse.dim_customer (
    customer_key SERIAL PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    customer_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip VARCHAR(20),
    effective_date DATE NOT NULL,
    expiry_date DATE,
    is_current BOOLEAN DEFAULT TRUE,
    CONSTRAINT uq_customer_scd UNIQUE (customer_id, effective_date)
);

-- Vehicle Dimension (SCD Type 2)
CREATE TABLE warehouse.dim_vehicle (
    vehicle_key SERIAL PRIMARY KEY,
    vin VARCHAR(50) NOT NULL,
    make VARCHAR(100),
    model VARCHAR(100),
    year INT,
    color VARCHAR(50),
    effective_date DATE NOT NULL,
    expiry_date DATE,
    is_current BOOLEAN DEFAULT TRUE,
    CONSTRAINT uq_vehicle_scd UNIQUE (vin, effective_date)
);

-- Dealer Dimension
CREATE TABLE warehouse.dim_dealer (
    dealer_key SERIAL PRIMARY KEY,
    dealer_id VARCHAR(50) NOT NULL,
    dealer_name VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    country VARCHAR(50)
);

-- Supplier Dimension
CREATE TABLE warehouse.dim_supplier (
    supplier_key SERIAL PRIMARY KEY,
    supplier_id VARCHAR(50) NOT NULL,
    supplier_name VARCHAR(255),
    country VARCHAR(100),
    contact_email VARCHAR(255),
    supplier_type VARCHAR(50),
    status VARCHAR(50)
);


-- Fact Payments Table
CREATE TABLE warehouse.fact_payments (
    payment_key SERIAL PRIMARY KEY,
    payment_id VARCHAR(50) NOT NULL,
    sale_id VARCHAR(50),
    payment_date DATE,
    payment_amount NUMERIC(12,2),
    payment_method VARCHAR(50),
    payment_status VARCHAR(50),
    transaction_reference VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fact Sales Table
CREATE TABLE warehouse.fact_sales (
    sales_key SERIAL PRIMARY KEY,
    sale_id VARCHAR(50) NOT NULL,
    sale_date DATE,
    customer_key INT REFERENCES warehouse.dim_customer(customer_key),
    vehicle_key INT REFERENCES warehouse.dim_vehicle(vehicle_key),
    dealer_key INT REFERENCES warehouse.dim_dealer(dealer_key),
    sale_price NUMERIC(12,2),
    discount_amount NUMERIC(12,2),
    final_price NUMERIC(12,2),
    sale_channel VARCHAR(50),
    sale_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fact Procurement Table
CREATE TABLE warehouse.fact_procurement (
    procurement_key SERIAL PRIMARY KEY,
    procurement_id VARCHAR(50) NOT NULL,
    supplier_key INT REFERENCES warehouse.dim_supplier(supplier_key),
    vehicle_key INT REFERENCES warehouse.dim_vehicle(vehicle_key),
    cost_price NUMERIC(12,2),
    procurement_date DATE,
    status VARCHAR(50)
);

-- Fact Inventory Table
CREATE TABLE warehouse.fact_inventory (
    inventory_key SERIAL PRIMARY KEY,
    inventory_id VARCHAR(50) NOT NULL,
    vehicle_key INT REFERENCES warehouse.dim_vehicle(vehicle_key),
    dealer_key INT REFERENCES warehouse.dim_dealer(dealer_key),
    quantity INT,
    stock_status VARCHAR(50),
    last_updated DATE
);

-- Fact Interactions Table
CREATE TABLE warehouse.fact_interactions (
    interaction_key SERIAL PRIMARY KEY,
    interaction_id VARCHAR(50) NOT NULL,
    customer_key INT REFERENCES warehouse.dim_customer(customer_key),
    dealer_key INT REFERENCES warehouse.dim_dealer(dealer_key),
    employee_id VARCHAR(50),
    interaction_type VARCHAR(50),
    interaction_channel VARCHAR(50),
    interaction_date DATE,
    outcome VARCHAR(50),
    notes TEXT
);

-- Fact Telemetry Table
CREATE TABLE warehouse.fact_telemetry (
    telemetry_key SERIAL PRIMARY KEY,
    telemetry_id VARCHAR(50) NOT NULL,
    vehicle_key INT REFERENCES warehouse.dim_vehicle(vehicle_key),
    timestamp TIMESTAMP,
    speed INT,
    fuel_level INT,
    engine_temperature INT,
    location_lat NUMERIC(8,4),
    location_long NUMERIC(8,4)
);
