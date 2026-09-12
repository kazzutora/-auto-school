"""Asset budget gate, REDESIGN.md C.6 and R2 point 3.

C.6 fixes the numbers; this fails the build when one of them is exceeded. It is
a gate rather than a warning on purpose — a budget that only prints a number is
a budget that is already broken by the time anybody reads it.

Run after `make css`, because it measures the built stylesheet and not the
source. In CI that ordering is the job's, in the Makefile it is the target's.
"""

from __future__ import annotations

import gzip
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

KB = 1024

# (label, paths, gzip budget in bytes, what C.6 calls it)
BUDGETS: list[tuple[str, list[str], int]] = [
    ("css", ["static/css/app.css", "static/css/motion.css"], 40 * KB),
    (
        "js",
        [
            "static/js/htmx.min.js",
            "static/js/alpine.min.js",
            "static/js/app.js",
            "static/js/motion.js",
        ],
        45 * KB,
    ),
]

# R2 and R10 point 10 cap the hand written motion script on its own at 3 KB.
# C.2 does not name a unit, and this measures gzip because every other size in
# the C.6 table is gzip — a file counted raw against a budget written in gzip
# would be the only row on a different scale. The raw size is printed beside it
# so a sudden jump is still visible: what the number is really guarding is that
# nobody has quietly vendored a library in there, and the BANNED list below
# guards the same thing by name.
MOTION_GZIP_MAX = 3 * KB

# R10 point 9: no animation library, in the stylesheet or in the scripts. The
# check is on the built files rather than on package.json because the site has
# no build step for javascript — a library would arrive as a vendored file.
BANNED = ("gsap", "framer-motion", "motion.dev", "aos.js", "animate.css", "lottie", "velocity.js")


def gzipped(path: Path) -> int:
    return len(gzip.compress(path.read_bytes(), 9))


def strip_comments(text: str) -> str:
    """Block and line comments out, so the banned-name scan reads code only.

    Crude on purpose: a `//` inside a string literal would be cut too. Nothing
    here needs to survive that, and a real parser for two file formats would be
    a great deal of machinery to answer one question.
    """
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"(?m)^\s*//.*$", " ", text)


def main() -> int:
    failures: list[str] = []

    for label, names, budget in BUDGETS:
        total = 0
        for name in names:
            path = ROOT / name
            if not path.exists():
                failures.append(f"{label}: {name} is missing — run `make css` first")
                continue
            size = gzipped(path)
            total += size
            print(f"  {name:34} {size / KB:6.1f} KB gzip")
        print(f"{label:5} total {total / KB:6.1f} KB gzip   budget {budget / KB:.0f} KB")
        if total > budget:
            failures.append(
                f"{label} is {total / KB:.1f} KB gzip, over the {budget / KB:.0f} KB budget in C.6"
            )
        print()

    motion = ROOT / "static/js/motion.js"
    if motion.exists():
        packed, raw = gzipped(motion), motion.stat().st_size
        print(
            f"motion.js {packed / KB:6.1f} KB gzip  ({raw / KB:.1f} KB raw)"
            f"   budget {MOTION_GZIP_MAX / KB:.0f} KB"
        )
        if packed > MOTION_GZIP_MAX:
            failures.append(
                f"static/js/motion.js is {packed / KB:.1f} KB gzip, "
                f"over the {MOTION_GZIP_MAX / KB:.0f} KB in C.2"
            )
    else:
        failures.append("static/js/motion.js is missing")

    for label, names, _ in BUDGETS:
        for name in names:
            path = ROOT / name
            if not path.exists():
                continue
            # Comments are stripped first. C.2 explains at length why GSAP and
            # Motion are not here, by name and with their sizes, and a scanner
            # that reads prose would fail the build over the explanation for
            # the rule it is enforcing.
            text = strip_comments(path.read_text(encoding="utf-8", errors="ignore")).lower()
            for banned in BANNED:
                if banned in text:
                    failures.append(f"{name} mentions {banned}; C.2 bans animation libraries")

    if failures:
        print("\nbudget gate failed:", file=sys.stderr)
        for line in failures:
            print(f"  - {line}", file=sys.stderr)
        return 1
    print("\nall budgets met")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
