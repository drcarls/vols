"""Emit the tidy long ``(date, series, value)`` CSV that ``crisis_lag`` consumes.

This mirrors the schema of ``gallica_le_temps.series`` so the monthly IMM
sovereign spreads and the daily Le Temps quotations stack with a plain concat and
feed the same lag harness (``crisis_lag.series.load_long_csv`` reads
``date``/``series``/``value`` and ignores the provenance columns).

Monthly observations are dated to the first of the month (``YYYY-MM-01``); the
``value`` is the spread in basis points, ``unit`` is ``"bp"`` and ``source`` is
``"imm_yale"``.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Sequence

from .spread import SpreadPoint

DEFAULT_SOURCE = "imm_yale"
DEFAULT_UNIT = "bp"

LONG_FIELDS = [
    "date",
    "series",
    "value",
    "unit",
    "source",
    "status",
    "issuer_yield",
    "benchmark_yield",
    "security_id",
    "benchmark_id",
]


@dataclass
class SeriesPoint:
    date: str
    series: str
    value: Optional[str]  # spread in bp as str, or None
    unit: Optional[str]
    source: str
    status: str
    issuer_yield: Optional[str] = None
    benchmark_yield: Optional[str] = None
    security_id: Optional[str] = None
    benchmark_id: Optional[str] = None


def _date_of(month: str) -> str:
    """``"1911-07"`` -> ``"1911-07-01"``."""
    return f"{month}-01"


def spreads_to_points(
    series_id: str,
    spreads: Sequence[SpreadPoint],
    *,
    source: str = DEFAULT_SOURCE,
    security_id: Optional[str] = None,
    benchmark_id: Optional[str] = None,
) -> List[SeriesPoint]:
    """Convert one power's :class:`SpreadPoint` list into tidy long rows."""
    points: List[SeriesPoint] = []
    for sp in spreads:
        points.append(
            SeriesPoint(
                date=_date_of(sp.month),
                series=series_id,
                value=f"{sp.spread_bp:.2f}",
                unit=DEFAULT_UNIT,
                source=source,
                status="ok",
                issuer_yield=f"{sp.issuer_yield:.4f}",
                benchmark_yield=f"{sp.benchmark_yield:.4f}",
                security_id=security_id,
                benchmark_id=benchmark_id,
            )
        )
    return points


def write_long_csv(points: Sequence[SeriesPoint], path: str) -> int:
    """Write tidy long rows to ``path`` (date-then-series sorted); return count."""
    ordered = sorted(points, key=lambda p: (p.date, p.series))
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=LONG_FIELDS)
        writer.writeheader()
        for p in ordered:
            writer.writerow(asdict(p))
    return len(ordered)


def merge_series(*groups: Sequence[SeriesPoint]) -> List[SeriesPoint]:
    """Concatenate several powers' point lists into one long table."""
    out: List[SeriesPoint] = []
    for g in groups:
        out.extend(g)
    return out
