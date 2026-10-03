"""Test settings. The suite runs against fakes only, tech.md section 6."""

from .base import *  # noqa: F403

DEBUG = False
SECRET_KEY = "test-not-secret"

MAIL_CLIENT = "fake"
SMS_CLIENT = "fake"
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Run tasks in process so idempotency tests can call them twice directly,
# tech.md section 9.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# One process, and the suite clears the cache around every test: in memory, so
# that never reaches the Redis the running dev stack uses.
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
