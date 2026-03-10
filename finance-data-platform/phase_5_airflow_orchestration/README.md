# 🔄 Phase 5: Airflow Orchestration

**Status:** ✅ Complete  
**Runtime Role:** Schedule and coordinate the production flow from RAW bucket monitoring through Phase 3, Phase 4, archive, and final notification

## Overview

Phase 5 now uses a single production DAG named `automotive_finance_orchestration`. Airflow owns the full workflow: monitoring the raw bucket, invoking the real Phase 3 shell ingestion script, invoking the real Phase 4 ETL script, archiving processed staging files, and sending the Phase 5 completion notification.

## Completion Summary

- One canonical DAG owns the supported orchestration path.
- The DAG runs every 5 minutes and is intended to remain unpaused for automatic processing.
- Streaming and manual raw-file entry points now converge into this same orchestration layer.

## 🎯 Objective

Run one orchestration path for all entry points:
- ✅ Auto-monitor the S3 raw bucket every 5 minutes
- ✅ Execute the real Phase 3 shell ingestion flow
- ✅ Let Phase 3 send its own notifications
- ✅ Execute the real Phase 4 ETL flow from staging
- ✅ Archive processed staging files after ETL
- ✅ Send the final Phase 5 Airflow notification

## 📊 DAG Flow

```
automotive_finance_orchestration
├── monitor_raw_bucket
├── run_phase_3_shell_ingestion
├── run_phase_4_etl
├── archive_processed_staging_files
└── send_phase_5_airflow_notification
```

## 📁 Files

| File | Purpose |
|------|---------|
| `dags/automotive_finance_orchestration_dag.py` | Main orchestration DAG |
| `requirements.txt` | Airflow runtime dependencies including ETL requirements |
| `logs/` | Airflow task execution logs |
| `plugins/` | Custom Airflow plugins if needed later |

## 🚀 Usage

### View the DAG in Airflow UI

```
1. Open http://localhost:8081
2. Login to Airflow
3. Search for: automotive_finance_orchestration
4. Open the graph or grid view
```

### Trigger the DAG manually

```bash
docker exec airflow-webserver airflow dags trigger automotive_finance_orchestration
```

### Check recent runs

```bash
docker exec airflow-postgres psql -U airflow -d airflow -c \
"SELECT dag_id, state, start_date FROM dag_run WHERE dag_id='automotive_finance_orchestration' ORDER BY execution_date DESC LIMIT 5;"
```

### Inspect task logs

```bash
docker exec airflow-webserver airflow tasks logs automotive_finance_orchestration monitor_raw_bucket
docker compose logs -f airflow-scheduler
docker compose logs -f airflow-worker
```

## 🔄 Runtime Behavior

1. `monitor_raw_bucket` scans the raw bucket and records the keys found for the current run.
2. `run_phase_3_shell_ingestion` calls `phase_3_shell_ingestion/ingest.py` to move valid data from RAW to STAGING and send Phase 3 notifications.
3. `run_phase_4_etl` calls `phase_4_python_etl/etl_main.py` against the staging bucket.
4. `archive_processed_staging_files` moves the just-processed staging objects into the archive bucket.
5. `send_phase_5_airflow_notification` sends the final orchestration summary through the configured notification channels.

## 🔧 Runtime Wiring

- Airflow scheduler and worker mount the real Phase 3 and Phase 4 folders.
- The DAG normalizes both `RAW_BUCKET` and `S3_RAW_BUCKET` style variables.
- Manual and streaming helpers trigger this DAG instead of bypassing Airflow.
- The root stack builds the Airflow image as `automative-airflow:2.10.5-psycopg2`.

## 📧 Notifications

- Phase 3 notifications are sent by the Phase 3 ingestion script.
- Phase 5 notifications are sent by Airflow after ETL and archive complete.
✅ Consolidated ETL Pipeline Complete

Execution: 2026-03-09 10:05:00
Status: SUCCESS

📊 Records: 170
📦 Files: 4 archived
⏱️ Time: 95s (SLA: 300s)

✅ All tasks successful
```

## 🔧 Configuration

### Environment Variables (.env)

```bash
# AWS S3
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_RAW_BUCKET=automotive-raw-data-lerato-2026
S3_STAGING_BUCKET=automotive-staging-data-lerato-2026
S3_ARCHIVE_BUCKET=automotive-archive-data-lerato-2026

# SMTP Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_RECIPIENT=lerato.matamela01@gmail.com

# Teams Webhook
TEAMS_WEBHOOK_URL=https://outlook.webhook.office.com/webhookb2/xxxxx
```

## 📊 Monitoring

### Database Queries

```sql
-- View recent DAG runs
SELECT dag_id, state, start_date, end_date 
FROM dag_run 
WHERE dag_id='automotive_finance_orchestration'
ORDER BY execution_date DESC LIMIT 10;

-- View task execution
SELECT task_id, state, start_date, end_date
FROM task_instance
WHERE dag_id='automotive_finance_orchestration'
ORDER BY start_date DESC;

-- Success rate
SELECT state, COUNT(*) as count
FROM dag_run
WHERE dag_id='automotive_finance_orchestration'
GROUP BY state;
```

### Log Locations

```
Scheduler: docker logs airflow-scheduler
Worker: docker logs airflow-worker
Webserver: docker logs airflow-webserver
Python logs: /opt/airflow/logs/automotive_finance_orchestration/
```

## 🐛 Troubleshooting

### DAG Not Loading

```bash
# Check syntax
docker exec airflow-webserver airflow dags list | grep automotive_finance_orchestration

# Restart scheduler
docker compose restart airflow-scheduler

# View errors
docker logs airflow-scheduler 2>&1 | grep -i error
```

### Tasks Not Running

```bash
# Check worker is running
docker compose ps | grep worker

# Restart worker
docker compose restart airflow-worker

# Check task logs
docker exec airflow-webserver airflow tasks logs \
  automotive_finance_orchestration monitor_raw_bucket
```

### S3 Files Not Detected

```bash
# Verify bucket exists
aws s3 ls s3://automotive-raw-data-lerato-2026/

# Test AWS credentials
aws sts get-caller-identity

# Test S3 access from container
docker exec airflow-scheduler aws s3 ls
```

### Notifications Not Sent

```bash
# Check SMTP credentials in .env
grep SMTP_USERNAME ../.env

# Test Teams webhook manually
curl -X POST $TEAMS_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test message"}'
```

## 📈 Performance

| Metric | Value |
|--------|-------|
| Schedule | Every 5 min |
| Avg Execution | 95 seconds |
| Max Records/Run | 200+ |
| S3 Operations | ~50 MB/min |
| SLA Target | 300 seconds |

## 🔗 Related Phases

- **Phase 3:** Shell Ingestion (Task 3 validation)
- **Phase 4:** Python ETL (Task 5 transformation)
- **Phase 6:** Kafka Streaming (upstream data source)

## 📚 Resources

- [Airflow Docs](https://airflow.apache.org/docs/)
- [DAG Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html)
- [PythonOperator](https://airflow.apache.org/docs/apache-airflow/stable/howto/operator/python.html)

---

**Status:** ✅ Operational  
**Last Updated:** March 10, 2026  
**DAG:** `automotive_finance_orchestration_dag.py`  
**Schedule:** Every 5 minutes  
**Tasks:** 5 (all implemented)

