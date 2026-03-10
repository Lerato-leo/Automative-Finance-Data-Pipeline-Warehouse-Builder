# 🏗️ Phase 1: Data Warehouse Design

**Status:** ✅ Complete  
**Scope:** Warehouse schema, modeling conventions, fact/dimension design, and downstream transformation targets

## Overview

Phase 1 establishes the foundational design and architecture of the data warehouse for the Automotive Finance Data Pipeline. This phase focuses on schema design, entity relationships, and data modeling principles that guide all downstream phases.

## Completion Summary

- The warehouse shape for staging, dimensions, and fact tables is defined.
- Phase 4 ETL targets this design when loading curated warehouse data.
- Phase 5 orchestration and Phase 6 streaming now both feed into this modeled warehouse path.

## 🎯 Objective

Design a scalable, production-ready data warehouse that:
- ✅ Normalizes data from 6 data sources
- ✅ Supports cross-domain queries
- ✅ Enables historical tracking
- ✅ Optimizes for common access patterns
- ✅ Maintains data quality and integrity

## 📊 Warehouse Architecture

### Schema Layers

```
Raw Layer (External)
    ↓
Staging Layer (stg_*)
    ├─ stg_sales
    ├─ stg_payments
    ├─ stg_interactions
    ├─ stg_inventory
    ├─ stg_procurement
    └─ stg_telemetry
    ↓
Processing Layer (Transformations)
    ├─ Data validation (16 rules)
    ├─ Deduplication
    ├─ Reconciliation
    └─ Enrichment
    ↓
Warehouse Layer (Mart/Analytics)
    ├─ dim_customers
    ├─ dim_products
    ├─ dim_date
    ├─ dim_region
    ├─ fact_sales
    ├─ fact_payments
    └─ fact_interactions
    ↓
Access Layer (BI/Reports)
    └─ Views, cubes, dashboards
```

### Data Sources

| Source | Domain | Tables | Records | Format |
|--------|--------|--------|---------|--------|
| ERP System | Finance | Sales, Payments, General Ledger | 100K+ | CSV |
| CRM System | Customer Relationship | Contacts, Interactions, Campaigns | 50K+ | JSON |
| Inventory Mgmt | Operations | Stock, Movements, Warehouses | 30K+ | CSV |
| Purchase Orders | Procurement | POs, Vendors, Line Items | 20K+ | JSON |
| IoT Sensors | Telemetry | Device Data, Readings, Alerts | 500K+ | JSON |
| Master Data | Reference | Customers, Products, Regions | 10K+ | CSV |

## 📋 Table Structure

### Staging Tables (Direct from Source)

#### stg_sales
```
Columns: sales_id (PK), customer_id (FK), product_id (FK), order_date, 
         amount, quantity, status, created_at, updated_at
Partitioning: By month (sales_date)
Indexes: sales_id, customer_id, order_date
```

#### stg_payments
```
Columns: payment_id (PK), sales_id (FK), payment_date, amount, 
         method, status, reference, created_at
Indexes: payment_id, sales_id, payment_date
```

#### stg_interactions
```
Columns: interaction_id (PK), customer_id (FK), type, channel, 
         subject, status, timestamp, created_at
Indexes: interaction_id, customer_id, timestamp
```

#### stg_inventory
```
Columns: inventory_id (PK), product_id (FK), warehouse_id, 
         quantity_on_hand, reorder_level, last_movement_date
Indexes: inventory_id, product_id, warehouse_id
```

#### stg_procurement
```
Columns: po_id (PK), vendor_id (FK), po_date, delivery_date, 
         amount, status, created_at
Indexes: po_id, vendor_id, po_date
```

#### stg_telemetry
```
Columns: telemetry_id (PK), device_id, reading_type, reading_value, 
         timestamp, unit, status
Indexes: telemetry_id, device_id, timestamp
```

### Dimension Tables (Star Schema)

#### dim_customers
```
customer_key (PK), customer_id (natural key), name, email, 
phone, address, city, state, zip, country, 
date_of_birth, segment, created_date, effective_date, 
end_date, is_current
```

#### dim_products
```
product_key (PK), product_id (natural key), product_name, 
category, manufacturer, sku, unit_cost, list_price, 
weight, status, created_date, effective_date, end_date, is_current
```

#### dim_date
```
date_key (PK), calendar_date, year, quarter, month, day, 
day_of_week, is_weekday, is_holiday, holiday_name
```

#### dim_region
```
region_key (PK), region_id, region_name, country, 
state_province, sales_manager, created_date
```

### Fact Tables (Metrics)

#### fact_sales
```
sales_key (PK), customer_key (FK to dim_customers), 
product_key (FK to dim_products), date_key (FK to dim_date), 
region_key (FK to dim_region), order_quantity, 
order_amount, discount_amount, net_amount, tax_amount, 
total_amount, sales_status, order_date, ship_date, 
delivery_date, load_date
```

#### fact_payments
```
payment_key (PK), sales_key (FK to fact_sales), 
customer_key (FK to dim_customers), date_key (FK to dim_date), 
payment_amount, payment_method, payment_status, 
payment_date, clearing_date, load_date
```

#### fact_interactions
```
interaction_key (PK), customer_key (FK to dim_customers), 
date_key (FK to dim_date), interaction_type, interaction_channel, 
duration_minutes, satisfaction_score, agent_id, 
interaction_date, resolution_date, load_date
```

## 🔑 Data Model

### Entity-Relationship Diagram

```
Customer
    |
    ├─ 1:M ─→ Sales
    |           |
    |           ├─ 1:1 ─→ Payments
    |           └─ M:1 ─→ Products
    |
    └─ 1:M ─→ Interactions

Products
    |
    ├─ 1:M ─→ Inventory
    |           └─ M:1 ─→ Warehouse
    |
    └─ M:M ─→ PurchaseOrders
                └─ M:1 ─→ Vendors

Devices
    |
    └─ 1:M ─→ Telemetry
```

## 📐 Design Principles

### Normalization

```
Sales Table (Pre-normalized):
┌─────────────┬──────────┬──────────┬──────────┐
│ sales_id    │ cust_id  │ cust_name│ amount   │
├─────────────┼──────────┼──────────┼──────────┤
│ S001        │ C001     │ John Doe │ 1500     │
└─────────────┴──────────┴──────────┴──────────┘

↓ NORMALIZE TO

Customers Table:
┌─────────────┬──────────┐
│ customer_id │ name     │
├─────────────┼──────────┤
│ C001        │ John Doe │
└─────────────┴──────────┘

Sales Table:
┌─────────────┬──────────┬────────┐
│ sales_id    │ cust_id  │ amount │
├─────────────┼──────────┼────────┤
│ S001        │ C001     │ 1500   │
└─────────────┴──────────┴────────┘

Benefits:
✓ Reduced data redundancy
✓ Improved data consistency
✓ Easier updates
✓ Better performance for joins
```

### Slowly Changing Dimensions (SCD)

```
Type 2: Track History with Effective Dates

dim_customers:
┌──────────┬────────────┬──────────┬──────────┬────────────┐
│ cust_key │ cust_id    │ segment  │ eff_date │ end_date   │
├──────────┼────────────┼──────────┼──────────┼────────────┤
│ 1        │ C001       │ BRONZE   │ 2024-01  │ 2026-02-28 │
│ 2        │ C001       │ SILVER   │ 2026-03-01 │ NULL     │
└──────────┴────────────┴──────────┴──────────┴────────────┘

Benefits:
✓ Historical tracking
✓ Accurate point-in-time analysis
✓ Audit trail maintained
```

## 📏 Indexing Strategy

### Staging Tables (Write-Heavy)
- Primary Key: Clustered Index
- Foreign Keys: Non-clustered
- Timestamps: Non-clustered (for time-range queries)

### Dimension Tables (Read-Heavy)
- Natural Key: Non-clustered (for lookups)
- Effective Date: Non-clustered (for SCD Type 2 queries)

### Fact Tables (Large Volume)
- Foreign Keys: Clustered Index
- Date Dimension: Non-clustered (for time aggregations)

## 📊 Data Quality Rules

### 16 Validation Rules (Applied in Phase 4 ETL)

| Rule # | Table | Condition | Action |
|--------|-------|-----------|--------|
| 1 | stg_sales | amount > 0 | Flag for review |
| 2 | stg_sales | quantity > 0 | Flag for review |
| 3 | stg_payments | payment_date ≥ sales.order_date | Flag, recon |
| 4 | stg_payments | amount ≤ sales.amount | Flag for review |
| 5 | stg_customers | email valid | Quarantine |
| 6 | stg_customers | phone valid format | Quarantine |
| 7 | stg_inventory | qty_on_hand ≥ 0 | Flag for review |
| 8 | stg_inventory | qty_on_hand ≤ max_capacity | Flag for review |
| 9 | stg_interactions | duration > 0 | Flag for review |
| 10 | stg_interactions | timestamp < NOW() | Quarantine |
| 11 | stg_procurement | delivery_date ≥ po_date | Flag for review |
| 12 | stg_procurement | amount > 0 | Flag for review |
| 13 | stg_telemetry | reading_value reasonable | Flag for review |
| 14 | All | No NULL in mandatory columns | Quarantine |
| 15 | All | No duplicate keys | Quarantine |
| 16 | All | Referential integrity maintained | Alter/reject |

## 🔄 Data Lineage

### Sample ETL Flow: Sales

```
Source: ERP system (sales_extract.csv)
    ↓
1. Extract (Phase 3)
   └─ Read CSV from S3 RAW/finance/sales/
    ↓
2. Load to Staging (Phase 4)
   └─ Load → stg_sales
    ↓
3. Validate (Phase 4)
   └─ Apply 16 rules, flag issues
    ↓
4. Transform (Phase 4)
   └─ Join with customers, products
   └─ Calculate net_amount, tax
    ↓
5. Load to Warehouse (Phase 4)
   └─ Insert into fact_sales + dim tables
    ↓
6. Aggregate (Phase 5)
   └─ Create summary views
    ↓
7. Query (Phase 9)
   └─ Available to reporting tools
```

## 📈 Capacity Planning

### Storage Estimates

| Table | Records | Size | Total | Retention |
|-------|---------|------|-------|-----------|
| stg_sales | 100K/month | 500 KB | 6 GB/year | 12 months |
| stg_payments | 80K/month | 400 KB | 4.8 GB/year | 12 months |
| stg_interactions | 50K/month | 300 KB | 3.6 GB/year | 12 months |
| stg_inventory | 30K | 200 KB | 2.4 GB | Current state |
| stg_procurement | 20K/month | 150 KB | 1.8 GB/year | 12 months |
| stg_telemetry | 500K/month | 5 MB | 60 GB/year | 6 months |
| **Total** | - | - | **~78 GB/year** | - |

### Query Performance Targets

| Type | Target | Notes |
|------|--------|-------|
| Fact table scan (1M rows) | <2 seconds | With indexes |
| Dimension lookup (10K rows) | <100ms | PK lookup |
| Cross-table join (fact + 3 dims) | <5 seconds | Optimized indexes |
| Aggregation (MONTH, SUM) | <3 seconds | Pre-aggregated views |

## 🔐 Data Governance

### Access Control

```
Finance Team
  ├─ READ: stg_sales, stg_payments, fact_sales, fact_payments
  └─ WRITE: dim_date, reference data only

Operations Team
  ├─ READ: stg_inventory, stg_procurement, fact_inventory
  └─ WRITE: dim_warehouse, dim_vendor

BI / Analytics
  ├─ READ: ALL fact & dim tables, views
  └─ WRITE: Aggregates, summary tables

IT Admin
  ├─ FULL: All tables
  └─ MANAGE: Backups, maintenance, indexes
```

### Audit Trail

```
audit_log table:
  audit_id (PK)
  table_name
  operation (INSERT, UPDATE, DELETE)
  user_id
  old_values
  new_values
  timestamp
  
Triggers: Automatic logging on all fact/dim tables
Retention: 7 years (regulatory)
Archival: Annual roll to cold storage
```

## 🚀 Implementation Checklist

- [ ] Define all table schemas (staging, dimensions, facts)
- [ ] Create PostgreSQL database and schemas
- [ ] Implement primary keys and constraints
- [ ] Create clustered indexes on fact tables
- [ ] Create non-clustered indexes on dimensions
- [ ] Implement slowly changing dimensions
- [ ] Create audit tables and triggers
- [ ] Define data quality rules (16 rules)
- [ ] Load reference (dimension) data
- [ ] Create materialized views for common queries
- [ ] Document all table relationships
- [ ] Test query performance
- [ ] Validate capacity planning estimates

## 🔗 Related Phases

- **Phase 2:** Data Source Setup (configure connections to 6 sources)
- **Phase 3:** Shell Ingestion (extract raw files)
- **Phase 4:** Python ETL (validate and transform per design)
- **Phase 8:** Database Administration (manage and monitor)

## 📚 Resources

- [Star Schema Design](https://www.kimballgroup.com/data-warehouse-business-intelligence/)
- [Slowly Changing Dimensions](https://en.wikipedia.org/wiki/Slowly_changing_dimension)
- [Kimball Method](https://www.kimballgroup.com/)
- [PostgreSQL Design](https://www.postgresql.org/docs/current/ddl.html)

---

**Status:** ✅ Design Complete  
**Last Updated:** March 9, 2026  
**Tables:** 12 (6 staging + 4 dimensions + 3 facts)  
**Records:** 650K+/month  
**Storage:** ~78 GB/year
