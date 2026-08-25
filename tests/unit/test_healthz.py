"""The health probe, tech.md section 17."""

import json

import pytest
from django.test import Client
from django.urls import reverse

from apps.core import health

pytestmark = pytest.mark.django_db


def body(response) -> dict:
    return json.loads(response.content)


def test_route_is_not_language_prefixed() -> None:
    """The deploy smoke step and the container probe both call /healthz flat."""
    assert reverse("healthz") == "/healthz"


def test_green_when_both_dependencies_answer(client: Client) -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    assert body(response) == {"status": "ok", "checks": {"database": "ok", "redis": "ok"}}


def test_red_when_redis_is_down(client: Client, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(health, "_redis", lambda: "ConnectionError")

    response = client.get("/healthz")

    assert response.status_code == 503
    assert body(response)["status"] == "error"
    assert body(response)["checks"] == {"database": "ok", "redis": "ConnectionError"}


def test_red_when_the_database_is_down(client: Client, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(health, "_database", lambda: "OperationalError")

    response = client.get("/healthz")

    assert response.status_code == 503
    assert body(response)["checks"]["database"] == "OperationalError"


def test_never_cached(client: Client) -> None:
    """A cached probe would keep reporting a service that has since died."""
    assert client.get("/healthz")["Cache-Control"] == "no-store"


def test_probes_report_the_failure_class_not_the_connection_string(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A leaked dsn in a public probe would publish the database password."""

    def explode(*args: object, **kwargs: object) -> None:
        raise ConnectionError("postgres://osk:hunter2@db:5432/osk refused")

    monkeypatch.setattr(health.redis.Redis, "from_url", explode)
    assert health._redis() == "ConnectionError"
