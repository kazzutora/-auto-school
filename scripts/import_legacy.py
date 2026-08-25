"""Import the old site export into Course rows, DEV.md S1.1.

Writes only to apps.courses models. Page bodies come later, in the slice that
owns them.

Idempotent: rows are matched on slug, so a second run updates the same fifteen
courses instead of adding more. Fields an editor curates in the admin, the title
above all, are set only when the row is created, so a rerun never overwrites
someone's work with the shouty heading the old site used.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# tech.md section 15: the source typos, corrected on the way in.
TYPO_FIXES = {
    "Szkolnie okresowe": "Szkolenia okresowe",
    "Jesteśmy firma rodzinną": "Jesteśmy firmą rodzinną",
    "otrzymuja": "otrzymują",
    "prowadzane": "prowadzone",
    "Pracowania czynna": "Pracownia czynna",
}

# Two fragments could not be read from the old site in full. Both forms appear
# in exports, so accept either.
UNREAD_MARKERS = ("[…]", "[...]")
NEEDS_WORK = "[TODO_OWNER: fragment do uzupełnienia]"

SECTION_ENTITLEMENTS = "Uprawnia do kierowania"
SECTION_REQUIREMENTS = "Wymagania"

LEGACY_DIR = Path(__file__).resolve().parents[1] / "data" / "legacy"


def _setup() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    import django

    django.setup()


def fix_typos(text: str) -> str:
    """Apply the correction table from tech.md section 15.

    Whole words only. A bare replace would also rewrite the middle of a longer
    word that happens to contain one of these strings.
    """
    for wrong, right in TYPO_FIXES.items():
        text = re.sub(rf"\b{re.escape(wrong)}\b", right, text)
    return text


def mark_unread(text: str) -> tuple[str, bool]:
    """Replace an unreadable fragment with something an editor will notice."""
    marked = False
    for marker in UNREAD_MARKERS:
        if marker in text:
            text = text.replace(marker, NEEDS_WORK)
            marked = True
    return text, marked


@dataclass
class LegacyPage:
    slug: str
    meta: dict[str, str]
    lead: str
    entitlements: str
    requirements: str
    body: str
    needs_work: bool


def parse(path: Path) -> LegacyPage:
    """Split one exported page into the fields Course keeps."""
    raw = fix_typos(path.read_text(encoding="utf-8"))
    raw, needs_work = mark_unread(raw)

    meta: dict[str, str] = {}
    if raw.startswith("---"):
        header, _, raw = raw[3:].partition("---")
        for line in header.strip().splitlines():
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()

    sections: dict[str, list[str]] = {"": []}
    current = ""
    for line in raw.strip().splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
        elif not line.startswith("# "):
            sections[current].append(line)

    def text(name: str) -> str:
        return "\n".join(sections.get(name, [])).strip()

    return LegacyPage(
        slug=meta.get("slug") or path.stem,
        meta=meta,
        lead=text(""),
        entitlements=text(SECTION_ENTITLEMENTS),
        requirements=text(SECTION_REQUIREMENTS),
        body=text("Opis"),
        needs_work=needs_work,
    )


@dataclass
class Report:
    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    needs_work: list[str] = field(default_factory=list)
    reconstructed: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.created) + len(self.updated)


def import_courses(directory: Path | None = None) -> Report:
    from apps.courses.models import Course

    directory = Path(directory or LEGACY_DIR)
    report = Report()

    for order, path in enumerate(sorted(directory.glob("*.md")), start=10):
        if path.name.lower() == "readme.md":
            continue

        page = parse(path)
        content: dict[str, Any] = {
            "lead": page.lead,
            "entitlements": page.entitlements,
            "requirements": page.requirements,
            "body": page.body,
        }
        # Applied on creation only: an editor owns these afterwards.
        creation: dict[str, Any] = {
            **content,
            "title": page.meta.get("title") or page.slug,
            "kind": page.meta.get("kind") or Course.Kind.LICENSE,
            "code": page.meta.get("code", ""),
            "min_age": int(page.meta["min_age"]) if page.meta.get("min_age") else None,
            "languages": ["pl"],
            "is_active": True,
            "order": order,
        }

        _course, created = Course.objects.update_or_create(
            slug=page.slug, defaults=content, create_defaults=creation
        )
        (report.created if created else report.updated).append(page.slug)
        if page.needs_work:
            report.needs_work.append(page.slug)
        if page.meta.get("source") == "reconstructed":
            report.reconstructed.append(page.slug)

    return report


def main() -> None:
    _setup()
    report = import_courses()
    print(
        f"imported {report.total} courses: {len(report.created)} new, {len(report.updated)} updated"
    )
    for slug in report.needs_work:
        print(f"  needs manual completion: {slug}")
    if report.reconstructed:
        print(
            f"  warning: {len(report.reconstructed)} pages are marked source: reconstructed, "
            "not the real export"
        )


if __name__ == "__main__":
    main()
