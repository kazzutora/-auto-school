"""Pure domain logic for the leads slice. No ORM here."""

import hashlib
import re

from django.http import HttpRequest

# Polish numbers: nine national digits behind country code 48.
COUNTRY_CODE = "48"
NATIONAL_LENGTH = 9


def normalize_phone(value: str | None) -> str:
    """One canonical +48XXXXXXXXX for every way a visitor types their number.

    Empty string when the input is not a Polish number we can recognise, so the
    caller can reject it instead of storing something unusable.
    """
    digits = re.sub(r"\D", "", value or "")
    if not digits:
        return ""

    # 00 is the international prefix people still dial from a landline.
    if digits.startswith("00"):
        digits = digits[2:]
    # Strip the country code only when something is left underneath it: a nine
    # digit national number may itself start with 48.
    if len(digits) > NATIONAL_LENGTH and digits.startswith(COUNTRY_CODE):
        digits = digits[len(COUNTRY_CODE) :]
    # Trunk prefix, as in 0 605 065 795.
    digits = digits.lstrip("0")

    if len(digits) != NATIONAL_LENGTH:
        return ""
    return f"+{COUNTRY_CODE}{digits}"


def hash_ip(ip: str | None, salt: str) -> str:
    """sha256(ip + salt), tech.md section 4.3.

    The raw address is never stored. The hash still lets the owner see that two
    submissions came from the same place.
    """
    if not ip:
        return ""
    return hashlib.sha256(f"{ip}{salt}".encode()).hexdigest()


def client_ip(meta: dict[str, str]) -> str:
    """The visitor's address as seen behind Caddy.

    X-Forwarded-For is only trustworthy because our own proxy sets it, and the
    left most entry is the original client.
    """
    forwarded = (meta.get("HTTP_X_FORWARDED_FOR") or "").split(",")[0].strip()
    return forwarded or (meta.get("REMOTE_ADDR") or "").strip()


def request_ip(request: HttpRequest) -> str:
    """client_ip for django-ratelimit, RATELIMIT_IP_META_KEY in settings.

    Its own default reads REMOTE_ADDR, which behind Caddy is the proxy, and
    every visitor would share one limit.
    """
    return client_ip(request.META)
