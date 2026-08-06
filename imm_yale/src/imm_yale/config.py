"""The securities catalogue: which IMM security carries each power's spread.

The falsification test keys each crisis to a power's series id (``france``,
``germany``, ``russia``, ``austria_hungary`` — see ``crisis_lag.events``). This
module maps each of those ids to the *sovereign security* whose yield we pull
from the IMM, and names the common benchmark (the UK Consol) the spread is taken
over.

The mapping is **provisional** and is exactly the "which power's spread carries
each crisis" specification to reconcile against the original thesis dataset — the
same reconciliation ``crisis_lag`` flags for its event dates. Every field is
overridable via a YAML file (:func:`load_catalogue`); the built-in defaults below
name the conventional benchmark issue for each power so the pipeline has a
concrete, documented starting point rather than a silent guess.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Security:
    """A sovereign security to pull, identified either by IMM id or by name.

    ``security_id`` (a numeric IMM id, if known) is the most precise selector;
    otherwise ``name_query`` is used as an *exact*-company-name search. ``notes``
    records the human-readable issue and any caveat (coupon date, conversion).
    """

    series: str  # crisis_lag series id, e.g. "germany"
    label: str  # human label, e.g. "German 3% Imperial Loan"
    name_query: Optional[str] = None
    security_id: Optional[str] = None
    notes: Optional[str] = None


@dataclass(frozen=True)
class Catalogue:
    benchmark: Security
    issuers: List[Security] = field(default_factory=list)


# Conventional benchmark: the British Consol, the era's risk-free long bond.
DEFAULT_BENCHMARK = Security(
    series="benchmark",
    label="UK Consols 2.5%",
    name_query="Consols",
    notes="Goschen 2.75%->2.5% consolidated stock; the risk-free reference yield.",
)

# PROVISIONAL issuer mapping — reconcile against the thesis dataset before use.
DEFAULT_ISSUERS: List[Security] = [
    Security(
        series="france",
        label="French 3% Rente",
        name_query="French Rentes",
        notes="Perpetual 3% rente; France's benchmark sovereign.",
    ),
    Security(
        series="germany",
        label="German 3% Imperial Loan",
        name_query="German Imperial",
        notes="Reich 3% loan; the fiscally-binding power in Agadir 1911.",
    ),
    Security(
        series="russia",
        label="Russian 4% Government Loan",
        name_query="Russian Government",
        notes="Post-1906 4% state loan placed largely in Paris.",
    ),
    Security(
        series="austria_hungary",
        label="Austrian 4% Gold Rente",
        name_query="Austrian Gold",
        notes="Austro-Hungarian benchmark; the binding power in the Balkans/1914.",
    ),
]


def default_catalogue() -> Catalogue:
    return Catalogue(benchmark=DEFAULT_BENCHMARK, issuers=list(DEFAULT_ISSUERS))


def _security_from_dict(d: dict, *, default_series: Optional[str] = None) -> Security:
    return Security(
        series=str(d.get("series", default_series)),
        label=str(d.get("label", d.get("series", default_series))),
        name_query=d.get("name_query"),
        security_id=(str(d["security_id"]) if d.get("security_id") is not None else None),
        notes=d.get("notes"),
    )


def load_catalogue(path: str) -> Catalogue:
    """Load a securities catalogue from YAML (keys ``benchmark`` and ``issuers``)."""
    import yaml

    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    bench = (
        _security_from_dict(data["benchmark"], default_series="benchmark")
        if data.get("benchmark")
        else DEFAULT_BENCHMARK
    )
    issuers = [_security_from_dict(d) for d in data.get("issuers", [])]
    return Catalogue(benchmark=bench, issuers=issuers or list(DEFAULT_ISSUERS))


def catalogue_series(cat: Catalogue) -> Dict[str, Security]:
    """Map series id -> issuer Security (benchmark excluded)."""
    return {s.series: s for s in cat.issuers}
