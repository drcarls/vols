"""Convert the IMM's pre-decimal £-s-d yield fields into a decimal percent.

The *Investor's Monthly Manual* records the yield on investment at the late price
in pounds, shillings and pence **per cent** — three separate columns in the Yale
digitisation (``YieldInvtLatePricePound`` / ``…Shilling`` / ``…Pence``, the
``Var7`` group of the search form). A yield printed as "£4 3s 6d %" is

    4 + 3/20 + 6/240  =  4.175 per cent.

There are 20 shillings to the pound and 12 pence to the shilling, so a shilling
is 1/20 of a point and a penny 1/240. This module is pure arithmetic — it is the
one part of the pipeline that can be verified without the live backend, and the
tests pin the conversion to worked examples.
"""

from __future__ import annotations

from typing import Optional

SHILLINGS_PER_POUND = 20
PENCE_PER_SHILLING = 12
PENCE_PER_POUND = SHILLINGS_PER_POUND * PENCE_PER_SHILLING  # 240


def lsd_to_percent(
    pound: Optional[float],
    shilling: Optional[float] = 0.0,
    pence: Optional[float] = 0.0,
) -> Optional[float]:
    """Return the yield in decimal percent from £-s-d parts.

    ``None`` for *every* part means "not quoted" and yields ``None``; a ``None``
    in one part alone is treated as zero (a blank shilling/pence cell is common).
    Raises ``ValueError`` on shillings/pence outside their normal range, which
    signals a misparsed cell rather than a real quotation.
    """
    if pound is None and shilling is None and pence is None:
        return None
    p = 0.0 if pound is None else float(pound)
    s = 0.0 if shilling is None else float(shilling)
    d = 0.0 if pence is None else float(pence)
    if not (0 <= s < SHILLINGS_PER_POUND):
        raise ValueError(f"shillings out of range [0,20): {s}")
    if not (0 <= d < PENCE_PER_SHILLING):
        raise ValueError(f"pence out of range [0,12): {d}")
    return p + s / SHILLINGS_PER_POUND + d / PENCE_PER_POUND


def parse_number(raw: Optional[str]) -> Optional[float]:
    """Parse one £-s-d cell string to a float, or ``None`` when blank.

    Tolerates the messiness of digitised cells: surrounding whitespace, a stray
    currency/percent mark, en/em dashes used for "nil", and empty strings.
    """
    if raw is None:
        return None
    t = raw.strip().strip("£%").replace("—", "").replace("–", "").strip()
    if t in ("", "-", "–", "—", "nil", "Nil", "n/a", "N/A"):
        return None
    try:
        return float(t)
    except ValueError:
        return None


def cells_to_percent(
    pound_raw: Optional[str],
    shilling_raw: Optional[str],
    pence_raw: Optional[str],
) -> Optional[float]:
    """Convenience: parse the three raw £-s-d cell strings and convert."""
    return lsd_to_percent(
        parse_number(pound_raw),
        parse_number(shilling_raw),
        parse_number(pence_raw),
    )
