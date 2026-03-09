#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

echo "Automotive Finance Data Platform - Docker Startup"
echo "================================================="
echo

if ! command -v docker >/dev/null 2>&1; then
    echo "Docker not found. Install Docker first."
    exit 1
fi

if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(docker-compose)
else
    echo "Neither 'docker compose' nor 'docker-compose' is available."
    exit 1
fi

if [ ! -f "${REPO_ROOT}/.env" ]; then
    echo ".env file not found in ${REPO_ROOT}"
    if [ -f "${REPO_ROOT}/.env.example" ]; then
        echo "Creating .env from .env.example..."
        cp "${REPO_ROOT}/.env.example" "${REPO_ROOT}/.env"
        echo "Created .env. Update it with real credentials before running the pipeline."
    else
        echo ".env.example not found in ${REPO_ROOT}"
        exit 1
    fi
fi

echo "Starting Docker services from ${REPO_ROOT}"
cd "${REPO_ROOT}"
"${COMPOSE_CMD[@]}" -f docker-compose.yml up -d

echo
echo "Waiting for services to initialize..."
sleep 10

echo
echo "Active services:"
"${COMPOSE_CMD[@]}" -f docker-compose.yml ps
echo
echo "Airflow UI: http://localhost:8081"
echo "Next steps:"
echo "  1. Open the Airflow UI."
echo "  2. Enable the automotive_finance_orchestration DAG."
echo "  3. Upload files to the RAW bucket."
echo
echo "Stop services with:"
echo "  ${COMPOSE_CMD[*]} -f docker-compose.yml down"