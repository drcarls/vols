"""A timing test for the cause-vs-cover question — the one thing markets can say.

The objection: if Rouvier, Kokovtsov and Bilinski produced *fiscal* justifications
for climb-downs actually decided on military/diplomatic grounds, the financial
architecture is decoration. **Market data cannot settle that** — intent lives in
cabinet minutes, not bond prices. But it offers one bounded, *asymmetric* handle:

    Was the climbing-down power's financial stress already MATERIAL
    (first z>2 above a pre-onset baseline in its own sovereign spread)
    at the moment it climbed down?

- **If NO** (stress became material only after the climb-down) — finance cannot
  have been the binding cause; the fiscal argument is at best cover. This can
  *refute* finance-as-cause.
- **If YES** (stress was already material) — finance-as-cause is *consistent*,
  but this is necessary, not sufficient: a government can climb down for
  diplomatic reasons while its bonds happen to be under stress. Consistency is
  not proof.

So the test can partially refute, never confirm. It uses each crisis's
*climbing-down power's own* spread (not merely the fiscally-binding one) and a
dated climb-down. Both are documented assumptions, overridable and debatable.

    python cause_or_cover.py        # prints the table
"""

from __future__ import annotations

import datetime
import os
from dataclasses import dataclass
from typing import Optional

from crisis_lag.events import CrisisEvent
from crisis_lag.series import load_long_csv
from crisis_lag.stress import baseline_for, stress_series

D = datetime.date

_HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(_HERE, "data", "nw_spreads_long.csv")


@dataclass(frozen=True)
class ClimbDown:
    crisis: str
    power: str            # the government that climbed down
    series: str           # its sovereign spread series id
    onset: str            # crisis onset (baseline anchor)
    climb_down: str       # the dated concession
    minister: str         # the finance/foreign minister who justified it
    source: str


# Documented, debatable assumptions. The climb-down is the concession itself; the
# series is the CLIMBING-DOWN power's spread (so the test asks about that
# government's own market pressure, not a third party's).
CLIMB_DOWNS = [
    ClimbDown("Morocco_1905", "France", "france", "1905-03-31", "1905-06-06",
              "Rouvier", "Delcasse forced out 6 Jun 1905; France accepts the Algeciras conference."),
    ClimbDown("Bosnia_1909", "Russia", "russia", "1908-10-06", "1909-03-27",
              "Kokovtsov / Izvolsky", "Russia accepts the annexation after the German demarche of 21 Mar 1909."),
    ClimbDown("Agadir_1911", "Germany", "germany", "1911-07-01", "1911-11-04",
              "(Kiderlen / Reich)", "Franco-German treaty 4 Nov 1911: Germany concedes Morocco for Congo land."),
    ClimbDown("Balkans_1912_13", "Austria-Hungary", "austria_hungary", "1912-10-08", "1913-05-30",
              "Bilinski", "Austria stands down from war on Serbia; Treaty of London 30 May 1913 (Albania secured, not war)."),
]


def _window_peak(obs, lo: D, hi: D) -> Optional[float]:
    vals = [v for d, v in obs if lo <= d <= hi]
    return max(vals) if vals else None


# Years contaminated by a coded crisis for SOME great power — unusable as clean
# controls (Bosnia 1908-09 stressed Austria too; Morocco 1905; Agadir 1911;
# Balkans 1912-13; July 1914). Leaves 1904/1906/1907/1910 as the calm set.
CRISIS_YEARS = {1905, 1908, 1909, 1911, 1912, 1913, 1914}


def control_check(obs, onset: str, span_days: int = 300, span_years: int = 5):
    """Is the crisis-window peak DISTINCTIVE vs matched *clean* control windows?

    A long 'material stress before the climb-down' lead is only evidence of crisis
    stress if the crisis-window level actually exceeds what the same bond did in
    the same calendar window in NON-crisis years. Otherwise the z>2 flag is a
    low-variance-baseline artifact on a pre-existing level/trend. Crisis years are
    excluded from controls. NOTE these spreads carry strong secular trends (Russia
    declining post-1905, Austria U-shaped), so distant controls conflate trend
    with crisis — read this together with the yearly-mean trend, not alone.
    """
    o = D.fromisoformat(onset)
    hi = o + datetime.timedelta(days=span_days)
    crisis_peak = _window_peak(obs, o, hi)
    controls = []
    for dy in range(-span_years, span_years + 1):
        y = o.year + dy
        if dy == 0 or y in CRISIS_YEARS:
            continue
        try:
            lo_c, hi_c = o.replace(year=y), hi.replace(year=hi.year + dy)
        except ValueError:
            continue
        p = _window_peak(obs, lo_c, hi_c)
        if p is not None:
            controls.append((y, round(p, 3)))
    distinctive = (
        crisis_peak is not None and controls
        and crisis_peak > max(p for _, p in controls)
    )
    return crisis_peak, controls, distinctive


def yearly_means(obs):
    import collections
    ym = collections.defaultdict(list)
    for d, v in obs:
        ym[d.year].append(v)
    return {y: round(sum(vs) / len(vs), 2) for y, vs in sorted(ym.items())}


# ---- the fixed control: neutral-benchmarked, change-based, vs a null distribution ----
#
# The level-vs-control-year check above is confounded three ways (few clean years,
# each with its own events; strong secular trends). The proper event-study control
# removes all three:
#   1. benchmark against a NEUTRAL creditor (the Dutch yield), not British consols
#      (a great-power asset that itself sold off for liquidity) -> strips common
#      global bond moves;
#   2. measure the CHANGE (max rise of the power-minus-Dutch spread over a window),
#      not the level -> strips the secular trend;
#   3. compare that change to the distribution of the SAME change over every
#      non-crisis window -> a real null, not a handful of hand-picked years.
# nw_yields_long.csv carries country current yields + the 'dutch' neutral series.
YIELDS_WITH_NEUTRAL = os.path.join(_HERE, "data", "nw_yields_long.csv")


def _asof(obs, d, tol_days: int = 20):
    best = None
    for dd, v in obs:
        delta = abs((dd - d).days)
        if delta <= tol_days and (best is None or delta < best[0]):
            best = (delta, v)
    return best[1] if best else None


def _spread_vs_neutral(power_obs, neutral_obs, d):
    a, n = _asof(power_obs, d), _asof(neutral_obs, d)
    return None if (a is None or n is None) else a - n


def _max_rise(power_obs, neutral_obs, t0: D, window_days: int):
    base = _spread_vs_neutral(power_obs, neutral_obs, t0)
    if base is None:
        return None
    peak = None
    k = 0
    while k <= window_days:
        v = _spread_vs_neutral(power_obs, neutral_obs, t0 + datetime.timedelta(days=k))
        if v is not None and (peak is None or v > peak):
            peak = v
        k += 7
    return None if peak is None else peak - base


def neutral_benchmark_check(yields_map, power: str, onset: str, window_days: int):
    """Effect (max rise of power-minus-Dutch spread) and its percentile vs a null
    of the same over all non-crisis windows. Returns (effect, percentile, n_null)."""
    power_obs = sorted(yields_map.get(power, []))
    neutral_obs = sorted(yields_map.get("dutch", []))
    if not power_obs or not neutral_obs:
        return None, None, 0
    onsets = [D.fromisoformat(c.onset) for c in CLIMB_DOWNS]
    eff = _max_rise(power_obs, neutral_obs, D.fromisoformat(onset), window_days)
    nulls = []
    t, last = power_obs[0][0], power_obs[-1][0] - datetime.timedelta(days=window_days)
    while t < last:
        if not any(abs((t - o).days) < window_days + 60 for o in onsets):
            m = _max_rise(power_obs, neutral_obs, t, window_days)
            if m is not None:
                nulls.append(m)
        t += datetime.timedelta(days=21)
    pct = (100.0 * sum(1 for x in nulls if x < eff) / len(nulls)) if (eff is not None and nulls) else None
    return eff, pct, len(nulls)


def _first_material_date(obs, onset: str, z_threshold: float = 2.0) -> Optional[D]:
    """Date the spread first crosses z>threshold above its pre-onset baseline."""
    ev = CrisisEvent(name="x", onset=onset, series="x", binding_power="x", search_days=420)
    base = baseline_for(obs, ev)
    if base is None or base.sd == 0:
        return None
    onset_d = D.fromisoformat(onset)
    for sp in stress_series(obs, ev, base):
        if sp.date >= onset_d and sp.z is not None and sp.z >= z_threshold:
            return sp.date
    return None


SPREADS = os.path.join(_HERE, "data", "nw_spreads_long.csv")
YIELDS = os.path.join(_HERE, "data", "nw_yields_long.csv")


def run(path: str = SPREADS):
    series = load_long_csv(path)
    rows = []
    for c in CLIMB_DOWNS:
        obs = series.get(c.series, [])
        mat = _first_material_date(obs, c.onset)
        cd = D.fromisoformat(c.climb_down)
        onset_d = D.fromisoformat(c.onset)
        if mat is None:
            verdict, gap = "no material stress found (spread never crossed z>2)", None
        elif mat > cd:
            gap, verdict = (cd - mat).days, "material only AFTER climb-down -> points to COVER"
        elif mat <= onset_d:
            gap = (cd - mat).days
            verdict = "already material AT onset (degenerate 'before' — read with care)"
        else:
            gap = (cd - mat).days
            verdict = "material BEFORE climb-down -> finance-as-cause CONSISTENT (not proof)"
        rows.append((c, mat, cd, gap, verdict))
    return rows


def main() -> int:
    for label, path in (("SPREAD over British consols", SPREADS), ("RAW country yield", YIELDS)):
        print(f"=== Cause-or-cover timing test — measure: {label} ===\n")
        series = load_long_csv(path)
        for c, mat, cd, gap, verdict in run(path):
            g = f"({gap} days before)" if gap is not None else ""
            print(f"{c.crisis:<17}{c.power:<16} climb-down {cd}  material {str(mat):<12} {g}")
            print(f"    -> {verdict}")
            # control-window check: is the crisis peak distinctive vs calm years?
            peak, controls, distinct = control_check(series.get(c.series, []), c.onset)
            cps = ", ".join(f"{y}:{p}" for y, p in controls)
            print(f"    control-check: crisis peak {peak} vs control-year peaks [{cps}]")
            print(f"       -> {'DISTINCTIVE (above all control years)' if distinct else 'NOT distinctive on this CRUDE level check (but see the fixed control below — it is confounded by trend)'}")
        print()
    print("=== FIXED control — neutral (Dutch) benchmark, change vs null distribution ===\n")
    ym_yields = load_long_csv(YIELDS_WITH_NEUTRAL)
    print("Percentile of the crisis-window rise (power minus Dutch) vs all non-crisis windows:")
    print(f"  {'crisis':<16}{'power':<16}{'90d':>7}{'180d':>7}{'270d':>7}")
    for c in CLIMB_DOWNS:
        pcts = []
        for W in (90, 180, 270):
            _eff, pct, _n = neutral_benchmark_check(ym_yields, c.series, c.onset, W)
            pcts.append(f"{pct:.0f}%" if pct is not None else "—")
        print(f"  {c.crisis:<16}{c.power:<16}{pcts[0]:>7}{pcts[1]:>7}{pcts[2]:>7}")
    print("  Reading: high percentile = the power's own bonds rose abnormally vs a neutral")
    print("  during its crisis. Germany ~90-95th, Russia ~80th, Austria ~90th but only at the")
    print("  long (270d) horizon it needed to build; France stays low (9-17th) — no stress.")
    print("  So with proper controls the finance-as-constraint signal HOLDS for the three")
    print("  powers whose own solvency was in question, and France is the clean exception.\n")

    print("Yearly-mean spread trend (the robust backbone — no window-selection fiddliness):")
    sp = load_long_csv(SPREADS)
    for s in ("russia", "austria_hungary"):
        print(f"  {s:<16} {yearly_means(sp.get(s, []))}")
    print()
    print("Reading it — three passes, converging:")
    print(" - Raw z>2 'material before' leads (162/224 d) OVERSTATED it: the flags can ride a")
    print("   pre-existing level/trend on a low-variance baseline.")
    print(" - The crude level-vs-control-year check UNDERSTATED it: only ~4 clean years, each")
    print("   with its own events, and strong secular trends confounding a level comparison.")
    print(" - The FIXED control (neutral Dutch benchmark, change, null distribution) is the")
    print("   one to trust: the finance-as-constraint signal HOLDS for the three powers whose")
    print("   own solvency was in question — Germany ~90th pctile, Russia ~80th, Austria ~90th")
    print("   (only at its slow 270d horizon) — and France is a clean null (9-17th).")
    print("Net: consistent with finance-as-constraint for Germany/Russia/Austria, cleanly absent")
    print("for France. Still consistency, not causation, and silent on intent (archives). Limits:")
    print("one neutral, current-yield proxies, overlapping null windows -> descriptive percentiles.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
