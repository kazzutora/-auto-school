"""Development settings."""

from .base import *  # noqa: F403
from .base import COTTON_TEMPLATE_LOADERS, MAIL_CLIENT, TEMPLATES

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Uncached loaders so template edits show up without a restart.
TEMPLATES[0]["OPTIONS"]["loaders"] = COTTON_TEMPLATE_LOADERS

# Fakes by default: no real credentials exist in development, tech.md section 6.
# MAIL_CLIENT=smtp in .env switches the dev stack to a real mailbox, so the
# owner can see what a lead notification actually looks like in an inbox.
if MAIL_CLIENT == "smtp":
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

SMS_CLIENT = "fake"
