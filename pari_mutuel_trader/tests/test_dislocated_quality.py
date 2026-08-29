"""The dislocated quality sleeve: durable businesses whose price fell past their value."""

from datetime import timedelta

import pandas as pd
import pytest
import yaml

from pari_mutuel_trader.agents import AGENTS, DislocatedQualityAgent, build_agents
from pari_mutuel_trader.backtest.engine import run_backtest
from pari_mutuel_trader.data.features import build_features
from pari_mutuel_trader.data.loaders import generate_sample_features, generate_sample_fundamentals
from pari_mutuel_trader.portfolio.constraints import apply_quality_filter
from pari_mutuel_trader.valuation.features import Revision, attach_valuation, load_fundamentals
from pari_mutuel_trader.valuation.intrinsic import ValuationInputs
from pari_mutuel_trader.valuation.quality import QualityProfile

CONFIG = "configs/dislocated_quality.yaml"
FUNDAMENTALS = "configs/fundamentals.example.yaml"


def sample(days=400, n_symbols=30):
    feat = build_features(generate_sample_features(days=days, n_symbols=n_symbols))
    return attach_valuation(feat, generate_sample_fundamentals(feat))


# --- the fundamentals bridge ------------------------------------------------

def test_fundamentals_load_as_single_sets_or_dated_revisions():
    funds = load_fundamentals(FUNDAMENTALS)
    assert len(funds["PYPL"]) == 2 and len(funds["CDNS"]) == 1
    assert [r.as_of for r in funds["PYPL"]] == sorted(r.as_of for r in funds["PYPL"])
    assert funds["PYPL"][-1].inputs.owner_earnings_ps == 7.40


def test_attaching_valuation_fills_the_columns_the_agents_need():
    feat = sample()
    for column in ("iv15", "iv8", "discount_to_iv15", "premium_to_iv8", "durability", "dislocation"):
        assert column in feat.columns
        assert feat[column].notna().all()
    assert feat["iv15"].gt(0).all()
    assert (feat["iv15"] < feat["iv8"]).all()


def test_the_discount_is_measured_against_the_price():
    feat = sample()
    row = feat.iloc[0]
    assert row["discount_to_iv15"] == pytest.approx(row["iv15"] / row["close"] - 1.0)
    assert row["premium_to_iv8"] == pytest.approx(row["close"] / row["iv8"] - 1.0)


def test_a_revision_moves_value_without_the_price_moving():
    """Value and price are separate series - which is what makes dislocation real."""
    feat = build_features(generate_sample_features(days=300, n_symbols=2))
    symbols = sorted(set(feat.index.get_level_values("symbol")))
    dates = feat.index.get_level_values("date").unique().sort_values()
    cut = dates[len(dates) // 2].date()

    def revision(on, earnings):
        return Revision(on, ValuationInputs(earnings, 0.10, QualityProfile(0.8, 0.25, 0.8)))

    funds = {s: [revision(dates[0].date() - timedelta(days=1), 5.0), revision(cut, 2.5)] for s in symbols}
    valued = attach_valuation(feat, funds)
    iv = valued.xs(symbols[0], level="symbol")["iv15"]
    before = iv.loc[: pd.Timestamp(cut) - pd.Timedelta(days=1)]
    after = iv.loc[pd.Timestamp(cut):]
    assert before.nunique() == 1 and after.nunique() == 1
    assert before.iloc[-1] == pytest.approx(2 * after.iloc[-1])


def test_a_price_that_fell_with_its_value_is_not_dislocated():
    """A deterioration must score zero; only an excess price fall counts."""
    feat = build_features(generate_sample_features(days=300, n_symbols=2))
    symbols = sorted(set(feat.index.get_level_values("symbol")))
    dates = feat.index.get_level_values("date").unique().sort_values()

    def revision(on, earnings):
        return Revision(on, ValuationInputs(earnings, 0.10, QualityProfile(0.8, 0.25, 0.8)))

    cut_index = len(dates) // 2
    # Value cut by 90% at the midpoint; over the 60 sessions that span the cut, no
    # plausible price fall keeps up with it.
    slashed = {s: [revision(dates[0].date() - timedelta(days=1), 5.0),
                   revision(dates[cut_index].date(), 0.5)] for s in symbols}
    spanning = dates[cut_index + 60]
    assert attach_valuation(feat, slashed).xs(spanning, level="date")["dislocation"].max() == 0.0

    # Value held flat instead: the same price falls now show through as dislocation.
    flat = {s: [revision(dates[0].date() - timedelta(days=1), 5.0)] for s in symbols}
    assert attach_valuation(feat, flat)["dislocation"].max() > 0.0


def test_dislocation_is_never_negative():
    assert sample()["dislocation"].ge(0).all()


def test_symbols_without_fundamentals_are_left_at_zero():
    feat = build_features(generate_sample_features(days=200, n_symbols=4))
    funds = generate_sample_fundamentals(feat)
    partial = {k: v for k, v in list(funds.items())[:2]}
    valued = attach_valuation(feat, partial)
    covered = valued[valued["iv15"] > 0].index.get_level_values("symbol").unique()
    assert set(covered) == set(partial)


# --- the agent --------------------------------------------------------------

def test_the_agent_abstains_without_valuation_data():
    agent = DislocatedQualityAgent()
    assert agent.abstains(pd.DataFrame({"close": [1.0]}))
    assert agent.abstains(pd.DataFrame({"durability": [0.8], "discount_to_iv15": [0.0], "dislocation": [0.0]}))
    assert not agent.abstains(pd.DataFrame({"durability": [0.8], "discount_to_iv15": [0.2], "dislocation": [0.1]}))


def test_the_agent_prefers_the_cheap_dislocated_franchise():
    frame = pd.DataFrame(
        {
            "durability": [0.9, 0.9, 0.2, 0.9],
            "discount_to_iv15": [0.30, -0.30, 0.30, 0.30],
            "dislocation": [0.20, 0.20, 0.20, 0.00],
        },
        index=["cheap_dislocated", "dear", "junk", "cheap_quiet"],
    )
    signal = DislocatedQualityAgent().compute_signal(frame)
    assert signal.idxmax() == "cheap_dislocated"
    assert signal["cheap_dislocated"] > signal["cheap_quiet"] > signal["junk"]
    assert signal["dear"] < signal["cheap_dislocated"]


def test_it_votes_against_momentum_by_construction():
    """Buying weakness is the point; the pool needs a vote that is not price trend."""
    feat = sample()
    frame = feat.xs(feat.index.get_level_values("date")[-1], level="date")
    dq = DislocatedQualityAgent().compute_signal(frame)
    momentum = AGENTS["momentum"]().compute_signal(frame)
    assert dq.corr(momentum) < 0.2


# --- the quality gate -------------------------------------------------------

def test_the_gate_removes_names_below_the_durability_threshold():
    frame = pd.DataFrame({"durability": [0.9, 0.5, 0.61], "close": [1.0, 2.0, 3.0]},
                         index=["a", "b", "c"])
    assert list(apply_quality_filter(frame, 0.60).index) == ["a", "c"]
    assert list(apply_quality_filter(frame, 0.0).index) == ["a", "b", "c"]
    assert list(apply_quality_filter(pd.DataFrame({"close": [1.0]}, index=["a"]), 0.6).index) == ["a"]


def test_the_gate_binds_in_the_sleeve():
    cfg = yaml.safe_load(open(CONFIG))
    feat = sample()
    gated = run_backtest(feat, cfg)
    holdings = set(gated.metrics["current_holdings"])
    latest = feat.xs(feat.index.get_level_values("date")[-1], level="date")
    assert holdings
    assert all(latest.loc[s, "durability"] >= cfg["portfolio"]["min_durability"] for s in holdings)


# --- the sleeve -------------------------------------------------------------

def test_the_roster_is_config_driven():
    names = [a.name for a in build_agents(["dislocated_quality", "house"])]
    assert names == ["dislocated_quality", "house"]
    with pytest.raises(ValueError, match="Unknown agents"):
        build_agents(["not_an_agent"])


def test_the_sleeve_runs_on_its_own_config():
    cfg = yaml.safe_load(open(CONFIG))
    result = run_backtest(sample(), cfg)
    m = result.metrics
    assert m["average_holdings"] >= cfg["portfolio"]["min_holdings"]
    assert m["rebalance_count"] >= cfg["backtest"]["min_rebalances"]
    assert m["CAGR_after_tax"] < m["CAGR"]  # it pays tax, and says so


def test_a_slower_clock_converts_short_term_gains_into_long_term():
    """The structural argument for the quarterly cadence, independent of returns."""
    cfg = yaml.safe_load(open(CONFIG))
    feat = sample(days=800, n_symbols=40)

    weekly = dict(cfg, backtest={**cfg["backtest"], "rebalance_days": 5})
    annual = dict(cfg, backtest={**cfg["backtest"], "rebalance_days": 252})
    fast, slow = run_backtest(feat, weekly).metrics, run_backtest(feat, annual).metrics

    assert fast["short_term_share_of_tax"] > slow["short_term_share_of_tax"]
    assert abs(fast["tax_drag_annual"]) > abs(slow["tax_drag_annual"])


def test_the_cadence_defaults_to_weekly():
    feat = sample(days=200, n_symbols=20)
    cfg = yaml.safe_load(open(CONFIG))
    cfg["backtest"].pop("rebalance_days")
    cfg["portfolio"]["min_holdings"] = 5
    cfg["portfolio"]["top_k"] = 8
    assert run_backtest(feat, cfg).metrics["rebalance_count"] > 10
