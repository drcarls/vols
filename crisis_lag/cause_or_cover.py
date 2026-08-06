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
        for c, mat, cd, gap, verdict in run(path):
            g = f"({gap} days before)" if gap is not None else ""
            print(f"{c.crisis:<17}{c.power:<16} climb-down {cd}  material {str(mat):<12} {g}")
            print(f"    -> {verdict}")
        print()
    print("Reading it: 'material before' is CONSISTENCY with finance-as-cause, never proof —")
    print("a government can climb down on diplomatic grounds while its bonds happen to be")
    print("stressed. Only 'material only after' would REFUTE finance-as-cause, and no crisis")
    print("shows that. Measure matters: Agadir/Germany crosses on raw yield (~8 wk, the 1911")
    print("bourse panic) but NOT on the spread — British consols sold off with it. Morocco/")
    print("France is 'material at onset' (degenerate) and confounded by the 1905 revolution.")
    print("Bottom line: the data is consistent with finance-as-constraint and does not support")
    print("pure 'cover', but it CANNOT establish intent. That is an archival question.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
