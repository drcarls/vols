"""Which FRED/NBER series carries each power's yield, and the benchmark.

These are real NBER Macrohistory (Chapter 13, Interest Rates) series on FRED,
verified to cover the pre-1914 window. The benchmark is the England Consol yield;
each issuer series minus the benchmark gives that power's sovereign spread.

**Coverage is honest, not complete.** NBER Macrohistory carries monthly *bond
yields* for France and Germany (and the UK Consol benchmark), but **not** for
Russia or Austria-Hungary — it has their discount rates, not sovereign yields.
So this open source can drive the France/Germany crises directly; Russia and
Austria still need the Investor's Monthly Manual (see ``../imm_yale``). This is
the same reason the thesis reached for the IMM in the first place.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class FredSeries:
    series: str  # crisis_lag series id, e.g. "germany", or "benchmark"
    fred_id: str
    label: str
    coverage: str  # documented date span, for provenance
    notes: Optional[str] = None


@dataclass(frozen=True)
class Catalog:
    benchmark: FredSeries
    issuers: List[FredSeries] = field(default_factory=list)


# England Yield of Consols, 1888-03..1938-12 — the risk-free reference.
DEFAULT_BENCHMARK = FredSeries(
    series="benchmark",
    fred_id="M1341CGB40000M156NNBR",
    label="England Yield of Consols",
    coverage="1888-03..1938-12",
    notes="NBER Macrohistory ch.13; the spread is taken over this yield.",
)

DEFAULT_ISSUERS: List[FredSeries] = [
    FredSeries(
        series="france",
        fred_id="M13027FRM156NNBR",
        label="France Security Yields",
        coverage="1898-01..1939-07 (through Jul 1914)",
        notes="NBER Macrohistory ch.13; French government security yields.",
    ),
    FredSeries(
        series="germany",
        fred_id="M1328ADEM193NNBR",
        label="Germany Bond Yields",
        coverage="1870-01..1913-12",
        notes="NBER Macrohistory ch.13; ends Dec 1913 (covers Agadir 1911).",
    ),
]


def default_catalog() -> Catalog:
    return Catalog(benchmark=DEFAULT_BENCHMARK, issuers=list(DEFAULT_ISSUERS))


def _series_from_dict(d: dict) -> FredSeries:
    return FredSeries(
        series=str(d["series"]),
        fred_id=str(d["fred_id"]),
        label=str(d.get("label", d["series"])),
        coverage=str(d.get("coverage", "")),
        notes=d.get("notes"),
    )


def load_catalog(path: str) -> Catalog:
    """Load a catalog from YAML (keys ``benchmark`` and ``issuers``)."""
    import yaml

    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    bench = _series_from_dict(data["benchmark"]) if data.get("benchmark") else DEFAULT_BENCHMARK
    issuers = [_series_from_dict(d) for d in data.get("issuers", [])]
    return Catalog(benchmark=bench, issuers=issuers or list(DEFAULT_ISSUERS))


def catalog_by_series(cat: Catalog) -> Dict[str, FredSeries]:
    return {s.series: s for s in cat.issuers}
