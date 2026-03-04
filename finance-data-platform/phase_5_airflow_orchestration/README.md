# Phase 5: Airflow Orchestration

## Overview

This phase implements Apache Airflow as the orchestration layer for the automotive finance data pipeline. Airflow automatically manages:

1. **Data movement**: RAW → STAGING → ARCHIVE buckets
2. **ETL transformation**: Validates, cleans, and loads data to PostgreSQL
3. **Scheduling & monitoring**: Tracks all pipeline executions
4. **Error handling & retries**: Automatic failure recovery
5. **Dependency management**: Ensures correct task execution order

## Architecture

```
S3 Event
    ↓
S3 Event Notification → SQS Queue
    ↓
SQS Sensor DAG (s3_raw_bucket_sensor_trigger)
    ↓ consumes ObjectCreated events continuously
TriggerDagRun Operator
    ↓
Event-Driven ETL DAG (event_driven_real_time_etl)
    ├→ Task 1: scan_raw_bucket
    ├→ Task 2: move_to_staging
    ├→ Task 3: detect_schema
    ├→ Task 4: run_etl
    ├→ Task 5: archive_processed
    └→ Task 6: check_sla
         ↓
    PostgreSQL Warehouse (staging schema)
```

## Components

### 1. Docker Compose Stack (`docker-compose.yml`)

**Services**:
- **PostgreSQL (postgres)**: Metadata store for Airflow + Warehouse staging database
- **Redis (redis)**: Message broker for Celery task queue
- **Webserver (webserver)**: Airflow UI (port 8080) + REST API
- **Scheduler (scheduler)**: Monitors DAGs and schedules tasks
- **Worker (worker)**: Executes tasks via Celery

**Features**:
- Health checks for all services
- Volume persistence for DAG code
- AWS credentials passed as environment variables
- Isolated network for container communication

### 2. DAGs

#### DAG 1: `event_driven_real_time_etl.py` (445 lines)

**Purpose**: Process streaming data from S3 to data warehouse

**Tasks**:
1. **scan_raw_bucket**: Check S3 RAW bucket for new files
2. **move_to_staging**: Copy files from RAW to STAGING (preserves domain folders)
3. **detect_schema**: Analyze data structure (columns, types, cardinality)
4. **run_etl**: Execute transformation
   - Read from STAGING
   - Validate against 16 rules (see `phase_4_python_etl/etl_main.py`)
   - Load to PostgreSQL stg_* tables
5. **archive_processed**: Move processed files to ARCHIVE bucket (with timestamp)
6. **check_sla**: Verify pipeline completed within SLA (2 hours)

**Execution**:
- Manual trigger: Via Airflow UI
- Auto-trigger: Via sensor DAG when files detected

#### DAG 2: `s3_raw_bucket_sensor_trigger.py`

**Purpose**: Auto-trigger ETL when data lands in S3

**Tasks**:
1. **validate_queue_config**: Ensure `RAW_S3_EVENTS_QUEUE_URL` is configured
2. **wait_for_s3_events**: SqsSensor waits for S3 ObjectCreated events
3. **extract_s3_event_details**: Parse SQS payload and extract file keys
4. **trigger_etl_dag**: TriggerDagRunOperator fires `event_driven_real_time_etl`
5. **log_trigger_event**: Logs summary of triggered file keys

**Execution**:
- Schedule: Continuous (`@continuous`)
- Triggered by: S3 Event Notification messages delivered to SQS

### 3. Configuration Files

#### `.env` (Root of project)

Contains AWS credentials and bucket names:
```
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1
RAW_BUCKET=automotive-raw-data-lerato-2026
STAGING_BUCKET=automotive-staging-data-lerato-2026
ARCHIVE_BUCKET=automotive-archive-data-lerato-2026
RAW_S3_EVENTS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/<account-id>/<queue-name>
```

**Location**: `finance-data-platform/.env`
**Required**: Yes - script will fail without it

#### `airflow.cfg`

Airflow configuration (generated automatically in Docker):
- Max active tasks per DAG: 16
- Executor: Celery (distributed task execution)
- Database: PostgreSQL (docker service)
- Broker: Redis (docker service)

### 4. Startup Scripts

#### `start_airflow.py`

Initialization script that:
1. Checks for `.env` file
2. Loads AWS credentials
3. Runs `docker compose up -d`
4. Initializes database: `airflow db init`
5. Creates admin user: `airflow users create --role Admin`
6. Displays startup information

**Usage**:
```bash
cd phase_5_airflow_orchestration
python start_airflow.py
```

## Setup Instructions

### Step 1: Configure AWS Credentials

```bash
# In finance-data-platform/ root directory
cp .env.template .env

# Edit .env with your AWS credentials:
# AWS_ACCESS_KEY_ID=your_key
# AWS_SECRET_ACCESS_KEY=your_secret
# RAW_BUCKET=your-bucket-name
# RAW_S3_EVENTS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/<account-id>/<queue-name>
```

### Step 1.1: Configure S3 Event Notification to SQS (Required)

1. Create an SQS queue for RAW bucket events
2. In S3 RAW bucket, configure Event Notification:
    - Event type: `ObjectCreated:*`
    - Prefix: your raw landing prefix (optional)
    - Destination: the SQS queue URL above
3. Ensure queue policy allows S3 to send messages
4. Set `RAW_S3_EVENTS_QUEUE_URL` in `.env`

### Step 1.2: Auto-Provision SQS + S3 Notification (Recommended)

Use the included PowerShell setup script to create/configure everything end-to-end:

```powershell
cd phase_5_airflow_orchestration
./setup_s3_event_sqs_trigger.ps1 -RawBucket "automotive-raw-data-lerato-2026" -QueueName "automotive-raw-s3-events" -Region "us-east-1"
```

Optional prefix filter example:

```powershell
./setup_s3_event_sqs_trigger.ps1 -RawBucket "automotive-raw-data-lerato-2026" -QueueName "automotive-raw-s3-events" -Region "us-east-1" -PrefixFilter "erp/"
```

What the script does:
1. Creates (or reuses) SQS queue
2. Applies queue policy to allow S3 publish
3. Configures S3 `ObjectCreated:*` notification to queue
4. Updates `.env` with `RAW_S3_EVENTS_QUEUE_URL`

### Step 2: Start Services

```bash
cd phase_5_airflow_orchestration
python start_airflow.py
```

### Step 3: Access Airflow UI

- URL: `http://localhost:8080`
- Username: `admin`
- Password: `admin`

### Step 4: Verify DAGs

Dashboard should show:
- `event_driven_real_time_etl` (paused or active)
- `s3_raw_bucket_sensor_trigger` (active - continuously waiting for S3 events)

## Usage

### Manual Pipeline Trigger

```
Airflow UI → DAGs → event_driven_real_time_etl → Trigger DAG → Select run date
```

### Automatic Pipeline Trigger

```
1. Run Kafka producer to generate data
2. Kafka consumer batches to S3 RAW bucket
3. S3 publishes ObjectCreated event to SQS queue
4. Sensor DAG consumes event and triggers event_driven_real_time_etl
5. ETL pipeline executes automatically
```

### Monitor Execution

```
Airflow UI → DAGs → event_driven_real_time_etl → Graph View
```

Shows:
- Task status (running, success, failed)
- Execution time
- Task logs (click task → View Logs)

### View Logs

**From UI**:
Airflow UI → Select DAG → Task → View Logs

**From Terminal**:
```bash
# All webserver logs
docker compose logs -f webserver

# All scheduler logs
docker compose logs -f scheduler

# Specific DAG run
docker exec airflow-webserver airflow tasks log event_driven_real_time_etl scan_raw_bucket 2026-02-26T16:00:00
```

## Troubleshooting

### DAGs Not Appearing

**Symptom**: Airflow UI shows empty DAG list

**Solutions**:
```bash
# 1. Check DAG files exist
ls -la dags/

# 2. Check syntax (from phase_5_airflow_orchestration/)
python -m py_compile dags/event_driven_real_time_etl.py
python -m py_compile dags/s3_raw_bucket_sensor_trigger.py

# 3. Check webserver logs
docker compose logs webserver | grep -i "parsing\|error\|dag"

# 4. Restart webserver
docker compose restart webserver
```

### Services Not Starting

**Symptom**: `docker compose up -d` fails

**Solutions**:
```bash
# 1. Check Docker is running
docker ps

# 2. Check .env file exists in parent directory
ls -la ../.env

# 3. View detailed logs
docker compose logs postgres

# 4. Reset (WARNING: loses data)
docker compose down
docker volume rm phase_5_airflow_orchestration_postgres_data
python start_airflow.py
```

### S3 Connection Failed

**Symptom**: Task fails with "NoCredentialsError" or "Forbidden"

**Solutions**:
```bash
# 1. Verify .env has credentials
cat ../.env | grep AWS_

# 2. Test S3 access from container
docker exec airflow-webserver aws s3 ls

# 3. Check IAM permissions
# AWS credentials must allow: s3:GetObject, s3:PutObject, s3:ListBucket
```

### Task Repeatedly Failing

**Symptom**: Same task fails multiple times

**Solutions**:
1. Check task logs for specific error
2. Fix underlying issue (invalid data, schema mismatch, etc.)
3. Trigger DAG again to retry

**For ETL failures**:
- Check S3 STAGING bucket has valid CSV files
- Verify all required columns present
- Check PostgreSQL stg_* tables exist and are writable

## Data Flow Validation

After pipeline completes, query warehouse:

```sql
-- Connect to PostgreSQL (localhost:5432, user: warehouse_user)
SELECT COUNT(*) FROM staging.stg_sales;           -- Should have rows
SELECT COUNT(*) FROM staging.stg_payments;        -- Should have rows
SELECT COUNT(*) FROM staging.stg_interactions;    -- Should have rows
SELECT COUNT(*) FROM staging.stg_inventory;       -- Should have rows
SELECT COUNT(*) FROM staging.stg_procurement;     -- Should have rows
SELECT COUNT(*) FROM staging.stg_telemetry;       -- Should have rows
```

## Stop Services

```bash
# From phase_5_airflow_orchestration/
docker compose down

# Remove all data
docker compose down -v

# View stopped services
docker compose ps
```

## Advanced Configuration

### Change Schedule

Edit `dags/s3_raw_bucket_sensor_trigger.py`:
```python
dag = DAG(
    'schedule_interval='*/5 * * * *',  # Every 5 minutes instead of 1
    ...
)
```

### Change SLA Timeout

Edit `dags/event_driven_real_time_etl.py`:
```python
sla=timedelta(hours=4)  # Instead of 2 hours
```

### Add Email Alerts

Edit `.env`:
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=airflow@example.com
```

Then in DAG:
```python
default_args={
    'email': ['admin@example.com'],
    'email_on_failure': True,
}
```

## Integration Points

### Upstream: Phase 6 (Kafka Streaming)
- Source: Kafka topics (6 domains: erp, crm, finance, etc.)
- Bridge: Kafka consumer batches to S3 RAW bucket
- Format: CSV files with domain folder structure

### Downstream: Phase 8 (Database Administration)
- Target: PostgreSQL staging schema (stg_sales, stg_payments, etc.)
- Validation: 16 rules applied during ETL (see Phase 4)
- Archive: Processed files moved to ARCHIVE bucket

## Monitoring & Observability

### Airflow UI Metrics

- Active DAG runs
- Task duration
- Success/failure rates
- Execution timeline

### PostgreSQL Metrics

```sql
-- Monitor data freshness
SELECT table_name, COUNT(*) as row_count, MAX(updated_at) as last_update
FROM information_schema.tables t
LEFT JOIN staging.stg_sales s ON t.table_name = 'stg_sales'
WHERE table_schema = 'staging'
GROUP BY table_name;
```

### Docker Container Health

```bash
docker ps --all
docker stats airflow-webserver airflow-scheduler airflow-worker
docker logs -f airflow-webserver --tail 50
```

## Files Reference

```
phase_5_airflow_orchestration/
├── dags/
│   ├── event_driven_real_time_etl.py     (445 lines) - Main pipeline
│   └── s3_raw_bucket_sensor_trigger.py   (140 lines) - Auto-trigger sensor
├── logs/                                   (Generated) - Task execution logs
├── plugins/                                (Optional) - Custom operators/hooks
├── docker-compose.yml                      (Services) - Postgres, Redis, Airflow
├── start_airflow.py                        (Script) - Initialize & start
├── STARTUP.md                              (Guide) - Quick start instructions
├── README.md                               (This file)
└── requirements.txt (if needed)

finance-data-platform/
└── .env                                    (Required) - AWS credentials
└── .env.template                           (Template) - Copy to .env
```

## Related Documentation

- **Phase 4** (`phase_4_python_etl/etl_main.py`): ETL validation rules
- **Phase 6** (`phase_6_streaming_kafka/`): Kafka streaming & S3 upload
- **Phase 8** (`phase_8_database_administration/`): Database schema & administration

## Summary

✅ **Setup**: Copy `.env.template` → `.env`, add credentials
✅ **Start**: Run `python start_airflow.py`
✅ **Verify**: Open http://localhost:8080, check DAGs
✅ **Trigger**: Generate data via Kafka → auto-triggers DAG
✅ **Monitor**: View execution in Airflow UI
✅ **Validate**: Query PostgreSQL staging tables

**Next**: When ready to use, create `.env` with AWS credentials and run startup script!
