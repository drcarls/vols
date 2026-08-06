"""The UK is a contaminated benchmark — it moves when Britain is involved.

Pins two facts: the UK bond is distinctive in Agadir (Britain was a party) but
NOT in the Balkans (Britain detached); and re-benchmarking Morocco's lag from
British consols to the Dutch neutral shortens it sharply. Skips if absent.
"""

import datetime
import os

import pytest

import build_nw_spreads as b
import cause_or_cover as cc

BONDS = os.path.join(os.path.dirname(__file__), "..", "..", "neal_weidenmier",
                     "data", "longtermbonds.xls")

pytestmark = pytest.mark.skipif(
    not os.path.exists(BONDS), reason="mirrored bond workbook not present"
)


def _uk_and_dutch_yields():
    data = b._text_dates_and_prices(BONDS)
    uk = [(d, 2.75 / data[d][3] * 100) for d in sorted(data) if data[d].get(3)]
    dutch = [(datetime.date.fromisoformat(r[0]), r[2]) for r in b._dutch_neutral(BONDS)]
    return {"uk": uk, "dutch": dutch}


def test_uk_moves_in_agadir_but_not_the_balkans():
    ym = _uk_and_dutch_yields()
    _e, agadir, _n = cc.neutral_benchmark_check(ym, "uk", "1911-07-01", 180)
    _e, balkans, _n = cc.neutral_benchmark_check(ym, "uk", "1912-10-08", 180)
    assert agadir >= 75          # Britain was a party to Agadir
    assert balkans <= 20         # Britain detached from the Balkans


def test_morocco_lag_shortens_under_a_neutral_benchmark():
    # British-benchmarked Morocco lag is ~16 wk; Dutch-benchmarked is ~3 wk.
    data = b._text_dates_and_prices(BONDS)
    dutch = {datetime.date.fromisoformat(r[0]): r[2] for r in b._dutch_neutral(BONDS)}

    def asof(m, d, tol=20):
        best = None
        for dd, v in m.items():
            delta = abs((dd - d).days)
            if delta <= tol and (best is None or delta < best[0]):
                best = (delta, v)
        return best[1] if best else None

    rows = []
    for d in sorted(data):
        nd = asof(dutch, d)
        p = data[d].get(15)  # Russian New 4%, coupon 4
        if nd is not None and p:
            rows.append({"date": d.isoformat(), "series": "russia",
                         "value": str(round(4.0 / p * 100 - nd, 4))})
    from crisis_lag.series import rows_to_series
    from crisis_lag.lag import measure_lag
    from crisis_lag.events import CrisisEvent
    series = rows_to_series(rows)
    ev = CrisisEvent(name="Morocco", onset="1905-03-31", series="russia",
                     binding_power="France/Russia")
    res = measure_lag(series["russia"], ev)
    assert res.lag_to_peak_weeks is not None and res.lag_to_peak_weeks < 8
