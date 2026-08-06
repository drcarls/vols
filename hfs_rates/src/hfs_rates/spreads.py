"""Money-market rate series -> spread over London -> tidy long CSV for crisis_lag.

    spread_bp(week) = ( rate_power(week) - rate_london(week) ) * 100

Only weeks quoted in *both* legs produce a spread; nothing is imputed. Dates are
the actual weekly observation dates (``YYYY-MM-DD``), so crisis_lag sees weekly —
not monthly — resolution. The emitted schema matches the other extractors
(``date,series,value`` + provenance), so it stacks under crisis_lag directly.
"""

from __future__ import annotations

import csv
import datetime
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Sequence

from .parse import RateSeries

SOURCE = "hfs"
UNIT = "bp"

LONG_FIELDS = [
    "date", "series", "value", "unit", "source", "status",
    "power_rate", "london_rate",
]


@dataclass
class SpreadRow:
    date: str
    series: str
    value: str
    unit: str
    source: str
    status: str
    power_rate: str
    london_rate: str


def to_spread_rows(series_id: str, power: RateSeries, london: RateSeries) -> List[SpreadRow]:
    """Weekly spread rows for one power over the London benchmark."""
    rows: List[SpreadRow] = []
    for d in sorted(set(power) & set(london)):
        pr, lr = power[d], london[d]
        rows.append(
            SpreadRow(
                date=d.isoformat(),
                series=series_id,
                value=f"{(pr - lr) * 100.0:.2f}",
                unit=UNIT,
                source=SOURCE,
                status="ok",
                power_rate=f"{pr:.3f}",
                london_rate=f"{lr:.3f}",
            )
        )
    return rows


def write_long_csv(rows: Sequence[SpreadRow], path: str) -> int:
    ordered = sorted(rows, key=lambda r: (r.date, r.series))
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=LONG_FIELDS)
        w.writeheader()
        for r in ordered:
            w.writerow(asdict(r))
    return len(ordered)


def coverage(power: RateSeries, london: RateSeries) -> "tuple[int,int,int]":
    return len(power), len(london), len(set(power) & set(london))
