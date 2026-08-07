"""The blockade / trade-exposure test: premium vs 1913 Central-Powers trade share.

Pins the sourced result: within the eight European neutrals the premium is
positively correlated with Central-Powers trade dependence (COW 1913), and the
US is the negative-premium / high-trade break. Skips if the workbook is absent.
"""

import os

import pytest

import trade_exposure as te

pytestmark = pytest.mark.skipif(
    not (os.path.exists(te.SHORT) and os.path.exists(te.SHARES)),
    reason="short-rate workbook / trade shares not present",
)


def test_premium_rises_with_central_powers_trade_among_neutrals():
    data = [d for d in te.load() if d["type"] == "neut"]
    ys = [d["beta"] for d in data]
    xs = [d["pct_central"] for d in data]
    r = te._pearson(ys, xs)
    assert r > 0.4                       # right sign, moderate-to-strong
    assert te._tstat(r, len(data)) > 1.5


def test_us_is_the_break_high_trade_negative_premium():
    us = next(d for d in te.load() if d["country"] == "USA")
    assert us["beta"] < 0                 # negative premium (war supplier)
    assert us["pct_bellig"] > 40          # despite high belligerent trade
