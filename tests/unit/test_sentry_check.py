"""The sentry probe, DEV.md checklist I.3."""

from typing import Any

import pytest
import sentry_sdk
from django.core.management import call_command
from django.core.management.base import CommandError
from sentry_sdk.transport import Transport


class Recorder(Transport):
    """Keeps envelopes instead of shipping them anywhere."""

    def __init__(self) -> None:
        super().__init__()
        self.envelopes: list[Any] = []

    def capture_envelope(self, envelope: Any) -> None:
        self.envelopes.append(envelope)


def test_it_refuses_when_sentry_is_not_configured() -> None:
    """Silently doing nothing would let a broken dsn ship unnoticed."""
    with pytest.raises(CommandError, match="SENTRY_DSN is not set"):
        call_command("sentry_check")


def test_it_sends_exactly_one_exception() -> None:
    recorder = Recorder()

    with sentry_sdk.isolation_scope():
        sentry_sdk.init(
            dsn="https://key@example.invalid/1",
            transport=recorder,
            send_default_pii=False,
        )
        call_command("sentry_check")
        sentry_sdk.get_client().close()

    assert len(recorder.envelopes) == 1
    event = recorder.envelopes[0].get_event()
    assert event["exception"]["values"][0]["type"] == "SentryCheckError"


def test_personal_data_stays_out_of_the_report() -> None:
    """Lead data is personal data under RODO, tech.md section 4.3."""
    recorder = Recorder()

    with sentry_sdk.isolation_scope():
        sentry_sdk.init(
            dsn="https://key@example.invalid/1",
            transport=recorder,
            send_default_pii=False,
        )
        assert sentry_sdk.get_client().options["send_default_pii"] is False
        call_command("sentry_check")
        sentry_sdk.get_client().close()

    event = recorder.envelopes[0].get_event()
    assert "user" not in event or not event["user"].get("email")
