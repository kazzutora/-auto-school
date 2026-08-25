"""Markdown must not be able to emit html an editor wrote, tech.md section 4."""

import re

import pytest
from hypothesis import given
from hypothesis import strategies as st

from apps.core.markdown import render_markdown

# Everything the renderer is allowed to produce.
GENERATED_TAG = re.compile(r"</?(?:p|h2|h3|h4|ul|ol|li|strong|em|code|a)(?: href=\"[^\"<>]*\")?>")


@given(st.text())
def test_only_generated_tags_reach_the_output(source: str) -> None:
    stripped = GENERATED_TAG.sub("", render_markdown(source))
    assert "<" not in stripped
    assert ">" not in stripped


@given(st.text())
def test_no_heading_ever_reaches_h1(source: str) -> None:
    """A page owns exactly one h1 and it comes from the template."""
    assert "<h1" not in render_markdown(source)


@pytest.mark.parametrize(
    "attack",
    [
        "<script>alert(1)</script>",
        "<img src=x onerror=alert(1)>",
        "<iframe src='//evil'></iframe>",
        "<a href='javascript:alert(1)'>x</a>",
        "<style>body{display:none}</style>",
        "<!-- --><svg/onload=alert(1)>",
        "# <script>alert(1)</script>",
        "- <script>alert(1)</script>",
        "**<script>alert(1)</script>**",
    ],
)
def test_html_in_the_source_is_neutralised(attack: str) -> None:
    """Escaped markup may still read like an attack, it just cannot be one.

    So the check is structural: strip the tags the renderer is allowed to emit
    and nothing that could open a tag or an attribute may be left.
    """
    rendered = render_markdown(attack)
    stripped = GENERATED_TAG.sub("", rendered)

    assert "<" not in stripped
    assert ">" not in stripped
    assert "&lt;" in rendered  # escaped, not silently dropped


@pytest.mark.parametrize(
    "scheme",
    [
        "javascript:alert(1)",
        "data:text/html;base64,PHNjcmlwdD4=",
        "vbscript:x",
        "file:///etc/passwd",
    ],
)
def test_dangerous_link_schemes_lose_the_href(scheme: str) -> None:
    rendered = render_markdown(f"[click]({scheme})")
    assert "href" not in rendered
    assert "click" in rendered


@pytest.mark.parametrize(
    "url",
    [
        "https://info-car.pl/",
        "http://example.com/a?b=1&c=2",
        "mailto:osk@wp.pl",
        "tel:+48605065795",
        "/kursy/kat-b/",
        "#faq",
    ],
)
def test_allowed_link_schemes_keep_the_href(url: str) -> None:
    assert "<a href=" in render_markdown(f"[click]({url})")
