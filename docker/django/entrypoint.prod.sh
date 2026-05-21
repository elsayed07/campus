#!/usr/bin/env bash
set -euo pipefail

python - <<'PY'
import os, socket, time
host = os.environ.get("DB_HOST", "postgres")
port = int(os.environ.get("DB_PORT", "5432"))
deadline = time.time() + 60
while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=2):
            break
    except OSError:
        time.sleep(1)
else:
    raise SystemExit(f"Database at {host}:{port} not reachable in time")
PY

uv run python manage.py migrate --noinput
uv run python manage.py collectstatic --noinput

exec "$@"
