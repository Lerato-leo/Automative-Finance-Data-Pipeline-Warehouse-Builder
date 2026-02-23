-- ============================================================
-- PHASE 1: Staging Schema DDL (Automotive Finance)
-- Raw tables for initial S3 data loads
-- ============================================================

-- Staging Payments
CREATE TABLE staging.stg_payments (
    payment_id VARCHAR(50),
    sale_id VARCHAR(50),
    payment_date VARCHAR(50),
    payment_amount VARCHAR(50),
    payment_method VARCHAR(50),
    payment_status VARCHAR(50),
    transaction_reference VARCHAR(100),
    created_at VARCHAR(50)
);

-- Staging Inventory
CREATE TABLE staging.stg_inventory (
    inventory_id VARCHAR(50),
    vehicle_id VARCHAR(50),
    dealer_id VARCHAR(50),
    quantity VARCHAR(50),
    stock_status VARCHAR(50),
    last_updated VARCHAR(50)
);

-- Staging Suppliers
CREATE TABLE staging.stg_suppliers (
    supplier_id VARCHAR(50),
    supplier_name VARCHAR(255),
    country VARCHAR(100),
    contact_email VARCHAR(255),
    supplier_type VARCHAR(50),
    status VARCHAR(50)
);

-- Staging Interactions
CREATE TABLE staging.stg_interactions (
    interaction_id VARCHAR(50),
    customer_id VARCHAR(50),
    interaction_type VARCHAR(50),
    interaction_channel VARCHAR(50),
    interaction_date VARCHAR(50),
    dealer_id VARCHAR(50),
    employee_id VARCHAR(50),
    outcome VARCHAR(50),
    notes TEXT
);

-- Staging Telemetry
CREATE TABLE staging.stg_telemetry (
    telemetry_id VARCHAR(50),
    vehicle_id VARCHAR(50),
    timestamp VARCHAR(50),
    speed VARCHAR(50),
    fuel_level VARCHAR(50),
    engine_temperature VARCHAR(50),
    location_lat VARCHAR(50),
    location_long VARCHAR(50)
);

-- Staging ERP/Sales (example)

-- Staging Sales (ERP)
CREATE TABLE staging.stg_sales (
    sale_id VARCHAR(50),
    sale_date VARCHAR(50),
    customer_id VARCHAR(50),
    vehicle_id VARCHAR(50),
    dealer_id VARCHAR(50),
    sale_price VARCHAR(50),
    discount_amount VARCHAR(50),
    final_price VARCHAR(50),
    sale_channel VARCHAR(50),
    sale_status VARCHAR(50),
    created_at VARCHAR(50)
);

-- Staging Customers (ERP)
CREATE TABLE staging.stg_customers (
    customer_id VARCHAR(50),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(50),
    date_of_birth VARCHAR(50),
    gender VARCHAR(20),
    street_number VARCHAR(20),
    street_name VARCHAR(100),
    suburb VARCHAR(100),
    city VARCHAR(100),
    province VARCHAR(50),
    postal_code VARCHAR(20),
    country VARCHAR(50),
    created_at VARCHAR(50),
    status VARCHAR(20)
);

-- Staging Vehicles (ERP)
CREATE TABLE staging.stg_vehicles (
    vehicle_id VARCHAR(50),
    vin VARCHAR(50),
    make VARCHAR(50),
    model VARCHAR(50),
    year VARCHAR(10),
    color VARCHAR(20),
    engine_type VARCHAR(20),
    transmission VARCHAR(20),
    manufacture_country VARCHAR(50),
    manufacture_date VARCHAR(50),
    status VARCHAR(20),
    created_at VARCHAR(50)
);

-- Staging Dealers (ERP)
CREATE TABLE staging.stg_dealers (
    dealer_id VARCHAR(50),
    dealer_name VARCHAR(255),
    dealer_code VARCHAR(50),
    street_number VARCHAR(20),
    street_name VARCHAR(100),
    city VARCHAR(100),
    province VARCHAR(50),
    postal_code VARCHAR(20),
    country VARCHAR(50),
    phone VARCHAR(50),
    email VARCHAR(255),
    dealer_type VARCHAR(50),
    status VARCHAR(20),
    created_at VARCHAR(50)
);

-- Staging Procurement (Suppliers)
CREATE TABLE staging.stg_procurement (
    procurement_id VARCHAR(50),
    supplier_id VARCHAR(50),
    vehicle_id VARCHAR(50),
    cost_price VARCHAR(50),
    procurement_date VARCHAR(50),
    status VARCHAR(50)
);
