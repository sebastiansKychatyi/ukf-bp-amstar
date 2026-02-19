#!/bin/bash

set -euo pipefail

echo "==> AmStar Backend: starting up"


DB_HOST=$(echo "${DATABASE_URL:-}" | sed -n 's|.*@\(.*\):\([0-9]*\)/.*|\1|p')
DB_PORT=$(echo "${DATABASE_URL:-}" | sed -n 's|.*@\(.*\):\([0-9]*\)/.*|\2|p')

# Фоллбэк если URL не распарсился (например, нестандартный формат)
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"

echo "==> Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."


MAX_RETRIES="${DB_WAIT_RETRIES:-30}"   
RETRY_SLEEP=2
RETRY_COUNT=0

until pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${POSTGRES_USER:-postgres}" -q; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ "${RETRY_COUNT}" -ge "${MAX_RETRIES}" ]; then
        echo "ERROR: PostgreSQL at ${DB_HOST}:${DB_PORT} is not ready after" \
             "$((MAX_RETRIES * RETRY_SLEEP))s. Aborting."
        exit 1
    fi
    echo "    PostgreSQL not ready yet (attempt ${RETRY_COUNT}/${MAX_RETRIES})," \
         "retrying in ${RETRY_SLEEP}s..."
    sleep "${RETRY_SLEEP}"
done

echo "==> PostgreSQL is ready"


echo "==> Running Alembic migrations..."
alembic upgrade head
echo "==> Migrations complete"


EXTRA_ARGS=()

if [ "${RELOAD:-false}" = "true" ]; then
    EXTRA_ARGS+=("--reload")
    echo "==> Hot-reload enabled (development mode)"
fi


if [ "${RELOAD:-false}" != "true" ] && [ -n "${UVICORN_WORKERS:-}" ]; then
    EXTRA_ARGS+=("--workers" "${UVICORN_WORKERS}")
    echo "==> Starting with ${UVICORN_WORKERS} workers"
fi

echo "==> Starting uvicorn..."


exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info \
    "${EXTRA_ARGS[@]}"
