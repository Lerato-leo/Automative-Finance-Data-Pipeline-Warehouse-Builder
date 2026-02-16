/* ============================================================
   WAREHOUSE STAR SCHEMA — AUTOMOTIVE FINANCE
   Dimensional model for executive reporting
   ============================================================ */

CREATE SCHEMA IF NOT EXISTS warehouse;

SET search_path TO warehouse;

-- ============================================================
-- DATE DIMENSION
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_date (
    date_key     INT PRIMARY KEY,
    full_date    DATE,
    year         INT,
    quarter      INT,
    month        INT,
    month_name   VARCHAR(20),
    day          INT,
    day_name     VARCHAR(20)
);

-- ============================================================
-- VEHICLE DIMENSION (SCD TYPE 2)
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_vehicle (
    vehicle_key      SERIAL PRIMARY KEY,
    vehicle_id       VARCHAR(50),
    model_name       VARCHAR(100),
    brand            VARCHAR(100),
    category         VARCHAR(50),
    engine_type      VARCHAR(50),
    manufacture_year INT,
    production_cost  NUMERIC(12,2),
    logistics_cost   NUMERIC(12,2),
    total_cost       NUMERIC(12,2),
    effective_date   DATE,
    expiry_date      DATE,
    is_current       BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- DEALER DIMENSION
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_dealer (
    dealer_key    SERIAL PRIMARY KEY,
    dealer_id     VARCHAR(50),
    dealer_name   VARCHAR(150),
    city          VARCHAR(100),
    province      VARCHAR(100),
    country       VARCHAR(100),
    effective_date DATE,
    expiry_date    DATE,
    is_current     BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- CUSTOMER DIMENSION
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_customer (
    customer_key  SERIAL PRIMARY KEY,
    customer_id   VARCHAR(50),
    first_name    VARCHAR(100),
    last_name     VARCHAR(100),
    gender        VARCHAR(20),
    city          VARCHAR(100),
    country       VARCHAR(100),
    effective_date DATE,
    expiry_date    DATE,
    is_current     BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- FACT TABLE — VEHICLE SALES
-- ============================================================

CREATE TABLE IF NOT EXISTS fact_vehicle_sales (
    sales_key         SERIAL PRIMARY KEY,
    sale_id           VARCHAR(50),

    date_key          INT,
    vehicle_key       INT,
    dealer_key        INT,
    customer_key      INT,

    quantity          INT,
    sale_price        NUMERIC(12,2),
    revenue           NUMERIC(14,2),
    production_cost   NUMERIC(14,2),
    commission_amt    NUMERIC(14,2),
    operating_expense NUMERIC(14,2),
    profit            NUMERIC(14,2),

    FOREIGN KEY (date_key)
        REFERENCES dim_date(date_key),

    FOREIGN KEY (vehicle_key)
        REFERENCES dim_vehicle(vehicle_key),

    FOREIGN KEY (dealer_key)
        REFERENCES dim_dealer(dealer_key),

    FOREIGN KEY (customer_key)
        REFERENCES dim_customer(customer_key)
);
