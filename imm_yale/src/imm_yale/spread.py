"""Turn per-security monthly yields into sovereign *spreads* over a benchmark.

The stress measure the falsification test consumes is a sovereign spread: a
power's government-bond yield *above* a common risk-free benchmark (the UK
Consol). Working in a spread rather than a raw yield strips out the common
movement in the general level of interest rates, so what remains is the
country-specific risk premium — which is what widens in a crisis.

    spread_bp(month) = ( yield_issuer(month) - yield_benchmark(month) ) * 100

Yields are in percent (see :mod:`imm_yale.lsd`); ×100 puts the spread in basis
points, the unit :mod:`crisis_lag` treats as "stress rising when it widens". A
month with no benchmark quotation, or no issuer quotation, produces no spread —
we never impute one.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# A monthly yield series: {"YYYY-MM": yield_percent}.
YieldSeries = Dict[str, float]


@dataclass(frozen=True)
class SpreadPoint:
    month: str  # "YYYY-MM"
    issuer_yield: float
    benchmark_yield: float
    spread_bp: float


def month_key(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}"


def to_spreads(
    issuer: YieldSeries,
    benchmark: YieldSeries,
) -> List[SpreadPoint]:
    """Compute basis-point spreads for every month present in *both* series.

    The result is sorted by month. Months quoted for only one of the two series
    are dropped (a spread needs both legs); nothing is interpolated.
    """
    points: List[SpreadPoint] = []
    for m in sorted(set(issuer) & set(benchmark)):
        iy = issuer[m]
        by = benchmark[m]
        points.append(
            SpreadPoint(
                month=m,
                issuer_yield=iy,
                benchmark_yield=by,
                spread_bp=(iy - by) * 100.0,
            )
        )
    return points


def coverage(issuer: YieldSeries, benchmark: YieldSeries) -> Tuple[int, int, int]:
    """Return ``(n_issuer, n_benchmark, n_overlap)`` — a quick completeness read."""
    return len(issuer), len(benchmark), len(set(issuer) & set(benchmark))
