"""Section 9: every IV value at time t must use only what was knowable at time t."""

from datetime import date, timedelta

import pandas as pd
import pytest

from pari_mutuel_trader.backtest.engine import run_backtest
from pari_mutuel_trader.data.features import build_features
from pari_mutuel_trader.data.loaders import generate_valuation_universe
from pari_mutuel_trader.study.conditional import forward_returns
from pari_mutuel_trader.valuation.features import Revision, attach_valuation, valuation_columns
from pari_mutuel_trader.valuation.intrinsic import ValuationInputs
from pari_mutuel_trader.valuation.quality import QualityProfile
import yaml


def world(days=400, n_symbols=20, seed=2, reversion=0.003):
    raw, funds = generate_valuation_universe(days=days, n_symbols=n_symbols, seed=seed, reversion=reversion)
    return build_features(raw), funds


def _inputs(earnings):
    return ValuationInputs(earnings, 0.10, QualityProfile(0.8, 0.25, 0.8))


# --- revisions -------------------------------------------------------------

def test_a_revision_is_invisible_before_its_own_date():
    feat, _ = world()
    symbols = sorted(set(feat.index.get_level_values("symbol")))
    dates = feat.index.get_level_values("date").unique().sort_values()
    cut = dates[len(dates) // 2]

    funds = {s: [Revision(dates[0].date() - timedelta(days=1), _inputs(5.0)),
                 Revision(cut.date(), _inputs(50.0))] for s in symbols}
    iv = attach_valuation(feat, funds)["iv8"]

    before = iv[iv.index.get_level_values("date") < cut]
    after = iv[iv.index.get_level_values("date") >= cut]
    assert before.nunique() == 1 and after.nunique() == 1
    assert after.iloc[0] > before.iloc[0] * 5   # the later, much larger estimate


def test_publication_lag_delays_when_a_figure_becomes_usable():
    """Fundamentals stamped to a period end but used from that date is the classic leak."""
    feat, _ = world()
    symbols = sorted(set(feat.index.get_level_values("symbol")))
    dates = feat.index.get_level_values("date").unique().sort_values()
    cut = dates[len(dates) // 2]
    funds = {s: [Revision(dates[0].date() - timedelta(days=1), _inputs(5.0)),
                 Revision(cut.date(), _inputs(50.0))] for s in symbols}

    prompt = attach_valuation(feat, funds, publication_lag_days=0)["iv8"]
    lagged = attach_valuation(feat, funds, publication_lag_days=60)["iv8"]

    on_cut = (slice(cut, cut), slice(None))
    assert lagged.loc[on_cut].iloc[0] < prompt.loc[on_cut].iloc[0]
    assert lagged.iloc[-1] == prompt.iloc[-1]   # both know it by the end


def test_a_revision_dated_after_the_sample_never_appears():
    feat, _ = world()
    symbols = sorted(set(feat.index.get_level_values("symbol")))
    dates = feat.index.get_level_values("date").unique().sort_values()
    funds = {s: [Revision(dates[0].date() - timedelta(days=1), _inputs(5.0)),
                 Revision(dates[-1].date() + timedelta(days=365), _inputs(500.0))] for s in symbols}
    assert attach_valuation(feat, funds)["iv8"].nunique() == 1


# --- truncation: the strongest general test --------------------------------

def test_truncating_the_sample_leaves_earlier_iv_untouched():
    """If any future information leaked in, cutting the future would change the past."""
    feat, funds = world(days=500)
    dates = feat.index.get_level_values("date").unique().sort_values()
    cut = dates[300]

    full = valuation_columns(feat, funds)
    truncated = valuation_columns(feat[feat.index.get_level_values("date") <= cut], funds)

    columns = [c for c in truncated.columns if c != "iv_agreement"]
    a = full.loc[full.index.get_level_values("date") <= cut, columns].astype(float)
    b = truncated[columns].astype(float)
    pd.testing.assert_frame_equal(a, b)


def test_truncating_the_sample_leaves_earlier_holdings_untouched():
    feat, funds = world(days=500, n_symbols=30)
    valued = attach_valuation(feat, funds)
    cfg = yaml.safe_load(open("configs/momentum.yaml"))
    cfg["portfolio"] = {**cfg["portfolio"], "top_k": 10, "min_holdings": 5}
    cfg["iv_overlay"] = {"enabled": True, "mode": "rank", "signal": "discount_to_iv8", "iv_weight": 0.25}

    dates = valued.index.get_level_values("date").unique().sort_values()
    cut = dates[300]
    full = run_backtest(valued, cfg).holdings_history
    early = run_backtest(valued[valued.index.get_level_values("date") <= cut], cfg).holdings_history

    shared = set(early) & set(full)
    assert len(shared) > 3
    for day in shared:
        assert early[day] == pytest.approx(full[day])


# --- derived columns are trailing ------------------------------------------

def test_iv_change_columns_look_backward_only():
    feat, funds = world(days=400)
    valued = attach_valuation(feat, funds)
    symbol = sorted(set(valued.index.get_level_values("symbol")))[0]
    series = valued.xs(symbol, level="symbol")
    expected = series["iv8"] / series["iv8"].shift(63) - 1.0
    pd.testing.assert_series_equal(series["iv8_chg_3m"], expected.fillna(0.0),
                                   check_names=False)


def test_forward_returns_are_forward_and_run_out_at_the_tail():
    feat, _ = world(days=300)
    fwd = forward_returns(feat, horizons=(20,))
    symbol = sorted(set(feat.index.get_level_values("symbol")))[0]
    close = feat.xs(symbol, level="symbol")["close"]
    got = fwd.xs(symbol, level="symbol")["fwd_20d"]
    assert got.iloc[0] == pytest.approx(close.iloc[20] / close.iloc[0] - 1)
    assert got.iloc[-20:].isna().all()   # nothing invented past the end of the sample


def test_forward_returns_never_reach_another_symbol():
    feat, _ = world(days=200, n_symbols=3)
    fwd = forward_returns(feat, horizons=(10,))
    for symbol in sorted(set(feat.index.get_level_values("symbol"))):
        assert fwd.xs(symbol, level="symbol")["fwd_10d"].iloc[-10:].isna().all()


# --- universe integrity ----------------------------------------------------

def test_fundamentals_for_absent_symbols_do_not_enter_the_frame():
    """Guards against a survivorship list quietly widening the universe."""
    feat, funds = world(days=200, n_symbols=10)
    funds["DELISTED"] = [Revision(date(2018, 1, 1), _inputs(9.0))]
    valued = attach_valuation(feat, funds)
    assert "DELISTED" not in set(valued.index.get_level_values("symbol"))
    assert len(valued) == len(feat)


def test_symbols_without_fundamentals_are_not_silently_valued():
    feat, funds = world(days=200, n_symbols=6)
    dropped = sorted(funds)[0]
    partial = {k: v for k, v in funds.items() if k != dropped}
    valued = attach_valuation(feat, partial)
    assert (valued.xs(dropped, level="symbol")["iv8"] == 0.0).all()
    assert (valued.xs(sorted(partial)[0], level="symbol")["iv8"] > 0).all()
