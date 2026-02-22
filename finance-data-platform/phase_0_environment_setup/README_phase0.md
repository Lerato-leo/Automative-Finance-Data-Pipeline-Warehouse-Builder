# Phase 0: Environment Setup

## Purpose
- Set up schemas in the warehouse database (staging, warehouse, analytics, metadata)
- Install required tools and Python libraries
- Establish S3 buckets for raw, staging, and archive data
- Document repo structure and configuration

## Contents
- `00_create_schemas.sql`: SQL script to create schemas
- `requirements.txt`: Python dependencies
- `aws_config.md`: S3 bucket documentation
- `docker-compose.yml` (optional): Local orchestration
- `.env.example`: Example environment variables

## S3 Buckets
- automotive-raw-data-lerato-2026
- automotive-staging-data-lerato-2026
- automotive-archive-data-lerato-2026

## Tools
- Python 3.11
- PostgreSQL
- Docker & Docker Compose
- Git
- AWS CLI

## How to Use
1. Install dependencies from `requirements.txt`
2. Set up your `.env` file (see `.env.example`)
3. Run `00_create_schemas.sql` in your warehouse DB
4. Review S3 structure in `aws_config.md`

---
This phase ensures a reproducible, documented, and cloud-ready foundation for the data platform.
