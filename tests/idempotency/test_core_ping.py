"""tech.md section 9: every Celery task ships an idempotency test."""

from apps.core.tasks import ping


def test_ping_repeats_without_changing_anything() -> None:
    first = ping.apply().get()
    second = ping.apply().get()

    assert first == "pong"
    assert second == first
