"""IIIF Image API: scale ALTO coordinates and build crop URLs.

Gallica serves the IIIF Image API at::

    https://gallica.bnf.fr/iiif/ark:/12148/<ark>/f<page>/<region>/<size>/<rot>/<quality>.<fmt>

``<region>`` is ``x,y,w,h`` in pixels of the *full* IIIF image. ALTO coordinates
live in the ALTO ``<Page>`` space, which can differ in resolution from the IIIF
full image, so we rescale by the ratio of the two dimensions (read from the
page's ``info.json``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .locate import Region

IIIF_BASE = "https://gallica.bnf.fr/iiif/ark:/12148"


@dataclass(frozen=True)
class PixelRegion:
    """A crop region in IIIF full-image pixel coordinates."""

    x: int
    y: int
    w: int
    h: int

    def as_iiif(self) -> str:
        return f"{self.x},{self.y},{self.w},{self.h}"


def info_url(ark: str, page: int, *, base: str = IIIF_BASE) -> str:
    """URL of the ``info.json`` describing the full IIIF image for a page."""
    return f"{base}/{ark}/f{page}/info.json"


def full_size_from_info(info: dict) -> "tuple[int, int]":
    """Return ``(width, height)`` of the full IIIF image from an ``info.json`` dict."""
    return int(info["width"]), int(info["height"])


def scale_region(
    region: Region,
    iiif_width: int,
    iiif_height: int,
    *,
    clamp: bool = True,
) -> PixelRegion:
    """Scale an ALTO :class:`Region` into IIIF full-image pixel coordinates.

    The scale factors are ``iiif_width / page_width`` and
    ``iiif_height / page_height``. If the ALTO page dimensions are unknown (0),
    the region is assumed to already be in IIIF space (scale 1).
    """
    sx = iiif_width / region.page_width if region.page_width else 1.0
    sy = iiif_height / region.page_height if region.page_height else 1.0

    x = int(round(region.hpos * sx))
    y = int(round(region.vpos * sy))
    w = int(round(region.width * sx))
    h = int(round(region.height * sy))

    if clamp:
        x = max(0, min(x, iiif_width))
        y = max(0, min(y, iiif_height))
        w = max(1, min(w, iiif_width - x))
        h = max(1, min(h, iiif_height - y))
    return PixelRegion(x=x, y=y, w=w, h=h)


def crop_url(
    ark: str,
    page: int,
    region: PixelRegion,
    *,
    size: str = "full",
    rotation: int = 0,
    quality: str = "native",
    fmt: str = "jpg",
    base: str = IIIF_BASE,
) -> str:
    """Build a IIIF Image API URL cropping ``region`` from page ``page``.

    ``size`` defaults to ``full`` (native resolution of the crop). Use e.g.
    ``"400,"`` to request a fixed 400px-wide rendering.
    """
    return (
        f"{base}/{ark}/f{page}/{region.as_iiif()}/{size}/{rotation}/{quality}.{fmt}"
    )


def region_crop_url(
    ark: str,
    page: int,
    region: Region,
    iiif_width: int,
    iiif_height: int,
    *,
    size: str = "full",
    **kwargs,
) -> str:
    """Convenience: scale an ALTO :class:`Region` and return its crop URL."""
    pixel = scale_region(region, iiif_width, iiif_height)
    return crop_url(ark, page, pixel, size=size, **kwargs)
