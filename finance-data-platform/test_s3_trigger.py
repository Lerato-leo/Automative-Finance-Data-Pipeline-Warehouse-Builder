#!/usr/bin/env python3
"""
Test Script: Generate sample data and upload to S3 RAW bucket
This triggers the Airflow S3 event sensor which will auto-run the ETL pipeline
"""

import os
import sys
import json
import csv
import boto3
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from faker import Faker
import random

# Configuration
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
RAW_BUCKET = os.getenv('RAW_BUCKET', 'automotive-raw-data-lerato-2026')
DATA_SAMPLES = 100  # Number of records to generate

fake = Faker()

def generate_erp_data():
    """Generate sample ERP/Finance data"""
    print("📊 Generating ERP Finance data...")
    data = []
    for i in range(DATA_SAMPLES):
        data.append({
            'transaction_id': f'TXN_{datetime.now().strftime("%Y%m%d%H%M%S")}_{i:04d}',
            'account_code': fake.bothify('###-###-####'),
            'amount': round(random.uniform(100, 50000), 2),
            'currency': 'USD',
            'transaction_date': fake.date_time_this_year().isoformat(),
            'description': fake.sentence(nb_words=5),
            'department': fake.word(),
            'status': 'COMPLETED'
        })
    return pd.DataFrame(data)

def generate_crm_data():
    """Generate sample CRM/Customer data"""
    print("👥 Generating CRM Customer data...")
    data = []
    for i in range(DATA_SAMPLES):
        data.append({
            'customer_id': f'CUST_{i:06d}',
            'name': fake.name(),
            'email': fake.email(),
            'phone': fake.phone_number(),
            'company': fake.company(),
            'address': fake.address().replace('\n', ', '),
            'created_date': fake.date_time_this_year().isoformat(),
            'lifetime_value': round(random.uniform(1000, 100000), 2),
            'status': random.choice(['ACTIVE', 'INACTIVE', 'PROSPECTIVE'])
        })
    return pd.DataFrame(data)

def generate_iot_data():
    """Generate sample IoT sensor data"""
    print("🔧 Generating IoT Sensor data...")
    data = []
    now = datetime.now()
    for i in range(DATA_SAMPLES):
        # Generate data from last 24 hours
        random_hours = random.randint(0, 23)
        ts = now - timedelta(hours=random_hours)
        data.append({
            'device_id': f'IOT_{fake.bothify("DEV-##-##")}',
            'sensor_type': random.choice(['temperature', 'pressure', 'vibration', 'humidity']),
            'sensor_value': round(random.uniform(0, 100), 2),
            'unit': random.choice(['°C', 'psi', 'mm/s', '%']),
            'timestamp': ts.isoformat(),
            'location': f'{fake.city()}, {fake.country_code()}',
            'status': random.choice(['NORMAL', 'WARNING', 'ALERT'])
        })
    return pd.DataFrame(data)

def generate_suppliers_data():
    """Generate sample Supplier/Vendor data"""
    print("🏭 Generating Supplier data...")
    data = []
    for i in range(DATA_SAMPLES):
        data.append({
            'supplier_id': f'SUP_{i:06d}',
            'supplier_name': fake.company(),
            'contact_person': fake.name(),
            'email': fake.email(),
            'phone': fake.phone_number(),
            'country': fake.country(),
            'rating': round(random.uniform(1, 5), 2),
            'payment_terms': random.choice(['NET30', 'NET60', 'COD']),
            'active': random.choice([True, False])
        })
    return pd.DataFrame(data)

def upload_to_s3(dataframe, filename, s3_client):
    """Upload CSV file to S3 RAW bucket"""
    try:
        # Convert to CSV
        csv_content = dataframe.to_csv(index=False)
        
        # Upload to S3
        s3_client.put_object(
            Bucket=RAW_BUCKET,
            Key=filename,
            Body=csv_content.encode('utf-8'),
            ContentType='text/csv'
        )
        print(f"✅ Uploaded: s3://{RAW_BUCKET}/{filename}")
        return True
    except Exception as e:
        print(f"❌ Error uploading {filename}: {str(e)}")
        return False

def main():
    """Main execution"""
    print("\n" + "="*70)
    print("🚀 S3 TEST DATA UPLOAD - Triggering Airflow ETL Pipeline")
    print("="*70)
    
    # Initialize S3 client
    try:
        s3_client = boto3.client('s3', region_name=AWS_REGION)
        # Test connection
        s3_client.head_bucket(Bucket=RAW_BUCKET)
        print(f"\n✓ Connected to S3 bucket: {RAW_BUCKET}")
    except Exception as e:
        print(f"\n❌ Error connecting to S3: {str(e)}")
        print("Ensure AWS credentials are configured: aws configure")
        sys.exit(1)
    
    # Generate and upload data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    files_uploaded = 0
    
    try:
        # ERP Data
        erp_df = generate_erp_data()
        if upload_to_s3(erp_df, f"erp_finance_{timestamp}.csv", s3_client):
            files_uploaded += 1
        
        # CRM Data
        crm_df = generate_crm_data()
        if upload_to_s3(crm_df, f"crm_customers_{timestamp}.csv", s3_client):
            files_uploaded += 1
        
        # IoT Data
        iot_df = generate_iot_data()
        if upload_to_s3(iot_df, f"iot_sensors_{timestamp}.csv", s3_client):
            files_uploaded += 1
        
        # Supplier Data
        sup_df = generate_suppliers_data()
        if upload_to_s3(sup_df, f"suppliers_{timestamp}.csv", s3_client):
            files_uploaded += 1
        
        print("\n" + "="*70)
        print(f"📤 UPLOAD COMPLETE: {files_uploaded} files uploaded")
        print("="*70)
        print("\n🔔 S3 Event Notification triggered!")
        print("⏳ Airflow sensor DAG should auto-trigger in ~5-10 seconds...")
        print("\n📊 Monitor progress at: http://localhost:8081")
        print("   DAG: s3_raw_bucket_sensor_trigger -> event_driven_real_time_etl")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error during data generation: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
