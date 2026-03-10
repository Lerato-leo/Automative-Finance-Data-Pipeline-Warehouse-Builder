"""Single Airflow DAG for the automotive finance orchestration flow."""

# pyright: reportMissingImports=false, reportMissingModuleSource=false

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
from pathlib import Path
from subprocess import run
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import json
import os
import re
import smtplib
import sys
from time import perf_counter

import boto3
import psycopg2
try:
    from airflow import DAG
    from airflow.exceptions import AirflowException
    from airflow.operators.python import PythonOperator
except ModuleNotFoundError:
    class AirflowException(RuntimeError):
        """Fallback exception for local editor analysis without Airflow installed."""


    class DAG:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.args = args
            self.kwargs = kwargs

        def __enter__(self) -> "DAG":
            return self

        def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> bool:
            return False


    class PythonOperator:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.args = args
            self.kwargs = kwargs

        def __rshift__(self, other: Any) -> Any:
            return other

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*args: Any, **kwargs: Any) -> bool:
        return False

load_dotenv()

LOGGER = logging.getLogger(__name__)


def get_env_value(*names: str, default: str | None = None) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value not in (None, ""):
            return value
    return default


AIRFLOW_HOME = os.getenv("AIRFLOW_HOME", "/opt/airflow")
PROJECT_ROOT = os.getenv("PIPELINE_PROJECT_ROOT", "/opt/airflow/project")
PHASE_3_SCRIPT = os.path.join(PROJECT_ROOT, "phase_3_shell_ingestion", "ingest.py")
PHASE_4_SCRIPT = os.path.join(PROJECT_ROOT, "phase_4_python_etl", "etl_main.py")
PHASE_8_PIPELINE_METRICS_SQL = os.path.join(
    PROJECT_ROOT,
    "phase_8_monitoring_logging",
    "sql",
    "create_pipeline_metrics_table.sql",
)
PIPELINE_NAME = "automotive_finance_pipeline"

AWS_REGION = get_env_value(
    "AWS_REGION",
    "AWS_DEFAULT_REGION",
    "AIRFLOW_VAR_AWS_REGION",
    default="us-east-1",
)
AWS_ACCESS_KEY = get_env_value("AWS_ACCESS_KEY_ID", "AIRFLOW_VAR_AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = get_env_value("AWS_SECRET_ACCESS_KEY", "AIRFLOW_VAR_AWS_SECRET_ACCESS_KEY")

S3_RAW_BUCKET = get_env_value(
    "S3_RAW_BUCKET",
    "RAW_BUCKET",
    "AIRFLOW_VAR_S3_RAW_BUCKET",
    "AIRFLOW_VAR_RAW_BUCKET",
    default="automotive-raw-data-lerato-2026",
)
S3_STAGING_BUCKET = get_env_value(
    "S3_STAGING_BUCKET",
    "STAGING_BUCKET",
    "AIRFLOW_VAR_S3_STAGING_BUCKET",
    "AIRFLOW_VAR_STAGING_BUCKET",
    default="automotive-staging-data-lerato-2026",
)
S3_ARCHIVE_BUCKET = get_env_value(
    "S3_ARCHIVE_BUCKET",
    "ARCHIVE_BUCKET",
    "AIRFLOW_VAR_S3_ARCHIVE_BUCKET",
    "AIRFLOW_VAR_ARCHIVE_BUCKET",
    default="automotive-archive-data-lerato-2026",
)

SMTP_HOST = get_env_value("SMTP_HOST", "AIRFLOW_VAR_SMTP_HOST", default="smtp.gmail.com")
SMTP_PORT = int(get_env_value("SMTP_PORT", "AIRFLOW_VAR_SMTP_PORT", default="587"))
SMTP_USER = get_env_value(
    "SMTP_USER",
    "SMTP_USERNAME",
    "AIRFLOW_VAR_SMTP_USER",
    "AIRFLOW_VAR_SMTP_USERNAME",
)
SMTP_PASSWORD = get_env_value("SMTP_PASSWORD", "AIRFLOW_VAR_SMTP_PASSWORD")
SMTP_FROM = get_env_value(
    "SMTP_MAIL_FROM",
    "SMTP_FROM",
    "AIRFLOW_VAR_SMTP_FROM",
    default=SMTP_USER or "notifications@automativedata.com",
)
SMTP_TO = get_env_value(
    "SMTP_TO",
    "EMAIL_RECIPIENT",
    "AIRFLOW_VAR_EMAIL_RECIPIENT",
    default="lerato.matamela01@gmail.com",
)
TEAMS_WEBHOOK_URL = get_env_value("TEAMS_WEBHOOK_URL", "AIRFLOW_VAR_TEAMS_WEBHOOK_URL")
PIPELINE_SLA_THRESHOLD_SECONDS = int(
    get_env_value(
        "PIPELINE_SLA_THRESHOLD_SECONDS",
        "AIRFLOW_VAR_PIPELINE_SLA_THRESHOLD_SECONDS",
        default="600",
    )
)


def get_s3_client() -> Any:
    client_args: dict[str, Any] = {"service_name": "s3", "region_name": AWS_REGION}
    if AWS_ACCESS_KEY and AWS_SECRET_KEY:
        client_args["aws_access_key_id"] = AWS_ACCESS_KEY
        client_args["aws_secret_access_key"] = AWS_SECRET_KEY
    return boto3.client(**client_args)


def get_warehouse_connection() -> Any:
    warehouse_conn = build_warehouse_conn()
    if not warehouse_conn:
        raise AirflowException("WAREHOUSE_CONN could not be built for pipeline metrics storage")
    return psycopg2.connect(warehouse_conn)


def ensure_pipeline_metrics_table() -> None:
    sql_path = Path(PHASE_8_PIPELINE_METRICS_SQL)
    if not sql_path.exists():
        raise AirflowException(f"Pipeline metrics SQL file not found: {sql_path}")

    with get_warehouse_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql_path.read_text(encoding="utf-8"))
        conn.commit()


def extract_script_summary(stdout: str) -> dict[str, Any] | None:
    for line in reversed(stdout.splitlines()):
        if line.startswith("ETL_SUMMARY::"):
            payload = line.split("ETL_SUMMARY::", 1)[1].strip()
            try:
                return json.loads(payload)
            except json.JSONDecodeError:
                LOGGER.warning("Failed to parse ETL summary payload from script output")
                return None
    return None


def compute_dag_processing_time_seconds(context: Any) -> float:
    dag_run = context.get("dag_run")
    if dag_run and dag_run.start_date:
        return round((datetime.now(timezone.utc) - dag_run.start_date).total_seconds(), 2)
    return 0.0


def collect_pipeline_metrics_payload(context: Any, status: str) -> dict[str, Any]:
    task_instance = context["task_instance"]
    raw_files = task_instance.xcom_pull(task_ids="monitor_raw_bucket", key="raw_files") or []
    phase_4_result = task_instance.xcom_pull(task_ids="run_phase_4_etl") or {}
    phase_4_summary = phase_4_result.get("summary") or {}
    files_processed = phase_4_summary.get("files_processed") or phase_4_result.get("file_count") or len(raw_files)
    rows_loaded = phase_4_summary.get("rows_loaded") or phase_4_result.get("rows_loaded") or 0

    return {
        "pipeline_name": PIPELINE_NAME,
        "dag_id": context["dag"].dag_id,
        "files_processed": int(files_processed),
        "rows_loaded": int(rows_loaded),
        "processing_time_seconds": compute_dag_processing_time_seconds(context),
        "status": status,
        "run_timestamp": context["logical_date"],
    }


def persist_pipeline_metrics(context: Any, status: str) -> dict[str, Any]:
    ensure_pipeline_metrics_table()
    payload = collect_pipeline_metrics_payload(context, status)

    with get_warehouse_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM pipeline_metrics WHERE dag_id = %s AND run_timestamp = %s",
                (payload["dag_id"], payload["run_timestamp"]),
            )
            cursor.execute(
                """
                INSERT INTO pipeline_metrics (
                    pipeline_name,
                    dag_id,
                    files_processed,
                    rows_loaded,
                    processing_time_seconds,
                    status,
                    run_timestamp
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    payload["pipeline_name"],
                    payload["dag_id"],
                    payload["files_processed"],
                    payload["rows_loaded"],
                    payload["processing_time_seconds"],
                    payload["status"],
                    payload["run_timestamp"],
                ),
            )
        conn.commit()

    LOGGER.info("Pipeline metrics stored | status=%s | files_processed=%s | rows_loaded=%s | processing_time_seconds=%.2f", payload["status"], payload["files_processed"], payload["rows_loaded"], payload["processing_time_seconds"])
    return payload


def send_alert_notification(title: str, body: str, facts: list[dict[str, str]]) -> None:
    try:
        send_email(title, body)
    except Exception as exc:
        LOGGER.warning("Email alert delivery failed | title=%s | error=%s", title, exc)

    try:
        send_teams_notification(title, facts)
    except Exception as exc:
        LOGGER.warning("Teams alert delivery failed | title=%s | error=%s", title, exc)


def build_failure_alert_title(error_message: str) -> str:
    if "Data quality validation failed" in error_message:
        return "Automotive Finance Data Quality Failure"
    return "Automotive Finance Pipeline Failure"


def notify_on_pipeline_failure(context: Any) -> None:
    error_message = str(context.get("exception") or "Unknown pipeline failure")
    title = build_failure_alert_title(error_message)
    body = (
        f"{title}\n"
        f"DAG: {context['dag'].dag_id}\n"
        f"Task: {context['task_instance'].task_id}\n"
        f"Execution Date: {context['logical_date']}\n"
        f"Error: {error_message}\n"
    )

    send_alert_notification(
        title,
        body,
        [
            {"title": "DAG", "value": context["dag"].dag_id},
            {"title": "Task", "value": context["task_instance"].task_id},
            {"title": "Execution", "value": str(context["logical_date"])},
            {"title": "Error", "value": error_message[:300]},
        ],
    )

    persist_pipeline_metrics(context, "FAILED")


def notify_on_sla_breach(context: Any, payload: dict[str, Any]) -> None:
    if payload["processing_time_seconds"] <= PIPELINE_SLA_THRESHOLD_SECONDS:
        return

    title = "Automotive Finance Performance Degradation Alert"
    body = (
        f"{title}\n"
        f"DAG: {payload['dag_id']}\n"
        f"Run Timestamp: {payload['run_timestamp']}\n"
        f"Processing Time: {payload['processing_time_seconds']} seconds\n"
        f"SLA Threshold: {PIPELINE_SLA_THRESHOLD_SECONDS} seconds\n"
    )

    send_alert_notification(
        title,
        body,
        [
            {"title": "DAG", "value": payload["dag_id"]},
            {"title": "Files", "value": str(payload["files_processed"])},
            {"title": "Rows Loaded", "value": str(payload["rows_loaded"])},
            {"title": "Processing Time", "value": f"{payload['processing_time_seconds']} seconds"},
            {"title": "SLA", "value": f"{PIPELINE_SLA_THRESHOLD_SECONDS} seconds"},
        ],
    )


def list_bucket_files(bucket_name: str) -> list[str]:
    s3_client = get_s3_client()
    paginator = s3_client.get_paginator("list_objects_v2")
    files: list[str] = []

    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not key.endswith("/"):
                files.append(key)

    return files


def build_warehouse_conn() -> str | None:
    explicit = get_env_value("WAREHOUSE_CONN", "AIRFLOW_VAR_WAREHOUSE_CONN")
    if explicit:
        return explicit

    database_url = get_env_value("DATABASE_URL_EXTERNAL", "AIRFLOW_VAR_DATABASE_URL_EXTERNAL")
    if database_url:
        parsed = urlparse(database_url)
        if parsed.hostname and parsed.path:
            port = parsed.port or 5432
            db_name = parsed.path.lstrip("/")
            user = parsed.username or ""
            password = parsed.password or ""
            return (
                f"dbname={db_name} user={user} password={password} "
                f"host={parsed.hostname} port={port}"
            )

    db_name = get_env_value("DB_NAME", "AIRFLOW_VAR_DB_NAME")
    db_user = get_env_value("DB_USER", "AIRFLOW_VAR_DB_USER")
    db_password = get_env_value("DB_PASSWORD", "AIRFLOW_VAR_DB_PASSWORD")
    db_host = get_env_value(
        "DB_HOST_EXTERNAL",
        "DB_HOST",
        "AIRFLOW_VAR_DB_HOST_EXTERNAL",
        "AIRFLOW_VAR_DB_HOST",
    )
    db_port = get_env_value("DB_PORT", "AIRFLOW_VAR_DB_PORT", default="5432")

    if all([db_name, db_user, db_password, db_host]):
        return (
            f"dbname={db_name} user={db_user} password={db_password} "
            f"host={db_host} port={db_port}"
        )

    return None


def build_runtime_env() -> dict[str, str]:
    env = os.environ.copy()
    env["AIRFLOW_HOME"] = AIRFLOW_HOME
    env["AWS_REGION"] = AWS_REGION or "us-east-1"
    env["AWS_DEFAULT_REGION"] = AWS_REGION or "us-east-1"
    env["S3_RAW_BUCKET"] = S3_RAW_BUCKET or ""
    env["S3_STAGING_BUCKET"] = S3_STAGING_BUCKET or ""
    env["S3_ARCHIVE_BUCKET"] = S3_ARCHIVE_BUCKET or ""
    env["RAW_BUCKET"] = S3_RAW_BUCKET or ""
    env["STAGING_BUCKET"] = S3_STAGING_BUCKET or ""
    env["ARCHIVE_BUCKET"] = S3_ARCHIVE_BUCKET or ""

    if AWS_ACCESS_KEY:
        env["AWS_ACCESS_KEY_ID"] = AWS_ACCESS_KEY
    if AWS_SECRET_KEY:
        env["AWS_SECRET_ACCESS_KEY"] = AWS_SECRET_KEY

    if SMTP_HOST:
        env["SMTP_HOST"] = SMTP_HOST
    env["SMTP_PORT"] = str(SMTP_PORT)
    if SMTP_USER:
        env["SMTP_USER"] = SMTP_USER
        env["SMTP_USERNAME"] = SMTP_USER
    if SMTP_PASSWORD:
        env["SMTP_PASSWORD"] = SMTP_PASSWORD
    if SMTP_FROM:
        env["SMTP_MAIL_FROM"] = SMTP_FROM
        env["SMTP_FROM"] = SMTP_FROM
    if SMTP_TO:
        env["SMTP_TO"] = SMTP_TO
        env["EMAIL_RECIPIENT"] = SMTP_TO
    if TEAMS_WEBHOOK_URL:
        env["TEAMS_WEBHOOK_URL"] = TEAMS_WEBHOOK_URL

    warehouse_conn = build_warehouse_conn()
    if warehouse_conn:
        env["WAREHOUSE_CONN"] = warehouse_conn

    return env


def run_python_script(script_path: str, task_name: str, extra_env: dict[str, str] | None = None) -> dict[str, Any]:
    if not Path(script_path).exists():
        raise AirflowException(f"{task_name} script not found: {script_path}")

    env = build_runtime_env()
    if extra_env:
        env.update(extra_env)

    started_at = perf_counter()

    completed = run(
        [sys.executable, script_path],
        cwd=str(Path(script_path).parent),
        capture_output=True,
        text=True,
        env=env,
        timeout=1800,
        check=False,
    )

    if completed.stdout:
        print(completed.stdout)
    if completed.stderr:
        print(completed.stderr)

    script_summary = extract_script_summary(completed.stdout)
    duration_seconds = round(perf_counter() - started_at, 2)

    if completed.returncode != 0:
        raise AirflowException(f"{task_name} failed with exit code {completed.returncode}")

    return {
        "returncode": completed.returncode,
        "duration_seconds": duration_seconds,
        "stdout": completed.stdout[-4000:],
        "stderr": completed.stderr[-4000:],
        "summary": script_summary,
    }


def monitor_raw_bucket(**context: Any) -> dict[str, Any]:
    raw_files = list_bucket_files(S3_RAW_BUCKET)
    context["task_instance"].xcom_push(key="raw_files", value=raw_files)
    LOGGER.info("Raw bucket scan complete | file_count=%s", len(raw_files))
    return {"file_count": len(raw_files), "files": raw_files}


def run_phase_3_shell_ingestion(**context: Any) -> dict[str, Any]:
    raw_files = context["task_instance"].xcom_pull(task_ids="monitor_raw_bucket", key="raw_files") or []
    if not raw_files:
        context["task_instance"].xcom_push(key="staging_keys_for_run", value=[])
        LOGGER.info("Phase 3 ingestion skipped because no raw files were found")
        return {"status": "skipped_no_files", "processed_files": 0, "staging_keys": []}

    script_result = run_python_script(PHASE_3_SCRIPT, "Phase 3 shell ingestion")

    staging_keys = [f"ingested/{Path(key).name}" for key in raw_files]
    context["task_instance"].xcom_push(key="staging_keys_for_run", value=staging_keys)
    return {
        "status": "success",
        "processed_files": len(raw_files),
        "staging_keys": staging_keys,
        "script_result": script_result,
    }


def run_phase_4_etl(**context: Any) -> dict[str, Any]:
    staging_keys = context["task_instance"].xcom_pull(
        task_ids="run_phase_3_shell_ingestion",
        key="staging_keys_for_run",
    ) or []

    if not staging_keys:
        LOGGER.info("Phase 4 ETL skipped because there were no staged files for the current run")
        return {"status": "skipped_no_files", "file_count": 0}

    script_result = run_python_script(
        PHASE_4_SCRIPT,
        "Phase 4 ETL",
        extra_env={
            "STAGING_BUCKET": S3_STAGING_BUCKET or "",
            "CURRENT_RUN_STAGING_KEYS": json.dumps(staging_keys),
        },
    )
    summary = script_result.get("summary") or {}
    return {
        "status": "success",
        "file_count": len(staging_keys),
        "rows_loaded": summary.get("rows_loaded", 0),
        "script_result": script_result,
        "summary": summary,
    }


def archive_processed_staging_files(**context: Any) -> dict[str, Any]:
    staging_keys = context["task_instance"].xcom_pull(
        task_ids="run_phase_3_shell_ingestion",
        key="staging_keys_for_run",
    ) or []

    if not staging_keys:
        LOGGER.info("No staged files to archive for the current run")
        return {"archived_count": 0, "archived_files": []}

    s3_client = get_s3_client()
    archived_files: list[str] = []
    archive_prefix = datetime.now(timezone.utc).strftime("archive/%Y/%m/%d")

    for staging_key in staging_keys:
        try:
            s3_client.head_object(Bucket=S3_STAGING_BUCKET, Key=staging_key)
        except Exception:
            print(f"Skipping archive for missing staging object: {staging_key}")
            continue

        archive_key = f"{archive_prefix}/{Path(staging_key).name}"
        s3_client.copy_object(
            CopySource={"Bucket": S3_STAGING_BUCKET, "Key": staging_key},
            Bucket=S3_ARCHIVE_BUCKET,
            Key=archive_key,
        )
        s3_client.delete_object(Bucket=S3_STAGING_BUCKET, Key=staging_key)
        archived_files.append(archive_key)
        LOGGER.info("Archived staged object | source=%s | destination=%s", staging_key, archive_key)

    return {"archived_count": len(archived_files), "archived_files": archived_files}


def send_email(subject: str, body: str) -> None:
    if not SMTP_USER or not SMTP_PASSWORD:
        print("Email notification skipped: SMTP credentials not configured.")
        return

    message = MIMEMultipart()
    message["From"] = SMTP_FROM or SMTP_USER
    message["To"] = SMTP_TO or ""
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(message)

    print(f"Phase 5 email notification sent to {SMTP_TO}.")


def send_teams_notification(title: str, facts: list[dict[str, str]]) -> None:
    if not TEAMS_WEBHOOK_URL:
        print("Teams notification skipped: webhook not configured.")
        return

    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": [
                        {"type": "TextBlock", "text": title, "weight": "Bolder", "size": "Large"},
                        {
                            "type": "FactSet",
                            "facts": facts,
                        },
                    ],
                },
            }
        ],
    }

    request = Request(
        TEAMS_WEBHOOK_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=15) as response:
        if not 200 <= response.status < 300:
            raise AirflowException(f"Teams notification failed with status {response.status}")

    print("Phase 5 Teams notification sent.")


def send_phase_5_airflow_notification(**context: Any) -> dict[str, Any]:
    raw_files = context["task_instance"].xcom_pull(task_ids="monitor_raw_bucket", key="raw_files") or []
    phase_3_result = context["task_instance"].xcom_pull(task_ids="run_phase_3_shell_ingestion") or {}
    phase_4_result = context["task_instance"].xcom_pull(task_ids="run_phase_4_etl") or {}
    archive_result = context["task_instance"].xcom_pull(task_ids="archive_processed_staging_files") or {}
    dag_duration_seconds = compute_dag_processing_time_seconds(context)

    execution_date = context["logical_date"]
    dag_id = context["dag"].dag_id

    email_body = (
        "Automotive Finance Orchestration Complete\n"
        "======================================\n\n"
        f"Execution Date: {execution_date}\n"
        f"DAG: {dag_id}\n\n"
        f"Raw files detected: {len(raw_files)}\n"
        f"Phase 3 status: {phase_3_result.get('status', 'unknown')}\n"
        f"Phase 4 status: {phase_4_result.get('status', 'unknown')}\n"
        f"Archived files: {archive_result.get('archived_count', 0)}\n\n"
        f"Processing time (seconds): {dag_duration_seconds}\n\n"
        "Flow executed:\n"
        "1. Airflow monitored the S3 raw bucket\n"
        "2. Phase 3 shell ingestion moved data from raw to staging\n"
        "3. Phase 3 notifications were handled by the shell ingestion step\n"
        "4. Phase 4 ETL processed files from staging\n"
        "5. Airflow archived the processed staging files\n"
        "6. Phase 5 Airflow notification sent\n"
    )

    send_email("Automotive Finance Orchestration Complete", email_body)
    send_teams_notification(
        "Automotive Finance Orchestration Complete",
        [
            {"title": "Execution", "value": str(execution_date)},
            {"title": "Raw files", "value": str(len(raw_files))},
            {"title": "Phase 3", "value": str(phase_3_result.get("status", "unknown"))},
            {"title": "Phase 4", "value": str(phase_4_result.get("status", "unknown"))},
            {"title": "Archived", "value": str(archive_result.get("archived_count", 0))},
            {"title": "Duration", "value": f"{dag_duration_seconds} seconds"},
        ],
    )

    metrics_payload = persist_pipeline_metrics(context, "SUCCESS")
    notify_on_sla_breach(context, metrics_payload)

    return {
        "status": "success",
        "summary": {
            "raw_files": len(raw_files),
            "phase_3": phase_3_result.get("status", "unknown"),
            "phase_4": phase_4_result.get("status", "unknown"),
            "archived_count": archive_result.get("archived_count", 0),
            "processing_time_seconds": dag_duration_seconds,
        },
    }


default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email": [SMTP_TO] if SMTP_TO else [],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": notify_on_pipeline_failure,
}


with DAG(
    dag_id="automotive_finance_orchestration",
    default_args=default_args,
    description="Monitor S3 raw data, run shell ingestion, ETL, archive, and notify from one DAG.",
    schedule="*/5 * * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(minutes=30),
    tags=["automotive", "finance", "orchestration"],
) as dag:
    monitor_raw = PythonOperator(
        task_id="monitor_raw_bucket",
        python_callable=monitor_raw_bucket,
    )

    phase_3_shell_ingestion = PythonOperator(
        task_id="run_phase_3_shell_ingestion",
        python_callable=run_phase_3_shell_ingestion,
    )

    phase_4_etl = PythonOperator(
        task_id="run_phase_4_etl",
        python_callable=run_phase_4_etl,
    )

    archive_processed = PythonOperator(
        task_id="archive_processed_staging_files",
        python_callable=archive_processed_staging_files,
    )

    phase_5_notification = PythonOperator(
        task_id="send_phase_5_airflow_notification",
        python_callable=send_phase_5_airflow_notification,
    )

    monitor_raw >> phase_3_shell_ingestion >> phase_4_etl >> archive_processed >> phase_5_notification