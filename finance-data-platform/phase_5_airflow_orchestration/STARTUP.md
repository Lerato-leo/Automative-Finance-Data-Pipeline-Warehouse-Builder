# AIRFLOW STARTUP GUIDE
# =====================

## Prerequisites
- Docker Desktop installed and running
- AWS credentials (Access Key ID, Secret Access Key)
- S3 bucket names configured

## Step 0: Setup AWS Credentials (REQUIRED FIRST)

The Airflow services need AWS credentials to access your S3 buckets.

**1. Create .env file from template:**
```bash
cd finance-data-platform
cp .env.template .env
```

**2. Edit `.env` file and add your AWS credentials:**
```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=your_actual_access_key
AWS_SECRET_ACCESS_KEY=your_actual_secret_key
AWS_DEFAULT_REGION=us-east-1

# S3 Bucket Names (update these to match YOUR buckets)
RAW_BUCKET=automotive-raw-data-lerato-2026
STAGING_BUCKET=automotive-staging-data-lerato-2026
ARCHIVE_BUCKET=automotive-archive-data-lerato-2026
```

**3. Verify .env file is in the root directory:**
```bash
ls -la .env  # Should exist in finance-data-platform/.env
```

⚠️ **IMPORTANT**: Without this .env file, the startup script will fail.

## Step 1: Start Airflow Services

```bash
cd finance-data-platform/phase_5_airflow_orchestration
python start_airflow.py
```

This will:
✓ Start Docker containers (Postgres, Redis, Webserver, Scheduler, Worker)
✓ Initialize Airflow database
✓ Create admin user (admin/admin)
✓ Display access information

Expected output:
```
✅ Airflow Services Started!

ACCESS AIRFLOW UI:
  http://localhost:8080
  
LOGIN:
  Username: admin
  Password: admin
```

## Step 2: Access Airflow UI

Open browser: **http://localhost:8080**

Login:
- Username: `admin`
- Password: `admin`

## Step 3: Verify DAGs Appear

1. Go to DAGs view
2. Look for two DAGs:
   - `event_driven_real_time_etl` - Main ETL pipeline
   - `s3_raw_bucket_sensor_trigger` - Auto-trigger sensor

If DAGs don't appear:
```bash
# Check DAGs folder
ls -la finance-data-platform/phase_5_airflow_orchestration/dags/

# Check logs
docker compose logs webserver | grep -i dag

# Refresh UI manually
# Go to Admin → DAG Code → Click refresh
```

## Step 4: Test the Pipeline

### Option A: Manual Trigger
1. Click on `event_driven_real_time_etl` DAG
2. Click "Trigger DAG" button
3. Monitor execution in Graph View

### Option B: Auto-Trigger with Sensor
1. S3 Sensor DAG runs every minute
2. When files land in S3 RAW bucket, it auto-triggers ETL DAG
3. Monitor both DAGs in Airflow UI

## Step 5: Monitor Task Execution

### View DAG Runs
```bash
docker exec airflow-webserver airflow dags list-runs \
  --dag-id=event_driven_real_time_etl
```

### View Task Logs
```bash
docker exec airflow-webserver airflow tasks log \
  event_driven_real_time_etl \
  scan_raw_bucket \
  2026-02-26T16:00:00
```

## Step 6: Stop Services

```bash
cd finance-data-platform/phase_5_airflow_orchestration
docker compose down
```

## Troubleshooting

### DAGs not showing
```bash
# Verify files exist
ls dags/*.py

# Check syntax
python -m py_compile dags/event_driven_real_time_etl.py
python -m py_compile dags/s3_raw_bucket_sensor_trigger.py

# Reload DAGs
docker exec airflow-webserver airflow dags find
```

### Database errors
```bash
# Reset database (WARNING: loses all data)
docker compose down
docker volume rm phase_5_airflow_orchestration_postgres_data
python start_airflow.py
```

### Can't connect to AWS/S3
```bash
# Verify env vars are loaded
docker exec airflow-webserver printenv | grep AWS_
docker exec airflow-webserver printenv | grep BUCKET

# Check .env file exists
cat phase_6_streaming_kafka/.env
```

## Data Flow Reminder

```
Kafka → S3 RAW (erp/sales/, crm/interactions/, etc.)
  ↓ (S3 files detected)
Airflow Sensor (s3_raw_bucket_sensor_trigger) detects files
  ↓
Auto-triggers Event_Driven_Real_Time_ETL DAG
  ↓
Scan RAW → Move to STAGING → Run ETL → Archive
  ↓
PostgreSQL Warehouse (stg_sales, stg_payments, etc.)
```

## Next Steps

1. Run orchestrator producer+consumer to generate data:
   ```bash
   cd phase_6_streaming_kafka
   python orchestrator.py --demo
   ```

2. Monitor Airflow triggering DAG automatically

3. Query warehouse to see results:
   ```bash
   SELECT COUNT(*) FROM staging.stg_sales;
   ```
