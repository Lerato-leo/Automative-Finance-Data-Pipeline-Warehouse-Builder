# Phase 4: Python ETL Pipeline

This module extracts data from the S3 staging bucket (CSV, JSON, XLSX), applies cleaning and business logic, and loads it into the data warehouse (PostgreSQL staging schema).

## Features
- Extracts all CSV, JSON, and XLSX files from the S3 staging bucket
- Cleans, deduplicates, and normalizes data (handles nulls, whitespace, email normalization, title casing)
- Loads data into warehouse staging tables (one table per entity)
- Supports incremental and full loads, upserts, and ETL metadata tracking
- Modular: add more business logic in the `transform()` function

## Usage
1. Set environment variables:
   - `STAGING_BUCKET` (default: automotive-staging-data-lerato-2026)
   - `WAREHOUSE_CONN` (Postgres connection string)
2. Install dependencies:
   - `pip install boto3 pandas psycopg2`
3. Run the ETL pipeline:
   ```
   python etl_main.py
   ```

## Problems Faced & Fixes
- **Missing Tables/Columns:**
  - Created all required staging tables and columns in PostgreSQL using an updated schema.
  - Added missing `date_of_birth` column to `staging_customers`.
  - Created `staging.etl_metadata` table for ETL tracking.
- **Pandas 3 Compatibility:**
  - Updated code to handle both `object` and `string` dtypes for string operations.
- **Schema Mismatches:**
  - Ensured ETL logic matches the latest warehouse schema and generator outputs.
- **Execution Errors:**
  - Ensured ETL is always run from the correct directory and with the correct Python environment.

## Extending
- Add more cleaning, validation, or transformation logic in `transform()`
- Add error handling, logging, or notification as needed

---
See the main project [README](../../README.md) for architecture and phase details.
