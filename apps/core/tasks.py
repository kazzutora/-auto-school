"""Shared Celery base class and the core background tasks."""

import gzip
import os
import re
import shutil
import subprocess
import tempfile
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from celery import Task, shared_task
from django.conf import settings

from apps.core.contracts import validate_payload


class BaseTask(Task):
    """Retry policy every task in the project inherits, tech.md section 6.

    Celery reads these off the task instance in add_autoretry_behaviour, so a
    slice only has to pass base=BaseTask instead of repeating the options.
    """

    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 600
    max_retries = 5
    acks_late = True


@shared_task(bind=True, base=BaseTask)
def ping(self: Task) -> str:
    """Prove the broker, the worker and the result backend are wired up."""
    return "pong"


BACKUP_NAME = re.compile(r"^osk-(\d{8})\.sql\.gz$")


def _backup_name(day: date) -> str:
    return f"osk-{day:%Y%m%d}.sql.gz"


def _rotate(directory: Path, keep_days: int, today: date) -> list[str]:
    """Drop dumps older than the retention window, tech.md section 19."""
    cutoff = today - timedelta(days=keep_days)
    removed = []
    for path in sorted(directory.glob("osk-*.sql.gz")):
        match = BACKUP_NAME.match(path.name)
        if not match:
            continue
        taken = date(int(match[1][:4]), int(match[1][4:6]), int(match[1][6:]))
        if taken < cutoff:
            path.unlink()
            removed.append(path.name)
    return removed


@shared_task(bind=True, base=BaseTask)
def db_backup(self: Task) -> dict[str, Any]:
    """pg_dump into the backup directory, tech.md sections 6 and 19.

    Idempotent on the dated filename: a second run on the same day finds the
    dump already there and does nothing. The dump is written to a .part file and
    renamed only once pg_dump succeeds, so a crash cannot leave a truncated file
    that the next run would mistake for a finished backup.
    """
    validate_payload("core.tasks.db_backup", {})

    directory = Path(settings.BACKUP_DIR)
    directory.mkdir(parents=True, exist_ok=True)

    today = date.today()
    target = directory / _backup_name(today)
    if target.exists():
        return {"created": None, "removed": []}

    config = settings.DATABASES["default"]
    command = [
        "pg_dump",
        "--no-owner",
        "--no-privileges",
        "--host",
        str(config["HOST"] or "localhost"),
        "--port",
        str(config["PORT"] or 5432),
        "--username",
        str(config["USER"]),
        "--dbname",
        str(config["NAME"]),
    ]
    # The password goes through the environment, never through argv, where any
    # process listing on the box would show it.
    environment = {**os.environ, "PGPASSWORD": str(config.get("PASSWORD") or "")}

    partial = target.with_suffix(target.suffix + ".part")
    try:
        # pg_dump has to be streamed through python. Handing the GzipFile
        # straight to subprocess passes its underlying descriptor, so the dump
        # lands uncompressed inside a gzip wrapper and the file is unreadable.
        with gzip.open(partial, "wb") as archive, tempfile.TemporaryFile() as errors:
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=errors, env=environment
            )
            with process:
                assert process.stdout is not None
                shutil.copyfileobj(process.stdout, archive)
            if process.returncode != 0:
                errors.seek(0)
                detail = errors.read().decode("utf-8", "replace").strip()
                raise RuntimeError(f"pg_dump exited {process.returncode}: {detail[:500]}")
    except Exception:
        partial.unlink(missing_ok=True)
        raise

    partial.rename(target)
    return {
        "created": target.name,
        "removed": _rotate(directory, settings.BACKUP_RETENTION_DAYS, today),
    }
