# Phase 4: Python ETL Pipeline

This module extracts data from the S3 staging bucket, applies cleaning and business logic, and loads it into the data warehouse (PostgreSQL).

## Features
- Extracts all CSV files from the S3 staging bucket
- Cleans and deduplicates data
- Loads data into warehouse tables (one table per file)
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

## Extending
- Add more cleaning, validation, or transformation logic in `transform()`
- Add error handling, logging, or notification as needed

---
See the main project [README](../../README.md) for architecture and phase details.
