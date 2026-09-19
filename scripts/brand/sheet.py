"""The contact sheet for the logo kit, ROSE.md K1 step 5.

    python -m scripts.brand.sheet

Writes .local/brand-sheet.html: every version of the mark beside the owner's
own file, on the light ground, on the dark one, and the favicon at 16, 32, 48
and 96px. The point of the sheet is the comparison — a mark that reads on its
own can still be the wrong mark — so the owner's raster sits in the first row
at the same width as ours in the second.

The file is written to .local/ because it is a proof, not an asset: it inlines
the sources as data uris and weighs half a megabyte. Serve it with

    python -m http.server 8899 --bind 127.0.0.1 --directory .local

and screenshot it for the pull request.
"""

from __future__ import annotations

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRAND = ROOT / "static" / "img" / "brand"
SOURCE = BRAND / "source"
OUT = ROOT / ".local" / "brand-sheet.html"

STYLE = """
body{margin:0;font:13px/1.45 system-ui,sans-serif;background:#fff;color:#221B1E}
h2{font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:#9C8A91;
   margin:0 0 12px;font-weight:700}
.row{padding:22px 28px;border-bottom:1px solid #EBD3D9}
.dark{background:#1A1417;color:#F6E9EC;border-color:#332428}
.ground{background:#FBEDEF}
.paper{background:#FFFBFA}
.box{display:flex;gap:34px;align-items:center;flex-wrap:wrap}
.fav{display:flex;gap:28px;align-items:flex-end}
.fav figure{margin:0;text-align:center}
.fav figcaption{color:#9C8A91;font-size:10px;margin-top:6px}
img{display:block}
svg{display:block}
"""


def data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def sized(name: str, style: str) -> str:
    svg = (BRAND / name).read_text(encoding="utf-8")
    return svg.replace("<svg", f'<svg style="{style}"', 1)


def main() -> int:
    rows = []

    rows.append(
        '<div class="row"><h2>owner — logo-light.png</h2>'
        f'<img src="{data_uri(SOURCE / "logo-light.png")}" style="width:585px"></div>'
    )
    rows.append(
        '<div class="row ground"><h2>ours — logo-full.svg, same width</h2>'
        f'<div style="width:585px">{sized("logo-full.svg", "width:100%;height:auto")}'
        "</div></div>"
    )
    rows.append(
        '<div class="row ground"><h2>logo-compact.svg — the site header, '
        "40px and 64px high</h2><div class=box>"
        f"{sized('logo-compact.svg', 'height:40px;width:auto')}"
        f"{sized('logo-compact.svg', 'height:64px;width:auto')}</div></div>"
    )
    rows.append(
        '<div class="row dark"><h2>logo-full-dark.svg on #1A1417</h2>'
        f'<div style="width:585px">'
        f"{sized('logo-full-dark.svg', 'width:100%;height:auto')}</div></div>"
    )
    rows.append(
        '<div class="row dark"><h2>owner — logo-dark.png</h2>'
        f'<img src="{data_uri(SOURCE / "logo-dark.png")}" style="width:585px"></div>'
    )
    rows.append(
        '<div class="row ground"><h2>mark-wheel.svg · mark-l.svg · '
        "the owner's file at the same height</h2><div class=box>"
        f"{sized('mark-wheel.svg', 'height:120px;width:auto')}"
        f"{sized('mark-l.svg', 'height:120px;width:auto')}"
        f'<img src="{data_uri(SOURCE / "logo-light.png")}" style="height:120px">'
        "</div></div>"
    )

    fav = "".join(
        f"<figure>{sized('favicon.svg', f'height:{s}px;width:auto')}"
        f"<figcaption>{s}px</figcaption></figure>"
        for s in (16, 32, 48, 96)
    )
    rows.append(f'<div class="row paper"><h2>favicon.svg</h2><div class=fav>{fav}</div></div>')

    html = (
        "<!doctype html><html lang=pl><head><meta charset=utf-8>"
        "<title>OSK Ostrycharz — logo kit</title>"
        f"<style>{STYLE}</style></head><body>{''.join(rows)}</body></html>"
    )
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}  {len(html) / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
