import argparse
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

import psycopg2


ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"


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


def get_connection():
    host = os.getenv("DB_HOST_EXTERNAL") or os.getenv("DB_HOST")
    return psycopg2.connect(
        host=host,
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def persist_alert(alert_type: str, severity: str, message: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO monitoring.alert_events (alert_type, severity, alert_message)
                VALUES (%s, %s, %s)
                """,
                (alert_type, severity, message),
            )


def send_email(subject: str, body: str) -> None:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    to_email = os.getenv("SMTP_FROM_EMAIL")

    if not all([smtp_host, smtp_user, smtp_password, to_email]):
        print("Email settings not fully configured; skipping email notification")
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = smtp_user
    message["To"] = to_email
    message.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(smtp_user, smtp_password)
        smtp.send_message(message)


def check_pipeline_failure_rate(threshold: float) -> list[str]:
    sql = """
        SELECT dag_id, run_date, success_rate
        FROM monitoring.v_pipeline_success_failure
        WHERE run_date >= CURRENT_DATE - INTERVAL '1 day'
          AND success_rate < %s
    """

    alerts = []
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, (threshold,))
            for dag_id, run_date, success_rate in cursor.fetchall():
                alerts.append(
                    f"Pipeline failure alert: {dag_id} success_rate={success_rate}% on {run_date} (threshold={threshold}%)"
                )

    return alerts


def check_data_quality_issues() -> list[str]:
    sql = """
        SELECT table_name, metric_name, metric_value, metric_threshold
        FROM monitoring.data_quality_metrics
        WHERE captured_at >= NOW() - INTERVAL '1 day'
          AND metric_status = 'FAIL'
    """

    alerts = []
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            for table_name, metric_name, metric_value, metric_threshold in cursor.fetchall():
                alerts.append(
                    f"Data quality alert: {table_name} {metric_name}={metric_value}% exceeded threshold {metric_threshold}%"
                )

    return alerts


def check_performance_degradation(p95_threshold_seconds: float) -> list[str]:
    sql = """
        SELECT dag_id, run_date, p95_duration_seconds
        FROM monitoring.v_processing_time_trends
        WHERE run_date >= CURRENT_DATE - INTERVAL '1 day'
          AND p95_duration_seconds > %s
    """

    alerts = []
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, (p95_threshold_seconds,))
            for dag_id, run_date, p95_duration_seconds in cursor.fetchall():
                alerts.append(
                    f"Performance alert: {dag_id} p95_duration={p95_duration_seconds}s on {run_date} exceeded threshold={p95_threshold_seconds}s"
                )

    return alerts


def run_alerts(failure_rate_threshold: float, p95_threshold_seconds: float) -> None:
    pipeline_alerts = check_pipeline_failure_rate(failure_rate_threshold)
    quality_alerts = check_data_quality_issues()
    performance_alerts = check_performance_degradation(p95_threshold_seconds)

    all_alerts = pipeline_alerts + quality_alerts + performance_alerts

    if not all_alerts:
        print("No alerts triggered")
        return

    for message in all_alerts:
        severity = "CRITICAL" if "failure" in message.lower() else "WARNING"
        alert_type = (
            "pipeline_failure" if "Pipeline" in message else "data_quality" if "Data quality" in message else "performance"
        )
        persist_alert(alert_type, severity, message)
        send_email(subject=f"[Auto Finance Pipeline] {alert_type}", body=message)
        print(message)


def parse_args():
    parser = argparse.ArgumentParser(description="Phase 8 - Alert manager")
    parser.add_argument("action", choices=["run-alerts"])
    parser.add_argument("--failure-rate-threshold", type=float, default=95.0)
    parser.add_argument("--p95-threshold-seconds", type=float, default=300.0)
    return parser.parse_args()


def main():
    load_env(ROOT_ENV)
    args = parse_args()

    if args.action == "run-alerts":
        run_alerts(args.failure_rate_threshold, args.p95_threshold_seconds)


if __name__ == "__main__":
    main()
