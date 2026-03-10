# 🚗 Automotive Finance Data Pipeline & Warehouse Builder

A comprehensive, production-ready data engineering pipeline for automotive finance data processing. End-to-end solution from data ingestion through streaming to warehousing and monitoring.

## 📋 Overview

This project implements a complete data pipeline architecture with 10 phases. Phases 1 through 6 are now implemented and wired together end to end.

| Phase | Name | Status | Purpose |
|-------|------|--------|---------|
| 0 | Environment Setup | ✅ Complete | Docker/Infrastructure initialization |
| 1 | Data Warehouse Design | ✅ Complete | Schema design & database setup |
| 2 | Data Source Setup | ✅ Complete | Data source registration & connections |
| 3 | Shell Ingestion | ✅ Complete | File validation & staging |
| 4 | Python ETL | ✅ Complete | Data transformation & enrichment |
| 5 | Airflow Orchestration | ✅ Complete | Workflow scheduling & automation |
| 6 | Kafka Streaming | ✅ Complete | Real-time data streaming into the unified pipeline |
| 7 | Database Administration | 📋 Planned | Performance tuning & optimization |
| 8 | Monitoring & Logging | 📋 Planned | Observability & alerting |
| 9 | Documentation & Deployment | 📋 Planned | Final documentation & CI/CD |

## ✅ Current Delivery Status

- Phases 1 to 6 are complete and integrated.
- Phase 6 streaming now lands mixed-format raw files into S3 and feeds the same Airflow DAG used by the batch path.
- The canonical root stack is [docker-compose.yml](c:\Users\lerat\Documents\Project 4 - Data\Automative-Finance-Data-Pipeline-Warehouse-Builder\docker-compose.yml).

## 🎯 Key Feature: Single Orchestration DAG

**One DAG owns the full production flow** from S3 landing through Phase 3 ingestion, Phase 4 ETL, archive, and Phase 5 notifications.

```
automotive_finance_orchestration (Runs every 5 minutes)
├── monitor_raw_bucket              → Monitor RAW files
├── run_phase_3_shell_ingestion     → Move RAW to STAGING and send Phase 3 alerts
├── run_phase_4_etl                 → Execute the real ETL script on STAGING data
├── archive_processed_staging_files → Move processed files to ARCHIVE
└── send_phase_5_airflow_notification → Send Airflow completion notifications
```

✅ **Automatic:** Monitors the raw bucket every 5 minutes  
✅ **Unified:** Manual and streaming entry points trigger the same DAG  
✅ **Real:** Airflow calls the actual Phase 3 and Phase 4 scripts  
✅ **Clean:** Only one active DAG remains in the orchestration layer  

## 🏗️ Data Architecture

```
AWS S3 (Data Lake)
├─ RAW Bucket (auto upload)
│  ├─ Finance/Payments
│  ├─ CRM/Interactions
│  ├─ ERP/Orders
│  ├─ Supplier/Catalog
│  └─ IoT/Sensors
│
├─ STAGING Bucket (Phase 3 output)
│  └─ Validated & processed files
│
└─ ARCHIVE Bucket (Final storage)
   └─ Historical & completed files
        ↓
    PostgreSQL Warehouse
    ├─ payments_table
    ├─ interactions_table
    ├─ orders_table
    ├─ suppliers_table
    └─ sensor_data_table
        ↓
    📊 Reporting & Analytics
```

## 🚀 Quick Start

### Prerequisites

```bash
python --version        # 3.11+
docker --version        # 20.10+
docker-compose --version # 1.29+
aws configure list      # AWS credentials
```

### Setup (5 minutes)

```bash
# 1. Clone & setup
git clone <repo-url>
cd Automative-Finance-Data-Pipeline-Warehouse-Builder
python -m venv .venv
source .venv/bin/activate
pip install -r finance-data-platform/phase_0_environment_setup/requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with AWS/SMTP/Teams credentials

# 3. Start infrastructure
./finance-data-platform/scripts/start/start.sh

# 4. Initialize Airflow
docker exec airflow-webserver airflow db migrate
docker exec airflow-webserver airflow users create \
  --username admin --password admin \
  --firstname Admin --lastname User \
  --role Admin --email admin@example.com
```

### Run Pipeline

```bash
# Upload your data files:
aws s3 cp finance.csv s3://automotive-raw-data-lerato-2026/finance/
aws s3 cp crm.json s3://automotive-raw-data-lerato-2026/crm/
# ... more files

# Pipeline automatically:
# → Monitors the RAW bucket (every 5 min)
# → Runs Phase 3 shell ingestion (RAW → STAGING)
# → Runs Phase 4 ETL from STAGING
# → Archives processed files
# → Sends Phase 5 Airflow notifications
```

### Monitor

```bash
# Airflow Dashboard
open http://localhost:8081

# View logs
docker compose logs -f airflow-scheduler
docker compose logs -f airflow-worker

# Check status
docker compose ps
```

## 📁 Project Structure

```
finance-data-platform/
├── scripts/
│   └── start/
│       ├── start.bat
│       └── start.sh
├── tests/
│   └── integration/
│       └── run_full_system_test.py
├── phase_0_environment_setup/
│   └── README.md
├── phase_1_data_warehouse_design/
│   └── README.md
├── phase_2_data_source_setup/
│   └── README.md
├── phase_3_shell_ingestion/
│   └── README.md
├── phase_4_python_etl/
│   └── README.md
├── phase_5_airflow_orchestration/
│   ├── README.md
│   ├── dags/
│   │   └── automotive_finance_orchestration_dag.py  ← MAIN DAG
│   ├── logs/
│   └── plugins/
├── phase_6_streaming_kafka/
│   └── README.md
├── phase_7_database_administration/
│   └── README.md
├── phase_8_monitoring_logging/
│   └── README.md
└── phase_10_documentation_deployment/
    └── README.md

docker-compose.yml
README.md
.env.example
```

## ⚙️ System Components

### Airflow (Orchestration)
- **Webserver:** Port 8081 - UI for DAG management
- **Scheduler:** Runs DAGs on schedule (every 5 min)
- **Worker:** Executes tasks using Celery
- **Database:** PostgreSQL - Airflow metadata
- **Message Broker:** Redis - Celery task queue

### Data Storage
- **S3 RAW:** Incoming files (~170 GB capacity)
- **S3 STAGING:** Intermediate processing (~50 GB)
- **S3 ARCHIVE:** Historical storage (~500 GB)
- **PostgreSQL Warehouse:** Transformed data (5+ tables)

## 📧 Notifications

Pipeline sends automatic alerts on completion:

### Email (SMTP)
```
To: lerato.matamela01@gmail.com
Subject: Automotive Finance Orchestration Complete

Pipeline Status: SUCCESS
Raw Files Detected: 4
Phase 3: SUCCESS
Phase 4: SUCCESS
Archived Files: 4

Tasks:
✅ S3 Monitoring
✅ Phase 3 shell ingestion
✅ Phase 3 notifications
✅ Phase 4 ETL
✅ Archive
✅ Phase 5 notifications
```

### Teams (Webhook)
```
Channel: capeitinitiative
Message Card:
  Status: ✅ SUCCESS
  Raw Files: 4
  Archived Files: 4
  Flow: Phase 3 → Phase 4 → Archive → Notify
```

## 🔧 Configuration

### .env File

```bash
# AWS
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
S3_RAW_BUCKET=automotive-raw-data-lerato-2026
S3_STAGING_BUCKET=automotive-staging-data-lerato-2026
S3_ARCHIVE_BUCKET=automotive-archive-data-lerato-2026

# Email (Gmail with app password)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
EMAIL_RECIPIENT=lerato.matamela01@gmail.com

# Teams Webhook
TEAMS_WEBHOOK_URL=https://outlook.webhook.office.com/webhookb2/xxxxx/IncomingWebhook/xxxx

# Airflow
AIRFLOW_HOME=/opt/airflow
AIRFLOW__CORE__EXECUTOR=CeleryExecutor
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql://airflow:airflow@airflow-postgres/airflow
AIRFLOW__CORE__LOAD_EXAMPLES=False
```

## 📊 Workflow Execution

### Timeline (90-120 seconds total)

```
00:00 - User uploads file to S3
00:00 - File sits in RAW bucket
05:00 - DAG scheduler triggers (every 5 min)
05:10 - Task 1: check_s3_bucket → Detects file
05:15 - Task 2: move_raw_to_staging → Copy to STAGING
05:25 - Task 3: run_phase_3_ingestion → Validate
05:35 - Task 4: detect_file_types → Categorize
05:45 - Task 5: run_etl_pipeline → Transform
06:10 - Task 6: archive_processed → Archive
06:20 - Task 7: check_sla_compliance → Verify SLA
06:30 - Task 8: send_notifications → Email + Teams
06:35 - COMPLETE ✅
```

## 🛠️ Common Operations

### View DAG Runs

```bash
# List all runs for the production DAG
docker exec airflow-postgres psql -U airflow -d airflow -c "
SELECT dag_id, state, start_date 
FROM dag_run 
WHERE dag_id='automotive_finance_orchestration'
ORDER BY execution_date DESC LIMIT 10;"
```

### Trigger DAG Manually

```bash
# For testing (usually auto-triggered)
docker exec airflow-webserver airflow dags trigger automotive_finance_orchestration
```

### View Task Logs

```bash
# Get logs for specific task
docker exec airflow-webserver airflow tasks logs \
  automotive_finance_orchestration monitor_raw_bucket
```

### Check S3 Files

```bash
# List files in RAW bucket
aws s3 ls s3://automotive-raw-data-lerato-2026/ --recursive

# Check STAGING
aws s3 ls s3://automotive-staging-data-lerato-2026/ --recursive

# Check ARCHIVE
aws s3 ls s3://automotive-archive-data-lerato-2026/ --recursive
```

### Query Warehouse

```bash
# Connect to warehouse
psql -h localhost -U airflow -d automotive_warehouse

# Check tables
\dt

# Count records
SELECT COUNT(*) FROM payments;
SELECT COUNT(*) FROM interactions;
SELECT COUNT(*) FROM orders;
```

## 🔍 Monitoring & Troubleshooting

### Check System Health

```bash
# Verify all containers running
docker compose ps

# Check logs for errors
docker compose logs airflow-scheduler | grep -i error
docker compose logs airflow-worker | grep -i error

# Health check
curl http://localhost:8081/health
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| DAG not loading | Syntax error in DAG file | Check logs: `docker logs airflow-scheduler` |
| Tasks queued forever | Worker not running | `docker compose restart airflow-worker` |
| S3 files not detected | Wrong bucket name or credentials | Verify `.env` and AWS access |
| Notifications not sent | Email/Teams credentials | Test SMTP and webhook URLs |
| Database connection failed | PostgreSQL not healthy | `docker compose restart airflow-postgres` |

## 📚 Phase Documentation

Each phase has detailed README with architecture, data flow, and implementation details:

- **[Phase 0](finance-data-platform/phase_0_environment_setup/README.md)** - Docker & environment setup
- **[Phase 1](finance-data-platform/phase_1_data_warehouse_design/README.md)** - Star schema design
- **[Phase 2](finance-data-platform/phase_2_data_source_setup/README.md)** - Data source configuration
- **[Phase 3](finance-data-platform/phase_3_shell_ingestion/README.md)** - Ingestion validation
- **[Phase 4](finance-data-platform/phase_4_python_etl/README.md)** - ETL transformation
- **[Phase 5](finance-data-platform/phase_5_airflow_orchestration/README.md)** - Airflow orchestration (CURRENT)
- **[Phase 6](finance-data-platform/phase_6_streaming_kafka/README.md)** - Kafka streaming
- **[Phase 7](finance-data-platform/phase_7_database_administration/README.md)** - DB optimization
- **[Phase 8](finance-data-platform/phase_8_monitoring_logging/README.md)** - Monitoring setup
- **[Phase 10](finance-data-platform/phase_10_documentation_deployment/README.md)** - Documentation

## 📈 Performance Metrics

- **Data Ingestion:** 170+ records/batch
- **Processing Time:** 90-120 seconds per batch
- **S3 Throughput:** ~50 MB/min
- **SLA Compliance:** Target 5 minutes
- **Notification Latency:** <2 minutes
- **Warehouse Queries:** <1 second

## 🔐 Security Considerations

- ✅ AWS IAM policies for S3 access
- ✅ Encrypted credentials in `.env` (NOT in git)
- ✅ PostgreSQL authentication required
- ✅ Teams webhook validation
- ✅ Email authentication via app password
- ⚠️ Never commit credentials to repository

## 🚀 Next Steps

### Immediate (Phase 5)
- ✅ Consolidated DAG fully functional
- ✅ All 8 tasks implemented
- ✅ Notifications working
- ➡️ Install postgresql module in Docker (in progress)

### Short Term (Phase 6)
- Kafka topic setup
- Streaming data ingestion
- Real-time ETL pipeline
- Kafka → Warehouse integration

### Medium Term (Phases 7-8)
- Database performance optimization
- Monitoring & alerting setup
- Cost analysis & optimization
- Advanced analytics

### Long Term (Phase 9)
- Production deployment
- CI/CD pipeline
- Documentation package
- Knowledge transfer

## 📄 License

[Your License]

## 📞 Support

- **Issues:** GitHub Issues page
- **Email:** [contact-email]
- **Slack:** [workspace]

---

**Status:** ✅ Phase 5 Complete - Consolidated DAG Live  
**Last Updated:** March 9, 2026  
**Version:** 1.0.0  
**Python:** 3.11+  
**Airflow:** 2.7.3
