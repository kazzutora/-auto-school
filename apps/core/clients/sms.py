"""Sms clients, tech.md section 6."""

import re

from .base import ClientPayloadError
from .mail import _fail

_PHONE = re.compile(r"^\+?[0-9 ()-]{6,20}$")


def validate_sms(*, to: str, text: str) -> None:
    if not isinstance(to, str) or not _PHONE.match(to):
        raise ClientPayloadError(f"invalid recipient number {to!r}")
    if not text.strip():
        raise ClientPayloadError("text must not be empty")


class FakeSmsClient:
    """Keeps sent messages in memory, with the same failure modes as the mail fake."""

    def __init__(self, fail_with: int | str | None = None) -> None:
        self.fail_with = fail_with
        self.sent: list[dict[str, str]] = []

    def send(self, *, to: str, text: str) -> str:
        validate_sms(to=to, text=text)
        _fail(self.fail_with)

        message_id = f"fake-sms-{len(self.sent) + 1}"
        self.sent.append({"message_id": message_id, "to": to, "text": text})
        return message_id
