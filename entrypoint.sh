#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."

while ! python -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect(('${POSTGRES_HOST:-db}', ${POSTGRES_PORT:-5432}))
    s.close()
    exit(0)
except Exception:
    exit(1)
" 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping..."
  sleep 1
done

echo "PostgreSQL is up - running migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

echo "Starting server..."
exec "$@"
