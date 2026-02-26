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
S3 Raw Bucket (staging area)
    ↓
Airflow event_driven_real_time_etl (ETL)
    ↓
PostgreSQL Warehouse (Analytics)
```

---

### 🏗️ Components

#### 1. **Kafka Infrastructure** (`docker-compose.yml`)
- **Apache Kafka** (broker): Message bus for real-time events
- **Zookeeper**: Cluster coordination & metadata management
- **Kafka UI**: Web interface to monitor topics and messages

#### 2. **Producer Scripts** (`kafka_producer.py`)
Simulates 6 different ERP/CRM systems generating events:
- **Sales**: New vehicle sales transactions
- **Payments**: Payment processing events
- **Interactions**: Customer interactions (calls, emails, visits)
- **Inventory**: Stock level updates
- **Procurement**: Supplier orders and receipts
- **Telemetry**: Real-time vehicle GPS/sensor data

Each event includes realistic data (VINs, customer IDs, timestamps, etc.).

#### 3. **Consumer** (`kafka_consumer.py`)
- Listens to all Kafka topics
- Batches messages (100 events or 5 minutes, whichever comes first)
- Writes batches to S3 as CSV files
- Automatically triggers Airflow detection

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

Expected output:
```
✅ Kafka Infrastructure Started!
   - Kafka Broker: localhost:9092
   - Zookeeper: localhost:2181
   - Kafka UI: http://localhost:8888
```

#### Step 2: Start Producers (Simulated ERP/CRM)
```bash
# All systems continuously (5-second interval)
python orchestrator.py --producers all --interval 5

# Single system only
python orchestrator.py --producers sales --interval 5

# Limited to 100 events
python orchestrator.py --producers all --count 100
```

You'll see output like:
```
✓ Published sales_#1: SALE-A1B2C3D4
✓ Published payments_#2: PAY-E5F6G7H8
✓ Published interactions_#3: INT-I9J0K1L2
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
- Writes to S3: `s3://automotive-raw-data-lerato-2026/[data_type]/`

Output example:
```
✓ Flushed 100 sales events → s3://automotive-raw-data-lerato-2026/sales/sales_20260226_102345.csv
✓ Flushed 100 payments events → s3://automotive-raw-data-lerato-2026/payments/payments_20260226_102346.csv
```

#### Step 4: Monitor Data Flow
1. **Kafka UI**: http://localhost:8888
   - View topics and message counts
   - See messages in real-time
   - Monitor consumer lag

2. **S3 Raw Bucket**:
   - Check `s3://automotive-raw-data-lerato-2026/[data_type]/`
   - New CSV files appear every 5 minutes or 100 messages

3. **Airflow**:
   - Airflow `event_driven_real_time_etl` DAG auto-triggers
   - Monitors S3 for new files
   - Processes through ETL pipeline

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
python orchestrator.py --producers sales           # Sales only
python orchestrator.py --producers payments        # Payments only
python orchestrator.py --producers interactions    # Interactions only
python orchestrator.py --producers inventory       # Inventory only
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
  "event_type": "sales|payments|interactions|inventory|procurement|telemetry",
  "event_id": "SALE-A1B2C3D4",
  "timestamp": "2026-02-26T10:30:45.123456",
  ...event-specific fields...
}
```

#### Topic to S3 Mapping
| Kafka Topic | S3 Folder | CSV Format |
|------------|-----------|-----------|
| sales_topic | sales/ | sales_YYYYMMDD_HHMMSS.csv |
| payments_topic | payments/ | payments_YYYYMMDD_HHMMSS.csv |
| interactions_topic | interactions/ | interactions_YYYYMMDD_HHMMSS.csv |
| inventory_topic | inventory/ | inventory_YYYYMMDD_HHMMSS.csv |
| procurement_topic | procurement/ | procurement_YYYYMMDD_HHMMSS.csv |
| telemetry_topic | telemetry/ | telemetry_YYYYMMDD_HHMMSS.csv |

---

### 🔍 Monitoring

#### Kafka UI (http://localhost:8888)
- **Topics Tab**: View all 6 topics + message counts
- **Messages Tab**: Inspect individual events
- **Consumer Groups**: Track `automotive-consumer-group` lag

#### Docker Status
```bash
docker-compose -f docker-compose.yml ps
```

#### AWS S3
```bash
# Monitor raw bucket
aws s3 ls s3://automotive-raw-data-lerato-2026/sales/
aws s3 ls s3://automotive-raw-data-lerato-2026/payments/
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

# Observe S3 receives CSV batches after ~100 messages
```

#### Scenario 2: High-Volume Stress Test
```bash
# Terminal 1
python orchestrator.py --kafka-start

# Terminal 2
python orchestrator.py --producers all --interval 1 --count 1000

# Terminal 3
python orchestrator.py --consumer

# Monitor: Does consumer keep up? Check Kafka UI lag
```

#### Scenario 3: Single Data Type
```bash
# Test only telemetry (IoT sensor data)
python orchestrator.py --kafka-start
python orchestrator.py --producers telemetry --interval 2 --count 100
python orchestrator.py --consumer

# Check S3: s3://automotive-raw-data-lerato-2026/telemetry/
```

---

### 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Connection refused" on port 9092 | Run `--kafka-start` first; wait 10 sec |
| Consumer not batching to S3 | Check AWS credentials; verify RAW_BUCKET exists |
| Topics not appearing in Kafka UI | Producers must be running; topics auto-create |
| Producer hangs after starting | Check Kafka is healthy: `docker-compose ps` |
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
Airflow event_driven_real_time_etl (Phase 5)
        ↓
    Warehouse
```

**With Phase 6 (Streaming):**
```
Batch Files (Phase 3-4) ─┐
                        ├→ S3 Raw
Kafka Streams (Phase 6) ┘
        ↓
Airflow event_driven_real_time_etl (Phase 5)
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
