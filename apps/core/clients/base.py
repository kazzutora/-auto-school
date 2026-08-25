"""External client protocols and errors, tech.md section 6.

Slices never talk to a third party directly. They depend on these protocols, and
development and tests always resolve to the fakes.
"""

from typing import Protocol, runtime_checkable


class ClientError(Exception):
    """A client call failed."""


class ClientTimeout(ClientError):
    """The remote side did not answer in time."""


class ClientServerError(ClientError):
    """The remote side answered with a server error."""

    def __init__(self, status: int = 500) -> None:
        super().__init__(f"remote returned {status}")
        self.status = status


class ClientPayloadError(ClientError, ValueError):
    """The caller passed something the contract does not allow."""


@runtime_checkable
class MailClient(Protocol):
    def send(self, *, to: list[str], subject: str, body_html: str, body_text: str) -> str: ...


@runtime_checkable
class SmsClient(Protocol):
    def send(self, *, to: str, text: str) -> str: ...
