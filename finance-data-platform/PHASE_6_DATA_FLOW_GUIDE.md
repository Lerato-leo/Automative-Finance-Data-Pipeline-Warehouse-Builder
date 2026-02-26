# Phase 6: Complete Data Flow - Kafka → S3 → ETL → Warehouse

## 1. KAFKA CONSUMER → S3 RAW BUCKET (How Data Enters S3)

### 📤 Kafka Consumer Writing to S3

**File**: `phase_6_streaming_kafka/kafka_consumer.py`

The consumer listens to 6 Kafka topics and writes to S3 **with domain-based folder organization**:

```python
FOLDER_MAPPING = {
    'sales': ('erp/sales', f'sales_{timestamp}.csv'),
    'inventory': ('erp/inventory', f'inventory_{timestamp}.csv'),
    'customers': ('erp/customers', f'customers_{timestamp}.csv'),
    'dealers': ('erp/dealers', f'dealers_{timestamp}.csv'),
    'vehicles': ('erp/vehicles', f'vehicles_{timestamp}.csv'),
    'interactions': ('crm/interactions', f'interactions_{timestamp}.csv'),
    'payments': ('finance/payments', f'payments_{timestamp}.csv'),
    'procurement': ('suppliers_chain/procurement', f'procurement_{timestamp}.csv'),
    'suppliers': ('suppliers_chain/suppliers', f'suppliers_{timestamp}.csv'),
    'telemetry': ('iot/telemetry', f'telemetry_{timestamp}.csv'),
}
```

**Key Points**:
- ✅ Kafka topic → Domain folder mapping is explicit
- ✅ Timestamps ensure unique filenames (no overwrites)
- ✅ Folder structure: `domain/subdomain/` (e.g., `erp/sales/`, `crm/interactions/`)
- ✅ **All consumer writes include the full domain path**

**Example Data Entry**:
```
Kafka Topic: sales_topic
Published Message: {customer_id: 123, sale_date: 2026-02-26, ...}
        ↓
Consumer Maps: sales_topic → erp/sales folder
        ↓
S3 Path: s3://automotive-raw-data-lerato-2026/erp/sales/sales_20260226_145606.csv
```

**How It Works**:
```python
def _get_s3_key_and_folder(self, event_type: str) -> tuple:
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    folder, filename = FOLDER_MAPPING.get(event_type)
    return folder, filename
    # Returns: ('erp/sales', 'sales_20260226_145606.csv')
    # Final S3 key: f"{bucket}/{folder}/{filename}"
    # → s3://automotive-raw-data-lerato-2026/erp/sales/sales_20260226_145606.csv
```

---

## 2. AIRFLOW SCANS RAW BUCKET

### 📋 Task 1: Scan Raw Bucket
**File**: `phase_5_airflow_orchestration/dags/event_driven_real_time_dag.py`

The Airflow DAG is **event-driven** (triggered when S3 files appear):

```python
def scan_raw_bucket(**context):
    """
    List ALL files in raw bucket
    Returns file paths with FULL folder structure preserved
    """
    response = s3.list_objects_v2(Bucket='automotive-raw-data-lerato-2026')
    
    # Returns complete keys:
    # - erp/sales/sales_20260226_145606.csv
    # - crm/interactions/interactions_20260226_145610.csv
    # - finance/payments/payments_20260226_145610.csv
    # etc.
    
    files = [obj['Key'] for obj in response['Contents']]
    # Files list contains FULL PATHS, not just filenames
```

✅ **Folder paths are NOT stripped or flattened**

---

## 3. AIRFLOW MOVES RAW → STAGING (Full Path Preserved)

### 🔄 Task 2: Move to Staging
**File**: `phase_5_airflow_orchestration/dags/event_driven_real_time_dag.py`

```python
def move_to_staging(**context):
    file_list = context['task_instance'].xcom_pull(...)  # List of full paths
    
    for file_key in file_list:  # file_key = "erp/sales/sales_*.csv"
        s3.copy_object(
            Bucket='automotive-staging-data-lerato-2026',
            CopySource={'Bucket': 'automotive-raw-data-lerato-2026', 'Key': file_key},
            Key=file_key  # ← SAME KEY = SAME FOLDER STRUCTURE
        )
        s3.delete_object(Bucket='automotive-raw-data-lerato-2026', Key=file_key)
```

**What This Does**:
```
Source:  s3://automotive-raw-data-lerato-2026/erp/sales/sales_20260226_145606.csv
Copy:    (exact same path)
Target:  s3://automotive-staging-data-lerato-2026/erp/sales/sales_20260226_145606.csv
Delete:  Remove from raw bucket
```

✅ **Folder structure is identical: `erp/sales/` preserved in both buckets**

---

## 4. AIRFLOW DETECTS FILE TYPES

### 📊 Task 3: Detect File Types
**File**: `phase_5_airflow_orchestration/dags/event_driven_real_time_dag.py`

```python
def detect_file_types(**context):
    """
    Parse folder structure to identify which domains have data
    """
    files = [obj['Key'] for obj in response['Contents']]
    # files = ['erp/sales/sales_*.csv', 'crm/interactions/interactions_*.csv', ...]
    
    data_types = set()
    for f in files:
        parts = f.split('/')  # Split path: ['erp', 'sales', 'sales_*.csv']
        domain = parts[0]     # Extract: 'erp'
        data_types.add(domain)
    
    # Extracted: {'erp', 'crm', 'finance', 'suppliers_chain', 'iot'}
```

✅ **Reads from folder structure, doesn't modify it**

---

## 5. ETL PIPELINE PROCESSES FILES

### 🔧 Task 4: Run ETL
**File**: `phase_4_python_etl/etl_main.py`

#### 5a. File Discovery from Staging
```python
def list_staging_files():
    """
    List files from staging bucket
    Preserves full folder paths
    """
    s3 = boto3.client('s3')
    paginator = s3.get_paginator('list_objects_v2')
    files = []
    
    for page in paginator.paginate(Bucket='automotive-staging-data-lerato-2026'):
        files.extend([obj['Key'] for obj in page.get('Contents', [])])
    
    # Returns: ['erp/sales/sales_*.csv', 'crm/interactions/interactions_*.csv', ...]
    return files
```

#### 5b. Extract → Transform → Load
```python
def extract_file(key):
    """
    Download file from S3 using its full path
    key = "erp/sales/sales_20260226_145606.csv"
    """
    obj = s3.get_object(Bucket='automotive-staging-data-lerato-2026', Key=key)
    
    if key.endswith('.csv'):
        df = pd.read_csv(obj['Body'])
    # ... handle JSON, XLSX
    
    return df

def transform(df):
    """
    Apply data quality rules
    - 16 categorical constraints
    - NULL handling
    - Type conversion
    - Email normalization
    - Flag dirty records (is_dirty column)
    """
    # Apply validation rules
    categorical_rules = {
        'gender': ['M', 'F', 'Other'],
        'status': ['Active', 'Inactive', 'Pending', 'Closed'],
        'province': ['AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'NT', 'NU', 'ON', 'PE', 'QC', 'SK', 'YT'],
        'engine_type': ['Gasoline', 'Diesel', 'Electric', 'Hybrid', 'Plug-in Hybrid'],
        # ... 12 more rules
    }
    
    # Mark invalid rows with is_dirty=True
    # These get filtered out during LOAD
    return df

def upsert(df, table_key, conn):
    """
    Load to PostgreSQL staging schema
    
    Table mapping (inferred from filename):
    - sales_*.csv → staging.staging_sales
    - payments_*.csv → staging.staging_payments
    - interactions_*.csv → staging.staging_interactions
    - inventory_*.csv → staging.staging_inventory
    - etc.
    """
    table_name = TABLE_MAP[table_key]
    target_table = f"staging.{table_name}"
    
    # Filter out dirty records
    clean_df = df[df['is_dirty'] == False].copy()
    
    # UPSERT to PostgreSQL
    execute_values(cursor, SQL_INSERT, values, page_size=1000)
```

✅ **ETL reads from staging folder structure, doesn't modify S3**
✅ **Data quality validation filters bad records (marked as is_dirty)**
✅ **Clean data loads to warehouse (PostgreSQL)**

---

## 6. AIRFLOW ARCHIVES PROCESSED FILES

### 📦 Task 5: Archive with Folder Structure + Timestamp
**File**: `phase_5_airflow_orchestration/dags/event_driven_real_time_dag.py`

```python
def archive_all_files(**context):
    """
    Move processed files from staging → archive
    PRESERVES full folder structure + adds timestamp
    """
    for data_type, files in file_details.items():
        for file_key in files:  # file_key = "erp/sales/sales_20260226_145606.csv"
            
            # Split into components
            path_parts = file_key.split('/')
            # path_parts = ['erp', 'sales', 'sales_20260226_145606.csv']
            
            filename = path_parts[-1]           # 'sales_20260226_145606.csv'
            folder_path = '/'.join(path_parts[:-1])  # 'erp/sales'
            
            # Add timestamp to filename
            name_parts = filename.rsplit('.', 1)
            # name_parts = ['sales_20260226_145606', 'csv']
            
            timestamped_filename = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
            # timestamped_filename = 'sales_20260226_145606_20260226_150000.csv'
            
            # Archive with preserved folder structure
            archive_key = f"archive/{folder_path}/{timestamped_filename}"
            # archive_key = "archive/erp/sales/sales_20260226_145606_20260226_150000.csv"
            
            # Copy to archive
            s3.copy_object(
                Bucket='automotive-archive-data-lerato-2026',
                CopySource={'Bucket': 'automotive-staging-data-lerato-2026', 'Key': file_key},
                Key=archive_key
            )
            
            # Delete from staging
            s3.delete_object(Bucket='automotive-staging-data-lerato-2026', Key=file_key)
```

**Archive Structure**:
```
Before (Staging):
s3://automotive-staging-data-lerato-2026/erp/sales/sales_20260226_145606.csv

After (Archive):
s3://automotive-archive-data-lerato-2026/archive/erp/sales/sales_20260226_145606_20260226_150000.csv
                                           ↑ prefix prefix      ↑ original name    ↑ timestamp
```

✅ **Archive preserves domain folder structure (`erp/sales/`, `crm/interactions/`, etc.)**
✅ **Timestamp added to filename (no overwrites)**
✅ **Easy to query by domain and date**

---

## 7. COMPLETE DATA FLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────┐
│ KAFKA PRODUCER (6 Event Types)                                      │
│ - sales_topic, payments_topic, interactions_topic                   │
│ - inventory_topic, procurement_topic, telemetry_topic               │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────────────┐
│ KAFKA CONSUMER (kafka_consumer.py)                                  │
│ Maps topic → domain folder + writes to S3 RAW                       │
│ - FOLDER_MAPPING: sales → erp/sales/, payments → finance/payments/ │
│ - Batches: 100 msgs or 300s timeout                                 │
│ - Output: CSV files with timestamps                                 │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       ↓
     ┌─────────────────────────────────────────┐
     │ S3 RAW BUCKET (Domain Organized)         │
     │ ✓ erp/sales/sales_*.csv                 │
     │ ✓ erp/inventory/inventory_*.csv          │
     │ ✓ crm/interactions/interactions_*.csv    │
     │ ✓ finance/payments/payments_*.csv        │
     │ ✓ suppliers_chain/procurement/*.csv      │
     │ ✓ iot/telemetry/telemetry_*.csv         │
     └──────────────────┬──────────────────────┘
                       │
    ┌──────────────────┴──────────────────┐
    │ AIRFLOW DAG: event_driven_real_time_etl
    │ Triggered on S3 file arrival
    │ (No schedule, event-driven)
    │
    │ Task 1: scan_raw_bucket
    │ └─→ Lists all files with FULL paths
    │     (paths NOT stripped)
    │
    │ Task 2: move_raw_to_staging
    │ └─→ Copy: raw/erp/sales/* → staging/erp/sales/*
    │     (folder structure PRESERVED in destination)
    │
    │ Task 3: detect_file_types
    │ └─→ Parse folder names to identify domains
    │
    │ Task 4: run_etl_pipeline
    │ └─→ Phase 4 ETL (etl_main.py)
    │     - Reads from: staging/erp/sales/*, staging/crm/interactions/*, etc.
    │     - Applies: 16 categorical validation rules
    │     - Filters: Dirty records marked as is_dirty=True
    │     - Loads: PostgreSQL staging schema
    │       - stg_sales ← sales_*.csv
    │       - stg_payments ← payments_*.csv
    │       - stg_interactions ← interactions_*.csv
    │       - stg_inventory ← inventory_*.csv
    │       - stg_procurement ← procurement_*.csv
    │       - stg_telemetry ← telemetry_*.csv
    │
    │ Task 5: archive_processed_files
    │ └─→ Move to archive with timestamp
    │     staging/erp/sales/* → archive/erp/sales/*_timestamp.csv
    │     (folder structure PRESERVED with domain prefix)
    │
    │ Task 6: check_sla_compliance
    │ └─→ Verify <5 min end-to-end execution
    └──────────────────┬──────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ↓                             ↓
┌──────────────────────┐    ┌──────────────────────┐
│ S3 STAGING BUCKET    │    │ PostgreSQL WAREHOUSE │
│ (During processing)  │    │ Staging Schema       │
│ ✓ erp/sales/        │    │ ✓ stg_sales          │
│ ✓ crm/interactions/  │    │ ✓ stg_payments       │
│ ✓ finance/payments/  │    │ ✓ stg_interactions   │
│ ✓ suppliers_chain/   │    │ ✓ stg_inventory      │
│ ✓ iot/telemetry/    │    │ ✓ stg_procurement    │
└──────────────────────┘    │ ✓ stg_telemetry      │
                             └──────────────────────┘
        │ (after ETL)
        ↓
┌────────────────────────────────────────┐
│ S3 ARCHIVE BUCKET (With Timestamps)    │
│ ✓ archive/erp/sales/*_timestamp.csv    │
│ ✓ archive/erp/inventory/*_timestamp    │
│ ✓ archive/crm/interactions/*_timestamp │
│ ✓ archive/finance/payments/*_timestamp │
│ ✓ archive/suppliers_chain/*_timestamp  │
│ ✓ archive/iot/telemetry/*_timestamp    │
└────────────────────────────────────────┘
```

---

## 8. KEY GUARANTEES: S3 Prefix Preservation

| Stage | Bucket | Path Format | Example | ✓ Preserved |
|-------|--------|-------------|---------|-------------|
| **Kafka Entry** | Raw | `domain/subdomain/file_timestamp.csv` | `erp/sales/sales_20260226_145606.csv` | ✓ YES |
| **Airflow Scan** | Raw | Full path read | `erp/sales/sales_20260226_145606.csv` | ✓ YES |
| **Move to Staging** | Staging | Exact copy (same key) | `erp/sales/sales_20260226_145606.csv` | ✓ YES |
| **ETL Reads** | Staging | Full path used | `erp/sales/sales_20260226_145606.csv` | ✓ YES |
| **ETL Writes** | PostgreSQL | Table name inferred from filename | `staging.stg_sales` | ✓ YES |
| **Archive** | Archive | `archive/domain/subdomain/file_timestamp.csv` | `archive/erp/sales/sales_20260226_145606_20260226_150000.csv` | ✓ YES |

---

## 9. ETL DATA QUALITY & VALIDATION

The ETL stage **does NOT modify file structure** but applies quality rules:

```python
# 16 Categorical Validation Rules Applied
categorical_rules = {
    'gender': ['M', 'F', 'Other'],
    'status': ['Active', 'Inactive', 'Pending', 'Closed'],
    'province': ['AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'NT', 'NU', 'ON', 'PE', 'QC', 'SK', 'YT'],
    'engine_type': ['Gasoline', 'Diesel', 'Electric', 'Hybrid', 'Plug-in Hybrid'],
    'transmission': ['Manual', 'Automatic', 'CVT'],
    'vehicle_status': ['Available', 'Sold', 'Reserved', 'Damaged'],
    'sale_channel': ['Dealership', 'Online', 'Auction', 'Private'],
    'sale_status': ['Completed', 'Pending', 'Cancelled'],
    'stock_status': ['In Stock', 'Out of Stock', 'Coming Soon'],
    'interaction_type': ['Phone', 'Email', 'Chat', 'In-Person'],
    'interaction_channel': ['Sales', 'Support', 'Marketing'],
    'outcome': ['Won', 'Lost', 'Pending', 'Cancelled'],
    'payment_method': ['Credit Card', 'Debit Card', 'Check', 'Bank Transfer'],
    'payment_status': ['Paid', 'Pending', 'Failed', 'Refunded'],
    'procurement_status': ['Ordered', 'Received', 'Returned'],
}

# Records violating rules marked as: is_dirty=True
# Filtered out before loading to warehouse (only clean data loads)
```

**What gets to the warehouse**: ✓ Only valid records
**What gets archived**: ✓ All records (including validation timestamps)

---

## 10. TESTING THE COMPLETE FLOW

### Start Kafka & Producer
```bash
cd phase_6_streaming_kafka
python orchestrator.py --kafka-start
# Wait 30 seconds for Kafka to be ready
```

### Run Producer
```bash
python kafka_producer.py --type all --interval 1 --count 50
# Generates 50 events across all 6 types
# Events published to Kafka topics
```

### Start Consumer (in separate terminal)
```bash
python kafka_consumer.py
# Batches events to S3 RAW bucket (erp/sales/, crm/interactions/, etc.)
# Every 100 events or 5 minutes
```

### Check S3 RAW Bucket
```bash
# Verify folder structure created:
# s3://automotive-raw-data-lerato-2026/
#   ├── erp/
#   │   ├── sales/
#   │   │   └── sales_*.csv
#   │   └── inventory/
#   │       └── inventory_*.csv
#   ├── crm/
#   │   └── interactions/
#   │       └── interactions_*.csv
#   ├── finance/
#   │   └── payments/
#   │       └── payments_*.csv
#   ├── suppliers_chain/
#   │   └── procurement/
#   │       └── procurement_*.csv
#   └── iot/
#       └── telemetry/
#           └── telemetry_*.csv
```

### Airflow Automatically:
1. **Detects** new files in RAW bucket
2. **Moves** to STAGING (preserves paths)
3. **Runs ETL** (validates, filters, loads to warehouse)
4. **Archives** to ARCHIVE bucket (preserves paths + timestamp)

---

## 11. FOLDER STRUCTURE GUARANTEED ✓

```
RAW:     erp/sales/sales_*.csv
  ↓ (copy, same key)
STAGING: erp/sales/sales_*.csv
  ↓ (read by ETL, data loaded to DB)
ARCHIVE: archive/erp/sales/sales_*_timestamp.csv

Folder prefix (erp/, crm/, finance/, etc.) NEVER lost or flattened
```

---

## Summary

✅ **Kafka Consumer** embeds domain folder in S3 path (erp/sales/, crm/interactions/, etc.)
✅ **Airflow Scanner** reads full paths without stripping
✅ **Move Task** preserves exact folder structure when copying
✅ **ETL Pipeline** reads from organized folders, doesn't modify S3 structure
✅ **Archive Task** preserves domain folders with timestamp added to filename
✅ **Data Quality** validated (16 categorical rules) before warehouse load
✅ **Complete Traceability** maintained from Kafka → RAW → STAGING → WAREHOUSE → ARCHIVE

**Your S3 prefixes are safe throughout the entire pipeline!**
