#!/usr/bin/env python3
"""Trigger the single Airflow orchestration DAG after verifying raw S3 data exists."""

import os
import sys
import boto3
import subprocess
from pathlib import Path
from datetime import datetime

print("\n" + "="*80)
print("🚀 MANUAL DAG TRIGGER - Automotive Finance Orchestration")
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
dag_id = 'automotive_finance_orchestration'

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

# Step 2: Trigger the Airflow DAG
print("\n\nStep 2: Triggering the Airflow orchestration DAG...")
print("-" * 80)

run_id = f"manual_stream_trigger_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}"

try:
    result = subprocess.run(
        [
            'docker',
            'exec',
            'airflow-webserver',
            'airflow',
            'dags',
            'trigger',
            dag_id,
            '--run-id',
            run_id,
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)

    if result.returncode != 0:
        print(f"❌ Failed to trigger Airflow DAG {dag_id}")
        sys.exit(result.returncode)

    print(f"✅ Triggered {dag_id} with run id {run_id}")

except subprocess.TimeoutExpired:
    print('❌ Timed out while triggering the Airflow DAG')
    sys.exit(1)
except Exception as e:
    print(f"❌ Error triggering Airflow DAG: {e}")
    sys.exit(1)

print("\n\n" + "="*80)
print("📊 SUMMARY")
print("="*80)
print(f"""
Files are present in the RAW bucket and the single Airflow DAG has been triggered.

Triggered DAG: {dag_id}
Run ID: {run_id}

The orchestration flow will now:
  1. Monitor the S3 raw bucket
  2. Run Phase 3 shell ingestion from RAW to STAGING
  3. Let Phase 3 send ingestion notifications
  4. Run Phase 4 ETL from STAGING
  5. Archive processed STAGING files
  6. Send the Phase 5 Airflow notification
""")
print("="*80 + "\n")
