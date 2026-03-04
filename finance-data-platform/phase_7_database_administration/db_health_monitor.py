import argparse
import os
from pathlib import Path

import psycopg2


ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"


HEALTH_QUERIES = {
    "active_connections": "SELECT COUNT(*) FROM pg_stat_activity",
    "long_running_queries": """
        SELECT COUNT(*)
        FROM pg_stat_activity
        WHERE state = 'active'
          AND NOW() - query_start > INTERVAL '2 minutes'
    """,
    "slow_statements_available": "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements')",
}


TOP_TABLES_QUERY = """
    SELECT
        n.nspname AS schema_name,
        c.relname AS table_name,
        pg_size_pretty(pg_total_relation_size(c.oid)) AS total_size,
        pg_total_relation_size(c.oid) AS total_size_bytes,
        c.reltuples::BIGINT AS estimated_rows
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.relkind = 'r'
      AND n.nspname IN ('warehouse', 'staging')
    ORDER BY pg_total_relation_size(c.oid) DESC
    LIMIT 15;
"""


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


def connection_params() -> dict:
    return {
        "host": os.getenv("DB_HOST_EXTERNAL") or os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT", "5432"),
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
    }


def get_connection():
    cfg = connection_params()
    if not all([cfg["host"], cfg["dbname"], cfg["user"], cfg["password"]]):
        raise RuntimeError("Missing DB config values in root .env")
    return psycopg2.connect(**cfg)


def run_health_check() -> None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            print("\nDatabase Health Snapshot")
            print("=" * 40)
            for name, query in HEALTH_QUERIES.items():
                cursor.execute(query)
                value = cursor.fetchone()[0]
                print(f"- {name}: {value}")

            print("\nTop tables by size")
            print("=" * 40)
            cursor.execute(TOP_TABLES_QUERY)
            for schema_name, table_name, total_size, _, estimated_rows in cursor.fetchall():
                print(f"- {schema_name}.{table_name}: {total_size} (rows~{estimated_rows})")


def capture_query_runtime(query_name: str, query: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS admin")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS admin.query_performance_history (
                    id BIGSERIAL PRIMARY KEY,
                    captured_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    query_name TEXT NOT NULL,
                    execution_ms NUMERIC NOT NULL,
                    rows_returned BIGINT NOT NULL
                )
                """
            )

            cursor.execute(f"EXPLAIN (ANALYZE, FORMAT JSON) {query}")
            explain_json = cursor.fetchone()[0]
            plan = explain_json[0]["Plan"]
            execution_ms = explain_json[0].get("Execution Time", 0)
            rows_returned = plan.get("Actual Rows", 0)

            cursor.execute(
                """
                INSERT INTO admin.query_performance_history (query_name, execution_ms, rows_returned)
                VALUES (%s, %s, %s)
                """,
                (query_name, execution_ms, rows_returned),
            )

    print(f"Captured performance for query '{query_name}' ({execution_ms} ms)")


def parse_args():
    parser = argparse.ArgumentParser(description="Phase 7 - DB health monitor")
    parser.add_argument("action", choices=["snapshot", "capture-query"])
    parser.add_argument("--query-name", default="adhoc_query")
    parser.add_argument("--query", default="SELECT COUNT(*) FROM warehouse.fact_sales")
    return parser.parse_args()


def main():
    load_env(ROOT_ENV)
    args = parse_args()

    if args.action == "snapshot":
        run_health_check()
    elif args.action == "capture-query":
        capture_query_runtime(args.query_name, args.query)


if __name__ == "__main__":
    main()
