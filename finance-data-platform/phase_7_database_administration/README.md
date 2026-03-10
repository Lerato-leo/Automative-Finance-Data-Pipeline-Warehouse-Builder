# 🗄️ Phase 7: Database Administration

## Overview

Phase 7 now provides the exact PostgreSQL administration deliverables required for this project: warehouse performance optimization SQL, backup and restore procedures, health monitoring queries, and PgBouncer connection pooling guidance.

## Requirement Fit Analysis

### What the requirement asked for

- warehouse performance optimization
- backup and recovery automation
- database health monitoring
- PgBouncer connection pooling guidance

### How this phase now matches it

- `sql/create_indexes.sql` creates practical indexes for the current warehouse and staging access paths.
- `sql/partition_tables.sql` prepares PostgreSQL RANGE partitioning for the largest time-based warehouse facts.
- `sql/maintenance_tasks.sql` covers `VACUUM`, `ANALYZE`, compression settings, and execution-plan review queries.
- `sql/monitoring_queries.sql` provides table growth, slow-query, execution-statistics, and connection-monitoring queries.
- `scripts/backup_warehouse.sh` creates daily logical backups with optional S3 upload to the archive bucket.
- `docs/restore_procedure.md` documents restore testing and recovery steps using `psql`.
- `docs/connection_pooling.md` documents how Airflow and ETL should connect through PgBouncer.

## Schema Mapping Used

The requirement names logical tables such as `payments_table` and `sensor_data_table`. The actual project schema uses warehouse fact tables and staging tables instead, so Phase 7 maps the requirement onto the real database objects already used in this repo:

- `payments_table` → `warehouse.fact_payments` and `staging.staging_payments`
- `interactions_table` → `warehouse.fact_interactions` and `staging.staging_interactions`
- `orders_table` → `warehouse.fact_sales`
- `suppliers_table` → `warehouse.fact_procurement`, `warehouse.dim_supplier`, and `staging.staging_procurement`
- `sensor_data_table` → `warehouse.fact_telemetry` and `staging.staging_telemetry`

## Deliverables

```text
phase_7_database_administration/
├── sql/
│   ├── create_indexes.sql
│   ├── partition_tables.sql
│   ├── maintenance_tasks.sql
│   └── monitoring_queries.sql
├── scripts/
│   └── backup_warehouse.sh
├── docs/
│   ├── restore_procedure.md
│   └── connection_pooling.md
└── README.md
```

## Usage

```bash
# 1. Apply index strategy to the existing live schema
psql "$DATABASE_URL_EXTERNAL" -f sql/create_indexes.sql

# 2. Prepare partitioned warehouse tables after confirming the source fact tables exist
psql "$DATABASE_URL_EXTERNAL" -f sql/partition_tables.sql

# 3. Run maintenance settings and review plan-analysis queries
psql "$DATABASE_URL_EXTERNAL" -f sql/maintenance_tasks.sql

# 4. Run monitoring queries interactively
psql "$DATABASE_URL_EXTERNAL" -f sql/monitoring_queries.sql

# 5. Create a backup
bash scripts/backup_warehouse.sh
```

## Recommended Run Order

1. Run `sql/create_indexes.sql` first.
2. Run `sql/partition_tables.sql` second.
3. Run `sql/maintenance_tasks.sql` third.
4. Run `sql/monitoring_queries.sql` after the structural changes are in place.
5. Run `scripts/backup_warehouse.sh` once you are satisfied with the warehouse state.

`partition_tables.sql` now auto-detects the live time column for warehouse payments and telemetry facts. If the live database uses `timestamp` or `created_at` instead of `telemetry_timestamp`, the script will adapt instead of failing.

## Purpose In The Platform

- improves query performance for the warehouse used by downstream analytics
- prepares operational backup and restore processes for the PostgreSQL warehouse
- provides monitoring queries for DB growth, query performance, and connections
- documents the connection-pooling path for Airflow and ETL workloads

---

**Status:** ✅ Implemented  
**Last Updated:** March 10, 2026
