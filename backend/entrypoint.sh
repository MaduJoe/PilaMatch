#!/bin/bash
set -e

echo "Waiting for database..."
while ! pg_isready -h db -p 5432 -U postgres; do
    sleep 1
done

echo "Running database migrations..."
alembic upgrade head

echo "Starting server (APP_ENV=${APP_ENV:-development})..."
if [ "$APP_ENV" = "production" ]; then
    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers ${WORKERS:-4} \
        --loop uvloop \
        --no-access-log
else
    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload
fi
