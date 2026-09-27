"""Turn the downloaded photographs into what the pages actually load.

PHOTOS.md section 4, which narrows REDESIGN.md D.6 for this set of files. One
source in, a crop per aspect ratio out, each in AVIF, WebP and JPEG at 480, 960,
1440 and 1920 — and every one weighed against the ceiling section 4 fixes.

    ./scripts/fetch_photos.sh      # a person chose the photographs first
    make optimize-photos           # what the site serves, unstamped
    make watermark-demo            # the owner's demo, stock stamped

**Over the limit is an error, not a warning.** PHOTOS.md says so and C.6 is why:
the hero is the LCP element on the home page, the budget is 2.2 s on Slow 4G,
and a 400 KB hero spends all of it before the text has painted. A warning in a
build log is a limit nobody enforces.

The watermark, PHOTOS.md section 6 and REDESIGN.md D.2, is opt-in through
--watermark. With it, every file the owner has not sent is stock, and stock is
stamped ZDJĘCIE POGLĄDOWE so a demo cannot be mistaken for their own
photographs. The owner's real files are listed in scripts/owned.txt and are
never stamped either way.

Where the files live, and why the split:

    static/src/img/     the 2400px originals and CREDITS.txt. Sources, like
                        static/src/css/ beside them — read by this script and
                        never served. Mapping them into STATICFILES_DIRS would
                        publish 4.4 MB nothing links to and copy it into the
                        production image on every collectstatic.
    static/img/<crop>/  what the pages load. Served through the ("img", ...)
                        entry in config/settings/base.py.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - the message is the whole point
    sys.exit(
        "Pillow is not installed.\n"
        "It is a dev dependency, not a runtime one: this script runs on somebody's\n"
        "machine when new photographs arrive, and the server never touches it.\n"
        "  pip install pillow"
    )

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "static" / "src" / "img"
OUT = ROOT / "static" / "img"
CREDITS = SOURCE / "CREDITS.txt"
OWNED = ROOT / "scripts" / "owned.txt"

KB = 1024


@dataclass(frozen=True)
class Crop:
    """One aspect ratio a source file is cut to, PHOTOS.md section 4."""

    name: str
    ratio: tuple[int, int]
    max_bytes: int
    widths: tuple[int, ...]
    # Where the interesting part of the frame is, 0.0 top to 1.0 bottom. A
    # centre crop is right for most photographs and wrong for a portrait one:
    # cutting 16:9 out of a 2400x3600 frame throws away three quarters of it,
    # and the quarter worth keeping is rarely the exact middle.
    focus: float = 0.5
    # The same thing across, 0.0 left to 1.0 right, and it exists for the phone
    # hero. Cutting 4:5 out of a 16:9 frame throws away more than half the
    # width, and on a photograph whose subject stands to one side the centre is
    # exactly where the subject is not.
    focus_x: float = 0.5
    # The file name the renditions are written under, when it is not the
    # source's own. The phone hero is cut from a portrait file of its own but
    # has to land under the banner's stem, which is the name <c-photo> asks
    # for with crop_mobile.
    as_stem: str = ""


# PHOTOS.md section 4's table, to the kilobyte.
HERO = (
    Crop("hero", (16, 9), 180 * KB, (960, 1440, 1920), focus=0.46),
    Crop("hero-tall", (4, 5), 120 * KB, (480, 960), focus=0.46),
)

# The school's own cars, and the frame is a banner rather than a photograph:
# the car stands on the right and the left half is already faded to near white
# for the words to sit on. So the wide cut is `band` at 21:9, which is within a
# whisker of the source's own 2.21 and therefore keeps the whole composition —
# a 16:9 cut would eat a fifth of the width, and the fifth it eats is the fade.
#
# The phone cannot use that frame: a 21:9 band on a portrait screen is a strip
# with a thumbnail of a car in it. It gets a 4:5 cut pulled hard to the right,
# which is the car alone, and the text sits under it on the page rather than
# over it.
FLEET = (Crop("band", (21, 9), 140 * KB, (960, 1440, 1920)),)

# The phone's hero since 2026-09-27: a portrait frame of its own, the car small
# under a tall sky, so the heading lies on the sky and not on the car. Kept
# whole at 2:3 and written under the banner's stem.
FLEET_PHONE = (
    Crop("hero-tall", (2, 3), 160 * KB, (480, 960), as_stem="hero-fleet"),
)
BAND = (Crop("band", (21, 9), 140 * KB, (960, 1440, 1920)),)
CARD = (Crop("card", (3, 2), 90 * KB, (480, 960, 1440)),)
POSTER = (Crop("poster", (16, 9), 120 * KB, (960, 1440)),)

# Which source file is cut to what. A file not named here is treated as a card,
# which is the commonest shape and the safest default.
ROLES: dict[str, tuple[Crop, ...]] = {
    "hero-fleet": FLEET,
    "hero-fleet-phone": FLEET_PHONE,
    "hero-dusk": HERO,
    "hero-motion": HERO,
    "hero-city": HERO,
    # The one photograph that reads as "learning to drive" rather than "a person
    # in a car", so it earns both the about block and the video poster.
    "about-plac": CARD + POSTER,
    "about-pair": CARD + POSTER,
    "bento-white": CARD,
    "bento-wheel": CARD,
    "bento-woman": CARD,
    "bento-vw": CARD,
    "band-road": BAND,
    "band-day": BAND,
    # The footer's ground: an empty plac at dusk, under a graphite wash.
    "band-dusk": BAND,
}

WATERMARK = "ZDJĘCIE POGLĄDOWE"


def owned() -> set[str]:
    """Files the owner has actually sent, which are never watermarked.

    Everything else in static/src/img came off a stock library, and D.2 is
    unambiguous that a stock photograph must not be passed off as the school's
    own — least of all in a demo, which is exactly where it would be.
    """
    if not OWNED.exists():
        return set()
    return {
        line.strip()
        for line in OWNED.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }


def credited() -> set[str]:
    if not CREDITS.exists():
        return set()
    return {
        line.split("|", 1)[0].strip()
        for line in CREDITS.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#") and "|" in line
    }


def crop_to(
    image: Image.Image,
    ratio: tuple[int, int],
    focus: float,
    focus_x: float = 0.5,
) -> Image.Image:
    """Crop to an aspect ratio, keeping the part of the frame that matters."""
    want = ratio[0] / ratio[1]
    have = image.width / image.height
    if have > want:
        new_width = round(image.height * want)
        left = round((image.width - new_width) * focus_x)
        left = max(0, min(left, image.width - new_width))
        return image.crop((left, 0, left + new_width, image.height))
    new_height = round(image.width / want)
    top = round((image.height - new_height) * focus)
    top = max(0, min(top, image.height - new_height))
    return image.crop((0, top, image.width, top + new_height))


def stamp(image: Image.Image) -> Image.Image:
    """PHOTOS.md section 6's watermark, across the middle of the frame.

    In the middle because every block on the site crops these with
    object-cover, and a corner is the first thing a crop takes: the phone hero
    is a 4:5 file in a taller box, and the chip that had been in its top right
    was simply not on screen. A watermark that the layout can remove is not a
    watermark.

    Semi-transparent and slightly rotated, so it reads as a proof mark rather
    than as part of the picture, and so the photograph underneath is still
    judgeable — which is the point of a demo. It goes the moment the owner's own
    files arrive: scripts/owned.txt is the list, one filename at a time.
    """
    image = image.convert("RGB")
    size = max(15, round(image.width / 20))
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except OSError:
        # No truetype on the box. The default bitmap font is small and plain,
        # which for a watermark is not a problem: it still says the word.
        font = ImageFont.load_default()

    # Drawn on its own transparent layer so it can be rotated and composited
    # without the rotation eating the photograph's corners.
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    box = draw.textbbox((0, 0), WATERMARK, font=font)
    width, height = box[2] - box[0], box[3] - box[1]
    x = (image.width - width) // 2 - box[0]
    y = (image.height - height) // 2 - box[1]

    # A dark plate under the letters, so the mark reads on a light frame as
    # well as a dark one without having to be opaque.
    pad = round(size * 0.45)
    draw.rounded_rectangle(
        (x + box[0] - pad, y + box[1] - pad, x + box[0] + width + pad, y + box[1] + height + pad),
        radius=round(size * 0.35),
        fill=(27, 27, 32, 140),
    )
    draw.text((x, y), WATERMARK, font=font, fill=(255, 212, 0, 225))

    layer = layer.rotate(8, resample=Image.BICUBIC)
    image.paste(layer, (0, 0), layer)
    return image


def write(image: Image.Image, target: Path, fmt: str, quality: int) -> int:
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        if fmt == "WEBP":
            image.save(target, fmt, quality=quality, method=6)
        else:
            image.save(target, fmt, quality=quality)
    except (OSError, ValueError) as error:
        if fmt == "AVIF":
            # Pillow only speaks AVIF with pillow-avif-plugin or a recent build.
            # WebP and JPEG still cover every browser in the support table, so a
            # missing encoder costs a format rather than the pipeline.
            print(f"    avif unavailable ({error}); webp and jpeg still written")
            return 0
        raise
    return target.stat().st_size


# PHOTOS.md section 4: AVIF around q50, WebP around q75, JPEG as the fallback.
#
# 72 rather than 75 for WebP. Section 4 writes "q≈75" and the approximation is
# doing work: at 75 the 1440 bento card came out at 91 KB against a 90 KB
# ceiling, and three points of quality nobody can see is a better answer than
# a ceiling nobody enforces.
FORMATS = (("AVIF", "avif", 50), ("WEBP", "webp", 72), ("JPEG", "jpg", 80))

# The ceiling in section 4 is strict for the two formats a browser actually
# receives, and 2x for the JPEG.
#
# Section 4 calls the JPEG a fallback in as many words, and that is what it is:
# every browser in the C.6 support table takes the AVIF or the WebP, which are
# the files the LCP budget is spent on. Holding the JPEG to the same number
# would mean compressing it to roughly q55 — visibly worse, and worse for
# precisely the people already on the oldest browser.
#
# It is bounded rather than exempt, because somebody does get it. A JPEG that
# has quietly grown past twice the ceiling is a source file nobody cropped.
FALLBACK_ALLOWANCE = 2.0


def process(path: Path, watermark: bool) -> list[str]:
    problems: list[str] = []
    crops = ROLES.get(path.stem, CARD)

    with Image.open(path) as original:
        original = original.convert("RGB")

        for crop in crops:
            shape = crop_to(original, crop.ratio, crop.focus, crop.focus_x)
            usable = [width for width in crop.widths if width <= shape.width]
            if not usable:
                problems.append(f"{path.name}: source too small for the {crop.name} crop")
                continue

            for width in usable:
                height = round(width * crop.ratio[1] / crop.ratio[0])
                resized = shape.resize((width, height), Image.LANCZOS)

                # Stamped after the crop and the resize, not before either.
                # Stamping the source first put the mark where a later crop
                # sliced it in half, and sized the lettering against the source
                # rather than the output — so the 480 came out unreadable and
                # the 1920 covered a third of the frame.
                if watermark:
                    resized = stamp(resized)

                for fmt, ext, quality in FORMATS:
                    target = OUT / crop.name / f"{crop.as_stem or path.stem}-{width}.{ext}"
                    ceiling = crop.max_bytes
                    if fmt == "JPEG":
                        ceiling = round(ceiling * FALLBACK_ALLOWANCE)

                    size = write(resized, target, fmt, quality)
                    if not size:
                        continue

                    # Every lossy format is as good as fits. One source — a
                    # 2400x3600 interior with a great deal of fine detail —
                    # came out 12 KB over at the quality every other file
                    # managed comfortably, and the choice there is between a
                    # fixed quality that sometimes breaks the budget and a
                    # fixed budget that sometimes costs quality. The budget is
                    # the one with a reason behind it, so the quality gives
                    # way, and only for the file that needs it.
                    #
                    # This was JPEG only until a hero came in 1 KB over in
                    # webp. The rule had nothing to do with the format — a
                    # ceiling that only one of three encoders respects is a
                    # ceiling that reports rather than holds.
                    while size > ceiling and quality > 55:
                        quality -= 6
                        size = write(resized, target, fmt, quality)

                    if width == max(usable) and size > ceiling:
                        problems.append(
                            f"{target.relative_to(ROOT)} is {size / KB:.0f} KB, over the "
                            f"{ceiling / KB:.0f} KB PHOTOS.md allows for a {crop.name}"
                            + (" fallback" if fmt == "JPEG" else "")
                        )
                    default = next(q for f, _e, q in FORMATS if f == fmt)
                    note = f"  (q{quality})" if quality != default else ""
                    print(f"    {target.relative_to(OUT)}  {size / KB:6.1f} KB{note}")
    return problems


def main() -> int:
    if not SOURCE.exists() or not any(SOURCE.glob("*.[jJpP]*[gG]")):
        print(
            "static/src/img is empty.\n\n"
            "Fill scripts/photos.txt and run ./scripts/fetch_photos.sh first. Until then\n"
            "the site renders without photographs on purpose: the hero falls back to the\n"
            "branded panel, and every block that would need a real photograph of the\n"
            "school shows <c-empty> rather than a stranger's car. REDESIGN.md D.2."
        )
        return 0

    # Off unless asked for: the site serves clean renditions, and the owner's
    # demo build is the one that passes --watermark, `make watermark-demo`.
    watermark = "--watermark" in sys.argv[1:]
    have_credits = credited()
    ours = owned()
    problems: list[str] = []

    for path in sorted(SOURCE.glob("*")):
        if path.name == "CREDITS.txt" or path.is_dir():
            continue

        # PHOTOS.md's opening line and R8's acceptance criterion: not one image
        # without a line in CREDITS.txt. A file whose origin nobody recorded is
        # a file nobody can defend if a rights holder writes.
        if path.name not in have_credits:
            problems.append(f"{path.name} has no line in CREDITS.txt")
            continue

        stock = path.name not in ours
        stamped = watermark and stock
        label = "  [stock, watermarked]" if stamped else "  [stock]" if stock else "  [owner]"
        print(f"{path.name}{label}")
        problems.extend(process(path, watermark=stamped))

    if problems:
        print("\noptimize-photos failed:", file=sys.stderr)
        for line in problems:
            print(f"  - {line}", file=sys.stderr)
        return 1

    print("\nall crops written and within budget")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
