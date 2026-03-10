# Data Warehouse Schema Documentation

## Overview

The Automotive Finance warehouse uses a layered design built around staging ingestion, curated warehouse tables, operational metadata, and run-level monitoring.

## Logical Layers

```text
RAW files in S3
  -> staging.stg_* tables
  -> warehouse.fact_* and dim_* targets
  -> metadata and monitoring support tables
```

## Staging Layer

The Phase 4 ETL loads source-aligned data into staging tables before downstream warehouse modeling and validation.

| Table | Purpose | Primary Business Key |
|------|---------|----------------------|
| `staging.stg_sales` | ERP sales landing table | `sale_id` |
| `staging.stg_payments` | Payment events and settlements | `payment_id` |
| `staging.stg_interactions` | CRM interactions and service activity | `interaction_id` |
| `staging.stg_inventory` | Inventory snapshots and movement records | `inventory_id` |
| `staging.stg_procurement` | Procurement and supplier order data | `procurement_id` |
| `staging.stg_telemetry` | Vehicle or device telemetry data | `telemetry_id` |
| `staging.stg_customers` | Customer reference data | `customer_id` |
| `staging.stg_dealers` | Dealer reference data | `dealer_id` |
| `staging.stg_vehicles` | Vehicle master data | `vehicle_id` |
| `staging.stg_suppliers` | Supplier reference data | `supplier_id` |

## Warehouse Layer

The modeled warehouse supports reporting and analytics against finance, customer, and operational domains.

### Dimensions

| Table | Purpose | Grain |
|------|---------|-------|
| `warehouse.dim_customers` | Customer master and slowly changing attributes | One row per current or historical customer version |
| `warehouse.dim_products` | Product and vehicle-related product reference data | One row per product version |
| `warehouse.dim_date` | Calendar analysis dimension | One row per calendar date |
| `warehouse.dim_region` | Sales and geographic analysis dimension | One row per region |

### Facts

| Table | Purpose | Grain |
|------|---------|-------|
| `warehouse.fact_sales` | Commercial sales activity | One row per sale event or order line |
| `warehouse.fact_payments` | Payment settlement and method analytics | One row per payment event |
| `warehouse.fact_interactions` | Customer interaction metrics | One row per interaction |
| `warehouse.fact_inventory` | Inventory reporting support | One row per tracked inventory record |
| `warehouse.fact_procurement` | Procurement and supplier spend analysis | One row per procurement record |
| `warehouse.fact_telemetry` | Telemetry readings for analytical use | One row per telemetry event |

## Operational Support Tables

| Table | Purpose |
|------|---------|
| `metadata.*` | ETL run metadata and administrative tracking used by pipeline components |
| `pipeline_metrics` | Phase 8 run-level monitoring records written by the Airflow DAG |

## Data Quality Controls

The ETL applies validation before loading warehouse targets.

- required-column checks
- duplicate detection
- null checks on critical columns
- source-to-target schema alignment
- task failure on validation errors so Airflow run state reflects data-quality issues

## Monitoring Fields in `pipeline_metrics`

| Column | Meaning |
|------|---------|
| `pipeline_name` | Name of the monitored pipeline |
| `dag_id` | Airflow DAG identifier |
| `files_processed` | Number of files handled in the run |
| `rows_loaded` | Number of rows loaded by ETL |
| `processing_time_seconds` | End-to-end DAG runtime |
| `status` | Run outcome such as `SUCCESS` or `FAILED` |
| `run_timestamp` | Logical run timestamp persisted for trend analysis |

## Query Starting Points

```sql
SELECT *
FROM pipeline_metrics
ORDER BY run_timestamp DESC
LIMIT 20;

SELECT COUNT(*)
FROM staging.stg_sales;

SELECT COUNT(*)
FROM warehouse.fact_sales;
```