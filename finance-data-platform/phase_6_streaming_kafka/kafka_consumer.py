#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 6: Kafka Consumer - Batches events and writes to S3
Listens to Kafka topics and periodically flushes batches to S3 raw folders
Acts as a bridge: Kafka → S3 (simulating ERP/CRM connectors)
"""

import argparse
import json
import os
import threading
import time
from collections import defaultdict
from datetime import datetime
from io import BytesIO, StringIO
from typing import Any, Dict, List

import boto3
import pandas as pd
from kafka.admin import KafkaAdminClient, NewTopic
from kafka import KafkaConsumer


KAFKA_BOOTSTRAP_SERVERS = [
    server.strip()
    for server in os.getenv('KAFKA_BOOTSTRAP_SERVERS', os.getenv('KAFKA_BROKER', 'localhost:9092')).split(',')
    if server.strip()
]
KAFKA_GROUP_ID = os.getenv('KAFKA_GROUP_ID', 'automotive-consumer-group')
RAW_BUCKET = os.getenv('RAW_BUCKET', 'automotive-raw-data-lerato-2026')

DATASET_CONFIG = {
    'customers': {'topic': 'customers_topic', 'folder': 'erp/customers', 'base_name': 'customers', 'extension': 'xlsx', 'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'},
    'sales': {'topic': 'sales_topic', 'folder': 'erp/sales', 'base_name': 'sales', 'extension': 'csv', 'content_type': 'text/csv'},
    'vehicles': {'topic': 'vehicles_topic', 'folder': 'erp/vehicles', 'base_name': 'vehicles', 'extension': 'csv', 'content_type': 'text/csv'},
    'dealers': {'topic': 'dealers_topic', 'folder': 'erp/dealers', 'base_name': 'dealers', 'extension': 'xlsx', 'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'},
    'inventory': {'topic': 'inventory_topic', 'folder': 'erp/inventory', 'base_name': 'inventory', 'extension': 'csv', 'content_type': 'text/csv'},
    'interactions': {'topic': 'interactions_topic', 'folder': 'crm/interactions', 'base_name': 'interactions', 'extension': 'json', 'content_type': 'application/json'},
    'payments': {'topic': 'payments_topic', 'folder': 'finance/payments', 'base_name': 'payments', 'extension': 'csv', 'content_type': 'text/csv'},
    'suppliers': {'topic': 'suppliers_topic', 'folder': 'suppliers_chain/suppliers', 'base_name': 'suppliers', 'extension': 'csv', 'content_type': 'text/csv'},
    'procurement': {'topic': 'procurement_topic', 'folder': 'suppliers_chain/procurement', 'base_name': 'procurement', 'extension': 'csv', 'content_type': 'text/csv'},
    'telemetry': {'topic': 'telemetry_topic', 'folder': 'iot/telemetry', 'base_name': 'telemetry', 'extension': 'json', 'content_type': 'application/json'},
}
KAFKA_TOPICS = [config['topic'] for config in DATASET_CONFIG.values()]

BATCH_SIZE = 100
BATCH_TIMEOUT = 300


class KafkaToS3Consumer:
    def __init__(self, batch_size: int = BATCH_SIZE, batch_timeout: int = BATCH_TIMEOUT):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.message_batches = defaultdict(list)
        self.last_flush = defaultdict(lambda: datetime.now())
        self.is_running = True

        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
            )
            print(f"✅ Connected to S3: {RAW_BUCKET}")
        except Exception as exc:
            print(f"❌ Failed to initialize S3: {exc}")
            raise

        try:
            self._ensure_topics_exist()
            self.consumer = KafkaConsumer(
                *KAFKA_TOPICS,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=KAFKA_GROUP_ID,
                value_deserializer=lambda message: json.loads(message.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                max_poll_records=100,
                session_timeout_ms=30000,
            )
            print(f"✅ Connected to Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
        except Exception as exc:
            print(f"❌ Failed to connect to Kafka: {exc}")
            raise

        self.flush_thread = threading.Thread(target=self._flush_periodically, daemon=True)
        self.flush_thread.start()

    def _ensure_topics_exist(self) -> None:
        admin_client = KafkaAdminClient(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            client_id='phase6-topic-bootstrap',
        )

        try:
            existing_topics = set(admin_client.list_topics())
            new_topics = [
                NewTopic(name=topic_name, num_partitions=1, replication_factor=1)
                for topic_name in KAFKA_TOPICS
                if topic_name not in existing_topics
            ]

            if new_topics:
                admin_client.create_topics(new_topics=new_topics, validate_only=False)
                created = ', '.join(topic.name for topic in new_topics)
                print(f"✅ Pre-created Kafka topics: {created}")
            else:
                print("✅ Kafka topics already exist")
        finally:
            admin_client.close()

    def _get_s3_key(self, event_type: str) -> str:
        config = DATASET_CONFIG[event_type]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        year = datetime.now().year
        filename = f"{config['base_name']}_{year}_{timestamp}.{config['extension']}"
        return f"{config['folder']}/{filename}"

    def _serialize_messages(self, event_type: str, messages: List[Dict[str, Any]]) -> bytes:
        extension = DATASET_CONFIG[event_type]['extension']

        if extension == 'csv':
            frame = pd.DataFrame(messages)
            csv_buffer = StringIO()
            frame.to_csv(csv_buffer, index=False)
            return csv_buffer.getvalue().encode('utf-8')

        if extension == 'json':
            return json.dumps(messages, indent=2).encode('utf-8')

        if extension == 'xlsx':
            frame = pd.DataFrame(messages)
            binary_buffer = BytesIO()
            frame.to_excel(binary_buffer, index=False)
            return binary_buffer.getvalue()

        raise ValueError(f"Unsupported output format for {event_type}: {extension}")

    def _write_batch_to_s3(self, event_type: str, messages: List[Dict[str, Any]]) -> bool:
        if not messages:
            return False

        try:
            s3_key = self._get_s3_key(event_type)
            payload = self._serialize_messages(event_type, messages)
            self.s3_client.put_object(
                Bucket=RAW_BUCKET,
                Key=s3_key,
                Body=payload,
                ContentType=DATASET_CONFIG[event_type]['content_type'],
            )
            print(f"✓ Flushed {len(messages)} {event_type} events → s3://{RAW_BUCKET}/{s3_key}")
            return True
        except Exception as exc:
            print(f"✗ Failed to flush {event_type} batch to S3: {exc}")
            return False

    def flush_batches(self, force_all: bool = False) -> None:
        current_time = datetime.now()

        for event_type, messages in list(self.message_batches.items()):
            should_flush = (
                len(messages) >= self.batch_size
                or (force_all and len(messages) > 0)
                or (current_time - self.last_flush[event_type]).total_seconds() >= self.batch_timeout
            )

            if should_flush and self._write_batch_to_s3(event_type, messages):
                self.message_batches[event_type] = []
                self.last_flush[event_type] = current_time

    def _flush_periodically(self) -> None:
        while self.is_running:
            time.sleep(10)
            self.flush_batches()

    def run(self) -> None:
        print(f"\n{'=' * 70}")
        print('KAFKA TO S3 CONSUMER - Event Batching Bridge')
        print(f"{'=' * 70}")
        print(f"📚 Topics: {', '.join(KAFKA_TOPICS)}")
        print(f"📦 Batch size: {self.batch_size} messages")
        print(f"⏱️  Batch timeout: {self.batch_timeout}s")
        print(f"☁️  S3 Bucket: {RAW_BUCKET}")
        print(f"{'=' * 70}\n")

        message_count = 0
        try:
            for message in self.consumer:
                event_data = message.value
                event_type = event_data.get('event_type', 'unknown')
                if event_type not in DATASET_CONFIG:
                    print(f"✗ Skipping unsupported event type: {event_type}")
                    continue

                self.message_batches[event_type].append(event_data)
                message_count += 1

                if message_count % 10 == 0:
                    batch_stats = {key: len(value) for key, value in self.message_batches.items()}
                    print(f"📊 Received {message_count} messages. Batches: {batch_stats}")

                if len(self.message_batches[event_type]) >= self.batch_size:
                    self.flush_batches()

        except KeyboardInterrupt:
            print('\n⏹️  Consumer stopping...')
        finally:
            print('\n💾 Flushing remaining batches...')
            self.flush_batches(force_all=True)
            self.is_running = False
            self.consumer.close()
            print(f"✅ Consumer closed. Processed {message_count} total messages.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Kafka Consumer - Batches events to S3')
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE, help=f'Messages per batch (default: {BATCH_SIZE})')
    parser.add_argument('--timeout', type=int, default=BATCH_TIMEOUT, help=f'Seconds before flush (default: {BATCH_TIMEOUT})')

    args = parser.parse_args()

    consumer = KafkaToS3Consumer(batch_size=args.batch_size, batch_timeout=args.timeout)
    consumer.run()
