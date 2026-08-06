"""A continuous great-power war-risk index across the whole period, from MID.

The lag test looks only at hand-picked crisis windows. This builds an objective
series over *every* week of 1900–1914 instead: at each step, the maximum
hostility level (COW's 1–5 scale) of any militarized dispute active that week
that is a **great-power confrontation** — a great power on *each* side. That
"both sides" restriction is what makes it a proxy for *great-power* war risk
rather than colonial policing: it is quiet (0) in normal weeks and lights up only
at real great-power stand-offs (1904 Dogger Bank, 1911 Agadir, 1912 Austria–
Russia, 1914 war).

Honest naming: this is a war-risk **intensity** index, not a market-implied
*probability* of war — no traded war contract existed for 1914, so an ex-ante
probability is not recoverable. Hostility level is an ordinal escalation measure
(2 threat · 3 display · 4 use of force · 5 war); 0 means no active great-power
dispute. A crude monotone pseudo-probability is offered separately and flagged as
illustrative.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional

from .parse import Dispute

# COW ccodes for the European great powers of the period.
GREAT_POWERS: FrozenSet[int] = frozenset({
    200,  # United Kingdom
    220,  # France
    255,  # Germany
    300,  # Austria-Hungary
    325,  # Italy
    365,  # Russia
})

# Illustrative-only map from hostility level to a pseudo-probability of war.
PSEUDO_PROB = {0: 0.0, 1: 0.0, 2: 0.1, 3: 0.25, 4: 0.5, 5: 1.0}


@dataclass(frozen=True)
class RiskPoint:
    date: datetime.date
    max_hostlev: int          # 0..5
    n_active: int             # active great-power disputes that week
    dispnums: List[str]


def _active_on(d: Dispute, day: datetime.date) -> bool:
    if d.onset is None:
        return False
    end = d.end or d.onset
    return d.onset <= day <= end


def _is_gp_confrontation(
    d: Dispute, great_powers: FrozenSet[int], both_sides: bool
) -> bool:
    a = any(c in great_powers for c in d.side_a)
    b = any(c in great_powers for c in d.side_b)
    return (a and b) if both_sides else (a or b)


def war_risk_series(
    disputes: Dict[str, Dispute],
    start: datetime.date,
    end: datetime.date,
    *,
    step_days: int = 7,
    great_powers: FrozenSet[int] = GREAT_POWERS,
    both_sides: bool = True,
) -> List[RiskPoint]:
    """Weekly (by default) great-power war-risk intensity over ``[start, end]``.

    Pure over the disputes mapping — no I/O — so it is unit-tested with synthetic
    disputes. ``both_sides=True`` requires a great power on each side (great-power
    confrontation); ``False`` counts any dispute a great power is in at all.
    """
    relevant = [
        d for d in disputes.values()
        if d.hostlev and _is_gp_confrontation(d, great_powers, both_sides)
    ]
    out: List[RiskPoint] = []
    n_steps = (end - start).days // step_days
    for i in range(n_steps + 1):
        day = start + datetime.timedelta(days=step_days * i)
        active = [d for d in relevant if _active_on(d, day)]
        mx = max((d.hostlev or 0 for d in active), default=0)
        out.append(
            RiskPoint(
                date=day,
                max_hostlev=mx,
                n_active=len(active),
                dispnums=sorted(d.dispnum for d in active),
            )
        )
    return out


def pseudo_probability(hostlev: int) -> float:
    """Illustrative-only ordinal->[0,1] map (NOT an estimated probability)."""
    return PSEUDO_PROB.get(hostlev, 0.0)


LONG_FIELDS = ["date", "series", "value", "unit", "source", "status", "n_active", "dispnums"]


def write_long_csv(points: "List[RiskPoint]", path: str) -> int:
    """Emit the war-risk series as a tidy long CSV (two series: intensity + pseudo-prob).

    Schema matches the financial extractors so it stacks under the same tools.
    ``war_risk`` is the 0–5 hostility intensity; ``war_risk_pprob`` the illustrative
    pseudo-probability.
    """
    import csv

    rows = []
    for p in points:
        common = dict(source="cow_mid", status="ok", n_active=p.n_active,
                      dispnums="|".join(p.dispnums))
        rows.append(dict(date=p.date.isoformat(), series="war_risk",
                         value=str(p.max_hostlev), unit="hostlev(0-5)", **common))
        rows.append(dict(date=p.date.isoformat(), series="war_risk_pprob",
                         value=f"{pseudo_probability(p.max_hostlev):.3f}",
                         unit="pseudo-prob", **common))
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=LONG_FIELDS)
        w.writeheader()
        w.writerows(rows)
    return len(rows)
