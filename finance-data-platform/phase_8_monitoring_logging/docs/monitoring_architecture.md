# Monitoring Architecture

## Overview

Phase 8 extends the existing Automotive Finance pipeline with runtime observability instead of a separate monitoring subsystem.

## Components

- `phase_3_shell_ingestion/ingest.py`
  Emits structured file-ingestion logs for RAW → STAGING movement.
- `phase_4_python_etl/etl_main.py`
  Logs pipeline start/completion, file metadata, row counts, processing times, and data-quality metrics. Validation failures raise exceptions so Airflow marks the run as failed.
- `phase_5_airflow_orchestration/dags/automotive_finance_orchestration_dag.py`
  Captures ETL summaries, persists one run record in `pipeline_metrics`, and sends alerts for pipeline failures, data-quality failures, and SLA breaches.
- `phase_8_monitoring_logging/dashboard/monitoring_dashboard.py`
  Reads `pipeline_metrics` from PostgreSQL and presents run-level health views in Streamlit with 10-second refresh.

## Data Flow

```text
RAW S3 bucket
   ↓
Phase 3 ingestion logs
   ↓
STAGING S3 bucket
   ↓
Phase 4 ETL logs + data-quality checks
   ↓
Airflow DAG success/failure handling
   ↓
pipeline_metrics table in PostgreSQL
   ↓
Streamlit monitoring dashboard
```

## Alert Flow

- Task failure in Airflow triggers email and Teams notifications.
- Data-quality validation failure in Phase 4 surfaces as a task failure and uses the same notification path.
- Successful runs that exceed the configured SLA threshold still write a success metric row and then emit a performance-degradation alert.

## Dashboard Coverage

- success vs failure rate from `status`
- rows loaded trend from `rows_loaded`
- processing duration trend from `processing_time_seconds`
- recent pipeline runs from latest records
- files processed trend from `files_processed`