import argparse
import os
from pathlib import Path

import psycopg2


ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"
BASE_DIR = Path(__file__).resolve().parent


FACT_TABLES = [
    "warehouse.fact_sales",
    "warehouse.fact_payments",
    "warehouse.fact_procurement",
    "warehouse.fact_inventory",
    "warehouse.fact_interactions",
    "warehouse.fact_telemetry",
]


def load_env(path: Path) -> None:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as file:
        for raw in file:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def get_warehouse_conn():
    host = os.getenv("DB_HOST_EXTERNAL") or os.getenv("DB_HOST")
    return psycopg2.connect(
        host=host,
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def get_airflow_conn():
    airflow_url = os.getenv("AIRFLOW_DB_URL", "postgresql://airflow:airflow@localhost:5432/airflow")
    return psycopg2.connect(airflow_url)


def apply_sql_file(path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    with get_warehouse_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)


def setup_monitoring_schema() -> None:
    apply_sql_file(BASE_DIR / "sql" / "monitoring_schema.sql")
    apply_sql_file(BASE_DIR / "sql" / "dashboard_views.sql")
    print("Monitoring schema and dashboard views applied")


def collect_pipeline_success_failure(days_back: int = 7) -> None:
    pipeline_sql = """
        SELECT
            dag_id,
            DATE(execution_date) AS run_date,
            COUNT(*) AS total_runs,
            SUM(CASE WHEN state = 'success' THEN 1 ELSE 0 END) AS successful_runs,
            SUM(CASE WHEN state = 'failed' THEN 1 ELSE 0 END) AS failed_runs,
            ROUND(AVG(EXTRACT(EPOCH FROM (end_date - start_date)))::NUMERIC, 2) AS avg_duration_seconds
        FROM dag_run
        WHERE execution_date >= CURRENT_DATE - (%s || ' days')::INTERVAL
        GROUP BY dag_id, DATE(execution_date)
    """

    insert_sql = """
        INSERT INTO monitoring.pipeline_execution_log (
            dag_id, run_date, total_runs, successful_runs, failed_runs, success_rate, avg_duration_seconds
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    with get_airflow_conn() as airflow_conn, get_warehouse_conn() as warehouse_conn:
        with airflow_conn.cursor() as airflow_cursor, warehouse_conn.cursor() as warehouse_cursor:
            airflow_cursor.execute(pipeline_sql, (days_back,))
            rows = airflow_cursor.fetchall()
            for dag_id, run_date, total_runs, successful_runs, failed_runs, avg_duration_seconds in rows:
                success_rate = round((successful_runs / total_runs) * 100, 2) if total_runs else 0
                warehouse_cursor.execute(
                    insert_sql,
                    (
                        dag_id,
                        run_date,
                        total_runs,
                        successful_runs,
                        failed_runs,
                        success_rate,
                        avg_duration_seconds,
                    ),
                )

    print(f"Collected pipeline success/failure metrics ({days_back} day window)")


def collect_processing_time_metrics(days_back: int = 7) -> None:
    sql = """
        SELECT
            dag_id,
            DATE(execution_date) AS run_date,
            ROUND(AVG(EXTRACT(EPOCH FROM (end_date - start_date)))::NUMERIC, 2) AS avg_duration,
            ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (end_date - start_date)))::NUMERIC, 2) AS p95_duration
        FROM dag_run
        WHERE execution_date >= CURRENT_DATE - (%s || ' days')::INTERVAL
          AND end_date IS NOT NULL
          AND start_date IS NOT NULL
        GROUP BY dag_id, DATE(execution_date)
    """

    insert_sql = """
        INSERT INTO monitoring.processing_time_metrics (dag_id, run_date, avg_duration_seconds, p95_duration_seconds)
        VALUES (%s, %s, %s, %s)
    """

    with get_airflow_conn() as airflow_conn, get_warehouse_conn() as warehouse_conn:
        with airflow_conn.cursor() as airflow_cursor, warehouse_conn.cursor() as warehouse_cursor:
            airflow_cursor.execute(sql, (days_back,))
            for row in airflow_cursor.fetchall():
                warehouse_cursor.execute(insert_sql, row)

    print("Collected processing time metrics")


def collect_data_volume_trends() -> None:
    insert_sql = """
        INSERT INTO monitoring.data_volume_metrics (table_name, row_count, snapshot_date)
        VALUES (%s, %s, CURRENT_DATE)
    """

    with get_warehouse_conn() as conn:
        with conn.cursor() as cursor:
            for table in FACT_TABLES:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                cursor.execute(insert_sql, (table, row_count))

    print("Collected data volume trend metrics")


def collect_data_quality_metrics(null_threshold: float = 1.0) -> None:
    quality_checks = [
        ("warehouse.fact_sales", "sale_id", "sale_id_null_rate"),
        ("warehouse.fact_payments", "payment_id", "payment_id_null_rate"),
        ("warehouse.fact_interactions", "interaction_id", "interaction_id_null_rate"),
    ]

    insert_sql = """
        INSERT INTO monitoring.data_quality_metrics (table_name, metric_name, metric_value, metric_threshold, metric_status)
        VALUES (%s, %s, %s, %s, %s)
    """

    with get_warehouse_conn() as conn:
        with conn.cursor() as cursor:
            for table_name, key_column, metric_name in quality_checks:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                total_rows = cursor.fetchone()[0]
                if total_rows == 0:
                    null_rate = 0
                else:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {key_column} IS NULL")
                    null_rows = cursor.fetchone()[0]
                    null_rate = round((null_rows / total_rows) * 100, 4)

                status = "PASS" if null_rate <= null_threshold else "FAIL"
                cursor.execute(
                    insert_sql,
                    (table_name, metric_name, null_rate, null_threshold, status),
                )

    print("Collected data quality metrics")


def collect_error_tracking(days_back: int = 7) -> None:
    airflow_sql = """
        SELECT
            ti.dag_id,
            ti.task_id,
            ti.run_id,
            COALESCE(ti.state, 'unknown') AS error_summary,
            CONCAT('Task state=', ti.state, ', try_number=', ti.try_number) AS error_details
        FROM task_instance ti
        WHERE ti.state = 'failed'
          AND ti.start_date >= CURRENT_DATE - (%s || ' days')::INTERVAL
    """

    insert_sql = """
        INSERT INTO monitoring.error_tracking (dag_id, task_id, run_id, error_summary, error_details)
        VALUES (%s, %s, %s, %s, %s)
    """

    with get_airflow_conn() as airflow_conn, get_warehouse_conn() as warehouse_conn:
        with airflow_conn.cursor() as airflow_cursor, warehouse_conn.cursor() as warehouse_cursor:
            airflow_cursor.execute(airflow_sql, (days_back,))
            for row in airflow_cursor.fetchall():
                warehouse_cursor.execute(insert_sql, row)

    print("Collected error tracking data")


def run_full_collection(days_back: int = 7) -> None:
    setup_monitoring_schema()
    collect_pipeline_success_failure(days_back=days_back)
    collect_processing_time_metrics(days_back=days_back)
    collect_data_volume_trends()
    collect_data_quality_metrics()
    collect_error_tracking(days_back=days_back)
    print("Phase 8 monitoring collection completed")


def parse_args():
    parser = argparse.ArgumentParser(description="Phase 8 - Monitoring collector")
    parser.add_argument(
        "action",
        choices=[
            "setup",
            "collect-all",
            "pipeline-metrics",
            "processing-time",
            "volume-metrics",
            "quality-metrics",
            "error-tracking",
        ],
    )
    parser.add_argument("--days-back", type=int, default=7)
    return parser.parse_args()


def main():
    load_env(ROOT_ENV)
    args = parse_args()

    if args.action == "setup":
        setup_monitoring_schema()
    elif args.action == "collect-all":
        run_full_collection(days_back=args.days_back)
    elif args.action == "pipeline-metrics":
        collect_pipeline_success_failure(days_back=args.days_back)
    elif args.action == "processing-time":
        collect_processing_time_metrics(days_back=args.days_back)
    elif args.action == "volume-metrics":
        collect_data_volume_trends()
    elif args.action == "quality-metrics":
        collect_data_quality_metrics()
    elif args.action == "error-tracking":
        collect_error_tracking(days_back=args.days_back)


if __name__ == "__main__":
    main()
