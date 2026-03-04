#!/usr/bin/env python3
"""
Start Airflow Services (Docker Compose)
Initialize database and start webserver, scheduler, and workers
"""

import subprocess
import time
import sys
import os
from pathlib import Path

print("\n" + "="*80)
print("🚀 STARTING AIRFLOW SERVICES (DOCKER COMPOSE)")
print("="*80 + "\n")

# Check for .env file in project root (two levels up from this script)
project_root = Path(__file__).parent.parent.parent
env_file = project_root / '.env'
env_template = project_root / '.env.template'

if not env_file.exists():
    print("❌ ERROR: .env file not found!")
    print("-" * 80)
    print(f"Location expected: {env_file}")
    print("\n📋 Setup Instructions:")
    print(f"1. Copy the template file:")
    print(f"   cp {env_template} {env_file}")
    print(f"\n2. Edit {env_file} and fill in your AWS credentials:")
    print(f"   AWS_ACCESS_KEY_ID=your_access_key")
    print(f"   AWS_SECRET_ACCESS_KEY=your_secret_key")
    print(f"   AWS_DEFAULT_REGION=us-east-1")
    print(f"   RAW_BUCKET=your-raw-bucket-name")
    print(f"   STAGING_BUCKET=your-staging-bucket-name")
    print(f"   ARCHIVE_BUCKET=your-archive-bucket-name")
    print(f"   RAW_S3_EVENTS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/<account-id>/<queue-name>")
    print(f"\n3. Run this script again: python start_airflow.py")
    sys.exit(1)

print(f"✅ .env file found: {env_file}\n")

# Load environment variables from .env
try:
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    k, v = line.split('=', 1)
                    os.environ[k.strip()] = v.strip().strip('"').strip("'")
    print("✅ Environment variables loaded from .env\n")
except Exception as e:
    print(f"⚠️  Warning: Could not load .env file: {e}\n")

# Step 1: Docker Compose Up
print("Step 1: Starting Docker containers...")
print("-" * 80)

try:
    result = subprocess.run(
        ["docker", "compose", "--env-file", "../../.env", "up", "-d"],
        cwd=os.path.dirname(__file__),
        capture_output=True,
        text=True,
        timeout=120
    )
    
    if result.returncode == 0:
        print("✅ Docker containers started\n")
    else:
        print(f"❌ Docker Compose failed:\n{result.stderr}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error starting Docker: {e}")
    sys.exit(1)

# Step 2: Wait for services
print("Step 2: Waiting for services to be healthy...")
print("-" * 80)

time.sleep(10)
print("✅ Services initialized\n")

# Step 3: Initialize Airflow database
print("Step 3: Initializing Airflow database...")
print("-" * 80)

try:
    result = subprocess.run(
        ["docker", "exec", "airflow-webserver", "airflow", "db", "init"],
        capture_output=True,
        text=True,
        timeout=60
    )
    
    if result.returncode == 0:
        print("✅ Airflow database initialized\n")
    else:
        # Database might already exist, that's OK
        if "already exists" in result.stderr.lower():
            print("✅ Airflow database already exists\n")
        else:
            print(f"⚠️  Database init message: {result.stderr[:200]}\n")
except Exception as e:
    print(f"⚠️  Database init (might already exist): {e}\n")

# Step 4: Create default admin user (if not exists)
print("Step 4: Creating default admin user...")
print("-" * 80)

try:
    result = subprocess.run(
        ["docker", "exec", "airflow-webserver", "airflow", "users", "create",
         "--username", "admin",
         "--firstname", "Admin",
         "--lastname", "User",
         "--role", "Admin",
         "--email", "admin@example.com",
         "--password", "admin"],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode == 0 or "already exists" in result.stderr.lower():
        print("✅ Admin user ready (username: admin, password: admin)\n")
    else:
        print(f"⚠️  Admin user: {result.stderr[:200]}\n")
except Exception as e:
    print(f"⚠️  Admin user creation: {e}\n")

# Step 5: Show status and access info
print("\n" + "="*80)
print("📊 AIRFLOW STATUS")
print("="*80 + "\n")

try:
    result = subprocess.run(
        ["docker", "ps", "--filter", "name=airflow"],
        capture_output=True,
        text=True
    )
    
    # Show running services
    lines = result.stdout.strip().split('\n')[1:]  # Skip header
    for line in lines:
        if line.strip():
            print(f"  {line}")
except:
    pass

print(f"""
✅ Airflow Services Started!

ACCESS AIRFLOW UI:
    http://localhost:8081
  
LOGIN:
  Username: admin
  Password: admin

SERVICES RUNNING:
    ✓ webserver    (UI + REST API) - localhost:8081
  ✓ scheduler    (DAG orchestration)
  ✓ worker       (Task execution)
    ✓ postgres     (Metadata database) - localhost:{os.getenv('AIRFLOW_POSTGRES_HOST_PORT', '5433')}
  ✓ redis        (Message broker) - localhost:6379

DAGs LOCATION:
  {os.path.join(os.path.dirname(__file__), 'dags')}

STOP ALL SERVICES:
  docker compose down

VIEW LOGS:
  docker compose logs -f webserver
  docker compose logs -f scheduler
  docker compose logs -f worker
""")

print("="*80 + "\n")
