#!/usr/bin/env bash
set -euo pipefail

# Start script used by Docker/Render/Railway
# Uses Gunicorn with Uvicorn worker for production

# POSIX-style defaulting so behavior is predictable across shells/platforms
PORT=${PORT:-8000}
WEB_CONCURRENCY=${WEB_CONCURRENCY:-1}

echo "Starting app with Gunicorn (workers=${WEB_CONCURRENCY}) on port ${PORT}"

exec gunicorn -k uvicorn.workers.UvicornWorker \
  app.main:app \
  --bind 0.0.0.0:${PORT} \
  --workers "${WEB_CONCURRENCY}" \
  --timeout 120 \
  --log-level info
