# 📥 Phase 3: Shell Ingestion

## Overview

Phase 3 implements shell scripts and Python utilities for data extraction and ingestion from configured data sources into S3 RAW bucket. This layer handles the initial data landing with validation and error handling.

## 🎯 Objective

Create automated scripts to:
- ✅ Extract data from 6 sources (ERP, CRM, Inventory, Procurement, IoT, Master Data)
- ✅ Validate file integrity (schema, format, checksums)
- ✅ Transfer to S3 RAW bucket with organized folder structure
- ✅ Log all ingestion events with audit trail
- ✅ Handle errors gracefully with retry logic

## 🔄 Data Flow

```
Data Sources (ERP, CRM, Inventory, Procurement, IoT, Master Data)
    ↓
Shell/Python Scripts (Phase 3)
    ├─ Authenticate to source
    ├─ Extract data (CSV/JSON)
    ├─ Validate schema
    ├─ Validate row counts
    ├─ Validate checksums
    └─ Upload to S3 RAW
        ↓
    S3 RAW Bucket (automotive-raw-data-lerato-2026/)
        ├─ finance/sales/
        ├─ finance/payments/
        ├─ crm/interactions/
        ├─ operations/inventory/
        ├─ procurement/orders/
        ├─ iot/telemetry/
        └─ reference/master_data/
```

## 📂 Data Organization

Files are organized by source domain and type:

```
s3://automotive-raw-data-lerato-2026/
├── finance/
│   ├── sales/YYYY/MM/DD/sales_YYYYMMDD.csv
│   ├── payments/YYYY/MM/DD/payments_YYYYMMDD.csv
│   └── gl/YYYY/MM/DD/gl_YYYYMMDD.csv
├── crm/
│   └── interactions/YYYY/MM/DD_HH/interactions_YYYYMMDD_HHMM.jsonl
├── operations/
│   └── inventory/YYYY/MM/DD_HH/inventory_YYYYMMDD_HHMM.csv
├── procurement/
│   └── purchase_orders/YYYY/MM/DD/po_YYYYMMDD.json
├── iot/
│   └── telemetry/YYYY/MM/DD_HH/telemetry_batch.json
└── reference/
    └── master_data/YYYY/MM/DD/master_data_YYYYMMDD.csv
```

## ✅ Validation Rules

### CSV Files
- ✓ Column count consistent across all rows
- ✓ Header row present and valid
- ✓ No empty mandatory columns
- ✓ Data types match expected schema
- ✓ Date format = YYYY-MM-DD
- ✓ Numeric fields valid

### JSON Files
- ✓ Valid JSON syntax (parseable)
- ✓ Required fields present
- ✓ Data types match schema
- ✓ Nested objects valid

### All Files
- ✓ File size < 500 MB
- ✓ No duplicate records (by primary key)
- ✓ Checksum/MD5 validation
- ✓ Encoding = UTF-8

## 📊 File Ingestion Metrics

| Source | Files/Day | Avg Size | Format | Frequency |
|--------|-----------|----------|--------|-----------|
| ERP | 3 | 250 MB | CSV | Daily 3 AM |
| CRM | 24 | 50 MB | JSONL | Hourly |
| Inventory | 6 | 10 MB | CSV | Every 4h |
| Procurement | 1 | 20 MB | JSON | Daily 7 AM |
| IoT | 24 | 100 MB | JSON | Hourly |
| Master Data | 1/7 | 5 MB | CSV | Weekly |
| **Total/Day** | **~80** | **~550 MB** | - | - |

## 🐛 Troubleshooting

### SFTP Connection Failed
```bash
# Test source connection
sftp -v ${ERP_SFTP_USER}@${ERP_SFTP_HOST}

# Check network
nslookup ${ERP_SFTP_HOST}
telnet ${ERP_SFTP_HOST} 22
```

### S3 Upload Failed
```bash
# Verify AWS credentials
aws sts get-caller-identity

# List bucket contents
aws s3 ls s3://${S3_RAW_BUCKET}/
```

### File Validation Failed
```bash
# Check file format
file /path/to/file.csv

# Validate CSV
head -5 /path/to/file.csv | column -t -s,

# Validate JSON
jq . /path/to/file.json
```

## 📚 Resources

- [AWS S3 CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-services-s3.html)
- [OpenSSH SFTP](https://man.openbsd.org/sftp)
- [cURL REST API](https://curl.se/)
- [Bash Scripting](https://www.gnu.org/software/bash/manual/)
- [Python Pandas](https://pandas.pydata.org/)

## 📧 Notifications

### Email Format
- Subject: "✅ Phase 3: File Ingestion - {filename}"
- Body: File name, size, record count, validation status, timestamp

### Teams Format
- Card with file details, status indicator, and counts
- Channel: Data Pipeline notifications

## 🚀 Integration

Phase 3 is triggered by **Phase 5 (Airflow):**

```python
# automotive_finance_orchestration_dag.py

@task
def ingest_files(**context):
    # Phase 3: Validate and ingest files
    result = run_phase_3_shell_ingestion()
    return result
```

---

**Status:** ✅ Ingestion Ready  
**Last Updated:** March 9, 2026  
**Daily Volume:** 80 files, 550 MB

Beautiful HTML email with:
- File name and status
- Timestamp
- Details (error message if failed)

### Teams
Same information delivered to Teams channel via webhook

## Logs

Check container logs:

```bash
docker logs -f phase-3-ingestion
```

Expected output:
```
============================================================
🔄 PHASE 3: Data Ingestion - File Movement with Notifications
============================================================
RAW bucket: automotive-raw-data-lerato-2026
STAGING bucket: automotive-staging-data-lerato-2026

📂 Processing: erp/sales_data.csv
✓ File validated: erp/sales_data.csv (12.45MB)
✓ File copied: erp/sales_data.csv → automotive-staging-data-lerato-2026/ingested/sales_data.csv
✓ Original deleted: automotive-raw-data-lerato-2026/erp/sales_data.csv
📧 Email sent: erp/sales_data.csv [Success]
💬 Teams message posted: erp/sales_data.csv

============================================================
✓ Phase 3 Complete: 1 files processed, 0 failed
============================================================
```

## Integration with Phase 5 (Airflow)

Phase 5's `automotive_finance_orchestration_dag.py` includes the `run_phase_3_shell_ingestion` task that:
- Can invoke Phase 3 as a Docker service
- Or run the Python script directly within the DAG

Currently configured to call Phase 3 as an external service.

## Troubleshooting

### Email Not Sending

```
❌ Email failed: [SSL: WRONG_VERSION_NUMBER]
```

Fix:
- Ensure SMTP_PORT=587 (TLS, not SSL 465)
- For Gmail, use "App Password" (not regular password)
- Enable "Less secure app access" if using regular password

### Teams Webhook Not Working

```
⚠️ Teams webhook not configured - skipping Teams notification
```

Fix:
- Create incoming webhook in Teams channel
- Copy webhook URL to TEAMS_WEBHOOK_URL environment variable

### Files Not Processing

Check:
1. S3 bucket names are correct
2. AWS credentials have S3 access
3. Files are in correct format
4. File size < 500MB

## Architecture Diagram

```
┌─────────────────┐
│   RAW Bucket    │  (automotive-raw-data-lerato-2026)
│  ┌───────┐      │
│  │file.csv   │      │
│  └───────┘      │
└────────┬────────┘
         │
         ▼
┌──────────────────┐
│   Phase 3        │
│  Ingestion       │
│  ┌────────────┐  │
│  │ Validate   │  │
│  │ ✓ Format   │  │
│  │ ✓ Size     │  │
│  └────────────┘  │
│  ┌────────────┐  │
│  │ Notify     │  │
│  │ ✓ Email    │  │
│  │ ✓ Teams    │  │
│  └────────────┘  │
└────────┬─────────┘
         │
         ▼
┌─────────────────────────┐
│  STAGING Bucket         │
│  ┌─────────────────┐    │
│  │ ingested/       │    │
│  │└─ file.csv      │    │
│  └─────────────────┘    │
└─────────────────────────┘
```

## S3 Bucket Structure

```
automotive-raw-data-lerato-2026/          ← Input (RAW)
  ├── erp/
  │   ├── sales_data.csv
  │   └── inventory.json
  ├── crm/
  │   └── customers.xlsx
  └── finance/
      └── transactions.parquet

automotive-staging-data-lerato-2026/       ← Output (STAGING)
  └── ingested/
      ├── sales_data.csv
      ├── inventory.json
      ├── customers.xlsx
      └── transactions.parquet
```

## Next Steps

1. ✅ Configure AWS credentials in docker-compose
2. ✅ Configure SMTP (Gmail or custom)
3. ✅ Configure Teams webhook (optional)
4. ✅ Upload test files to RAW bucket
5. ✅ Run Docker container
6. ✅ Check email/Teams for notifications
7. ✅ Verify files moved to STAGING

## Related Phases

- **Phase 1**: Data Warehouse Design (schema setup)
- **Phase 2**: Data Source Setup (S3 bucket creation)
- **Phase 4**: Python ETL (transforms STAGING data)
- **Phase 5**: Airflow Orchestration (orchestrates all phases)
- **Phase 6**: Streaming with Kafka (real-time alternatives)

---

**Status**: ✅ Production Ready  
**Last Updated**: March 2026
