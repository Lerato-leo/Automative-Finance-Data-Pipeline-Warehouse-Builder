# Directory Explanations

## docs/
Centralized documentation, architecture diagrams, business context, deployment guides, runbooks, and glossary for onboarding and compliance.

## cloud_storage/
Represents AWS S3 landing zones for raw data, organized by domain. Ensures scalable, durable, and cloud-native storage.

## ingestion/
Python and Bash scripts for ingesting data from S3, simulating file lifecycle, archiving, and validation. Separation of concerns for maintainability.

## etl/
Python scripts for light transformations and staging data. Handles initial data cleaning and preparation.

## elt/
SQL scripts for transforming, loading, and modeling data within PostgreSQL. Builds star schema, marts, and applies data quality checks.

## warehouse/
Database schema definitions for staging, warehouse, marts, and star schema. Supports logical separation and optimized analytics.

## orchestration/
Airflow DAGs, configs, operators, and sensors for pipeline orchestration. Enables workflow management, retries, and scheduling.

## streaming/
Kafka assets for simulating streaming ingestion, including producers, consumers, and topic definitions. Supports real-time and event-driven architecture.

## monitoring/
Logging, alerting, dashboards, and data quality metrics for observability and reliability.

## dba/
Database administration scripts for backups, indexing, partitioning, performance tuning, and recovery. Ensures warehouse reliability and performance.

## deployment/
Docker assets, cloud deployment configs, repo setup, and CI/CD pipelines for reproducible, scalable deployments.
