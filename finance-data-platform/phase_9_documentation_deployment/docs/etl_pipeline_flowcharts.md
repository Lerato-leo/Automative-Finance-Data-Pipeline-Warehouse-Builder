# ETL Pipeline Flowcharts

## Batch Pipeline Flow

```mermaid
flowchart TD
    A[Source files uploaded to S3 RAW] --> B[Airflow monitor_raw_bucket]
    B --> C[Phase 3 ingest.py]
    C --> D[Validation and file movement]
    D --> E[S3 STAGING bucket]
    E --> F[Phase 4 etl_main.py]
    F --> G[Schema validation]
    G --> H[Transform and deduplicate]
    H --> I[Load staging and warehouse targets]
    I --> J[Emit ETL_SUMMARY payload]
    J --> K[Airflow archive_processed_staging_files]
    K --> L[S3 ARCHIVE bucket]
    J --> M[Persist pipeline_metrics]
    M --> N[Streamlit dashboard]
```

## Streaming-Assisted Flow

```mermaid
flowchart TD
    A[Kafka producer] --> B[Kafka topics]
    B --> C[Kafka consumer]
    C --> D[Write files into S3 RAW]
    D --> E[Airflow scheduled DAG]
    E --> F[Same batch ingestion path]
```

## Error Flow

```mermaid
flowchart TD
    A[ETL validation error] --> B[Phase 4 raises exception]
    B --> C[Airflow task marked failed]
    C --> D[on_failure_callback runs]
    D --> E[Failure notification via email and Teams]
    D --> F[FAILED record persisted to pipeline_metrics]
```

## Key Design Choice

The project uses one orchestration path. Batch uploads and Kafka-assisted ingestion both converge on the same Airflow DAG so alerting, archive handling, ETL logic, and monitoring stay consistent.