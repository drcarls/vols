"""Which HFS column carries each power's money-market rate, and the benchmark.

Each power's **open-market rate** (the private-discount / bill rate that tightens
under funding stress) is spread over the **London** open-market rate — 90-day
bank bills — so the strong common autumn seasonality of money markets is largely
differenced out (see the README's seasonality note; the spread is why a raw level
would misread seasonal tightening as crisis stress).

series ids match ``crisis_lag.events``. Coverage is honest: Austria, France,
Germany and the UK benchmark are weekly across 1900–1914; **Russia's** market
rate is sparse (HFS carries St Petersburg only to 1900), so its spread will be
mostly empty here — Russia's pre-war crises still need another source.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class RateColumn:
    series: str  # crisis_lag series id (or "benchmark")
    country: str  # HFS Country header value
    series_substr: str  # substring identifying the Series text
    label: str
    notes: Optional[str] = None


@dataclass(frozen=True)
class Catalog:
    benchmark: RateColumn
    issuers: List[RateColumn] = field(default_factory=list)


# London open-market rate: 90-day bank bills (bid). The common benchmark.
DEFAULT_BENCHMARK = RateColumn(
    series="benchmark",
    country="United Kingdom",
    series_substr="bank bills, 90 days, bid",
    label="London 90-day bank bills",
    notes="London open-market rate; the spread is taken over this.",
)

DEFAULT_ISSUERS: List[RateColumn] = [
    RateColumn("france", "France", "open market rate", "Paris open-market rate"),
    RateColumn("germany", "Germany", "open market rate", "Berlin open-market rate",
               notes="Agadir 1911 comparator."),
    RateColumn("austria_hungary", "Austria", "open market rate", "Vienna open-market rate",
               notes="Balkan Wars 1912-13 comparator."),
    RateColumn("russia", "Russia", "open market rate", "St Petersburg open-market rate",
               notes="Sparse in HFS (ends 1900); mostly empty here."),
]


def default_catalog() -> Catalog:
    return Catalog(benchmark=DEFAULT_BENCHMARK, issuers=list(DEFAULT_ISSUERS))
