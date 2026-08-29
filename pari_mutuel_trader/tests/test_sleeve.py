"""The valuation and tax discipline as it applies to a diversified strategy sleeve."""

from datetime import date, timedelta

import pandas as pd
import pytest

from pari_mutuel_trader.agents import ValuationAgent
from pari_mutuel_trader.agents.momentum import MomentumAgent
from pari_mutuel_trader.backtest.engine import run_backtest
from pari_mutuel_trader.data.features import build_features
from pari_mutuel_trader.data.loaders import generate_sample_features
from pari_mutuel_trader.portfolio.lots import LotLedger
from pari_mutuel_trader.portfolio.tax_aware import SeasoningPolicy, apply_holds, seasoning_holds
from pari_mutuel_trader.valuation.overlay import zone_ceilings
from pari_mutuel_trader.valuation.sell_rules import SellPolicy
from pari_mutuel_trader.valuation.tax import TaxProfile

TAX = TaxProfile()
DAY = date(2026, 6, 1)


def sleeve_config(**overrides) -> dict:
    cfg = {
        "portfolio": {"top_k": 25, "min_holdings": 20, "max_stock_weight": 0.05,
                      "turnover_cap": 1.0, "rebalance_threshold": 0.01,
                      "weighting": "equal_weight", "min_adv": 0},
        "learning": {"temperature": 1.0, "hedge_eta": 0.03, "min_agent_weight": 0.05,
                     "max_agent_weight": 0.5},
        "backtest": {"frequency": "weekly", "min_rebalances": 3},
        "risk": {"max_drawdown_limit": -0.25},
        "valuation": {"enabled": True, "sizing": "relative"},
        "tax_aware": {"enabled": True},
        "tax": {"federal_short_term": 0.37, "federal_long_term": 0.20, "state": 0.0, "niit": 0.038},
    }
    for key, value in overrides.items():
        cfg[key] = {**cfg.get(key, {}), **value}
    return cfg


# --- breadth-aware ceilings -------------------------------------------------

def test_absolute_ceilings_are_inert_at_sleeve_breadth():
    """At 25 equal-weighted names only the expensive ceiling sits below 4%."""
    ceilings = zone_ceilings(SellPolicy(sizing="absolute"))
    natural = 1 / 25
    binding = {z: c for z, c in ceilings.items() if c < natural}
    assert set(binding) == {"expensive"}


def test_relative_ceilings_bind_at_any_breadth():
    for holdings in (10, 25, 50):
        natural = 1 / holdings
        ceilings = zone_ceilings(SellPolicy(sizing="relative"), natural_weight=natural)
        assert ceilings["spring_loaded"] > natural > ceilings["rich"] > ceilings["expensive"]
        assert ceilings["expensive"] == pytest.approx(natural * 0.5)


def test_relative_sizing_requires_a_natural_weight():
    with pytest.raises(ValueError):
        zone_ceilings(SellPolicy(sizing="relative"))


# --- agent abstention -------------------------------------------------------

def test_the_valuation_agent_abstains_without_intrinsic_value_data():
    agent = ValuationAgent()
    assert agent.abstains(pd.DataFrame({"close": [1.0, 2.0]}))
    assert agent.abstains(pd.DataFrame({"discount_to_iv15": [0.0, 0.0], "premium_to_iv8": [0.0, 0.0]}))
    assert not agent.abstains(pd.DataFrame({"discount_to_iv15": [0.1, -0.2], "premium_to_iv8": [0.0, 0.1]}))
    assert not MomentumAgent().abstains(pd.DataFrame({"ret_20d": [0.1]}))


def test_an_abstaining_agent_leaves_the_sleeve_exactly_as_it_was():
    """Sample data carries no IV, so the picker must score identically to before."""
    from pari_mutuel_trader.agents import V1_AGENTS

    feat = build_features(generate_sample_features(days=300, n_symbols=40))
    with_agent = run_backtest(feat, sleeve_config(learning={"agents": V1_AGENTS})).metrics
    without_agent = run_backtest(
        feat, sleeve_config(learning={"agents": [a for a in V1_AGENTS if a != "valuation"]})
    ).metrics

    assert with_agent["CAGR"] == pytest.approx(without_agent["CAGR"])
    assert with_agent["current_holdings"] == without_agent["current_holdings"]


# --- seasoning --------------------------------------------------------------

def _ledger_holding(symbol, acquired, price=100.0, weight=0.04):
    led = LotLedger()
    led.buy(symbol, weight, price, acquired)
    return led


def _pooled(names, top="A"):
    scores = {n: 0.9 if n == top else 0.5 for n in names}
    return pd.Series(scores)


def test_a_near_seasoned_winner_is_held_over():
    as_of = DAY
    led = _ledger_holding("A", as_of - timedelta(days=340))
    current = pd.Series({"A": 0.04, "B": 0.04})
    target = pd.Series({"B": 0.04, "C": 0.04})
    holds = seasoning_holds(target, current, led, pd.Series({"A": 200.0}),
                            _pooled(["A", "B", "C"]), SeasoningPolicy(), as_of, keep_rank=3)
    assert holds == {"A"}


def test_a_loss_is_realized_rather_than_deferred():
    as_of = DAY
    led = _ledger_holding("A", as_of - timedelta(days=340), price=300.0)
    current = pd.Series({"A": 0.04})
    target = pd.Series({"B": 0.04})
    holds = seasoning_holds(target, current, led, pd.Series({"A": 100.0}),
                            _pooled(["A", "B"]), SeasoningPolicy(), as_of, keep_rank=3)
    assert holds == set()


def test_the_clock_stops_being_a_reason_once_conviction_goes():
    as_of = DAY
    led = _ledger_holding("A", as_of - timedelta(days=340))
    current = pd.Series({"A": 0.04})
    target = pd.Series({"B": 0.04})
    pooled = pd.Series({"A": 0.01, "B": 0.9, "C": 0.8})
    holds = seasoning_holds(target, current, led, pd.Series({"A": 200.0}),
                            pooled, SeasoningPolicy(), as_of, keep_rank=2)
    assert holds == set()


def test_a_freshly_bought_name_is_not_deferred():
    as_of = DAY
    led = _ledger_holding("A", as_of - timedelta(days=20))
    holds = seasoning_holds(pd.Series({"B": 0.04}), pd.Series({"A": 0.04}), led,
                            pd.Series({"A": 200.0}), _pooled(["A", "B"]),
                            SeasoningPolicy(), as_of, keep_rank=3)
    assert holds == set()


def test_seasoning_can_be_switched_off():
    as_of = DAY
    led = _ledger_holding("A", as_of - timedelta(days=340))
    holds = seasoning_holds(pd.Series({"B": 0.04}), pd.Series({"A": 0.04}), led,
                            pd.Series({"A": 200.0}), _pooled(["A", "B"]),
                            SeasoningPolicy(enabled=False), as_of, keep_rank=3)
    assert holds == set()


def test_apply_holds_readmits_and_renormalizes():
    target = pd.Series({"B": 0.5, "C": 0.5})
    current = pd.Series({"A": 0.04, "B": 0.04})
    out = apply_holds(target, current, {"A"})
    assert "A" in out.index
    assert float(out.sum()) == pytest.approx(1.0)
    assert apply_holds(target, current, set()).equals(target)


# --- after-tax accounting in the sleeve -------------------------------------

def test_the_sleeve_reports_an_after_tax_curve_and_its_drag():
    feat = build_features(generate_sample_features(days=400, n_symbols=40))
    result = run_backtest(feat, sleeve_config())
    m = result.metrics
    assert len(result.after_tax_curve) == len(result.equity_curve)
    assert m["tax_drag_annual"] == pytest.approx(m["CAGR"] - m["CAGR_after_tax"])
    assert result.realized_sales
    assert 0.0 <= m["short_term_share_of_tax"] <= 1.0


def test_a_weekly_sleeve_realizes_short_term_gains():
    feat = build_features(generate_sample_features(days=400, n_symbols=40))
    result = run_backtest(feat, sleeve_config())
    assert not any(s.long_term for s in result.realized_sales)


def test_the_wash_sale_rule_only_ever_costs():
    feat = build_features(generate_sample_features(days=400, n_symbols=40))
    strict = run_backtest(feat, sleeve_config()).metrics
    naive = run_backtest(feat, sleeve_config(tax_aware={"wash_sales": False})).metrics
    assert strict["CAGR_after_tax"] <= naive["CAGR_after_tax"]
    assert strict["wash_sale_disallowed"] > 0
    assert naive["wash_sale_disallowed"] == 0.0


def test_building_the_book_from_cash_is_not_blocked_by_the_turnover_cap():
    feat = build_features(generate_sample_features(days=300, n_symbols=40))
    result = run_backtest(feat, sleeve_config(portfolio={"turnover_cap": 0.05}))
    assert result.metrics["rebalance_count"] >= 1
    assert result.metrics["average_holdings"] >= 20
    # The build is exempt from the cap, so it must not be averaged into turnover.
    assert result.metrics["turnover"] <= 0.05
    assert result.metrics["blocked_by_turnover_cap"] > 0
