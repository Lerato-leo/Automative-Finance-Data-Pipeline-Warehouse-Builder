#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 6: Kafka Producer - Simulates ERP/CRM/IoT Systems
Generates real-time events for all automotive data types
Publishes to Kafka topics for streaming ingestion
"""

import sys
import io
import json

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
import random
import uuid
from datetime import datetime, timedelta
from kafka import KafkaProducer
import time
import argparse
from typing import Dict, Any

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = ['localhost:9092']
KAFKA_TOPICS = {
    'sales': 'sales_topic',
    'payments': 'payments_topic',
    'interactions': 'interactions_topic',
    'inventory': 'inventory_topic',
    'procurement': 'procurement_topic',
    'telemetry': 'telemetry_topic',
}

# Master data
CUSTOMER_IDS = [f'CUST-{i:03d}' for i in range(1, 51)]
CUSTOMER_NAMES = ['John Smith', 'Sarah Johnson', 'Michael Brown', 'Emily Davis', 'James Wilson']
DEALERS = [
    {'id': 'DEALER-01', 'name': 'Main Street Motors', 'city': 'Toronto'},
    {'id': 'DEALER-02', 'name': 'Downtown Auto Sales', 'city': 'Vancouver'},
    {'id': 'DEALER-03', 'name': 'Suburban Vehicles', 'city': 'Calgary'},
]
VEHICLES = [
    {'vin': f'VIN{i:05d}', 'make': make, 'model': model, 'year': 2022 + (i % 2)}
    for i, (make, model) in enumerate([
        ('Toyota', 'Camry'), ('Honda', 'Civic'), ('Ford', 'Focus'),
        ('Chevrolet', 'Malibu'), ('BMW', '320i'), ('Mercedes', 'C-Class'),
        ('Audi', 'A4'), ('Tesla', 'Model 3'), ('Hyundai', 'Elantra'),
        ('Kia', 'Optima'),
    ])
]
SUPPLIERS = [
    {'id': 'SUP-001', 'name': 'Toyota Factory'},
    {'id': 'SUP-002', 'name': 'Honda Distributor'},
    {'id': 'SUP-003', 'name': 'Parts Supplier Co'},
]

class EventProducer:
    def __init__(self, event_type: str = 'all', interval: int = 5, count: int = None):
        """
        Initialize Kafka producer
        event_type: 'sales', 'payments', 'interactions', 'inventory', 'procurement', 'telemetry', or 'all'
        interval: seconds between events
        count: number of events to generate (None = infinite)
        """
        self.event_type = event_type
        self.interval = interval
        self.count = count
        self.event_counter = 0
        
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3
            )
            print(f"✅ Connected to Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
        except Exception as e:
            print(f"❌ Failed to connect to Kafka: {str(e)}")
            raise

    def generate_sales_event(self) -> Dict[str, Any]:
        """Generate simulated sales event"""
        base_date = datetime.now() - timedelta(days=random.randint(0, 30))
        return {
            'event_type': 'sales',
            'sale_id': f'SALE-{uuid.uuid4().hex[:8].upper()}',
            'sale_date': base_date.isoformat(),
            'customer_id': random.choice(CUSTOMER_IDS),
            'customer_name': random.choice(CUSTOMER_NAMES),
            'email': f'{random.choice(CUSTOMER_NAMES).lower().replace(" ", "")}@example.com',
            'vehicle_vin': random.choice(VEHICLES)['vin'],
            'dealer_id': random.choice(DEALERS)['id'],
            'dealer_name': random.choice(DEALERS)['name'],
            'sale_price': round(random.uniform(20000, 60000), 2),
            'discount_amount': round(random.uniform(0, 5000), 2),
            'final_price': round(random.uniform(18000, 55000), 2),
            'sale_channel': random.choice(['Dealership', 'Online', 'Auction']),
            'sale_status': random.choice(['Completed', 'Pending', 'Cancelled']),
            'timestamp': datetime.now().isoformat(),
        }

    def generate_payments_event(self) -> Dict[str, Any]:
        """Generate simulated payments event"""
        return {
            'event_type': 'payments',
            'payment_id': f'PAY-{uuid.uuid4().hex[:8].upper()}',
            'sale_id': f'SALE-{random.randint(1000, 9999)}',
            'payment_date': datetime.now().isoformat(),
            'payment_amount': round(random.uniform(15000, 50000), 2),
            'payment_method': random.choice(['Credit Card', 'Bank Transfer', 'Debit Card', 'Check']),
            'payment_status': random.choice(['Paid', 'Pending', 'Failed']),
            'transaction_reference': f'TXN-2026-{random.randint(100000, 999999)}',
            'timestamp': datetime.now().isoformat(),
        }

    def generate_interactions_event(self) -> Dict[str, Any]:
        """Generate simulated customer interaction event"""
        return {
            'event_type': 'interactions',
            'interaction_id': f'INT-{uuid.uuid4().hex[:8].upper()}',
            'customer_id': random.choice(CUSTOMER_IDS),
            'customer_name': random.choice(CUSTOMER_NAMES),
            'dealer_id': random.choice(DEALERS)['id'],
            'interaction_date': datetime.now().isoformat(),
            'interaction_type': random.choice(['Phone', 'Email', 'Chat', 'In-Person']),
            'interaction_channel': random.choice(['Sales', 'Support', 'Marketing']),
            'outcome': random.choice(['Won', 'Lost', 'Pending']),
            'duration_minutes': random.randint(5, 120),
            'notes': f'Customer interaction #{random.randint(1000, 9999)}',
            'timestamp': datetime.now().isoformat(),
        }

    def generate_inventory_event(self) -> Dict[str, Any]:
        """Generate simulated inventory event"""
        vehicle = random.choice(VEHICLES)
        dealer = random.choice(DEALERS)
        return {
            'event_type': 'inventory',
            'inventory_id': f'INV-{uuid.uuid4().hex[:8].upper()}',
            'vehicle_vin': vehicle['vin'],
            'vehicle_make': vehicle['make'],
            'vehicle_model': vehicle['model'],
            'dealer_id': dealer['id'],
            'dealer_name': dealer['name'],
            'quantity': random.randint(1, 10),
            'stock_status': random.choice(['In Stock', 'Out of Stock', 'Coming Soon']),
            'last_updated': datetime.now().isoformat(),
            'timestamp': datetime.now().isoformat(),
        }

    def generate_procurement_event(self) -> Dict[str, Any]:
        """Generate simulated procurement event"""
        vehicle = random.choice(VEHICLES)
        supplier = random.choice(SUPPLIERS)
        return {
            'event_type': 'procurement',
            'procurement_id': f'PROC-{uuid.uuid4().hex[:8].upper()}',
            'vehicle_vin': vehicle['vin'],
            'vehicle_make': vehicle['make'],
            'supplier_id': supplier['id'],
            'supplier_name': supplier['name'],
            'cost_price': round(random.uniform(12000, 40000), 2),
            'procurement_date': datetime.now().isoformat(),
            'procurement_status': random.choice(['Ordered', 'Received', 'Returned']),
            'quantity': random.randint(1, 5),
            'timestamp': datetime.now().isoformat(),
        }

    def generate_telemetry_event(self) -> Dict[str, Any]:
        """Generate simulated vehicle telemetry event"""
        return {
            'event_type': 'telemetry',
            'telemetry_id': f'TEL-{uuid.uuid4().hex[:8].upper()}',
            'vehicle_vin': random.choice(VEHICLES)['vin'],
            'speed': random.randint(0, 200),
            'fuel_level': random.randint(0, 100),
            'engine_temperature': random.randint(60, 100),
            'location_lat': round(random.uniform(43.6, 43.7), 4),
            'location_long': round(random.uniform(-79.5, -79.4), 4),
            'timestamp': datetime.now().isoformat(),
        }

    def produce_event(self, event_data: Dict[str, Any]):
        """Publish event to Kafka topic"""
        event_type = event_data['event_type']
        topic = KAFKA_TOPICS[event_type]
        
        try:
            self.producer.send(topic, value=event_data).get(timeout=10)
            self.event_counter += 1
            print(f"✓ Published {event_type}_#{self.event_counter}: {event_data.get('id', event_data.get(f'{event_type}_id'))}")
        except Exception as e:
            print(f"✗ Failed to publish to {topic}: {str(e)}")

    def run(self):
        """Main production loop"""
        print(f"\n{'='*70}")
        print(f"KAFKA EVENT PRODUCER - {self.event_type.upper()}")
        print(f"{'='*70}")
        print(f"📊 Interval: {self.interval}s between events")
        print(f"📊 Topics: {KAFKA_TOPICS}")
        print(f"{'='*70}\n")

        generators = {
            'sales': self.generate_sales_event,
            'payments': self.generate_payments_event,
            'interactions': self.generate_interactions_event,
            'inventory': self.generate_inventory_event,
            'procurement': self.generate_procurement_event,
            'telemetry': self.generate_telemetry_event,
        }

        event_types = list(generators.keys()) if self.event_type == 'all' else [self.event_type]

        try:
            iteration = 0
            while True:
                if self.count and self.event_counter >= self.count:
                    print(f"\n✅ Reached limit of {self.count} events. Stopping...")
                    break

                iteration += 1
                for event_type in event_types:
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
    parser.add_argument('--type', type=str, default='all',
                       choices=['sales', 'payments', 'interactions', 'inventory', 'procurement', 'telemetry', 'all'],
                       help='Type of events to produce')
    parser.add_argument('--interval', type=int, default=5,
                       help='Seconds between events')
    parser.add_argument('--count', type=int, default=None,
                       help='Total number of events to produce (default: infinite)')

    args = parser.parse_args()
    
    producer = EventProducer(event_type=args.type, interval=args.interval, count=args.count)
    producer.run()
