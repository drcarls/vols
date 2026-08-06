"""Great-power capability balance from COW National Material Capabilities (NMC).

Adds the *structural* dimension to the war-risk picture: the material-capability
ratio between the two alliance blocs, and the Anglo-German military-spending gap
(the arms race), annually across 1900–1914. Power-transition theory reads
approaching **parity** as raising war risk; these series make that observable.

NMC gives each state a yearly **CINC** (Composite Indicator of National
Capability, a share of world capability built from military spending/personnel,
iron-and-steel, energy, and population) plus the raw components. The blocs:

* **Triple Entente** — France, Russia, United Kingdom.
* **Triple Alliance** — Germany, Austria-Hungary, Italy.

Italy is included by default (it was a treaty member) but stayed neutral in 1914;
``exclude_italy`` drops it, which is the more honest measure of the blocs that
*actually* went to war. This is structural context, **not** a fitted probability
of war — with 15 years and one war, no probability model is identified; these are
covariates, reported as such.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Tuple

ENTENTE: FrozenSet[int] = frozenset({220, 365, 200})       # France, Russia, UK
ALLIANCE_CORE: FrozenSet[int] = frozenset({255, 300})       # Germany, Austria-Hungary
ITALY = 325

# (ccode, year) -> row of floats for the fields we use.
FIELDS = ("cinc", "milex", "milper", "irst", "pec", "tpop", "upop")


def _num(v: Optional[str]) -> Optional[float]:
    if v is None:
        return None
    t = v.strip()
    if t in ("", "-9", "."):
        return None
    try:
        return float(t)
    except ValueError:
        return None


def parse_nmc(path: str) -> Dict[Tuple[int, int], Dict[str, Optional[float]]]:
    """Load the NMC abridged CSV into ``{(ccode, year): {field: value}}``."""
    out: Dict[Tuple[int, int], Dict[str, Optional[float]]] = {}
    with open(path, newline="", encoding="utf-8", errors="replace") as fh:
        for r in csv.DictReader(fh):
            try:
                key = (int(r["ccode"]), int(r["year"]))
            except (KeyError, ValueError):
                continue
            out[key] = {f: _num(r.get(f)) for f in FIELDS}
    return out


def alliance_ccodes(exclude_italy: bool = False) -> FrozenSet[int]:
    return ALLIANCE_CORE if exclude_italy else (ALLIANCE_CORE | {ITALY})


def _bloc_sum(nmc, ccodes: FrozenSet[int], year: int, field: str) -> float:
    total = 0.0
    for c in ccodes:
        v = nmc.get((c, year), {}).get(field)
        if v is not None:
            total += v
    return total


@dataclass(frozen=True)
class CapabilityYear:
    year: int
    entente_cinc: float
    alliance_cinc: float

    @property
    def capratio(self) -> Optional[float]:
        """Alliance CINC / Entente CINC (>1 => Alliance stronger)."""
        return self.alliance_cinc / self.entente_cinc if self.entente_cinc else None

    @property
    def parity(self) -> Optional[float]:
        """min/max of the two bloc totals: 1.0 = perfect parity, ->0 = lopsided."""
        hi = max(self.alliance_cinc, self.entente_cinc)
        lo = min(self.alliance_cinc, self.entente_cinc)
        return lo / hi if hi else None

    @property
    def alliance_share(self) -> Optional[float]:
        """Alliance share of the two blocs' combined CINC."""
        tot = self.alliance_cinc + self.entente_cinc
        return self.alliance_cinc / tot if tot else None


def capability_series(
    nmc, start: int = 1900, end: int = 1914, *, exclude_italy: bool = False
) -> List[CapabilityYear]:
    """Yearly bloc CINC totals over ``[start, end]``."""
    allies = alliance_ccodes(exclude_italy)
    out: List[CapabilityYear] = []
    for year in range(start, end + 1):
        out.append(
            CapabilityYear(
                year=year,
                entente_cinc=_bloc_sum(nmc, ENTENTE, year, "cinc"),
                alliance_cinc=_bloc_sum(nmc, allies, year, "cinc"),
            )
        )
    return out


def milex_ratio(nmc, a: int, b: int, year: int) -> Optional[float]:
    """Military-expenditure ratio of state ``a`` to state ``b`` (e.g. Germany/UK)."""
    va = nmc.get((a, year), {}).get("milex")
    vb = nmc.get((b, year), {}).get("milex")
    if va is None or vb in (None, 0):
        return None
    return va / vb


LONG_FIELDS = ["date", "series", "value", "unit", "source", "status",
               "entente_cinc", "alliance_cinc"]


def write_long_csv(
    nmc, path: str, *, start: int = 1900, end: int = 1914, exclude_italy: bool = False
) -> int:
    """Emit the capability series as a tidy long CSV (annual, dated YYYY-01-01)."""
    rows = []
    for cy in capability_series(nmc, start, end, exclude_italy=exclude_italy):
        d = f"{cy.year}-01-01"
        base = dict(source="cow_nmc", status="ok",
                    entente_cinc=f"{cy.entente_cinc:.5f}",
                    alliance_cinc=f"{cy.alliance_cinc:.5f}")
        if cy.capratio is not None:
            rows.append(dict(date=d, series="capratio_alliance_entente",
                             value=f"{cy.capratio:.4f}", unit="ratio", **base))
        if cy.parity is not None:
            rows.append(dict(date=d, series="bloc_parity",
                             value=f"{cy.parity:.4f}", unit="ratio(0-1)", **base))
        mg = milex_ratio(nmc, 255, 200, cy.year)  # Germany / UK military spend
        if mg is not None:
            rows.append(dict(date=d, series="milex_germany_uk",
                             value=f"{mg:.4f}", unit="ratio", **base))
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=LONG_FIELDS)
        w.writeheader()
        w.writerows(rows)
    return len(rows)
