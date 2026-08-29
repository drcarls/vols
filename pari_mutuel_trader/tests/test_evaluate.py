"""The test bench itself: it has to be able to find nothing before it can find something."""

import pandas as pd
import pytest

from pari_mutuel_trader.backtest.evaluate import build_world, compare, evaluate_variants
from pari_mutuel_trader.data.features import build_features
from pari_mutuel_trader.data.loaders import generate_valuation_universe
from pari_mutuel_trader.valuation.features import attach_valuation
from pari_mutuel_trader.valuation.sell_rules import SellPolicy


def _forward_return(feat, horizon=60):
    return feat.groupby(level="symbol")["close"].shift(-horizon) / feat["close"] - 1


def test_fundamentals_are_drawn_independently_of_the_price_path():
    """The whole point: if owner earnings come from price history, cheap means fallen."""
    raw_a, funds_a = generate_valuation_universe(days=300, n_symbols=10, seed=1, reversion=0.0)
    raw_b, funds_b = generate_valuation_universe(days=300, n_symbols=10, seed=1, reversion=0.006)
    # Same seed, same businesses - only the price process differs.
    assert list(funds_a) == list(funds_b)
    for symbol in funds_a:
        assert funds_a[symbol][0].inputs.owner_earnings_ps == funds_b[symbol][0].inputs.owner_earnings_ps
    assert not raw_a["close"].equals(raw_b["close"])


def test_the_null_world_hides_no_value_signal():
    raw, funds = generate_valuation_universe(days=600, n_symbols=40, seed=3, reversion=0.0)
    feat = attach_valuation(build_features(raw), funds)
    assert abs(feat["discount_to_iv15"].corr(_forward_return(feat))) < 0.15


def test_the_reverting_world_contains_one():
    raw, funds = generate_valuation_universe(days=600, n_symbols=40, seed=3, reversion=0.004)
    feat = attach_valuation(build_features(raw), funds)
    assert feat["discount_to_iv15"].corr(_forward_return(feat)) > 0.2


def test_prices_start_scattered_around_value():
    raw, funds = generate_valuation_universe(days=200, n_symbols=60, seed=5)
    feat = attach_valuation(build_features(raw), funds)
    first = feat.xs(feat.index.get_level_values("date")[0], level="date")
    assert (first["discount_to_iv15"] > 0).any() and (first["discount_to_iv15"] < 0).any()


def test_variants_are_scored_on_the_same_worlds():
    """Pairing is what makes a 12-seed comparison mean anything."""
    policy = SellPolicy()
    a = build_world(7, 0.0, 200, 20, policy)
    b = build_world(7, 0.0, 200, 20, policy)
    pd.testing.assert_frame_equal(a, b)


def _tiny_variants():
    common = {
        "portfolio": {"top_k": 8, "min_holdings": 5, "max_stock_weight": 0.3, "turnover_cap": 1.0,
                      "rebalance_threshold": 0.01, "weighting": "equal_weight", "min_adv": 0,
                      "min_durability": 0.0, "cost_bps": 10.0},
        "learning": {"temperature": 1.0, "hedge_eta": 0.03, "min_agent_weight": 0.05,
                     "max_agent_weight": 0.5, "agents": ["momentum", "house"]},
        "backtest": {"rebalance_days": 21, "min_rebalances": 1},
        "risk": {"max_drawdown_limit": -0.5},
        "valuation": {"enabled": False},
        "tax": {"status": "tax_deferred"},
    }
    other = {**common, "learning": {**common["learning"], "agents": ["dislocated_quality", "house"]}}
    return {"baseline": common, "dislocation": other}


def test_evaluate_returns_one_row_per_seed_and_variant():
    frame = evaluate_variants(_tiny_variants(), [0, 1], reversion=0.0, days=200, n_symbols=20)
    assert len(frame) == 4
    assert set(frame["variant"]) == {"baseline", "dislocation"}
    assert frame["CAGR"].notna().all()


def test_compare_reports_a_paired_difference():
    frame = evaluate_variants(_tiny_variants(), [0, 1, 2], reversion=0.0, days=200, n_symbols=20)
    result = compare(frame, "baseline", "CAGR")
    assert result.loc["baseline", "delta"] == pytest.approx(0.0)
    assert result.loc["baseline", "win_rate"] == 0.0
    assert 0.0 <= result.loc["dislocation", "win_rate"] <= 1.0
    assert result.loc["dislocation", "seeds"] == 3
