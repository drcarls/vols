"""Read the value out of a cropped image, and parse period French numbers.

Two independent concerns:

* :func:`parse_french_number` turns an OCR string into a :class:`Decimal`,
  handling the period conventions of Le Temps' finance page: comma decimal
  separator, ``.``/space thousands separators, and rente rows quoted in eighths
  or fractions (``83 1/2`` -> ``83.5``).

* :class:`TesseractExtractor` OCRs a cropped region. It is optional: it lazily
  imports :mod:`pytesseract`/:mod:`PIL`, so the locate-and-crop pipeline runs
  without an OCR install. Any object with ``extract(image_bytes) -> str`` can be
  used instead.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Optional, Protocol


class Extractor(Protocol):
    def extract(self, image_bytes: bytes) -> str: ...


_FRACTION_RE = re.compile(r"^(\d+)\s+(\d+)\s*/\s*(\d+)$")
_NUMBER_TOKEN_RE = re.compile(r"[0-9][0-9.,\s/]*[0-9]|[0-9]")


def parse_french_number(text: str) -> Optional[Decimal]:
    """Parse a period-French numeric string into a :class:`Decimal`.

    Examples::

        "84,25"     -> Decimal("84.25")
        "1.234,50"  -> Decimal("1234.50")
        "1 234"     -> Decimal("1234")
        "83 1/2"    -> Decimal("83.5")
        "0/0"       -> None   (a per-cent mark, not a value)

    Returns ``None`` when nothing numeric can be recovered.
    """
    if text is None:
        return None
    s = text.strip().replace(" ", " ")
    if not s:
        return None

    # Mixed fraction like "83 1/2" or "83 3/8" (rente eighths).
    m = _FRACTION_RE.match(s)
    if m:
        whole, num, den = (int(g) for g in m.groups())
        if den == 0:
            return None
        return Decimal(whole) + (Decimal(num) / Decimal(den))

    # A bare fraction such as "0/0" is a per-cent mark, not a quotation.
    if re.fullmatch(r"\d+\s*/\s*\d+", s):
        return None

    cleaned = s
    if "," in cleaned:
        # Comma is the decimal separator; '.' and spaces are thousands groupers.
        cleaned = cleaned.replace(".", "").replace(" ", "").replace(",", ".")
    else:
        # No comma: treat '.' and spaces as thousands separators only when they
        # group triples (e.g. "1.234", "12 500"); otherwise keep a lone '.'.
        if re.fullmatch(r"\d{1,3}([.\s]\d{3})+", cleaned):
            cleaned = cleaned.replace(".", "").replace(" ", "")
        else:
            cleaned = cleaned.replace(" ", "")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def first_number(text: str) -> Optional[Decimal]:
    """Return the first parseable French number found anywhere in ``text``."""
    for token in _NUMBER_TOKEN_RE.findall(text or ""):
        value = parse_french_number(token)
        if value is not None:
            return value
    return None


class TesseractExtractor:
    """OCR a cropped region with Tesseract, tuned for numeric quotations.

    ``psm=7`` treats the crop as a single text line; the character whitelist
    keeps Tesseract to the glyphs that appear in a price ("0-9 , . / space").
    """

    def __init__(
        self,
        *,
        lang: str = "fra",
        psm: int = 7,
        whitelist: str = "0123456789.,/ ",
    ) -> None:
        self._lang = lang
        self._config = (
            f"--psm {psm} -c tessedit_char_whitelist={whitelist}"
            if whitelist
            else f"--psm {psm}"
        )

    def extract(self, image_bytes: bytes) -> str:
        import io

        import pytesseract  # lazy: only needed when OCR is actually used
        from PIL import Image

        image = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(
            image, lang=self._lang, config=self._config
        ).strip()
