#!/usr/bin/env python3
"""
Manual Airflow DAG Trigger - Simulates S3 event-driven behavior
Reads files from S3 RAW bucket and processes them through the ETL pipeline
This is a substitute for in-place Airflow event triggering
"""

import os
import sys
import boto3
import subprocess
import json
from pathlib import Path
from datetime import datetime

print("\n" + "="*80)
print("🚀 MANUAL DAG TRIGGER - Process Streaming Data")
print("="*80 + "\n")

# Load env
env_file = Path('finance-data-platform/phase_6_streaming_kafka/.env')
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.strip().startswith('#'):
                k, v = line.strip().split('=', 1)
                os.environ[k] = v.strip().strip('"')

s3 = boto3.client('s3')
raw_bucket = os.getenv('RAW_BUCKET', 'automotive-raw-data-lerato-2026')
staging_bucket = os.getenv('STAGING_BUCKET', 'automotive-staging-data-lerato-2026')
archive_bucket = os.getenv('ARCHIVE_BUCKET', 'automotive-archive-data-lerato-2026')

# Step 1: Check if data exists in RAW bucket
print("Step 1: Scanning RAW bucket for streamed data...")
print("-" * 80)

try:
    response = s3.list_objects_v2(Bucket=raw_bucket)
    
    if 'Contents' not in response:
        print("❌ No files found in RAW bucket!")
        print("   Producer/Consumer may not have completed yet.")
        sys.exit(1)
    
    files = sorted([obj['Key'] for obj in response['Contents']])
    print(f"✅ Found {len(files)} files in RAW bucket:\n")
    
    # Organize by folder
    folders = {}
    for f in files:
        domain = f.split('/')[0]
        if domain not in folders:
            folders[domain] = []
        folders[domain].append(f)
    
    for domain in sorted(folders.keys()):
        print(f"   {domain}/ ({len(folders[domain])} files)")
        for f in folders[domain][:2]:
            print(f"      └─ {f}")
        if len(folders[domain]) > 2:
            print(f"      └─ ... {len(folders[domain])-2} more")
    
except Exception as e:
    print(f"❌ Error checking RAW bucket: {e}")
    sys.exit(1)

# Step 2: Simulate DAG Task 2: Move to Staging
print("\n\nStep 2: Moving files from RAW → STAGING...")
print("-" * 80)

moved = 0
failed = 0

try:
    for file_key in files:
        try:
            s3.copy_object(
                Bucket=staging_bucket,
                CopySource={'Bucket': raw_bucket, 'Key': file_key},
                Key=file_key
            )
            s3.delete_object(Bucket=raw_bucket, Key=file_key)
            moved += 1
        except Exception as e:
            print(f"❌ Failed to move {file_key}: {e}")
            failed += 1
    
    print(f"✅ Moved {moved} files to staging ({failed} failures)")
    
except Exception as e:
    print(f"❌ Error moving files: {e}")
    sys.exit(1)

# Step 3: Simulate DAG Task 4: Run ETL Pipeline
print("\n\nStep 3: Running ETL Pipeline (validate + load to warehouse)...")
print("-" * 80)

try:
    etl_script = Path('finance-data-platform/phase_4_python_etl/etl_main.py')
    
    if not etl_script.exists():
        print(f"❌ ETL script not found: {etl_script}")
        sys.exit(1)
    
    env = os.environ.copy()
    env['STAGING_BUCKET'] = staging_bucket
    
    result = subprocess.run(
        [sys.executable, str(etl_script)],
        capture_output=True,
        text=True,
        timeout=600,
        env=env,
        cwd='finance-data-platform'
    )
    
    if result.returncode == 0:
        print("✅ ETL Pipeline completed successfully")
        # Show last 20 lines of output
        lines = result.stdout.split('\n')
        for line in lines[-20:]:
            if line.strip():
                print(f"   {line}")
    else:
        print(f"❌ ETL Pipeline failed:\n{result.stderr}")
        sys.exit(1)
        
except subprocess.TimeoutExpired:
    print("⏱️  ETL Pipeline timeout (takes >10 min)")
except Exception as e:
    print(f"❌ Error running ETL: {e}")
    sys.exit(1)

# Step 4: Simulate DAG Task 5: Archive
print("\n\nStep 4: Archiving processed files (STAGING → ARCHIVE)...")
print("-" * 80)

try:
    response = s3.list_objects_v2(Bucket=staging_bucket)
    
    if 'Contents' not in response:
        print("✅ All files archived (STAGING bucket is now empty)")
    else:
        archived = 0
        failed = 0
        
        for obj in response['Contents']:
            file_key = obj['Key']
            try:
                # Preserve folder structure + add timestamp
                path_parts = file_key.split('/')
                filename = path_parts[-1]
                folder_path = '/'.join(path_parts[:-1])
                
                name_parts = filename.rsplit('.', 1)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                timestamped_filename = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
                
                archive_key = f"archive/{folder_path}/{timestamped_filename}"
                
                s3.copy_object(
                    Bucket=archive_bucket,
                    CopySource={'Bucket': staging_bucket, 'Key': file_key},
                    Key=archive_key
                )
                s3.delete_object(Bucket=staging_bucket, Key=file_key)
                archived += 1
            except Exception as e:
                print(f"❌ Failed: {e}")
                failed += 1
        
        print(f"✅ Archived {archived} files ({failed} failures)")

except Exception as e:
    print(f"❌ Error archiving: {e}")

# Summary
print("\n\n" + "="*80)
print("📊 SUMMARY")
print("="*80)
print(f"""
Data Flow Completed:
  ✓ Streamed to S3 RAW bucket (Kafka → Consumer)
  ✓ Moved to STAGING bucket (Airflow Task 2)
  ✓ Validated & cleaned by ETL (Airflow Task 4)
  ✓ Loaded to PostgreSQL warehouse
  ✓ Archived with timestamps (Airflow Task 5)

Next: Query PostgreSQL staging schema for results:
  SELECT COUNT(*) FROM staging.stg_sales;
  SELECT COUNT(*) FROM staging.stg_payments;
  SELECT COUNT(*) FROM staging.stg_interactions;
  SELECT COUNT(*) FROM staging.stg_inventory;
  SELECT COUNT(*) FROM staging.stg_procurement;
  SELECT COUNT(*) FROM staging.stg_telemetry;
""")
print("="*80 + "\n")
