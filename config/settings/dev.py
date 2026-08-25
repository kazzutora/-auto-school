"""Development settings."""

from .base import *  # noqa: F403
from .base import COTTON_TEMPLATE_LOADERS, TEMPLATES

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Uncached loaders so template edits show up without a restart.
TEMPLATES[0]["OPTIONS"]["loaders"] = COTTON_TEMPLATE_LOADERS

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Fakes only: no real credentials exist in development, tech.md section 6.
MAIL_CLIENT = "fake"
SMS_CLIENT = "fake"
