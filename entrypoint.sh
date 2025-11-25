#!/bin/bash
set -euo pipefail

echo "Starting the application..."

wait_for_db() {
    echo "Waiting for database at ${DB_HOST}:${DB_PORT}..."

    max_attempts=30
    attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if python -c "
import os
import psycopg2
try:
    conn = psycopg2.connect(
        host=os.getenv('DATABASE_HOST', 'localhost'),
        port=os.getenv('DATABASE_PORT', 5432),
        user=os.getenv('DATABASE_USER', 'postgres'),
        password=os.getenv('DATABASE_PASSWORD', ''),
        database=os.getenv('DATABASE_NAME', 'postgres')
    )
    conn.close()
    print('Database is ready!')
    exit(0)
except Exception as e:
    print(f'Database not ready: {e}')
    exit(1)
        " 2>/dev/null; then
            echo "Database is ready!"
            return 0
        else
            echo "Database not ready yet. Retrying in 2 seconds..."
            attempt=$((attempt + 1))
            sleep 2
        fi
    done

    echo "Database failed to become ready after ${max_attempts} attempts."
}

if [ -n "${DATABASE_URL}" ]; then
    python -c "
from urllib.parse import urlparse
url = urlparse('${DATABASE_URL}')
print(f'HOST={url.hostname}')
print(f'PORT={url.port or 5432}')
print(f'USER={url.username}')
print(f'PASSWORD={url.password}')
print(f'NAME={url.path.lstrip('/')}')
" | while read line; do
        export "DATABASE_${line}"
    done
fi

if [ "${DATABASE_HOST}" != "sqlite" ] && [ -n  "${DATABASE_HOST}" ]; then
    wait_for_db || exit 1
fi

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn server..."

exec "$@"