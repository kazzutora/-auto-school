"""Production settings. Security baseline comes from tech.md section 19."""

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *  # noqa: F403
from .base import COTTON_TEMPLATE_LOADERS, MIDDLEWARE, SENTRY_DSN, TEMPLATES, env

DEBUG = False

# No development fallback: the stack must refuse to start without real values.
SECRET_KEY = env("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

TEMPLATES[0]["OPTIONS"]["loaders"] = [
    ("django.template.loaders.cached.Loader", COTTON_TEMPLATE_LOADERS),
]

# A preview box reached by bare ip has no certificate anyone would accept, so
# the redirect to https and the secure-only cookies would shut the browser out
# of a site that otherwise works. HTTPS_ENABLED=0 drops exactly those, and
# nothing else. It stays on by default: the live site is served over tls.
HTTPS_ENABLED = env.bool("HTTPS_ENABLED", default=True)

# Caddy terminates tls and sets the header, tech.md section 19.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = HTTPS_ENABLED
# The container healthcheck and the deploy smoke step reach /healthz over plain
# http on the loopback, where no proxy sets X-Forwarded-Proto. Without the
# exemption the redirect above answers them with a 301 to port 443 of a
# container that does not listen there, and a healthy stack reports itself sick.
# Nothing is exposed by it: a request from outside meets Caddy first, and Caddy
# redirects the whole host to https before django is reached.
SECURE_REDIRECT_EXEMPT = [r"^healthz$"]
SECURE_HSTS_SECONDS = 31536000 if HTTPS_ENABLED else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = HTTPS_ENABLED
SECURE_HSTS_PRELOAD = HTTPS_ENABLED
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SESSION_COOKIE_SECURE = HTTPS_ENABLED
CSRF_COOKIE_SECURE = HTTPS_ENABLED
X_FRAME_OPTIONS = "DENY"

# Derived from ALLOWED_HOSTS rather than read from .env: the domain would
# otherwise be written twice and the two copies would drift apart. Django
# matches the Origin header of an unsafe request against this list, and behind
# Caddy every origin is https - except in preview mode, which has no
# certificate to name.
_ORIGIN_SCHEME = "https" if HTTPS_ENABLED else "http"
CSRF_TRUSTED_ORIGINS = [
    f"{_ORIGIN_SCHEME}://*{host}" if host.startswith(".") else f"{_ORIGIN_SCHEME}://{host}"
    for host in ALLOWED_HOSTS
    if host != "*"
]

# tech.md section 19 scopes the policy to production: the django debug page
# needs inline scripts that 'self' would block.
MIDDLEWARE = [*MIDDLEWARE, "config.middleware.ContentSecurityPolicyMiddleware"]

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        traces_sample_rate=0.1,
        # Lead data is personal data under RODO, keep it out of error reports.
        send_default_pii=False,
    )
