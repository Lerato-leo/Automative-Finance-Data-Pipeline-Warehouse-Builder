CREATE TABLE IF NOT EXISTS pipeline_metrics (
    id BIGSERIAL PRIMARY KEY,
    pipeline_name VARCHAR(255) NOT NULL,
    dag_id VARCHAR(255) NOT NULL,
    files_processed INTEGER NOT NULL DEFAULT 0,
    rows_loaded BIGINT NOT NULL DEFAULT 0,
    processing_time_seconds NUMERIC(12, 2) NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL,
    run_timestamp TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_pipeline_metrics_run_timestamp
    ON pipeline_metrics (run_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_pipeline_metrics_status
    ON pipeline_metrics (status);