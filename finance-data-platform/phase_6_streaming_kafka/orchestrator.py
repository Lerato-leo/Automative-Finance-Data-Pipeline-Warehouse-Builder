#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 6: Streaming Orchestration Manager
Manages Kafka infrastructure, producers, and consumers for the automotive platform
Simulates ERP/CRM → Kafka → S3 → Airflow data flow
"""

import subprocess
import time
import sys
import signal
import os
import io
from pathlib import Path
from typing import Optional
import argparse

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class StreamingOrchestrator:
    def __init__(self):
        self.phase_dir = Path(__file__).parent
        self.docker_compose_file = self.phase_dir / "docker-compose.yml"
        self.producer_script = self.phase_dir / "kafka_producer.py"
        self.consumer_script = self.phase_dir / "kafka_consumer.py"
        self.processes = []

    def run_command(self, command: list, name: str = None, background: bool = False):
        """Run a shell command with status output"""
        print(f"\n▶️  {name or ' '.join(command)}")
        print("-" * 70)
        
        try:
            if background:
                process = subprocess.Popen(command)
                self.processes.append(process)
                print(f"✅ Started (PID: {process.pid})")
                return process
            else:
                result = subprocess.run(command, capture_output=False, text=True)
                if result.returncode == 0:
                    print(f"✅ Success")
                else:
                    print(f"❌ Failed with code {result.returncode}")
                return result
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None

    def start_kafka(self):
        """Start Kafka infrastructure (Zookeeper + Broker + UI)"""
        print("\n" + "="*70)
        print("STARTING KAFKA INFRASTRUCTURE")
        print("="*70)
        
        self.run_command(
            ["docker-compose", "-f", str(self.docker_compose_file), "up", "-d"],
            name="Docker Compose - Kafka + Zookeeper + UI"
        )
        
        print("\n⏳ Waiting for Kafka to be ready...")
        time.sleep(10)
        
        # Verify Kafka is running
        self.run_command(
            ["docker-compose", "-f", str(self.docker_compose_file), "ps"],
            name="Kafka Status Check"
        )
        
        print("\n✅ Kafka Infrastructure Started!")
        print("   - Kafka Broker: localhost:9092")
        print("   - Zookeeper: localhost:2181")
        print("   - Kafka UI: http://localhost:8888")

    def stop_kafka(self):
        """Stop Kafka infrastructure"""
        print("\n" + "="*70)
        print("STOPPING KAFKA INFRASTRUCTURE")
        print("="*70)
        
        self.run_command(
            ["docker-compose", "-f", str(self.docker_compose_file), "down"],
            name="Docker Compose - Shutdown"
        )
        
        print("\n✅ Kafka Infrastructure Stopped!")

    def start_producers(self, event_type: str = "all", interval: int = 5, count: int = None):
        """Start Kafka producer(s)"""
        print("\n" + "="*70)
        print(f"STARTING PRODUCERS - {event_type.upper()}")
        print("="*70)
        
        check_kafka = self.run_command(
            ["docker", "ps", "--filter", "name=automotive-kafka"],
            name="Checking Kafka availability"
        )
        
        command = [sys.executable, str(self.producer_script), "--type", event_type, "--interval", str(interval)]
        if count:
            command.extend(["--count", str(count)])
        
        self.run_command(command, name=f"Kafka Producer - {event_type}", background=True)
        
        print("\n✅ Producer(s) Started!")
        print(f"   - Event Type: {event_type}")
        print(f"   - Interval: {interval}s")
        if count:
            print(f"   - Total Events: {count}")

    def start_consumer(self, batch_size: int = 100, timeout: int = 300):
        """Start Kafka consumer (batches → S3)"""
        print("\n" + "="*70)
        print("STARTING CONSUMER - Kafka → S3")
        print("="*70)
        
        command = [sys.executable, str(self.consumer_script), "--batch-size", str(batch_size), "--timeout", str(timeout)]
        self.run_command(command, name=f"Kafka Consumer", background=True)
        
        print("\n✅ Consumer Started!")
        print(f"   - Batch Size: {batch_size} messages")
        print(f"   - Timeout: {timeout}s")
        print(f"   - Destination: S3 {os.getenv('RAW_BUCKET', 'automotive-raw-data-lerato-2026')}")

    def stop_all_processes(self):
        """Stop all running producer/consumer processes"""
        print("\n" + "="*70)
        print("STOPPING ALL PRODUCERS AND CONSUMERS")
        print("="*70)
        
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ Stopped process {process.pid}")
            except:
                process.kill()
                print(f"❌ Force-killed process {process.pid}")
        
        self.processes = []
        print("\n✅ All processes stopped!")

    def show_status(self):
        """Show current Kafka and container status"""
        print("\n" + "="*70)
        print("KAFKA STREAMING STATUS")
        print("="*70)
        
        self.run_command(
            ["docker", "ps", "--filter", "name=automotive"],
            name="Running Automotive Containers"
        )
        
        print("\n🔗 Access Points:")
        print("   - Kafka Broker: localhost:9092")
        print("   - Zookeeper: localhost:2181")
        print("   - Kafka UI: http://localhost:8888")
        print("   - S3 Raw Bucket: automotive-raw-data-lerato-2026")

    def run_demo(self):
        """Run a complete demo: Kafka → Producers → Consumer → S3 → Airflow"""
        print("\n" + "="*70)
        print("RUNNING COMPLETE STREAMING DEMO")
        print("="*70)
        
        steps = [
            ("1️⃣  Starting Kafka Infrastructure", self.start_kafka),
            ("2️⃣  Starting Producers (5 events over 30 seconds)", lambda: self.start_producers("all", interval=6, count=5)),
            ("3️⃣  Starting Consumer (batch → S3)", lambda: self.start_consumer(batch_size=5, timeout=60)),
            ("4️⃣  Running demo for 90 seconds", lambda: time.sleep(90)),
            ("5️⃣  Stopping all processes", self.stop_all_processes),
            ("6️⃣  Kafka status check", self.show_status),
        ]
        
        try:
            for step_name, step_func in steps:
                print(f"\n{'='*70}")
                print(step_name)
                print('='*70)
                step_func()
                time.sleep(2)
            
            print("\n" + "="*70)
            print("✅ DEMO COMPLETE!")
            print("="*70)
            print("\nData Flow Summary:")
            print("  Producers → Kafka Topics → Consumer")
            print("  → Batched into CSV → S3 raw folder")
            print("  → Airflow event_driven_real_time_etl triggers")
            print("  → ETL processes data → Warehouse")
            
        except KeyboardInterrupt:
            print("\n\n⏹️  Demo interrupted by user")
            self.stop_all_processes()
            self.stop_kafka()


def main():
    parser = argparse.ArgumentParser(
        description='Phase 6: Streaming Orchestration Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start Kafka infrastructure
  python orchestrator.py --kafka-start
  
  # Run complete demo
  python orchestrator.py --demo
  
  # Start all producers (infinite)
  python orchestrator.py --producers all --interval 5
  
  # Start specific producer with limit
  python orchestrator.py --producers sales --count 100
  
  # Start consumer
  python orchestrator.py --consumer
  
  # Stop everything
  python orchestrator.py --stop-all
  
  # Show status
  python orchestrator.py --status
        """
    )
    
    parser.add_argument('--kafka-start', action='store_true', help='Start Kafka infrastructure')
    parser.add_argument('--kafka-stop', action='store_true', help='Stop Kafka infrastructure')
    parser.add_argument('--producers', type=str, nargs='?', const='all',
                       choices=['sales', 'payments', 'interactions', 'inventory', 'procurement', 'telemetry', 'all'],
                       help='Start producer(s)')
    parser.add_argument('--interval', type=int, default=5, help='Seconds between events (default: 5)')
    parser.add_argument('--count', type=int, default=None, help='Total events to produce (default: infinite)')
    parser.add_argument('--consumer', action='store_true', help='Start consumer (batches → S3)')
    parser.add_argument('--demo', action='store_true', help='Run complete demo')
    parser.add_argument('--status', action='store_true', help='Show Kafka status')
    parser.add_argument('--stop-all', action='store_true', help='Stop all producers and consumers')
    
    args = parser.parse_args()
    
    orchestrator = StreamingOrchestrator()
    
    try:
        if args.kafka_start:
            orchestrator.start_kafka()
        elif args.kafka_stop:
            orchestrator.stop_kafka()
        elif args.producers:
            orchestrator.start_producers(event_type=args.producers, interval=args.interval, count=args.count)
        elif args.consumer:
            orchestrator.start_consumer()
        elif args.demo:
            orchestrator.run_demo()
        elif args.status:
            orchestrator.show_status()
        elif args.stop_all:
            orchestrator.stop_all_processes()
            orchestrator.stop_kafka()
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Orchestrator interrupted")
        orchestrator.stop_all_processes()


if __name__ == '__main__':
    main()
