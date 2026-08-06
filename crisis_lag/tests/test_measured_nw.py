"""Pin the measured NW transmission lags — the '6-10 weeks' claim, run on data.

Not synthetic: builds sovereign spreads from the mirrored Neal-Weidenmier bonds
and asserts what the data actually shows — peak lags of ~16-37 weeks, none in the
asserted 6-10 week band. Skips cleanly if the mirrored workbook is absent.
"""

import os

import pytest

from crisis_lag.events import DEFAULT_EVENTS
from crisis_lag.lag import measure_all

import build_nw_spreads as b
from crisis_lag.series import rows_to_series

BONDS = os.path.join(os.path.dirname(__file__), "..", "..", "neal_weidenmier",
                     "data", "longtermbonds.xls")

pytestmark = pytest.mark.skipif(
    not os.path.exists(BONDS), reason="mirrored bond workbook not present"
)


_COMPARATORS = ("Morocco_1905", "Bosnia_1908", "Agadir_1911", "Balkans_1912_13")


def _results():
    rows = [{"date": d, "series": s, "value": str(v)} for d, s, v in b.build(BONDS)]
    series = rows_to_series(rows)
    return {r.name: r for r in measure_all(series, DEFAULT_EVENTS)}


def test_measured_peak_lags_are_far_longer_than_6_to_10_weeks():
    res = _results()
    peaks = {name: res[name].lag_to_peak_weeks for name in _COMPARATORS}
    # every measured peak lag exceeds the asserted 6-10 week band
    for name, wk in peaks.items():
        assert wk is not None and wk > 12.0, f"{name}: {wk}"
    # none falls inside 6-10 weeks
    assert not any(6.0 <= wk <= 10.0 for wk in peaks.values())


def test_july_1914_window_is_far_shorter_than_any_measured_lag():
    res = _results()
    win = res["July_1914"].decision_window_weeks
    assert win is not None and win < 1.0
    peaks = [res[n].lag_to_peak_weeks for n in _COMPARATORS]
    assert win < min(peaks)   # the directional argument survives
