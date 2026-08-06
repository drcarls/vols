"""Locate a target value in the ALTO word boxes by its text anchor.

The extraction is *locate-with-text*: we do not trust the raw OCR of the number
itself. Instead we find a reliable textual anchor (a label such as "Banque de
France", or the start of a rente row like "3 0/0"), then take the value token(s)
that follow it on the same line and return the bounding box to crop.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import List, Optional, Sequence

from .alto import WordBox


def normalize(text: str) -> str:
    """Casefold and strip diacritics for tolerant matching of OCR'd French.

    "Banque" -> "banque", "3 0/0" keeps its digits, accents are dropped so that
    a mis-OCR'd "Federe"/"Fédéré" still matches.
    """
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    return without_accents.casefold().strip()


@dataclass(frozen=True)
class Region:
    """An axis-aligned bounding box in ALTO page coordinates."""

    hpos: int
    vpos: int
    width: int
    height: int
    page_width: int
    page_height: int
    words: Sequence[WordBox] = ()

    @property
    def text(self) -> str:
        return " ".join(w.content for w in self.words)


def bounding_region(words: Sequence[WordBox]) -> Region:
    """Return the minimal :class:`Region` enclosing ``words``."""
    if not words:
        raise ValueError("cannot build a region from zero words")
    left = min(w.hpos for w in words)
    top = min(w.vpos for w in words)
    right = max(w.right for w in words)
    bottom = max(w.bottom for w in words)
    return Region(
        hpos=left,
        vpos=top,
        width=right - left,
        height=bottom - top,
        page_width=words[0].page_width,
        page_height=words[0].page_height,
        words=tuple(words),
    )


def find_anchor(
    words: Sequence[WordBox], phrase: str
) -> List[List[WordBox]]:
    """Find every run of consecutive same-line tokens matching ``phrase``.

    Matching is diacritic- and case-insensitive and compares token-by-token, so
    ``"Banque de France"`` matches the three tokens ``Banque`` ``de`` ``France``
    appearing in order on one line. Returns a list of matches, each a list of the
    matched :class:`WordBox` tokens.
    """
    targets = [normalize(t) for t in phrase.split()]
    if not targets:
        return []
    matches: List[List[WordBox]] = []

    # Group by line, preserving in-line order (already sorted by alto.parse_alto).
    by_line: dict = {}
    for w in words:
        by_line.setdefault(w.line_id, []).append(w)

    for line_words in by_line.values():
        norm = [normalize(w.content) for w in line_words]
        n = len(targets)
        for i in range(0, len(line_words) - n + 1):
            if norm[i : i + n] == targets:
                matches.append(line_words[i : i + n])
    return matches


_NUMERIC_RE = re.compile(r"\d")


def _is_numeric_token(content: str) -> bool:
    """A token counts as a value token if it contains a digit.

    This admits quotations like ``84,25``, ``1.234``, ``83`` and fraction marks
    such as ``0/0`` (the period-era way of writing "per cent") are handled by the
    caller via ``max_tokens``.
    """
    return bool(_NUMERIC_RE.search(content))


def value_after_anchor(
    words: Sequence[WordBox],
    anchor: Sequence[WordBox],
    *,
    max_tokens: int = 1,
    skip_tokens: int = 0,
) -> Optional[List[WordBox]]:
    """Return the value token(s) following ``anchor`` on the same line.

    Starting immediately after the anchor's last token, ``skip_tokens`` non-value
    tokens are ignored, then up to ``max_tokens`` numeric tokens are collected.
    Returns ``None`` if no numeric token is found on the line.
    """
    if not anchor:
        return None
    line_id = anchor[-1].line_id
    last_order = anchor[-1].order
    line_words = sorted(
        (w for w in words if w.line_id == line_id), key=lambda w: w.order
    )
    following = [w for w in line_words if w.order > last_order]

    skipped = 0
    collected: List[WordBox] = []
    for w in following:
        if not _is_numeric_token(w.content):
            if collected:
                break  # a non-numeric token ends the value run
            if skipped < skip_tokens:
                skipped += 1
                continue
            # Non-numeric filler before we reach the number: keep scanning until
            # skip budget exhausted; if no budget, stop only once we hit a number.
            continue
        collected.append(w)
        if len(collected) >= max_tokens:
            break
    return collected or None


def locate_value(
    words: Sequence[WordBox],
    anchor_phrases: Sequence[str],
    *,
    max_tokens: int = 1,
    skip_tokens: int = 0,
    include_anchor: bool = False,
    pad_ratio: float = 0.0,
) -> Optional[Region]:
    """Locate the value for the first anchor phrase that matches.

    ``anchor_phrases`` are tried in order (useful when OCR spells a label several
    ways). ``include_anchor`` widens the crop to include the anchor tokens too,
    which helps a human verify the crop. ``pad_ratio`` grows the region by that
    fraction of its own height on each side.
    """
    for phrase in anchor_phrases:
        for anchor in find_anchor(words, phrase):
            value_words = value_after_anchor(
                words, anchor, max_tokens=max_tokens, skip_tokens=skip_tokens
            )
            if not value_words:
                continue
            region_words = (list(anchor) + value_words) if include_anchor else value_words
            region = bounding_region(region_words)
            if pad_ratio:
                region = pad_region(region, pad_ratio)
            return region
    return None


def pad_region(region: Region, pad_ratio: float) -> Region:
    """Grow ``region`` by ``pad_ratio`` of its height on every side, clamped to page."""
    pad = int(round(region.height * pad_ratio))
    left = max(0, region.hpos - pad)
    top = max(0, region.vpos - pad)
    right = region.hpos + region.width + pad
    bottom = region.vpos + region.height + pad
    if region.page_width:
        right = min(region.page_width, right)
    if region.page_height:
        bottom = min(region.page_height, bottom)
    return Region(
        hpos=left,
        vpos=top,
        width=right - left,
        height=bottom - top,
        page_width=region.page_width,
        page_height=region.page_height,
        words=region.words,
    )
