"""Pure domain logic for the gallery slice. No ORM here."""

from collections.abc import Iterable, Sequence
from typing import Protocol


class SectionedImage(Protocol):
    section: str


class HasLabel(Protocol):
    def __call__(self, value: str) -> str: ...


def group_by_section(
    images: Iterable[SectionedImage], order: Sequence[str]
) -> list[tuple[str, list[SectionedImage]]]:
    """Bucket images into the declared section order.

    Sections with nothing in them are dropped, so a page never renders an empty
    heading. A section that is not in ``order`` keeps its images and lands at the
    end, which means a new choice in the enum cannot silently hide rows.
    """
    buckets: dict[str, list[SectionedImage]] = {name: [] for name in order}
    for image in images:
        buckets.setdefault(image.section, []).append(image)
    return [(name, items) for name, items in buckets.items() if items]
