"""Adjudicate the thesis from the measured lags.

The claim has two halves, and the verdict checks both:

1. **Regularity** — across the measurable comparators, is the onset→peak-stress
   lag consistently in the predicted band (default 6–10 weeks)? The mechanism
   requires the brake to need *weeks*; if any comparator peaked in days, a crisis
   could have engaged the brake inside July 1914's window and the mechanism
   collapses.
2. **Contrast** — is July 1914's decision window an order of magnitude shorter
   than the comparators' lags?

The verdict is deliberately conservative: it reports CORROBORATED only when the
comparator lags all clear a floor clearly longer than the 1914 window, and
FALSIFIED when any comparator's lag is short enough that the brake could have
bitten in five days. Everything else is INCONCLUSIVE — which, with a handful of
comparators and monthly data, is an honest outcome.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import List, Optional

from .lag import LagResult

CORROBORATED = "CORROBORATED"
FALSIFIED = "FALSIFIED"
INCONCLUSIVE = "INCONCLUSIVE"


@dataclass(frozen=True)
class Verdict:
    verdict: str
    band_lo_weeks: float
    band_hi_weeks: float
    falsify_floor_weeks: float
    comparator_lags_weeks: List[float]
    n_in_band: int
    n_comparators: int
    mean_lag_weeks: Optional[float]
    min_lag_weeks: Optional[float]
    decision_window_weeks: Optional[float]
    rationale: str


def adjudicate(
    results: List[LagResult],
    *,
    band_lo_weeks: float = 6.0,
    band_hi_weeks: float = 10.0,
    falsify_floor_weeks: float = 2.0,
    lag_measure: str = "peak",  # "peak" or "material"
) -> Verdict:
    """Reduce lag results to a single verdict on the mechanism."""
    def lag_weeks(r: LagResult) -> Optional[float]:
        return r.lag_to_peak_weeks if lag_measure == "peak" else r.lag_to_material_weeks

    comparators = [r for r in results if r.measurable and r.status == "ok"]
    lags = [lag_weeks(r) for r in comparators]
    lags = [x for x in lags if x is not None]

    censored = [r for r in results if not r.measurable]
    dw = next(
        (r.decision_window_weeks for r in censored if r.decision_window_weeks is not None),
        None,
    )

    n = len(lags)
    in_band = sum(1 for x in lags if band_lo_weeks <= x <= band_hi_weeks)
    mn = min(lags) if lags else None
    mean_lag = mean(lags) if lags else None

    if n == 0:
        return Verdict(
            INCONCLUSIVE, band_lo_weeks, band_hi_weeks, falsify_floor_weeks,
            [], 0, 0, None, None, dw,
            "No comparator lag could be measured — dataset missing or windows empty.",
        )

    # FALSIFIED: some crisis peaked fast enough that the brake could bite in days.
    if mn is not None and mn < falsify_floor_weeks:
        return Verdict(
            FALSIFIED, band_lo_weeks, band_hi_weeks, falsify_floor_weeks,
            lags, in_band, n, mean_lag, mn, dw,
            (
                f"A comparator peaked in {mn:.1f} weeks (< {falsify_floor_weeks:g}), "
                "so financial stress could have become material within a July-1914-"
                "length window. The 'brake needs weeks' mechanism is not supported."
            ),
        )

    # CORROBORATED: every comparator lag clears the floor AND is longer than the
    # 1914 decision window by a clear margin.
    all_clear_floor = all(x >= falsify_floor_weeks for x in lags)
    contrast_ok = dw is None or (mn is not None and mn >= max(2.0 * dw, falsify_floor_weeks))
    if all_clear_floor and contrast_ok and in_band >= max(1, n - 1):
        return Verdict(
            CORROBORATED, band_lo_weeks, band_hi_weeks, falsify_floor_weeks,
            lags, in_band, n, mean_lag, mn, dw,
            (
                f"{in_band}/{n} comparator lags fall in {band_lo_weeks:g}-{band_hi_weeks:g} "
                f"weeks (min {mn:.1f}); "
                + (
                    f"the July 1914 window ({dw:.1f} wk) is far shorter."
                    if dw is not None
                    else "no 1914 window supplied for contrast."
                )
            ),
        )

    return Verdict(
        INCONCLUSIVE, band_lo_weeks, band_hi_weeks, falsify_floor_weeks,
        lags, in_band, n, mean_lag, mn, dw,
        (
            f"Lags cleared the {falsify_floor_weeks:g}-week floor but were not tight in "
            f"the {band_lo_weeks:g}-{band_hi_weeks:g} band ({in_band}/{n} in band). "
            "Suggestive, not demonstrated — widen the comparator set or sharpen "
            "resolution in the crisis weeks."
        ),
    )


def format_table(results: List[LagResult], lag_measure: str = "peak") -> str:
    """Render the per-crisis lag table as fixed-width text."""
    hdr = f"{'crisis':<18}{'series':<16}{'onset':<12}{'status':<11}{'peak':<12}{'lag(wk)':>8}{'material(wk)':>14}"
    lines = [hdr, "-" * len(hdr)]
    for r in results:
        lag = r.lag_to_peak_weeks if lag_measure == "peak" else r.lag_to_material_weeks
        lag_s = f"{lag:.1f}" if lag is not None else "-"
        mat_s = f"{r.lag_to_material_weeks:.1f}" if r.lag_to_material_weeks is not None else "-"
        if not r.measurable:
            dw = r.decision_window_weeks
            peak_s = f"window {dw:.1f}wk" if dw is not None else "censored"
        else:
            peak_s = r.peak_date or "-"
        lines.append(
            f"{r.name:<18}{r.series:<16}{r.onset:<12}{r.status:<11}{peak_s:<12}{lag_s:>8}{mat_s:>14}"
        )
    return "\n".join(lines)


def format_verdict(v: Verdict) -> str:
    parts = [
        f"VERDICT: {v.verdict}",
        f"  comparators measured : {v.n_comparators}",
        f"  lags (weeks)         : "
        + (", ".join(f"{x:.1f}" for x in v.comparator_lags_weeks) or "none"),
    ]
    if v.mean_lag_weeks is not None:
        parts.append(
            f"  mean / min lag       : {v.mean_lag_weeks:.1f} / {v.min_lag_weeks:.1f} wk"
        )
    parts.append(
        f"  in {v.band_lo_weeks:g}-{v.band_hi_weeks:g} wk band  : {v.n_in_band}/{v.n_comparators}"
    )
    if v.decision_window_weeks is not None:
        parts.append(f"  July 1914 window     : {v.decision_window_weeks:.1f} wk")
    parts.append(f"  {v.rationale}")
    return "\n".join(parts)
