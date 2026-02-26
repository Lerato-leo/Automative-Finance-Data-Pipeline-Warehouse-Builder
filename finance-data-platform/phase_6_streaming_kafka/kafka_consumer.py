#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 6: Kafka Consumer - Batches events and writes to S3
Listens to Kafka topics and periodically flushes batches to S3 raw folders
Acts as a bridge: Kafka → S3 (simulating ERP/CRM connectors)

FOLDER STRUCTURE ORGANIZATION:
  Events are written to domain-organized folders in raw bucket:
  
  sales_topic         → s3://automotive-raw-data-lerato-2026/erp/sales/sales_*.csv
  inventory_topic     → s3://automotive-raw-data-lerato-2026/erp/inventory/inventory_*.csv
  interactions_topic  → s3://automotive-raw-data-lerato-2026/crm/interactions/interactions_*.csv
  payments_topic      → s3://automotive-raw-data-lerato-2026/finance/payments/payments_*.csv
  procurement_topic   → s3://automotive-raw-data-lerato-2026/suppliers_chain/procurement/procurement_*.csv
  telemetry_topic     → s3://automotive-raw-data-lerato-2026/iot/telemetry/telemetry_*.csv
  
  This folder structure is preserved throughout the pipeline:
  raw/ → staging/ → archive/ (maintaining erp/, crm/, finance/, etc.)
"""

import json
import boto3
import csv
from io import StringIO
from datetime import datetime
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import threading
import time
import argparse
from typing import Dict, List, Any
from collections import defaultdict

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = ['localhost:9092']
KAFKA_GROUP_ID = 'automotive-consumer-group'
KAFKA_TOPICS = ['sales_topic', 'payments_topic', 'interactions_topic', 'inventory_topic', 'procurement_topic', 'telemetry_topic']

# S3 Configuration
AWS_ACCESS_KEY_ID = None  # Will use environment variable
AWS_SECRET_ACCESS_KEY = None  # Will use environment variable
AWS_DEFAULT_REGION = None  # Will use environment variable
RAW_BUCKET = 'automotive-raw-data-lerato-2026'

# Batch Configuration
BATCH_SIZE = 100  # Number of messages before flushing
BATCH_TIMEOUT = 300  # Seconds (5 minutes)

class KafkaToS3Consumer:
    def __init__(self, batch_size: int = BATCH_SIZE, batch_timeout: int = BATCH_TIMEOUT):
        """Initialize Kafka consumer and S3 client"""
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.message_batches = defaultdict(list)
        self.last_flush = defaultdict(lambda: datetime.now())
        self.is_running = True
        
        # Initialize S3 client
        try:
            import os
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
            )
            print(f"✅ Connected to S3: {RAW_BUCKET}")
        except Exception as e:
            print(f"❌ Failed to initialize S3: {str(e)}")
            raise

        # Initialize Kafka consumer
        try:
            self.consumer = KafkaConsumer(
                *KAFKA_TOPICS,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=KAFKA_GROUP_ID,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                max_poll_records=100,
                session_timeout_ms=30000,
            )
            print(f"✅ Connected to Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
        except Exception as e:
            print(f"❌ Failed to connect to Kafka: {str(e)}")
            raise

        # Start background flush thread
        self.flush_thread = threading.Thread(target=self._flush_periodically, daemon=True)
        self.flush_thread.start()

    def _get_s3_key_and_folder(self, event_type: str) -> tuple:
        """Determine S3 folder and filename based on event type
        
        Maps event types to original domain structure:
        - erp/* → sales, inventory, customers, dealers, vehicles
        - crm/* → interactions
        - finance/* → payments
        - suppliers_chain/* → procurement, suppliers
        - iot/* → telemetry
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        mapping = {
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
        
        folder, filename = mapping.get(event_type, ('raw', f'{event_type}_{timestamp}.csv'))
        return folder, filename

    def _write_batch_to_s3(self, event_type: str, messages: List[Dict[str, Any]]) -> bool:
        """Write batch of messages to S3 as CSV"""
        if not messages:
            return False

        try:
            folder, filename = self._get_s3_key_and_folder(event_type)
            s3_key = f"{folder}/{filename}"
            
            # Convert messages to CSV
            csv_buffer = StringIO()
            if messages:
                fieldnames = messages[0].keys()
                writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
                writer.writeheader()
                for msg in messages:
                    writer.writerow(msg)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=RAW_BUCKET,
                Key=s3_key,
                Body=csv_buffer.getvalue(),
                ContentType='text/csv'
            )
            
            print(f"✓ Flushed {len(messages)} {event_type} events → s3://{RAW_BUCKET}/{s3_key}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to flush {event_type} batch to S3: {str(e)}")
            return False

    def flush_batches(self, force_all: bool = False):
        """Flush message batches to S3"""
        current_time = datetime.now()
        
        for event_type, messages in list(self.message_batches.items()):
            should_flush = (
                len(messages) >= self.batch_size or
                (force_all and len(messages) > 0) or
                (current_time - self.last_flush[event_type]).total_seconds() >= self.batch_timeout
            )
            
            if should_flush:
                if self._write_batch_to_s3(event_type, messages):
                    self.message_batches[event_type] = []
                    self.last_flush[event_type] = current_time

    def _flush_periodically(self):
        """Background thread to periodically flush batches"""
        while self.is_running:
            time.sleep(10)  # Check every 10 seconds
            self.flush_batches()

    def run(self):
        """Main consumption loop"""
        print(f"\n{'='*70}")
        print(f"KAFKA TO S3 CONSUMER - Event Batching Bridge")
        print(f"{'='*70}")
        print(f"📚 Topics: {', '.join(KAFKA_TOPICS)}")
        print(f"📦 Batch size: {self.batch_size} messages")
        print(f"⏱️  Batch timeout: {self.batch_timeout}s")
        print(f"☁️  S3 Bucket: {RAW_BUCKET}")
        print(f"{'='*70}\n")

        try:
            message_count = 0
            for message in self.consumer:
                try:
                    event_data = message.value
                    event_type = event_data.get('event_type', 'unknown')
                    
                    # Add to batch
                    self.message_batches[event_type].append(event_data)
                    message_count += 1
                    
                    if message_count % 10 == 0:
                        batch_stats = {k: len(v) for k, v in self.message_batches.items()}
                        print(f"📊 Received {message_count} messages. Batches: {batch_stats}")
                    
                    # Check if batch is full
                    if len(self.message_batches[event_type]) >= self.batch_size:
                        self.flush_batches()
                        
                except Exception as e:
                    print(f"✗ Error processing message: {str(e)}")

        except KeyboardInterrupt:
            print(f"\n⏹️  Consumer stopping...")
        finally:
            # Flush remaining messages
            print(f"\n💾 Flushing remaining batches...")
            self.flush_batches(force_all=True)
            self.is_running = False
            self.consumer.close()
            print(f"✅ Consumer closed. Processed {message_count} total messages.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Kafka Consumer - Batches events to S3')
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE,
                       help=f'Messages per batch (default: {BATCH_SIZE})')
    parser.add_argument('--timeout', type=int, default=BATCH_TIMEOUT,
                       help=f'Seconds before flush (default: {BATCH_TIMEOUT})')

    args = parser.parse_args()
    
    consumer = KafkaToS3Consumer(batch_size=args.batch_size, batch_timeout=args.timeout)
    consumer.run()
