"""Shared settings. Every environment file imports from here.

All configuration comes from the environment via django-environ, tech.md
section 10. Defaults are development values, never real secrets.
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parents[2]

env = environ.Env()

SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-not-secret")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# Host default targets the port docker-compose publishes, so pytest and
# manage.py work from the host as well as from inside the web container.
DATABASES = {
    "default": env.db("DATABASE_URL", default="postgres://osk:osk@localhost:5432/osk"),
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")

INSTALLED_APPS = [
    # Before django.contrib.admin: modeltranslation patches the admin classes.
    "modeltranslation",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.sitemaps",
    # tech.md section 4.8: legacy urls are served from the redirects table.
    "django.contrib.redirects",
    # SimpleAppConfig skips cotton's automatic loader wiring: TEMPLATES below
    # sets the loaders explicitly so dev can drop the cached loader.
    "django_cotton.apps.SimpleAppConfig",
    "solo",
    "imagekit",
    "crispy_forms",
    "crispy_tailwind",
    "apps.core",
    "apps.courses",
    "apps.leads",
    "apps.people",
    "apps.gallery",
    "apps.links",
    "apps.reviews",
]

SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # LocaleMiddleware needs the session, and must precede CommonMiddleware.
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.contrib.redirects.middleware.RedirectFallbackMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

COTTON_TEMPLATE_LOADERS = [
    "django_cotton.cotton_loader.Loader",
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
]

TEMPLATE_CONTEXT_PROCESSORS = [
    "django.template.context_processors.debug",
    "django.template.context_processors.request",
    "django.contrib.auth.context_processors.auth",
    "django.contrib.messages.context_processors.messages",
    "django.template.context_processors.i18n",
    "apps.core.context_processors.site_settings",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "OPTIONS": {
            "loaders": COTTON_TEMPLATE_LOADERS,
            "builtins": ["django_cotton.templatetags.cotton"],
            "context_processors": TEMPLATE_CONTEXT_PROCESSORS,
        },
    },
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# i18n. Polish is the default and carries no url prefix, tech.md section 5.
LANGUAGE_CODE = "pl"
LANGUAGES = [
    ("pl", "Polski"),
    ("ru", "Русский"),
    ("uk", "Українська"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = "Europe/Warsaw"
USE_I18N = True
USE_TZ = True

MODELTRANSLATION_DEFAULT_LANGUAGE = "pl"
MODELTRANSLATION_LANGUAGES = ("pl", "ru", "uk")
MODELTRANSLATION_FALLBACK_LANGUAGES = ("pl",)

STATIC_URL = "static/"
# Not BASE_DIR/static: that directory holds the sources, and the compose stack
# mounts the static volume here.
STATIC_ROOT = BASE_DIR / "staticfiles"
# Listed one by one rather than as the whole static/ tree, because tech.md
# section 3 puts the tailwind input at static/src/css/app.css. Collecting that
# breaks the manifest: its font urls are relative to the built file, so
# ../fonts resolves to src/fonts and nothing is there.
STATICFILES_DIRS = [
    ("css", BASE_DIR / "static" / "css"),
    ("js", BASE_DIR / "static" / "js"),
    ("fonts", BASE_DIR / "static" / "fonts"),
    ("icons", BASE_DIR / "static" / "icons"),
    # The logo kit: lettering, mark, favicon and the og card. Self hosted like
    # everything else, tech.md section 2.
    ("brand", BASE_DIR / "static" / "brand"),
    # The photographs, PHOTOS.md. scripts/optimize_photos.py writes the crops
    # into static/img/<ratio>/ and they are served from here; the 2400px
    # originals live in static/img/source/ beside their CREDITS.txt and are
    # never served — nothing links to them, and they are three times the weight
    # of anything the page asks for.
    ("img", BASE_DIR / "static" / "img"),
]

# The default pair, with the filesystem half swapped for one that hides the
# source/ trees: the owner's raster logo and mockup, ROSE.md A.1, and the
# photograph originals, PHOTOS.md. Both are inputs, not assets.
STATICFILES_FINDERS = [
    "apps.core.staticfiles.PrivateSourceFilteredFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

MEDIA_URL = "media/"
MEDIA_ROOT = Path(env("MEDIA_ROOT", default=str(BASE_DIR / "media")))

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# gallery.tasks.build_renditions warms these ahead of time, tech.md section 6.
# JustInTime is the safety net for anything the task has not reached yet.
IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY = "imagekit.cachefiles.strategies.JustInTime"
IMAGEKIT_CACHEFILE_DIR = "renditions"

CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# Celery. The beat schedule lives in config/celery.py and nowhere else,
# tech.md section 6.
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TASK_DEFAULT_QUEUE = "default"
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = TIME_ZONE

# External clients are chosen here and resolved in apps/core/clients,
# tech.md section 6. Development and tests always run the fakes.
MAIL_CLIENT = env("MAIL_CLIENT", default="fake")
SMS_CLIENT = env("SMS_CLIENT", default="fake")

EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER or "noreply@oskostrycharz.pl"

SMSAPI_TOKEN = env("SMSAPI_TOKEN", default="")

# core.tasks.db_backup writes here, tech.md section 19. The production stack
# mounts deploy/backups on this path.
BACKUP_DIR = BASE_DIR / "backups"
BACKUP_RETENTION_DAYS = 14

# Where FakeMailClient drops messages, tech.md section 6.
MAIL_OUTBOX_DIR = BASE_DIR / "tests" / "outbox"

# Raw client ip is never stored, only sha256(ip + salt), tech.md section 4.3.
IP_HASH_SALT = env("IP_HASH_SALT", default="dev-salt")

SENTRY_DSN = env("SENTRY_DSN", default="")

# Nothing on a public page may come from a third party host, tech.md section 2.
# Two deliberate exceptions, both forced by contracts in section 7:
#   script-src 'unsafe-eval'  Alpine 3 evaluates x-* expressions with
#                             new Function(). The modal and the lightbox are
#                             specified as Alpine components. Dropping this
#                             means switching to the Alpine CSP build, which
#                             forbids inline expressions entirely.
#   frame-src google          The map, core v26: a google maps embed that
#                             static/js/app.js builds only when the visitor
#                             presses the button. Nothing is framed before it.
CONTENT_SECURITY_POLICY = {
    "default-src": ["'self'"],
    "script-src": ["'self'", "'unsafe-eval'"],
    "style-src": ["'self'", "'unsafe-inline'"],
    "img-src": ["'self'", "data:"],
    "font-src": ["'self'"],
    "connect-src": ["'self'"],
    "frame-src": ["https://www.google.com"],
    "frame-ancestors": ["'none'"],
    "base-uri": ["'self'"],
    "form-action": ["'self'"],
    "object-src": ["'none'"],
}
