#!/bin/bash
set -euo pipefail

echo "Starting Django application..."

if [[ "${DATABASE_URL}" == postgres* ]]; then
    echo "Waiting for PostgreSQL..."
    
    for i in {1..30}; do
        if python -c "
import psycopg2
from urllib.parse import urlparse
url = urlparse('$DATABASE_URL')
psycopg2.connect(
    host=url.hostname,
    port=url.port or 5432,
    user=url.username,
    password=url.password,
    database=url.path.lstrip('/')
)
" 2>/dev/null; then
            echo "Database is ready!"
            break
        fi
        echo "   Attempt ${i}/30: database not ready yet, waiting..."
        sleep 2
    done
fi

echo "Running migrations..."
python manage.py migrate --noinput

echo "Django application ready!"

exec "$@"
