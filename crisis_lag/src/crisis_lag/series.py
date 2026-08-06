"""Load a tidy long spread/quotation series.

Shares the schema emitted by ``gallica_le_temps.series`` (long form): a CSV with
at least ``date``, ``series`` and ``value`` columns. Extra columns (source,
provenance) are ignored. This lets the monthly IMM sovereign spreads and the
daily Le Temps quotations feed the same lag harness.

``value`` is whatever stress measure the series carries — a spread in basis
points, a yield, or a price. The lag machinery only needs a number per date; the
direction of "stress" (up for spreads/yields) is handled in :mod:`crisis_lag.stress`.
"""

from __future__ import annotations

import csv
from datetime import date
from typing import Dict, List, Optional, Tuple

# A series is a date-sorted list of (date, value) observations.
Observation = Tuple[date, float]
SeriesMap = Dict[str, List[Observation]]


def load_long_csv(
    path: str,
    *,
    date_col: str = "date",
    series_col: str = "series",
    value_col: str = "value",
) -> SeriesMap:
    """Load a tidy long CSV into ``{series: [(date, value), ...]}`` (sorted)."""
    with open(path, "r", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return rows_to_series(
        rows, date_col=date_col, series_col=series_col, value_col=value_col
    )


def rows_to_series(
    rows,
    *,
    date_col: str = "date",
    series_col: str = "series",
    value_col: str = "value",
) -> SeriesMap:
    """Build a :data:`SeriesMap` from dict rows; blank/unparseable values dropped."""
    out: Dict[str, List[Observation]] = {}
    for r in rows:
        raw = (r.get(value_col) or "").strip()
        if not raw:
            continue
        try:
            value = float(raw)
        except ValueError:
            continue
        try:
            d = date.fromisoformat((r.get(date_col) or "").strip())
        except ValueError:
            continue
        out.setdefault(r.get(series_col, ""), []).append((d, value))
    for key in out:
        out[key].sort(key=lambda ob: ob[0])
    return out


def window(
    obs: List[Observation], start: date, end: date
) -> List[Observation]:
    """Return observations with ``start <= date <= end`` (inclusive)."""
    return [(d, v) for (d, v) in obs if start <= d <= end]


def series_span(obs: List[Observation]) -> Optional[Tuple[date, date]]:
    """Return ``(first_date, last_date)`` or ``None`` if empty."""
    if not obs:
        return None
    return obs[0][0], obs[-1][0]
