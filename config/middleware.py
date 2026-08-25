"""Project wide middleware.

Django 5.1 has no built in content security policy, and tech.md section 2 bans
third party hosts on public pages, so the header is assembled here from
settings.CONTENT_SECURITY_POLICY instead of pulling in another dependency.
"""

from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse


def _render_policy(directives: dict[str, list[str]]) -> str:
    return "; ".join(f"{name} {' '.join(values)}" for name, values in directives.items())


class ContentSecurityPolicyMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        self.policy = _render_policy(getattr(settings, "CONTENT_SECURITY_POLICY", {}))

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        if self.policy and "Content-Security-Policy" not in response:
            response["Content-Security-Policy"] = self.policy
        return response
