"""Yield series -> sovereign spreads -> the tidy long CSV ``crisis_lag`` reads.

A power's spread is its government-bond yield above the common benchmark (the
England Consol), in basis points:

    spread_bp(month) = ( yield_issuer(month) - yield_benchmark(month) ) * 100

Only months quoted in *both* legs produce a spread; nothing is imputed. The
emitted CSV shares the schema of ``gallica_le_temps.series`` / ``imm_yale.series``
(``date,series,value`` plus provenance), so ``crisis_lag.series.load_long_csv``
reads it directly and the sources stack with a plain concat.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Sequence

from .client import YieldSeries

SOURCE = "fred_nber"
UNIT = "bp"

LONG_FIELDS = [
    "date",
    "series",
    "value",
    "unit",
    "source",
    "status",
    "issuer_yield",
    "benchmark_yield",
    "fred_id",
    "benchmark_id",
]


@dataclass
class SpreadRow:
    date: str
    series: str
    value: str
    unit: str
    source: str
    status: str
    issuer_yield: str
    benchmark_yield: str
    fred_id: Optional[str] = None
    benchmark_id: Optional[str] = None


def to_spread_rows(
    series_id: str,
    issuer: YieldSeries,
    benchmark: YieldSeries,
    *,
    fred_id: Optional[str] = None,
    benchmark_id: Optional[str] = None,
) -> List[SpreadRow]:
    """Build tidy long rows for one power's spread over the benchmark."""
    rows: List[SpreadRow] = []
    for m in sorted(set(issuer) & set(benchmark)):
        iy, by = issuer[m], benchmark[m]
        rows.append(
            SpreadRow(
                date=f"{m}-01",  # month -> first of month (ISO)
                series=series_id,
                value=f"{(iy - by) * 100.0:.2f}",
                unit=UNIT,
                source=SOURCE,
                status="ok",
                issuer_yield=f"{iy:.4f}",
                benchmark_yield=f"{by:.4f}",
                fred_id=fred_id,
                benchmark_id=benchmark_id,
            )
        )
    return rows


def write_long_csv(rows: Sequence[SpreadRow], path: str) -> int:
    """Write rows (date-then-series sorted) to ``path``; return the count."""
    ordered = sorted(rows, key=lambda r: (r.date, r.series))
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=LONG_FIELDS)
        w.writeheader()
        for r in ordered:
            w.writerow(asdict(r))
    return len(ordered)


def coverage(issuer: YieldSeries, benchmark: YieldSeries) -> "tuple[int,int,int]":
    return len(issuer), len(benchmark), len(set(issuer) & set(benchmark))
