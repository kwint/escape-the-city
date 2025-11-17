#!/bin/bash
set -e

echo "Running database migrations..."
uv run python manage.py migrate --no-input

echo "Creating superuser if needed..."
uv run python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    print("No admin user found, you'll need to create one manually")
EOF

echo "Starting gunicorn..."
exec uv run gunicorn scavenger_hunt.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
