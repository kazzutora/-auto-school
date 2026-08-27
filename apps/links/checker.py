"""Reaching the outside world for links.tasks.check_links, DEV.md S7.2.

CONTRACT GAP: tech.md section 6 keeps external services behind protocols in
apps/core/clients, with a fake for dev and tests. The only protocols there are
MailClient and SmsClient, and a link check is the same kind of call: it leaves
the machine, it times out, it fails with a status. Until an HttpClient and a
settings switch for it exist, the seam lives here and the tests replace it.

Nothing outside this module knows what makes the request.
"""

from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from apps.links.models import HTTP_ERROR

# DEV.md S7.2. Ten seconds is long enough for a slow government site and short
# enough that a sweep of the whole list still finishes in a couple of minutes.
TIMEOUT = 10.0

# Some servers answer HEAD with an error and the same url with GET perfectly
# well, so a failing HEAD is worth one more question rather than a verdict.
RETRY_WITH_GET = frozenset({400, 401, 403, 405, 406, 501})

# UsefulLink.last_error is 200 characters, tech.md section 4.6.
ERROR_LIMIT = 200


@dataclass(frozen=True)
class CheckResult:
    """What one look at a url found. No status at all means it never answered."""

    status: int | None = None
    error: str = ""


def user_agent() -> str:
    """Who is knocking, so an administrator can tell us from a scraper."""
    from django.contrib.sites.models import Site

    from apps.core.models import SiteSettings

    name = SiteSettings.get_solo().short_name or "OSK"
    return f"{name} link checker (+https://{Site.objects.get_current().domain})"


def _looks_like_a_timeout(error: URLError) -> bool:
    return isinstance(error.reason, TimeoutError)


def _fetch(url: str, *, method: str, timeout: float, agent: str) -> CheckResult:
    request = Request(url, method=method, headers={"User-Agent": agent})  # noqa: S310
    with urlopen(request, timeout=timeout) as response:  # noqa: S310
        # Redirects are followed by the opener, so this is the final answer.
        return CheckResult(status=response.status)


def check(url: str, *, timeout: float = TIMEOUT, agent: str | None = None) -> CheckResult:
    """HEAD the url, fall back to GET, and never raise.

    tech.md section 6 asks for HEAD/GET. The caller gets a result either way:
    one unreachable link must not end the sweep, DEV.md S7.2.
    """
    agent = agent or user_agent()

    for method in ("HEAD", "GET"):
        try:
            return _fetch(url, method=method, timeout=timeout, agent=agent)
        except HTTPError as error:
            # A redirect the opener could not follow, usually a 302 to HEAD with
            # no usable Location. GET is what follows it, tech.md section 6.
            refused_head = error.code in RETRY_WITH_GET or error.code < HTTP_ERROR
            if method == "HEAD" and refused_head:
                continue
            # A link that redirects works. Only 4xx and 5xx are worth flagging.
            failure = f"HTTP {error.code}" if error.code >= HTTP_ERROR else ""
            return CheckResult(status=error.code, error=failure)
        except TimeoutError:
            return CheckResult(error=f"timeout after {timeout:.0f}s")
        except URLError as error:
            if _looks_like_a_timeout(error):
                return CheckResult(error=f"timeout after {timeout:.0f}s")
            return CheckResult(error=str(error.reason)[:ERROR_LIMIT])
        except Exception as error:  # a malformed url, a broken proxy, anything
            return CheckResult(error=f"{type(error).__name__}: {error}"[:ERROR_LIMIT])

    return CheckResult(error="no answer to HEAD or GET")
