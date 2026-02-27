CREATE SCHEMA IF NOT EXISTS monitoring;

CREATE TABLE IF NOT EXISTS monitoring.pipeline_execution_log (
    id BIGSERIAL PRIMARY KEY,
    captured_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dag_id TEXT NOT NULL,
    run_date DATE NOT NULL,
    total_runs INT NOT NULL,
    successful_runs INT NOT NULL,
    failed_runs INT NOT NULL,
    success_rate NUMERIC(6,2) NOT NULL,
    avg_duration_seconds NUMERIC(12,2)
);

CREATE TABLE IF NOT EXISTS monitoring.data_quality_metrics (
    id BIGSERIAL PRIMARY KEY,
    captured_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    table_name TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value NUMERIC(18,4) NOT NULL,
    metric_threshold NUMERIC(18,4),
    metric_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS monitoring.data_volume_metrics (
    id BIGSERIAL PRIMARY KEY,
    captured_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    table_name TEXT NOT NULL,
    row_count BIGINT NOT NULL,
    snapshot_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS monitoring.processing_time_metrics (
    id BIGSERIAL PRIMARY KEY,
    captured_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dag_id TEXT NOT NULL,
    run_date DATE NOT NULL,
    avg_duration_seconds NUMERIC(12,2),
    p95_duration_seconds NUMERIC(12,2)
);

CREATE TABLE IF NOT EXISTS monitoring.error_tracking (
    id BIGSERIAL PRIMARY KEY,
    captured_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dag_id TEXT,
    task_id TEXT,
    run_id TEXT,
    error_summary TEXT NOT NULL,
    error_details TEXT
);

CREATE TABLE IF NOT EXISTS monitoring.alert_events (
    id BIGSERIAL PRIMARY KEY,
    captured_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    alert_message TEXT NOT NULL,
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE
);
