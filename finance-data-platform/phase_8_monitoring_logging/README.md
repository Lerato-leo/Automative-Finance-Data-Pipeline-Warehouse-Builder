# 📊 Phase 8: Monitoring & Logging

## Overview

Phase 8 now integrates observability directly into the existing Automotive Finance pipeline. Logging is emitted from the Phase 3 and Phase 4 scripts into Airflow task logs, data-quality checks can fail the DAG run, every DAG run writes a monitoring record into PostgreSQL, and a Streamlit dashboard visualizes pipeline health from the warehouse.

## Deliverables

```text
phase_8_monitoring_logging/
├── dashboard/
│   └── monitoring_dashboard.py
├── docs/
│   └── monitoring_architecture.md
├── logging/
│   └── logging_config.py
├── sql/
│   └── create_pipeline_metrics_table.sql
└── README.md
```

## What This Phase Implements

- execution logging for Phase 3 ingestion, Phase 4 ETL, and the Airflow DAG
- data-quality validation for row counts, null counts, duplicate detection, and schema checks
- pipeline metrics storage in `pipeline_metrics`
- alerts for failures, quality validation failures, and SLA overruns using email and Teams
- a Streamlit dashboard for success/failure rates, volume trends, processing times, recent runs, and files processed

## Run Order

1. Apply `sql/create_pipeline_metrics_table.sql` to the warehouse.
2. Deploy the updated Airflow DAG and ETL scripts.
3. Start the Streamlit dashboard with `streamlit run phase_8_monitoring_logging/dashboard/monitoring_dashboard.py`.
4. Review the system design in `docs/monitoring_architecture.md`.

## Status

**Status:** ✅ Implemented  
**Last Updated:** March 10, 2026