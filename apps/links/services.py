"""Pure domain logic for the links slice. No ORM here."""

from collections.abc import Iterable, Sequence
from typing import Protocol


class Grouped(Protocol):
    group: str


class GroupedLink(Grouped, Protocol):
    description: str


def publishable(links: Iterable[GroupedLink]) -> list[GroupedLink]:
    """Drop anything that would render as a bare url.

    The description is mandatory on the model, so this only catches rows that
    got in around it: a data migration, a fixture, a direct update. tech.md
    section 4.6 is explicit that a link with no explanation is not published.
    """
    return [link for link in links if (link.description or "").strip()]


def group_links(
    links: Iterable[GroupedLink], order: Sequence[str]
) -> list[tuple[str, list[GroupedLink]]]:
    """Bucket links into the declared group order.

    Empty groups are dropped, so the page never renders a heading with nothing
    under it. A group missing from order keeps its links and lands at the end,
    which means a new choice in the enum cannot hide rows.
    """
    buckets: dict[str, list[GroupedLink]] = {name: [] for name in order}
    for link in links:
        buckets.setdefault(link.group, []).append(link)
    return [(name, items) for name, items in buckets.items() if items]


def group_questions[GroupedT: Grouped](
    questions: Iterable[GroupedT],
) -> list[tuple[str, list[GroupedT]]]:
    """Bucket questions by their group, in the order the owner put them in.

    Unlike links, a faq group is free text, so there is no declared order to
    follow: a group appears where its first question does. Questions with no
    group form one bucket with an empty label, and the page leaves it unheaded.
    """
    buckets: dict[str, list[GroupedT]] = {}
    for question in questions:
        buckets.setdefault((question.group or "").strip(), []).append(question)
    return list(buckets.items())
