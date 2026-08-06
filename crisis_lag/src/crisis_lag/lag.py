"""Measure the lag from crisis onset to peak financial stress.

Two lag measures per crisis, both pre-registered:

* **time-to-peak** — days from onset to the maximum spread level within the
  search window. The headline number.
* **time-to-material** — days from onset to the *first* date the abnormal spread
  crosses ``z_threshold`` standard deviations above baseline. Arguably the better
  "when did the squeeze start to bite" measure, and robust to a late blow-off.

Both are reported in weeks, since the claim is stated in weeks (~6–10).

July-1914-style events (``measurable=False``) are not measured — the market
closed, so the peak is right-censored. They carry a decision-window length
instead, which the report contrasts against the comparators' lags.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .events import CrisisEvent
from .series import Observation
from .stress import Baseline, StressPoint, baseline_for, stress_series


@dataclass(frozen=True)
class LagResult:
    name: str
    series: str
    onset: str
    measurable: bool
    status: str  # "ok" | "censored" | "no_baseline" | "no_data"
    n_search: int = 0
    baseline_n: int = 0
    baseline_mean: Optional[float] = None
    baseline_sd: Optional[float] = None
    peak_date: Optional[str] = None
    peak_value: Optional[float] = None
    peak_z: Optional[float] = None
    lag_to_peak_days: Optional[int] = None
    lag_to_material_days: Optional[int] = None
    decision_window_days: Optional[int] = None
    note: Optional[str] = None

    @property
    def lag_to_peak_weeks(self) -> Optional[float]:
        return None if self.lag_to_peak_days is None else self.lag_to_peak_days / 7.0

    @property
    def lag_to_material_weeks(self) -> Optional[float]:
        return (
            None
            if self.lag_to_material_days is None
            else self.lag_to_material_days / 7.0
        )

    @property
    def decision_window_weeks(self) -> Optional[float]:
        return (
            None
            if self.decision_window_days is None
            else self.decision_window_days / 7.0
        )


def _first_material(points: List[StressPoint], z_threshold: float) -> Optional[StressPoint]:
    for p in points:
        if p.z is not None and p.z >= z_threshold:
            return p
    return None


def measure_lag(
    obs: List[Observation],
    event: CrisisEvent,
    *,
    z_threshold: float = 2.0,
) -> LagResult:
    """Measure onset→peak-stress lag for one crisis.

    ``obs`` is the (date, value) series for ``event.series``. Stress is taken as
    the spread *widening*, so the peak is the maximum value in the search window.
    """
    onset = event.onset_date()

    if not event.measurable:
        return LagResult(
            name=event.name,
            series=event.series,
            onset=event.onset,
            measurable=False,
            status="censored",
            decision_window_days=event.decision_window_days,
            note=event.notes or "peak censored (market closed)",
        )

    baseline = baseline_for(obs, event)
    if baseline is None:
        return LagResult(
            name=event.name, series=event.series, onset=event.onset,
            measurable=True, status="no_baseline",
            note="no observations in the pre-onset baseline window",
        )

    points = stress_series(obs, event, baseline)
    if not points:
        return LagResult(
            name=event.name, series=event.series, onset=event.onset,
            measurable=True, status="no_data", baseline_n=baseline.n,
            baseline_mean=baseline.mean, baseline_sd=baseline.sd,
            note="no observations in the post-onset search window",
        )

    peak = max(points, key=lambda p: p.value)
    material = _first_material(points, z_threshold)

    return LagResult(
        name=event.name,
        series=event.series,
        onset=event.onset,
        measurable=True,
        status="ok",
        n_search=len(points),
        baseline_n=baseline.n,
        baseline_mean=baseline.mean,
        baseline_sd=baseline.sd,
        peak_date=peak.date.isoformat(),
        peak_value=peak.value,
        peak_z=peak.z,
        lag_to_peak_days=(peak.date - onset).days,
        lag_to_material_days=(
            None if material is None else (material.date - onset).days
        ),
        note=event.notes,
    )


def measure_all(
    series_map, events: List[CrisisEvent], *, z_threshold: float = 2.0
) -> List[LagResult]:
    """Measure lag for every event against its series in ``series_map``."""
    results: List[LagResult] = []
    for ev in events:
        obs = series_map.get(ev.series, [])
        if not obs and ev.measurable:
            results.append(
                LagResult(
                    name=ev.name, series=ev.series, onset=ev.onset,
                    measurable=True, status="no_data",
                    note=f"series {ev.series!r} absent from the dataset",
                )
            )
            continue
        results.append(measure_lag(obs, ev, z_threshold=z_threshold))
    return results
