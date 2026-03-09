#!/usr/bin/env python3
"""
Phase 3: Shell Scripting for Data Ingestion
Monitor raw S3 bucket, validate files, move to staging with notifications
"""

import os
import sys
import logging
import json
import smtplib
from datetime import datetime, timezone
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import boto3
from botocore.exceptions import ClientError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# AWS Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
RAW_BUCKET = os.getenv('S3_RAW_BUCKET', 'automotive-raw-data-lerato-2026')
STAGING_BUCKET = os.getenv('S3_STAGING_BUCKET', 'automotive-staging-data-lerato-2026')
ARCHIVE_BUCKET = os.getenv('S3_ARCHIVE_BUCKET', 'automotive-archive-data-lerato-2026')

# SMTP Configuration
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
SMTP_FROM = os.getenv('SMTP_MAIL_FROM', 'notifications@automativedata.com')
SMTP_TO = os.getenv('SMTP_TO', 'lerato.matamela01@gmail.com')

# Teams Configuration
TEAMS_WEBHOOK = os.getenv('TEAMS_WEBHOOK_URL')

# S3 Client
s3_client = boto3.client('s3', region_name=AWS_REGION)


def validate_file(bucket, key):
    """
    Validate file format and size
    Returns: (is_valid, error_message)
    """
    try:
        response = s3_client.head_object(Bucket=bucket, Key=key)
        size = response['ContentLength']
        
        # Check file size (max 500MB)
        if size > 500 * 1024 * 1024:
            return False, f"File too large: {size / 1024 / 1024:.2f}MB (max 500MB)"
        
        # Check file extension
        valid_extensions = {'.csv', '.json', '.xlsx', '.parquet', '.avro'}
        file_ext = Path(key).suffix.lower()
        if file_ext not in valid_extensions:
            return False, f"Invalid file format: {file_ext}"
        
        logger.info(f"✓ File validated: {key} ({size / 1024 / 1024:.2f}MB)")
        return True, None
    
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            return False, "File not found"
        return False, str(e)


def move_file(source_bucket, source_key, dest_bucket, dest_key):
    """
    Move file from source to destination bucket
    Returns: success boolean
    """
    try:
        # Copy file
        copy_source = {'Bucket': source_bucket, 'Key': source_key}
        s3_client.copy_object(CopySource=copy_source, Bucket=dest_bucket, Key=dest_key)
        logger.info(f"✓ File copied: {source_key} → {dest_bucket}/{dest_key}")
        
        # Delete original
        s3_client.delete_object(Bucket=source_bucket, Key=source_key)
        logger.info(f"✓ Original deleted: {source_bucket}/{source_key}")
        
        return True
    except ClientError as e:
        logger.error(f"✗ Move failed: {e}")
        return False


def send_email_notification(filename, status, details):
    """
    Send HTML email notification
    status: 'success' or 'failure'
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("⚠️  SMTP not configured - skipping email")
        return False
    
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        color = "#28a745" if status == "success" else "#dc3545"
        icon = "✅" if status == "success" else "❌"
        status_text = "Success" if status == "success" else "Failure"
        
        html_body = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; }}
                    .container {{ max-width: 700px; margin: 20px auto; background-color: white; padding: 0; 
                                  border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, {color}, {color}); color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 30px; }}
                    .details {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0; 
                               border-left: 4px solid {color}; }}
                    .footer {{ text-align: center; color: #999; font-size: 11px; padding: 20px; 
                              background-color: #f9f9f9; border-top: 1px solid #eee; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div style="font-size: 40px; margin-bottom: 10px;">{icon}</div>
                        <h2>Phase 3: Data Ingestion [{status_text}]</h2>
                    </div>
                    <div class="content">
                        <div class="details">
                            <strong>File:</strong> {filename}<br>
                            <strong>Status:</strong> {status_text} {icon}<br>
                            <strong>Timestamp:</strong> {timestamp}<br>
                            <strong>Details:</strong> {details}
                        </div>
                        <p style="color: #333; font-size: 14px;">
                            This is an automated notification from <strong>Phase 3: Shell Ingestion</strong>.<br>
                            Files are validated, moved from RAW → STAGING buckets.
                        </p>
                    </div>
                    <div class="footer">
                        <p>Automotive Finance Data Pipeline - Phase 3 Ingestion</p>
                        <p>Generated: {timestamp}</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Phase 3: {filename} [{status_text}] - {timestamp}"
        msg['From'] = SMTP_FROM
        msg['To'] = SMTP_TO
        msg.attach(MIMEText(html_body, 'html'))
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"📧 Email sent: {filename} [{status_text}]")
        return True
    
    except Exception as e:
        logger.error(f"❌ Email failed: {e}")
        return False


def send_teams_notification(filename, status, details):
    """
    Send Teams webhook notification
    """
    if not TEAMS_WEBHOOK:
        logger.warning("⚠️  Teams webhook not configured - skipping Teams notification")
        return False
    
    try:
        color = "28a745" if status == "success" else "dc3545"
        status_text = "Success" if status == "success" else "Failure"
        
        payload = {
            'themeColor': color,
            'summary': f'Phase 3: {filename} [{status_text}]',
            'sections': [
                {
                    'activityTitle': f'File Ingestion {status_text}',
                    'facts': [
                        {'name': 'File', 'value': filename},
                        {'name': 'Status', 'value': status_text},
                        {'name': 'Timestamp', 'value': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
                        {'name': 'Details', 'value': details},
                    ],
                    'text': 'Phase 3: File moved from RAW to STAGING bucket'
                }
            ]
        }
        
        response = requests.post(
            TEAMS_WEBHOOK,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"💬 Teams message posted: {filename}")
            return True
        else:
            logger.error(f"❌ Teams webhook failed: {response.status_code}")
            return False
    
    except Exception as e:
        logger.error(f"❌ Teams notification failed: {e}")
        return False


def process_bucket():
    """
    Main ingestion loop: scan RAW bucket, validate, move to STAGING
    """
    logger.info("\n" + "="*70)
    logger.info("🔄 PHASE 3: Data Ingestion - File Movement with Notifications")
    logger.info("="*70)
    logger.info(f"RAW bucket: {RAW_BUCKET}")
    logger.info(f"STAGING bucket: {STAGING_BUCKET}\n")
    
    processed_count = 0
    failed_count = 0
    
    try:
        # List objects in raw bucket
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=RAW_BUCKET)
        
        for page in pages:
            if 'Contents' not in page:
                logger.info("✓ No files to process in RAW bucket")
                break
            
            for obj in page['Contents']:
                key = obj['Key']
                
                # Skip directories
                if key.endswith('/'):
                    continue
                
                logger.info(f"\n📂 Processing: {key}")
                
                # Validate file
                is_valid, error_msg = validate_file(RAW_BUCKET, key)
                
                if not is_valid:
                    logger.warning(f"✗ Validation failed: {error_msg}")
                    send_email_notification(key, 'failure', f"Validation failed: {error_msg}")
                    send_teams_notification(key, 'failure', f"Validation failed: {error_msg}")
                    failed_count += 1
                    continue
                
                # Move file to staging
                staging_key = f"ingested/{key.split('/')[-1]}"
                if move_file(RAW_BUCKET, key, STAGING_BUCKET, staging_key):
                    logger.info(f"✓ File successfully moved: {staging_key}")
                    send_email_notification(key, 'success', f"Moved to {STAGING_BUCKET}/{staging_key}")
                    send_teams_notification(key, 'success', f"Moved to STAGING bucket")
                    processed_count += 1
                else:
                    logger.error(f"✗ Move failed: {key}")
                    send_email_notification(key, 'failure', "Move operation failed")
                    send_teams_notification(key, 'failure', "Move operation failed")
                    failed_count += 1
        
        # Summary notification
        logger.info("\n" + "="*70)
        logger.info(f"✓ Phase 3 Complete: {processed_count} files processed, {failed_count} failed")
        logger.info("="*70 + "\n")
        
        return processed_count, failed_count
    
    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}")
        return 0, 1


if __name__ == '__main__':
    try:
        processed, failed = process_bucket()
        sys.exit(0 if failed == 0 else 1)
    except KeyboardInterrupt:
        logger.info("\n🛑 Ingestion stopped by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
