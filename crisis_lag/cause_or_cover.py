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
            print(f"       -> {'DISTINCTIVE (above all control years)' if distinct else 'NOT distinctive (within/below control range) — the flag is an artifact'}")
        print()
    print("Yearly-mean spread trend (the robust backbone — no window-selection fiddliness):")
    sp = load_long_csv(SPREADS)
    for s in ("russia", "austria_hungary"):
        print(f"  {s:<16} {yearly_means(sp.get(s, []))}")
    print()
    print("Reading it, AFTER the control check (and holding its own limits in view):")
    print(" - A long 'material before' lead (162/224 d) is a WARNING that the z>2 flag may ride")
    print("   a pre-existing level/trend, not a warrant for it. It weakens the leads; it does")
    print("   not by itself refute them.")
    print(" - Russia/Bosnia: only a small onset blip, and the spread was near multi-year lows on")
    print("   a strong post-1905 recovery trend — so no sustained distinctive stress. But the")
    print("   control years (1906-07) were themselves elevated, so this is 'not robust', not a")
    print("   clean refutation.")
    print(" - Austria/Balkans: the strongest case — spread breaks its 1910-12 decline (0.56->")
    print("   0.70->1.00) and clears clean controls on YIELD (though not on the spread, where")
    print("   1907 is higher). Real, but slow-building and measure-dependent.")
    print(" - Germany/Agadir: small rise, above 1909-10 but on a rising secular trend — weak.")
    print(" - France/Morocco: no own stress on either measure — the firmest of these reads.")
    print("Limits of this check itself: ~4 clean years (1904/06/07/10), each with its own")
    print("events (1907 panic, 1906 Algeciras/loan), and strong secular trends that confound a")
    print("level comparison. So treat all of this as SUGGESTIVE and underpowered, in both")
    print("directions. Net: the raw leads overstated finance-as-cause; the corrected reading is")
    print("weak/mixed, not a refutation; France is the one fairly firm null. Intent needs archives.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
