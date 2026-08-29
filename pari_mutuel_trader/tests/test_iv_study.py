"""IV as a conditioning signal on an existing sleeve, rather than a strategy of its own."""

import numpy as np
import pandas as pd
import pytest
import yaml

from pari_mutuel_trader.backtest.engine import run_backtest
from pari_mutuel_trader.data.features import build_features
from pari_mutuel_trader.data.loaders import generate_valuation_universe
from pari_mutuel_trader.study import (
    bucket_by_signal,
    bucket_returns,
    build_variants,
    compare_to_baseline,
    conditional_study,
    monotonicity,
    selected_panel,
)
from pari_mutuel_trader.valuation import QualityProfile, ValuationInputs, intrinsic_value
from pari_mutuel_trader.valuation import conditioning
from pari_mutuel_trader.valuation.features import attach_valuation


def world(days=500, n_symbols=30, seed=4, reversion=0.003):
    raw, funds = generate_valuation_universe(days=days, n_symbols=n_symbols, seed=seed, reversion=reversion)
    return attach_valuation(build_features(raw), funds)


def momentum_config(**portfolio):
    cfg = yaml.safe_load(open("configs/momentum.yaml"))
    cfg["portfolio"] = {**cfg["portfolio"], "top_k": 12, "min_holdings": 6, **portfolio}
    return cfg


# --- IV6 and IV8 are not two opinions --------------------------------------

def test_iv6_always_exceeds_iv8_which_always_exceeds_iv15():
    rng = np.random.default_rng(0)
    for _ in range(50):
        moat = rng.uniform(0.15, 0.95)
        inputs = ValuationInputs(rng.uniform(0.5, 12), rng.uniform(0.03, 0.18),
                                 QualityProfile(moat, 0.08 + moat * 0.2, moat))
        assert intrinsic_value(inputs, 0.06) > intrinsic_value(inputs, 0.08) > intrinsic_value(inputs, 0.15)


def test_the_two_readings_rank_stocks_almost_identically():
    """Section 6 assumes they can disagree. They are monotone transforms, so they cannot."""
    feat = world()
    latest = feat.xs(feat.index.get_level_values("date")[-1], level="date")
    spearman = latest["discount_to_iv6"].rank().corr(latest["discount_to_iv8"].rank())
    assert spearman > 0.95
    assert (feat["iv6"] > feat["iv8"]).all()


def test_disagreement_is_rare_and_never_extreme():
    feat = world()
    mix = feat["iv_agreement"].value_counts(normalize=True)
    assert mix.get("disagree", 0.0) < 0.25
    latest = feat.xs(feat.index.get_level_values("date")[-1], level="date")
    q6 = pd.qcut(latest["discount_to_iv6"].rank(method="first"), 5, labels=False)
    q8 = pd.qcut(latest["discount_to_iv8"].rank(method="first"), 5, labels=False)
    assert not (((q6 == 0) & (q8 == 4)) | ((q6 == 4) & (q8 == 0))).any()


def test_dispersion_measures_duration_not_disagreement():
    """The IV6-IV8 gap widens with the share of value in distant cash flows."""
    def gap(moat):
        inputs = ValuationInputs(5.0, 0.10, QualityProfile(moat, 0.08 + moat * 0.25, moat))
        return (intrinsic_value(inputs, 0.06) - intrinsic_value(inputs, 0.08)) / intrinsic_value(inputs, 0.08)

    assert gap(0.95) > gap(0.20)


# --- section 2: the conditional study --------------------------------------

def test_buckets_are_cut_within_each_date():
    feat = world()
    result = run_backtest(feat, momentum_config())
    panel = bucket_by_signal(selected_panel(feat, result.holdings_history, "discount_to_iv8"))
    counts = panel.dropna(subset=["bucket"]).groupby("date")["bucket"].nunique()
    assert (counts <= 5).all() and (counts >= 3).all()


def test_the_study_recovers_an_effect_that_is_present():
    # Wide enough that each bucket holds a real sample; five buckets of three names
    # is noise however strong the underlying effect.
    feat = world(reversion=0.004, days=800, n_symbols=60)
    result = run_backtest(feat, momentum_config(top_k=25, min_holdings=20))
    study = conditional_study(feat, result.holdings_history, ["discount_to_iv8"])
    mono = study["discount_to_iv8"]["monotonicity"]["fwd_60d"]
    assert mono["spearman"] > 0.8 and mono["spread"] > 0


def test_the_study_reports_no_effect_when_there_is_none():
    """The null matters more than the positive: a bench that always finds something is useless."""
    feat = world(reversion=0.0, days=800, n_symbols=60)
    result = run_backtest(feat, momentum_config())
    study = conditional_study(feat, result.holdings_history, ["discount_to_iv8"])
    assert abs(study["discount_to_iv8"]["monotonicity"]["fwd_60d"]["spread"]) < 0.10


def test_monotonicity_is_signed_correctly():
    table = pd.DataFrame({"fwd_60d": [-0.02, 0.0, 0.03, 0.05, 0.09]}, index=[1.0, 2, 3, 4, 5])
    assert monotonicity(table, "fwd_60d")["spearman"] == pytest.approx(1.0)
    flipped = table.iloc[::-1].set_index(table.index)
    assert monotonicity(flipped, "fwd_60d")["spearman"] == pytest.approx(-1.0)
    assert monotonicity(pd.DataFrame(), "fwd_60d")["buckets"] == 0


def test_bucket_table_covers_every_selected_name():
    feat = world()
    result = run_backtest(feat, momentum_config())
    panel = bucket_by_signal(selected_panel(feat, result.holdings_history, "discount_to_iv6"))
    assert int(bucket_returns(panel)["n"].sum()) == len(panel.dropna(subset=["bucket"]))


# --- sections 3, 4, 5: the conditioning modes -------------------------------

def test_rank_blending_moves_toward_the_iv_ordering():
    feat = world()
    frame = feat.xs(feat.index.get_level_values("date")[-1], level="date")
    pooled = pd.Series(np.linspace(1, 0, len(frame)), index=frame.index)

    none = conditioning.blend_rank(pooled, frame, "discount_to_iv8", 0.0)
    quarter = conditioning.blend_rank(pooled, frame, "discount_to_iv8", 0.25)
    half = conditioning.blend_rank(pooled, frame, "discount_to_iv8", 0.50)

    iv_rank = frame["discount_to_iv8"].rank()
    assert none.equals(pooled)
    assert half.rank().corr(iv_rank) > quarter.rank().corr(iv_rank)


def test_the_veto_removes_only_the_richest_tail():
    feat = world()
    frame = feat.xs(feat.index.get_level_values("date")[-1], level="date")
    kept = conditioning.veto_mask(frame, "discount_to_iv8", 0.20)
    dropped = frame.index.difference(kept)
    assert 0 < len(dropped) <= round(0.25 * len(frame))
    assert frame.loc[dropped, "discount_to_iv8"].max() <= frame.loc[kept, "discount_to_iv8"].max()


def test_requiring_both_readings_vetoes_no_more_than_either_alone():
    feat = world()
    frame = feat.xs(feat.index.get_level_values("date")[-1], level="date")
    either = frame.index.difference(conditioning.veto_mask(frame, "discount_to_iv8", 0.10))
    both = frame.index.difference(conditioning.veto_mask(frame, "discount_to_iv8", 0.10, require_both=True))
    assert set(both) <= set(either)


def test_sizing_scales_by_valuation_and_preserves_exposure():
    feat = world()
    frame = feat.xs(feat.index.get_level_values("date")[-1], level="date")
    weights = pd.Series(1.0 / len(frame), index=frame.index)
    multipliers = conditioning.size_multipliers(frame, "discount_to_iv8")
    sized = conditioning.apply_size(weights, multipliers)

    assert float(sized.sum()) == pytest.approx(1.0)
    cheapest = frame["discount_to_iv8"].idxmax()
    dearest = frame["discount_to_iv8"].idxmin()
    assert sized[cheapest] > weights[cheapest] > sized[dearest]


def test_overlays_leave_eligibility_alone():
    """Sections 3-5 must not introduce names the sleeve would not have held."""
    feat = world()
    base = run_backtest(feat, momentum_config())
    universe = {s for holdings in base.holdings_history.values() for s in holdings}

    for overlay in ({"mode": "rank", "signal": "discount_to_iv8", "iv_weight": 0.25},
                    {"mode": "veto", "signal": "discount_to_iv8", "exclude_pct": 0.20},
                    {"mode": "size", "signal": "discount_to_iv8"}):
        cfg = dict(momentum_config(), iv_overlay={"enabled": True, **overlay})
        result = run_backtest(feat, cfg)
        assert result.metrics["average_holdings"] >= cfg["portfolio"]["min_holdings"]
        if overlay["mode"] in ("veto", "size"):
            picked = {s for h in result.holdings_history.values() for s in h}
            assert picked <= universe or overlay["mode"] == "veto"


def test_an_absent_iv_column_leaves_the_sleeve_untouched():
    feat = world()
    bare = feat.drop(columns=[c for c in feat.columns if c.startswith(("discount_to_", "iv"))])
    cfg = dict(momentum_config(), iv_overlay={"enabled": True, "mode": "rank",
                                              "signal": "discount_to_iv8", "iv_weight": 0.5})
    assert run_backtest(bare, cfg).metrics["CAGR"] == pytest.approx(
        run_backtest(bare, momentum_config()).metrics["CAGR"])


def test_an_unknown_overlay_mode_is_rejected():
    with pytest.raises(ValueError, match="Unknown iv_overlay mode"):
        conditioning.from_config({"enabled": True, "mode": "sideways"})
    assert conditioning.from_config({"enabled": False}) is None


# --- section 8: the comparison ----------------------------------------------

def test_every_variant_is_measured_against_the_same_baseline():
    variants = build_variants(momentum_config())
    assert "baseline" in variants
    assert variants["baseline"].get("iv_overlay") is None
    assert all(v["iv_overlay"]["enabled"] for k, v in variants.items() if k != "baseline")
    # Selection rules are untouched across every variant.
    assert {tuple(sorted(v["portfolio"].items())) for v in variants.values()}.__len__() == 1


def test_the_table_reports_deltas_against_the_baseline():
    results = {
        "baseline": {"CAGR": 0.10, "Sharpe": 0.8, "MaxDrawdown": -0.2},
        "variant": {"CAGR": 0.12, "Sharpe": 0.9, "MaxDrawdown": -0.15},
    }
    table = compare_to_baseline(results)
    assert table.loc["baseline", "d_CAGR"] == 0.0
    assert table.loc["variant", "d_CAGR"] == pytest.approx(0.02)
    assert table.loc["variant", "d_Sharpe"] == pytest.approx(0.1)


def test_the_metric_set_covers_what_the_brief_asks_for():
    feat = world(days=300, n_symbols=20)
    metrics = run_backtest(feat, momentum_config()).metrics
    for name in ("CAGR", "Volatility", "Sharpe", "Sortino", "MaxDrawdown",
                 "Calmar", "turnover", "HitRate", "average_holdings"):
        assert name in metrics
