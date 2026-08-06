"""Run the Rigobon-Sack war-premium estimation across cities and crises.

Loads the mirrored Neal-Weidenmeier short-term rates, takes weekly first
differences of each city's rate and of the London 3-month trade bill (the basis
asset), and estimates the war-risk premium per city per crisis — reproducing the
paper's Tables 3-7, and extending to July 1914 on short rates and long-term bonds.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from .estimator import IVResult, estimate
from .warweeks import Crisis, war_mask

D = datetime.date
BASIS_KEY = "london_trade3mo"
WEEK = datetime.timedelta(days=7)


@dataclass(frozen=True)
class CityResult:
    city: str
    single: IVResult
    two: IVResult


def _weekly_changes(series: Dict[D, float], window: Tuple[D, D]) -> Dict[D, float]:
    """Δ at each Saturday t in window where both t and t-7d are present."""
    lo, hi = window
    out: Dict[D, float] = {}
    for d, v in series.items():
        if lo <= d <= hi and (d - WEEK) in series:
            out[d] = v - series[d - WEEK]
    return out


def run_crisis(
    series_map: Dict[str, List[Tuple[D, float]]],
    crisis: Crisis,
    *,
    basis_key: str = BASIS_KEY,
    events: Optional[Sequence[D]] = None,
) -> List[CityResult]:
    """Estimate the premium for every city in ``series_map`` for one crisis."""
    ev = list(events) if events is not None else crisis.war_events
    basis = dict(series_map[basis_key])
    dY = _weekly_changes(basis, crisis.window)

    results: List[CityResult] = []
    for city, pairs in series_map.items():
        if city == basis_key:
            continue
        dX = _weekly_changes(dict(pairs), crisis.window)
        common = sorted(set(dX) & set(dY))
        if len(common) < 8:
            continue
        dx = [dX[d] for d in common]
        dy = [dY[d] for d in common]
        war = war_mask(common, ev)
        if not any(war):
            continue
        results.append(CityResult(
            city=city,
            single=estimate(dx, dy, war, two_instrument=False),
            two=estimate(dx, dy, war, two_instrument=True),
        ))
    return results


def format_table(crisis: Crisis, results: Sequence[CityResult]) -> str:
    lines = [
        f"# {crisis.label}  window={crisis.window[0]}..{crisis.window[1]}"
        + (f"  (paper n={crisis.stated_n})" if crisis.stated_n else ""),
        f"{'city':<22}{'beta(Lon)':>10}{'t':>7}{'beta(2iv)':>11}{'t':>7}{'n':>5}{'war':>4}",
    ]
    for r in sorted(results, key=lambda x: x.city):
        s, tw = r.single, r.two
        lines.append(
            f"{r.city:<22}{s.beta:>10.2f}{s.t_stat:>7.2f}"
            f"{tw.beta:>11.2f}{tw.t_stat:>7.2f}{s.n:>5}{s.n_war:>4}"
        )
    return "\n".join(lines)
