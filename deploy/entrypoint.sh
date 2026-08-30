#!/bin/sh
# Container entrypoint for web, worker and beat.
#
# Compose already gates these services on the db healthcheck, but a plain
# `docker run` and the production stack do not, and django dies on a closed
# socket instead of retrying. So block here until postgres answers.
set -e

python - "$@" <<'PY'
import os
import sys
import time

import psycopg

dsn = os.environ.get("DATABASE_URL")
if not dsn:
    print("entrypoint: DATABASE_URL is not set, skipping the database wait")
    sys.exit(0)

deadline = time.monotonic() + float(os.environ.get("DB_WAIT_TIMEOUT", "60"))
while True:
    try:
        with psycopg.connect(dsn, connect_timeout=3):
            print("entrypoint: database is up")
            break
    except psycopg.OperationalError as exc:
        if time.monotonic() >= deadline:
            print(f"entrypoint: database still unreachable, giving up: {exc}")
            sys.exit(1)
        print("entrypoint: waiting for the database")
        time.sleep(1)
PY

# Compile the message catalogues when a .po is newer than its .mo. Dev keeps
# only the .po under version control, so without this a fresh checkout serves
# polish to a reader who asked for russian. Production ships the .mo already
# built and has no msgfmt, hence the guard rather than an unconditional call.
if command -v msgfmt >/dev/null 2>&1; then
  find locale -name '*.po' 2>/dev/null | while read -r po; do
    mo="${po%.po}.mo"
    if [ ! -f "$mo" ] || [ "$po" -nt "$mo" ]; then
      msgfmt -o "$mo" "$po" && echo "entrypoint: compiled $po"
    fi
  done
fi

exec "$@"
