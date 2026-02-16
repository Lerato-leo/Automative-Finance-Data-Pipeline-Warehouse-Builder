/* ============================================================
   STAGING SCHEMA — AUTOMOTIVE FINANCE WAREHOUSE
   Raw ingestion layer (no transformations)
   ============================================================ */

CREATE SCHEMA IF NOT EXISTS staging;

SET search_path TO staging;

-- ============================================================
-- VEHICLE SALES (ERP EXPORT)
-- ============================================================

CREATE TABLE IF NOT EXISTS vehicle_sales_raw (
    sale_id            VARCHAR(50),
    sale_date          DATE,
    dealer_id          VARCHAR(50),
    vehicle_id         VARCHAR(50),
    customer_id        VARCHAR(50),
    sale_price         NUMERIC(12,2),
    quantity           INT,
    payment_method     VARCHAR(50),
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- VEHICLES (MANUFACTURING)
-- ============================================================

CREATE TABLE IF NOT EXISTS vehicles_raw (
    vehicle_id        VARCHAR(50),
    model_name        VARCHAR(100),
    brand             VARCHAR(100),
    category          VARCHAR(50),
    engine_type       VARCHAR(50),
    manufacture_year  INT,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- VEHICLE COSTS
-- ============================================================

CREATE TABLE IF NOT EXISTS vehicle_costs_raw (
    vehicle_id       VARCHAR(50),
    production_cost  NUMERIC(12,2),
    logistics_cost   NUMERIC(12,2),
    total_cost       NUMERIC(12,2),
    cost_year        INT,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- DEALERS
-- ============================================================

CREATE TABLE IF NOT EXISTS dealers_raw (
    dealer_id     VARCHAR(50),
    dealer_name   VARCHAR(150),
    city          VARCHAR(100),
    province      VARCHAR(100),
    country       VARCHAR(100),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- DEALER COMMISSIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS dealer_commissions_raw (
    commission_id   VARCHAR(50),
    dealer_id       VARCHAR(50),
    sale_id         VARCHAR(50),
    commission_pct  NUMERIC(5,2),
    commission_amt  NUMERIC(12,2),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- OPERATING EXPENSES
-- ============================================================

CREATE TABLE IF NOT EXISTS operating_expenses_raw (
    expense_id     VARCHAR(50),
    expense_date   DATE,
    expense_type   VARCHAR(100),
    amount         NUMERIC(12,2),
    department     VARCHAR(100),
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- CUSTOMERS (CRM JSON FLATTENED)
-- ============================================================

CREATE TABLE IF NOT EXISTS customers_raw (
    customer_id   VARCHAR(50),
    first_name    VARCHAR(100),
    last_name     VARCHAR(100),
    gender        VARCHAR(20),
    email         VARCHAR(150),
    phone         VARCHAR(50),
    city          VARCHAR(100),
    country       VARCHAR(100),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
