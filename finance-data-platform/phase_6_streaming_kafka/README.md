## Phase 6: Streaming with Kafka

### 📊 Overview

Phase 6 implements a **realistic streaming data pipeline** that simulates ERP/CRM systems sending real-time events into your automotive data warehouse. Instead of waiting for batch files, data arrives continuously through Kafka topics.

**Architecture Flow:**
```
Simulated ERP/CRM Systems (Producers)
    ↓
Kafka Topics (Message Bus)
    ↓
Kafka Consumers (Batch to S3)
    ↓
S3 Raw Bucket (canonical raw landing zone)
    ↓
Airflow automotive_finance_orchestration
    ↓
PostgreSQL Warehouse (Analytics)
```

Phase 6 now has a single supported streaming path:
- `orchestrator.py` manages Kafka startup, producer runs, consumer runs, and demo flows.
- `kafka_producer.py` publishes canonical event types.
- `kafka_consumer.py` batches those events into the existing raw S3 layout.

The streaming raw landing zone now matches the intended mixed-format structure:

```text
automotive-raw-data-lerato-2026/
├── erp/
│   ├── customers/      -> XLSX
│   ├── sales/          -> CSV
│   ├── vehicles/       -> CSV
│   ├── dealers/        -> XLSX
│   └── inventory/      -> CSV
├── crm/
│   └── interactions/   -> JSON
├── finance/
│   └── payments/       -> CSV
├── suppliers_chain/
│   ├── suppliers/      -> CSV
│   └── procurement/    -> CSV
└── iot/
    └── telemetry/      -> JSON
```

Older duplicate scripts were removed and are no longer part of the workflow.

---

### 🏗️ Components

#### 1. **Kafka Infrastructure** (`docker-compose.yml`)
- **Apache Kafka** (broker): Message bus for real-time events
- **Zookeeper**: Cluster coordination & metadata management
- **Kafka UI**: Web interface to monitor topics and messages

#### 2. **Producer Scripts** (`kafka_producer.py`)
Simulates 10 datasets across ERP, CRM, finance, supplier, and IoT domains:
- **Customers**: ERP customer master data written as XLSX
- **Sales**: Sales transactions written as CSV
- **Vehicles**: ERP vehicle master data written as CSV
- **Dealers**: ERP dealer master data written as XLSX
- **Inventory**: Inventory updates written as CSV
- **Interactions**: CRM interactions written as JSON
- **Payments**: Finance payments written as CSV
- **Suppliers**: Supplier reference data written as CSV
- **Procurement**: Procurement events written as CSV
- **Telemetry**: Vehicle telemetry written as JSON

Each event includes realistic fields aligned to the existing Phase 4 staging tables.

#### 3. **Consumer** (`kafka_consumer.py`)
- Listens to all Kafka topics
- Batches messages (100 events or 5 minutes, whichever comes first)
- Writes each dataset in its intended file format: CSV, JSON, or XLSX
- Lands files in the raw bucket first, then lets the single Airflow DAG pick them up on schedule or by manual trigger

#### 4. **Orchestrator** (`orchestrator.py`)
Command-line tool to manage the entire pipeline:
- Start/stop Kafka infrastructure
- Launch producers with custom intervals
- Start consumer
- Run complete end-to-end demo

---

### 🚀 Getting Started

#### Prerequisites
```bash
# Install Kafka Python client and AWS SDK
pip install -r requirements.txt

# Ensure Docker is running
docker --version
```

#### Step 1: Start Kafka Infrastructure
```bash
python orchestrator.py --kafka-start
```

This starts:
- Zookeeper (port 2181)
- Kafka Broker (port 9092)
- Kafka UI (http://localhost:8888)
- Airflow UI is available from the root stack at http://localhost:8080

As part of startup, the supported Phase 6 topics are pre-created before producers run. That prevents the first `--producers all` batch from losing early records while Kafka is auto-creating topics.

Expected output:
```
✅ Kafka Infrastructure Started!
   - Kafka Broker: localhost:9092
   - Zookeeper: localhost:2181
   - Kafka UI: http://localhost:8888
```

#### Step 2: Start Producers (Simulated Source Systems)
```bash
# All datasets continuously (5-second interval)
python orchestrator.py --producers all --interval 5

# Single dataset only
python orchestrator.py --producers sales --interval 5

# Limited to 100 events
python orchestrator.py --producers all --count 100
```

You'll see output like:
```
✓ Published customers_#1: CUST-004
✓ Published sales_#2: SALE-A1B2C3D4
✓ Published telemetry_#10: TEL-I9J0K1L2
```

#### Step 3: Start Consumer (Batches → S3)
In a new terminal:
```bash
python orchestrator.py --consumer
```

The consumer:
- Listens to all topics
- Accumulates messages
- Flushes every 100 messages or 5 minutes
- Writes to the canonical raw prefixes already used by the rest of the platform, preserving the intended per-dataset file formats

Output example:
```
✓ Flushed 100 sales events → s3://automotive-raw-data-lerato-2026/erp/sales/sales_20260226_102345.csv
✓ Flushed 100 customers events → s3://automotive-raw-data-lerato-2026/erp/customers/customers_2026_20260226_102346.xlsx
```

#### Step 4: Monitor Data Flow
1. **Kafka UI**: http://localhost:8888
   - View topics and message counts
   - See messages in real-time
   - Monitor consumer lag

2. **S3 Raw Bucket**:
    - Check the canonical raw prefixes such as:
        - `s3://automotive-raw-data-lerato-2026/erp/customers/`
      - `s3://automotive-raw-data-lerato-2026/erp/sales/`
        - `s3://automotive-raw-data-lerato-2026/erp/vehicles/`
        - `s3://automotive-raw-data-lerato-2026/erp/dealers/`
      - `s3://automotive-raw-data-lerato-2026/finance/payments/`
      - `s3://automotive-raw-data-lerato-2026/crm/interactions/`
      - `s3://automotive-raw-data-lerato-2026/erp/inventory/`
        - `s3://automotive-raw-data-lerato-2026/suppliers_chain/suppliers/`
      - `s3://automotive-raw-data-lerato-2026/suppliers_chain/procurement/`
      - `s3://automotive-raw-data-lerato-2026/iot/telemetry/`
    - New files appear every 5 minutes or 100 messages in CSV, JSON, or XLSX depending on dataset

3. **Airflow**:
    - Airflow `automotive_finance_orchestration` runs the end-to-end flow
    - Monitors S3 for new files
    - Executes Phase 3, Phase 4, archive, and notifications

#### Step 5: Trigger Airflow Safely For Streaming Tests
```bash
python trigger_dag_manually.py
```

This is the supported manual verification path after streamed files land in the raw bucket.

- The helper checks that raw S3 data exists before triggering Airflow.
- If the DAG is paused, it unpauses it temporarily.
- It waits for the triggered DAG run to reach a terminal state.
- It only re-pauses the DAG after the run finishes.

Use this blocking helper instead of manually pausing the DAG immediately after a trigger. That avoids interrupting the final downstream notification task before Airflow has queued it.

Optional flags:
```bash
python trigger_dag_manually.py --timeout-seconds 1200 --poll-seconds 15
python trigger_dag_manually.py --no-wait
```

If you use `--no-wait`, leave the DAG unpaused until the triggered run is complete, then pause it manually.

---

### 🎯 Complete Demo

Run the entire pipeline in one command:
```bash
python orchestrator.py --demo
```

This automatically:
1. ✅ Starts Kafka infrastructure
2. ✅ Launches producers (5 events over 30 sec)
3. ✅ Launches consumer (batches → S3)
4. ✅ Runs for 90 seconds
5. ✅ Stops all processes
6. ✅ Shows final status

Perfect for testing the complete flow!

---

### 📋 Command Reference

```bash
# Infrastructure Management
python orchestrator.py --kafka-start          # Start Kafka (Zookeeper + Broker + UI)
python orchestrator.py --kafka-stop           # Stop Kafka

# Producer Control
python orchestrator.py --producers all              # All systems (infinite)
python orchestrator.py --producers customers       # Customers only
python orchestrator.py --producers sales           # Sales only
python orchestrator.py --producers vehicles        # Vehicles only
python orchestrator.py --producers dealers         # Dealers only
python orchestrator.py --producers payments        # Payments only
python orchestrator.py --producers interactions    # Interactions only
python orchestrator.py --producers inventory       # Inventory only
python orchestrator.py --producers suppliers       # Suppliers only
python orchestrator.py --producers procurement     # Procurement only
python orchestrator.py --producers telemetry       # Telemetry only

# Producer Options
--interval 5        # Default: 5 seconds between events
--count 100         # Stop after 100 events (default: infinite)

# Consumer Control
python orchestrator.py --consumer                   # Start consumer (Kafka → S3)

# System Management
python orchestrator.py --status                     # Show Kafka status
python orchestrator.py --stop-all                   # Stop producers/consumers + Kafka
python orchestrator.py --demo                       # Run complete demo

# Direct Script Usage
python kafka_producer.py --type sales --interval 5 --count 100
python kafka_consumer.py --batch-size 50 --timeout 300
```

---

### 📊 Data Flow Visualization

#### Event Schema (All Types)
Every event includes:
```json
{
    "event_type": "customers|sales|vehicles|dealers|inventory|interactions|payments|suppliers|procurement|telemetry",
    "event_id": "dataset-specific id",
  "timestamp": "2026-02-26T10:30:45.123456",
  ...event-specific fields...
}
```

#### Topic to S3 Mapping
| Kafka Topic | S3 Folder | File Pattern |
|------------|-----------|-----------|
| customers_topic | erp/customers/ | customers_YYYY_YYYYMMDD_HHMMSS.xlsx |
| sales_topic | erp/sales/ | sales_YYYY_YYYYMMDD_HHMMSS.csv |
| vehicles_topic | erp/vehicles/ | vehicles_YYYY_YYYYMMDD_HHMMSS.csv |
| dealers_topic | erp/dealers/ | dealers_YYYY_YYYYMMDD_HHMMSS.xlsx |
| inventory_topic | erp/inventory/ | inventory_YYYY_YYYYMMDD_HHMMSS.csv |
| interactions_topic | crm/interactions/ | interactions_YYYY_YYYYMMDD_HHMMSS.json |
| payments_topic | finance/payments/ | payments_YYYY_YYYYMMDD_HHMMSS.csv |
| suppliers_topic | suppliers_chain/suppliers/ | suppliers_YYYY_YYYYMMDD_HHMMSS.csv |
| procurement_topic | suppliers_chain/procurement/ | procurement_YYYY_YYYYMMDD_HHMMSS.csv |
| telemetry_topic | iot/telemetry/ | telemetry_YYYY_YYYYMMDD_HHMMSS.json |

---

### 🔍 Monitoring

#### Kafka UI (http://localhost:8888)
- **Topics Tab**: View all 10 topics + message counts
- **Messages Tab**: Inspect individual events
- **Consumer Groups**: Track `automotive-consumer-group` lag

#### Docker Status
```bash
docker compose -f docker-compose.yml ps
```

#### AWS S3
```bash
# Monitor raw bucket
aws s3 ls s3://automotive-raw-data-lerato-2026/erp/customers/
aws s3 ls s3://automotive-raw-data-lerato-2026/erp/sales/
aws s3 ls s3://automotive-raw-data-lerato-2026/crm/interactions/
aws s3 ls s3://automotive-raw-data-lerato-2026/finance/payments/
```

#### Airflow Logs
```bash
# View ETL pipeline execution
docker logs phase_5_airflow_orchestration-airflow-scheduler-1
```

---

### ⚙️ Configuration

#### Batch Settings (`kafka_consumer.py`)
```python
BATCH_SIZE = 100          # Messages before flush
BATCH_TIMEOUT = 300       # Seconds before flush (5 min)
```

#### Producer Intervals
- **Default**: 5 seconds between events
- For high-volume: `--interval 1` (1 event/sec)
- For low-volume: `--interval 30` (1 event/30 sec)

#### S3 Configuration
```python
RAW_BUCKET = 'automotive-raw-data-lerato-2026'  # Must match your bucket
```

---

### 🧪 Testing Scenarios

#### Scenario 1: Quick Test
```bash
# Terminal 1
python orchestrator.py --kafka-start

# Terminal 2
python orchestrator.py --producers all --count 20

# Terminal 3
python orchestrator.py --consumer

# Terminal 4
python trigger_dag_manually.py
```

#### Scenario 2: High-Volume Stress Test
```bash
# Terminal 1
python orchestrator.py --kafka-start

# Terminal 2
python orchestrator.py --producers all --interval 1 --count 1000

# Terminal 3
python orchestrator.py --consumer

# Terminal 4
python trigger_dag_manually.py --timeout-seconds 1800
```

#### Scenario 3: Single Data Type
```bash
# Test only telemetry (IoT sensor data)
python orchestrator.py --kafka-start
python orchestrator.py --producers telemetry --interval 2 --count 100
python orchestrator.py --consumer
python trigger_dag_manually.py

# Check S3: s3://automotive-raw-data-lerato-2026/iot/telemetry/
```

---

### 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Connection refused" on port 9092 | Run `--kafka-start` first; wait 10 sec |
| Consumer not batching to S3 | Check AWS credentials; verify RAW_BUCKET exists |
| Topics not appearing in Kafka UI | Producers must be running; topics auto-create |
| Producer hangs after starting | Check Kafka is healthy: `docker compose ps` |
| No AWS credentials error | Set: `export AWS_ACCESS_KEY_ID=...` and `AWS_SECRET_ACCESS_KEY` |

---

### 📈 Performance Metrics

With default settings (5-second intervals):
- **Throughput**: ~12 events/minute per producer (all types)
- **Total**: ~72 events/minute (6 types)
- **Batch Size**: 100 messages = ~8 minutes fill-up
- **Or**: 5-minute timeout triggers flush
- **S3 File Size**: ~15-20 KB per batch (CSV)
- **Latency**: Event → Kafka: <100ms; Kafka → S3: <1 sec

---

### 🔗 Integration with Phases 1-5

**Current Architecture:**
```
Batch Files (Phase 3-4)
        ↓
    S3 Raw
        ↓
Airflow automotive_finance_orchestration (Phase 5)
        ↓
    Warehouse
```

**With Phase 6 (Streaming):**
```
Batch Files (Phase 3-4) ─┐
                        ├→ S3 Raw
Kafka Streams (Phase 6) ┘
        ↓
Airflow automotive_finance_orchestration (Phase 5)
        ↓
    Warehouse
```

The same Airflow DAG handles **both** batch and streaming data!

---

### 📚 References

- **Kafka Documentation**: https://kafka.apache.org/documentation/
- **Kafka Python Client**: https://github.com/dpkp/kafka-python
- **Docker Compose**: https://docs.docker.com/compose/
- **AWS S3**: https://docs.aws.amazon.com/s3/

---

### ✅ Phase 6 Checklist

- [x] Apache Kafka + Zookeeper setup (docker-compose)
- [x] Kafka UI for monitoring
- [x] Producer scripts for all 6 data types
- [x] Consumer script (batches → S3)
- [x] Orchestrator tool for easy management
- [x] Documentation and examples
- [x] Integration with existing Airflow pipeline

**Next Steps**: Monitor streaming data flow through complete warehouse pipeline!
