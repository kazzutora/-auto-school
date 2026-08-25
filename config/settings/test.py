"""Bootstrap settings for the test runner and the mypy django plugin.

Deliberately minimal. The real settings tree (base, dev, prod, test on top of
django-environ, tech.md section 10) lands in S0.3 and replaces this module.
Until then it only has to let django.setup() succeed against the empty skeleton,
so it declares no DATABASES: postgres belongs to the S0.2 compose stack.
"""

SECRET_KEY = "test-not-secret"
DEBUG = False
USE_TZ = True

INSTALLED_APPS = [
    "apps.core",
    "apps.courses",
    "apps.leads",
    "apps.people",
    "apps.gallery",
    "apps.links",
    "apps.reviews",
]
