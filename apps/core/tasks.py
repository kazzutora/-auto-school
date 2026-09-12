"""Shared Celery base class and the core background tasks."""

import gzip
import logging
import os
import re
import shutil
import subprocess
import tempfile
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen

from celery import Task, shared_task
from django.conf import settings
from django.urls import reverse

from apps.core.contracts import validate_payload

logger = logging.getLogger(__name__)


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


# --------------------------------------------------------------------------
# sitemap ping, tech.md section 6, DEV.md S8
#
# CONTRACT GAP: tech.md section 6 keeps every call that leaves the machine
# behind a protocol in apps/core/clients, and the only two there are MailClient
# and SmsClient. A ping is the same kind of call: it goes out, it times out, it
# answers with a status. Until an HttpClient and a settings switch for it exist,
# the seam is fetch_status below and the tests replace it, the same stand in
# apps/links/checker.py had to make for the link sweep.

PING_TIMEOUT = 10.0
PING_ERROR = 400

# tech.md section 6 names google and bing. Google retired its ping endpoint in
# 2023 and now answers 404 there, which is why one engine refusing is a logged
# line and not a failed task.
SEARCH_ENGINES = {
    "google": "https://www.google.com/ping?sitemap=",
    "bing": "https://www.bing.com/ping?sitemap=",
}

# What django.contrib.sites ships with. It means nobody has set the real one.
PLACEHOLDER_DOMAIN = "example.com"


def fetch_status(url: str, *, timeout: float = PING_TIMEOUT) -> int:
    """GET the url and return the status code it answered with."""
    request = Request(url, headers={"User-Agent": "OSK Ostrycharz sitemap ping"})  # noqa: S310
    with urlopen(request, timeout=timeout) as response:  # noqa: S310
        return int(response.status)


def sitemap_url() -> str:
    """The absolute url of sitemap.xml, or empty when the domain is unset.

    A background job has no request to build an absolute url from, so the
    domain can only come from the Site row. https because production is behind
    Caddy and http would advertise a url that immediately redirects.
    """
    from django.contrib.sites.models import Site

    domain = Site.objects.get_current().domain
    if not domain or domain == PLACEHOLDER_DOMAIN:
        return ""
    return f"https://{domain}{reverse('sitemap')}"


@shared_task(bind=True, base=BaseTask)
def ping_sitemap(self: Task) -> dict[str, Any]:
    """Tell the search engines where sitemap.xml is, tech.md section 6.

    Repeatable by nature: the task writes nothing anywhere, so a second run in
    the same night sends the same two requests and leaves the same state.

    One engine failing does not fail the task. Both are best effort, and a
    retry storm against a search engine would earn the domain nothing but a
    rate limit.
    """
    validate_payload("core.tasks.ping_sitemap", {})

    target = sitemap_url()
    if not target:
        logger.warning("sitemap ping skipped: the site domain is still the default")
        return {"sitemap": "", "accepted": [], "failed": []}

    accepted = []
    failed = []
    for engine, endpoint in SEARCH_ENGINES.items():
        try:
            status = fetch_status(endpoint + quote(target, safe=""))
        except Exception as error:
            logger.warning("sitemap ping to %s failed: %s", engine, error)
            failed.append(engine)
            continue

        if status >= PING_ERROR:
            logger.warning("sitemap ping to %s answered %s", engine, status)
            failed.append(engine)
        else:
            accepted.append(engine)

    return {"sitemap": target, "accepted": accepted, "failed": failed}


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
