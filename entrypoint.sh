#!/usr/bin/env bash
set -euo pipefail

# Wait for Postgres to be available
# Use a simple python loop so we don't require extra tools
host="${POSTGRES_HOST:-db}"
port="${POSTGRES_PORT:-5432}"

echo "Waiting for Postgres at ${host}:${port}..."
python - <<PY
import sys, time, socket
host = "${host}"
port = int("${port}")
for i in range(60):
    try:
        s = socket.create_connection((host, port), timeout=2)
        s.close()
        sys.exit(0)
    except Exception:
        time.sleep(1)
print("Timed out waiting for Postgres")
sys.exit(1)
PY

# Run migrations & collectstatic (optional)
echo "Running migrations..."
python manage.py migrate --noinput

# Optional: collect static for production
if [ "${COLLECT_STATIC:-0}" = "1" ]; then
  echo "Collecting static files..."
  python manage.py collectstatic --noinput
fi

# Exec the provided command (gunicorn / celery ...)
exec "$@"
