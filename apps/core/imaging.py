"""WebP renditions, tech.md section 6.

Specs are built against a file rather than declared on a model on purpose.
tech.md section 7 freezes the <c-picture> prop as an ImageField, so the component
only ever holds the file, never the row it came from. Building the spec from the
file keeps that contract and gives every image field in the project the same
pipeline for free.
"""

from typing import Any

from imagekit import ImageSpec, register
from imagekit.cachefiles import ImageCacheFile
from imagekit.processors import ResizeToFit

# tech.md section 6: WebP 480, 960 and 1600.
RENDITION_WIDTHS = (480, 960, 1600)


class _WebP(ImageSpec):
    format = "WEBP"
    options = {"quality": 82}  # noqa: RUF012 - imagekit reads this as a plain dict


class WebP480(_WebP):
    processors = (ResizeToFit(480, upscale=False),)


class WebP960(_WebP):
    processors = (ResizeToFit(960, upscale=False),)


class WebP1600(_WebP):
    processors = (ResizeToFit(1600, upscale=False),)


SPECS: dict[int, type[ImageSpec]] = {480: WebP480, 960: WebP960, 1600: WebP1600}

# Registration is not optional. imagekit's registry only dispatches the
# cachefile strategy for generators it knows about, so an unregistered spec
# silently hands out a url for a file it never generates.
for _width, _spec in SPECS.items():
    register.generator(f"core:webp_{_width}", _spec)


def rendition(source: Any, width: int) -> ImageCacheFile:
    """The WebP cache file for one width."""
    return ImageCacheFile(SPECS[width](source=source))


def renditions(source: Any) -> list[tuple[int, ImageCacheFile]]:
    """Every width, narrowest first."""
    return [(width, rendition(source, width)) for width in RENDITION_WIDTHS]


def webp_srcset(source: Any) -> str:
    """A srcset string for <source type="image/webp">.

    Empty for anything that is not a stored file. A plain url, a data uri or
    a stand-in object has nothing to resize, and the caller falls back to the
    <img> on its own.
    """
    if not source or not getattr(source, "name", None):
        return ""
    return ", ".join(f"{file.url} {width}w" for width, file in renditions(source))
