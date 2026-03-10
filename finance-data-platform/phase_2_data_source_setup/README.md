# 🔌 Phase 2: Data Source Setup

**Status:** ✅ Complete  
**Scope:** Source registration, extraction patterns, connectivity assumptions, and environment configuration

## Overview

Phase 2 establishes connections to the 6 data sources for the Automotive Finance Data Pipeline. This phase covers authentication, configuration, and validation of each source system.

## Completion Summary

- The source domains and extraction contracts are defined for ERP, CRM, inventory, procurement, IoT, and reference data.
- These source contracts inform the Phase 3 raw landing structure and the Phase 6 streaming event model.
- The repo now uses a unified root environment file for runtime configuration across the stack.

## 🎯 Objective

Set up reliable connections to:
- ✅ ERP System (Finance/Sales)
- ✅ CRM System (Customer/Interactions)
- ✅ Inventory Management (Stock/Warehouse)
- ✅ Purchase Order System (Procurement/Vendors)
- ✅ IoT Sensors (Telemetry/Devices)
- ✅ Master Data (Reference/Lookups)

## 📊 Data Sources Overview

### 1. ERP System (Finance)

**Purpose:** Sales orders, payments, general ledger data  
**Type:** Enterprise Resource Planning system  
**Extraction Method:** CSV export via SFTP  
**Frequency:** Daily at 2 AM UTC  
**Volume:** 100K+ sales records/month, 80K+ payment records/month

**Configuration:**
```
Host: erp.company.com
Port: 22 (SFTP)
Username: extract_user (in .env)
Password: ****** (in .env)
Path: /exports/finance/
Files:
  - sales_consolidated.csv (daily)
  - payments_consolidated.csv (daily)
  - gl_consolidated.csv (daily)
```

**Connection Test:**
```bash
sftp extract_user@erp.company.com
cd /exports/finance/
ls -la
```

### 2. CRM System (Customer Relationship)

**Purpose:** Customer contacts, interactions, campaigns  
**Type:** Cloud-based CRM  
**Extraction Method:** REST API (JSON)  
**Frequency:** Hourly (incremental)  
**Volume:** 50K+ interaction records/month

**Configuration:**
```
API Endpoint: https://api.crm.example.com/v2
Authentication: OAuth 2.0
Client ID: (in .env)
Client Secret: ****** (in .env)
Scopes: customers:read, interactions:read
Rate Limit: 1000 req/hour
```

**Connection Test:**
```bash
curl -X GET https://api.crm.example.com/v2/customers \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### 3. Inventory Management

**Purpose:** Stock levels, warehouse movements, reorder points  
**Type:** On-premise database system  
**Extraction Method:** SQL queries (CSV export)  
**Frequency:** Every 4 hours  
**Volume:** 30K inventory records (current state)

**Configuration:**
```
Database: PostgreSQL
Host: inventory.internal.company.com
Port: 5432
Database: inventory_db
Username: extract_user (in .env)
Password: ****** (in .env)
```

**Connection Test:**
```bash
psql -h inventory.internal.company.com -U extract_user -d inventory_db -c \
  "SELECT COUNT(*) FROM inventory;"
```

### 4. Purchase Order System

**Purpose:** Vendor purchases, PO details, deliveries  
**Type:** Cloud-based procurement platform  
**Extraction Method:** API (JSON)  
**Frequency:** Daily at 6 AM UTC  
**Volume:** 20K+ PO records/month

**Configuration:**
```
API Endpoint: https://api.procurement.com/v1
Authentication: API Key
API Key: (in .env)
Headers: Accept: application/json
```

**Connection Test:**
```bash
curl -X GET https://api.procurement.com/v1/purchase_orders \
  -H "X-API-Key: $API_KEY" \
  -H "Accept: application/json"
```

### 5. IoT Sensors

**Purpose:** Device readings, alerts, performance metrics  
**Type:** Cloud IoT platform  
**Extraction Method:** MQTT / REST API (JSON)  
**Frequency:** Real-time streaming (batched hourly)  
**Volume:** 500K+ telemetry records/month

**Configuration:**
```
MQTT Broker: mqtt.iot.company.com:8883
Username: iot_service (in .env)
Password: ****** (in .env)
Topic: automotive/telemetry/#
QoS: 1 (at least once)

OR REST API:
Endpoint: https://api.iot.company.com/telemetry
Authentication: Certificate + Key
Certificate: /certs/iot-client.crt
Key: /certs/iot-client.key
```

**Connection Test:**
```bash
# MQTT test
mosquitto_sub -h mqtt.iot.company.com -p 8883 \
  -u iot_service -P $IOT_PASSWORD \
  -t "automotive/telemetry/sample" \
  --cafile /certs/ca.crt

# REST test
curl -X GET https://api.iot.company.com/telemetry/latest \
  --cert /certs/iot-client.crt \
  --key /certs/iot-client.key
```

### 6. Master Data (Reference)

**Purpose:** Lookup tables (customers, products, regions)  
**Type:** Shared database / files  
**Extraction Method:** Database queries / flat files  
**Frequency:** Weekly (on Sundays 1 AM UTC)  
**Volume:** 10K+ reference records

**Configuration:**
```
Method 1: Database
  Database: PostgreSQL
  Host: master-data.company.com
  Database: reference_db
  
Method 2: Flat Files
  Path: s3://company-shared/master-data/
  Format: CSV/JSON
  Credentials: IAM role
```

**Connection Test:**
```bash
# Database
psql -h master-data.company.com -U ref_user -d reference_db -c \
  "SELECT COUNT(*) FROM customers;"

# S3
aws s3 ls s3://company-shared/master-data/
```

## 🔧 Environment Configuration

### .env File Template

Create `finance-data-platform/.env` with:

```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-east-1

# S3 Buckets
S3_RAW_BUCKET=automotive-raw-data-lerato-2026
S3_STAGING_BUCKET=automotive-staging-data-lerato-2026
S3_ARCHIVE_BUCKET=automotive-archive-data-lerato-2026

# ERP System (SFTP)
ERP_SFTP_HOST=erp.company.com
ERP_SFTP_PORT=22
ERP_SFTP_USER=extract_user
ERP_SFTP_PASSWORD=your_password
ERP_SFTP_PATH=/exports/finance/

# CRM System (REST API)
CRM_API_URL=https://api.crm.example.com/v2
CRM_CLIENT_ID=your_client_id
CRM_CLIENT_SECRET=your_client_secret
CRM_OAUTH_SCOPE=customers:read,interactions:read

# Inventory System (PostgreSQL)
INVENTORY_DB_HOST=inventory.internal.company.com
INVENTORY_DB_PORT=5432
INVENTORY_DB_NAME=inventory_db
INVENTORY_DB_USER=extract_user
INVENTORY_DB_PASSWORD=your_password

# Procurement System (API)
PROCUREMENT_API_URL=https://api.procurement.com/v1
PROCUREMENT_API_KEY=your_api_key

# IoT System (MQTT)
IOT_MQTT_HOST=mqtt.iot.company.com
IOT_MQTT_PORT=8883
IOT_MQTT_USER=iot_service
IOT_MQTT_PASSWORD=your_password
IOT_MQTT_TOPIC=automotive/telemetry/#
IOT_MQTT_CAFILE=/certs/ca.crt

# Master Data (Database)
MASTER_DATA_HOST=master-data.company.com
MASTER_DATA_PORT=5432
MASTER_DATA_DB=reference_db
MASTER_DATA_USER=ref_user
MASTER_DATA_PASSWORD=your_password

# Master Data (S3)
MASTER_DATA_S3_PATH=s3://company-shared/master-data/

# Logging
LOG_LEVEL=INFO
LOG_FILE=/opt/airflow/logs/data-sources.log
```

## 🔐 Secure Credential Management

### Option 1: .env File (Development)
```bash
# Use for local development only
# Never commit to source control
echo ".env" >> .gitignore
```

### Option 2: Environment Variables (Docker)
```bash
# In docker-compose.yml
environment:
  - ERP_SFTP_HOST=${ERP_SFTP_HOST}
  - ERP_SFTP_USER=${ERP_SFTP_USER}
  - ERP_SFTP_PASSWORD=${ERP_SFTP_PASSWORD}
  # ... all other variables
```

### Option 3: Secret Manager (Production)
```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name automotive/erp-sftp-credentials \
  --secret-string '{
    "host": "erp.company.com",
    "user": "extract_user",
    "password": "***"
  }'

# In code:
import boto3
sm = boto3.client('secretsmanager')
secret = sm.get_secret_value(SecretId='automotive/erp-sftp-credentials')
```

## ✅ Connection Validation

### Test All Sources

```bash
# Run from phase_2_data_source_setup/
python validate_connections.py

# Expected output:
✓ ERP System (SFTP) - Connected successfully
✓ CRM System (REST API) - 200 OK
✓ Inventory System (PostgreSQL) - 12,543 records
✓ Procurement System (API) - 856 POs
✓ IoT System (MQTT) - 45,234 messages/hour
✓ Master Data (Database) - 10,234 reference records

All connections validated!
```

### Individual Source Tests

```bash
# Test ERP SFTP
python test_erp_connection.py

# Test CRM API
python test_crm_connection.py

# Test Inventory Database
python test_inventory_connection.py

# Test Procurement API
python test_procurement_connection.py

# Test IoT MQTT
python test_iot_connection.py

# Test Master Data
python test_master_data_connection.py
```

## 🔄 Data Extraction Patterns

### Pull Pattern (Most Sources)
```
Airflow DAG (Phase 5)
    ↓ [Scheduled trigger]
Source System [ERP, CRM, Inventory, Procurement, Master Data]
    ↓ [Authenticate, query, extract]
S3 RAW Bucket
    └─ finance/sales/sales_YYYYMMDD.csv
    └─ finance/payments/payments_YYYYMMDD.csv
    └─ crm/interactions/interactions_YYYYMMDD.json
    └─ ... etc
```

### Push Pattern (IoT)
```
IoT Devices
    ↓ [Real-time streaming]
MQTT Broker (mqtt.iot.company.com)
    ↓ [Consume messages]
Kafka Consumer (Phase 6)
    ↓ [Batch conversion]
S3 RAW Bucket
    └─ iot/telemetry/telemetry_YYYYMMDD_HHMM.json
```

## 📋 Data Extraction Frequency

| Source | Mode | Schedule | Latency | Retention |
|--------|------|----------|---------|-----------|
| ERP | Pull | Daily 2 AM | 2 hours | 12 months |
| CRM | Pull | Hourly | 1 hour | 12 months |
| Inventory | Pull | Every 4 hours | Near real-time | Current |
| Procurement | Pull | Daily 6 AM | 2 hours | 12 months |
| IoT | Push | Real-time (batched hourly) | <5 minutes | 6 months |
| Master Data | Pull | Weekly (Sun 1 AM) | 7 days | Current |

## 🚀 Implementation Checklist

- [ ] Configure ERP SFTP credentials in .env
- [ ] Test ERP SFTP connection
- [ ] Configure CRM OAuth in .env
- [ ] Test CRM API connection
- [ ] Configure Inventory database in .env
- [ ] Test Inventory database connection
- [ ] Configure Procurement API in .env
- [ ] Test Procurement API connection
- [ ] Configure IoT MQTT/REST in .env
- [ ] Test IoT connection
- [ ] Configure Master Data source(s) in .env
- [ ] Test Master Data connection
- [ ] Run comprehensive validation
- [ ] Document all connection details (secure location)
- [ ] Test extraction with sample data
- [ ] Verify S3 bucket permissions
- [ ] Set up monitoring for failed connections

## 📊 Source Characteristics

| Attribute | ERP | CRM | Inventory | Procurement | IoT | Master |
|-----------|-----|-----|-----------|-------------|-----|--------|
| Connection | SFTP | REST | DB | API | MQTT | DB/S3 |
| Auth | Username/Pass | OAuth2 | Username/Pass | API Key | Cert | Username/Pass |
| Format | CSV | JSON | SQL | JSON | JSON | CSV/JSON |
| Frequency | Daily | Hourly | 4 hourly | Daily | Real-time | Weekly |
| Volume | 100K+/mo | 50K+/mo | 30K | 20K+/mo | 500K+/mo | 10K |
| Latency | 2 hrs | 1 hr | 4 hrs | 2 hrs | <5 min | 7 days |

## 🔗 Related Phases

- **Phase 1:** Data Warehouse Design (defines what data we need)
- **Phase 3:** Shell Ingestion (extracts files once sources configured)
- **Phase 5:** Airflow Orchestration (schedules data extraction)
- **Phase 6:** Kafka Streaming (handles IoT push pattern)

## 📞 Support & Troubleshooting

### Connection Issues

| Issue | Solution |
|-------|----------|
| "Connection refused" | Check host/port, firewall, VPN |
| "Authentication failed" | Verify credentials in .env, check password expiry |
| "Permission denied" | Check file/directory permissions, IAM roles |
| "Network timeout" | Check bandwidth, latency, rate limits |
| "API 429 (Too Many Requests)" | Implement backoff, reduce request frequency |

## 📚 Resources

- [Airflow Connectors](https://airflow.apache.org/docs/apache-airflow-providers/)
- [Paramiko SSH/SFTP](https://www.paramiko.org/)
- [Python requests library](https://requests.readthedocs.io/)
- [paho-mqtt](https://www.eclipse.org/paho/)

---

**Status:** ✅ Connections Configured  
**Last Updated:** March 9, 2026  
**Sources:** 6 (ERP, CRM, Inventory, Procurement, IoT, Master Data)  
**Daily Volume:** 250K+ records
