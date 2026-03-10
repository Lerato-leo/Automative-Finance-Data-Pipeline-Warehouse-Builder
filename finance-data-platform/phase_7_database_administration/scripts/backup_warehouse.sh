#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PHASE7_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${PHASE7_DIR}/../.." && pwd)"
ENV_FILE="${REPO_ROOT}/.env"
BACKUP_DIR="${PHASE7_DIR}/backups"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="${BACKUP_DIR}/warehouse_backup_${TIMESTAMP}.sql.gz"
TEMP_BACKUP_FILE="${BACKUP_FILE}.tmp"

resolve_pg_dump() {
  local candidate

  if candidate="$(command -v pg_dump 2>/dev/null)" && [[ -n "${candidate}" ]]; then
    printf '%s\n' "${candidate}"
    return 0
  fi

  if [[ -n "${PROGRAMFILES:-}" ]]; then
    while IFS= read -r candidate; do
      if [[ -n "${candidate}" ]]; then
        printf '%s\n' "${candidate}"
        return 0
      fi
    done < <(compgen -G "${PROGRAMFILES//\\//}/PostgreSQL/*/bin/pg_dump.exe" | sort -Vr)
  fi

  return 1
}

if [[ -f "${ENV_FILE}" ]]; then
  set -a
  source "${ENV_FILE}"
  set +a
fi

DB_HOST_VALUE="${DB_HOST_EXTERNAL:-${DB_HOST:-}}"
DB_PORT_VALUE="${DB_PORT:-5432}"
DB_NAME_VALUE="${DB_NAME:-}"
DB_USER_VALUE="${DB_USER:-}"
DB_PASSWORD_VALUE="${DB_PASSWORD:-}"
ARCHIVE_BUCKET_VALUE="${ARCHIVE_BUCKET:-}"

if ! PG_DUMP_CMD="$(resolve_pg_dump)"; then
  echo "pg_dump was not found on PATH or under the standard PostgreSQL installation directory." >&2
  exit 1
fi

if [[ -z "${DB_HOST_VALUE}" || -z "${DB_NAME_VALUE}" || -z "${DB_USER_VALUE}" || -z "${DB_PASSWORD_VALUE}" ]]; then
  echo "Missing database settings in ${ENV_FILE}. Expected DB_HOST or DB_HOST_EXTERNAL, DB_NAME, DB_USER, and DB_PASSWORD." >&2
  exit 1
fi

mkdir -p "${BACKUP_DIR}"
rm -f "${TEMP_BACKUP_FILE}"

export PGPASSWORD="${DB_PASSWORD_VALUE}"

"${PG_DUMP_CMD}" \
  --host "${DB_HOST_VALUE}" \
  --port "${DB_PORT_VALUE}" \
  --username "${DB_USER_VALUE}" \
  --dbname "${DB_NAME_VALUE}" \
  --no-owner \
  --no-privileges \
  --format=plain | gzip > "${TEMP_BACKUP_FILE}"

mv "${TEMP_BACKUP_FILE}" "${BACKUP_FILE}"

echo "Backup created: ${BACKUP_FILE}"

if command -v aws >/dev/null 2>&1 && [[ -n "${ARCHIVE_BUCKET_VALUE}" ]]; then
  S3_TARGET="s3://${ARCHIVE_BUCKET_VALUE}/backups/$(basename "${BACKUP_FILE}")"
  aws s3 cp "${BACKUP_FILE}" "${S3_TARGET}"
  echo "Backup uploaded: ${S3_TARGET}"
else
  echo "S3 upload skipped. Either AWS CLI is unavailable or ARCHIVE_BUCKET is not set."
fi

unset PGPASSWORD
