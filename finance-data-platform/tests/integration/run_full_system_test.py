#!/usr/bin/env python3
"""Repo integration smoke test for the automotive finance platform."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
DAG_ID = "automotive_finance_orchestration"


def resolve_compose_command() -> list[str]:
    if shutil.which("docker"):
        result = subprocess.run(
            ["docker", "compose", "version"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return ["docker", "compose"]
    if shutil.which("docker-compose"):
        return ["docker-compose"]
    raise RuntimeError("Neither 'docker compose' nor 'docker-compose' is available.")


def run_command(command: list[str], description: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    print(f"[check] {description}")
    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip())
    if check and result.returncode != 0:
        raise RuntimeError(f"{description} failed with exit code {result.returncode}")
    return result


def main() -> int:
    compose = resolve_compose_command()

    if not (ROOT / "docker-compose.yml").exists():
        raise RuntimeError("docker-compose.yml not found at repository root.")

    if not ((ROOT / ".env").exists() or (ROOT / ".env.example").exists()):
        raise RuntimeError("Neither .env nor .env.example exists at repository root.")

    print("Running integration smoke test")
    print(f"Repository root: {ROOT}")

    run_command(compose + ["-f", "docker-compose.yml", "config", "--quiet"], "Validate Docker Compose config")
    run_command(compose + ["-f", "docker-compose.yml", "ps"], "Inspect service status", check=False)

    dags_result = run_command(
        ["docker", "exec", "airflow-webserver", "airflow", "dags", "list"],
        "List Airflow DAGs",
        check=False,
    )

    if dags_result.returncode != 0:
        print("Airflow webserver is not reachable yet. Start the stack before rerunning this test.")
        return 1

    if DAG_ID not in dags_result.stdout:
        raise RuntimeError(f"Expected DAG '{DAG_ID}' was not found in Airflow.")

    run_command(
        ["docker", "exec", "airflow-webserver", "airflow", "tasks", "list", DAG_ID],
        f"List tasks for DAG {DAG_ID}",
    )

    print("Smoke test passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Smoke test failed: {exc}")
        raise SystemExit(1)