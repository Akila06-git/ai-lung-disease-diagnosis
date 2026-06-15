#!/bin/bash
set -e

# Only run migrations from the backend service (not celery/flower)
if echo "$@" | grep -q "gunicorn"; then
    echo "Running database migrations..."
    python manage.py migrate --noinput
fi

echo "Starting application..."
exec "$@"
