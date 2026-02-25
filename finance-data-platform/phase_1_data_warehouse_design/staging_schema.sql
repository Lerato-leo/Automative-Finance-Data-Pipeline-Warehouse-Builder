-- Automotive Finance Data Platform: Staging Schema (Fresh)
-- Created: 2026-02-24
-- All tables reflect generator scripts, S3 structure, and Excel compatibility

-- Customers
CREATE TABLE staging_customers (
    customer_id VARCHAR(64) PRIMARY KEY,
    first_name VARCHAR(64),
    last_name VARCHAR(64),
    email VARCHAR(128),
    phone VARCHAR(32),
    address VARCHAR(256),
    city VARCHAR(64),
    state VARCHAR(32),
    zip_code VARCHAR(16),
    date_of_birth DATE,
    created_at TIMESTAMP,
    is_dirty BOOLEAN DEFAULT FALSE
);

-- Dealers
CREATE TABLE staging_dealers (
    dealer_id VARCHAR(64) PRIMARY KEY,
    dealer_name VARCHAR(128),
    contact_name VARCHAR(64),
    contact_email VARCHAR(128),
    contact_phone VARCHAR(32),
    address VARCHAR(256),
    city VARCHAR(64),
    state VARCHAR(32),
    zip_code VARCHAR(16),
    created_at TIMESTAMP,
    is_dirty BOOLEAN DEFAULT FALSE
);

-- Vehicles
CREATE TABLE staging_vehicles (
    vehicle_id VARCHAR(64) PRIMARY KEY,
    vin VARCHAR(32),
    make VARCHAR(64),
    model VARCHAR(64),
    year INT,
    color VARCHAR(32),
    dealer_id VARCHAR(64),
    customer_id VARCHAR(64),
    purchase_date TIMESTAMP,
    is_dirty BOOLEAN DEFAULT FALSE
);

-- Sales
CREATE TABLE staging_sales (
    sale_id VARCHAR(64) PRIMARY KEY,
    vehicle_id VARCHAR(64),
    customer_id VARCHAR(64),
    dealer_id VARCHAR(64),
    sale_date TIMESTAMP,
    sale_price DECIMAL(18,2),
    payment_method VARCHAR(32),
    is_dirty BOOLEAN DEFAULT FALSE
);

-- Inventory
CREATE TABLE staging_inventory (
    inventory_id VARCHAR(64) PRIMARY KEY,
    dealer_id VARCHAR(64),
    vehicle_id VARCHAR(64),
    stock_date TIMESTAMP,
    quantity INT,
    is_dirty BOOLEAN DEFAULT FALSE
);

-- Payments
CREATE TABLE staging_payments (
    payment_id VARCHAR(64) PRIMARY KEY,
    sale_id VARCHAR(64),
    customer_id VARCHAR(64),
    payment_date TIMESTAMP,
    amount DECIMAL(18,2),
    payment_method VARCHAR(32),
    status VARCHAR(32),
    is_dirty BOOLEAN DEFAULT FALSE
);

-- Suppliers
CREATE TABLE staging_suppliers (
    supplier_id VARCHAR(64) PRIMARY KEY,
    supplier_name VARCHAR(128),
    contact_name VARCHAR(64),
    contact_email VARCHAR(128),
    contact_phone VARCHAR(32),
    address VARCHAR(256),
    city VARCHAR(64),
    state VARCHAR(32),
    zip_code VARCHAR(16),
    created_at TIMESTAMP,
    is_dirty BOOLEAN DEFAULT FALSE
);

-- Procurement
CREATE TABLE staging_procurement (
    procurement_id VARCHAR(64) PRIMARY KEY,
    supplier_id VARCHAR(64),
    dealer_id VARCHAR(64),
    item VARCHAR(64),
    quantity INT,
    procurement_date TIMESTAMP,
    cost DECIMAL(18,2),
    status VARCHAR(32),
    is_dirty BOOLEAN DEFAULT FALSE
);

-- Interactions (CRM)
CREATE TABLE staging_interactions (
    interaction_id VARCHAR(64) PRIMARY KEY,
    customer_id VARCHAR(64),
    dealer_id VARCHAR(64),
    interaction_type VARCHAR(32),
    interaction_date TIMESTAMP,
    notes VARCHAR(512),
    is_dirty BOOLEAN DEFAULT FALSE
);

-- Telemetry (IoT)
CREATE TABLE staging_telemetry (
    telemetry_id VARCHAR(64) PRIMARY KEY,
    vehicle_id VARCHAR(64),
    timestamp TIMESTAMP,
    sensor_type VARCHAR(32),
    sensor_value VARCHAR(64),
    location VARCHAR(128),
    is_dirty BOOLEAN DEFAULT FALSE
);

-- ETL Metadata (for tracking loads)
CREATE SCHEMA IF NOT EXISTS staging;
CREATE TABLE IF NOT EXISTS staging.etl_metadata (
    table_name VARCHAR(64) PRIMARY KEY,
    load_time TIMESTAMP,
    row_count INT
);
