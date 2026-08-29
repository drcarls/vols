from __future__ import annotations

import copy

import numpy as np
import pandas as pd

from pari_mutuel_trader.backtest.engine import run_backtest
from pari_mutuel_trader.data.features import build_features
from pari_mutuel_trader.data.loaders import generate_valuation_universe
from pari_mutuel_trader.valuation.features import attach_valuation
from pari_mutuel_trader.valuation.sell_rules import SellPolicy

METRICS = ("CAGR", "CAGR_gross", "Sharpe", "MaxDrawdown", "turnover", "average_holdings")


def build_world(seed: int, reversion: float, days: int, n_symbols: int, policy: SellPolicy) -> pd.DataFrame:
    raw, fundamentals = generate_valuation_universe(
        days=days, n_symbols=n_symbols, seed=seed, reversion=reversion
    )
    return attach_valuation(build_features(raw), fundamentals, policy)


def evaluate_variants(
    variants: dict[str, dict],
    seeds: list[int],
    reversion: float = 0.0,
    days: int = 800,
    n_symbols: int = 80,
) -> pd.DataFrame:
    """Run every variant on the same worlds, one row per (seed, variant).

    Sharing the world across variants makes the comparison paired, so the spread
    between them is not swamped by the spread between draws.
    """
    base_policy = SellPolicy.from_config(next(iter(variants.values())).get("valuation"))
    rows = []
    for seed in seeds:
        features = build_world(seed, reversion, days, n_symbols, base_policy)
        for name, config in variants.items():
            metrics = run_backtest(features, copy.deepcopy(config)).metrics
            rows.append({"seed": seed, "variant": name, **{m: metrics.get(m) for m in METRICS}})
    return pd.DataFrame(rows)


def compare(frame: pd.DataFrame, baseline: str, metric: str = "CAGR") -> pd.DataFrame:
    """Paired difference against the baseline variant, per seed."""
    wide = frame.pivot(index="seed", columns="variant", values=metric)
    out = []
    for variant in wide.columns:
        delta = wide[variant] - wide[baseline]
        n = len(delta)
        se = float(delta.std(ddof=1) / np.sqrt(n)) if n > 1 else float("nan")
        out.append({
            "variant": variant,
            metric: float(wide[variant].mean()),
            "delta": float(delta.mean()),
            "std": float(delta.std(ddof=1)) if n > 1 else float("nan"),
            "t_stat": float(delta.mean() / se) if se else float("nan"),
            "win_rate": float((delta > 0).mean()),
            "seeds": n,
        })
    return pd.DataFrame(out).set_index("variant").sort_values("delta", ascending=False)
