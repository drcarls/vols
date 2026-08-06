"""Pin the cause-or-cover timing test — what the market data can/can't say.

Asserts the asymmetric finding: no crisis shows stress becoming material only
AFTER the climb-down (so no support for pure 'cover'); Russia and Austria are
materially stressed well before; France's OWN yield shows no material stress
(the case that leans toward the objection). Skips if the workbook is absent.
"""

import datetime
import os

import pytest

import cause_or_cover as cc

BONDS = os.path.join(os.path.dirname(__file__), "..", "..", "neal_weidenmier",
                     "data", "longtermbonds.xls")

pytestmark = pytest.mark.skipif(
    not os.path.exists(BONDS) or not os.path.exists(cc.SPREADS),
    reason="mirrored workbook / built spreads not present",
)


def test_no_crisis_has_stress_only_after_climbdown():
    # The refuting pattern (pure 'cover') appears in neither measure.
    for path in (cc.SPREADS, cc.YIELDS):
        for c, mat, cd, gap, verdict in cc.run(path):
            if mat is not None:
                assert mat <= cd, f"{c.crisis} on {path}: material {mat} after climb-down {cd}"


def test_russia_bosnia_flag_does_not_survive_the_control_check():
    # The z>2 lead is an artifact: the 1908 Russian spread sat BELOW calm control
    # years, so the crisis peak is NOT distinctive.
    series = cc.load_long_csv(cc.SPREADS)
    ru = next(c for c in cc.CLIMB_DOWNS if c.crisis == "Bosnia_1909")
    peak, controls, distinct = cc.control_check(series[ru.series], ru.onset)
    assert distinct is False
    assert peak < max(p for _, p in controls)   # crisis below the calm-year peak


def test_austria_balkans_is_the_one_distinctive_case_on_yield():
    series = cc.load_long_csv(cc.YIELDS)
    au = next(c for c in cc.CLIMB_DOWNS if c.crisis == "Balkans_1912_13")
    _peak, _controls, distinct = cc.control_check(series[au.series], au.onset)
    assert distinct is True


def test_austria_spread_breaks_its_declining_trend():
    # The robust backbone: Austria bottoms in 1912 then rises 1913 -> 1914.
    series = cc.load_long_csv(cc.SPREADS)
    ym = cc.yearly_means(series["austria_hungary"])
    assert ym[1912] < ym[1913] < ym[1914]


def test_france_own_yield_shows_no_material_stress_in_1905():
    # Morocco/France on RAW yield: France's own borrowing cost never crosses z>2
    # -> French finances were not the binding constraint (leans to the objection).
    rows = {c.crisis: mat for c, mat, cd, gap, v in cc.run(cc.YIELDS)}
    assert rows["Morocco_1905"] is None
