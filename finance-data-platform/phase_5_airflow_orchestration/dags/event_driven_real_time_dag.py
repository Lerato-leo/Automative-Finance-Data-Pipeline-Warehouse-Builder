"""
Phase 5: Event-Driven Real-Time DAG
Triggered by S3 file arrivals for all transactional data types.
Schedule: Event-driven (no fixed schedule)
Latency target: <1 minute from file upload to warehouse
Data types: Sales, Payments, Interactions, Inventory, Procurement
Flow: Raw → Staging → Warehouse → Archive

FOLDER STRUCTURE PRESERVATION:
  All data moves while preserving domain-based folder hierarchy:
  
  Raw:     automotive-raw-data-lerato-2026/erp/sales/sales_file.csv
  Staging: automotive-staging-data-lerato-2026/erp/sales/sales_file.csv  (path preserved)
  Archive: automotive-archive-data-lerato-2026/erp/sales/sales_file_timestamp.csv (path preserved)
  
  Domain prefixes maintained: erp/, crm/, finance/, suppliers_chain/, iot/
  Ensures consistent organization across all buckets throughout pipeline.
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import logging
import subprocess
import sys
import os

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'email': ['data-alerts@automativedata.com'],
    'email_on_failure': True,
    'retries': 2,
    'retry_delay': timedelta(minutes=2),
    'execution_timeout': timedelta(minutes=30),
    'sla': timedelta(minutes=5),  # 5-minute SLA for real-time
}

dag = DAG(
    'event_driven_real_time_etl',
    default_args=default_args,
    description='Real-time ETL for all data types (sales, payments, interactions, inventory, procurement)',
    schedule_interval=None,  # Event-driven, not scheduled
    start_date=days_ago(1),
    catchup=False,
    tags=['event-driven', 'real-time', 'all-data-types'],
    max_active_runs=5,  # Allow up to 5 concurrent runs for different files
)

# ============================================
# TASK 1: SCAN RAW BUCKET FOR NEW FILES
# ============================================
def scan_raw_bucket(**context):
    """
    Scan raw S3 bucket for all new files (all data types).
    Supports: sales/, payments/, interactions/, inventory/, procurement/
    """
    import boto3
    
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    )
    bucket = os.getenv('RAW_BUCKET', 'automotive-raw-data-lerato-2026')
    
    try:
        # List all objects in raw bucket
        response = s3.list_objects_v2(Bucket=bucket)
        
        if 'Contents' not in response:
            logger.warning(f"No files found in {bucket}")
            return {'files': [], 'count': 0}
        
        # Filter out .keep files and get actual data files
        files = [
            obj['Key'] for obj in response['Contents'] 
            if not obj['Key'].endswith('.keep') and obj['Key'].endswith(('.csv', '.json', '.xlsx'))
        ]
        
        if not files:
            logger.warning("No data files found in raw bucket")
            return {'files': [], 'count': 0}
        
        logger.info(f"✓ Found {len(files)} files in raw bucket")
        
        # Push to XCom for next tasks
        context['task_instance'].xcom_push(key='file_list', value=files)
        context['task_instance'].xcom_push(key='file_count', value=len(files))
        
        return {'files': files, 'count': len(files)}
    
    except Exception as e:
        logger.error(f"✗ Error scanning raw bucket: {str(e)}")
        raise

scan_bucket = PythonOperator(
    task_id='scan_raw_bucket',
    python_callable=scan_raw_bucket,
    dag=dag,
)

# ============================================
# TASK 2: MOVE FILES FROM RAW TO STAGING
# ============================================
def move_to_staging(**context):
    """
    Move files from raw bucket to staging bucket.
    This ensures ETL pipeline has all files available.
    """
    import boto3
    
    file_list = context['task_instance'].xcom_pull(
        task_ids='scan_raw_bucket',
        key='file_list'
    ) or []
    
    if not file_list:
        logger.warning("No files to move")
        return {'moved_count': 0, 'failed_count': 0}
    
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    )
    
    raw_bucket = os.getenv('RAW_BUCKET', 'automotive-raw-data-lerato-2026')
    staging_bucket = os.getenv('STAGING_BUCKET', 'automotive-staging-data-lerato-2026')
    
    moved_count = 0
    failed_count = 0
    
    try:
        for file_key in file_list:
            try:
                # Copy from raw to staging
                s3.copy_object(
                    Bucket=staging_bucket,
                    CopySource={'Bucket': raw_bucket, 'Key': file_key},
                    Key=file_key
                )
                
                # Delete from raw
                s3.delete_object(Bucket=raw_bucket, Key=file_key)
                
                logger.info(f"  ✓ Moved {file_key} to staging")
                moved_count += 1
                
            except Exception as e:
                logger.error(f"  ✗ Failed to move {file_key}: {e}")
                failed_count += 1
        
        logger.info(f"✓ Moved {moved_count} files to staging ({failed_count} failures)")
        
        context['task_instance'].xcom_push(key='move_count', value=moved_count)
        return {'moved_count': moved_count, 'failed_count': failed_count}
        
    except Exception as e:
        logger.error(f"✗ Error during move operation: {e}")
        raise

move_staging = PythonOperator(
    task_id='move_raw_to_staging',
    python_callable=move_to_staging,
    dag=dag,
)

# ============================================
# TASK 3: DETECT FILE TYPES
# ============================================
def detect_file_types(**context):
    """
    Identify which data types are present in the batch.
    Returns list of data types for routing.
    """
    import boto3
    
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    )
    
    staging_bucket = os.getenv('STAGING_BUCKET', 'automotive-staging-data-lerato-2026')
    
    try:
        response = s3.list_objects_v2(Bucket=staging_bucket)
        
        if 'Contents' not in response:
            raise FileNotFoundError(f"No files in staging bucket")
        
        files = [obj['Key'] for obj in response['Contents'] if not obj['Key'].endswith('.keep')]
        
        # Detect data types from folder structure
        data_types = set()
        file_details = {}
        
        for f in files:
            parts = f.split('/')
            if len(parts) >= 2:
                data_type = parts[0]  # sales/, payments/, interactions/, etc.
                data_types.add(data_type)
                if data_type not in file_details:
                    file_details[data_type] = []
                file_details[data_type].append(f)
        
        logger.info(f"✓ Detected {len(data_types)} data types: {list(data_types)}")
        logger.info(f"  Total files: {len(files)}")
        
        context['task_instance'].xcom_push(key='data_types', value=list(data_types))
        context['task_instance'].xcom_push(key='total_files', value=len(files))
        context['task_instance'].xcom_push(key='file_details', value=file_details)
        
        return {'data_types': list(data_types), 'total_files': len(files)}
        
    except Exception as e:
        logger.error(f"✗ Error detecting file types: {e}")
        raise

detect_types = PythonOperator(
    task_id='detect_file_types',
    python_callable=detect_file_types,
    dag=dag,
)

# ============================================
# TASK 4: RUN ETL PIPELINE (ALL DATA TYPES)
# ============================================
def run_etl_pipeline(**context):
    """
    Execute the unified ETL pipeline that processes all data types:
    - Sales
    - Payments
    - Interactions
    - Inventory
    - Procurement
    
    The etl_main.py handles:
    1. S3 staging → PostgreSQL staging schema
    2. Staging → Warehouse with SCD2, surrogate keys, date dimensions
    """
    data_types = context['task_instance'].xcom_pull(
        task_ids='detect_file_types',
        key='data_types'
    )
    
    total_files = context['task_instance'].xcom_pull(
        task_ids='detect_file_types',
        key='total_files'
    )
    
    logger.info(f"Running ETL pipeline for {len(data_types)} data types ({total_files} files)...")
    logger.info(f"Data types: {data_types}")
    
    try:
        etl_script = '/opt/airflow/etl_scripts/etl_main.py'
        
        # Prepare environment with AWS credentials
        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = os.getenv('AWS_ACCESS_KEY_ID', '')
        env['AWS_SECRET_ACCESS_KEY'] = os.getenv('AWS_SECRET_ACCESS_KEY', '')
        env['AWS_DEFAULT_REGION'] = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        
        # Run ETL subprocess
        result = subprocess.run(
            [sys.executable, etl_script],
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutes for full ETL
            env=env
        )
        
        if result.returncode != 0:
            logger.error(f"ETL Pipeline failed:\n{result.stderr}")
            raise Exception(f"ETL failed: {result.stderr}")
        
        logger.info("✓ ETL Pipeline completed successfully")
        logger.info(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
        
        context['task_instance'].xcom_push(key='etl_status', value='success')
        
        return {
            'status': 'success',
            'data_types': data_types,
            'file_count': total_files
        }
    
    except Exception as e:
        logger.error(f"✗ ETL pipeline execution failed: {e}")
        raise

run_etl = PythonOperator(
    task_id='run_etl_pipeline',
    python_callable=run_etl_pipeline,
    provide_context=True,
    dag=dag,
)

# ============================================
# TASK 5: ARCHIVE PROCESSED FILES
# ============================================
def archive_all_files(**context):
    """
    Move processed files from staging to archive bucket with timestamp.
    Preserves data types folder structure in archive.
    """
    import boto3
    from datetime import datetime
    
    total_files = context['task_instance'].xcom_pull(
        task_ids='detect_file_types',
        key='total_files'
    )
    
    file_details = context['task_instance'].xcom_pull(
        task_ids='detect_file_types',
        key='file_details'
    ) or {}
    
    logger.info(f"Archiving {total_files} files from staging...")
    
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    )
    
    staging_bucket = os.getenv('STAGING_BUCKET', 'automotive-staging-data-lerato-2026')
    archive_bucket = os.getenv('ARCHIVE_BUCKET', 'automotive-archive-data-lerato-2026')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    archived_count = 0
    failed_count = 0
    
    try:
        for data_type, files in file_details.items():
            for file_key in files:
                try:
                    # Preserve full folder structure: staging/erp/sales/file.csv → archive/erp/sales/file_timestamp.csv
                    # Split file_key into directory path and filename
                    path_parts = file_key.split('/')
                    filename = path_parts[-1]
                    folder_path = '/'.join(path_parts[:-1])  # e.g., "erp/sales"
                    
                    # Add timestamp to filename
                    name_parts = filename.rsplit('.', 1)
                    timestamped_filename = f"{name_parts[0]}_{timestamp}.{name_parts[1]}" if len(name_parts) > 1 else f"{filename}_{timestamp}"
                    
                    # Archive with full folder structure preserved: archive/erp/sales/file_timestamp.csv
                    archive_key = f"archive/{folder_path}/{timestamped_filename}"
                    
                    # Copy to archive
                    s3.copy_object(
                        Bucket=archive_bucket,
                        CopySource={'Bucket': staging_bucket, 'Key': file_key},
                        Key=archive_key
                    )
                    
                    # Delete from staging
                    s3.delete_object(Bucket=staging_bucket, Key=file_key)
                    
                    logger.info(f"  ✓ Archived {file_key} → {archive_key}")
                    archived_count += 1
                    
                except Exception as e:
                    logger.error(f"  ✗ Failed to archive {file_key}: {e}")
                    failed_count += 1
        
        logger.info(f"✓ Archived {archived_count} files ({failed_count} failures)")
        
        context['task_instance'].xcom_push(key='archive_count', value=archived_count)
        
        return {'archived': archived_count, 'failed': failed_count}
    
    except Exception as e:
        logger.error(f"✗ Archiving failed: {e}")
        raise

archive_files = PythonOperator(
    task_id='archive_processed_files',
    python_callable=archive_all_files,
    provide_context=True,
    dag=dag,
)

# ============================================
# TASK 6: SLA COMPLIANCE CHECK
# ============================================
def check_sla_compliance(**context):
    """
    Verify that real-time SLA was met (<5 minutes end-to-end).
    Measures from DAG execution_date (data_interval_start) to now.
    """
    from datetime import datetime, timezone
    
    task_instance = context['task_instance']
    dag_run = context['dag_run']
    
    # Get DAG run start time (execution start, not scheduled time)
    dag_start_time = dag_run.start_date
    
    # Get current UTC time (not local time)
    current_time = datetime.now(timezone.utc)
    
    # Calculate elapsed time in minutes
    elapsed = (current_time - dag_start_time).total_seconds() / 60
    sla_minutes = 5
    
    logger.info(f"✓ SLA Check: DAG started at {dag_start_time}, now {current_time}")
    logger.info(f"  Elapsed: {elapsed:.2f} minutes (SLA limit: {sla_minutes} minutes)")
    
    if elapsed <= sla_minutes:
        logger.info(f"✓ SLA MET: Completed in {elapsed:.2f} minutes")
        status = 'PASSED'
    else:
        logger.warning(f"⚠ SLA MISSED: Took {elapsed:.2f} minutes (exceeded by {elapsed - sla_minutes:.2f} min)")
        status = 'FAILED'
        # Don't fail the task, just log warning
    
    context['task_instance'].xcom_push(key='sla_status', value=status)
    context['task_instance'].xcom_push(key='elapsed_minutes', value=elapsed)
    
    return {'status': status, 'elapsed_minutes': elapsed}

check_sla = PythonOperator(
    task_id='check_sla_compliance',
    python_callable=check_sla_compliance,
    provide_context=True,
    dag=dag,
)

# ============================================
# DAG TASK DEPENDENCIES
# ============================================
# Sequence: Scan → Move → Detect Types → ETL → Archive → SLA Check
scan_bucket >> move_staging >> detect_types >> run_etl >> archive_files >> check_sla
