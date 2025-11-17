#!/bin/bash
set -e

echo "Running database migrations..."
uv run python manage.py migrate --no-input

echo "Starting gunicorn..."
exec uv run gunicorn scavenger_hunt.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
