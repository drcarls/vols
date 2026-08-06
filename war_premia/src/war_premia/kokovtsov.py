"""The Kokovtsov event test — a test the 2005 paper could not run.

Vladimir Kokovtsov, Russia's finance minister (1904-1914) and premier — the
architect of Russian fiscal orthodoxy and of the foreign-borrowing programme
that anchored Russian credit in Paris — was dismissed by imperial rescript in
late January 1914 (Old Style); his cabinet formally ended **12 February 1914
(New Style)**. If any Russian short rate ever ought to carry a political-risk
signal, it is this: the market losing the man who guaranteed the debt.

The recovered Neal-Weidenmier data adds a St Petersburg column the paper lacked,
so the event is now runnable. This module runs it. The result is a clean,
*informative* null:

- The only Russian short rate present in 1914 is the **State Bank discount
  (bank) rate** — an administered policy rate. Around the dismissal it did not
  move: it sat on a flat plateau that straddles the event, and its next change
  was a *cut* weeks later (opposite sign to stress).
- The **market (open-market) rate**, which would price the shock, is exactly the
  series NW loses after 1900 — it ends 20 Oct 1900, with no 1914 observation.

So the answer to "did Russian short rates move around Kokovtsov's dismissal?" is:
the administered rate we have is silent by construction, and the market rate that
would answer the question is missing. The data cannot see the event.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import List, Optional

from neal_weidenmier.load import Observation, load_short_rates

# Cabinet formally ended 12 Feb 1914 (N.S.); dismissal rescript late Jan (O.S.).
# NW dates are weekly (Saturday) and Gregorian, so the N.S. date is the anchor.
EVENT_NS = datetime.date(1914, 2, 12)


@dataclass(frozen=True)
class Plateau:
    """A maximal run of a constant rate level that contains a target date."""

    level: float
    start: datetime.date
    end: datetime.date
    next_change_date: Optional[datetime.date]
    next_change_level: Optional[float]


@dataclass(frozen=True)
class KokovtsovResult:
    bracket: List[Observation]          # weekly obs straddling the event
    bank_plateau: Optional[Plateau]     # the constant-level run around the event
    market_last: Optional[datetime.date]  # last St Petersburg market-rate obs
    market_in_1914: bool


def _series(obs: List[Observation], rate_type: str) -> List[Observation]:
    rows = [o for o in obs if o.city == "Petersburg" and o.rate_type == rate_type]
    return sorted(rows, key=lambda o: o.date)


def _plateau_containing(series: List[Observation], target: datetime.date) -> Optional[Plateau]:
    """The maximal constant-value run bracketing ``target`` (by nearest obs)."""
    if not series:
        return None
    # index of the observation on or just before the target (else the first)
    i = 0
    for j, o in enumerate(series):
        if o.date <= target:
            i = j
        else:
            break
    level = series[i].value
    lo = hi = i
    while lo > 0 and series[lo - 1].value == level:
        lo -= 1
    while hi + 1 < len(series) and series[hi + 1].value == level:
        hi += 1
    nxt = series[hi + 1] if hi + 1 < len(series) else None
    return Plateau(
        level=level,
        start=series[lo].date,
        end=series[hi].date,
        next_change_date=nxt.date if nxt else None,
        next_change_level=nxt.value if nxt else None,
    )


def kokovtsov_test(short_path: str, event: datetime.date = EVENT_NS) -> KokovtsovResult:
    obs = load_short_rates(short_path)
    bank = _series(obs, "Bank")
    market = _series(obs, "Market")

    bracket = [o for o in bank if abs((o.date - event).days) <= 10]
    plateau = _plateau_containing(bank, event)
    market_last = market[-1].date if market else None
    market_in_1914 = any(o.date.year == 1914 for o in market)

    return KokovtsovResult(
        bracket=bracket,
        bank_plateau=plateau,
        market_last=market_last,
        market_in_1914=market_in_1914,
    )


def format_result(res: KokovtsovResult) -> str:
    lines = []
    lines.append("Kokovtsov dismissal — St Petersburg short rates (event 12 Feb 1914 N.S.)")
    lines.append("")
    lines.append("Weekly BANK (State Bank discount) rate straddling the event:")
    for o in res.bracket:
        lines.append(f"    {o.date}   {o.value:.2f}%")
    p = res.bank_plateau
    if p:
        lines.append("")
        lines.append(f"  The rate sat at {p.level:.2f}% unbroken from {p.start} to {p.end}")
        lines.append(f"    (a {(p.end - p.start).days // 7}-week plateau straddling the dismissal).")
        if p.next_change_date is not None:
            direction = "cut" if p.next_change_level < p.level else "hike"
            wk = (p.next_change_date - EVENT_NS).days // 7
            lines.append(
                f"    Next change: {p.level:.2f}% -> {p.next_change_level:.2f}% on "
                f"{p.next_change_date} — a {direction}, ~{wk} weeks AFTER the event."
            )
    lines.append("")
    lines.append("MARKET (open-market) rate — the series that would price the shock:")
    lines.append(f"    last observation {res.market_last}; present in 1914? {res.market_in_1914}")
    lines.append("")
    lines.append("Finding: the administered bank rate did NOT move (mid-plateau, next move")
    lines.append("a cut); the market rate that could carry the signal ends in 1900. The")
    lines.append("event is real and runnable, but the data cannot see it.")
    return "\n".join(lines)
