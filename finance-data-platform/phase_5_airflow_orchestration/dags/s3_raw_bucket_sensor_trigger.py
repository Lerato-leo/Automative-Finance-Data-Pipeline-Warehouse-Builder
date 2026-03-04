# pyright: reportMissingImports=false

"""
Phase 5+6 Integration: S3 Event (via SQS) → Auto-Trigger ETL DAG
Consumes S3 ObjectCreated events from an SQS queue and triggers event_driven_real_time_etl DAG.
This avoids broad RAW bucket polling and gives near real-time, event-driven execution.
"""

from airflow import DAG  # pyright: ignore[reportMissingImports]
from airflow.operators.python import PythonOperator  # pyright: ignore[reportMissingImports]
from airflow.operators.trigger_dagrun import TriggerDagRunOperator  # pyright: ignore[reportMissingImports]
from airflow.providers.amazon.aws.sensors.sqs import SqsSensor  # pyright: ignore[reportMissingImports]
from airflow.utils.dates import days_ago  # pyright: ignore[reportMissingImports]
from datetime import datetime, timedelta
import logging
import os
import json
from urllib.parse import unquote_plus

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'email': ['data-alerts@automativedata.com'],
    'email_on_failure': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=1),
    'execution_timeout': timedelta(minutes=15),
}

dag = DAG(
    's3_raw_bucket_sensor_trigger',
    default_args=default_args,
    description='SQS Sensor: Listens to S3 ObjectCreated events and triggers ETL DAG',
    schedule='@continuous',
    start_date=days_ago(1),
    catchup=False,
    tags=['sensor', 'event-driven', 's3', 'sqs'],
    max_active_runs=1,
)

# ============================================
# TASK 1: VALIDATE CONFIG
# ============================================
def validate_queue_config(**context):
    """
    Ensure required queue config exists before starting sensor.
    """
    queue_url = os.getenv('RAW_S3_EVENTS_QUEUE_URL', '').strip()

    if not queue_url:
        raise ValueError(
            "RAW_S3_EVENTS_QUEUE_URL is not set. Configure S3 Event Notification to SQS and set this env var."
        )

    logger.info(f"✓ Using S3 events queue: {queue_url}")
    return {'queue_url': queue_url}

validate_config = PythonOperator(
    task_id='validate_queue_config',
    python_callable=validate_queue_config,
    provide_context=True,
    dag=dag,
)

# ============================================
# TASK 2: SENSOR - Wait for S3 events from SQS
# ============================================
wait_for_s3_events = SqsSensor(
    task_id='wait_for_s3_events',
    sqs_queue=os.getenv('RAW_S3_EVENTS_QUEUE_URL', ''),
    max_messages=10,
    num_batches=1,
    wait_time_seconds=20,
    visibility_timeout=120,
    delete_message_on_reception=True,
    poke_interval=5,
    timeout=31536000,
    mode='reschedule',
    dag=dag,
)

# ============================================
# TASK 3: PARSE EVENT PAYLOAD
# ============================================
def extract_s3_event_details(**context):
    """
    Parse S3 event messages from SQS and extract keys for downstream ETL processing.
    Handles direct S3 payloads and SNS-wrapped payloads.
    """
    messages = context['task_instance'].xcom_pull(task_ids='wait_for_s3_events') or []

    parsed_records = []
    s3_keys = []

    for message in messages:
        body = message.get('Body') if isinstance(message, dict) else None
        if not body:
            continue

        try:
            payload = json.loads(body)
        except Exception:
            logger.warning("Skipping non-JSON SQS message body")
            continue

        if isinstance(payload, dict) and 'Message' in payload:
            try:
                payload = json.loads(payload['Message'])
            except Exception:
                logger.warning("SNS envelope Message is not valid JSON")

        records = payload.get('Records', []) if isinstance(payload, dict) else []
        for record in records:
            s3_info = record.get('s3', {})
            bucket_name = s3_info.get('bucket', {}).get('name')
            key = s3_info.get('object', {}).get('key')
            if key:
                key = unquote_plus(key)
                s3_keys.append(key)
                parsed_records.append({'bucket': bucket_name, 'key': key})

    unique_keys = sorted(set(s3_keys))

    summary = {
        'event_count': len(parsed_records),
        'file_count': len(unique_keys),
        'files': unique_keys,
        'records': parsed_records,
        'detected_at': datetime.utcnow().isoformat(),
    }

    context['task_instance'].xcom_push(key='event_summary', value=summary)

    logger.info(
        f"✓ Parsed {summary['event_count']} S3 event records for {summary['file_count']} files"
    )

    return summary

extract_event_details = PythonOperator(
    task_id='extract_s3_event_details',
    python_callable=extract_s3_event_details,
    provide_context=True,
    dag=dag,
)

# ============================================
# TASK 4: TRIGGER - Auto-Fire ETL DAG
# ============================================
trigger_etl = TriggerDagRunOperator(
    task_id='trigger_etl_dag',
    trigger_dag_id='event_driven_real_time_etl',
    conf={
        'source': 's3_event_sqs',
        'triggered_at': '{{ ts }}',
        's3_keys': "{{ ti.xcom_pull(task_ids='extract_s3_event_details', key='event_summary')['files'] if ti.xcom_pull(task_ids='extract_s3_event_details', key='event_summary') else [] }}",
    },
    dag=dag,
)

# ============================================
# TASK 5: LOG - Record Event
# ============================================
def log_trigger_event(**context):
    """Log when ETL DAG was triggered"""
    summary = context['task_instance'].xcom_pull(
        task_ids='extract_s3_event_details',
        key='event_summary'
    ) or {}

    file_count = summary.get('file_count', 0)
    files = summary.get('files', [])

    logger.info(f"""
    ✓ ETL DAG Triggered!
    Trigger source: S3 Event Notification via SQS
    Files: {file_count}
    Timestamp: {datetime.now().isoformat()}
    Sample files: {files[:3]}
    """)

log_event = PythonOperator(
    task_id='log_trigger_event',
    python_callable=log_trigger_event,
    provide_context=True,
    dag=dag,
)

# ============================================
# DAG TASK DEPENDENCIES
# ============================================
# Validate config → Wait for S3 event → Extract details → Trigger ETL → Log event
validate_config >> wait_for_s3_events >> extract_event_details >> trigger_etl >> log_event
