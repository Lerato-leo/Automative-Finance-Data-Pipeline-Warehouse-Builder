import argparse
import json
import os
from datetime import date
from pathlib import Path

import psycopg2
from psycopg2.pool import SimpleConnectionPool


ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"
BASE_DIR = Path(__file__).resolve().parent


QUERY_PLAN_QUERIES = {
    "sales_by_month": """
        SELECT DATE_TRUNC('month', sale_date) AS month_start, COUNT(*) AS sales_count, SUM(final_price) AS sales_value
        FROM warehouse.fact_sales
        WHERE sale_date >= CURRENT_DATE - INTERVAL '180 days'
        GROUP BY 1
        ORDER BY 1 DESC
    """,
    "payments_status_mix": """
        SELECT payment_status, COUNT(*) AS total, SUM(payment_amount) AS amount
        FROM warehouse.fact_payments
        WHERE payment_date >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY payment_status
        ORDER BY total DESC
    """,
    "daily_pipeline_interactions": """
        SELECT interaction_date, COUNT(*)
        FROM warehouse.fact_interactions
        WHERE interaction_date >= CURRENT_DATE - INTERVAL '60 days'
        GROUP BY interaction_date
        ORDER BY interaction_date DESC
    """,
}


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


def get_db_url() -> str:
    db_url = os.getenv("DATABASE_URL_EXTERNAL")
    if db_url:
        return db_url

    host = os.getenv("DB_HOST_EXTERNAL") or os.getenv("DB_HOST")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    if not all([host, name, user, password]):
        raise RuntimeError("Database connection details are missing in root .env")

    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


def get_connection():
    return psycopg2.connect(get_db_url())


def run_sql_file(file_path: Path) -> None:
    sql = file_path.read_text(encoding="utf-8")
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)
    print(f"Applied SQL: {file_path.name}")


def create_monthly_partition(cursor, table_base: str, column: str, year: int, month: int) -> None:
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    partition_name = f"{table_base}_{year}_{str(month).zfill(2)}"
    sql = f"""
        CREATE TABLE IF NOT EXISTS warehouse.{partition_name}
        PARTITION OF warehouse.{table_base}
        FOR VALUES FROM ('{start_date}') TO ('{end_date}');
    """
    cursor.execute(sql)


def setup_partitioning(months_ahead: int = 6) -> None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            today = date.today()
            year, month = today.year, today.month
            for _ in range(months_ahead):
                create_monthly_partition(cursor, "fact_sales_partitioned", "sale_date", year, month)
                create_monthly_partition(cursor, "fact_payments_partitioned", "payment_date", year, month)
                month += 1
                if month > 12:
                    month = 1
                    year += 1
    print(f"Created/validated monthly partitions for next {months_ahead} months")


def capture_query_plans() -> None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            for name, query in QUERY_PLAN_QUERIES.items():
                cursor.execute(f"EXPLAIN (FORMAT JSON) {query}")
                explain = cursor.fetchone()[0]
                plan = explain[0]["Plan"]
                cursor.execute(
                    """
                    INSERT INTO admin.query_plan_history (query_name, execution_plan, total_cost, plan_rows, plan_width)
                    VALUES (%s, %s::jsonb, %s, %s, %s)
                    """,
                    (
                        name,
                        json.dumps(explain),
                        plan.get("Total Cost"),
                        plan.get("Plan Rows"),
                        plan.get("Plan Width"),
                    ),
                )
    print("Captured EXPLAIN plans into admin.query_plan_history")


def capture_table_growth() -> None:
    sql = """
        INSERT INTO admin.table_growth_history (table_schema, table_name, table_size_bytes, total_size_bytes, estimated_rows)
        SELECT
            n.nspname AS table_schema,
            c.relname AS table_name,
            pg_table_size(c.oid) AS table_size_bytes,
            pg_total_relation_size(c.oid) AS total_size_bytes,
            c.reltuples::BIGINT AS estimated_rows
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname IN ('warehouse', 'staging')
          AND c.relkind = 'r';
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)
    print("Captured table size snapshot into admin.table_growth_history")


def test_connection_pool(min_conn: int = 1, max_conn: int = 10) -> None:
    pool = SimpleConnectionPool(minconn=min_conn, maxconn=max_conn, dsn=get_db_url())
    borrowed = []
    try:
        for _ in range(max_conn):
            conn = pool.getconn()
            borrowed.append(conn)
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
    finally:
        for conn in borrowed:
            pool.putconn(conn)
        pool.closeall()

    print(f"Connection pool test passed ({max_conn} concurrent connections)")


def optimize_all() -> None:
    run_sql_file(BASE_DIR / "sql" / "admin_schema.sql")
    run_sql_file(BASE_DIR / "sql" / "performance_optimization.sql")
    setup_partitioning(months_ahead=6)
    capture_query_plans()
    capture_table_growth()
    test_connection_pool()
    print("Phase 7 performance optimization completed")


def parse_args():
    parser = argparse.ArgumentParser(description="Phase 7 - Database administration toolkit")
    parser.add_argument(
        "action",
        choices=[
            "optimize",
            "partitions",
            "plans",
            "table-growth",
            "pool-test",
            "apply-admin-schema",
        ],
        help="Action to execute",
    )
    parser.add_argument("--months-ahead", type=int, default=6, help="How many future monthly partitions to prepare")
    parser.add_argument("--pool-size", type=int, default=10, help="Max connections for pool-test")
    return parser.parse_args()


def main():
    load_env(ROOT_ENV)
    args = parse_args()

    if args.action == "optimize":
        optimize_all()
    elif args.action == "partitions":
        setup_partitioning(months_ahead=args.months_ahead)
    elif args.action == "plans":
        capture_query_plans()
    elif args.action == "table-growth":
        capture_table_growth()
    elif args.action == "pool-test":
        test_connection_pool(max_conn=args.pool_size)
    elif args.action == "apply-admin-schema":
        run_sql_file(BASE_DIR / "sql" / "admin_schema.sql")


if __name__ == "__main__":
    main()
