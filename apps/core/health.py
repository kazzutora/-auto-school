"""Health probe, tech.md section 17.

/healthz answers 200 only when postgres and redis are both reachable. The deploy
smoke step gates a release on it, so it must actually touch both, not report
what it hopes is true.
"""

from typing import Any

import redis
from django.conf import settings
from django.db import connection
from django.http import HttpRequest, JsonResponse


def _database() -> str | None:
    """None when healthy, otherwise the class of failure."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception as exc:
        return type(exc).__name__
    return None


def _redis() -> str | None:
    client = None
    try:
        client = redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        client.ping()
    except Exception as exc:
        return type(exc).__name__
    finally:
        if client is not None:
            client.close()
    return None


def healthz(request: HttpRequest) -> JsonResponse:
    checks: dict[str, Any] = {}
    for name, probe in (("database", _database), ("redis", _redis)):
        failure = probe()
        checks[name] = "ok" if failure is None else failure

    healthy = all(value == "ok" for value in checks.values())
    response = JsonResponse(
        {"status": "ok" if healthy else "error", "checks": checks},
        status=200 if healthy else 503,
    )
    # A cached health probe is a health probe that lies.
    response["Cache-Control"] = "no-store"
    return response
