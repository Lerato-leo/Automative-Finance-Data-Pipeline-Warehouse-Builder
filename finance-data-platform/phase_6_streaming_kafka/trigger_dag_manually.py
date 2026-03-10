#!/usr/bin/env python3
"""Trigger the single Airflow orchestration DAG after verifying raw S3 data exists."""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import boto3

AIRFLOW_CONTAINER = 'airflow-webserver'
DEFAULT_DAG_ID = 'automotive_finance_orchestration'
TERMINAL_STATES = {'success', 'failed'}


def load_env_file() -> None:
    env_file = Path('finance-data-platform/phase_6_streaming_kafka/.env')
    if not env_file.exists():
        return

    with open(env_file, encoding='utf-8') as handle:
        for line in handle:
            if line.strip() and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value.strip().strip('"')


def run_airflow_command(command: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    result = subprocess.run(
        ['docker', 'exec', AIRFLOW_CONTAINER, 'airflow', *command],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if result.returncode != 0:
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        raise RuntimeError(f"Airflow command failed: {' '.join(command)}")
    return result


def get_dag_paused_state(dag_id: str) -> bool:
    result = run_airflow_command(['dags', 'list', '--output', 'json'])
    dags = json.loads(result.stdout or '[]')

    for dag in dags:
        if dag.get('dag_id') == dag_id:
            paused_value = dag.get('paused', dag.get('is_paused', 'false'))
            return str(paused_value).lower() == 'true'

    raise RuntimeError(f"Could not find DAG {dag_id} in Airflow")


def set_dag_pause_state(dag_id: str, paused: bool) -> None:
    action = 'pause' if paused else 'unpause'
    result = run_airflow_command(['dags', action, dag_id])
    if result.stdout:
        print(result.stdout.strip())


def trigger_dag(dag_id: str, run_id: str) -> None:
    result = run_airflow_command(['dags', 'trigger', dag_id, '--run-id', run_id])
    if result.stdout:
        print(result.stdout.strip())
    print(f"✅ Triggered {dag_id} with run id {run_id}")


def get_dag_run_state(dag_id: str, run_id: str) -> str | None:
    result = run_airflow_command(['dags', 'list-runs', '-d', dag_id, '--output', 'json'])
    dag_runs = json.loads(result.stdout or '[]')

    for dag_run in dag_runs:
        if dag_run.get('run_id') == run_id:
            state = dag_run.get('state')
            return state.lower() if isinstance(state, str) else state

    return None


def wait_for_terminal_state(dag_id: str, run_id: str, timeout_seconds: int, poll_seconds: int) -> str:
    start_time = time.time()

    while True:
        state = get_dag_run_state(dag_id, run_id)
        elapsed = int(time.time() - start_time)

        if state is not None:
            print(f"   - DAG run state after {elapsed}s: {state}")
            if state in TERMINAL_STATES:
                return state

        if elapsed >= timeout_seconds:
            raise TimeoutError(
                f"Timed out waiting for DAG run {run_id} to finish after {timeout_seconds} seconds"
            )

        time.sleep(poll_seconds)


def list_raw_files(raw_bucket: str) -> list[str]:
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket=raw_bucket)

    if 'Contents' not in response:
        raise RuntimeError('No files found in RAW bucket. Producer/Consumer may not have completed yet.')

    return sorted(obj['Key'] for obj in response['Contents'])


def print_raw_summary(files: list[str]) -> None:
    print(f"✅ Found {len(files)} files in RAW bucket:\n")
    folders: dict[str, list[str]] = {}

    for file_key in files:
        domain = file_key.split('/')[0]
        folders.setdefault(domain, []).append(file_key)

    for domain in sorted(folders):
        print(f"   {domain}/ ({len(folders[domain])} files)")
        for file_key in folders[domain][:2]:
            print(f"      └─ {file_key}")
        if len(folders[domain]) > 2:
            print(f"      └─ ... {len(folders[domain]) - 2} more")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Safely trigger the Airflow orchestration DAG for a streaming verification run.'
    )
    parser.add_argument('--dag-id', default=DEFAULT_DAG_ID, help='Airflow DAG id to trigger')
    parser.add_argument('--raw-bucket', default=os.getenv('RAW_BUCKET', 'automotive-raw-data-lerato-2026'))
    parser.add_argument('--run-id-prefix', default='manual_stream_trigger')
    parser.add_argument(
        '--wait',
        action=argparse.BooleanOptionalAction,
        default=True,
        help='Wait for the DAG run to reach a terminal state before exiting',
    )
    parser.add_argument('--timeout-seconds', type=int, default=900, help='Max wait time for DAG completion')
    parser.add_argument('--poll-seconds', type=int, default=10, help='Polling interval while waiting')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_env_file()

    print("\n" + "=" * 80)
    print("🚀 MANUAL DAG TRIGGER - Automotive Finance Orchestration")
    print("=" * 80 + "\n")

    print("Step 1: Scanning RAW bucket for streamed data...")
    print("-" * 80)
    try:
        raw_files = list_raw_files(args.raw_bucket)
        print_raw_summary(raw_files)
    except Exception as exc:
        print(f"❌ Error checking RAW bucket: {exc}")
        return 1

    print("\n\nStep 2: Preparing Airflow DAG state...")
    print("-" * 80)

    run_id = f"{args.run_id_prefix}_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}"
    original_paused_state = None
    dag_unpaused_by_script = False

    try:
        original_paused_state = get_dag_paused_state(args.dag_id)
        print(f"Current paused state for {args.dag_id}: {original_paused_state}")

        if original_paused_state:
            print("Unpausing DAG for this verification run...")
            set_dag_pause_state(args.dag_id, paused=False)
            dag_unpaused_by_script = True

        print("\nStep 3: Triggering the Airflow orchestration DAG...")
        print("-" * 80)
        trigger_dag(args.dag_id, run_id)

        final_state = None
        if args.wait:
            print("\nStep 4: Waiting for the DAG run to finish before restoring pause state...")
            print("-" * 80)
            final_state = wait_for_terminal_state(
                args.dag_id,
                run_id,
                timeout_seconds=args.timeout_seconds,
                poll_seconds=args.poll_seconds,
            )

        if dag_unpaused_by_script and args.wait:
            print("\nStep 5: Restoring the original paused state...")
            print("-" * 80)
            set_dag_pause_state(args.dag_id, paused=True)

        print("\n\n" + "=" * 80)
        print("📊 SUMMARY")
        print("=" * 80)
        print(f"Triggered DAG: {args.dag_id}")
        print(f"Run ID: {run_id}")
        if args.wait:
            print(f"Final State: {final_state}")
            print("Pause restoration: completed after the run reached a terminal state")
        else:
            print("Final State: not waited")
            print("Pause restoration: skipped to avoid interrupting the active DAG run")
        print("=" * 80 + "\n")

        return 0 if final_state in (None, 'success') else 1

    except TimeoutError as exc:
        print(f"❌ {exc}")
        if dag_unpaused_by_script:
            print(
                "Leaving the DAG unpaused so the active run can finish. "
                "Pause it manually after the DAG reaches a terminal state."
            )
        return 1
    except Exception as exc:
        print(f"❌ Error triggering Airflow DAG: {exc}")
        if dag_unpaused_by_script and original_paused_state:
            print("Restoring the DAG to paused because the trigger flow failed before completion.")
            set_dag_pause_state(args.dag_id, paused=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
