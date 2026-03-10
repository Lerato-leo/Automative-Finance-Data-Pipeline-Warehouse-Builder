"""Streamlit monitoring dashboard for Automotive Finance pipeline runs."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import psycopg2
import streamlit as st

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:  # pragma: no cover - fallback for environments missing the helper package
    def st_autorefresh(*args, **kwargs):
        return None


ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"


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


def get_connection() -> psycopg2.extensions.connection:
    load_env(ROOT_ENV)
    host = os.getenv("DB_HOST_EXTERNAL") or os.getenv("DB_HOST")
    return psycopg2.connect(
        host=host,
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


@st.cache_data(ttl=10)
def load_pipeline_metrics() -> pd.DataFrame:
    query = """
        SELECT
            pipeline_name,
            dag_id,
            files_processed,
            rows_loaded,
            processing_time_seconds,
            status,
            run_timestamp
        FROM pipeline_metrics
        ORDER BY run_timestamp DESC
        LIMIT 500
    """
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, parse_dates=["run_timestamp"])


def main() -> None:
    st.set_page_config(page_title="Automotive Finance Monitoring Dashboard", layout="wide")
    st_autorefresh(interval=10_000, key="automotive-finance-monitoring-refresh")

    st.title("Automotive Finance Monitoring Dashboard")
    st.caption("Auto-refresh every 10 seconds")

    metrics_df = load_pipeline_metrics()
    if metrics_df.empty:
        st.warning("No pipeline metrics are available yet. Run the Airflow DAG to populate the dashboard.")
        return

    metrics_df = metrics_df.sort_values("run_timestamp")
    status_counts = metrics_df["status"].value_counts()
    success_count = int(status_counts.get("SUCCESS", 0))
    failure_count = int(status_counts.get("FAILED", 0))
    total_runs = success_count + failure_count
    success_rate = round((success_count / total_runs) * 100, 2) if total_runs else 0.0
    failure_rate = round((failure_count / total_runs) * 100, 2) if total_runs else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Runs", f"{len(metrics_df)}")
    col2.metric("Success Rate", f"{success_rate}%")
    col3.metric("Failure Rate", f"{failure_rate}%")
    col4.metric("Latest Rows Loaded", f"{int(metrics_df.iloc[-1]['rows_loaded'])}")

    st.subheader("Pipeline Success vs Failure Rate")
    st.bar_chart(status_counts.rename_axis("status").reset_index(name="runs").set_index("status"))

    st.subheader("Data Volume Trends")
    st.line_chart(metrics_df.set_index("run_timestamp")[["rows_loaded"]])

    st.subheader("Processing Time Metrics")
    st.line_chart(metrics_df.set_index("run_timestamp")[["processing_time_seconds"]])

    st.subheader("Files Processed Per Run")
    files_chart = metrics_df[["run_timestamp", "files_processed"]].copy()
    files_chart["run_label"] = files_chart["run_timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    st.bar_chart(files_chart.set_index("run_label")[["files_processed"]].tail(30))

    st.subheader("Recent Pipeline Runs")
    recent_runs = metrics_df.sort_values("run_timestamp", ascending=False).head(20).copy()
    recent_runs["run_timestamp"] = recent_runs["run_timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    st.dataframe(recent_runs, use_container_width=True)


if __name__ == "__main__":
    main()