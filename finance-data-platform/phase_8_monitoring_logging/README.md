# 📊 Phase 8: Monitoring & Logging

## Overview

Phase 8 provides monitoring, logging, and observability for the automotive finance data platform. Monitoring focuses on the single orchestration DAG, the data warehouse, and the supporting runtime services.

## What To Monitor

- `automotive_finance_orchestration` run success and duration
- Phase 3 ingestion outcomes and notification delivery
- Phase 4 ETL processing rates and data quality failures
- PostgreSQL health, storage, and connection pressure
- Container health for Airflow, Kafka, and supporting services

## Airflow Focus

```
automotive_finance_orchestration
├── monitor_raw_bucket
├── run_phase_3_shell_ingestion
├── run_phase_4_etl
├── archive_processed_staging_files
└── send_phase_5_airflow_notification
```

## Example Log Flow

```
2026-03-09T10:05:00 [INFO] [automotive_finance_orchestration] DAG START
2026-03-09T10:05:10 [INFO] [monitor_raw_bucket] Found 4 files
2026-03-09T10:05:30 [INFO] [run_phase_3_shell_ingestion] Phase 3 completed
2026-03-09T10:06:20 [INFO] [run_phase_4_etl] Phase 4 completed
2026-03-09T10:06:40 [INFO] [archive_processed_staging_files] Archived 4 files
2026-03-09T10:06:45 [INFO] [automotive_finance_orchestration] DAG SUCCESS
```

## Operational Checks

```bash
docker compose logs -f airflow-scheduler
docker compose logs -f airflow-worker
docker exec airflow-webserver airflow dags list | grep automotive_finance_orchestration
docker exec airflow-postgres psql -U airflow -d airflow -c "SELECT dag_id, state FROM dag_run ORDER BY execution_date DESC LIMIT 10;"
```

## Alerts

- DAG failure or repeated retries
- No successful run within the expected five-minute interval
- Phase 3 ingestion failures or missing notifications
- Phase 4 ETL failures or abnormal record counts
- Archive task failures leaving processed data in staging