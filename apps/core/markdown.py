"""Markdown rendering for content fields, tech.md section 4.

Safe by construction rather than by sanitising afterwards: the source is escaped
first, then a fixed subset of markdown is applied to the escaped text. No html
written by an editor can survive that order, so no separate sanitiser is needed.

Headings start at h2. A page owns exactly one h1 and it comes from the template,
tech.md section 8.
"""

import re

from django.utils.html import escape
from django.utils.safestring import SafeString, mark_safe

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_UNORDERED_ITEM = re.compile(r"^[-*]\s+(.*)$")
_ORDERED_ITEM = re.compile(r"^\d+[.)]\s+(.*)$")

_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_ITALIC = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")

_SAFE_SCHEMES = ("http://", "https://", "mailto:", "tel:")
_MAX_HEADING_LEVEL = 4


def _is_safe_href(url: str) -> bool:
    """Allow the listed schemes plus site relative links, nothing else."""
    if url.startswith(("/", "#")):
        return True
    return url.startswith(_SAFE_SCHEMES)


def _render_inline(text: str) -> str:
    """Inline markup on already escaped text."""
    text = _CODE.sub(r"<code>\1</code>", text)
    text = _BOLD.sub(r"<strong>\1</strong>", text)
    text = _ITALIC.sub(r"<em>\1</em>", text)

    def link(match: re.Match[str]) -> str:
        label, url = match.group(1), match.group(2)
        # The url arrives escaped, so &amp; has to go back for the comparison.
        if not _is_safe_href(url.replace("&amp;", "&")):
            return label
        return f'<a href="{url}">{label}</a>'

    return _LINK.sub(link, text)


def _flush(buffer: list[str], out: list[str], tag: str) -> None:
    if not buffer:
        return
    items = "".join(f"<li>{item}</li>" for item in buffer)
    out.append(f"<{tag}>{items}</{tag}>")
    buffer.clear()


def render_markdown(text: str) -> SafeString:
    """Render the supported markdown subset to safe html."""
    out: list[str] = []
    paragraph: list[str] = []
    unordered: list[str] = []
    ordered: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            out.append(f"<p>{' '.join(paragraph)}</p>")
            paragraph.clear()

    def flush_all() -> None:
        flush_paragraph()
        _flush(unordered, out, "ul")
        _flush(ordered, out, "ol")

    for raw_line in escape(text).splitlines():
        line = raw_line.strip()

        if not line:
            flush_all()
            continue

        heading = _HEADING.match(line)
        if heading:
            flush_all()
            level = min(len(heading.group(1)) + 1, _MAX_HEADING_LEVEL)
            out.append(f"<h{level}>{_render_inline(heading.group(2).strip())}</h{level}>")
            continue

        item = _UNORDERED_ITEM.match(line)
        if item:
            flush_paragraph()
            _flush(ordered, out, "ol")
            unordered.append(_render_inline(item.group(1).strip()))
            continue

        item = _ORDERED_ITEM.match(line)
        if item:
            flush_paragraph()
            _flush(unordered, out, "ul")
            ordered.append(_render_inline(item.group(1).strip()))
            continue

        _flush(unordered, out, "ul")
        _flush(ordered, out, "ol")
        paragraph.append(_render_inline(line))

    flush_all()
    return mark_safe("".join(out))  # noqa: S308 - input was escaped above
