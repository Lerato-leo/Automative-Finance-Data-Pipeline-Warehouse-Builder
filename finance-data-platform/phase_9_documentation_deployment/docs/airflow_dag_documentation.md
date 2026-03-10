# Airflow DAG Documentation

## DAG Identity

- DAG ID: `automotive_finance_orchestration`
- Schedule: `*/5 * * * *`
- Catchup: disabled
- Runtime role: canonical orchestrator for the production pipeline

## Task Order

```text
monitor_raw_bucket
  -> run_phase_3_shell_ingestion
  -> run_phase_4_etl
  -> archive_processed_staging_files
  -> send_phase_5_airflow_notification
```

## Task Responsibilities

### `monitor_raw_bucket`

- scans the raw S3 bucket
- records the keys found for the active run in XCom
- provides the initial file count for downstream metrics

### `run_phase_3_shell_ingestion`

- runs `phase_3_shell_ingestion/ingest.py`
- validates files and moves valid objects from RAW to STAGING
- sends Phase 3 notifications
- pushes the staged object keys for the current run into XCom

### `run_phase_4_etl`

- runs `phase_4_python_etl/etl_main.py`
- processes only the staged keys associated with the current DAG run
- captures the `ETL_SUMMARY::<json>` payload from stdout
- returns row counts and quality results for monitoring persistence

### `archive_processed_staging_files`

- moves successfully processed staged files into the archive bucket
- removes them from the staging bucket after copy

### `send_phase_5_airflow_notification`

- sends final orchestration notifications
- persists a `SUCCESS` monitoring row into `pipeline_metrics`
- checks SLA duration and sends a performance alert when breached

## Failure Handling

The DAG sets `on_failure_callback=notify_on_pipeline_failure`.

On failure the callback:

- classifies the failure title
- sends email and Teams notifications
- persists a `FAILED` row in `pipeline_metrics`

## Metrics Persistence

The DAG ensures the `pipeline_metrics` table exists using the SQL file mounted from Phase 8. The payload includes:

- pipeline name
- DAG identifier
- files processed
- rows loaded
- total processing time
- run status
- logical run timestamp

## Required Runtime Mounts

The Airflow scheduler, webserver, and worker must mount:

- `phase_3_shell_ingestion`
- `phase_4_python_etl`
- `phase_8_monitoring_logging`

Without the Phase 8 mount the DAG cannot load the monitoring SQL file or shared logging helpers at runtime.

## Operational Commands

```bash
docker exec airflow-webserver airflow dags list | grep automotive_finance_orchestration
docker exec airflow-webserver airflow dags trigger automotive_finance_orchestration
docker exec airflow-postgres psql -U airflow -d airflow -c "SELECT dag_id, state, start_date FROM dag_run ORDER BY execution_date DESC LIMIT 10;"
docker compose logs -f airflow-scheduler
docker compose logs -f airflow-worker
```