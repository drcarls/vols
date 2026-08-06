"""Join the Correlates of War Militarized Interstate Dispute (MID v5) tables.

MIDA (dispute-level: onset/end dates, hostility level, fatality) and MIDB
(participant-level: which states, on which side) are joined on ``dispnum`` into a
:class:`Dispute`. The join is a pure function over row dicts so it is unit-tested
without the CSVs; :func:`load_disputes` only adds the file read.

Hostility level is COW's 1–5 escalation scale — the objective "war risk" signal
this package brings to ``crisis_lag``: 1 none, 2 threat, 3 display of force,
4 use of force, 5 war.
"""

from __future__ import annotations

import csv
import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

HOSTILITY = {1: "none", 2: "threat", 3: "display of force", 4: "use of force", 5: "war"}

# COW country codes for the actors we name (others kept as their numeric code).
CCODE_NAME = {
    2: "USA", 200: "UK", 210: "Netherlands", 211: "Belgium", 220: "France",
    230: "Spain", 235: "Portugal", 255: "Germany", 300: "Austria-Hungary",
    325: "Italy", 341: "Montenegro", 345: "Serbia", 350: "Greece", 355: "Bulgaria",
    360: "Romania", 365: "Russia", 380: "Sweden", 640: "Ottoman Empire", 740: "Japan",
}

_MISSING = {"-9", "", None}


def _int(v) -> Optional[int]:
    if v in _MISSING:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _date(y, m, d) -> Optional[datetime.date]:
    """Build a date from MID y/m/d parts, tolerating -9 month/day (-> 1)."""
    yy = _int(y)
    if yy is None:
        return None
    mm = _int(m) or 1
    dd = _int(d) or 1
    try:
        return datetime.date(yy, mm, dd)
    except ValueError:
        return None


@dataclass(frozen=True)
class Dispute:
    dispnum: str
    onset: Optional[datetime.date]
    end: Optional[datetime.date]
    hostlev: Optional[int]
    fatality: Optional[int]
    side_a: List[int] = field(default_factory=list)  # ccodes, sidea == 1
    side_b: List[int] = field(default_factory=list)  # ccodes, sidea == 0

    @property
    def hostlev_label(self) -> str:
        return HOSTILITY.get(self.hostlev or 0, "unknown")

    def names(self, ccodes: Sequence[int]) -> List[str]:
        return [CCODE_NAME.get(c, str(c)) for c in ccodes]

    def participants(self) -> List[int]:
        return list(self.side_a) + list(self.side_b)


def join_disputes(mida_rows: Sequence[dict], midb_rows: Sequence[dict]) -> Dict[str, Dispute]:
    """Join MIDA + MIDB row dicts into ``{dispnum: Dispute}`` (pure)."""
    sides: Dict[str, "tuple[list, list]"] = {}
    for r in midb_rows:
        dn = r["dispnum"]
        a, b = sides.setdefault(dn, ([], []))
        cc = _int(r.get("ccode"))
        if cc is None:
            continue
        (a if r.get("sidea") == "1" else b).append(cc)
    out: Dict[str, Dispute] = {}
    for r in mida_rows:
        dn = r["dispnum"]
        a, b = sides.get(dn, ([], []))
        out[dn] = Dispute(
            dispnum=dn,
            onset=_date(r.get("styear"), r.get("stmon"), r.get("stday")),
            end=_date(r.get("endyear"), r.get("endmon"), r.get("endday")),
            hostlev=_int(r.get("hostlev")),
            fatality=_int(r.get("fatality")),
            side_a=a,
            side_b=b,
        )
    return out


def load_disputes(mida_path: str, midb_path: str) -> Dict[str, Dispute]:
    """Load and join the MIDA/MIDB CSV files."""
    with open(mida_path, newline="", encoding="utf-8", errors="replace") as fa:
        mida = list(csv.DictReader(fa))
    with open(midb_path, newline="", encoding="utf-8", errors="replace") as fb:
        midb = list(csv.DictReader(fb))
    return join_disputes(mida, midb)
