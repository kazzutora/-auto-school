"""Client resolution. settings.MAIL_CLIENT and settings.SMS_CLIENT pick the
implementation, tech.md section 6."""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .base import (
    ClientError,
    ClientPayloadError,
    ClientServerError,
    ClientTimeout,
    MailClient,
    SmsClient,
)
from .mail import FakeMailClient, SmtpMailClient
from .sms import FakeSmsClient

__all__ = [
    "ClientError",
    "ClientPayloadError",
    "ClientServerError",
    "ClientTimeout",
    "FakeMailClient",
    "FakeSmsClient",
    "MailClient",
    "SmsClient",
    "SmtpMailClient",
    "get_mail_client",
    "get_sms_client",
]


def get_mail_client() -> MailClient:
    choice = settings.MAIL_CLIENT
    if choice == "fake":
        return FakeMailClient()
    if choice == "smtp":
        return SmtpMailClient()
    raise ImproperlyConfigured(f"MAIL_CLIENT must be fake or smtp, got {choice!r}")


def get_sms_client() -> SmsClient:
    choice = settings.SMS_CLIENT
    if choice == "fake":
        return FakeSmsClient()
    # SmsApiClient is switched on later, tech.md section 6.
    raise ImproperlyConfigured(f"SMS_CLIENT must be fake, got {choice!r}")
