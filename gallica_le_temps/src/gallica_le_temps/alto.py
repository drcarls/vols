"""ALTO parsing: word-level bounding boxes for a Gallica page.

Gallica exposes ALTO XML per page via ``RequestDigitalElement``::

    https://gallica.bnf.fr/RequestDigitalElement?O=<ark>&E=ALTO&Deb=<page>

ALTO records every OCR'd token as a ``<String>`` with ``HPOS``/``VPOS`` (top-left
corner) and ``WIDTH``/``HEIGHT`` in the page's coordinate space. We flatten those
into :class:`WordBox` objects, remembering the enclosing ``<Page>`` dimensions
(needed later to scale into IIIF image space) and a per-line id (so callers can
ask for "the next token on the same line as the anchor").
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
from xml.etree import ElementTree as ET

from .xmlutil import iter_local, local_name


def alto_url(ark: str, page: int, *, base_url: str = "https://gallica.bnf.fr") -> str:
    """Build the ``RequestDigitalElement`` ALTO URL for ``ark`` page ``page``."""
    return f"{base_url}/RequestDigitalElement?O={ark}&E=ALTO&Deb={page}"


@dataclass(frozen=True)
class WordBox:
    """One OCR'd token and its bounding box in ALTO page coordinates."""

    content: str
    hpos: int
    vpos: int
    width: int
    height: int
    page_width: int
    page_height: int
    line_id: int
    order: int  # index of the token within its line (left-to-right)

    @property
    def right(self) -> int:
        return self.hpos + self.width

    @property
    def bottom(self) -> int:
        return self.vpos + self.height

    @property
    def cx(self) -> float:
        return self.hpos + self.width / 2

    @property
    def cy(self) -> float:
        return self.vpos + self.height / 2


def _int_attr(el: ET.Element, name: str) -> Optional[int]:
    raw = el.get(name)
    if raw is None:
        return None
    try:
        # ALTO coordinates are integers but some producers emit floats.
        return int(round(float(raw)))
    except ValueError:
        return None


def parse_alto(xml_text: str) -> List[WordBox]:
    """Parse ALTO XML into a flat, reading-order list of :class:`WordBox`.

    Only the first ``<Page>`` is used (Gallica serves one page per ALTO file).
    Tokens are ordered by their line's vertical position, then left-to-right
    within the line.
    """
    root = ET.fromstring(xml_text)

    page = next(iter_local(root, "Page"), None)
    if page is None:
        return []
    page_width = _int_attr(page, "WIDTH") or 0
    page_height = _int_attr(page, "HEIGHT") or 0

    # Collect lines with their vertical position so we can order top-to-bottom.
    lines: List[tuple] = []  # (vpos_for_sort, [String elements in doc order])
    for line in iter_local(page, "TextLine"):
        strings = [s for s in line if local_name(s.tag) == "String"]
        if not strings:
            continue
        vpos = _int_attr(line, "VPOS")
        if vpos is None:
            vpos = min((_int_attr(s, "VPOS") or 0) for s in strings)
        lines.append((vpos, strings))

    lines.sort(key=lambda pair: pair[0])

    words: List[WordBox] = []
    for line_id, (_vpos, strings) in enumerate(lines):
        # Order tokens left-to-right within the line.
        strings.sort(key=lambda s: _int_attr(s, "HPOS") or 0)
        for order, s in enumerate(strings):
            content = s.get("CONTENT")
            hpos = _int_attr(s, "HPOS")
            vpos = _int_attr(s, "VPOS")
            width = _int_attr(s, "WIDTH")
            height = _int_attr(s, "HEIGHT")
            if content is None or None in (hpos, vpos, width, height):
                continue
            words.append(
                WordBox(
                    content=content,
                    hpos=hpos,
                    vpos=vpos,
                    width=width,
                    height=height,
                    page_width=page_width,
                    page_height=page_height,
                    line_id=line_id,
                    order=order,
                )
            )
    return words
