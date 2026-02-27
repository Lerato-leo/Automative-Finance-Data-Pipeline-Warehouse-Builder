CREATE SCHEMA IF NOT EXISTS monitoring;

CREATE OR REPLACE VIEW monitoring.v_pipeline_success_failure AS
SELECT
    run_date,
    dag_id,
    SUM(total_runs) AS total_runs,
    SUM(successful_runs) AS successful_runs,
    SUM(failed_runs) AS failed_runs,
    ROUND((SUM(successful_runs)::NUMERIC / NULLIF(SUM(total_runs), 0)) * 100, 2) AS success_rate
FROM monitoring.pipeline_execution_log
GROUP BY run_date, dag_id;

CREATE OR REPLACE VIEW monitoring.v_data_volume_trends AS
SELECT
    snapshot_date,
    table_name,
    row_count,
    LAG(row_count) OVER (PARTITION BY table_name ORDER BY snapshot_date) AS previous_row_count,
    row_count - LAG(row_count) OVER (PARTITION BY table_name ORDER BY snapshot_date) AS growth_delta
FROM monitoring.data_volume_metrics;

CREATE OR REPLACE VIEW monitoring.v_processing_time_trends AS
SELECT
    run_date,
    dag_id,
    avg_duration_seconds,
    p95_duration_seconds,
    AVG(avg_duration_seconds) OVER (
        PARTITION BY dag_id
        ORDER BY run_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS rolling_7day_avg
FROM monitoring.processing_time_metrics;
