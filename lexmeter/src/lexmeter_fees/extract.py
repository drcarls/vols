"""Turning what a page displays into fee lines.

Extraction is split in two on purpose. Locating the elements is a live-DOM job
and belongs to Playwright (capture.py); deciding what the located text *means* is
pure logic and lives here, where it can be tested exhaustively without a browser.
The DOM snapshot we store is evidence, not an extraction source -- re-parsing it
later would silently drift from what the buyer actually saw.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .model import FeeLine, Mandatory, PriceBasis
from .taxonomy import classify

#: Matches the money shapes checkout pages actually use: "$1,234.56", "USD 12.50",
#: "12.50", with an optional leading sign for discounts and credits.
_MONEY = re.compile(
    r"(?P<sign>[-+−])?\s*(?:US\$|USD|\$)?\s*(?P<int>\d{1,3}(?:,\d{3})*|\d+)(?:\.(?P<frac>\d{1,2}))?",
    re.IGNORECASE,
)

_FREE = re.compile(r"\b(free|no charge|included|waived)\b", re.IGNORECASE)

#: Wording that presents a charge as elective. Its presence alongside a fee that
#: cannot actually be removed is the "optional but unavoidable" flag, which is a
#: stronger fact than a merely late-appearing fee.
_OPTIONAL_WORDING = re.compile(
    r"\b(optional|voluntary|if you wish|you may remove|suggested|add(?:\s+a)?\s+tip)\b",
    re.IGNORECASE,
)


def parse_money_cents(text: str | None) -> int | None:
    """Parse displayed money into integer cents.

    Returns 0 for text that explicitly says the charge is free or waived, and
    None where no amount is present -- the two are different, and collapsing them
    would turn a missing reading into a zero fee.
    """
    if text is None:
        return None
    stripped = text.strip()
    if not stripped:
        return None
    if _FREE.search(stripped) and not _MONEY.search(stripped):
        return 0

    match = _MONEY.search(stripped)
    if match is None:
        return None

    whole = int(match.group("int").replace(",", ""))
    frac = match.group("frac") or "0"
    # "1.5" is 50 cents of fraction, not 5.
    cents = whole * 100 + int(frac.ljust(2, "0"))
    if match.group("sign") in {"-", "−"}:
        cents = -cents
    return cents


#: Wording that marks a price as a floor rather than this item's price.
_FLOOR_WORDING = re.compile(
    r"\b(from|starting\s+at|as\s+low\s+as|prices?\s+from)\b", re.IGNORECASE
)
#: A trailing "+" does the same job without words: "$307+".
_TRAILING_PLUS = re.compile(r"\d\s*\+")
_RANGE = re.compile(r"\d\s*(?:-|\u2013|to)\s*(?:US\$|USD|\$)?\s*\d")


def classify_price_basis(text: str | None) -> PriceBasis:
    """Is this the price of the item, or a floor across many?

    Cheap to get wrong and expensive when wrong: a floor compared against a
    checkout total produces a gap that is entirely an artefact of the comparison.
    """
    if text is None or not text.strip():
        return PriceBasis.UNKNOWN
    if _RANGE.search(text):
        return PriceBasis.RANGE
    if _FLOOR_WORDING.search(text) or _TRAILING_PLUS.search(text):
        return PriceBasis.FLOOR
    return PriceBasis.EXACT


def label_reads_optional(label: str, nearby_text: str | None = None) -> bool:
    haystack = f"{label} {nearby_text or ''}"
    return bool(_OPTIONAL_WORDING.search(haystack))


@dataclass(frozen=True)
class RawFeeRow:
    """One line item as read off the page, before interpretation."""

    label: str
    amount_text: str
    #: Did the page offer a control that actually removes this charge? Determined
    #: by the flow script, which is the only thing that can try. Absent that
    #: evidence the fee stays UNKNOWN rather than being guessed either way.
    removable: bool | None = None
    purpose_text: str | None = None
    nearby_text: str | None = None


def to_fee_line(row: RawFeeRow, step_index: int) -> FeeLine | None:
    """Interpret one raw row. Returns None where no amount could be read."""
    cents = parse_money_cents(row.amount_text)
    if cents is None:
        return None

    if row.removable is True:
        mandatory = Mandatory.OPTIONAL
    elif row.removable is False:
        mandatory = Mandatory.MANDATORY
    else:
        mandatory = Mandatory.UNKNOWN

    return FeeLine(
        raw_label=row.label.strip(),
        amount_cents=cents,
        category=classify(row.label),
        mandatory=mandatory,
        first_seen_step_index=step_index,
        purpose_text=(row.purpose_text or "").strip() or None,
        label_says_optional=label_reads_optional(row.label, row.nearby_text),
    )


def to_fee_lines(rows: list[RawFeeRow], step_index: int) -> tuple[FeeLine, ...]:
    lines = (to_fee_line(row, step_index) for row in rows)
    return tuple(line for line in lines if line is not None)


def carry_forward(
    previous: tuple[FeeLine, ...], current: tuple[FeeLine, ...]
) -> tuple[FeeLine, ...]:
    """Preserve each fee's *first* appearance across steps.

    A fee restated at checkout has not appeared twice; it appeared once and was
    repeated. Since the whole measurement is "at which step did this first show",
    the earliest step index wins and later restatements are dropped.
    """
    seen = {line.raw_label: line for line in previous}
    out = list(previous)
    for line in current:
        if line.raw_label not in seen:
            out.append(line)
            seen[line.raw_label] = line
    return tuple(out)
