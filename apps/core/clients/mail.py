"""Mail clients, tech.md section 6."""

import json
from datetime import UTC, datetime
from email.utils import make_msgid
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.core.validators import validate_email

from .base import ClientPayloadError, ClientServerError, ClientTimeout


def validate_mail(*, to: list[str], subject: str, body_html: str, body_text: str) -> None:
    """The test seam: reject anything a slice should never send."""
    if not isinstance(to, list) or not to:
        raise ClientPayloadError("to must be a non empty list of addresses")
    for address in to:
        if not isinstance(address, str):
            raise ClientPayloadError(f"recipient must be a string, got {type(address).__name__}")
        try:
            validate_email(address)
        except ValidationError:
            raise ClientPayloadError(f"invalid recipient {address!r}") from None
    if not subject.strip():
        raise ClientPayloadError("subject must not be empty")
    if not body_text.strip() and not body_html.strip():
        raise ClientPayloadError("message needs a text or an html body")


def _fail(fail_with: int | str | None) -> None:
    if fail_with is None:
        return
    if fail_with == "timeout":
        raise ClientTimeout("simulated timeout")
    if isinstance(fail_with, int):
        raise ClientServerError(fail_with)
    raise ValueError(f"unsupported fail_with {fail_with!r}")


class FakeMailClient:
    """Writes messages to the outbox directory instead of sending them.

    fail_with drives the error paths tech.md section 9 requires a slice to cover:
    FakeMailClient(fail_with=500) and FakeMailClient(fail_with="timeout").
    """

    def __init__(self, outbox: Path | None = None, fail_with: int | str | None = None) -> None:
        self.outbox = Path(outbox) if outbox else Path(settings.MAIL_OUTBOX_DIR)
        self.fail_with = fail_with

    def send(self, *, to: list[str], subject: str, body_html: str, body_text: str) -> str:
        # Validate before failing, so a bad payload is caught even in error mode.
        validate_mail(to=to, subject=subject, body_html=body_html, body_text=body_text)
        _fail(self.fail_with)

        message_id = make_msgid(domain="fake.local")
        self.outbox.mkdir(parents=True, exist_ok=True)
        payload = {
            "message_id": message_id,
            "sent_at": datetime.now(UTC).isoformat(),
            "to": to,
            "subject": subject,
            "body_text": body_text,
            "body_html": body_html,
        }
        name = message_id.strip("<>").replace("@", "_at_").replace(".", "_")
        (self.outbox / f"{name}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return message_id

    def messages(self) -> list[dict[str, object]]:
        """Everything in the outbox, for assertions in tests."""
        if not self.outbox.exists():
            return []
        return [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(self.outbox.glob("*.json"))
        ]


class SmtpMailClient:
    def send(self, *, to: list[str], subject: str, body_html: str, body_text: str) -> str:
        validate_mail(to=to, subject=subject, body_html=body_html, body_text=body_text)

        message_id = make_msgid()
        message = EmailMultiAlternatives(subject=subject, body=body_text, to=to)
        message.extra_headers["Message-ID"] = message_id
        if body_html.strip():
            message.attach_alternative(body_html, "text/html")
        message.send()
        return message_id
