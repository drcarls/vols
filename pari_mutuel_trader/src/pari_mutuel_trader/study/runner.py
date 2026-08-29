from __future__ import annotations

import copy

import numpy as np
import pandas as pd

from pari_mutuel_trader.backtest.engine import run_backtest
from pari_mutuel_trader.study.conditional import conditional_study, momentum_iv_grid

REPORT_METRICS = ("CAGR", "Volatility", "Sharpe", "Sortino", "MaxDrawdown", "Calmar",
                  "turnover", "HitRate", "average_holdings")

IV_SIGNALS = ("discount_to_iv6", "discount_to_iv8", "iv_consensus")


def build_variants(baseline: dict) -> dict[str, dict]:
    """The variants sections 3-5 ask for, layered on one untouched baseline."""

    def with_overlay(**overlay):
        config = copy.deepcopy(baseline)
        config["iv_overlay"] = {"enabled": True, **overlay}
        return config

    variants = {"baseline": copy.deepcopy(baseline)}

    for label, signal in (("IV6", "discount_to_iv6"), ("IV8", "discount_to_iv8"),
                          ("IV6/8", "combined")):
        for weight in (0.10, 0.25, 0.50):
            variants[f"+ {label} rank {int(weight * 100)}%"] = with_overlay(
                mode="rank", signal=signal, iv_weight=weight)

    for label, signal in (("IV6", "discount_to_iv6"), ("IV8", "discount_to_iv8")):
        for pct in (0.10, 0.20):
            variants[f"veto richest {int(pct * 100)}% {label}"] = with_overlay(
                mode="veto", signal=signal, exclude_pct=pct)
    variants["veto richest 10% both"] = with_overlay(
        mode="veto", signal="discount_to_iv8", exclude_pct=0.10, require_both=True)

    for label, signal in (("IV6", "discount_to_iv6"), ("IV8", "discount_to_iv8"),
                          ("IV6/8", "combined")):
        variants[f"size by {label}"] = with_overlay(mode="size", signal=signal)

    return variants


def compare_to_baseline(results: dict[str, dict], baseline: str = "baseline") -> pd.DataFrame:
    """Section 8's table: levels plus the delta against the paired baseline."""
    frame = pd.DataFrame({name: {m: metrics.get(m) for m in REPORT_METRICS}
                          for name, metrics in results.items()}).T
    for column in ("CAGR", "Sharpe", "MaxDrawdown"):
        frame[f"d_{column}"] = frame[column] - frame.loc[baseline, column]
    return frame


def rolling_comparison(curves: dict[str, pd.Series], baseline: str, freq: str = "YE") -> pd.DataFrame:
    """Year-by-year excess return, to see whether an edge is persistent or one regime."""
    periods = {name: curve.resample(freq).last().pct_change().dropna()
               for name, curve in curves.items()}
    base = periods[baseline]
    return pd.DataFrame({name: series - base for name, series in periods.items()
                         if name != baseline}).dropna(how="all")


def bootstrap_delta(a: pd.Series, b: pd.Series, draws: int = 2000, seed: int = 0) -> dict:
    """Confidence interval on the difference in mean period return, by resampling periods.

    This resamples realized periods; it does not invent price paths. With a single
    historical run the interval reflects sampling within that one history and should
    not be read as a probability the edge is real out of sample.
    """
    paired = pd.concat([a, b], axis=1).dropna()
    if len(paired) < 3:
        return {"mean": float("nan"), "lo": float("nan"), "hi": float("nan"), "periods": len(paired)}
    delta = (paired.iloc[:, 0] - paired.iloc[:, 1]).to_numpy()
    rng = np.random.default_rng(seed)
    means = rng.choice(delta, size=(draws, len(delta)), replace=True).mean(axis=1)
    return {
        "mean": float(delta.mean()),
        "lo": float(np.percentile(means, 2.5)),
        "hi": float(np.percentile(means, 97.5)),
        "periods": int(len(delta)),
    }


def run_sleeve_study(features: pd.DataFrame, baseline_config: dict, buckets: int = 5) -> dict:
    """Sections 1-8 for one sleeve, against its own untouched baseline."""
    base_result = run_backtest(features, copy.deepcopy(baseline_config))

    conditional = conditional_study(features, base_result.holdings_history, list(IV_SIGNALS), buckets)
    grid = momentum_iv_grid(features, base_result.holdings_history)

    variants = build_variants(baseline_config)
    results, curves = {}, {}
    for name, config in variants.items():
        result = base_result if name == "baseline" else run_backtest(features, config)
        results[name] = result.metrics
        curves[name] = result.equity_curve

    table = compare_to_baseline(results)
    yearly = rolling_comparison(curves, "baseline")
    periods = {name: curve.resample("YE").last().pct_change().dropna() for name, curve in curves.items()}
    bootstrap = {name: bootstrap_delta(series, periods["baseline"])
                 for name, series in periods.items() if name != "baseline"}

    return {
        "baseline_metrics": base_result.metrics,
        "conditional": conditional,
        "momentum_iv_grid": grid,
        "table": table,
        "yearly_excess": yearly,
        "bootstrap": bootstrap,
        "rebalances": len(base_result.holdings_history),
    }
