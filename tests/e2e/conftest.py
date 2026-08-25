"""End to end fixtures.

Playwright's sync api drives the browser from a greenlet with an event loop
running, and django then refuses ordinary orm calls on that thread. The opt out
is scoped to this directory so the rest of the suite keeps the guard.
"""

import os

os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "1")
