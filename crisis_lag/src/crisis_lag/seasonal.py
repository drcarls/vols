"""Deseasonalise a series against a *control-year* norm before measuring stress.

Money-market rates (and, more weakly, bond spreads) tighten every autumn. Since a
crisis onset in summer is baselined on the calm spring and its peak is searched
into the autumn, that seasonal tightening masquerades as crisis stress — the raw
Berlin rate "spiked" into September 1911, but it rose *more* in the calm year 1910
(pure seasonality) than in the Agadir year.

The fix here is a seasonal, control-year baseline. Estimate the normal value for
each calendar unit (month, or ISO week) from the years that contain **no coded
crisis**, subtract it, and hand the residual series to the existing baseline/peak
machinery. Because the pre-onset baseline is then computed on the *residual*, the
crisis year's own level offset is differenced out too — so what remains is a
difference-in-differences: how much the crisis window deviates from the seasonal
norm, relative to how much the same year deviated *before* onset.

This reduces to the plain method when the seasonal index is flat, so it is a
strict generalisation. The estimator is a simple calendar-unit mean — transparent
and robust with a handful of years; nothing fancier is warranted at this n.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from statistics import mean
from typing import Dict, FrozenSet, Iterable, List, Set, Tuple

from .series import Observation

VALID_UNITS = ("month", "week")


def unit_key(d: date, unit: str = "month") -> int:
    """Calendar-unit key for a date: month 1–12, or ISO week 1–53."""
    if unit == "month":
        return d.month
    if unit == "week":
        return d.isocalendar()[1]
    raise ValueError(f"unit must be one of {VALID_UNITS}, got {unit!r}")


def crisis_years(onsets: Iterable[str]) -> Set[int]:
    """Years to exclude from the seasonal norm: those with a coded onset."""
    out: Set[int] = set()
    for o in onsets:
        try:
            out.add(date.fromisoformat(o).year)
        except ValueError:
            continue
    return out


def seasonal_index(
    obs: List[Observation],
    *,
    exclude_years: FrozenSet[int] = frozenset(),
    unit: str = "month",
) -> Dict[int, float]:
    """Mean value per calendar unit over the *control* years (those not excluded).

    Returns ``{unit_key: mean}``; a unit with no control-year observation is
    absent (its dates cannot be adjusted and are dropped by :func:`deseasonalize`).
    """
    buckets: Dict[int, List[float]] = defaultdict(list)
    for d, v in obs:
        if d.year in exclude_years:
            continue
        buckets[unit_key(d, unit)].append(v)
    return {k: mean(vs) for k, vs in buckets.items() if vs}


def deseasonalize(
    obs: List[Observation],
    index: Dict[int, float],
    *,
    unit: str = "month",
) -> List[Observation]:
    """Subtract the seasonal norm from each observation.

    Observations whose calendar unit is absent from ``index`` are dropped — the
    norm is undefined there, and imputing one would invent stress.
    """
    out: List[Observation] = []
    for d, v in obs:
        k = unit_key(d, unit)
        if k in index:
            out.append((d, v - index[k]))
    return out


def control_year_count(
    obs: List[Observation], exclude_years: FrozenSet[int]
) -> int:
    """How many distinct control years back the seasonal norm (for reporting)."""
    return len({d.year for d, _ in obs if d.year not in exclude_years})
