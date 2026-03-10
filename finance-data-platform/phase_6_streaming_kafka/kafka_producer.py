#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 6: Kafka Producer - Simulates ERP/CRM/IoT Systems
Generates real-time events for all automotive data types
Publishes to Kafka topics for streaming ingestion
"""

import argparse
import io
import json
import os
import random
import sys
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict

from kafka import KafkaProducer


if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


KAFKA_BOOTSTRAP_SERVERS = [
    server.strip()
    for server in os.getenv('KAFKA_BOOTSTRAP_SERVERS', os.getenv('KAFKA_BROKER', 'localhost:9092')).split(',')
    if server.strip()
]
KAFKA_TOPICS = {
    'customers': 'customers_topic',
    'sales': 'sales_topic',
    'vehicles': 'vehicles_topic',
    'dealers': 'dealers_topic',
    'inventory': 'inventory_topic',
    'interactions': 'interactions_topic',
    'payments': 'payments_topic',
    'suppliers': 'suppliers_topic',
    'procurement': 'procurement_topic',
    'telemetry': 'telemetry_topic',
}

CUSTOMER_IDS = [f'CUST-{i:03d}' for i in range(1, 51)]
FIRST_NAMES = ['John', 'Sarah', 'Michael', 'Emily', 'James', 'Lerato', 'Ava', 'Noah']
LAST_NAMES = ['Smith', 'Johnson', 'Brown', 'Davis', 'Wilson', 'Mokoena', 'Taylor', 'Martin']
PROVINCES = ['ON', 'BC', 'AB', 'QC', 'MB']
DEALERS = [
    {'dealer_id': 'DEALER-01', 'dealer_name': 'Main Street Motors', 'city': 'Toronto', 'province': 'ON'},
    {'dealer_id': 'DEALER-02', 'dealer_name': 'Downtown Auto Sales', 'city': 'Vancouver', 'province': 'BC'},
    {'dealer_id': 'DEALER-03', 'dealer_name': 'Suburban Vehicles', 'city': 'Calgary', 'province': 'AB'},
]
VEHICLES = [
    {
        'vehicle_id': f'VEH-{i:03d}',
        'vin': f'VIN{i:05d}',
        'make': make,
        'model': model,
        'year': 2022 + (i % 3),
        'engine_type': random.choice(['Gasoline', 'Hybrid', 'Electric']),
        'transmission': random.choice(['Automatic', 'Manual', 'CVT']),
        'vehicle_status': random.choice(['Available', 'Sold', 'Reserved']),
    }
    for i, (make, model) in enumerate([
        ('Toyota', 'Camry'), ('Honda', 'Civic'), ('Ford', 'Focus'),
        ('Chevrolet', 'Malibu'), ('BMW', '320i'), ('Mercedes', 'C-Class'),
        ('Audi', 'A4'), ('Tesla', 'Model 3'), ('Hyundai', 'Elantra'),
        ('Kia', 'Optima'),
    ], start=1)
]
SUPPLIERS = [
    {
        'supplier_id': 'SUP-001',
        'supplier_name': 'Toyota Factory',
        'contact_name': 'Amelia Stone',
        'contact_email': 'amelia.stone@toyotafactory.example',
        'contact_phone': '+1-555-210-1001',
        'city': 'Toronto',
        'province': 'ON',
        'zip_code': 'M5V1A1',
        'created_at': datetime.now().isoformat(),
    },
    {
        'supplier_id': 'SUP-002',
        'supplier_name': 'Honda Distributor',
        'contact_name': 'Liam Harper',
        'contact_email': 'liam.harper@hondadistributor.example',
        'contact_phone': '+1-555-210-1002',
        'city': 'Vancouver',
        'province': 'BC',
        'zip_code': 'V6B2W9',
        'created_at': datetime.now().isoformat(),
    },
    {
        'supplier_id': 'SUP-003',
        'supplier_name': 'Parts Supplier Co',
        'contact_name': 'Sophia Reed',
        'contact_email': 'sophia.reed@partssupplier.example',
        'contact_phone': '+1-555-210-1003',
        'city': 'Calgary',
        'province': 'AB',
        'zip_code': 'T2P3C7',
        'created_at': datetime.now().isoformat(),
    },
]


class EventProducer:
    def __init__(self, event_type: str = 'all', interval: int = 5, count: int | None = None):
        self.event_type = event_type
        self.interval = interval
        self.count = count
        self.event_counter = 0

        try:
            self.producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda value: json.dumps(value).encode('utf-8'),
                acks='all',
                retries=3,
            )
            print(f"✅ Connected to Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
        except Exception as exc:
            print(f"❌ Failed to connect to Kafka: {exc}")
            raise

    def _random_customer_identity(self) -> Dict[str, str]:
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        return {
            'customer_id': random.choice(CUSTOMER_IDS),
            'first_name': first_name,
            'last_name': last_name,
            'email': f"{first_name.lower()}.{last_name.lower()}@example.com",
        }

    def generate_customers_event(self) -> Dict[str, Any]:
        identity = self._random_customer_identity()
        return {
            'event_type': 'customers',
            'customer_id': identity['customer_id'],
            'first_name': identity['first_name'],
            'last_name': identity['last_name'],
            'email': identity['email'],
            'phone': f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            'date_of_birth': (datetime.now() - timedelta(days=random.randint(7000, 22000))).date().isoformat(),
            'gender': random.choice(['M', 'F', 'Other']),
            'city': random.choice(['Toronto', 'Vancouver', 'Calgary', 'Ottawa']),
            'province': random.choice(PROVINCES),
            'zip_code': f"{random.choice(['M5V', 'V6B', 'T2P', 'K1A'])}{random.randint(100, 999)}",
            'created_at': datetime.now().isoformat(),
        }

    def generate_sales_event(self) -> Dict[str, Any]:
        identity = self._random_customer_identity()
        vehicle = random.choice(VEHICLES)
        dealer = random.choice(DEALERS)
        sale_price = round(random.uniform(20000, 60000), 2)
        discount_amount = round(random.uniform(0, 5000), 2)
        return {
            'event_type': 'sales',
            'sale_id': f"SALE-{uuid.uuid4().hex[:8].upper()}",
            'sale_date': (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
            'customer_id': identity['customer_id'],
            'vehicle_id': vehicle['vehicle_id'],
            'dealer_id': dealer['dealer_id'],
            'sale_price': sale_price,
            'discount_amount': discount_amount,
            'final_price': round(sale_price - discount_amount, 2),
            'sale_channel': random.choice(['Dealership', 'Online', 'Auction']),
            'sale_status': random.choice(['Completed', 'Pending', 'Cancelled']),
            'timestamp': datetime.now().isoformat(),
        }

    def generate_vehicles_event(self) -> Dict[str, Any]:
        vehicle = random.choice(VEHICLES)
        return {
            'event_type': 'vehicles',
            'vehicle_id': vehicle['vehicle_id'],
            'vin': vehicle['vin'],
            'make': vehicle['make'],
            'model': vehicle['model'],
            'year': vehicle['year'],
            'engine_type': vehicle['engine_type'],
            'transmission': vehicle['transmission'],
            'vehicle_status': vehicle['vehicle_status'],
            'created_at': datetime.now().isoformat(),
        }

    def generate_dealers_event(self) -> Dict[str, Any]:
        dealer = random.choice(DEALERS)
        return {
            'event_type': 'dealers',
            'dealer_id': dealer['dealer_id'],
            'name': dealer['dealer_name'],
            'city': dealer['city'],
            'province': dealer['province'],
            'email': f"{dealer['dealer_name'].lower().replace(' ', '.')}@example.com",
            'phone': f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            'created_at': datetime.now().isoformat(),
        }

    def generate_inventory_event(self) -> Dict[str, Any]:
        vehicle = random.choice(VEHICLES)
        dealer = random.choice(DEALERS)
        return {
            'event_type': 'inventory',
            'inventory_id': f"INV-{uuid.uuid4().hex[:8].upper()}",
            'vehicle_id': vehicle['vehicle_id'],
            'dealer_id': dealer['dealer_id'],
            'quantity': random.randint(1, 10),
            'stock_status': random.choice(['In Stock', 'Out of Stock', 'Coming Soon']),
            'last_updated': datetime.now().isoformat(),
            'timestamp': datetime.now().isoformat(),
        }

    def generate_interactions_event(self) -> Dict[str, Any]:
        identity = self._random_customer_identity()
        dealer = random.choice(DEALERS)
        return {
            'event_type': 'interactions',
            'interaction_id': f"INT-{uuid.uuid4().hex[:8].upper()}",
            'customer_id': identity['customer_id'],
            'dealer_id': dealer['dealer_id'],
            'interaction_date': datetime.now().isoformat(),
            'interaction_type': random.choice(['Phone', 'Email', 'Chat', 'In-Person']),
            'interaction_channel': random.choice(['Sales', 'Support', 'Marketing']),
            'outcome': random.choice(['Won', 'Lost', 'Pending', 'Cancelled']),
            'duration_minutes': random.randint(5, 120),
            'notes': f"Customer interaction #{random.randint(1000, 9999)}",
            'timestamp': datetime.now().isoformat(),
        }

    def generate_payments_event(self) -> Dict[str, Any]:
        return {
            'event_type': 'payments',
            'payment_id': f"PAY-{uuid.uuid4().hex[:8].upper()}",
            'sale_id': f"SALE-{random.randint(1000, 9999)}",
            'payment_date': datetime.now().isoformat(),
            'amount': round(random.uniform(15000, 50000), 2),
            'payment_method': random.choice(['Credit Card', 'Bank Transfer', 'Debit Card', 'Check']),
            'status': random.choice(['Paid', 'Pending', 'Failed']),
            'transaction_reference': f"TXN-2026-{random.randint(100000, 999999)}",
            'timestamp': datetime.now().isoformat(),
        }

    def generate_suppliers_event(self) -> Dict[str, Any]:
        supplier = random.choice(SUPPLIERS)
        return {
            'event_type': 'suppliers',
            **supplier,
            'timestamp': datetime.now().isoformat(),
        }

    def generate_procurement_event(self) -> Dict[str, Any]:
        vehicle = random.choice(VEHICLES)
        supplier = random.choice(SUPPLIERS)
        return {
            'event_type': 'procurement',
            'procurement_id': f"PROC-{uuid.uuid4().hex[:8].upper()}",
            'supplier_id': supplier['supplier_id'],
            'vehicle_id': vehicle['vehicle_id'],
            'procurement_date': datetime.now().isoformat(),
            'cost': round(random.uniform(12000, 40000), 2),
            'status': random.choice(['Ordered', 'Received', 'Returned']),
            'quantity': random.randint(1, 5),
            'timestamp': datetime.now().isoformat(),
        }

    def generate_telemetry_event(self) -> Dict[str, Any]:
        vehicle = random.choice(VEHICLES)
        return {
            'event_type': 'telemetry',
            'telemetry_id': f"TEL-{uuid.uuid4().hex[:8].upper()}",
            'vehicle_id': vehicle['vehicle_id'],
            'sensor_type': random.choice(['speed', 'fuel_level', 'engine_temperature']),
            'sensor_value': round(random.uniform(10, 120), 2),
            'location_lat': round(random.uniform(43.6, 43.7), 4),
            'location_long': round(random.uniform(-79.5, -79.4), 4),
            'timestamp': datetime.now().isoformat(),
        }

    def produce_event(self, event_data: Dict[str, Any]) -> None:
        event_type = event_data['event_type']
        topic = KAFKA_TOPICS[event_type]
        identifier = next(
            (
                event_data.get(key)
                for key in ('customer_id', 'sale_id', 'vehicle_id', 'dealer_id', 'inventory_id', 'interaction_id', 'payment_id', 'supplier_id', 'procurement_id', 'telemetry_id')
                if event_data.get(key)
            ),
            'n/a',
        )

        try:
            self.producer.send(topic, value=event_data).get(timeout=10)
            self.event_counter += 1
            print(f"✓ Published {event_type}_#{self.event_counter}: {identifier}")
        except Exception as exc:
            print(f"✗ Failed to publish to {topic}: {exc}")

    def run(self) -> None:
        print(f"\n{'=' * 70}")
        print(f"KAFKA EVENT PRODUCER - {self.event_type.upper()}")
        print(f"{'=' * 70}")
        print(f"📊 Interval: {self.interval}s between events")
        print(f"📊 Topics: {KAFKA_TOPICS}")
        print(f"{'=' * 70}\n")

        generators = {
            'customers': self.generate_customers_event,
            'sales': self.generate_sales_event,
            'vehicles': self.generate_vehicles_event,
            'dealers': self.generate_dealers_event,
            'inventory': self.generate_inventory_event,
            'interactions': self.generate_interactions_event,
            'payments': self.generate_payments_event,
            'suppliers': self.generate_suppliers_event,
            'procurement': self.generate_procurement_event,
            'telemetry': self.generate_telemetry_event,
        }

        event_types = list(generators.keys()) if self.event_type == 'all' else [self.event_type]

        try:
            while True:
                if self.count and self.event_counter >= self.count:
                    print(f"\n✅ Reached limit of {self.count} events. Stopping...")
                    break

                for event_type in event_types:
                    if self.count and self.event_counter >= self.count:
                        break
                    event = generators[event_type]()
                    self.produce_event(event)

                time.sleep(self.interval)

        except KeyboardInterrupt:
            print(f"\n⏹️  Producer stopped. Published {self.event_counter} events.")
        finally:
            self.producer.flush()
            self.producer.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Kafka Event Producer for Automotive Platform')
    parser.add_argument(
        '--type',
        type=str,
        default='all',
        choices=['customers', 'sales', 'vehicles', 'dealers', 'inventory', 'interactions', 'payments', 'suppliers', 'procurement', 'telemetry', 'all'],
        help='Type of events to produce',
    )
    parser.add_argument('--interval', type=int, default=5, help='Seconds between events')
    parser.add_argument('--count', type=int, default=None, help='Total number of events to produce (default: infinite)')

    args = parser.parse_args()

    producer = EventProducer(event_type=args.type, interval=args.interval, count=args.count)
    producer.run()
