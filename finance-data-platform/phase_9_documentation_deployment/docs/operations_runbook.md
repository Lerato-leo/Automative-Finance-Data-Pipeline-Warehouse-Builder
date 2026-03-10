# Operations Runbook

## Daily Start Checks

```bash
docker compose ps
docker compose logs --tail 50 airflow-scheduler
docker compose logs --tail 50 airflow-worker
docker exec airflow-webserver airflow dags list | grep automotive_finance_orchestration
```

## Monitoring Checks

```bash
docker exec airflow-postgres psql -U airflow -d airflow -c "SELECT dag_id, state, start_date FROM dag_run WHERE dag_id='automotive_finance_orchestration' ORDER BY execution_date DESC LIMIT 10;"

psql "$DATABASE_URL_EXTERNAL" -c "SELECT * FROM pipeline_metrics ORDER BY run_timestamp DESC LIMIT 10;"
```

## Streamlit Dashboard

```bash
streamlit run finance-data-platform/phase_8_monitoring_logging/dashboard/monitoring_dashboard.py
```

Expected local URL:

- `http://localhost:8501`

## Incident: DAG Failing

1. Check the latest DAG and task states in Airflow.
2. Inspect `airflow-scheduler` and `airflow-worker` logs.
3. Inspect the failing task logs from the Airflow UI or CLI.
4. Query `pipeline_metrics` to confirm whether the run was persisted as `FAILED`.
5. If the failure is data-quality related, inspect the Phase 4 ETL logs for validation errors.

## Incident: No Files Processed

1. Check whether files exist in the raw S3 bucket.
2. Confirm AWS credentials and bucket names in `.env`.
3. Check the output of `monitor_raw_bucket` in the latest DAG run.
4. If Kafka ingestion is expected, confirm the producer and consumer are running.

## Incident: Dashboard Empty

1. Confirm the `pipeline_metrics` table exists in the warehouse.
2. Confirm at least one DAG run has completed since Phase 8 was enabled.
3. Validate DB connection variables used by the dashboard process.

## Backup and Recovery

Phase 7 owns backup and restore operations. Use the documented procedures in:

- `phase_7_database_administration/docs/restore_procedure.md`
- `phase_7_database_administration/scripts/backup_warehouse.sh`

## Deployment Smoke Test

Run these checks after any deployment:

```bash
docker compose config > /dev/null
docker exec airflow-webserver airflow db migrate
docker exec airflow-webserver airflow dags list | grep automotive_finance_orchestration
curl http://localhost:8501
```

## Escalation Points

- Airflow runtime issue: scheduler, worker, or DAG import problem
- Warehouse issue: PostgreSQL connectivity, schema, or permissions
- Data-quality issue: Phase 4 ETL validation failure
- Notification issue: SMTP or Teams webhook configuration