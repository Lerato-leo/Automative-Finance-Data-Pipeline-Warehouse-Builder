# Phase 0: Environment & Infrastructure Setup

Set up the foundational infrastructure: database schemas, S3 buckets, AWS credentials, and Docker environment for the entire data platform.

## Purpose

- ✅ Create PostgreSQL schemas (staging, warehouse, analytics, metadata)
- ✅ Set up AWS S3 buckets for data pipeline
- ✅ Configure environment variables and credentials
- ✅ Prepare Docker infrastructure
- ✅ Install Python dependencies

## Prerequisites

- **Python**: 3.11+
- **PostgreSQL**: 12+ (local or RDS)
- **Docker**: 20.10+ with Docker Compose
- **AWS Account**: With S3 access
- **Git**: For version control

## Installation

### 1. Create Python Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\Activate.ps1  # Windows PowerShell
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

```bash
cp .env.example .env
# Edit .env with your credentials
```

Required variables:

```ini
# AWS
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# S3 Buckets
S3_RAW_BUCKET=automotive-raw-data-lerato-2026
S3_STAGING_BUCKET=automotive-staging-data-lerato-2026
S3_ARCHIVE_BUCKET=automotive-archive-data-lerato-2026

# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=automotive_warehouse

# SMTP (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Teams (optional)
TEAMS_WEBHOOK_URL=https://outlook.webhook.office.com/webhookb2/...
```

### 4. Create Database Schemas

```bash
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f 00_create_schemas.sql
```

This creates:
- `staging` - Raw ingested data
- `warehouse` - Cleaned and transformed data
- `analytics` - Aggregated insights
- `metadata` - Pipeline metadata and logging

### 5. Verify S3 Buckets

```bash
aws s3 ls
```

Ensure these three buckets exist:
- `automotive-raw-data-lerato-2026` - Input data (Bronze)
- `automotive-staging-data-lerato-2026` - Staged data (Silver)
- `automotive-archive-data-lerato-2026` - Historical archive

## S3 Bucket Architecture

### Bronze (RAW) Tier
Raw, unprocessed files as they arrive from source systems.

```
automotive-raw-data-lerato-2026/
├── erp/
│   ├── sales_data.csv
│   └── inventory.json
├── crm/
│   └── customers.xlsx
├── finance/
│   └── transactions.parquet
├── suppliers/
│   └── vendor_master.csv
└── iot/
    └── sensor_readings.json
```

**Characteristics**:
- Various file formats (CSV, JSON, XLSX, Parquet, Avro)
- "As-is" from source systems
- Potential data quality issues
- Files expire after 30 days

### Silver (STAGING) Tier
Cleaned, validated, and normalized data ready for analytics.

```
automotive-staging-data-lerato-2026/
├── ingested/
│   ├── erp_sales.parquet
│   ├── crm_customers.parquet
│   ├── financial_transactions.parquet
│   └── supplier_data.parquet
└── schemas/
    └── metadata.json
```

**Characteristics**:
- Standardized formats (Parquet)
- Consistent schemas
- Data quality validated
- Ready for transformation

### Gold (ARCHIVE) Tier
Historical backups and audit trail of processed data.

```
automotive-archive-data-lerato-2026/
├── 2026-01/
│   ├── sales/
│   ├── customers/
│   └── transactions/
└── 2026-02/
    ├── sales/
    ├── customers/
    └── transactions/
```

**Characteristics**:
- Timestamped folders by month
- Complete audit trail
- Compression enabled
- Glacier lifecycle policies

## Project Structure

```
Automative-Finance-Data-Pipeline-Warehouse-Builder/
├── README.md                          ← Main documentation
├── .env.example                       ← Environment template
├── requirements.txt                   ← Python dependencies
│
├── phase_0_environment_setup/
│   ├── README.md                      ← This file
│   ├── 00_create_schemas.sql          ← Database setup
│   └── requirements.txt                ← Phase 0 dependencies
│
├── phase_1_data_warehouse_design/
│   └── README.md                      ← Schema design
│
├── phase_2_data_source_setup/
│   └── README.md                      ← S3 & data sources
│
├── phase_3_shell_ingestion/
│   ├── README.md                      ← File validation & movement
│   ├── ingest.py                      ← Main ingestion script
│   ├── Dockerfile                     ← Docker image
│   └── requirements.txt                ← Dependencies
│
├── phase_4_python_etl/
│   └── README.md                      ← ETL transformations
│
├── phase_5_airflow_orchestration/
│   ├── README.md                      ← Airflow setup
│   ├── docker-compose.yml             ← Airflow infrastructure
│   ├── dags/                          ← DAG definitions
│   └── plugins/                       ← Custom operators
│
├── phase_6_streaming_kafka/
│   ├── README.md                      ← Real-time streaming
│   ├── kafka_producer.py              ← Synthetic event generator
│   └── docker-compose.yml             ← Kafka infrastructure
│
├── phase_7_database_administration/
│   └── README.md                      ← DB maintenance
│
├── phase_8_monitoring_logging/
│   └── README.md                      ← Observability
│
└── phase_9_documentation_deployment/
    └── README.md                      ← Documentation
```

## Verification Checklist

After running Phase 0, verify:

- [ ] Python 3.11 environment activated
- [ ] All pip packages installed: `pip list`
- [ ] `.env` file configured with AWS credentials
- [ ] AWS credentials work: `aws s3 ls`
- [ ] PostgreSQL accessible: `psql -c "SELECT version();"`
- [ ] Schemas created: `psql -c "\dn"` shows staging, warehouse, analytics, metadata
- [ ] S3 buckets exist: All three buckets visible in S3
- [ ] Docker running: `docker ps` shows no errors
- [ ] Docker Compose available: `docker-compose --version`

## Troubleshooting

### AWS Credentials Not Working

```bash
# Check AWS CLI configuration
aws configure

# Verify credentials
aws iam get-user

# Test S3 access
aws s3 ls s3://automotive-raw-data-lerato-2026
```

### PostgreSQL Connection Failed

```bash
# Test connection
psql -h $DB_HOST -U $DB_USER -d postgres -c "SELECT version();"

# If RDS:
# - Check security groups allow port 5432
# - Verify subnet accessibility
# - Confirm parameter groups
```

### Docker Issues

```bash
# Verify Docker daemon
docker ps

# Check Docker Compose installation
docker-compose --version

# Diagnose Docker environment
docker info
```

### Schema Creation Failed

```bash
# Check if schemas exist
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\dn"

# Rerun script with verbose output
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f 00_create_schemas.sql -v ON_ERROR_STOP=1
```

## Next Steps

After Phase 0 setup is complete:

1. → **Phase 1**: Review data warehouse schema design
2. → **Phase 2**: Configure data sources
3. → **Phase 3**: Run file ingestion pipeline
4. → **Phase 4**: Execute ETL transformations
5. → **Phase 5**: Orchestrate with Airflow
6. → **Phase 6**: Optional - Add real-time Kafka streaming

## File Descriptions

### 00_create_schemas.sql
Creates all required PostgreSQL schemas:
- `staging` - Raw ingestion layer
- `warehouse` - Cleaned/transformed data
- `analytics` - Aggregated metrics
- `metadata` - Pipeline logs and metadata

### requirements.txt
Python 3.11 dependencies:
```
boto3==1.28.85              # AWS S3
psycopg2-binary==2.9.9      # PostgreSQL
python-dotenv==1.0.0        # Environment variables
requests==2.31.0            # HTTP client
```

### .env.example
Template showing all required environment variables with comments

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                  Phase 0: Infrastructure                      │
├──────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐        ┌──────────────┐       ┌────────┐        │
│  │  Python  │        │ PostgreSQL   │       │  AWS   │        │
│  │  3.11    │        │  Warehouse   │       │  S3    │        │
│  └────┬─────┘        └──────┬───────┘       └───┬────┘        │
│       │                     │                   │             │
│       └─────────────────────┼───────────────────┘             │
│                             │                                  │
│                      ┌──────▼──────┐                           │
│                      │   Docker    │                           │
│                      │  Compose    │                           │
│                      └─────────────┘                           │
│                                                                  │
│  ✓ Schemas created         ✓ Buckets ready      ✓ Env vars    │
│  ✓ Tables initialized      ✓ Lifecycle rules    ✓ Credentials │
│                                                                  │
└──────────────────────────────────────────────────────────────┘
```

## Environment Checklist

```bash
# Verify all Phase 0 components are ready

# Check Python
python3 --version  # Should be 3.11+

# Check PostgreSQL
psql --version     # Should be installed

# Check Docker
docker --version   # Should be 20.10+
docker-compose --version

# Check AWS CLI
aws --version      # Should be installed

# Check environment file
test -f .env && echo "✓ .env exists" || echo "✗ .env missing"

# Check AWS credentials
aws sts get-caller-identity

# Check S3 buckets
aws s3 ls | grep "automotive-"

# Check PostgreSQL
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT count(*) FROM information_schema.schemata;"
```

## Related Documentation

- **Main README**: See `../../README.md` for full project overview
- **Phase 1**: Data warehouse schema design in `../phase_1_data_warehouse_design/README.md`
- **Phase 5**: Airflow orchestration in `../phase_5_airflow_orchestration/README.md`

---

**Status**: ✅ Ready for Production  
**Last Updated**: March 2026  
**Maintainer**: Data Platform Team
