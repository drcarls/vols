"""Bonds vs commercial paper — the instrument that carries the brake.

Asserts the key contrast: on the neutral-benchmarked cause-or-cover, Austria's
money-market (commercial-paper) stress arrives FAST (within 90 days) where its
bond stress was slow (only by 270 days). Skips if the workbook is absent.
"""

import os

import pytest

import build_nw_money as bm
import cause_or_cover as cc

SHORT = os.path.join(os.path.dirname(__file__), "..", "..", "neal_weidenmier",
                     "data", "stinterestrates.xls")
MM_YIELDS = os.path.join(os.path.dirname(__file__), "..", "data", "mm_yields_long.csv")

pytestmark = pytest.mark.skipif(
    not os.path.exists(SHORT), reason="mirrored short-rate workbook not present"
)


def _mm_pct(crisis_name, window):
    ym = cc.load_long_csv(MM_YIELDS)
    c = next(x for x in cc.CLIMB_DOWNS if x.crisis == crisis_name)
    _eff, pct, _n = cc.neutral_benchmark_check(ym, c.series, c.onset, window)
    return pct


def test_money_market_series_build():
    spreads, yields_ = bm.build(SHORT)
    assert spreads and yields_
    assert any(s == "dutch" for _d, s, _v in yields_)          # Amsterdam neutral present
    assert {s for _d, s, _v in yields_} >= {"germany", "france", "austria_hungary"}


def test_austria_stress_is_fast_on_commercial_paper():
    # Money market: abnormal within 90 days (where bonds only reached it by 270).
    assert _mm_pct("Balkans_1912_13", 90) >= 80


def test_france_stays_weak_on_commercial_paper_too():
    assert _mm_pct("Morocco_1905", 90) <= 30
