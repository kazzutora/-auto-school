"""Prove Sentry is wired, DEV.md checklist I.3.

Deliberately a management command and not a url: a public route that raises on
demand is an invitation.

    docker compose -f deploy/docker-compose.prod.yml run --rm web \
        python manage.py sentry_check
"""

from typing import Any

import sentry_sdk
from django.core.management.base import BaseCommand, CommandError


class SentryCheckError(RuntimeError):
    """Raised on purpose, so the event is easy to spot in the issue list."""


class Command(BaseCommand):
    help = "Send one test exception to Sentry and confirm it was accepted."

    def handle(self, *args: Any, **options: Any) -> None:
        client = sentry_sdk.get_client()
        if not client.is_active():
            raise CommandError("SENTRY_DSN is not set, nothing would be sent")

        try:
            raise SentryCheckError("sentry_check: this exception is intentional")
        except SentryCheckError as exc:
            event_id = sentry_sdk.capture_exception(exc)

        client.flush(timeout=10)

        if event_id is None:
            raise CommandError("Sentry accepted no event")
        self.stdout.write(self.style.SUCCESS(f"sent event {event_id}"))
