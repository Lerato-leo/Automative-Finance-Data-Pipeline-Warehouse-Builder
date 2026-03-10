# Cloud Deployment Guide

## Overview

The project is already containerized locally through the root `docker-compose.yml`. Hosted deployment breaks into three concerns:

1. Airflow runtime
2. PostgreSQL warehouse
3. Secret and environment management

## 1. Dockerize Entire Application

The application already uses Docker Compose as the canonical local runtime:

- Airflow webserver, scheduler, worker
- Airflow metadata PostgreSQL
- Redis broker
- Kafka and Zookeeper for streaming
- Streamlit monitoring dashboard

Use this as the source of truth for service definitions and environment variables.

## 2. Airflow Deployment Options

### Option A: Astronomer

Recommended when managed Airflow is preferred.

Steps:

1. Create an Astronomer workspace and deployment.
2. Package DAGs and required project folders.
3. Ensure Phase 3, Phase 4, and Phase 8 assets are available to the Airflow runtime.
4. Set Airflow variables and environment variables for S3, SMTP, Teams, and warehouse connectivity.
5. Run a smoke-test DAG trigger after deployment.

### Option B: Self-Hosted Docker

Recommended when hosting on a VM or container platform.

Steps:

1. Provision a Linux VM or container host.
2. Install Docker and Docker Compose.
3. Copy the repository and `.env` values.
4. Start the stack with `docker compose up -d`.
5. Run `airflow db migrate` and create the Airflow admin user.
6. Expose ports `8081` for Airflow and `8501` for the monitoring dashboard.

## 3. PostgreSQL Warehouse Deployment

### Render

- provision a managed PostgreSQL instance
- capture external host, port, database, user, and password
- set `DB_HOST_EXTERNAL`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, and `DATABASE_URL_EXTERNAL`

### Railway

- provision a PostgreSQL service
- map the generated host and credentials into the same environment-variable contract used by the project

## 4. Environment Variables and Secrets

Minimum secret groups:

- AWS credentials
- bucket names
- warehouse credentials
- SMTP credentials
- Teams webhook
- optional SLA threshold for monitoring

Use `deployment/env.cloud.example` as the sanitized baseline.

## 5. Release Sequence

```text
Push repository
  -> provision managed warehouse
  -> configure secrets
  -> deploy Airflow runtime
  -> run schema and metrics-table migrations
  -> run one manual DAG execution
  -> start monitoring-dashboard service
  -> verify notifications and metrics
```

## 6. Post-Deployment Validation

- Airflow UI reachable
- DAG visible and healthy
- manual DAG run succeeds
- `pipeline_metrics` receives new rows
- Streamlit dashboard loads on port `8501`
- email and Teams notifications succeed

## 7. Deployment Link and Demo Video

This repository can document these release outputs, but they must be produced after the hosted environment exists.

Record these at release time:

- Airflow deployment URL
- Streamlit dashboard URL, if exposed publicly
- demo video link showing an end-to-end DAG run and dashboard verification

## Self-Hosted VM Commands

```bash
docker compose up -d airflow-postgres airflow-redis airflow-scheduler airflow-webserver airflow-worker monitoring-dashboard
docker exec airflow-webserver airflow db migrate
docker exec airflow-webserver airflow users create \
  --username admin --password change-me \
  --firstname Admin --lastname User \
  --role Admin --email admin@example.com
```

## Streamlit Cloud Notes

If the dashboard is deployed directly on Streamlit Cloud, the repository must expose a root `requirements.txt` so the platform installs dashboard dependencies.

Set these values in Streamlit app secrets:

```toml
DATABASE_URL_EXTERNAL = "postgresql://warehouse_user:your-password@your-render-host:5432/automative_warehousee_ygg3"
DB_SSLMODE = "require"
```

If you prefer split fields instead of a single URL, set `DB_HOST_EXTERNAL`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD`. For Render or Railway, use `DB_SSLMODE=require`.

Use `finance-data-platform/phase_8_monitoring_logging/dashboard/monitoring_dashboard.py` as the app entrypoint.
