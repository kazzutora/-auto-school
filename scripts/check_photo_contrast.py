"""Text over a photograph, measured on the rendered page. PHOTOS.md section 3.

Section 3 states the rule for the common case — white text needs a ground no
lighter than #767676 — and describes checking it with five eyedropper samples.
This does the same thing exhaustively, and generally:

  1. find every text node whose ground is a photograph, and read the colour the
     browser actually paints it in;
  2. make the text itself transparent and screenshot again, so what is left in
     each box is the ground and nothing else;
  3. take the worst pixel in that box — lightest for dark text, darkest for
     light text — and measure the real contrast against it.

Measuring the ground rather than assuming white text is what makes it right on
the one element section 3 singles out: the yellow slab under KAT. B carries
near-black text, so the bright pixels there are correct rather than a failure.
Five eyedropper points would also miss a bright window between them, and a
bright window is exactly what a photograph has.

    python scripts/check_photo_contrast.py            # against localhost:8000
    python scripts/check_photo_contrast.py http://...

What it cannot do is judge whether the picture still reads as a picture. That is
the other half of section 2 and it needs eyes.
"""

from __future__ import annotations

import io
import re
import sys

try:
    from PIL import Image
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sys.exit("needs pillow and playwright: this runs in the web container")

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

# WCAG 2.2 1.4.3. Large text is 24px, or 18.66px bold.
BODY_MIN = 4.5
LARGE_MIN = 3.0

# 390 is the phone the visitor arrives on. 1440 is where the desktop scrim is
# weakest: the gradient has the most width to fade across, so the right hand
# stop lands furthest from the text.
VIEWPORTS = ((390, 844), (768, 1024), (1440, 900), (1920, 1080))

COLLECT = """() => {
    const out = [];
    for (const ground of document.querySelectorAll('.u-photo-ground, .u-over-photo')) {
        // Leaves only: a wrapper's box covers its children and would drag in
        // the empty half of the hero, where there is no text and the scrim is
        // deliberately transparent.
        for (const el of ground.querySelectorAll('*')) {
            if (el.closest('[aria-hidden="true"]')) continue;
            if (!el.textContent.trim() || el.children.length) continue;
            const r = el.getBoundingClientRect();
            if (r.width < 2 || r.height < 2) continue;
            if (r.bottom < 0 || r.top > window.innerHeight) continue;

            // Skip anything another element is painting over. The cookie
            // banner is fixed to the bottom with an opaque white background,
            // and at 390px it covers the hero's buttons — so the box measured
            // there was the banner's white, not the photograph, and reported a
            // 1.00:1 failure about two elements that never touch.
            const cx = Math.min(window.innerWidth - 1, Math.max(0, r.left + r.width / 2));
            const cy = Math.min(window.innerHeight - 1, Math.max(0, r.top + r.height / 2));
            const top = document.elementFromPoint(cx, cy);
            if (!top || !(top === el || el.contains(top) || top.contains(el))) continue;
            const cs = getComputedStyle(el);
            out.push({
                text: el.textContent.trim().slice(0, 30),
                x: Math.round(r.left), y: Math.round(r.top),
                w: Math.round(r.width), h: Math.round(r.height),
                colour: cs.color,
                // An outlined heading is paper filled with a crimson
                // keyline, so the fill is within a hair of the page and the
                // whole of what a reader sees is the stroke. Which colour
                // has to clear the threshold depends on which one is
                // actually drawing the letter.
                stroke: cs.webkitTextStrokeColor,
                strokeWidth: parseFloat(cs.webkitTextStrokeWidth) || 0,
                size: parseFloat(cs.fontSize),
                weight: parseInt(cs.fontWeight, 10) || 400,
            });
        }
    }
    return out;
}"""

# Everything inside a photo ground goes transparent, glyphs and icons alike, so
# the screenshot shows the ground on its own. The backgrounds stay: the yellow
# slab has to remain, because it IS the ground for the word on it.
HIDE_TEXT = """() => {
    const style = document.createElement('style');
    style.textContent = `
      .u-photo-ground, .u-photo-ground *,
      .u-over-photo, .u-over-photo * {
        color: transparent !important;
        text-decoration-color: transparent !important;
        /* The keyline is part of the letter, not part of the ground behind
         * it. Headings are paper filled with a crimson stroke since core
         * v31, and a stroke is its own property: setting color alone left
         * it standing, so the gate sampled a heading's own outline as the
         * background of the line beside it and reported crimson on crimson
         * at 1.00. */
        -webkit-text-stroke-color: transparent !important;
      }
      .u-photo-ground svg, .u-over-photo svg { visibility: hidden !important; }

      /* The cookie banner is an overlay, not a ground. It is fixed to the
       * bottom of the viewport and its own text is outside every photo
       * region, so it stays opaque here while the measured text does not —
       * and a box whose lower edge reaches the banner had the banner's dark
       * paragraph sampled as the thing behind it. The centre-point guard
       * above only catches a block the banner covers entirely.
       *
       * It is display:none rather than transparent because what has to be
       * measured is the page underneath it, which is what the reader sees the
       * moment the banner is dismissed. */
      [data-cookie-banner] { display: none !important; }

      /* The scribble belongs to the word, not to what is behind it. It is
       * painted as a background on ::after, so making the text transparent
       * leaves it standing, and .script is rotated — its axis aligned box
       * contains its own stroke at any offset. The measurement that came back
       * was the crimson stroke against crimson text, 1.00:1, about a word
       * sitting on a pale field at 12:1. */
      .u-scribbled::after { content: none !important; }
    `;
    document.head.appendChild(style);
}"""


def luminance(rgb: tuple[int, int, int]) -> float:
    channels = []
    for value in rgb:
        c = value / 255
        channels.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = channels
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def parse(colour: str) -> tuple[int, int, int]:
    """The first three numbers of an rgb() or rgba() string.

    A regex rather than splitting on spaces: getComputedStyle returns
    "rgb(255, 255, 255)" with the brackets attached to the first and last
    numbers, and "rgba(27, 27, 32, 0.75)" has a fourth that is not a channel.
    """
    numbers = re.findall(r"[\d.]+", colour)
    return (int(float(numbers[0])), int(float(numbers[1])), int(float(numbers[2])))


def main() -> int:
    failures: list[str] = []
    checked = 0

    with sync_playwright() as play:
        browser = play.chromium.launch()
        for width, height in VIEWPORTS:
            context = browser.new_context(
                viewport={"width": width, "height": height},
                reduced_motion="reduce",  # nothing mid-fade while we measure
            )
            page = context.new_page()
            page.goto(BASE + "/", wait_until="load")
            page.wait_for_timeout(400)

            nodes = page.evaluate(COLLECT)
            page.evaluate(HIDE_TEXT)
            page.wait_for_timeout(120)
            shot = Image.open(io.BytesIO(page.screenshot())).convert("RGB")

            for node in nodes:
                box = (
                    max(0, node["x"]),
                    max(0, node["y"]),
                    min(shot.width, node["x"] + node["w"]),
                    min(shot.height, node["y"] + node["h"]),
                )
                if box[2] <= box[0] or box[3] <= box[1]:
                    continue
                checked += 1

                # The stroke is the foreground wherever there is one: the
                # fill of an outlined heading is paper on a pale page and
                # carries nothing, which is the point of outlining it.
                stroked = node.get("strokeWidth", 0) >= 0.5
                text = parse(node["stroke"] if stroked else node["colour"])
                large = node["size"] >= 24 or (node["size"] >= 18.66 and node["weight"] >= 700)
                floor = LARGE_MIN if large else BODY_MIN

                # The worst pixel in the box, not the average: one bright window
                # behind two letters is exactly the defect this is looking for.
                pixels = list(shot.crop(box).getdata())
                worst = min(pixels, key=lambda pixel: ratio(text, pixel))
                found = ratio(text, worst)

                if found < floor:
                    failures.append(
                        f"{width:>5}px  {node['text']!r}\n"
                        f"          {'keyline' if stroked else 'text'} "
                        f"{node['stroke'] if stroked else node['colour']} "
                        f"on #{worst[0]:02X}{worst[1]:02X}"
                        f"{worst[2]:02X} is {found:.2f}:1, needs {floor}"
                    )
            context.close()
        browser.close()

    print(f"{checked} text blocks measured over photographs across {len(VIEWPORTS)} viewports")
    if failures:
        print("\nPHOTOS.md section 3 failed — the scrim is too weak:", file=sys.stderr)
        for line in failures:
            print(f"  - {line}", file=sys.stderr)
        return 1
    print("every one clears its threshold against the worst pixel behind it")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
