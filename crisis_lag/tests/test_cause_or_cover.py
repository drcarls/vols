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


def _neutral_pct(crisis_name, window):
    ym = cc.load_long_csv(cc.YIELDS_WITH_NEUTRAL)
    c = next(x for x in cc.CLIMB_DOWNS if x.crisis == crisis_name)
    _eff, pct, _n = cc.neutral_benchmark_check(ym, c.series, c.onset, window)
    return pct


def test_neutral_benchmark_holds_for_the_three_stressed_powers():
    # Germany/Russia at 180d, Austria at its slow 270d horizon: all clearly
    # above-normal (>=70th percentile) vs a neutral (Dutch) benchmark.
    assert _neutral_pct("Agadir_1911", 180) >= 80
    assert _neutral_pct("Bosnia_1909", 180) >= 70
    assert _neutral_pct("Balkans_1912_13", 270) >= 80


def test_neutral_benchmark_france_is_the_clean_null():
    # France (Morocco) below normal at every horizon -> no own-market stress.
    for W in (90, 180, 270):
        assert _neutral_pct("Morocco_1905", W) <= 30


def test_austria_signal_is_horizon_dependent_slow_to_build():
    # Austria shows nothing early (90d) but is strong by 270d -- the slow build.
    assert _neutral_pct("Balkans_1912_13", 90) <= 20
    assert _neutral_pct("Balkans_1912_13", 270) >= 80


def test_austria_spread_breaks_its_declining_trend():
    # The robust backbone: Austria bottoms in 1912 then rises 1913 -> 1914.
    series = cc.load_long_csv(cc.SPREADS)
    ym = cc.yearly_means(series["austria_hungary"])
    assert ym[1912] < ym[1913] < ym[1914]
