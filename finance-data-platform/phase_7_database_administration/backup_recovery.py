import argparse
import gzip
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import psycopg2


ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"
BASE_DIR = Path(__file__).resolve().parent
BACKUP_DIR = BASE_DIR / "backups"


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


def db_config() -> dict:
    host = os.getenv("DB_HOST_EXTERNAL") or os.getenv("DB_HOST")
    return {
        "host": host,
        "port": os.getenv("DB_PORT", "5432"),
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
    }


def get_connection():
    config = db_config()
    if not all([config["host"], config["dbname"], config["user"], config["password"]]):
        raise RuntimeError("Missing DB_* values in root .env")
    return psycopg2.connect(**config)


def pg_dump_cmd() -> str:
    return shutil.which("pg_dump") or shutil.which("pg_dump.exe") or "pg_dump"


def pg_restore_cmd() -> str:
    return shutil.which("pg_restore") or shutil.which("pg_restore.exe") or "pg_restore"


def write_backup_history(backup_file: str, status: str, notes: str = "") -> None:
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("CREATE SCHEMA IF NOT EXISTS admin")
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS admin.backup_history (
                        id BIGSERIAL PRIMARY KEY,
                        executed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        backup_file TEXT NOT NULL,
                        backup_size_bytes BIGINT,
                        backup_status TEXT NOT NULL,
                        notes TEXT
                    )
                    """
                )
                file_path = Path(backup_file)
                size = file_path.stat().st_size if file_path.exists() else 0
                cursor.execute(
                    """
                    INSERT INTO admin.backup_history (backup_file, backup_size_bytes, backup_status, notes)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (backup_file, size, status, notes),
                )
    except Exception as exc:
        print(f"Warning: failed to write admin.backup_history: {exc}")


def run_daily_backup(retention_days: int = 14) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    cfg = db_config()

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"warehouse_backup_{timestamp}.dump"

    command = [
        pg_dump_cmd(),
        "-h", cfg["host"],
        "-p", cfg["port"],
        "-U", cfg["user"],
        "-d", cfg["dbname"],
        "-F", "c",
        "-f", str(backup_path),
        "-Z", "6",
    ]

    env = os.environ.copy()
    env["PGPASSWORD"] = cfg["password"]

    try:
        subprocess.run(command, env=env, check=True, capture_output=True, text=True)
        write_backup_history(str(backup_path), "SUCCESS", "Daily backup completed")
        print(f"Backup completed: {backup_path}")
    except subprocess.CalledProcessError as exc:
        write_backup_history(str(backup_path), "FAILED", exc.stderr[:4000])
        raise RuntimeError(f"Backup failed: {exc.stderr}") from exc

    prune_old_backups(retention_days)
    return backup_path


def prune_old_backups(retention_days: int) -> None:
    cutoff = datetime.utcnow().timestamp() - (retention_days * 86400)
    deleted = 0
    for backup_file in BACKUP_DIR.glob("warehouse_backup_*.dump"):
        if backup_file.stat().st_mtime < cutoff:
            backup_file.unlink(missing_ok=True)
            deleted += 1
    print(f"Retention cleanup done: removed {deleted} backup file(s)")


def test_restore_procedure(backup_file: Path) -> None:
    if not backup_file.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_file}")

    command = [pg_restore_cmd(), "--list", str(backup_file)]
    result = subprocess.run(command, check=True, capture_output=True, text=True)

    preview_path = backup_file.with_suffix(".restore_preview.txt.gz")
    with gzip.open(preview_path, "wt", encoding="utf-8") as gz_file:
        gz_file.write(result.stdout)

    print(f"Restore test passed. Restore listing saved to: {preview_path}")


def pitr_readiness_check() -> None:
    checks = {
        "wal_level": "SHOW wal_level",
        "archive_mode": "SHOW archive_mode",
        "archive_command": "SHOW archive_command",
        "max_wal_senders": "SHOW max_wal_senders",
    }

    with get_connection() as conn:
        with conn.cursor() as cursor:
            print("PITR configuration snapshot:")
            for label, query in checks.items():
                try:
                    cursor.execute(query)
                    value = cursor.fetchone()[0]
                except Exception:
                    value = "Not accessible on managed PostgreSQL"
                print(f"- {label}: {value}")


def print_scheduler_instructions(script_path: Path) -> None:
    command = f"python \"{script_path}\" backup --retention-days 14"
    print("\nDaily backup scheduler command (Windows Task Scheduler):")
    print(command)


def parse_args():
    parser = argparse.ArgumentParser(description="Phase 7 - Backup and recovery toolkit")
    parser.add_argument("action", choices=["backup", "restore-test", "pitr-check", "scheduler-help"])
    parser.add_argument("--retention-days", type=int, default=14)
    parser.add_argument("--backup-file", type=str, default="")
    return parser.parse_args()


def main():
    load_env(ROOT_ENV)
    args = parse_args()

    if args.action == "backup":
        run_daily_backup(retention_days=args.retention_days)
    elif args.action == "restore-test":
        if args.backup_file:
            target = Path(args.backup_file)
        else:
            candidates = sorted(BACKUP_DIR.glob("warehouse_backup_*.dump"), reverse=True)
            if not candidates:
                raise RuntimeError("No backup files found. Run backup first.")
            target = candidates[0]
        test_restore_procedure(target)
    elif args.action == "pitr-check":
        pitr_readiness_check()
    elif args.action == "scheduler-help":
        print_scheduler_instructions(Path(__file__).resolve())


if __name__ == "__main__":
    main()
