"""Turn a raw spread series into an *abnormal* stress series.

A raw maximum is not evidence of crisis stress — the series has a baseline level
and its own volatility. So for each crisis we characterise a pre-onset baseline
window and express stress relative to it:

* ``abnormal`` = value − baseline_mean   (level above normal)
* ``z``        = (value − baseline_mean) / baseline_sd

"Stress rising" means the spread widening (``value`` increasing), which is the
convention for sovereign spreads and yields. The baseline is drawn strictly
*before* onset, so the peak search cannot leak into the normalisation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from statistics import mean, pstdev
from typing import List, Optional

from .events import CrisisEvent
from .series import Observation, window


@dataclass(frozen=True)
class Baseline:
    n: int
    mean: float
    sd: float
    start: date
    end: date


@dataclass(frozen=True)
class StressPoint:
    date: date
    value: float
    abnormal: float
    z: Optional[float]  # None when baseline sd is 0 (undefined)


def baseline_for(obs: List[Observation], event: CrisisEvent) -> Optional[Baseline]:
    """Compute the pre-onset baseline for ``event`` from ``obs``.

    Returns ``None`` if the baseline window holds no observations.
    """
    onset = event.onset_date()
    start = onset - timedelta(days=event.baseline_start_days)
    end = onset - timedelta(days=event.baseline_end_days)
    base = window(obs, start, end)
    if not base:
        return None
    values = [v for (_d, v) in base]
    m = mean(values)
    sd = pstdev(values) if len(values) > 1 else 0.0
    return Baseline(n=len(values), mean=m, sd=sd, start=start, end=end)


def stress_series(
    obs: List[Observation], event: CrisisEvent, baseline: Baseline
) -> List[StressPoint]:
    """Express the post-onset search window as abnormal stress vs ``baseline``."""
    onset = event.onset_date()
    end = onset + timedelta(days=event.search_days)
    search = window(obs, onset, end)
    points: List[StressPoint] = []
    for d, v in search:
        abnormal = v - baseline.mean
        z = (abnormal / baseline.sd) if baseline.sd > 0 else None
        points.append(StressPoint(date=d, value=v, abnormal=abnormal, z=z))
    return points
